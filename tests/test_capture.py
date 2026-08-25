"""Focused tests for D6 candidate-keyed capture mechanics (ADR-0010 / ADR-0013)."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest
import yaml

from grainsys.discovery.candidate_universe import (
    CANONICAL_CANDIDATE_UNIVERSE_MANIFEST_RELATIVE,
    CANONICAL_CANDIDATES_RELATIVE,
)
from grainsys.discovery.capture import (
    CAPTURE_MANIFEST_SCHEMA_VERSION,
    CaptureError,
    CapturePathError,
    CaptureRecord,
    candidate_capture_dir,
    capture_candidate_evidence,
    render_capture_manifest_yaml,
)
from grainsys.discovery.config import REHOME_POLICIES

REPO = Path(__file__).resolve().parents[1]


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _capture(tmp_path: Path, **kwargs):
    defaults = {
        "sweep_id": "S1",
        "candidate_id": "CAND-0001",
        "raw_bytes": b"hello-evidence",
        "source_reference": "doc-a",
        "sweeps_subdir": "sweeps",
        "data_root_path": tmp_path,
    }
    defaults.update(kwargs)
    return capture_candidate_evidence(**defaults)


def test_rehome_closed_vocabulary_constant() -> None:
    assert REHOME_POLICIES == frozenset({"candidate_keyed_no_move"})


def test_deterministic_candidate_capture_directory(tmp_path: Path) -> None:
    a = candidate_capture_dir(
        sweep_id="S1",
        candidate_id="CAND-0001",
        data_root_path=tmp_path,
        sweeps_subdir="sweeps",
    )
    b = candidate_capture_dir(
        sweep_id="S1",
        candidate_id="CAND-0001",
        data_root_path=tmp_path,
        sweeps_subdir="sweeps",
    )
    assert a == b
    assert a == tmp_path / "sweeps" / "S1" / "CAND-0001"


@pytest.mark.parametrize(
    "kwargs",
    [
        {"sweep_id": "..", "candidate_id": "CAND-0001"},
        {"sweep_id": "S1", "candidate_id": "../x"},
        {"sweep_id": "S1", "candidate_id": "C:/windows"},
        {"sweep_id": "a/b", "candidate_id": "CAND-0001"},
        {"sweep_id": "S1", "candidate_id": "x\\y"},
        {"sweeps_subdir": "../escape"},
        {"sweeps_subdir": "/abs"},
        {"sweeps_subdir": "C:/windows"},
    ],
)
def test_traversal_blocked_through_capture_entry(tmp_path: Path, kwargs: dict) -> None:
    call = {
        "sweep_id": "S1",
        "candidate_id": "CAND-0001",
        "raw_bytes": b"x",
        "source_reference": "doc",
        "sweeps_subdir": "sweeps",
        "data_root_path": tmp_path,
    }
    call.update(kwargs)
    with pytest.raises((CapturePathError, CaptureError)):
        capture_candidate_evidence(**call)


def test_raw_bytes_persisted_exactly(tmp_path: Path) -> None:
    payload = b"exact-bytes-\x00\xff"
    rec = _capture(tmp_path, raw_bytes=payload)
    obj = tmp_path / "sweeps" / "S1" / "CAND-0001" / "objects" / rec.sha256
    assert obj.read_bytes() == payload


def test_sha_filename_equals_sha_of_persisted_bytes(tmp_path: Path) -> None:
    payload = b"hash-me"
    rec = _capture(tmp_path, raw_bytes=payload)
    assert rec.sha256 == _sha(payload)
    obj = tmp_path / "sweeps" / "S1" / "CAND-0001" / "objects" / rec.sha256
    assert obj.name == _sha(obj.read_bytes())


def test_byte_length_matches(tmp_path: Path) -> None:
    payload = b"0123456789"
    rec = _capture(tmp_path, raw_bytes=payload)
    assert rec.byte_length == len(payload)
    obj = tmp_path / "sweeps" / "S1" / "CAND-0001" / "objects" / rec.sha256
    assert len(obj.read_bytes()) == rec.byte_length


def test_manifest_record_resolves_to_raw_object(tmp_path: Path) -> None:
    rec = _capture(tmp_path, raw_bytes=b"resolve-me")
    man = yaml.safe_load(
        (tmp_path / "sweeps" / "S1" / "CAND-0001" / "manifest.yaml").read_text(
            encoding="utf-8"
        )
    )
    assert man["records"][0]["sha256"] == rec.sha256
    obj = tmp_path / "sweeps" / "S1" / "CAND-0001" / "objects" / man["records"][0]["sha256"]
    assert obj.is_file()
    assert _sha(obj.read_bytes()) == man["records"][0]["sha256"]


def test_identical_retry_idempotent(tmp_path: Path) -> None:
    kwargs = {
        "raw_bytes": b"same",
        "source_reference": "doc-a",
        "retrieved_on": "2099-01-01",
        "original_filename": "a.pdf",
        "content_type": "application/pdf",
    }
    a = _capture(tmp_path, **kwargs)
    b = _capture(tmp_path, **kwargs)
    assert a == b
    objects = list((tmp_path / "sweeps" / "S1" / "CAND-0001" / "objects").iterdir())
    objects = [p for p in objects if not p.name.startswith(".")]
    assert len(objects) == 1
    man = yaml.safe_load(
        (tmp_path / "sweeps" / "S1" / "CAND-0001" / "manifest.yaml").read_text(
            encoding="utf-8"
        )
    )
    assert len(man["records"]) == 1


def test_same_bytes_different_source_reference(tmp_path: Path) -> None:
    payload = b"shared-bytes"
    a = _capture(tmp_path, raw_bytes=payload, source_reference="doc-a")
    b = _capture(tmp_path, raw_bytes=payload, source_reference="doc-b")
    assert a.sha256 == b.sha256
    objects = [
        p
        for p in (tmp_path / "sweeps" / "S1" / "CAND-0001" / "objects").iterdir()
        if not p.name.startswith(".")
    ]
    assert len(objects) == 1
    man = yaml.safe_load(
        (tmp_path / "sweeps" / "S1" / "CAND-0001" / "manifest.yaml").read_text(
            encoding="utf-8"
        )
    )
    assert len(man["records"]) == 2
    assert {r["source_reference"] for r in man["records"]} == {"doc-a", "doc-b"}


def test_different_bytes_same_source_reference_keeps_first_object(tmp_path: Path) -> None:
    first = b"version-one"
    second = b"version-two-different"
    a = _capture(tmp_path, raw_bytes=first, source_reference="doc-a")
    b = _capture(tmp_path, raw_bytes=second, source_reference="doc-a")
    assert a.sha256 != b.sha256
    obj_a = tmp_path / "sweeps" / "S1" / "CAND-0001" / "objects" / a.sha256
    assert obj_a.read_bytes() == first
    objects = [
        p
        for p in (tmp_path / "sweeps" / "S1" / "CAND-0001" / "objects").iterdir()
        if not p.name.startswith(".")
    ]
    assert len(objects) == 2
    man = yaml.safe_load(
        (tmp_path / "sweeps" / "S1" / "CAND-0001" / "manifest.yaml").read_text(
            encoding="utf-8"
        )
    )
    assert len(man["records"]) == 2
    assert "latest" not in man
    assert "correction" not in man["records"][1]


def test_conflicting_optional_metadata_fail_closed(tmp_path: Path) -> None:
    payload = b"meta"
    _capture(
        tmp_path,
        raw_bytes=payload,
        source_reference="doc-a",
        retrieved_on="2099-01-01",
    )
    with pytest.raises(CaptureError, match="conflicting optional"):
        _capture(
            tmp_path,
            raw_bytes=payload,
            source_reference="doc-a",
            retrieved_on="2099-12-31",
        )


def test_existing_object_verified_never_overwritten(tmp_path: Path) -> None:
    payload = b"immutable"
    rec = _capture(tmp_path, raw_bytes=payload, source_reference="doc-a")
    obj = tmp_path / "sweeps" / "S1" / "CAND-0001" / "objects" / rec.sha256
    before = obj.read_bytes()
    _capture(tmp_path, raw_bytes=payload, source_reference="doc-b")
    assert obj.read_bytes() == before == payload


def test_corrupt_existing_object_fail_closed(tmp_path: Path) -> None:
    payload = b"good"
    digest = _sha(payload)
    objects = tmp_path / "sweeps" / "S1" / "CAND-0001" / "objects"
    objects.mkdir(parents=True)
    bad = objects / digest
    bad.write_bytes(b"CORRUPTED-CONTENT")
    with pytest.raises(CaptureError, match="corrupt|mismatch"):
        _capture(tmp_path, raw_bytes=payload, source_reference="doc-a")


def test_prior_manifest_records_unchanged_after_append(tmp_path: Path) -> None:
    first = _capture(tmp_path, raw_bytes=b"one", source_reference="doc-a")
    man1 = yaml.safe_load(
        (tmp_path / "sweeps" / "S1" / "CAND-0001" / "manifest.yaml").read_text(
            encoding="utf-8"
        )
    )
    first_rec = man1["records"][0]
    _capture(tmp_path, raw_bytes=b"two", source_reference="doc-b")
    man2 = yaml.safe_load(
        (tmp_path / "sweeps" / "S1" / "CAND-0001" / "manifest.yaml").read_text(
            encoding="utf-8"
        )
    )
    assert man2["records"][:-1] == [first_rec]
    assert man2["records"][0]["sha256"] == first.sha256


def test_deterministic_manifest_serialization() -> None:
    records = [
        CaptureRecord(source_reference="a", sha256="a" * 64, byte_length=1),
        CaptureRecord(
            source_reference="b",
            sha256="b" * 64,
            byte_length=2,
            retrieved_on="2099-01-01",
        ),
    ]
    a = render_capture_manifest_yaml(
        schema_version=CAPTURE_MANIFEST_SCHEMA_VERSION,
        candidate_id="CAND-0001",
        sweep_id="S1",
        records=records,
    )
    b = render_capture_manifest_yaml(
        schema_version=CAPTURE_MANIFEST_SCHEMA_VERSION,
        candidate_id="CAND-0001",
        sweep_id="S1",
        records=records,
    )
    assert a == b
    assert b"schema_version:" in a


def test_optional_fields_not_fabricated(tmp_path: Path) -> None:
    rec = _capture(tmp_path, raw_bytes=b"plain", source_reference="doc-a")
    assert rec.retrieved_on is None
    assert rec.original_filename is None
    assert rec.content_type is None
    man = yaml.safe_load(
        (tmp_path / "sweeps" / "S1" / "CAND-0001" / "manifest.yaml").read_text(
            encoding="utf-8"
        )
    )
    assert "retrieved_on" not in man["records"][0]
    assert "original_filename" not in man["records"][0]
    assert "content_type" not in man["records"][0]


def test_original_filename_does_not_influence_path(tmp_path: Path) -> None:
    rec = _capture(
        tmp_path,
        raw_bytes=b"named",
        source_reference="doc-a",
        original_filename="../evil.pdf",
    )
    obj = tmp_path / "sweeps" / "S1" / "CAND-0001" / "objects" / rec.sha256
    assert obj.is_file()
    assert not (tmp_path / "evil.pdf").exists()
    assert list((tmp_path / "sweeps" / "S1" / "CAND-0001" / "objects").glob("*")) == [
        obj
    ]


def test_no_episode_keyed_storage_created(tmp_path: Path) -> None:
    _capture(tmp_path, raw_bytes=b"x", source_reference="doc-a")
    assert not (tmp_path / "episodes").exists()
    assert (tmp_path / "sweeps" / "S1" / "CAND-0001").is_dir()


def test_live_prereg_rules_yaml_exists() -> None:
    """After Phase 0 ratification, live prereg_rules.yaml must exist."""
    assert (REPO / "config/discovery/prereg_rules.yaml").exists()


def test_d5_artifacts_exist_and_not_modified_by_capture(tmp_path: Path) -> None:
    """Verify D5 artifacts exist and capture doesn't modify them."""
    # D5 artifacts exist after authorized build
    assert (REPO / CANONICAL_CANDIDATES_RELATIVE).exists()
    assert (REPO / CANONICAL_CANDIDATE_UNIVERSE_MANIFEST_RELATIVE).exists()
    # Record state before capture
    candidates_before = (REPO / CANONICAL_CANDIDATES_RELATIVE).read_bytes()
    manifest_before = (REPO / CANONICAL_CANDIDATE_UNIVERSE_MANIFEST_RELATIVE).read_bytes()
    # Capture operation
    _capture(tmp_path, raw_bytes=b"x", source_reference="doc-a")
    # Verify artifacts unchanged by capture
    assert (REPO / CANONICAL_CANDIDATES_RELATIVE).read_bytes() == candidates_before
    assert (REPO / CANONICAL_CANDIDATE_UNIVERSE_MANIFEST_RELATIVE).read_bytes() == manifest_before
    # Capture doesn't create new candidates.csv in tmp_path
    assert not list(tmp_path.glob("**/candidates.csv"))


def test_real_candidate_artifact_exists_but_no_episode_artifact_in_repo() -> None:
    """Verify D5 candidates exist but no real episodes yet."""
    # D5 candidates exist after authorized build
    assert (REPO / CANONICAL_CANDIDATES_RELATIVE).exists()
    # No episode dispositions yet (created later in workflow)
    assert not (
        REPO / "research/episodes/discovery/candidates/no_episode_dispositions.csv"
    ).exists()
    # No real episode entries yet (only example entries)
    real_eps = [
        p
        for p in (REPO / "research/episodes/entries").glob("*.yaml")
        if not p.name.startswith("EP-0000-000")
    ]
    assert real_eps == []


def test_schema_file_documents_required_shape() -> None:
    schema = yaml.safe_load(
        (
            REPO
            / "research/episodes/discovery/candidates/capture_manifest.schema.yaml"
        ).read_text(encoding="utf-8")
    )
    assert schema["top_level_required_fields"] == [
        "schema_version",
        "candidate_id",
        "sweep_id",
        "records",
    ]
    assert "sha256" in schema["record_required_fields"]
    assert "correction" in schema["forbidden_record_fields"]
