"""Tests for candidate-to-episode lineage (ADR-0009 PR-B)."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from grainsys.discovery.candidate_universe import (
    CANDIDATES_CSV_FIELDNAMES,
    CANONICAL_CANDIDATE_UNIVERSE_MANIFEST_RELATIVE,
    CANONICAL_CANDIDATES_RELATIVE,
    mint_d5_candidate_ids,
    render_candidates_csv_bytes,
)
from grainsys.discovery.governance import LOAD_BEARING_RELATIVE_PATHS
from grainsys.episodes import Findings, check, load_schema, validate_entry
from grainsys.lineage import (
    LineageError,
    check_universe_accounting,
    derive_candidate_to_episode_index,
    lineage_candidate_id,
    parse_d5_candidate_sequence,
    validate_candidate_ids_shape,
    validate_candidate_universe_version,
)

REPO = Path(__file__).resolve().parents[1]
SCHEMA_PATH = REPO / "research/episodes/episode_schema.yaml"
ENTRIES_DIR = REPO / "research/episodes/entries"
EXAMPLE_PATH = ENTRIES_DIR / "EP-0000-000-example.yaml"
NO_EPISODE_SCHEMA = (
    REPO / "research/episodes/discovery/candidates/no_episode_dispositions.schema.yaml"
)

_FAMILIES = ("S1", "S2")
_ATTEST = {"S1": True, "S2": True}


def _hits() -> list[dict[str, str]]:
    return [
        {"sweep_id": "S1", "source_reference": "doc-a", "raw_capture_pointer": "raw/a"},
        {"sweep_id": "S2", "source_reference": "doc-b", "raw_capture_pointer": "raw/b"},
        {"sweep_id": "S1", "source_reference": "doc-c", "raw_capture_pointer": "raw/c"},
    ]


def _universe_fixtures() -> tuple[bytes, str]:
    minted = mint_d5_candidate_ids(_hits())
    csv_bytes = render_candidates_csv_bytes(minted)
    version = "d5cu-" + "a" * 64
    return csv_bytes, version


def _episode_entry(
    *,
    episode_id: str,
    candidate_ids: list[str],
    version: str,
    example: bool = False,
    status: str = "accepted",
) -> dict:
    with EXAMPLE_PATH.open(encoding="utf-8") as fh:
        base = yaml.safe_load(fh)
    base["episode_id"] = episode_id
    base["candidate_ids"] = candidate_ids
    base["candidate_universe_version"] = version
    base["status"] = status
    base["decision"] = "accept" if status == "accepted" else "reject"
    if example:
        base["example"] = True
    else:
        base.pop("example", None)
    base["_file"] = f"{episode_id}.yaml"
    return base


def codes(fx: Findings) -> set[str]:
    return {msg.split("[")[1].split("]")[0] for msg in fx.errors}


# --------------------------------------------------------------------------- #
# Standalone candidate_ids shape
# --------------------------------------------------------------------------- #
def test_candidate_ids_required_nonempty_via_validator() -> None:
    schema = load_schema(SCHEMA_PATH)
    with EXAMPLE_PATH.open(encoding="utf-8") as fh:
        entry = yaml.safe_load(fh)
    entry["_file"] = EXAMPLE_PATH.name
    entry["candidate_ids"] = []
    fx = Findings()
    validate_entry(entry, schema, fx)
    assert "E30" in codes(fx)


def test_malformed_candidate_id_fails() -> None:
    with pytest.raises(LineageError, match="numeric D5"):
        validate_candidate_ids_shape(["CAND-XY"])
    with pytest.raises(LineageError, match="prefix"):
        validate_candidate_ids_shape(["WRONG-0001"])


def test_duplicate_candidate_id_fails() -> None:
    with pytest.raises(LineageError, match="duplicate"):
        validate_candidate_ids_shape(["CAND-0001", "CAND-0001"])


def test_inconsistent_id_width_fails() -> None:
    with pytest.raises(LineageError, match="consistent D5 sequence width"):
        validate_candidate_ids_shape(["CAND-0001", "CAND-00002"])


def test_unsorted_candidate_ids_fails() -> None:
    with pytest.raises(LineageError, match="ascending D5 numeric order"):
        validate_candidate_ids_shape(["CAND-0002", "CAND-0001"])


def test_correctly_sorted_candidate_ids_passes() -> None:
    assert validate_candidate_ids_shape(["CAND-0001", "CAND-0002", "CAND-0010"]) == [
        "CAND-0001",
        "CAND-0002",
        "CAND-0010",
    ]


def test_candidate_universe_version_syntax() -> None:
    validate_candidate_universe_version("d5cu-" + "f" * 64)
    with pytest.raises(LineageError):
        validate_candidate_universe_version("d5cu-short")
    with pytest.raises(LineageError):
        validate_candidate_universe_version("not-a-version")


def test_stored_lineage_candidate_id_fails() -> None:
    schema = load_schema(SCHEMA_PATH)
    with EXAMPLE_PATH.open(encoding="utf-8") as fh:
        entry = yaml.safe_load(fh)
    entry["_file"] = EXAMPLE_PATH.name
    entry["lineage_candidate_id"] = "CAND-0001"
    fx = Findings()
    validate_entry(entry, schema, fx)
    assert "E06" in codes(fx)


def test_fictional_example_remains_standalone_valid() -> None:
    rows, fx = check(ENTRIES_DIR, SCHEMA_PATH)
    assert fx.errors == [], fx.errors
    example = next(r for r in rows if r.get("example"))
    assert example["candidate_ids"] == ["CAND-0001", "CAND-0002"]
    assert example["candidate_universe_version"].startswith("d5cu-")


# --------------------------------------------------------------------------- #
# Pure lineage primitives
# --------------------------------------------------------------------------- #
def test_lineage_candidate_id_returns_numeric_minimum() -> None:
    assert lineage_candidate_id(["CAND-0002", "CAND-0001"]) == "CAND-0001"
    assert lineage_candidate_id(["CAND-0010", "CAND-0002"]) == "CAND-0002"


def test_lineage_candidate_id_malformed_fails() -> None:
    with pytest.raises(LineageError):
        lineage_candidate_id(["CAND-bad"])


def test_lineage_candidate_id_empty_fails() -> None:
    with pytest.raises(LineageError, match="nonempty"):
        lineage_candidate_id([])


def test_no_lexicographic_width_bug() -> None:
    """Numeric min, not lexicographic string min, when width is consistent."""
    assert lineage_candidate_id(["CAND-0002", "CAND-0010"]) == "CAND-0002"
    seq, width = parse_d5_candidate_sequence("CAND-0010")
    assert seq == 10
    assert width == 4


def test_derive_index_many_candidates_one_episode() -> None:
    entries = [_episode_entry(episode_id="EP-2099-001", candidate_ids=["CAND-0001", "CAND-0002"], version="d5cu-" + "a" * 64)]
    idx = derive_candidate_to_episode_index(entries)
    assert idx["CAND-0001"] == ("EP-2099-001",)
    assert idx["CAND-0002"] == ("EP-2099-001",)


def test_derive_index_one_candidate_many_episodes() -> None:
    version = "d5cu-" + "a" * 64
    entries = [
        _episode_entry(episode_id="EP-2099-001", candidate_ids=["CAND-0001"], version=version),
        _episode_entry(episode_id="EP-2099-002", candidate_ids=["CAND-0001"], version=version),
    ]
    idx = derive_candidate_to_episode_index(entries)
    assert idx["CAND-0001"] == ("EP-2099-001", "EP-2099-002")


def test_reverse_index_deterministic() -> None:
    version = "d5cu-" + "a" * 64
    entries = [
        _episode_entry(episode_id="EP-2099-002", candidate_ids=["CAND-0002"], version=version),
        _episode_entry(episode_id="EP-2099-001", candidate_ids=["CAND-0001"], version=version),
    ]
    idx = derive_candidate_to_episode_index(entries)
    assert list(idx.keys()) == sorted(idx.keys())
    assert idx["CAND-0001"] == ("EP-2099-001",)


# --------------------------------------------------------------------------- #
# Layer-3 freeze accounting fixtures
# --------------------------------------------------------------------------- #
def test_valid_e_union_n_passes() -> None:
    csv_bytes, version = _universe_fixtures()
    minted_ids = ["CAND-0001", "CAND-0002", "CAND-0003"]
    entries = [
        _episode_entry(episode_id="EP-2099-001", candidate_ids=[minted_ids[0]], version=version),
    ]
    dispositions = [{"candidate_id": minted_ids[1], "reason_code": "R3"}]
    # Third candidate only in N
    dispositions.append({"candidate_id": minted_ids[2], "reason_code": "R2"})
    fx = check_universe_accounting(
        entries,
        candidates_csv=csv_bytes,
        candidate_universe_manifest={"candidate_universe_version": version},
        no_episode_dispositions=dispositions,
    )
    assert fx.ok, fx.errors


def test_unknown_candidate_in_episode_fails() -> None:
    csv_bytes, version = _universe_fixtures()
    entries = [
        _episode_entry(episode_id="EP-2099-001", candidate_ids=["CAND-9999"], version=version),
    ]
    fx = check_universe_accounting(
        entries,
        candidates_csv=csv_bytes,
        candidate_universe_manifest={"candidate_universe_version": version},
        no_episode_dispositions=[{"candidate_id": "CAND-0001", "reason_code": "R3"},
                                 {"candidate_id": "CAND-0002", "reason_code": "R3"}],
    )
    assert any("L07" in e for e in fx.errors)


def test_unknown_candidate_in_disposition_fails() -> None:
    csv_bytes, version = _universe_fixtures()
    fx = check_universe_accounting(
        [],
        candidates_csv=csv_bytes,
        candidate_universe_manifest={"candidate_universe_version": version},
        no_episode_dispositions=[{"candidate_id": "CAND-9999", "reason_code": "R3"}],
    )
    assert any("L12" in e for e in fx.errors)


def test_episode_universe_mismatch_fails() -> None:
    csv_bytes, version = _universe_fixtures()
    entries = [
        _episode_entry(
            episode_id="EP-2099-001",
            candidate_ids=["CAND-0001"],
            version="d5cu-" + "b" * 64,
        ),
    ]
    fx = check_universe_accounting(
        entries,
        candidates_csv=csv_bytes,
        candidate_universe_manifest={"candidate_universe_version": version},
        no_episode_dispositions=[
            {"candidate_id": "CAND-0002", "reason_code": "R3"},
            {"candidate_id": "CAND-0003", "reason_code": "R3"},
        ],
    )
    assert any("L05" in e for e in fx.errors)


def test_e_intersect_n_fails() -> None:
    csv_bytes, version = _universe_fixtures()
    entries = [
        _episode_entry(episode_id="EP-2099-001", candidate_ids=["CAND-0001"], version=version),
    ]
    fx = check_universe_accounting(
        entries,
        candidates_csv=csv_bytes,
        candidate_universe_manifest={"candidate_universe_version": version},
        no_episode_dispositions=[
            {"candidate_id": "CAND-0001", "reason_code": "R3"},
            {"candidate_id": "CAND-0002", "reason_code": "R3"},
            {"candidate_id": "CAND-0003", "reason_code": "R3"},
        ],
    )
    assert any("L14" in e for e in fx.errors)


def test_unaccounted_candidate_fails() -> None:
    csv_bytes, version = _universe_fixtures()
    entries = [
        _episode_entry(episode_id="EP-2099-001", candidate_ids=["CAND-0001"], version=version),
    ]
    fx = check_universe_accounting(
        entries,
        candidates_csv=csv_bytes,
        candidate_universe_manifest={"candidate_universe_version": version},
        no_episode_dispositions=[{"candidate_id": "CAND-0002", "reason_code": "R3"}],
    )
    assert any("L15" in e and "CAND-0003" in e for e in fx.errors)


def test_duplicate_disposition_row_fails() -> None:
    csv_bytes, version = _universe_fixtures()
    row = {"candidate_id": "CAND-0001", "reason_code": "R3", "note": "same"}
    fx = check_universe_accounting(
        [],
        candidates_csv=csv_bytes,
        candidate_universe_manifest={"candidate_universe_version": version},
        no_episode_dispositions=[row, dict(row)],
    )
    assert any("L13" in e for e in fx.errors)


def test_missing_reason_code_fails() -> None:
    csv_bytes, version = _universe_fixtures()
    fx = check_universe_accounting(
        [],
        candidates_csv=csv_bytes,
        candidate_universe_manifest={"candidate_universe_version": version},
        no_episode_dispositions=[{"candidate_id": "CAND-0001"}],
    )
    assert any("L09" in e for e in fx.errors)


def test_candidate_only_in_n_is_valid() -> None:
    csv_bytes, version = _universe_fixtures()
    fx = check_universe_accounting(
        [],
        candidates_csv=csv_bytes,
        candidate_universe_manifest={"candidate_universe_version": version},
        no_episode_dispositions=[
            {"candidate_id": "CAND-0001", "reason_code": "R3"},
            {"candidate_id": "CAND-0002", "reason_code": "R2"},
            {"candidate_id": "CAND-0003", "reason_code": "R5"},
        ],
    )
    assert fx.ok, fx.errors


def test_one_candidate_on_multiple_episodes_valid_accounting() -> None:
    csv_bytes, version = _universe_fixtures()
    entries = [
        _episode_entry(episode_id="EP-2099-001", candidate_ids=["CAND-0001"], version=version),
        _episode_entry(episode_id="EP-2099-002", candidate_ids=["CAND-0001"], version=version),
    ]
    fx = check_universe_accounting(
        entries,
        candidates_csv=csv_bytes,
        candidate_universe_manifest={"candidate_universe_version": version},
        no_episode_dispositions=[
            {"candidate_id": "CAND-0002", "reason_code": "R3"},
            {"candidate_id": "CAND-0003", "reason_code": "R3"},
        ],
    )
    assert fx.ok, fx.errors


def test_rejected_episode_ancestry_in_e() -> None:
    csv_bytes, version = _universe_fixtures()
    entries = [
        _episode_entry(
            episode_id="EP-2099-001",
            candidate_ids=["CAND-0001"],
            version=version,
            status="rejected",
        ),
    ]
    fx = check_universe_accounting(
        entries,
        candidates_csv=csv_bytes,
        candidate_universe_manifest={"candidate_universe_version": version},
        no_episode_dispositions=[
            {"candidate_id": "CAND-0002", "reason_code": "R3"},
            {"candidate_id": "CAND-0003", "reason_code": "R3"},
        ],
    )
    assert fx.ok, fx.errors


def test_example_entry_excluded_from_e() -> None:
    csv_bytes, version = _universe_fixtures()
    entries = [
        _episode_entry(
            episode_id="EP-0000-000",
            candidate_ids=["CAND-0001"],
            version=version,
            example=True,
        ),
    ]
    fx = check_universe_accounting(
        entries,
        candidates_csv=csv_bytes,
        candidate_universe_manifest={"candidate_universe_version": version},
        no_episode_dispositions=[
            {"candidate_id": "CAND-0001", "reason_code": "R3"},
            {"candidate_id": "CAND-0002", "reason_code": "R3"},
            {"candidate_id": "CAND-0003", "reason_code": "R3"},
        ],
    )
    assert fx.ok, fx.errors


def test_checker_does_not_modify_candidates_csv(tmp_path: Path) -> None:
    csv_bytes, version = _universe_fixtures()
    csv_path = tmp_path / "candidates.csv"
    csv_path.write_bytes(csv_bytes)
    before = csv_path.read_bytes()
    check_universe_accounting(
        [],
        candidates_csv=csv_path,
        candidate_universe_manifest={"candidate_universe_version": version},
        no_episode_dispositions=[
            {"candidate_id": "CAND-0001", "reason_code": "R3"},
            {"candidate_id": "CAND-0002", "reason_code": "R3"},
            {"candidate_id": "CAND-0003", "reason_code": "R3"},
        ],
    )
    assert csv_path.read_bytes() == before


def test_checker_does_not_modify_episode_yaml(tmp_path: Path) -> None:
    csv_bytes, version = _universe_fixtures()
    entry = _episode_entry(episode_id="EP-2099-001", candidate_ids=["CAND-0001"], version=version)
    path = tmp_path / "EP-2099-001.yaml"
    text = yaml.safe_dump({k: v for k, v in entry.items() if k != "_file"})
    path.write_text(text, encoding="utf-8")
    entry["_file"] = path.name
    before = path.read_text(encoding="utf-8")
    check_universe_accounting(
        [entry],
        candidates_csv=csv_bytes,
        candidate_universe_manifest={"candidate_universe_version": version},
        no_episode_dispositions=[
            {"candidate_id": "CAND-0002", "reason_code": "R3"},
            {"candidate_id": "CAND-0003", "reason_code": "R3"},
        ],
    )
    assert path.read_text(encoding="utf-8") == before


def test_missing_live_candidates_csv_does_not_break_standalone_validation() -> None:
    assert not (REPO / CANONICAL_CANDIDATES_RELATIVE).exists()
    _, fx = check(ENTRIES_DIR, SCHEMA_PATH)
    assert fx.errors == [], fx.errors


# --------------------------------------------------------------------------- #
# Regression guards
# --------------------------------------------------------------------------- #
def test_candidates_csv_never_gains_episode_id_field() -> None:
    assert "episode_id" not in CANDIDATES_CSV_FIELDNAMES
    csv_bytes = render_candidates_csv_bytes(mint_d5_candidate_ids(_hits()))
    assert b"episode_id" not in csv_bytes.splitlines()[0]


def test_no_live_candidates_csv_in_repo() -> None:
    assert not (REPO / CANONICAL_CANDIDATES_RELATIVE).exists()


def test_no_candidate_universe_yaml_in_repo() -> None:
    assert not (REPO / CANONICAL_CANDIDATE_UNIVERSE_MANIFEST_RELATIVE).exists()


def test_no_live_no_episode_dispositions_csv() -> None:
    assert not (
        REPO / "research/episodes/discovery/candidates/no_episode_dispositions.csv"
    ).exists()


def test_no_prereg_rules_yaml_in_repo() -> None:
    assert not (REPO / "config/discovery/prereg_rules.yaml").exists()


def test_load_bearing_relative_paths_unchanged() -> None:
    expected = (
        "src/grainsys/discovery/config.py",
        "src/grainsys/discovery/sweep.py",
        "src/grainsys/discovery/candidates.py",
        "src/grainsys/discovery/coverage.py",
        "src/grainsys/discovery/governance.py",
        "src/grainsys/discovery/archive_listing.py",
        "src/grainsys/discovery/capture.py",
        "src/grainsys/ingest/ntni.py",
        "src/grainsys/episodes.py",
        "research/episodes/EPISODE_PROTOCOL.md",
        "research/episodes/ADMISSION_CHECKLIST.md",
        "research/episodes/episode_schema.yaml",
        "research/episodes/discovery/candidates/_schema.yaml",
        "docs/decisions/0002-episode-preregistration.md",
        "docs/decisions/0003-phase0-prereg-hardening.md",
        "docs/decisions/0005-source-handling-and-vintage-rules.md",
        "docs/decisions/0015-d3-d4-positive-only-s1.md",
    )
    assert LOAD_BEARING_RELATIVE_PATHS == expected
    assert "lineage.py" not in " ".join(LOAD_BEARING_RELATIVE_PATHS)


def test_no_episode_schema_has_required_fields() -> None:
    schema = yaml.safe_load(NO_EPISODE_SCHEMA.read_text(encoding="utf-8"))
    assert schema["required_fields"] == ["candidate_id", "reason_code"]
    assert schema["optional_fields"] == ["note"]
    assert "R3" in schema["vocabularies"]["decision_reason"]


def test_missing_candidate_ids_field_fails_validation() -> None:
    schema = load_schema(SCHEMA_PATH)
    with EXAMPLE_PATH.open(encoding="utf-8") as fh:
        entry = yaml.safe_load(fh)
    entry["_file"] = EXAMPLE_PATH.name
    del entry["candidate_ids"]
    fx = Findings()
    validate_entry(entry, schema, fx)
    assert "E04" in codes(fx)
