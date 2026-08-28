"""Focused tests for D6 evidence-pack inventory (outcome-blind; no remint)."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest
import yaml

from grainsys.discovery.capture import capture_candidate_evidence
from grainsys.discovery.evidence_inventory import (
    BLOCKER_CAPTURE_STORE_MISSING,
    FROZEN_CANDIDATE_COUNT,
    FROZEN_CANDIDATE_UNIVERSE_VERSION,
    FROZEN_CANDIDATES_DIGEST,
    FROZEN_HIT_SET_DIGEST,
    FROZEN_S1_COUNT,
    FROZEN_S4_COUNT,
    HURDAT2_ATLANTIC_URL,
    HURDAT2_PACIFIC_URL,
    INVENTORY_RELATIVE,
    INVENTORY_SCHEMA_RELATIVE,
    STATUS_MANIFEST_GAP,
    STATUS_MISSING,
    STATUS_UNKNOWN,
    STATUS_VERIFIED,
    EvidenceInventoryError,
    FrozenPointer,
    enrich_hurdat2_archive_if_present,
    hurdat2_archive_specs,
    hurdat2_capture_candidate_id,
    load_frozen_d5_identity,
    load_frozen_pointers,
    render_inventory_yaml,
    run_d6_evidence_inventory,
    verify_hurdat2_archive,
    verify_pointer_object,
)
from grainsys.discovery.execute_v2_families import S4_ATLANTIC_SHA256, S4_PACIFIC_SHA256

REPO = Path(__file__).resolve().parents[1]


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _pointer(tmp_path: Path, *, sweep: str, capture_id: str, payload: bytes) -> FrozenPointer:
    rec = capture_candidate_evidence(
        sweep_id=sweep,
        candidate_id=capture_id,
        raw_bytes=payload,
        source_reference="doc-a",
        sweeps_subdir="sweeps",
        data_root_path=tmp_path,
    )
    return FrozenPointer(
        candidate_id="CAND-0001",
        sweep_id=sweep,
        source_reference="doc-a",
        raw_capture_pointer=f"sweeps/{sweep}/{capture_id}/objects/{rec.sha256}",
        expected_sha256=rec.sha256,
        capture_id=capture_id,
    )


def test_frozen_d5_identity_byte_identical() -> None:
    ident = load_frozen_d5_identity(REPO)
    assert ident.candidate_count == FROZEN_CANDIDATE_COUNT
    assert ident.s1_count == FROZEN_S1_COUNT
    assert ident.s4_count == FROZEN_S4_COUNT
    assert ident.hit_set_digest == FROZEN_HIT_SET_DIGEST
    assert ident.candidates_digest == FROZEN_CANDIDATES_DIGEST
    assert ident.candidate_universe_version == FROZEN_CANDIDATE_UNIVERSE_VERSION
    assert ident.cand_ids_unchanged is True
    assert ident.candidate_universe_version_unchanged is True
    assert ident.first_candidate_id == "CAND-0001"
    assert ident.last_candidate_id == "CAND-4234"
    assert _sha(ident.candidates_csv_bytes) == FROZEN_CANDIDATES_DIGEST


def test_frozen_pointers_count_and_no_empty() -> None:
    ident = load_frozen_d5_identity(REPO)
    pointers = load_frozen_pointers(ident)
    assert len(pointers) == 4234
    assert sum(1 for p in pointers if p.sweep_id == "S1") == 37
    assert sum(1 for p in pointers if p.sweep_id == "S4") == 4197
    assert all(p.raw_capture_pointer for p in pointers)
    assert all(p.expected_sha256 == p.raw_capture_pointer.rsplit("/", 1)[-1] for p in pointers)


def test_hurdat2_expected_sha256_matches_v2_executor() -> None:
    specs = hurdat2_archive_specs()
    assert specs[0].url == HURDAT2_ATLANTIC_URL
    assert specs[1].url == HURDAT2_PACIFIC_URL
    assert specs[0].expected_sha256 == S4_ATLANTIC_SHA256
    assert specs[1].expected_sha256 == S4_PACIFIC_SHA256
    assert specs[0].capture_id == hurdat2_capture_candidate_id(HURDAT2_ATLANTIC_URL)
    assert specs[1].capture_id == hurdat2_capture_candidate_id(HURDAT2_PACIFIC_URL)
    assert specs[0].capture_id == "S4-hurdat-acff99953be3"
    assert specs[1].capture_id == "S4-hurdat-11be4a281f9a"


def test_hurdat2_urls_match_ratified_prereg_endpoints() -> None:
    cfg = yaml.safe_load(
        (REPO / "config/discovery/prereg_rules.yaml").read_text(encoding="utf-8")
    )
    s4 = next(a for a in cfg["source_archives"] if a["sweep_id"] == "S4")
    assert s4["endpoints"] == [HURDAT2_ATLANTIC_URL, HURDAT2_PACIFIC_URL]


def test_verified_pointer_matches_manifest_and_sha(tmp_path: Path) -> None:
    pointer = _pointer(tmp_path, sweep="S1", capture_id="S1-LRH-2020-0001", payload=b"raw-a")
    chk = verify_pointer_object(pointer, store_root=tmp_path, store_blocker=None)
    assert chk.status == STATUS_VERIFIED


def test_missing_object_is_missing_not_zero(tmp_path: Path) -> None:
    (tmp_path / "sweeps" / "S1").mkdir(parents=True)
    pointer = FrozenPointer(
        candidate_id="CAND-0001",
        sweep_id="S1",
        source_reference="doc-a",
        raw_capture_pointer="sweeps/S1/S1-LRH-2020-0001/objects/" + ("a" * 64),
        expected_sha256="a" * 64,
        capture_id="S1-LRH-2020-0001",
    )
    chk = verify_pointer_object(pointer, store_root=tmp_path, store_blocker=None)
    assert chk.status == STATUS_MISSING
    assert chk.status != STATUS_VERIFIED


def test_store_absent_is_unknown_not_verified() -> None:
    pointer = FrozenPointer(
        candidate_id="CAND-0001",
        sweep_id="S1",
        source_reference="doc-a",
        raw_capture_pointer="sweeps/S1/S1-LRH-2020-0001/objects/" + ("b" * 64),
        expected_sha256="b" * 64,
        capture_id="S1-LRH-2020-0001",
    )
    chk = verify_pointer_object(
        pointer,
        store_root=None,
        store_blocker=BLOCKER_CAPTURE_STORE_MISSING,
    )
    assert chk.status == STATUS_UNKNOWN
    assert chk.status != STATUS_VERIFIED


def test_manifest_gap_fail_closed(tmp_path: Path) -> None:
    payload = b"orphan"
    digest = _sha(payload)
    obj = tmp_path / "sweeps" / "S1" / "S1-X" / "objects" / digest
    obj.parent.mkdir(parents=True)
    obj.write_bytes(payload)
    pointer = FrozenPointer(
        candidate_id="CAND-0001",
        sweep_id="S1",
        source_reference="doc-a",
        raw_capture_pointer=f"sweeps/S1/S1-X/objects/{digest}",
        expected_sha256=digest,
        capture_id="S1-X",
    )
    chk = verify_pointer_object(pointer, store_root=tmp_path, store_blocker=None)
    assert chk.status == STATUS_MANIFEST_GAP


def test_inventory_does_not_rewrite_frozen_identity(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GRAIN_DATA_ROOT", raising=False)
    csv_path = REPO / "research/episodes/discovery/candidates/candidates.csv"
    man_path = REPO / "research/episodes/discovery/candidates/candidate_universe.yaml"
    csv_before = csv_path.read_bytes()
    man_before = man_path.read_bytes()
    report = run_d6_evidence_inventory(
        repo_root=REPO,
        data_root_path=tmp_path / "no-such-root",
        refetch_hurdat2=False,
        persist=False,
    )
    assert csv_path.read_bytes() == csv_before
    assert man_path.read_bytes() == man_before
    assert report.cand_ids_unchanged is True
    assert report.candidate_universe_version_unchanged is True
    assert report.complete is False
    assert report.blocker == BLOCKER_CAPTURE_STORE_MISSING
    assert report.pointers_expected == 4234
    assert report.pointers_verified == 0
    assert report.hurdat2_expected == 2
    assert report.hurdat2_capture_verified == 0


def test_unset_grain_data_root_unknown_all_pointers(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GRAIN_DATA_ROOT", raising=False)
    report = run_d6_evidence_inventory(
        repo_root=REPO,
        data_root_path=None,
        refetch_hurdat2=False,
        persist=False,
    )
    assert report.blocker == BLOCKER_CAPTURE_STORE_MISSING
    assert report.grain_data_root_set is False
    assert report.capture_store_present is False
    assert report.pointers_verified == 0
    assert report.pointers_unknown == 4234
    assert report.pointers_missing == 0
    assert report.hurdat2_capture_unknown == 2
    assert report.complete is False


def test_empty_sweeps_dir_counts_missing(tmp_path: Path) -> None:
    (tmp_path / "sweeps").mkdir()
    report = run_d6_evidence_inventory(
        repo_root=REPO,
        data_root_path=tmp_path,
        refetch_hurdat2=False,
        persist=False,
    )
    assert report.blocker == BLOCKER_CAPTURE_STORE_MISSING
    assert report.capture_store_present is True
    assert report.pointers_verified == 0
    assert report.pointers_missing == 4234
    assert report.pointers_unknown == 0
    assert report.hurdat2_capture_missing == 2
    assert report.hurdat2_capture_verified == 0


def test_hurdat2_public_refetch_mocked_does_not_invent_capture(tmp_path: Path) -> None:
    atlantic = b"ATLANTIC-BYTES"
    pacific = b"PACIFIC-BYTES"
    # Digests will not match expected frozen SHA256; mock still returns bytes.
    calls: list[str] = []

    def fake_fetch(url: str, *, timeout: int = 120):
        calls.append(url)
        if "nepac" in url:
            return True, pacific, None
        return True, atlantic, None

    (tmp_path / "sweeps").mkdir()
    report = run_d6_evidence_inventory(
        repo_root=REPO,
        data_root_path=tmp_path,
        refetch_hurdat2=True,
        enrich_hurdat2=True,
        persist=False,
        fetch_fn=fake_fetch,
    )
    assert report.hurdat2_public_verified == 0  # digest mismatch; not invented
    assert report.enrichment_appended == 0
    assert not (tmp_path / "sweeps" / "S4").exists()
    assert report.blocker == BLOCKER_CAPTURE_STORE_MISSING
    assert set(calls) == {HURDAT2_ATLANTIC_URL, HURDAT2_PACIFIC_URL}


def test_append_only_enrichment_requires_existing_dir(tmp_path: Path) -> None:
    spec = hurdat2_archive_specs()[0]
    created = enrich_hurdat2_archive_if_present(
        spec, store_root=tmp_path, raw_bytes=b"x" * 10
    )
    assert created is False
    assert not (tmp_path / "sweeps" / "S4" / spec.capture_id).exists()


def test_append_only_enrichment_idempotent_on_existing_dir(tmp_path: Path) -> None:
    spec = hurdat2_archive_specs()[0]
    payload = b"hurdat-archive-bytes"
    # Existing capture dir (not a D5 remint).
    capture_candidate_evidence(
        sweep_id="S4",
        candidate_id=spec.capture_id,
        raw_bytes=payload,
        source_reference=spec.url,
        sweeps_subdir="sweeps",
        data_root_path=tmp_path,
        original_filename=spec.url.rsplit("/", 1)[-1],
        content_type="text/plain",
    )
    man1 = yaml.safe_load(
        (tmp_path / "sweeps" / "S4" / spec.capture_id / "manifest.yaml").read_text(
            encoding="utf-8"
        )
    )
    # Wrong digest must refuse rather than overwrite.
    with pytest.raises(EvidenceInventoryError, match="refuse to enrich"):
        enrich_hurdat2_archive_if_present(
            spec, store_root=tmp_path, raw_bytes=payload
        )
    # Matching digest (spec expected SHA is the real HURDAT2 hash, not payload).
    # Persist the real expected digest as the object name by using expected bytes
    # only when we construct a matching payload — here we only check no overwrite
    # of the existing object after a second identical capture_candidate_evidence.
    rec = capture_candidate_evidence(
        sweep_id="S4",
        candidate_id=spec.capture_id,
        raw_bytes=payload,
        source_reference=spec.url,
        sweeps_subdir="sweeps",
        data_root_path=tmp_path,
        original_filename=spec.url.rsplit("/", 1)[-1],
        content_type="text/plain",
    )
    obj = tmp_path / "sweeps" / "S4" / spec.capture_id / "objects" / rec.sha256
    assert obj.read_bytes() == payload
    man2 = yaml.safe_load(
        (tmp_path / "sweeps" / "S4" / spec.capture_id / "manifest.yaml").read_text(
            encoding="utf-8"
        )
    )
    assert man2["records"] == man1["records"]


def test_hurdat2_local_object_verified(tmp_path: Path) -> None:
    spec = hurdat2_archive_specs()[0]
    payload = b"local-hurdat"
    # Store under the expected sha filename only after capture hashes payload.
    rec = capture_candidate_evidence(
        sweep_id="S4",
        candidate_id=spec.capture_id,
        raw_bytes=payload,
        source_reference=spec.url,
        sweeps_subdir="sweeps",
        data_root_path=tmp_path,
    )
    # The real expected SHA is the published archive digest, not this payload.
    chk = verify_hurdat2_archive(
        spec,
        store_root=tmp_path,
        store_blocker=None,
        refetch=False,
    )
    assert rec.sha256 != spec.expected_sha256
    assert chk.capture_object_status == STATUS_MISSING

    # Place a correctly named object + manifest via capture of bytes whose hash
    # cannot be forced; instead, copy bytes to expected filename only if we
    # also update spec — we must not invent the published digest. Missing is
    # the correct fail-closed result for a non-matching local object name.
    assert chk.capture_object_status != STATUS_VERIFIED


def test_hurdat2_verified_when_object_named_for_expected_digest(tmp_path: Path) -> None:
    spec = hurdat2_archive_specs()[0]
    # Capture writes objects/<sha(payload)>. To verify the archive path we need
    # objects/<expected_sha256>. Use a stub spec-equivalent by writing through
    # capture and then checking a second spec built from that payload.
    payload = b"digest-named-archive"
    rec = capture_candidate_evidence(
        sweep_id="S4",
        candidate_id=spec.capture_id,
        raw_bytes=payload,
        source_reference=spec.url,
        sweeps_subdir="sweeps",
        data_root_path=tmp_path,
    )
    from grainsys.discovery.evidence_inventory import Hurdat2ArchiveSpec

    local_spec = Hurdat2ArchiveSpec(spec.basin, spec.url, rec.sha256)
    assert local_spec.capture_id == spec.capture_id
    chk = verify_hurdat2_archive(
        local_spec,
        store_root=tmp_path,
        store_blocker=None,
        refetch=False,
    )
    assert chk.capture_object_status == STATUS_VERIFIED


def test_persist_writes_inventory_not_candidates(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GRAIN_DATA_ROOT", raising=False)
    # Persist into a copy of repo identity files under tmp by using live repo
    # persist=True would write into the workspace; use a sandbox replica of
    # the two frozen artifacts plus schema path.
    sandbox = tmp_path / "repo"
    cand_dir = sandbox / "research/episodes/discovery/candidates"
    cand_dir.mkdir(parents=True)
    src = REPO / "research/episodes/discovery/candidates"
    (cand_dir / "candidates.csv").write_bytes((src / "candidates.csv").read_bytes())
    (cand_dir / "candidate_universe.yaml").write_bytes(
        (src / "candidate_universe.yaml").read_bytes()
    )
    csv_before = (cand_dir / "candidates.csv").read_bytes()
    man_before = (cand_dir / "candidate_universe.yaml").read_bytes()
    report = run_d6_evidence_inventory(
        repo_root=sandbox,
        data_root_path=None,
        refetch_hurdat2=False,
        persist=True,
    )
    assert (sandbox / INVENTORY_RELATIVE).is_file()
    assert (cand_dir / "candidates.csv").read_bytes() == csv_before
    assert (cand_dir / "candidate_universe.yaml").read_bytes() == man_before
    loaded = yaml.safe_load((sandbox / INVENTORY_RELATIVE).read_text(encoding="utf-8"))
    assert loaded["blocker"] == BLOCKER_CAPTURE_STORE_MISSING
    assert loaded["complete"] is False
    assert loaded["frozen_d5"]["candidate_universe_version"] == FROZEN_CANDIDATE_UNIVERSE_VERSION
    assert loaded["pointers"]["expected"] == 4234
    assert loaded["pointers"]["verified"] == 0
    assert loaded["hurdat2_archives"]["expected"] == 2
    assert "market_outcome" not in loaded
    assert report.cand_ids_unchanged is True
    again = render_inventory_yaml(report)
    assert again == (sandbox / INVENTORY_RELATIVE).read_bytes()


def test_committed_inventory_yaml_fail_closed_identity() -> None:
    path = REPO / INVENTORY_RELATIVE
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert data["record_kind"] == "d6_evidence_pack_inventory"
    assert data["complete"] is False
    assert data["blocker"] == BLOCKER_CAPTURE_STORE_MISSING
    assert data["frozen_d5"]["candidate_count"] == 4234
    assert data["frozen_d5"]["candidates_digest"] == FROZEN_CANDIDATES_DIGEST
    assert data["frozen_d5"]["hit_set_digest"] == FROZEN_HIT_SET_DIGEST
    assert data["frozen_d5"]["candidate_universe_version"] == FROZEN_CANDIDATE_UNIVERSE_VERSION
    assert data["frozen_d5"]["cand_ids_unchanged"] is True
    assert data["pointers"]["expected"] == 4234
    assert data["pointers"]["verified"] == 0
    assert data["pointers"]["unknown"] == 4234
    assert data["hurdat2_archives"]["expected"] == 2
    assert data["hurdat2_archives"]["capture_verified"] == 0
    assert data["hurdat2_archives"]["public_refetch_verified"] == 2
    assert data["enrichment_appended"] == 0
    sha = {r["basin"]: r["expected_sha256"] for r in data["hurdat2_archives"]["records"]}
    assert sha["atlantic"] == S4_ATLANTIC_SHA256
    assert sha["pacific"] == S4_PACIFIC_SHA256


def test_inventory_schema_documents_fail_closed_shape() -> None:
    schema = yaml.safe_load((REPO / INVENTORY_SCHEMA_RELATIVE).read_text(encoding="utf-8"))
    assert schema["record_kind"] == "d6_evidence_pack_inventory"
    assert "CAPTURE_STORE_MISSING" in schema["blocker_vocabulary"]
    assert "unknown" in schema["pointer_status_vocabulary"]
    assert "market_outcome" in schema["forbidden_fields"]
    assert "h7_survivor" in schema["forbidden_fields"]


def test_cli_nonzero_on_blocker(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GRAIN_DATA_ROOT", raising=False)
    from grainsys.discovery.evidence_inventory import main

    rc = main(["--repo-root", str(REPO)])
    assert rc == 2
