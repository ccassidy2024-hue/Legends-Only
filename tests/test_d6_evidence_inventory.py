"""Focused tests for D6 evidence inventory (pointer verification / field-sufficiency)."""

from __future__ import annotations

import csv
import hashlib
from pathlib import Path

import pytest
import yaml

from grainsys.discovery.candidate_universe import (
    CANONICAL_CANDIDATE_UNIVERSE_MANIFEST_RELATIVE,
    CANONICAL_CANDIDATES_RELATIVE,
)
from grainsys.discovery.capture import capture_candidate_evidence
from grainsys.discovery.evidence_inventory import (
    BLOCKER_CAPTURE_STORE_MISSING,
    FORBIDDEN_INVENTORY_FIELDS,
    FROZEN_CANDIDATE_COUNT,
    FROZEN_CANDIDATE_UNIVERSE_VERSION,
    FROZEN_CANDIDATES_DIGEST,
    FROZEN_HIT_SET_DIGEST,
    FROZEN_S1_COUNT,
    FROZEN_S4_COUNT,
    HURDAT2_ARCHIVES,
    I2_BODY_NOT_ADJUDICATED,
    I2_NEEDS_PRIMARY,
    I2_UNKNOWN,
    INVENTORY_CSV_FIELDNAMES,
    INVENTORY_CSV_RELATIVE,
    INVENTORY_SCHEMA_RELATIVE,
    INVENTORY_SUMMARY_RELATIVE,
    EvidenceInventoryError,
    _check_object_and_manifest,
    build_evidence_inventory,
    enrich_existing_capture_dir,
    find_capture_data_root,
    s1_field_sufficiency,
    s4_field_sufficiency,
)

REPO = Path(__file__).resolve().parents[1]


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def test_hurdat2_dir_prefixes_match_authorized_url_hashes() -> None:
    for archive in HURDAT2_ARCHIVES:
        got = _sha(archive["source_reference"].encode())[:12]
        assert archive["dir_prefix"] == f"S4-hurdat-{got}"


def test_s4_i2_always_needs_primary_operational_even_if_verified() -> None:
    verified = s4_field_sufficiency(pointer_status="verified")
    missing = s4_field_sufficiency(pointer_status="unknown")
    assert verified["i2_field_sufficiency"] == I2_NEEDS_PRIMARY
    assert missing["i2_field_sufficiency"] == I2_NEEDS_PRIMARY
    assert verified["public_anchor_sufficiency"] == I2_NEEDS_PRIMARY
    assert verified["event_mechanism_sufficiency"] == I2_NEEDS_PRIMARY
    assert verified["driver_identity_sufficiency"] == "sufficient_from_hurdat2_registry"
    assert missing["driver_identity_sufficiency"] == "unknown"


def test_s1_unreadable_body_is_unknown_not_zero() -> None:
    unread = s1_field_sufficiency(pointer_status="unknown")
    present = s1_field_sufficiency(pointer_status="verified")
    assert unread["i2_field_sufficiency"] == I2_UNKNOWN
    assert present["i2_field_sufficiency"] == I2_BODY_NOT_ADJUDICATED


def test_pointer_verified_requires_object_and_manifest(tmp_path: Path) -> None:
    payload = b"inventory-fixture"
    digest = _sha(payload)
    rec = capture_candidate_evidence(
        sweep_id="S1",
        candidate_id="S1-LRH-2020-0001",
        raw_bytes=payload,
        source_reference="LRH-2020-0001",
        sweeps_subdir="sweeps",
        data_root_path=tmp_path,
    )
    assert rec.sha256 == digest
    pointer = f"sweeps/S1/S1-LRH-2020-0001/objects/{digest}"
    status, observed, man = _check_object_and_manifest(
        data_root=tmp_path, pointer=pointer
    )
    assert status == "verified"
    assert observed == digest
    assert man == "verified"


def test_missing_and_corrupt_objects(tmp_path: Path) -> None:
    payload = b"good-bytes"
    digest = _sha(payload)
    missing_pointer = f"sweeps/S1/S1-LRH-2020-0001/objects/{digest}"
    status, observed, man = _check_object_and_manifest(
        data_root=tmp_path, pointer=missing_pointer
    )
    assert status == "missing"
    assert observed == ""
    assert man == "missing"

    capture_candidate_evidence(
        sweep_id="S1",
        candidate_id="S1-LRH-2020-0001",
        raw_bytes=payload,
        source_reference="LRH-2020-0001",
        sweeps_subdir="sweeps",
        data_root_path=tmp_path,
    )
    obj = tmp_path / "sweeps" / "S1" / "S1-LRH-2020-0001" / "objects" / digest
    obj.write_bytes(b"CORRUPTED-CONTENT")
    status, observed, man = _check_object_and_manifest(
        data_root=tmp_path, pointer=missing_pointer
    )
    assert status == "corrupt"
    assert observed == _sha(b"CORRUPTED-CONTENT")
    assert man == "mismatch"


