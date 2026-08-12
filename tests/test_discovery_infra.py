"""Contamination-safe discovery infrastructure tests (no live episode content)."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
import yaml

from grainsys.discovery.candidates import (
    FORBIDDEN_CANDIDATE_FIELDS,
    CandidateIdError,
    CandidateValidationError,
    mint_candidate_ids,
    validate_candidate_hit,
)
from grainsys.discovery.capture import CapturePathError, candidate_capture_dir, sweeps_root
from grainsys.discovery.config import DiscoveryConfigError, load_prereg_rules, prereg_rules_path
from grainsys.discovery.coverage import (
    FORBIDDEN_COVERAGE_FIELDS,
    CoverageValidationError,
    validate_coverage_record,
)
from grainsys.discovery.governance import (
    LOAD_BEARING_RELATIVE_PATHS,
    MANIFEST_RELATIVE,
    PREREG_TAG,
    RatificationError,
    assert_sweep_authorized,
    build_interpretation_digests,
    make_sweep_provenance,
    sha256_file,
)
from grainsys.discovery.sweep import SweepEnumerator, SweepError

REPO = Path(__file__).resolve().parents[1]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _base_identity(**overrides):
    row = {
        "authority": "TEST",
        "district": "TEST",
        "vehicle": "TEST",
        "retrieved_on": "2026-01-01",
        "coverage_status": "absent",
        "sweep_status": "not_attempted",
        "records_matched": None,
    }
    row.update(overrides)
    return row


def _complete_prereg(**overrides) -> dict:
    data = {
        "governing_adr": "docs/decisions/0003-phase0-prereg-hardening.md",
        "sample_period": {"sample_start": "TO_BE_SET", "sample_end": "TO_BE_SET"},
        "corridors": {"navigation_basins": ["TO_BE_SET"]},
        "source_archives": [
            {
                "sweep_id": "S_TEST",
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
        "capture": {"sweeps_subdir": "sweeps", "rehome_policy": None},
        "coverage": {
            "records_dir": "research/episodes/discovery/coverage",
            "absent_must_be_explicit": True,
            "gap_policy_notes": None,
        },
    }
    data.update(overrides)
    return data


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
    for rel in LOAD_BEARING_RELATIVE_PATHS:
        src = src_root / rel
        dst = dst_root / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        if src.is_file():
            dst.write_bytes(src.read_bytes())
        else:
            dst.write_text(f"# stub {rel}\n", encoding="utf-8")


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

    _seed_load_bearing(root)
    adr_rel = Path("docs/decisions/0003-phase0-prereg-hardening.md")
    _write_accepted_adr(root / adr_rel, status=adr_status)

    cfg = _complete_prereg(governing_adr=adr_rel.as_posix())
    cfg_path = root / "config" / "discovery" / "prereg_rules.yaml"
    cfg_path.parent.mkdir(parents=True, exist_ok=True)
    cfg_path.write_text(yaml.safe_dump(cfg), encoding="utf-8")

    manifest = {
        "prereg_config_digest": sha256_file(cfg_path),
        "governing_adr": adr_rel.as_posix(),
        "interpretation_digests": build_interpretation_digests(root),
    }
    man_path = root / MANIFEST_RELATIVE
    man_path.write_text(yaml.safe_dump(manifest), encoding="utf-8")

    _git(root, "add", "-A")
    _git(root, "commit", "-m", "ratify")
    if create_tag:
        _git(root, "tag", PREREG_TAG)

    if mutate_config_after_tag:
        cfg["sample_period"]["sample_end"] = "MUTATED"
        cfg_path.write_text(yaml.safe_dump(cfg), encoding="utf-8")
        _git(root, "add", "-A")
        _git(root, "commit", "-m", "mutate-config")

    if mutate_interpretation_after_tag:
        target = root / "src/grainsys/discovery/governance.py"
        target.write_text(target.read_text(encoding="utf-8") + "\n# drift\n", encoding="utf-8")
        _git(root, "add", "-A")
        _git(root, "commit", "-m", "mutate-interp")

    if mutate_adr0005_after_tag:
        target = root / "docs/decisions/0005-source-handling-and-vintage-rules.md"
        target.write_text(target.read_text(encoding="utf-8") + "\n# adr0005-drift\n", encoding="utf-8")
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


def test_repo_has_no_live_prereg_rules() -> None:
    live = prereg_rules_path(REPO)
    assert not live.exists(), "Do not commit invented prereg_rules.yaml yet"
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
    assert "research/episodes/episode_schema.yaml" not in LOAD_BEARING_RELATIVE_PATHS
    assert adr4_inference not in LOAD_BEARING_RELATIVE_PATHS

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


def test_n3_blocks_when_head_not_descendant(tmp_path: Path) -> None:
    root = _build_ratified_repo(tmp_path, orphan_head=True)
    with pytest.raises(RatificationError, match="descendant"):
        assert_sweep_authorized(root)


def test_n3_provenance_helper_ready() -> None:
    stamp = make_sweep_provenance(
        prereg_config_digest="abc",
        execution_commit_sha="def",
        governing_adr="docs/decisions/0003-phase0-prereg-hardening.md",
    )
    assert stamp.to_dict()["prereg_tag"] == PREREG_TAG
    with pytest.raises(RatificationError):
        make_sweep_provenance(
            prereg_config_digest="",
            execution_commit_sha="def",
            governing_adr="x",
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
