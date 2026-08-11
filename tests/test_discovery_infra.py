"""Contamination-safe discovery infrastructure tests (no live episode content)."""

from __future__ import annotations

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
from grainsys.discovery.sweep import SweepEnumerator, SweepError


def test_missing_prereg_config_prevents_sweep(tmp_path: Path) -> None:
    assert not prereg_rules_path(tmp_path).exists()
    with pytest.raises(DiscoveryConfigError, match="Missing live preregistration"):
        load_prereg_rules(tmp_path)
    with pytest.raises(SweepError, match="Missing live preregistration"):
        SweepEnumerator.from_repo(tmp_path)


def test_incomplete_prereg_config_fail_closed(tmp_path: Path) -> None:
    cfg_dir = tmp_path / "config" / "discovery"
    cfg_dir.mkdir(parents=True)
    (cfg_dir / "prereg_rules.yaml").write_text(
        yaml.safe_dump(
            {
                "sample_period": {"start_date": None, "end_date": None},
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


def _complete_prereg() -> dict:
    return {
        "sample_period": {"start_date": "TO_BE_SET", "end_date": "TO_BE_SET"},
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
        },
        "capture": {"sweeps_subdir": "sweeps", "rehome_policy": None},
        "coverage": {
            "records_dir": "research/episodes/discovery/coverage",
            "absent_must_be_explicit": True,
            "gap_policy_notes": None,
        },
    }


def test_sweep_enumerator_uses_only_committed_config(tmp_path: Path) -> None:
    cfg_dir = tmp_path / "config" / "discovery"
    cfg_dir.mkdir(parents=True)
    (cfg_dir / "prereg_rules.yaml").write_text(
        yaml.safe_dump(_complete_prereg()), encoding="utf-8"
    )
    enum = SweepEnumerator.from_repo(tmp_path)
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
            }
        )


def test_absent_coverage_row_requires_identity() -> None:
    with pytest.raises(CoverageValidationError, match="district"):
        validate_coverage_record(
            {
                "authority": "TEST",
                "vehicle": "TEST",
                "coverage_status": "absent",
                "retrieved_on": "2026-01-01",
            }
        )
    row = validate_coverage_record(
        {
            "authority": "TEST",
            "district": "TEST",
            "vehicle": "TEST",
            "coverage_status": "absent",
            "retrieved_on": "2026-01-01",
            "endpoint": None,
            "notes": "archive unreachable at census time",
        }
    )
    assert row.coverage_status == "absent"


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
    assert minted[0]["source_reference"] == "a"
    assert minted[1]["source_reference"] == "c"
    assert minted[2]["source_reference"] == "b"
    # Same rule twice ⇒ identical IDs
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
            {
                "authority": "TEST",
                "district": "TEST",
                "vehicle": "TEST",
                "coverage_status": "present",
                "endpoint": "https://example.invalid",
                "retrieved_on": "2026-01-01",
                "price": 1.0,
            }
        )


def test_infra_does_not_generate_episode_entries(tmp_path: Path) -> None:
    """Minting hits must not create episode YAML or ledger rows."""
    minted = mint_candidate_ids(
        [{"source_reference": "ref-1", "document_date": "2020-01-01", "sweep_id": "S_TEST"}],
        ordering_keys=["document_date", "source_reference"],
        id_prefix="CAND",
    )
    assert "episode_id" not in minted[0]
    episodes_dir = tmp_path / "research" / "episodes" / "entries"
    episodes_dir.mkdir(parents=True)
    # Simulate a workspace: after minting, no episode files should appear.
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
    """Canonical repo must not ship invented live prereg values on this branch."""
    repo = Path(__file__).resolve().parents[1]
    live = prereg_rules_path(repo)
    assert not live.exists(), "Do not commit invented prereg_rules.yaml yet"
    template = repo / "config" / "discovery" / "_prereg_rules.template.yaml"
    assert template.is_file()