def test_unset_root_is_unknown_not_missing() -> None:
    digest = "a" * 64
    pointer = f"sweeps/S4/S4-AL012018-WCSC-08UQ/objects/{digest}"
    status, observed, man = _check_object_and_manifest(data_root=None, pointer=pointer)
    assert status == "unknown"
    assert observed == ""
    assert man == "unknown"


def test_discover_capture_root_from_hints(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GRAIN_DATA_ROOT", raising=False)
    tree = tmp_path / "grain"
    (tree / "sweeps" / "S4").mkdir(parents=True)
    root, origin, searched = find_capture_data_root(
        search_hints=(tmp_path / "empty", tree)
    )
    assert origin == "discovered"
    assert root == tree
    assert str(tree) in searched


def test_enrich_refuses_minted_cand_dir_and_absent_dir(tmp_path: Path) -> None:
    with pytest.raises(EvidenceInventoryError, match="CAND-"):
        enrich_existing_capture_dir(
            sweep_id="S1",
            capture_dir="CAND-0001",
            raw_bytes=b"x",
            source_reference="doc",
            data_root_path=tmp_path,
        )
    with pytest.raises(EvidenceInventoryError, match="does not exist"):
        enrich_existing_capture_dir(
            sweep_id="S1",
            capture_dir="S1-LRH-2020-0001",
            raw_bytes=b"x",
            source_reference="doc",
            data_root_path=tmp_path,
        )


def test_enrich_appends_to_existing_source_derived_dir(tmp_path: Path) -> None:
    first = capture_candidate_evidence(
        sweep_id="S4",
        candidate_id="S4-AL012018-WCSC-08UQ",
        raw_bytes=b"node-hit",
        source_reference="AL012018:WCSC-08UQ",
        sweeps_subdir="sweeps",
        data_root_path=tmp_path,
    )
    extra = enrich_existing_capture_dir(
        sweep_id="S4",
        capture_dir="S4-AL012018-WCSC-08UQ",
        raw_bytes=b"corroboration",
        source_reference="authorized-ops-note",
        data_root_path=tmp_path,
    )
    assert extra.sha256 != first.sha256
    man = yaml.safe_load(
        (
            tmp_path
            / "sweeps"
            / "S4"
            / "S4-AL012018-WCSC-08UQ"
            / "manifest.yaml"
        ).read_text(encoding="utf-8")
    )
    assert [r["source_reference"] for r in man["records"]] == [
        "AL012018:WCSC-08UQ",
        "authorized-ops-note",
    ]
    assert not (tmp_path / "episodes").exists()
    assert not list(tmp_path.glob("**/CAND-*"))


def test_build_inventory_unknown_without_data_root_does_not_mutate_d5(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("GRAIN_DATA_ROOT", raising=False)
    before_csv = (REPO / CANONICAL_CANDIDATES_RELATIVE).read_bytes()
    before_man = (REPO / CANONICAL_CANDIDATE_UNIVERSE_MANIFEST_RELATIVE).read_bytes()
    result = build_evidence_inventory(
        repo_root=REPO,
        search_hints=(tmp_path / "nope",),
        persist=False,
    )
    assert result.access_gate == BLOCKER_CAPTURE_STORE_MISSING
    assert result.candidate_universe_version == FROZEN_CANDIDATE_UNIVERSE_VERSION
    assert result.hit_set_digest == FROZEN_HIT_SET_DIGEST
    assert result.candidates_digest == FROZEN_CANDIDATES_DIGEST
    assert result.candidate_count == FROZEN_CANDIDATE_COUNT
    assert result.counts["S1"]["unknown"] == FROZEN_S1_COUNT
    assert result.counts["S4"]["unknown"] == FROZEN_S4_COUNT
    assert result.counts["S1"]["missing"] == 0
    assert result.counts["S4"]["missing"] == 0
    assert result.hurdat2_counts["unknown"] == 2
    assert result.enrichment_count == 0
    assert {row.sweep_id for row in result.rows} == {"S1", "S4"}
    assert len({row.candidate_id for row in result.rows}) == FROZEN_CANDIDATE_COUNT
    s4_dirs = {row.capture_dir for row in result.rows if row.sweep_id == "S4"}
    assert not any(name.startswith("CAND-") for name in s4_dirs)
    storms = {row.capture_dir.split("-")[1] for row in result.rows if row.sweep_id == "S4"}
    assert len(storms) > 1
    assert (REPO / CANONICAL_CANDIDATES_RELATIVE).read_bytes() == before_csv
    assert (REPO / CANONICAL_CANDIDATE_UNIVERSE_MANIFEST_RELATIVE).read_bytes() == before_man
    real_eps = [
        p
        for p in (REPO / "research/episodes/entries").glob("*.yaml")
        if not p.name.startswith("EP-0000-000")
    ]
    assert real_eps == []


def test_explicit_empty_root_counts_missing_not_unknown(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("GRAIN_DATA_ROOT", raising=False)
    result = build_evidence_inventory(
        repo_root=REPO,
        data_root_path=tmp_path,
        persist=False,
    )
    assert result.access_gate == BLOCKER_CAPTURE_STORE_MISSING
    assert result.counts["S1"]["missing"] == FROZEN_S1_COUNT
    assert result.counts["S4"]["missing"] == FROZEN_S4_COUNT
    assert result.counts["S1"]["unknown"] == 0
    assert result.hurdat2_counts["missing"] == 2
    assert all(row.i2_field_sufficiency == I2_NEEDS_PRIMARY for row in result.rows if row.sweep_id == "S4")


def test_schema_documents_inventory_shape() -> None:
    schema = yaml.safe_load((REPO / INVENTORY_SCHEMA_RELATIVE).read_text(encoding="utf-8"))
    assert schema["record_kind"] == "d6_evidence_inventory"
    assert schema["csv_required_fields"] == list(INVENTORY_CSV_FIELDNAMES)
    assert "episode_id" in schema["forbidden_fields"]
    assert "reason_code" in schema["forbidden_fields"]
    assert FORBIDDEN_INVENTORY_FIELDS <= set(schema["forbidden_fields"])


def test_committed_inventory_is_d5_keyed_when_present() -> None:
    csv_path = REPO / INVENTORY_CSV_RELATIVE
    summary_path = REPO / INVENTORY_SUMMARY_RELATIVE
    if not csv_path.is_file() or not summary_path.is_file():
        pytest.skip("derived inventory not persisted in this tree")
    summary = yaml.safe_load(summary_path.read_text(encoding="utf-8"))
    assert summary["candidate_universe_version"] == FROZEN_CANDIDATE_UNIVERSE_VERSION
    assert summary["hit_set_digest"] == FROZEN_HIT_SET_DIGEST
    assert summary["candidates_digest"] == FROZEN_CANDIDATES_DIGEST
    assert summary["candidate_count"] == FROZEN_CANDIDATE_COUNT
    assert hashlib.sha256(csv_path.read_bytes()).hexdigest() == summary["inventory_csv_digest"]
    with csv_path.open(encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    assert list(rows[0].keys()) == list(INVENTORY_CSV_FIELDNAMES)
    assert len(rows) == FROZEN_CANDIDATE_COUNT
    with (REPO / CANONICAL_CANDIDATES_RELATIVE).open(encoding="utf-8", newline="") as fh:
        cand = list(csv.DictReader(fh))
    assert [r["candidate_id"] for r in rows] == [r["candidate_id"] for r in cand]
    assert all(set(FORBIDDEN_INVENTORY_FIELDS).isdisjoint(row) for row in rows)
    s4 = [r for r in rows if r["sweep_id"] == "S4"]
    assert len(s4) == FROZEN_S4_COUNT
    assert all(r["i2_field_sufficiency"] == I2_NEEDS_PRIMARY for r in s4)
    assert not any(r["capture_dir"].startswith("CAND-") for r in rows)
    assert not (REPO / "research/episodes/discovery/candidates/no_episode_dispositions.csv").exists()
    assert summary.get("hurdat2_public_verified") == 2
    for rec in summary["hurdat2_archives"]:
        assert rec["public_refetch_status"] == "verified"
        assert rec["public_observed_sha256"] == rec["expected_sha256"]
    # Live capture root verifies S4 + HURDAT2; S1 originals may be restored.
    if summary["access_gate"] == BLOCKER_CAPTURE_STORE_MISSING:
        assert summary["pointer_counts"]["S1"]["unknown"] == FROZEN_S1_COUNT
        assert summary["pointer_counts"]["S4"]["unknown"] == FROZEN_S4_COUNT
        for rec in summary["hurdat2_archives"]:
            assert rec["pointer_status"] == "unknown"
    else:
        assert summary["access_gate"] == "ok"
        assert summary["pointer_counts"]["S4"]["verified"] == FROZEN_S4_COUNT
        assert summary["pointer_counts"]["S1"]["verified"] == FROZEN_S1_COUNT
        assert summary["pointer_counts"]["S1"]["missing"] == 0
        assert summary["pointer_counts"]["S1"]["corrupt"] == 0
        for rec in summary["hurdat2_archives"]:
            assert rec["pointer_status"] == "verified"


def test_hurdat2_public_refetch_does_not_invent_capture(tmp_path: Path) -> None:
    payloads = {
        HURDAT2_ARCHIVES[0]["source_reference"]: b"not-the-atlantic-archive",
        HURDAT2_ARCHIVES[1]["source_reference"]: b"not-the-pacific-archive",
    }

    def fake_fetch(url: str, *, timeout: int = 120):
        return True, payloads[url], None

    (tmp_path / "sweeps").mkdir()
    result = build_evidence_inventory(
        repo_root=REPO,
        data_root_path=tmp_path,
        persist=False,
        refetch_hurdat2=True,
        fetch_fn=fake_fetch,
    )
    assert result.hurdat2_public_verified == 0
    assert all(h.public_refetch_status == "mismatch" for h in result.hurdat2)
    assert not (tmp_path / "sweeps" / "S4").exists()
    assert result.access_gate == BLOCKER_CAPTURE_STORE_MISSING
    assert result.enrichment_count == 0
