"""Contamination-safe discovery infrastructure tests (no live episode content)."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest
import yaml

from grainsys.discovery.archive_listing import (
    ArchiveListingError,
    normalize_and_mint_archive_listing,
    normalize_archive_listing,
)
from grainsys.discovery.candidates import (
    FORBIDDEN_CANDIDATE_FIELDS,
    CandidateIdError,
    CandidateValidationError,
    mint_candidate_ids,
    validate_candidate_hit,
)
from grainsys.discovery.capture import CapturePathError, candidate_capture_dir, sweeps_root
from grainsys.discovery.config import (
    ALLOWED_KEYWORD_MATCH_MODES,
    ANALYSIS_ANCHOR_GRID_KEYS,
    PROTOCOL_SWEEP_FAMILIES,
    DiscoveryConfigError,
    load_prereg_rules,
    prereg_rules_path,
    require_safe_path_component,
)
from grainsys.discovery.coverage import (
    FORBIDDEN_COVERAGE_FIELDS,
    CoverageValidationError,
    compute_covered_exposure,
    validate_coverage_collection,
    validate_coverage_record,
)
from grainsys.discovery.governance import (
    LOAD_BEARING_ADR_RELATIVE_PATHS,
    LOAD_BEARING_RELATIVE_PATHS,
    MANIFEST_RELATIVE,
    PREREG_TAG,
    RULINGS_PATH_CANONICAL,
    RULINGS_RELATIVE,
    RatificationError,
    assert_rulings_binding_holds,
    assert_sweep_authorized,
    build_interpretation_digests,
    build_ratification_manifest,
    build_rulings_binding,
    emit_ratification_manifest_bytes,
    make_sweep_provenance,
    parse_ruling_sections,
    serialize_ratification_manifest,
    sha256_file,
)
from grainsys.discovery.sweep import SweepEnumerator, SweepError

REPO = Path(__file__).resolve().parents[1]

# Extra paths needed for N3 rulings binding / templates (not all N3 file-digest-bound).
_CONFIG_SUPPORT_RELATIVE = (
    "research/episodes/RULINGS.md",
    "research/episodes/discovery/coverage/_template.yaml",
)

# Explicit synthetic identity strategy for P5 tests (not a live D3/D7 choice).
_TEST_IDENTITY_KEYS = ("authority", "district", "vehicle", "endpoint", "source_family")
_TEST_ABSENCE_FAMILIES = frozenset({"S1"})



# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _base_identity(**overrides):
    row = {
        "authority": "TEST",
        "district": "TEST",
        "vehicle": "TEST",
        "endpoint": None,
        "source_family": "S1",
        "retrieved_on": "2026-01-01",
        "coverage_status": "absent",
        "sweep_status": "not_attempted",
        "records_matched": None,
    }
    row.update(overrides)
    return row


def _anchor_grid_shape(**overrides) -> dict:
    """Synthetic explicit D13 values for isolated tests only — not live decisions."""
    grid = {
        "frequency": "SYNTHETIC_TEST_FREQUENCY",
        "weekday_or_calendar_convention": "SYNTHETIC_TEST_WEEKDAY",
        "cutoff_time": "SYNTHETIC_TEST_CUTOFF",
        "timezone": "SYNTHETIC_TEST_TZ",
        "holiday_treatment": "SYNTHETIC_TEST_HOLIDAY",
        "missing_anchor_handling": "SYNTHETIC_TEST_MISSING",
        "target_date_mapping": "SYNTHETIC_TEST_TARGET_DATE_MAPPING",
    }
    grid.update(overrides)
    return grid


def _complete_prereg(**overrides) -> dict:
    """Structurally complete synthetic config for isolated tests only.

    Uses fictional basin / synthetic dates / protocol family id — not live
    Phase-0 decisions. Does not invent real districts, keywords, or D13 values.
    """
    data = {
        "schema_version": "0.2",
        "governing_adr": "docs/decisions/0003-phase0-prereg-hardening.md",
        "sample_period": {"sample_start": "2099-01-01", "sample_end": "2099-12-31"},
        "corridors": {"navigation_basins": ["fictional_blue_river"]},
        "source_archives": [
            {
                "sweep_id": "S1",
                "authority": "TEST_AUTH",
                "district": "TEST_DISTRICT",
                "vehicle": "TEST_VEHICLE",
                "endpoint": "https://example.invalid/archive",
            }
        ],
        "keyword_policy": {
            "terms": ["TEST_TERM_ONLY"],
            "match": "substring",
            "case_sensitive": False,
            "fields": ["title"],
        },
        "candidates": {
            "table_path": "research/episodes/discovery/candidates/candidates.csv",
            "id_prefix": "CAND",
            "ordering_keys": ["document_date", "source_reference"],
            "stable_id_key": None,
        },
        "capture": {
            "sweeps_subdir": "sweeps",
            "rehome_policy": "candidate_keyed_no_move",
        },
        "coverage": {
            "records_dir": "research/episodes/discovery/coverage",
            "absent_must_be_explicit": True,
            "gap_policy_notes": "SYNTHETIC_TEST_GAP_POLICY",
            "absence_generating_families": ["S1"],
            "source_identity_keys": [
                "authority",
                "district",
                "vehicle",
                "endpoint",
                "source_family",
            ],
        },
        "physical_thresholds": {
            "mode": "binding_operational_restriction_only",
            "class_thresholds": [],
        },
        "event_windows": {
            "pre_event_horizon": "SYNTHETIC_TEST_PRE_EVENT_HORIZON",
            "reference_horizon": "SYNTHETIC_TEST_REFERENCE_HORIZON",
            "response_horizon": "SYNTHETIC_TEST_RESPONSE_HORIZON",
            "mapping_disposition": "SYNTHETIC_TEST_MAPPING_DISPOSITION",
        },
        "calibration_set": {
            "count": 3,
            "selection_rule": "SYNTHETIC_TEST_CALIBRATION_SELECTION_RULE",
        },
        "concurrent_shocks": {
            "shock_types": ["SYNTHETIC_TEST_SHOCK_TYPE"],
            "sweep_rule": "SYNTHETIC_TEST_SHOCK_SWEEP_RULE",
        },
        "analysis_anchor_grid": _anchor_grid_shape(),
    }
    data.update(overrides)
    return data


def _exposure(
    rows,
    *,
    families=_TEST_ABSENCE_FAMILIES,
    keys=_TEST_IDENTITY_KEYS,
    sample_start="2010-01-01",
    sample_end="2020-12-31",
):
    return compute_covered_exposure(
        rows,
        absence_generating_families=families,
        source_identity_keys=keys,
        sample_start=sample_start,
        sample_end=sample_end,
    )

def _git(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
    )


def _write_accepted_adr(path: Path, *, status: str = "accepted") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"# ADR fixture\n\n- **Status:** {status}\n- **Gate:** A | B\n",
        encoding="utf-8",
    )


def _seed_load_bearing(dst_root: Path, src_root: Path = REPO) -> None:
    for rel in (*LOAD_BEARING_RELATIVE_PATHS, *_CONFIG_SUPPORT_RELATIVE):
        src = src_root / rel
        dst = dst_root / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        if src.is_file():
            dst.write_bytes(src.read_bytes())
        else:
            dst.write_text(f"# stub {rel}\n", encoding="utf-8")
    # Good fixtures explicitly accept every load-bearing ADR (real repo statuses
    # are not mutated; only the isolated temp tree is rewritten).
    for rel in LOAD_BEARING_ADR_RELATIVE_PATHS:
        _write_accepted_adr(dst_root / rel, status="accepted")


def _build_ratified_repo(
    tmp_path: Path,
    *,
    adr_status: str = "accepted",
    create_tag: bool = True,
    mutate_config_after_tag: bool = False,
    mutate_interpretation_after_tag: bool = False,
    mutate_adr0005_after_tag: bool = False,
    orphan_head: bool = False,
) -> Path:
    """Isolated git repo for N3 tests — never touches the real repository."""
    root = tmp_path / "ratified"
    root.mkdir()
    _git(root, "init")
    _git(root, "config", "user.email", "test@example.invalid")
    _git(root, "config", "user.name", "Test")
    # Normalize line endings in the fixture repo so HEAD blob == working bytes.
    _git(root, "config", "core.autocrlf", "false")

    _seed_load_bearing(root)
    adr_rel = Path("docs/decisions/0003-phase0-prereg-hardening.md")
    # Build/tag while all load-bearing ADRs are accepted; apply adr_status after.
    _write_accepted_adr(root / adr_rel, status="accepted")

    cfg = _complete_prereg(governing_adr=adr_rel.as_posix())
    cfg_path = root / "config" / "discovery" / "prereg_rules.yaml"
    cfg_path.parent.mkdir(parents=True, exist_ok=True)
    cfg_path.write_text(yaml.safe_dump(cfg), encoding="utf-8", newline="\n")

    # Manifest build requires a clean HEAD byte-match — commit inputs first.
    _git(root, "add", "-A")
    _git(root, "commit", "-m", "seed-load-bearing")

    manifest = build_ratification_manifest(root)
    man_path = root / MANIFEST_RELATIVE
    man_path.write_bytes(serialize_ratification_manifest(manifest))

    _git(root, "add", "-A")
    _git(root, "commit", "-m", "ratify")
    if create_tag:
        _git(root, "tag", PREREG_TAG)

    if adr_status != "accepted":
        _write_accepted_adr(root / adr_rel, status=adr_status)

    if mutate_config_after_tag:
        # Keep ISO-valid dates so the digest mismatch path is what fails.
        cfg["sample_period"]["sample_end"] = "2099-06-30"
        cfg_path.write_text(yaml.safe_dump(cfg), encoding="utf-8", newline="\n")
        _git(root, "add", "-A")
        _git(root, "commit", "-m", "mutate-config")

    if mutate_interpretation_after_tag:
        target = root / "src/grainsys/discovery/governance.py"
        target.write_bytes(target.read_bytes() + b"\n# drift\n")
        _git(root, "add", "-A")
        _git(root, "commit", "-m", "mutate-interp")

    if mutate_adr0005_after_tag:
        target = root / "docs/decisions/0005-source-handling-and-vintage-rules.md"
        target.write_bytes(target.read_bytes() + b"\n# adr0005-drift\n")
        _git(root, "add", "-A")
        _git(root, "commit", "-m", "mutate-adr0005")

    if orphan_head:
        _git(root, "checkout", "--orphan", "orphan-branch")
        (root / "orphan.txt").write_text("x", encoding="utf-8")
        _git(root, "add", "-A")
        _git(root, "commit", "-m", "orphan")

    return root


# ---------------------------------------------------------------------------
# Existing behavioural checks (updated for N2/N3)
# ---------------------------------------------------------------------------


def test_missing_prereg_config_prevents_sweep(tmp_path: Path) -> None:
    assert not prereg_rules_path(tmp_path).exists()
    with pytest.raises(DiscoveryConfigError, match="Missing live preregistration"):
        load_prereg_rules(tmp_path)
    with pytest.raises(SweepError):
        SweepEnumerator.from_repo(tmp_path)


def test_incomplete_prereg_config_fail_closed(tmp_path: Path) -> None:
    cfg_dir = tmp_path / "config" / "discovery"
    cfg_dir.mkdir(parents=True)
    (cfg_dir / "prereg_rules.yaml").write_text(
        yaml.safe_dump(
            {
                "governing_adr": None,
                "sample_period": {"sample_start": None, "sample_end": None},
                "corridors": {"navigation_basins": []},
                "source_archives": [],
                "keyword_policy": {
                    "terms": [],
                    "match": None,
                    "case_sensitive": None,
                    "fields": [],
                },
                "candidates": {
                    "table_path": None,
                    "id_prefix": None,
                    "ordering_keys": [],
                },
                "capture": {"sweeps_subdir": "sweeps"},
                "coverage": {"absent_must_be_explicit": True},
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(DiscoveryConfigError):
        load_prereg_rules(tmp_path)


def test_sweep_enumerator_uses_only_committed_config() -> None:
    """Matching uses constructor; from_repo remains ratification-gated."""
    enum = SweepEnumerator(_complete_prereg())
    targets = list(enum.iter_archives())
    assert len(targets) == 1
    assert targets[0].district == "TEST_DISTRICT"
    assert enum.text_matches_policy("prefix TEST_TERM_ONLY suffix", field="title")
    assert not enum.text_matches_policy("unrelated", field="title")
    with pytest.raises(SweepError, match="not in registered"):
        enum.text_matches_policy("x", field="body")


def test_missing_coverage_status_is_explicit() -> None:
    with pytest.raises(CoverageValidationError, match="coverage_status"):
        validate_coverage_record(
            {
                "authority": "TEST",
                "district": "TEST",
                "vehicle": "TEST",
                "retrieved_on": "2026-01-01",
                "sweep_status": "not_attempted",
            }
        )


def test_absent_coverage_row_requires_identity() -> None:
    with pytest.raises(CoverageValidationError, match="district"):
        validate_coverage_record(
            {
                "authority": "TEST",
                "vehicle": "TEST",
                "coverage_status": "absent",
                "sweep_status": "not_attempted",
                "retrieved_on": "2026-01-01",
            }
        )
    row = validate_coverage_record(_base_identity())
    assert row.coverage_status == "absent"
    assert row.sweep_status == "not_attempted"


def test_candidate_ids_deterministic_under_supplied_ordering() -> None:
    hits = [
        {"source_reference": "b", "document_date": "2020-02-01", "sweep_id": "S_TEST"},
        {"source_reference": "a", "document_date": "2020-01-01", "sweep_id": "S_TEST"},
        {"source_reference": "c", "document_date": "2020-01-01", "sweep_id": "S_TEST"},
    ]
    minted = mint_candidate_ids(
        hits,
        ordering_keys=["document_date", "source_reference"],
        id_prefix="CAND",
    )
    assert [m["candidate_id"] for m in minted] == ["CAND-0001", "CAND-0002", "CAND-0003"]
    again = mint_candidate_ids(
        list(reversed(hits)),
        ordering_keys=["document_date", "source_reference"],
        id_prefix="CAND",
    )
    assert [m["candidate_id"] for m in again] == [m["candidate_id"] for m in minted]


def test_candidate_id_refuses_empty_ordering_rule() -> None:
    with pytest.raises(CandidateIdError, match="ordering_keys"):
        mint_candidate_ids([{"source_reference": "x"}], ordering_keys=[], id_prefix="CAND")


def test_no_market_or_outcome_fields_on_schemas() -> None:
    assert "market_outcome" in FORBIDDEN_CANDIDATE_FIELDS
    assert "price" in FORBIDDEN_COVERAGE_FIELDS
    with pytest.raises(CandidateValidationError, match="episode/market"):
        validate_candidate_hit(
            {
                "candidate_id": "CAND-0001",
                "sweep_id": "S_TEST",
                "source_reference": "ref",
                "ordering_key": "k",
                "market_outcome": "up",
            }
        )
    with pytest.raises(CoverageValidationError, match="event/market"):
        validate_coverage_record(
            _base_identity(
                coverage_status="present",
                endpoint="https://example.invalid",
                price=1.0,
            )
        )


def test_infra_does_not_generate_episode_entries(tmp_path: Path) -> None:
    minted = mint_candidate_ids(
        [{"source_reference": "ref-1", "document_date": "2020-01-01", "sweep_id": "S_TEST"}],
        ordering_keys=["document_date", "source_reference"],
        id_prefix="CAND",
    )
    assert "episode_id" not in minted[0]
    episodes_dir = tmp_path / "research" / "episodes" / "entries"
    episodes_dir.mkdir(parents=True)
    before = set(episodes_dir.rglob("*"))
    _ = minted
    after = set(episodes_dir.rglob("*"))
    assert before == after
    assert list(tmp_path.rglob("EP-*.yaml")) == []


def test_pre_episode_capture_paths_need_no_episode_id(tmp_path: Path) -> None:
    root = sweeps_root(data_root_path=tmp_path, sweeps_subdir="sweeps")
    assert root == tmp_path / "sweeps"
    path = candidate_capture_dir(
        sweep_id="S_TEST",
        candidate_id="CAND-0001",
        data_root_path=tmp_path,
        sweeps_subdir="sweeps",
    )
    assert path == tmp_path / "sweeps" / "S_TEST" / "CAND-0001"
    assert "episodes" not in path.parts
    with pytest.raises(CapturePathError):
        candidate_capture_dir(
            sweep_id="",
            candidate_id="CAND-0001",
            data_root_path=tmp_path,
            sweeps_subdir="sweeps",
        )


def test_repo_has_live_prereg_rules() -> None:
    """After Phase 0 ratification, live prereg_rules.yaml must exist."""
    live = prereg_rules_path(REPO)
    assert live.exists(), "Live prereg_rules.yaml required after Phase 0 ratification"
    template = REPO / "config" / "discovery" / "_prereg_rules.template.yaml"
    assert template.is_file()


# ---------------------------------------------------------------------------
# N1 — deterministic minting
# ---------------------------------------------------------------------------


def test_n1_reversed_input_identical_ids() -> None:
    hits = [
        {"source_reference": "z", "document_date": "2021-01-01", "sweep_id": "S"},
        {"source_reference": "a", "document_date": "2020-01-01", "sweep_id": "S"},
    ]
    a = mint_candidate_ids(hits, ordering_keys=["document_date", "source_reference"], id_prefix="C")
    b = mint_candidate_ids(
        list(reversed(hits)), ordering_keys=["document_date", "source_reference"], id_prefix="C"
    )
    assert [x["candidate_id"] for x in a] == [x["candidate_id"] for x in b]
    assert [x["source_reference"] for x in a] == [x["source_reference"] for x in b]


def test_n1_duplicate_ordering_tuple_raises() -> None:
    hits = [
        {"source_reference": "same", "document_date": "2020-01-01", "sweep_id": "S"},
        {"source_reference": "same", "document_date": "2020-01-01", "sweep_id": "S"},
    ]
    with pytest.raises(CandidateIdError, match="duplicate ordering tuple"):
        mint_candidate_ids(
            hits, ordering_keys=["document_date", "source_reference"], id_prefix="C"
        )


def test_n1_no_positional_fallback_for_ties() -> None:
    # Distinct records that collide on ordering keys must raise, not order by input index.
    hits = [
        {"source_reference": "a", "document_date": "2020-01-01", "extra": "1", "sweep_id": "S"},
        {"source_reference": "a", "document_date": "2020-01-01", "extra": "2", "sweep_id": "S"},
    ]
    with pytest.raises(CandidateIdError, match="duplicate ordering tuple"):
        mint_candidate_ids(
            hits, ordering_keys=["document_date", "source_reference"], id_prefix="C"
        )


def test_n1_exact_duplicate_stable_source_id_dedupes() -> None:
    row = {
        "stable_source_id": "SRC-1",
        "source_reference": "ref",
        "document_date": "2020-01-01",
        "sweep_id": "S",
    }
    minted = mint_candidate_ids(
        [row, dict(row)],
        ordering_keys=["document_date", "source_reference"],
        id_prefix="C",
        stable_id_key="stable_source_id",
    )
    assert len(minted) == 1
    assert minted[0]["candidate_id"] == "C-0001"


def test_n1_conflicting_stable_source_id_raises() -> None:
    a = {
        "stable_source_id": "SRC-1",
        "source_reference": "ref-a",
        "document_date": "2020-01-01",
        "sweep_id": "S",
    }
    b = {
        "stable_source_id": "SRC-1",
        "source_reference": "ref-b",
        "document_date": "2020-01-01",
        "sweep_id": "S",
    }
    with pytest.raises(CandidateIdError, match="conflicting representations"):
        mint_candidate_ids(
            [a, b],
            ordering_keys=["document_date", "source_reference"],
            id_prefix="C",
            stable_id_key="stable_source_id",
        )


def test_n1_missing_ordering_field_raises() -> None:
    with pytest.raises(CandidateIdError, match="ordering key"):
        mint_candidate_ids(
            [{"source_reference": "x", "sweep_id": "S"}],
            ordering_keys=["document_date", "source_reference"],
            id_prefix="C",
        )


# ---------------------------------------------------------------------------
# N2 — coverage / sweep state machine
# ---------------------------------------------------------------------------


def test_n2_present_not_attempted() -> None:
    row = validate_coverage_record(
        _base_identity(
            coverage_status="present",
            endpoint="https://example.invalid",
            sweep_status="not_attempted",
            earliest_available="2010-01-01",
            latest_available="2020-01-01",
        )
    )
    assert row.records_matched is None


def test_n2_present_enumerated_zero() -> None:
    row = validate_coverage_record(
        _base_identity(
            coverage_status="present",
            endpoint="https://example.invalid",
            sweep_status="enumerated",
            records_matched=0,
            scope_start="2015-01-01",
            scope_end="2015-12-31",
        )
    )
    assert row.records_matched == 0


def test_n2_present_enumerated_positive() -> None:
    row = validate_coverage_record(
        _base_identity(
            coverage_status="present",
            endpoint="https://example.invalid",
            sweep_status="enumerated",
            records_matched=3,
            scope_start="2015-01-01",
            scope_end="2015-12-31",
        )
    )
    assert row.records_matched == 3


def test_n2_attempted_failed_requires_present() -> None:
    validate_coverage_record(
        _base_identity(
            coverage_status="present",
            endpoint="https://example.invalid",
            sweep_status="attempted_failed",
        )
    )
    with pytest.raises(CoverageValidationError, match="attempted_failed"):
        validate_coverage_record(_base_identity(sweep_status="attempted_failed"))


def test_n2_absent_cannot_enumerate() -> None:
    with pytest.raises(CoverageValidationError, match="enumerated"):
        validate_coverage_record(
            _base_identity(
                coverage_status="absent",
                sweep_status="enumerated",
                records_matched=0,
                scope_start="2015-01-01",
                scope_end="2015-12-31",
            )
        )


def test_n2_unknown_cannot_enumerate() -> None:
    with pytest.raises(CoverageValidationError, match="present"):
        validate_coverage_record(
            _base_identity(
                coverage_status="unknown",
                sweep_status="enumerated",
                records_matched=0,
                scope_start="2015-01-01",
                scope_end="2015-12-31",
            )
        )


def test_n2_records_matched_null_unless_enumerated() -> None:
    with pytest.raises(CoverageValidationError, match="records_matched"):
        validate_coverage_record(
            _base_identity(
                coverage_status="present",
                endpoint="https://example.invalid",
                sweep_status="not_attempted",
                records_matched=0,
            )
        )


def test_n2_enumerated_requires_scope_and_count() -> None:
    with pytest.raises(CoverageValidationError, match="records_matched"):
        validate_coverage_record(
            _base_identity(
                coverage_status="present",
                endpoint="https://example.invalid",
                sweep_status="enumerated",
                scope_start="2015-01-01",
                scope_end="2015-12-31",
            )
        )
    with pytest.raises(CoverageValidationError, match="scope_start"):
        validate_coverage_record(
            _base_identity(
                coverage_status="present",
                endpoint="https://example.invalid",
                sweep_status="enumerated",
                records_matched=0,
                earliest_available="2010-01-01",
                latest_available="2020-01-01",
            )
        )


def test_n2_records_matched_negative_illegal() -> None:
    with pytest.raises(CoverageValidationError, match=">= 0"):
        validate_coverage_record(
            _base_identity(
                coverage_status="present",
                endpoint="https://example.invalid",
                sweep_status="enumerated",
                records_matched=-1,
                scope_start="2015-01-01",
                scope_end="2015-12-31",
            )
        )


def test_n2_missing_sweep_status_illegal() -> None:
    with pytest.raises(CoverageValidationError, match="sweep_status"):
        validate_coverage_record(
            {
                "authority": "TEST",
                "district": "TEST",
                "vehicle": "TEST",
                "retrieved_on": "2026-01-01",
                "coverage_status": "absent",
            }
        )


# ---------------------------------------------------------------------------
# N3 — ratification guard
# ---------------------------------------------------------------------------


def test_n3_real_repo_refuses_live_sweep_execution() -> None:
    """Current canonical repo has no prereg-rules-v1 — must fail closed."""
    with pytest.raises(RatificationError):
        assert_sweep_authorized(REPO)
    with pytest.raises(SweepError, match="ratification"):
        SweepEnumerator.from_repo(REPO)
    tags = subprocess.run(
        ["git", "tag", "-l", PREREG_TAG],
        cwd=REPO,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    assert tags == ""


def test_n3_isolated_repo_authorizes_when_all_conditions_met(tmp_path: Path) -> None:
    root = _build_ratified_repo(tmp_path)
    prov = assert_sweep_authorized(root)
    assert prov.prereg_tag == PREREG_TAG
    assert prov.governing_adr.endswith("0003-phase0-prereg-hardening.md")
    enum = SweepEnumerator.from_repo(root)
    assert len(list(enum.iter_archives())) == 1


def test_n3_blocks_when_adr_not_accepted(tmp_path: Path) -> None:
    root = _build_ratified_repo(tmp_path, adr_status="proposed")
    with pytest.raises(RatificationError, match="accepted"):
        assert_sweep_authorized(root)


def test_n3_blocks_when_tag_absent(tmp_path: Path) -> None:
    root = _build_ratified_repo(tmp_path, create_tag=False)
    with pytest.raises(RatificationError, match="absent"):
        assert_sweep_authorized(root)


def test_n3_blocks_on_config_digest_mismatch(tmp_path: Path) -> None:
    root = _build_ratified_repo(tmp_path, mutate_config_after_tag=True)
    with pytest.raises(RatificationError, match="digest"):
        assert_sweep_authorized(root)


def test_n3_blocks_on_interpretation_digest_drift(tmp_path: Path) -> None:
    root = _build_ratified_repo(tmp_path, mutate_interpretation_after_tag=True)
    with pytest.raises(RatificationError, match="interpretation digest"):
        assert_sweep_authorized(root)


def test_n3_adr0005_is_load_bearing_and_post_tag_drift_blocks(tmp_path: Path) -> None:
    """ADR-0005 must be digest-bound; post-tag edits fail closed (N3 architecture)."""
    adr5 = "docs/decisions/0005-source-handling-and-vintage-rules.md"
    adr4_inference = "docs/decisions/0004-phase0-inference-rules.md"
    assert adr5 in LOAD_BEARING_RELATIVE_PATHS
    assert "research/episodes/RULINGS.md" not in LOAD_BEARING_RELATIVE_PATHS
    assert "research/episodes/episode_schema.yaml" in LOAD_BEARING_RELATIVE_PATHS
    assert "research/episodes/discovery/candidates/_schema.yaml" in LOAD_BEARING_RELATIVE_PATHS
    assert "src/grainsys/discovery/archive_listing.py" in LOAD_BEARING_RELATIVE_PATHS
    assert "src/grainsys/discovery/capture.py" in LOAD_BEARING_RELATIVE_PATHS
    assert "src/grainsys/episodes.py" in LOAD_BEARING_RELATIVE_PATHS
    assert "research/episodes/ADMISSION_CHECKLIST.md" in LOAD_BEARING_RELATIVE_PATHS
    assert adr4_inference not in LOAD_BEARING_RELATIVE_PATHS
    # ADR-0004 deferred until present on branch / before real tag.
    assert not (REPO / adr4_inference).exists()

    root = _build_ratified_repo(tmp_path)
    assert (root / adr5).is_file()
    assert not (root / adr4_inference).is_file()
    digests = build_interpretation_digests(root)
    assert adr5 in digests
    manifest = yaml.safe_load((root / MANIFEST_RELATIVE).read_text(encoding="utf-8"))
    assert adr5 in manifest["interpretation_digests"]
    assert manifest["interpretation_digests"][adr5] == digests[adr5]
    assert_sweep_authorized(root)

    drift_base = tmp_path / "drift"
    drift_base.mkdir()
    drifted = _build_ratified_repo(drift_base, mutate_adr0005_after_tag=True)
    with pytest.raises(
        RatificationError,
        match=r"interpretation digest drift for docs/decisions/0005-source-handling-and-vintage-rules\.md",
    ):
        assert_sweep_authorized(drifted)


def test_n3_positive_only_s1_contract_is_load_bearing_and_drift_blocks(
    tmp_path: Path,
) -> None:
    """The approved S1 evidence rule and its adapter cannot drift after N3."""
    adr15 = "docs/decisions/0015-d3-d4-positive-only-s1.md"
    adapter = "src/grainsys/ingest/ntni.py"
    assert adr15 in LOAD_BEARING_RELATIVE_PATHS
    assert adapter in LOAD_BEARING_RELATIVE_PATHS

    root = _build_ratified_repo(tmp_path)
    digests = build_interpretation_digests(root)
    manifest = yaml.safe_load((root / MANIFEST_RELATIVE).read_text(encoding="utf-8"))
    assert manifest["interpretation_digests"][adr15] == digests[adr15]
    assert manifest["interpretation_digests"][adapter] == digests[adapter]
    assert_sweep_authorized(root)

    target = root / adr15
    target.write_bytes(target.read_bytes() + b"\n# positive-only-contract-drift\n")
    _git(root, "add", "-A")
    _git(root, "commit", "-m", "mutate-positive-only-contract")
    with pytest.raises(
        RatificationError,
        match=r"interpretation digest drift for docs/decisions/0015-d3-d4-positive-only-s1\.md",
    ):
        assert_sweep_authorized(root)


def test_n3_blocks_when_head_not_descendant(tmp_path: Path) -> None:
    root = _build_ratified_repo(tmp_path, orphan_head=True)
    with pytest.raises(RatificationError, match="descendant"):
        assert_sweep_authorized(root)


def test_n3_provenance_helper_ready() -> None:
    digest = "a" * 64
    sha = "b" * 40
    stamp = make_sweep_provenance(
        prereg_config_digest=digest,
        execution_commit_sha=sha,
        governing_adr="docs/decisions/0003-phase0-prereg-hardening.md",
    )
    assert stamp.to_dict()["prereg_tag"] == PREREG_TAG
    with pytest.raises(RatificationError):
        make_sweep_provenance(
            prereg_config_digest="",
            execution_commit_sha=sha,
            governing_adr="x",
        )
    with pytest.raises(RatificationError):
        make_sweep_provenance(
            prereg_config_digest="not-a-digest",
            execution_commit_sha=sha,
            governing_adr="docs/decisions/0003-phase0-prereg-hardening.md",
        )
    with pytest.raises(RatificationError, match="40-hex"):
        make_sweep_provenance(
            prereg_config_digest=digest,
            execution_commit_sha="def",
            governing_adr="docs/decisions/0003-phase0-prereg-hardening.md",
        )


# ---------------------------------------------------------------------------
# N4 — whole_word matcher capability
# ---------------------------------------------------------------------------


def test_n4_whole_word_match() -> None:
    enum = SweepEnumerator(
        _complete_prereg(
            keyword_policy={
                "terms": ["closure"],
                "match": "whole_word",
                "case_sensitive": False,
                "fields": ["title"],
            }
        )
    )
    assert enum.text_matches_policy("channel closure announced", field="title")


def test_n4_whole_word_non_match_inside_larger_word() -> None:
    enum = SweepEnumerator(
        _complete_prereg(
            keyword_policy={
                "terms": ["draft"],
                "match": "whole_word",
                "case_sensitive": False,
                "fields": ["title"],
            }
        )
    )
    assert not enum.text_matches_policy("redrafted notice", field="title")
    assert enum.text_matches_policy("draft restriction", field="title")


def test_n4_case_sensitive_behavior() -> None:
    enum = SweepEnumerator(
        _complete_prereg(
            keyword_policy={
                "terms": ["Closure"],
                "match": "whole_word",
                "case_sensitive": True,
                "fields": ["title"],
            }
        )
    )
    assert enum.text_matches_policy("Closure today", field="title")
    assert not enum.text_matches_policy("closure today", field="title")


def test_n4_case_folded_behavior() -> None:
    enum = SweepEnumerator(
        _complete_prereg(
            keyword_policy={
                "terms": ["Closure"],
                "match": "whole_word",
                "case_sensitive": False,
                "fields": ["title"],
            }
        )
    )
    assert enum.text_matches_policy("closure today", field="title")


def test_n4_explicit_variants_only() -> None:
    enum = SweepEnumerator(
        _complete_prereg(
            keyword_policy={
                "terms": ["closure", "closures"],
                "match": "whole_word",
                "case_sensitive": False,
                "fields": ["title"],
            }
        )
    )
    assert enum.text_matches_policy("closures overnight", field="title")
    # Stem not configured — must not match hidden morphology
    enum2 = SweepEnumerator(
        _complete_prereg(
            keyword_policy={
                "terms": ["closure"],
                "match": "whole_word",
                "case_sensitive": False,
                "fields": ["title"],
            }
        )
    )
    assert not enum2.text_matches_policy("closures overnight", field="title")


def test_n4_unsupported_mode_fail_closed() -> None:
    enum = SweepEnumerator(
        _complete_prereg(
            keyword_policy={
                "terms": ["closure"],
                "match": "stem",
                "case_sensitive": False,
                "fields": ["title"],
            }
        )
    )
    with pytest.raises(SweepError, match="not implemented"):
        enum.text_matches_policy("closure", field="title")


# ---------------------------------------------------------------------------
# A — config fail-closed hardening (live D13 / D6)
# ---------------------------------------------------------------------------


def _write_live_cfg(tmp_path: Path, data: dict) -> Path:
    _seed_load_bearing(tmp_path)
    cfg_path = tmp_path / "config" / "discovery" / "prereg_rules.yaml"
    cfg_path.parent.mkdir(parents=True, exist_ok=True)
    cfg_path.write_text(yaml.safe_dump(data), encoding="utf-8")
    return cfg_path


def test_a_complete_synthetic_config_loads(tmp_path: Path) -> None:
    _write_live_cfg(tmp_path, _complete_prereg())
    cfg = load_prereg_rules(tmp_path)
    assert cfg["sample_period"]["sample_start"] == "2099-01-01"
    for key in ANALYSIS_ANCHOR_GRID_KEYS:
        assert cfg["analysis_anchor_grid"][key] not in (None, "")


def test_a_unchanged_template_copy_fail_closed(tmp_path: Path) -> None:
    _seed_load_bearing(tmp_path)
    template = (REPO / "config/discovery/_prereg_rules.template.yaml").read_text(
        encoding="utf-8"
    )
    cfg_path = tmp_path / "config" / "discovery" / "prereg_rules.yaml"
    cfg_path.parent.mkdir(parents=True, exist_ok=True)
    cfg_path.write_text(template, encoding="utf-8")
    with pytest.raises(DiscoveryConfigError):
        load_prereg_rules(tmp_path)


def test_a_missing_analysis_anchor_grid_fail_closed(tmp_path: Path) -> None:
    cfg = _complete_prereg()
    del cfg["analysis_anchor_grid"]
    _write_live_cfg(tmp_path, cfg)
    with pytest.raises(DiscoveryConfigError, match="analysis_anchor_grid"):
        load_prereg_rules(tmp_path)


def test_a_incomplete_analysis_anchor_grid_keys_fail_closed(tmp_path: Path) -> None:
    cfg = _complete_prereg()
    cfg["analysis_anchor_grid"] = {"frequency": "weekly"}
    _write_live_cfg(tmp_path, cfg)
    with pytest.raises(DiscoveryConfigError, match="missing required keys"):
        load_prereg_rules(tmp_path)


@pytest.mark.parametrize("key", list(ANALYSIS_ANCHOR_GRID_KEYS))
def test_a_each_null_d13_field_fail_closed(tmp_path: Path, key: str) -> None:
    cfg = _complete_prereg()
    cfg["analysis_anchor_grid"][key] = None
    _write_live_cfg(tmp_path, cfg)
    with pytest.raises(DiscoveryConfigError, match=key):
        load_prereg_rules(tmp_path)


@pytest.mark.parametrize("key", list(ANALYSIS_ANCHOR_GRID_KEYS))
def test_a_each_empty_d13_field_fail_closed(tmp_path: Path, key: str) -> None:
    cfg = _complete_prereg()
    cfg["analysis_anchor_grid"][key] = "   "
    _write_live_cfg(tmp_path, cfg)
    with pytest.raises(DiscoveryConfigError, match=key):
        load_prereg_rules(tmp_path)


def test_a_fully_explicit_synthetic_grid_loads(tmp_path: Path) -> None:
    grid = _anchor_grid_shape(
        frequency="weekly",
        weekday_or_calendar_convention="thursday",
        cutoff_time="12:00",
        timezone="America/Chicago",
        holiday_treatment="skip",
        missing_anchor_handling="fail_closed",
    )
    _write_live_cfg(tmp_path, _complete_prereg(analysis_anchor_grid=grid))
    cfg = load_prereg_rules(tmp_path)
    assert cfg["analysis_anchor_grid"] == grid


def test_a_rehome_policy_null_fail_closed(tmp_path: Path) -> None:
    cfg = _complete_prereg()
    cfg["capture"]["rehome_policy"] = None
    _write_live_cfg(tmp_path, cfg)
    with pytest.raises(DiscoveryConfigError, match="rehome_policy"):
        load_prereg_rules(tmp_path)


def test_a_rehome_policy_missing_fail_closed(tmp_path: Path) -> None:
    cfg = _complete_prereg()
    del cfg["capture"]["rehome_policy"]
    _write_live_cfg(tmp_path, cfg)
    with pytest.raises(DiscoveryConfigError, match="rehome_policy"):
        load_prereg_rules(tmp_path)


@pytest.mark.parametrize("bad", ["", "   ", "\t"])
def test_a_rehome_policy_empty_whitespace_fail_closed(tmp_path: Path, bad: str) -> None:
    cfg = _complete_prereg()
    cfg["capture"]["rehome_policy"] = bad
    _write_live_cfg(tmp_path, cfg)
    with pytest.raises(DiscoveryConfigError, match="rehome_policy"):
        load_prereg_rules(tmp_path)


@pytest.mark.parametrize(
    "bad",
    [
        "move",
        "copy",
        "none",
        "reference_view",
        "verified_copy",
        "SYNTHETIC_TEST_ONLY_UNSET",
        "arbitrary_custom",
    ],
)
def test_a_rehome_policy_unauthorized_token_fail_closed(tmp_path: Path, bad: str) -> None:
    cfg = _complete_prereg()
    cfg["capture"]["rehome_policy"] = bad
    _write_live_cfg(tmp_path, cfg)
    with pytest.raises(DiscoveryConfigError, match="rehome_policy|unauthorized"):
        load_prereg_rules(tmp_path)


def test_a_rehome_policy_candidate_keyed_no_move_accepted(tmp_path: Path) -> None:
    cfg = _complete_prereg()
    cfg["capture"]["rehome_policy"] = "candidate_keyed_no_move"
    _write_live_cfg(tmp_path, cfg)
    loaded = load_prereg_rules(tmp_path)
    assert loaded["capture"]["rehome_policy"] == "candidate_keyed_no_move"


def test_a_sample_dates_reject_placeholder(tmp_path: Path) -> None:
    cfg = _complete_prereg()
    cfg["sample_period"] = {"sample_start": "TO_BE_SET", "sample_end": "2099-12-31"}
    _write_live_cfg(tmp_path, cfg)
    with pytest.raises(DiscoveryConfigError, match="placeholder"):
        load_prereg_rules(tmp_path)


def test_a_sample_dates_require_order(tmp_path: Path) -> None:
    cfg = _complete_prereg()
    cfg["sample_period"] = {"sample_start": "2099-12-31", "sample_end": "2099-01-01"}
    _write_live_cfg(tmp_path, cfg)
    with pytest.raises(DiscoveryConfigError, match="must be <="):
        load_prereg_rules(tmp_path)


def test_a_sample_dates_reject_non_iso(tmp_path: Path) -> None:
    cfg = _complete_prereg()
    cfg["sample_period"] = {"sample_start": "2099/01/01", "sample_end": "2099-12-31"}
    _write_live_cfg(tmp_path, cfg)
    with pytest.raises(DiscoveryConfigError, match="ISO calendar date"):
        load_prereg_rules(tmp_path)


def test_a_keyword_match_must_be_allowed_mode(tmp_path: Path) -> None:
    assert "substring" in ALLOWED_KEYWORD_MATCH_MODES
    cfg = _complete_prereg()
    cfg["keyword_policy"]["match"] = "stem"
    _write_live_cfg(tmp_path, cfg)
    with pytest.raises(DiscoveryConfigError, match="not an allowed mode"):
        load_prereg_rules(tmp_path)


def test_a_coverage_records_dir_required(tmp_path: Path) -> None:
    cfg = _complete_prereg()
    cfg["coverage"]["records_dir"] = None
    _write_live_cfg(tmp_path, cfg)
    with pytest.raises(DiscoveryConfigError, match="records_dir"):
        load_prereg_rules(tmp_path)


# ---------------------------------------------------------------------------
# B — coverage P5 / R-013 corrections
# ---------------------------------------------------------------------------


def test_b_scope_dates_validated_and_ordered() -> None:
    with pytest.raises(CoverageValidationError, match="scope_start"):
        validate_coverage_record(
            _base_identity(
                coverage_status="present",
                endpoint="https://example.invalid",
                sweep_status="enumerated",
                records_matched=0,
                scope_start="2015-13-01",
                scope_end="2015-12-31",
            )
        )
    with pytest.raises(CoverageValidationError, match="must be <="):
        validate_coverage_record(
            _base_identity(
                coverage_status="present",
                endpoint="https://example.invalid",
                sweep_status="enumerated",
                records_matched=0,
                scope_start="2015-12-31",
                scope_end="2015-01-01",
            )
        )


def test_b_known_gap_requires_both_bounds() -> None:
    with pytest.raises(CoverageValidationError, match="both be set"):
        validate_coverage_record(
            _base_identity(
                coverage_status="absent",
                sweep_status="not_attempted",
                scope_start="2015-06-01",
            )
        )


def test_b_defect_supplementary_family_not_swept_zero_eligible() -> None:
    """Defect 1/3: supplementary enumerated family never exposes intervals/zero."""
    rows = [
        _base_identity(
            source_family="S8",
            coverage_status="present",
            endpoint="https://example.invalid/a",
            sweep_status="enumerated",
            records_matched=0,
            scope_start="2015-01-01",
            scope_end="2015-12-31",
        )
    ]
    exposure = _exposure(rows, families=_TEST_ABSENCE_FAMILIES)  # S8 not included
    assert exposure[0].is_absence_generating is False
    assert exposure[0].has_enumeration is True
    assert exposure[0].intervals == ()
    assert exposure[0].is_swept_zero_eligible is False


def test_b_defect_fully_gapped_net_empty_not_eligible() -> None:
    """Defect 2: fully removed net exposure is not swept-zero eligible."""
    rows = [
        _base_identity(
            coverage_status="present",
            endpoint="https://example.invalid/a",
            sweep_status="enumerated",
            records_matched=0,
            scope_start="2015-01-01",
            scope_end="2015-12-31",
        ),
        _base_identity(
            coverage_status="absent",
            endpoint="https://example.invalid/a",
            sweep_status="not_attempted",
            scope_start="2015-01-01",
            scope_end="2015-12-31",
        ),
    ]
    exposure = _exposure(rows)
    assert exposure[0].has_enumeration is True
    assert exposure[0].intervals == ()
    assert exposure[0].is_swept_zero_eligible is False


def test_b_defect_explicit_identity_groups_null_endpoint_with_set() -> None:
    """Defect 3: identity keys must not invent '' for null endpoint."""
    # Same identity keys including endpoint — null vs set are different groups
    # unless caller omits endpoint from identity.
    rows_split = [
        _base_identity(
            coverage_status="present",
            endpoint="https://example.invalid/a",
            sweep_status="enumerated",
            records_matched=0,
            scope_start="2015-01-01",
            scope_end="2015-12-31",
        ),
        _base_identity(
            coverage_status="absent",
            endpoint=None,
            sweep_status="not_attempted",
            scope_start="2015-06-01",
            scope_end="2015-06-30",
        ),
    ]
    split = _exposure(rows_split, keys=_TEST_IDENTITY_KEYS)
    assert len(split) == 2

    # Explicit identity without endpoint groups them so the gap subtracts.
    keys = ("authority", "district", "vehicle", "source_family")
    rows_joined = [
        _base_identity(
            coverage_status="present",
            endpoint="https://example.invalid/a",
            sweep_status="enumerated",
            records_matched=0,
            scope_start="2015-01-01",
            scope_end="2015-12-31",
        ),
        _base_identity(
            coverage_status="absent",
            endpoint=None,
            sweep_status="not_attempted",
            scope_start="2015-06-01",
            scope_end="2015-06-30",
        ),
    ]
    joined = _exposure(rows_joined, keys=keys)
    assert len(joined) == 1
    assert [iv.to_pair() for iv in joined[0].intervals] == [
        ("2015-01-01", "2015-05-31"),
        ("2015-07-01", "2015-12-31"),
    ]
    assert joined[0].is_swept_zero_eligible is True


def test_b_missing_identity_key_rejected() -> None:
    row = _base_identity(
        coverage_status="present",
        endpoint="https://example.invalid",
        sweep_status="enumerated",
        records_matched=0,
        scope_start="2015-01-01",
        scope_end="2015-12-31",
    )
    del row["endpoint"]
    with pytest.raises(CoverageValidationError, match="identity key"):
        _exposure([row], keys=_TEST_IDENTITY_KEYS)


def test_b_overlapping_enumerated_union_merged() -> None:
    rows = [
        _base_identity(
            coverage_status="present",
            endpoint="https://example.invalid/a",
            sweep_status="enumerated",
            records_matched=0,
            scope_start="2015-01-01",
            scope_end="2015-06-30",
        ),
        _base_identity(
            coverage_status="present",
            endpoint="https://example.invalid/a",
            sweep_status="enumerated",
            records_matched=0,
            scope_start="2015-06-01",
            scope_end="2015-12-31",
        ),
    ]
    exposure = _exposure(rows)
    assert [iv.to_pair() for iv in exposure[0].intervals] == [
        ("2015-01-01", "2015-12-31")
    ]
    assert exposure[0].is_swept_zero_eligible is True


def test_b_nonzero_matches_not_swept_zero_eligible() -> None:
    rows = [
        _base_identity(
            coverage_status="present",
            endpoint="https://example.invalid/a",
            sweep_status="enumerated",
            records_matched=3,
            scope_start="2015-01-01",
            scope_end="2015-12-31",
        )
    ]
    exposure = _exposure(rows)
    assert exposure[0].is_absence_generating is True
    assert exposure[0].has_enumeration is True
    assert len(exposure[0].intervals) == 1
    assert exposure[0].is_swept_zero_eligible is False


def test_b_not_attempted_never_becomes_swept_zero() -> None:
    rows = [
        _base_identity(
            coverage_status="present",
            endpoint="https://example.invalid/a",
            sweep_status="not_attempted",
        )
    ]
    exposure = _exposure(rows)
    assert exposure[0].has_enumeration is False
    assert exposure[0].is_swept_zero_eligible is False


def test_b_attempted_failed_never_becomes_swept_zero() -> None:
    rows = [
        _base_identity(
            coverage_status="present",
            endpoint="https://example.invalid/a",
            sweep_status="attempted_failed",
        )
    ]
    exposure = _exposure(rows)
    assert exposure[0].has_enumeration is False
    assert exposure[0].is_swept_zero_eligible is False


def test_b_whole_source_absent_with_enumeration_rejected() -> None:
    rows = [
        _base_identity(
            coverage_status="present",
            endpoint="https://example.invalid/a",
            sweep_status="enumerated",
            records_matched=0,
            scope_start="2015-01-01",
            scope_end="2015-12-31",
        ),
        _base_identity(
            coverage_status="absent",
            endpoint="https://example.invalid/a",
            sweep_status="not_attempted",
        ),
    ]
    with pytest.raises(CoverageValidationError, match="whole-source absent"):
        _exposure(rows)


def test_b_covered_exposure_enumerated_minus_gaps() -> None:
    rows = [
        _base_identity(
            coverage_status="present",
            endpoint="https://example.invalid/a",
            sweep_status="enumerated",
            records_matched=0,
            scope_start="2015-01-01",
            scope_end="2015-12-31",
        ),
        _base_identity(
            coverage_status="absent",
            endpoint="https://example.invalid/a",
            sweep_status="not_attempted",
            scope_start="2015-06-01",
            scope_end="2015-06-30",
        ),
    ]
    exposure = validate_coverage_collection(
        rows,
        absence_generating_families=_TEST_ABSENCE_FAMILIES,
        source_identity_keys=_TEST_IDENTITY_KEYS,
        sample_start="2010-01-01",
        sample_end="2020-12-31",
    )
    assert exposure[0].is_swept_zero_eligible is True
    assert [iv.to_pair() for iv in exposure[0].intervals] == [
        ("2015-01-01", "2015-05-31"),
        ("2015-07-01", "2015-12-31"),
    ]


# ---------------------------------------------------------------------------
# C — N3 governance binding / emitter
# ---------------------------------------------------------------------------


def test_c_manifest_emitter_byte_identical(tmp_path: Path) -> None:
    root = _build_ratified_repo(tmp_path)
    a = emit_ratification_manifest_bytes(root)
    b = emit_ratification_manifest_bytes(root)
    assert a == b
    assert a == serialize_ratification_manifest(build_ratification_manifest(root))
    parsed = yaml.safe_load(a)
    assert parsed["prereg_config_digest"] == sha256_file(
        root / "config" / "discovery" / "prereg_rules.yaml"
    )
    assert set(parsed["interpretation_digests"]) == set(LOAD_BEARING_RELATIVE_PATHS)
    assert list(parsed["interpretation_digests"]) == sorted(LOAD_BEARING_RELATIVE_PATHS)
    assert "rulings_binding" in parsed
    assert parsed["rulings_binding"]["bound_ruling_ids"][0] == "R-001"


def test_c_manifest_shuffled_mapping_order_canonical(tmp_path: Path) -> None:
    root = _build_ratified_repo(tmp_path)
    base = build_ratification_manifest(root)
    shuffled = {
        "rulings_binding": {
            "ruling_digests": dict(
                reversed(list(base["rulings_binding"]["ruling_digests"].items()))
            ),
            "path": base["rulings_binding"]["path"],
            "bound_ruling_ids": list(base["rulings_binding"]["bound_ruling_ids"]),
        },
        "interpretation_digests": dict(
            reversed(list(base["interpretation_digests"].items()))
        ),
        "prereg_config_digest": base["prereg_config_digest"],
        "governing_adr": base["governing_adr"],
    }
    assert serialize_ratification_manifest(base) == serialize_ratification_manifest(
        shuffled
    )


def test_c_manifest_emitter_drifts_with_load_bearing_change(tmp_path: Path) -> None:
    root = _build_ratified_repo(tmp_path)
    before = emit_ratification_manifest_bytes(root)
    target = root / "src/grainsys/discovery/coverage.py"
    target.write_bytes(target.read_bytes() + b"\n# emitter-drift\n")
    with pytest.raises(RatificationError, match="working tree drift|fresh normalized"):
        emit_ratification_manifest_bytes(root)
    _git(root, "add", "-A")
    _git(root, "commit", "-m", "emitter-drift")
    after = emit_ratification_manifest_bytes(root)
    assert before != after
    before_doc = yaml.safe_load(before)
    after_doc = yaml.safe_load(after)
    rel = "src/grainsys/discovery/coverage.py"
    assert before_doc["interpretation_digests"][rel] != after_doc["interpretation_digests"][rel]


def test_c_manifest_emitter_drifts_with_config_change(tmp_path: Path) -> None:
    root = _build_ratified_repo(tmp_path)
    before = emit_ratification_manifest_bytes(root)
    cfg_path = root / "config" / "discovery" / "prereg_rules.yaml"
    cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
    cfg["sample_period"]["sample_end"] = "2099-11-30"
    cfg_path.write_text(yaml.safe_dump(cfg), encoding="utf-8", newline="\n")
    with pytest.raises(RatificationError, match="working tree drift|fresh normalized"):
        emit_ratification_manifest_bytes(root)
    _git(root, "add", "-A")
    _git(root, "commit", "-m", "config-drift")
    after = emit_ratification_manifest_bytes(root)
    assert yaml.safe_load(before)["prereg_config_digest"] != yaml.safe_load(after)[
        "prereg_config_digest"
    ]


def test_c_rulings_append_passes_bound_prefix(tmp_path: Path) -> None:
    root = _build_ratified_repo(tmp_path)
    bound = build_rulings_binding(root)
    rulings_path = root / RULINGS_RELATIVE
    base = rulings_path.read_text(encoding="utf-8")
    if not base.endswith("\n"):
        base += "\n"
    # Immediate-heading append.
    rulings_path.write_text(
        base
        + "### 2099-01-01 · R-999 · Synthetic append-only fixture\n\n"
        "- **Situation:** test\n"
        "- **Rule invoked:** test\n"
        "- **Ruling:** append only\n"
        "- **Generalises to:** tests\n"
        "- **Decided by:** A + B\n"
        "- **Supersedes:** none\n",
        encoding="utf-8",
    )
    assert_rulings_binding_holds(root, bound)
    # Authorization still holds after append (bound prefix unchanged).
    assert_sweep_authorized(root)


def test_c_rulings_natural_blank_line_append_passes(tmp_path: Path) -> None:
    root = _build_ratified_repo(tmp_path)
    bound = build_rulings_binding(root)
    rulings_path = root / RULINGS_RELATIVE
    base = rulings_path.read_text(encoding="utf-8")
    if not base.endswith("\n"):
        base += "\n"
    rulings_path.write_text(
        base
        + "\n### 2099-01-02 · R-998 · Blank-line append fixture\n\n"
        "- **Situation:** test\n"
        "- **Rule invoked:** test\n"
        "- **Ruling:** natural blank-line append\n"
        "- **Generalises to:** tests\n"
        "- **Decided by:** A + B\n"
        "- **Supersedes:** none\n",
        encoding="utf-8",
    )
    assert_rulings_binding_holds(root, bound)


def test_c_rulings_edit_bound_prefix_fails(tmp_path: Path) -> None:
    root = _build_ratified_repo(tmp_path)
    bound = build_rulings_binding(root)
    rulings_path = root / RULINGS_RELATIVE
    text = rulings_path.read_text(encoding="utf-8")
    rulings_path.write_text(
        text.replace("Date-only public_anchor", "MUTATED public_anchor", 1),
        encoding="utf-8",
    )
    with pytest.raises(RatificationError, match="digest drift|mutated"):
        assert_rulings_binding_holds(root, bound)


def test_c_rulings_delete_bound_prefix_fails(tmp_path: Path) -> None:
    root = _build_ratified_repo(tmp_path)
    bound = build_rulings_binding(root)
    sections = parse_ruling_sections((root / RULINGS_RELATIVE).read_text(encoding="utf-8"))
    # Drop the first concrete ruling body from the file.
    text = (root / RULINGS_RELATIVE).read_text(encoding="utf-8")
    (root / RULINGS_RELATIVE).write_text(
        text.replace(sections[0].body.rstrip("\n"), "", 1),
        encoding="utf-8",
    )
    with pytest.raises(RatificationError, match="prefix|missing|reordered|mutated"):
        assert_rulings_binding_holds(root, bound)


def test_c_rulings_reorder_bound_prefix_fails(tmp_path: Path) -> None:
    root = _build_ratified_repo(tmp_path)
    bound = build_rulings_binding(root)
    sections = parse_ruling_sections((root / RULINGS_RELATIVE).read_text(encoding="utf-8"))
    # Swap first two concrete sections in the file body.
    text = (root / RULINGS_RELATIVE).read_text(encoding="utf-8")
    a, b = sections[0].body, sections[1].body
    # Replace in reverse order of appearance carefully.
    without_a = text.replace(a.rstrip("\n"), "@@A@@", 1)
    swapped = without_a.replace(b.rstrip("\n"), a.rstrip("\n"), 1).replace(
        "@@A@@", b.rstrip("\n"), 1
    )
    (root / RULINGS_RELATIVE).write_text(swapped, encoding="utf-8")
    with pytest.raises(RatificationError, match="reordered|mutated|prefix"):
        assert_rulings_binding_holds(root, bound)


def test_c_rulings_insert_into_bound_prefix_fails(tmp_path: Path) -> None:
    root = _build_ratified_repo(tmp_path)
    bound = build_rulings_binding(root)
    sections = parse_ruling_sections((root / RULINGS_RELATIVE).read_text(encoding="utf-8"))
    text = (root / RULINGS_RELATIVE).read_text(encoding="utf-8")
    insertion = (
        "\n### 2099-01-01 · R-000 · Inserted into bound prefix\n\n"
        "- **Situation:** bad\n"
        "- **Rule invoked:** test\n"
        "- **Ruling:** must fail\n"
        "- **Generalises to:** tests\n"
        "- **Decided by:** A + B\n"
        "- **Supersedes:** none\n\n"
    )
    # Insert before the second bound ruling.
    pos = text.index(sections[1].body[:40])
    (root / RULINGS_RELATIVE).write_text(text[:pos] + insertion + text[pos:], encoding="utf-8")
    with pytest.raises(RatificationError, match="reordered|mutated|prefix"):
        assert_rulings_binding_holds(root, bound)


def test_c_no_live_manifest_in_repo() -> None:
    assert not (REPO / MANIFEST_RELATIVE).exists()


def test_c_format_block_example_ignored_in_rulings_parse() -> None:
    text = (REPO / RULINGS_RELATIVE).read_text(encoding="utf-8")
    sections = parse_ruling_sections(text)
    assert all(s.ruling_id.startswith("R-") for s in sections)
    # Example heading uses literal R-NNN and must not appear.
    assert "R-NNN" not in [s.ruling_id for s in sections]


# ---------------------------------------------------------------------------
# D — generic consistency / template tests
# ---------------------------------------------------------------------------


def test_d_navigation_basins_must_be_schema_subset(tmp_path: Path) -> None:
    cfg = _complete_prereg()
    cfg["corridors"]["navigation_basins"] = ["not_a_real_basin"]
    _write_live_cfg(tmp_path, cfg)
    with pytest.raises(DiscoveryConfigError, match="outside episode-schema"):
        load_prereg_rules(tmp_path)


def test_d_sweep_ids_must_be_protocol_families(tmp_path: Path) -> None:
    assert PROTOCOL_SWEEP_FAMILIES == frozenset({f"S{i}" for i in range(1, 9)})
    cfg = _complete_prereg()
    cfg["source_archives"][0]["sweep_id"] = "S9"
    _write_live_cfg(tmp_path, cfg)
    with pytest.raises(DiscoveryConfigError, match="protocol families"):
        load_prereg_rules(tmp_path)


def test_d_ordering_keys_must_exist_in_candidate_schema(tmp_path: Path) -> None:
    cfg = _complete_prereg()
    cfg["candidates"]["ordering_keys"] = ["document_date", "not_a_schema_field"]
    _write_live_cfg(tmp_path, cfg)
    with pytest.raises(DiscoveryConfigError, match="ordering_keys"):
        load_prereg_rules(tmp_path)


def test_d_committed_candidate_schema_supports_validator() -> None:
    schema = yaml.safe_load(
        (REPO / "research/episodes/discovery/candidates/_schema.yaml").read_text(
            encoding="utf-8"
        )
    )
    required = [str(x).split("#", 1)[0].strip() for x in schema["required_fields"]]
    hit = {
        "candidate_id": "CAND-0001",
        "sweep_id": "S1",
        "source_reference": "synthetic-ref",
        "raw_capture_pointer": None,
        "document_date": "2099-01-01",
        "ordering_key": "2099-01-01|synthetic-ref",
    }
    for field in required:
        assert field in hit
    validate_candidate_hit(hit)
    for forbidden in schema["forbidden_fields"]:
        assert forbidden in FORBIDDEN_CANDIDATE_FIELDS


def test_d_committed_coverage_template_validates_when_filled() -> None:
    template = yaml.safe_load(
        (REPO / "research/episodes/discovery/coverage/_template.yaml").read_text(
            encoding="utf-8"
        )
    )
    assert template["record_kind"] == "source_coverage"
    filled = dict(template)
    filled.update(
        {
            "authority": "TEST",
            "district": "TEST",
            "vehicle": "TEST",
            "retrieved_on": "2099-01-01",
            "coverage_status": "absent",
            "sweep_status": "not_attempted",
            "records_matched": None,
        }
    )
    validate_coverage_record(filled)


def test_d_template_declares_analysis_anchor_grid_shape_with_nulls() -> None:
    data = yaml.safe_load(
        (REPO / "config/discovery/_prereg_rules.template.yaml").read_text(encoding="utf-8")
    )
    assert isinstance(data.get("analysis_anchor_grid"), dict)
    for key in ANALYSIS_ANCHOR_GRID_KEYS:
        assert key in data["analysis_anchor_grid"]
        assert data["analysis_anchor_grid"][key] is None
    assert data["capture"]["sweeps_subdir"] is None
    assert data["coverage"]["records_dir"] is None
    assert data["coverage"]["gap_policy_notes"] is None
    assert data["physical_thresholds"]["mode"] is None
    assert data["physical_thresholds"]["class_thresholds"] == []
    assert data["event_windows"]["pre_event_horizon"] is None
    assert data["calibration_set"]["count"] is None
    assert data["concurrent_shocks"]["shock_types"] == []
    assert "severity" not in data and "d12" not in {k.lower() for k in data}


# ---------------------------------------------------------------------------
# E — archive listing adapter
# ---------------------------------------------------------------------------


def test_e_normalize_only_no_mint() -> None:
    rows = normalize_archive_listing(
        [{"source_reference": "a", "document_date": "2099-01-01"}],
        sweep_id="S1",
        ordering_keys=["document_date", "source_reference"],
    )
    assert "candidate_id" not in rows[0]
    assert rows[0]["source_reference"] == "a"


def test_e_listing_to_candidates_valid() -> None:
    listings = [
        {"source_reference": "b", "document_date": "2099-02-01"},
        {"source_reference": "a", "document_date": "2099-01-01"},
    ]
    hits = normalize_and_mint_archive_listing(
        listings,
        sweep_id="S1",
        ordering_keys=["document_date", "source_reference"],
        id_prefix="CAND",
        authority="TEST_AUTH",
        district="TEST_DISTRICT",
        vehicle="TEST_VEHICLE",
        retrieved_on="2099-03-01",
    )
    assert [h.candidate_id for h in hits] == ["CAND-0001", "CAND-0002"]
    assert [h.source_reference for h in hits] == ["a", "b"]


def test_e_source_reference_rejects_non_string() -> None:
    with pytest.raises(ArchiveListingError, match="source_reference"):
        normalize_archive_listing(
            [{"source_reference": 123, "document_date": "2099-01-01"}],
            sweep_id="S1",
            ordering_keys=["document_date", "source_reference"],
        )
    with pytest.raises(ArchiveListingError, match="source_reference"):
        normalize_archive_listing(
            [{"source_reference": True, "document_date": "2099-01-01"}],
            sweep_id="S1",
            ordering_keys=["document_date", "source_reference"],
        )


def test_e_stable_id_rejects_non_string() -> None:
    with pytest.raises(ArchiveListingError, match="stable_source_id"):
        normalize_archive_listing(
            [
                {
                    "source_reference": "ref",
                    "document_date": "2099-01-01",
                    "stable_source_id": 7,
                }
            ],
            sweep_id="S1",
            ordering_keys=["document_date", "source_reference"],
            stable_id_key="stable_source_id",
        )


def test_e_sweep_id_outside_protocol_rejected() -> None:
    with pytest.raises(ArchiveListingError, match="protocol families"):
        normalize_archive_listing(
            [{"source_reference": "a", "document_date": "2099-01-01"}],
            sweep_id="S9",
            ordering_keys=["document_date", "source_reference"],
        )


def test_e_listing_missing_ordering_key_no_positional_fallback() -> None:
    with pytest.raises(ArchiveListingError, match="ordering key"):
        normalize_archive_listing(
            [{"source_reference": "a"}],
            sweep_id="S1",
            ordering_keys=["document_date", "source_reference"],
        )


def test_e_listing_duplicate_ordering_raises() -> None:
    listings = [
        {"source_reference": "same", "document_date": "2099-01-01"},
        {"source_reference": "same", "document_date": "2099-01-01"},
    ]
    with pytest.raises(CandidateIdError, match="duplicate ordering tuple"):
        normalize_and_mint_archive_listing(
            listings,
            sweep_id="S1",
            ordering_keys=["document_date", "source_reference"],
            id_prefix="CAND",
        )


def test_e_listing_stable_id_explicit_and_dedupes() -> None:
    row = {
        "source_reference": "ref",
        "document_date": "2099-01-01",
        "stable_source_id": "SRC-1",
    }
    hits = normalize_and_mint_archive_listing(
        [row, dict(row)],
        sweep_id="S1",
        ordering_keys=["document_date", "source_reference"],
        id_prefix="CAND",
        stable_id_key="stable_source_id",
    )
    assert len(hits) == 1
    with pytest.raises(ArchiveListingError, match="stable_id_key"):
        normalize_archive_listing(
            [{"source_reference": "ref", "document_date": "2099-01-01"}],
            sweep_id="S1",
            ordering_keys=["document_date", "source_reference"],
            stable_id_key="stable_source_id",
        )


def test_e_reversed_listing_identical_ids() -> None:
    listings = [
        {"source_reference": "z", "document_date": "2099-02-01"},
        {"source_reference": "a", "document_date": "2099-01-01"},
    ]
    a = normalize_and_mint_archive_listing(
        listings,
        sweep_id="S1",
        ordering_keys=["document_date", "source_reference"],
        id_prefix="CAND",
    )
    b = normalize_and_mint_archive_listing(
        list(reversed(listings)),
        sweep_id="S1",
        ordering_keys=["document_date", "source_reference"],
        id_prefix="CAND",
    )
    assert [h.candidate_id for h in a] == [h.candidate_id for h in b]
    assert [h.source_reference for h in a] == [h.source_reference for h in b]

# ---------------------------------------------------------------------------
# Pass-3 regressions (defects 1-9 + requested extras)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("bad", [False, 0, 1.5, [], {}])
@pytest.mark.parametrize("key", list(ANALYSIS_ANCHOR_GRID_KEYS))
def test_a_d13_rejects_non_string_scalars(tmp_path: Path, key: str, bad) -> None:
    cfg = _complete_prereg()
    cfg["analysis_anchor_grid"][key] = bad
    _write_live_cfg(tmp_path, cfg)
    with pytest.raises(DiscoveryConfigError, match=key):
        load_prereg_rules(tmp_path)


@pytest.mark.parametrize("bad", [0, "false", None])
def test_a_case_sensitive_rejects_non_bool(tmp_path: Path, bad) -> None:
    cfg = _complete_prereg()
    cfg["keyword_policy"]["case_sensitive"] = bad
    _write_live_cfg(tmp_path, cfg)
    with pytest.raises(DiscoveryConfigError, match="case_sensitive"):
        load_prereg_rules(tmp_path)


@pytest.mark.parametrize(
    "bad_key",
    ["candidate_id", "ordering_key", "price", "unknown_field", "", 1],
)
def test_a_ordering_keys_reject_invalid(tmp_path: Path, bad_key) -> None:
    cfg = _complete_prereg()
    cfg["candidates"]["ordering_keys"] = ["document_date", bad_key]
    _write_live_cfg(tmp_path, cfg)
    with pytest.raises(DiscoveryConfigError, match="ordering_keys"):
        load_prereg_rules(tmp_path)


def test_a_ordering_keys_reject_duplicate(tmp_path: Path) -> None:
    cfg = _complete_prereg()
    cfg["candidates"]["ordering_keys"] = ["document_date", "document_date"]
    _write_live_cfg(tmp_path, cfg)
    with pytest.raises(DiscoveryConfigError, match="duplicate"):
        load_prereg_rules(tmp_path)


@pytest.mark.parametrize("bad", ["candidate_id", "ordering_key", "price", "sweep_id", ""])
def test_a_stable_id_key_rejects_invalid(tmp_path: Path, bad) -> None:
    cfg = _complete_prereg()
    cfg["candidates"]["stable_id_key"] = bad
    _write_live_cfg(tmp_path, cfg)
    with pytest.raises(DiscoveryConfigError, match="stable_id_key"):
        load_prereg_rules(tmp_path)


def test_a_timezone_false_rejected(tmp_path: Path) -> None:
    cfg = _complete_prereg()
    cfg["analysis_anchor_grid"]["timezone"] = False
    _write_live_cfg(tmp_path, cfg)
    with pytest.raises(DiscoveryConfigError, match="timezone"):
        load_prereg_rules(tmp_path)


def test_e_ordering_key_price_rejected() -> None:
    with pytest.raises(ArchiveListingError, match="forbidden|ordering_keys|price"):
        normalize_archive_listing(
            [{"source_reference": "a", "price": "SECRET"}],
            sweep_id="S1",
            ordering_keys=["price"],
        )


@pytest.mark.parametrize(
    "bad_key",
    ["candidate_id", "ordering_key", "price", "unknown_field", "", "document_date"],
)
def test_e_ordering_keys_reject_invalid_and_duplicate(bad_key) -> None:
    keys = (
        ["document_date", bad_key]
        if bad_key != "document_date"
        else ["document_date", "document_date"]
    )
    with pytest.raises(
        ArchiveListingError,
        match="ordering_keys|duplicate|forbidden|post-mint|unknown",
    ):
        normalize_archive_listing(
            [{"source_reference": "a", "document_date": "2099-01-01"}],
            sweep_id="S1",
            ordering_keys=keys,
        )


def test_e_stable_id_key_rejects_forbidden() -> None:
    with pytest.raises(
        ArchiveListingError,
        match="stable_id_key|forbidden|unknown|post-mint",
    ):
        normalize_archive_listing(
            [
                {
                    "source_reference": "a",
                    "document_date": "2099-01-01",
                    "price": "x",
                }
            ],
            sweep_id="S1",
            ordering_keys=["document_date", "source_reference"],
            stable_id_key="price",
        )


def test_b_missing_family_cannot_compute_exposure() -> None:
    row = _base_identity(
        coverage_status="present",
        endpoint="https://example.invalid/a",
        sweep_status="enumerated",
        records_matched=0,
        scope_start="2015-01-01",
        scope_end="2015-12-31",
    )
    del row["source_family"]
    with pytest.raises(CoverageValidationError, match="source_family"):
        _exposure([row])


def test_b_peer_missing_family_not_inferred_as_s1() -> None:
    rows = [
        _base_identity(
            source_family="S1",
            coverage_status="present",
            endpoint="https://example.invalid/a",
            sweep_status="enumerated",
            records_matched=0,
            scope_start="2015-01-01",
            scope_end="2015-12-31",
        ),
        _base_identity(
            coverage_status="absent",
            endpoint="https://example.invalid/a",
            sweep_status="not_attempted",
            scope_start="2015-06-01",
            scope_end="2015-06-30",
        ),
    ]
    del rows[1]["source_family"]
    with pytest.raises(CoverageValidationError, match="source_family"):
        _exposure(rows)


def test_b_invalid_family_and_identity_types_raise_coverage_error() -> None:
    with pytest.raises(CoverageValidationError):
        _exposure([_base_identity(source_family=1, coverage_status="absent")])
    with pytest.raises(CoverageValidationError):
        compute_covered_exposure(
            [_base_identity(coverage_status="absent")],
            absence_generating_families=[1],
            source_identity_keys=_TEST_IDENTITY_KEYS,
            sample_start="2010-01-01",
            sample_end="2020-12-31",
        )
    with pytest.raises(CoverageValidationError):
        compute_covered_exposure(
            [_base_identity(coverage_status="absent")],
            absence_generating_families=_TEST_ABSENCE_FAMILIES,
            source_identity_keys=["authority", "not_allowed"],
            sample_start="2010-01-01",
            sample_end="2020-12-31",
        )


def test_b_earliest_latest_reverse_rejects() -> None:
    with pytest.raises(CoverageValidationError, match="earliest_available"):
        validate_coverage_record(
            _base_identity(
                coverage_status="present",
                endpoint="https://example.invalid",
                sweep_status="not_attempted",
                earliest_available="2020-01-01",
                latest_available="2010-01-01",
            )
        )


def test_c_fenced_content_inside_real_ruling_changes_digest(tmp_path: Path) -> None:
    root = _build_ratified_repo(tmp_path)
    bound = build_rulings_binding(root)
    rulings_path = root / RULINGS_RELATIVE
    text = rulings_path.read_text(encoding="utf-8")
    sections = parse_ruling_sections(text)
    body = sections[0].body
    insertion = "\n```\nMUTATED_FENCE_BODY\n```\n"
    lines = body.splitlines(keepends=True)
    new_body = lines[0] + insertion + "".join(lines[1:])
    rulings_path.write_text(text.replace(body, new_body, 1), encoding="utf-8")
    with pytest.raises(RatificationError, match="digest drift|mutated"):
        assert_rulings_binding_holds(root, bound)


def test_c_duplicate_ruling_ids_rejected(tmp_path: Path) -> None:
    root = _build_ratified_repo(tmp_path)
    rulings_path = root / RULINGS_RELATIVE
    text = rulings_path.read_text(encoding="utf-8")
    sections = parse_ruling_sections(text)
    rulings_path.write_text(text + "\n" + sections[0].body, encoding="utf-8")
    with pytest.raises(RatificationError, match="duplicate"):
        build_rulings_binding(root)


def test_c_false_rulings_path_rejected(tmp_path: Path) -> None:
    root = _build_ratified_repo(tmp_path)
    binding = build_rulings_binding(root)
    binding["path"] = "research/episodes/NOT_RULINGS.md"
    with pytest.raises(RatificationError, match="path"):
        assert_rulings_binding_holds(root, binding)
    with pytest.raises(RatificationError, match="path"):
        serialize_ratification_manifest(
            {**build_ratification_manifest(root), "rulings_binding": binding}
        )


def test_c_missing_extra_ruling_digest_rejected(tmp_path: Path) -> None:
    root = _build_ratified_repo(tmp_path)
    binding = build_rulings_binding(root)
    digests = dict(binding["ruling_digests"])
    first = binding["bound_ruling_ids"][0]
    del digests[first]
    bad_missing = {**binding, "ruling_digests": digests}
    with pytest.raises(RatificationError, match="missing|digests"):
        assert_rulings_binding_holds(root, bad_missing)
    digests2 = dict(binding["ruling_digests"])
    digests2["R-998"] = "abc"
    bad_extra = {**binding, "ruling_digests": digests2}
    with pytest.raises(RatificationError, match="extra|digests"):
        assert_rulings_binding_holds(root, bad_extra)


@pytest.mark.parametrize("adr_rel", list(LOAD_BEARING_ADR_RELATIVE_PATHS))
def test_c_proposed_load_bearing_adr_blocks_build_and_auth(
    tmp_path: Path, adr_rel: str
) -> None:
    root = _build_ratified_repo(tmp_path)
    _write_accepted_adr(root / adr_rel, status="proposed")
    _git(root, "add", "-A")
    _git(root, "commit", "-m", "propose-load-bearing-adr")
    with pytest.raises(RatificationError, match="accepted"):
        build_ratification_manifest(root)
    with pytest.raises(RatificationError, match="accepted|digest drift"):
        assert_sweep_authorized(root)


def test_c_good_fixture_accepts_every_load_bearing_adr(tmp_path: Path) -> None:
    root = _build_ratified_repo(tmp_path)
    for rel in LOAD_BEARING_ADR_RELATIVE_PATHS:
        text = (root / rel).read_text(encoding="utf-8").lower().replace(" ", "")
        assert "**status:**accepted" in text
    assert_sweep_authorized(root)


def test_c_canonical_rulings_path_constant() -> None:
    assert RULINGS_PATH_CANONICAL == "research/episodes/RULINGS.md"


# ---------------------------------------------------------------------------
# Pass-4A regressions — fail-closed defects
# ---------------------------------------------------------------------------


def test_pass4a_rulings_trailing_blank_canonicalize_stable() -> None:
    body = (
        "### 2099-01-01 · R-777 · Canonicalize fixture\n"
        "- **Situation:** trailing blanks\n"
        "- **Rule invoked:** test\n"
        "- **Ruling:** keep interior  \n"
        "- **Generalises to:** tests\n"
        "- **Decided by:** A + B\n"
        "- **Supersedes:** none\n"
        "\n\n"
    )
    sections = parse_ruling_sections(body)
    assert sections[0].body.endswith("\n")
    assert not sections[0].body.endswith("\n\n")
    assert "interior  \n" in sections[0].body
    assert sections[0].digest == parse_ruling_sections(body + "\n\n")[0].digest


def test_pass4a_manifest_clean_build_and_determinism(tmp_path: Path) -> None:
    root = _build_ratified_repo(tmp_path)
    a = emit_ratification_manifest_bytes(root)
    b = emit_ratification_manifest_bytes(root)
    assert a == b
    doc = yaml.safe_load(a)
    assert re.fullmatch(r"[0-9a-f]{64}", doc["prereg_config_digest"])
    for digest in doc["interpretation_digests"].values():
        assert re.fullmatch(r"[0-9a-f]{64}", digest)
    for digest in doc["rulings_binding"]["ruling_digests"].values():
        assert re.fullmatch(r"[0-9a-f]{64}", digest)


def test_pass4a_manifest_crlf_drift_blocks_build(tmp_path: Path) -> None:
    root = _build_ratified_repo(tmp_path)
    target = root / "src/grainsys/discovery/config.py"
    lf = target.read_bytes()
    assert b"\r\n" not in lf
    target.write_bytes(lf.replace(b"\n", b"\r\n"))
    with pytest.raises(RatificationError, match="working tree drift|CRLF|fresh normalized"):
        build_ratification_manifest(root)


def test_pass4a_manifest_rejects_malformed_and_extra_keys(tmp_path: Path) -> None:
    root = _build_ratified_repo(tmp_path)
    base = build_ratification_manifest(root)
    with pytest.raises(RatificationError, match="unknown top-level"):
        serialize_ratification_manifest({**base, "extra_key": "nope"})
    with pytest.raises(RatificationError, match="prereg_config_digest|sha256|hex"):
        serialize_ratification_manifest({**base, "prereg_config_digest": "A" * 64})
    with pytest.raises(RatificationError, match="prereg_config_digest|refuse coercion"):
        serialize_ratification_manifest({**base, "prereg_config_digest": 123})
    bad_interp = dict(base["interpretation_digests"])
    bad_interp["docs/decisions/0004-not-real.md"] = "a" * 64
    with pytest.raises(RatificationError, match="extra|interpretation"):
        serialize_ratification_manifest({**base, "interpretation_digests": bad_interp})
    missing_interp = dict(base["interpretation_digests"])
    del missing_interp[LOAD_BEARING_RELATIVE_PATHS[0]]
    with pytest.raises(RatificationError, match="missing|interpretation"):
        serialize_ratification_manifest({**base, "interpretation_digests": missing_interp})


def test_pass4a_capture_path_attacks_and_valid(tmp_path: Path) -> None:
    data = tmp_path / "data"
    data.mkdir()
    ok = candidate_capture_dir(
        sweep_id="S1",
        candidate_id="CAND-0001",
        data_root_path=data,
        sweeps_subdir="sweeps",
    )
    assert ok == data / "sweeps" / "S1" / "CAND-0001"
    nested = sweeps_root(data_root_path=data, sweeps_subdir="phase1/sweeps")
    assert nested == data / "phase1" / "sweeps"

    attacks = [
        {"sweep_id": True, "candidate_id": "CAND-0001", "sweeps_subdir": "sweeps"},
        {"sweep_id": "S1", "candidate_id": False, "sweeps_subdir": "sweeps"},
        {"sweep_id": "..", "candidate_id": "CAND-0001", "sweeps_subdir": "sweeps"},
        {"sweep_id": "S1", "candidate_id": ".", "sweeps_subdir": "sweeps"},
        {"sweep_id": "a/b", "candidate_id": "CAND-0001", "sweeps_subdir": "sweeps"},
        {"sweep_id": "S1", "candidate_id": "x\\y", "sweeps_subdir": "sweeps"},
        {"sweep_id": "S1", "candidate_id": "CAND-0001", "sweeps_subdir": "../x"},
        {"sweep_id": "S1", "candidate_id": "CAND-0001", "sweeps_subdir": "/abs"},
        {"sweep_id": "S1", "candidate_id": "CAND-0001", "sweeps_subdir": "C:/windows"},
        {"sweep_id": "S1\x00", "candidate_id": "CAND-0001", "sweeps_subdir": "sweeps"},
    ]
    for kwargs in attacks:
        with pytest.raises(CapturePathError):
            candidate_capture_dir(data_root_path=data, **kwargs)


def test_pass4a_config_path_safety(tmp_path: Path) -> None:
    cfg = _complete_prereg()
    cfg["candidates"]["table_path"] = "../outside.csv"
    _write_live_cfg(tmp_path, cfg)
    with pytest.raises(DiscoveryConfigError, match="table_path"):
        load_prereg_rules(tmp_path)
    cfg = _complete_prereg()
    cfg["candidates"]["id_prefix"] = "CAND/../x"
    _write_live_cfg(tmp_path, cfg)
    with pytest.raises(DiscoveryConfigError, match="id_prefix"):
        load_prereg_rules(tmp_path)
    cfg = _complete_prereg()
    cfg["capture"]["sweeps_subdir"] = "..\\escape"
    _write_live_cfg(tmp_path, cfg)
    with pytest.raises(DiscoveryConfigError, match="sweeps_subdir"):
        load_prereg_rules(tmp_path)
    cfg = _complete_prereg()
    cfg["coverage"]["records_dir"] = "/abs/coverage"
    _write_live_cfg(tmp_path, cfg)
    with pytest.raises(DiscoveryConfigError, match="records_dir"):
        load_prereg_rules(tmp_path)


@pytest.mark.parametrize(
    "stable_id_key",
    ["notice_id", "source_reference", "stable_source_id"],
)
def test_pass4a_custom_stable_id_key_copies_to_stable_source_id(stable_id_key: str) -> None:
    base = {
        "source_reference": "ref-a",
        "document_date": "2099-01-01",
    }
    if stable_id_key == "notice_id":
        base["notice_id"] = "N-1"
    elif stable_id_key == "stable_source_id":
        base["stable_source_id"] = "SSID-1"
    listings = [dict(base), dict(base)]
    hits = normalize_and_mint_archive_listing(
        listings,
        sweep_id="S1",
        ordering_keys=["document_date", "source_reference"],
        id_prefix="CAND",
        stable_id_key=stable_id_key,
    )
    assert len(hits) == 1
    expected = listings[0][stable_id_key]
    assert hits[0].stable_source_id == expected
    assert "notice_id" not in hits[0].to_dict()


@pytest.mark.parametrize(
    "bad_key",
    ["sweep_id", "candidate_id", "ordering_key", "price", "../x", "a/b", True],
)
def test_pass4a_stable_id_key_rejects_reserved_unsafe(bad_key) -> None:
    with pytest.raises(ArchiveListingError, match="stable_id_key"):
        normalize_archive_listing(
            [
                {
                    "source_reference": "a",
                    "document_date": "2099-01-01",
                    "sweep_id": "S1",
                    "price": "x",
                    "candidate_id": "c",
                    "ordering_key": "o",
                    "../x": "bad",
                    "a/b": "bad",
                }
            ],
            sweep_id="S1",
            ordering_keys=["document_date", "source_reference"],
            stable_id_key=bad_key,
        )


def test_pass4a_invalid_listing_containers_raise() -> None:
    with pytest.raises(ArchiveListingError, match="listings"):
        normalize_archive_listing(
            "not-a-sequence",  # type: ignore[arg-type]
            sweep_id="S1",
            ordering_keys=["document_date"],
        )
    with pytest.raises(ArchiveListingError, match="ordering_keys"):
        normalize_archive_listing(
            [{"source_reference": "a", "document_date": "2099-01-01"}],
            sweep_id="S1",
            ordering_keys="document_date",  # type: ignore[arg-type]
        )


# ---------------------------------------------------------------------------
# Pass-4B regressions
# ---------------------------------------------------------------------------


def test_pass4b_unknown_and_duplicate_config_keys(tmp_path: Path) -> None:
    cfg = _complete_prereg()
    cfg["unexpected_top_level"] = "nope"
    _write_live_cfg(tmp_path, cfg)
    with pytest.raises(DiscoveryConfigError, match="unknown keys"):
        load_prereg_rules(tmp_path)
    cfg = _complete_prereg()
    cfg["sample_period"]["start_date"] = "2099-01-01"
    _write_live_cfg(tmp_path, cfg)
    with pytest.raises(DiscoveryConfigError, match="unknown keys"):
        load_prereg_rules(tmp_path)
    live = tmp_path / "config" / "discovery" / "prereg_rules.yaml"
    _seed_load_bearing(tmp_path)
    live.parent.mkdir(parents=True, exist_ok=True)
    dumped = yaml.safe_dump(_complete_prereg())
    live.write_text("governing_adr: x\n" + dumped, encoding="utf-8")
    with pytest.raises(DiscoveryConfigError, match="duplicate"):
        load_prereg_rules(tmp_path)


def test_pass4b_untrimmed_string_rejected(tmp_path: Path) -> None:
    cfg = _complete_prereg()
    cfg["governing_adr"] = " docs/decisions/0003-phase0-prereg-hardening.md"
    _write_live_cfg(tmp_path, cfg)
    with pytest.raises(DiscoveryConfigError, match="untrimmed"):
        load_prereg_rules(tmp_path)


@pytest.mark.parametrize(
    "block",
    ["physical_thresholds", "event_windows", "calibration_set", "concurrent_shocks"],
)
def test_pass4b_missing_lock1_block(tmp_path: Path, block: str) -> None:
    cfg = _complete_prereg()
    del cfg[block]
    _write_live_cfg(tmp_path, cfg)
    with pytest.raises(DiscoveryConfigError, match=block):
        load_prereg_rules(tmp_path)


def test_pass4b_missing_target_date_mapping(tmp_path: Path) -> None:
    cfg = _complete_prereg()
    del cfg["analysis_anchor_grid"]["target_date_mapping"]
    _write_live_cfg(tmp_path, cfg)
    with pytest.raises(DiscoveryConfigError, match="target_date_mapping"):
        load_prereg_rules(tmp_path)


def test_pass4b_duplicate_archives_rejected(tmp_path: Path) -> None:
    cfg = _complete_prereg()
    cfg["source_archives"] = [cfg["source_archives"][0], dict(cfg["source_archives"][0])]
    _write_live_cfg(tmp_path, cfg)
    with pytest.raises(DiscoveryConfigError, match="duplicates archive identity"):
        load_prereg_rules(tmp_path)


def test_pass4b_gap_policy_notes_required(tmp_path: Path) -> None:
    cfg = _complete_prereg()
    cfg["coverage"]["gap_policy_notes"] = None
    _write_live_cfg(tmp_path, cfg)
    with pytest.raises(DiscoveryConfigError, match="gap_policy_notes"):
        load_prereg_rules(tmp_path)


def test_pass4b_d6_d7_null_paths_fail_closed(tmp_path: Path) -> None:
    cfg = _complete_prereg()
    cfg["capture"]["sweeps_subdir"] = None
    _write_live_cfg(tmp_path, cfg)
    with pytest.raises(DiscoveryConfigError, match="sweeps_subdir"):
        load_prereg_rules(tmp_path)
    cfg = _complete_prereg()
    cfg["coverage"]["records_dir"] = None
    _write_live_cfg(tmp_path, cfg)
    with pytest.raises(DiscoveryConfigError, match="records_dir"):
        load_prereg_rules(tmp_path)


def test_pass4b_archive_context_conflict_and_unknown_price() -> None:
    with pytest.raises(ArchiveListingError, match="conflicts with registered"):
        normalize_archive_listing(
            [
                {
                    "source_reference": "a",
                    "document_date": "2099-01-01",
                    "authority": "OTHER",
                }
            ],
            sweep_id="S1",
            ordering_keys=["document_date", "source_reference"],
            authority="REGISTERED",
        )
    with pytest.raises(ArchiveListingError, match="unknown/contamination"):
        normalize_archive_listing(
            [
                {
                    "source_reference": "a",
                    "document_date": "2099-01-01",
                    "price": "SECRET",
                }
            ],
            sweep_id="S1",
            ordering_keys=["document_date", "source_reference"],
        )


def test_pass4b_sample_period_clips_exposure() -> None:
    rows = [
        _base_identity(
            coverage_status="present",
            endpoint="https://example.invalid/a",
            sweep_status="enumerated",
            records_matched=0,
            scope_start="2014-01-01",
            scope_end="2016-12-31",
        )
    ]
    exposure = _exposure(rows, sample_start="2015-01-01", sample_end="2015-12-31")
    assert [iv.to_pair() for iv in exposure[0].intervals] == [
        ("2015-01-01", "2015-12-31")
    ]


def test_pass4b_coverage_unknown_key_rejected() -> None:
    row = _base_identity(coverage_status="absent")
    row["unexpected_field"] = "x"
    with pytest.raises(CoverageValidationError, match="unknown keys"):
        validate_coverage_record(row)


# ---------------------------------------------------------------------------
# D7 empty-absence amendment (ADR-0003 N3 amendment)
# ---------------------------------------------------------------------------


def test_d7_empty_absence_generating_families_accepted(tmp_path: Path) -> None:
    """Empty absence_generating_families is valid per D7 amendment."""
    cfg = _complete_prereg()
    cfg["coverage"]["absence_generating_families"] = []
    _write_live_cfg(tmp_path, cfg)
    loaded = load_prereg_rules(tmp_path)
    assert loaded["coverage"]["absence_generating_families"] == []


def test_d7_valid_nonempty_s1_s8_subset_still_accepted(tmp_path: Path) -> None:
    """Valid nonempty S1-S8 subsets remain accepted."""
    cfg = _complete_prereg()
    cfg["coverage"]["absence_generating_families"] = ["S1", "S3", "S8"]
    _write_live_cfg(tmp_path, cfg)
    loaded = load_prereg_rules(tmp_path)
    assert loaded["coverage"]["absence_generating_families"] == ["S1", "S3", "S8"]


def test_d7_duplicate_family_still_rejected(tmp_path: Path) -> None:
    """Duplicates in absence_generating_families still fail closed."""
    cfg = _complete_prereg()
    cfg["coverage"]["absence_generating_families"] = ["S1", "S1"]
    _write_live_cfg(tmp_path, cfg)
    with pytest.raises(DiscoveryConfigError, match="duplicate"):
        load_prereg_rules(tmp_path)


def test_d7_invalid_family_still_rejected(tmp_path: Path) -> None:
    """Invalid family names still fail closed."""
    cfg = _complete_prereg()
    cfg["coverage"]["absence_generating_families"] = ["S1", "NOT_A_FAMILY"]
    _write_live_cfg(tmp_path, cfg)
    with pytest.raises(DiscoveryConfigError, match="outside S1–S8"):
        load_prereg_rules(tmp_path)


def test_d7_out_of_range_family_still_rejected(tmp_path: Path) -> None:
    """S9 and beyond are outside protocol families and still fail closed."""
    cfg = _complete_prereg()
    cfg["coverage"]["absence_generating_families"] = ["S9"]
    _write_live_cfg(tmp_path, cfg)
    with pytest.raises(DiscoveryConfigError, match="outside S1–S8"):
        load_prereg_rules(tmp_path)


@pytest.mark.parametrize("bad", [None, "S1", 1, {"S1": True}])
def test_d7_non_list_absence_generating_families_rejected(
    tmp_path: Path, bad
) -> None:
    """Non-list values for absence_generating_families still fail closed."""
    cfg = _complete_prereg()
    cfg["coverage"]["absence_generating_families"] = bad
    _write_live_cfg(tmp_path, cfg)
    with pytest.raises(DiscoveryConfigError, match="absence_generating_families"):
        load_prereg_rules(tmp_path)


@pytest.mark.parametrize("bad_entry", [None, 1, True, [], {}])
def test_d7_non_string_family_entry_rejected(tmp_path: Path, bad_entry) -> None:
    """Non-string entries in nonempty absence_generating_families fail closed."""
    cfg = _complete_prereg()
    cfg["coverage"]["absence_generating_families"] = ["S1", bad_entry]
    _write_live_cfg(tmp_path, cfg)
    with pytest.raises(DiscoveryConfigError, match="absence_generating_families"):
        load_prereg_rules(tmp_path)


def test_d7_untrimmed_family_rejected(tmp_path: Path) -> None:
    """Untrimmed strings in absence_generating_families fail closed."""
    cfg = _complete_prereg()
    cfg["coverage"]["absence_generating_families"] = [" S1"]
    _write_live_cfg(tmp_path, cfg)
    with pytest.raises(DiscoveryConfigError, match="untrimmed"):
        load_prereg_rules(tmp_path)


@pytest.mark.parametrize(
    "bad",
    ["CON", "PRN", "AUX", "NUL", "COM1", "LPT9", "CON.txt", "com1.foo", "file."],
)
def test_pass4b_windows_device_and_trailing_dot_rejected(bad: str) -> None:
    with pytest.raises(DiscoveryConfigError, match="device|trailing-dot|unsafe"):
        require_safe_path_component(bad, field="id_prefix")


def test_pass4b_execution_commit_mismatch_rejected(tmp_path: Path) -> None:
    root = _build_ratified_repo(tmp_path)
    (root / "unrelated.txt").write_text("x\n", encoding="utf-8")
    _git(root, "add", "-A")
    _git(root, "commit", "-m", "unrelated")
    head = _git(root, "rev-parse", "HEAD").stdout.strip().lower()
    parent = _git(root, "rev-parse", "HEAD^").stdout.strip().lower()
    assert_sweep_authorized(root, execution_commit=head)
    with pytest.raises(RatificationError, match="actual HEAD|execution_commit"):
        assert_sweep_authorized(root, execution_commit=parent)


def test_pass4b_restored_working_tree_over_drifted_head_blocks(tmp_path: Path) -> None:
    root = _build_ratified_repo(tmp_path)
    rel = "src/grainsys/discovery/coverage.py"
    target = root / rel
    old_bytes = target.read_bytes()
    target.write_bytes(old_bytes + b"\n# committed-drift\n")
    _git(root, "add", "-A")
    _git(root, "commit", "-m", "committed-drift")
    target.write_bytes(old_bytes)
    with pytest.raises(RatificationError, match="working tree drift|fresh normalized"):
        assert_sweep_authorized(root)


def test_pass4b_malformed_provenance_rejected() -> None:
    digest = "a" * 64
    sha = "b" * 40
    with pytest.raises(RatificationError, match="prereg_tag"):
        make_sweep_provenance(
            prereg_config_digest=digest,
            execution_commit_sha=sha,
            governing_adr="docs/decisions/0003-phase0-prereg-hardening.md",
            prereg_tag="wrong-tag",
        )
    with pytest.raises(RatificationError, match="40-hex"):
        make_sweep_provenance(
            prereg_config_digest=digest,
            execution_commit_sha="A" * 40,
            governing_adr="docs/decisions/0003-phase0-prereg-hardening.md",
        )
