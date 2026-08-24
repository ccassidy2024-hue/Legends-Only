"""Focused tests for D5 candidate-universe mechanics (PR-A)."""

from __future__ import annotations

import inspect
from pathlib import Path
from unittest.mock import patch

import pytest

from grainsys.discovery.candidate_universe import (
    CANDIDATES_CSV_FIELDNAMES,
    CANONICAL_CANDIDATE_UNIVERSE_MANIFEST_RELATIVE,
    CANONICAL_CANDIDATES_RELATIVE,
    D5_ID_PREFIX,
    D5_ORDERING_KEYS,
    D5_STABLE_ID_KEY,
    CandidateUniverseError,
    UnsupportedCandidateUniverseSupersession,
    build_authorized_d5_candidate_universe,
    build_manifest,
    candidate_universe_version_from_hit_set_digest,
    freeze_hit_set,
    mint_d5_candidate_ids,
    render_candidates_csv_bytes,
    write_canonical_candidates_csv,
    write_canonical_universe_artifacts,
)
from grainsys.discovery.candidates import (
    CandidateIdError,
    mint_candidate_ids,
    researcher_parity_for_candidate_id,
)
from grainsys.discovery.governance import LOAD_BEARING_RELATIVE_PATHS

# Frozen N3 boundary. Any change must be explicit here and in governance tests.
_EXPECTED_LOAD_BEARING = (
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

_FAMILIES = ("S1", "S2")
_ATTEST = {"S1": True, "S2": True}


def _hits_ab() -> list[dict[str, str]]:
    return [
        {
            "sweep_id": "S2",
            "source_reference": "doc-b",
            "raw_capture_pointer": "raw/b",
            "document_date": "2020-02-01",
        },
        {
            "sweep_id": "S1",
            "source_reference": "doc-a",
            "raw_capture_pointer": "raw/a",
            "document_date": "2020-01-01",
        },
    ]


def _ok_auth(repo_root, *, execution_commit=None):
    return None


def test_n3_load_bearing_tuple_matches_explicit_boundary() -> None:
    assert LOAD_BEARING_RELATIVE_PATHS == _EXPECTED_LOAD_BEARING
    assert "candidate_universe.schema.yaml" not in LOAD_BEARING_RELATIVE_PATHS
    assert "candidate_universe.py" not in " ".join(LOAD_BEARING_RELATIVE_PATHS)


def test_generic_mint_primitive_remains_parameterized_and_pure() -> None:
    src = inspect.getsource(mint_candidate_ids)
    for banned in (
        "open(",
        "Path(",
        "assert_sweep_authorized",
        "load_prereg_rules",
        "datetime",
        "time.",
        "os.environ",
    ):
        assert banned not in src
    minted = mint_candidate_ids(
        [{"document_date": "2020-01-01", "source_reference": "x"}],
        ordering_keys=["document_date", "source_reference"],
        id_prefix="TMP",
        stable_id_key=None,
    )
    assert minted[0]["candidate_id"] == "TMP-0001"


def test_d5_wrapper_binds_ratified_constants() -> None:
    assert D5_ID_PREFIX == "CAND"
    assert D5_ORDERING_KEYS == ("sweep_id", "source_reference")
    assert D5_STABLE_ID_KEY is None
    minted = mint_d5_candidate_ids(_hits_ab())
    assert [r["candidate_id"] for r in minted] == ["CAND-0001", "CAND-0002"]
    assert minted[0]["sweep_id"] == "S1"
    assert minted[0]["source_reference"] == "doc-a"
    sig = inspect.signature(mint_d5_candidate_ids)
    assert list(sig.parameters) == ["hits"]


def test_identical_frozen_hit_set_byte_identical_outputs() -> None:
    a = freeze_hit_set(
        _hits_ab(),
        required_sweep_families=_FAMILIES,
        family_completion_attestations=_ATTEST,
    )
    b = freeze_hit_set(
        list(reversed(_hits_ab())),
        required_sweep_families=_FAMILIES,
        family_completion_attestations=_ATTEST,
    )
    assert a.hit_set_digest == b.hit_set_digest
    assert len(a.hit_set_digest) == 64
    ca = mint_d5_candidate_ids(list(a.hits))
    cb = mint_d5_candidate_ids(list(b.hits))
    ba = render_candidates_csv_bytes(ca)
    bb = render_candidates_csv_bytes(cb)
    assert ba == bb
    assert ba.count(b"\n") >= 3
    assert b"episode_id" not in ba


def test_full_universe_version_token_same_and_different_hit_sets() -> None:
    a = freeze_hit_set(
        _hits_ab(),
        required_sweep_families=_FAMILIES,
        family_completion_attestations=_ATTEST,
    )
    b = freeze_hit_set(
        list(reversed(_hits_ab())),
        required_sweep_families=_FAMILIES,
        family_completion_attestations=_ATTEST,
    )
    va = candidate_universe_version_from_hit_set_digest(a.hit_set_digest)
    vb = candidate_universe_version_from_hit_set_digest(b.hit_set_digest)
    assert va == vb
    assert va == f"d5cu-{a.hit_set_digest}"
    assert va.startswith("d5cu-")
    assert len(va) == len("d5cu-") + 64
    # Truncation must not be used.
    assert va != f"d5cu-{a.hit_set_digest[:16]}"

    other_hits = [
        {
            "sweep_id": "S1",
            "source_reference": "other-a",
            "raw_capture_pointer": "raw/oa",
        },
        {
            "sweep_id": "S2",
            "source_reference": "other-b",
            "raw_capture_pointer": "raw/ob",
        },
    ]
    c = freeze_hit_set(
        other_hits,
        required_sweep_families=_FAMILIES,
        family_completion_attestations=_ATTEST,
    )
    vc = candidate_universe_version_from_hit_set_digest(c.hit_set_digest)
    assert vc != va
    assert vc == f"d5cu-{c.hit_set_digest}"
    assert len(vc) == len("d5cu-") + 64


def test_enumeration_order_invariant() -> None:
    fwd = mint_d5_candidate_ids(_hits_ab())
    rev = mint_d5_candidate_ids(list(reversed(_hits_ab())))
    assert [r["candidate_id"] for r in fwd] == [r["candidate_id"] for r in rev]
    assert [r["source_reference"] for r in fwd] == [r["source_reference"] for r in rev]


def test_duplicate_ordering_tuple_fail_closed() -> None:
    hits = [
        {"sweep_id": "S1", "source_reference": "same"},
        {"sweep_id": "S1", "source_reference": "same"},
    ]
    with pytest.raises(CandidateIdError, match="duplicate"):
        mint_d5_candidate_ids(hits)


def test_unexpected_sweep_family_fail_closed() -> None:
    """required={S1,S2} with hits including S3 ⇒ fail closed (not ignore/expand)."""
    hits = [
        *_hits_ab(),
        {
            "sweep_id": "S3",
            "source_reference": "doc-c",
            "raw_capture_pointer": "raw/c",
        },
    ]
    with pytest.raises(CandidateUniverseError, match="unexpected|outside required"):
        freeze_hit_set(
            hits,
            required_sweep_families=["S1", "S2"],
            family_completion_attestations={"S1": True, "S2": True},
        )


def test_extra_attestation_family_fail_closed() -> None:
    with pytest.raises(CandidateUniverseError, match="unexpected"):
        freeze_hit_set(
            _hits_ab(),
            required_sweep_families=["S1", "S2"],
            family_completion_attestations={"S1": True, "S2": True, "S3": True},
        )


def test_malformed_attestation_family_mismatch_fail_closed() -> None:
    with pytest.raises(CandidateUniverseError, match="mismatch|malformed"):
        freeze_hit_set(
            _hits_ab(),
            required_sweep_families=["S1", "S2"],
            family_completion_attestations={
                "S1": {"status": "complete", "sweep_family": "S9"},
                "S2": True,
            },
        )


def test_missing_required_sweep_family_hits_fail_closed() -> None:
    with pytest.raises(CandidateUniverseError, match="no hits for required"):
        freeze_hit_set(
            [
                {
                    "sweep_id": "S1",
                    "source_reference": "x",
                    "raw_capture_pointer": "r",
                }
            ],
            required_sweep_families=["S1", "S2"],
            family_completion_attestations={"S1": True, "S2": True},
        )


def test_incomplete_attestation_fail_closed() -> None:
    with pytest.raises(CandidateUniverseError, match="not attested complete"):
        freeze_hit_set(
            _hits_ab(),
            required_sweep_families=_FAMILIES,
            family_completion_attestations={"S1": True, "S2": False},
        )
    with pytest.raises(CandidateUniverseError, match="lacks a completion attestation"):
        freeze_hit_set(
            _hits_ab(),
            required_sweep_families=_FAMILIES,
            family_completion_attestations={"S1": True},
        )


def test_absent_required_families_fail_closed() -> None:
    with pytest.raises(CandidateUniverseError, match="empty/absent"):
        freeze_hit_set(
            _hits_ab(),
            required_sweep_families=[],
            family_completion_attestations={},
        )


def test_ids_contiguous_one_through_n() -> None:
    hits = [{"sweep_id": "S1", "source_reference": f"d{i}"} for i in (3, 1, 2, 5, 4)]
    minted = mint_d5_candidate_ids(hits)
    assert [r["candidate_id"] for r in minted] == [
        "CAND-0001",
        "CAND-0002",
        "CAND-0003",
        "CAND-0004",
        "CAND-0005",
    ]


def test_odd_even_parity_helper() -> None:
    assert researcher_parity_for_candidate_id("CAND-0001") == "A"
    assert researcher_parity_for_candidate_id("CAND-0002") == "B"
    assert researcher_parity_for_candidate_id("CAND-0010") == "B"
    assert researcher_parity_for_candidate_id("CAND-0011") == "A"
    assert researcher_parity_for_candidate_id("CAND-9999") == "A"
    csv_bytes = render_candidates_csv_bytes(mint_d5_candidate_ids(_hits_ab()))
    header = csv_bytes.decode("utf-8").splitlines()[0]
    assert "parity" not in header
    assert "researcher" not in header


def test_csv_only_write_refused() -> None:
    csv_bytes = render_candidates_csv_bytes(mint_d5_candidate_ids(_hits_ab()))
    with pytest.raises(CandidateUniverseError, match="CSV-only|together"):
        write_canonical_candidates_csv(repo_root=Path("/tmp"), csv_bytes=csv_bytes)


def test_dual_persist_and_existing_artifact_refuses_overwrite(tmp_path: Path) -> None:
    frozen = freeze_hit_set(
        _hits_ab(),
        required_sweep_families=_FAMILIES,
        family_completion_attestations=_ATTEST,
    )
    rows = mint_d5_candidate_ids(list(frozen.hits))
    csv_bytes = render_candidates_csv_bytes(rows)
    manifest = build_manifest(
        frozen=frozen, csv_bytes=csv_bytes, candidate_count=len(rows)
    )
    csv_path, man_path = write_canonical_universe_artifacts(
        tmp_path, csv_bytes=csv_bytes, manifest=manifest
    )
    assert csv_path == tmp_path / CANONICAL_CANDIDATES_RELATIVE
    assert man_path == tmp_path / CANONICAL_CANDIDATE_UNIVERSE_MANIFEST_RELATIVE
    assert csv_path.is_file() and man_path.is_file()
    assert csv_path.read_bytes() == csv_bytes
    assert f"d5cu-{frozen.hit_set_digest}".encode() in man_path.read_bytes()

    with pytest.raises(CandidateUniverseError, match="already exists"):
        write_canonical_universe_artifacts(
            tmp_path, csv_bytes=csv_bytes, manifest=manifest
        )


def test_existing_manifest_alone_refuses_partial_overwrite(tmp_path: Path) -> None:
    man = tmp_path / CANONICAL_CANDIDATE_UNIVERSE_MANIFEST_RELATIVE
    man.parent.mkdir(parents=True, exist_ok=True)
    man.write_text("stale: true\n", encoding="utf-8")
    frozen = freeze_hit_set(
        _hits_ab(),
        required_sweep_families=_FAMILIES,
        family_completion_attestations=_ATTEST,
    )
    rows = mint_d5_candidate_ids(list(frozen.hits))
    csv_bytes = render_candidates_csv_bytes(rows)
    manifest = build_manifest(
        frozen=frozen, csv_bytes=csv_bytes, candidate_count=len(rows)
    )
    with pytest.raises(CandidateUniverseError, match="manifest already exists"):
        write_canonical_universe_artifacts(
            tmp_path, csv_bytes=csv_bytes, manifest=manifest
        )
    assert not (tmp_path / CANONICAL_CANDIDATES_RELATIVE).exists()


def test_partial_failure_rolls_back_both_new_artifacts(tmp_path: Path) -> None:
    frozen = freeze_hit_set(
        _hits_ab(),
        required_sweep_families=_FAMILIES,
        family_completion_attestations=_ATTEST,
    )
    rows = mint_d5_candidate_ids(list(frozen.hits))
    csv_bytes = render_candidates_csv_bytes(rows)
    manifest = build_manifest(
        frozen=frozen, csv_bytes=csv_bytes, candidate_count=len(rows)
    )

    csv_final = tmp_path / CANONICAL_CANDIDATES_RELATIVE
    man_final = tmp_path / CANONICAL_CANDIDATE_UNIVERSE_MANIFEST_RELATIVE
    real_replace = Path.replace

    def _boom_on_manifest_replace(self: Path, target: Path) -> Path:
        if self.name.endswith("candidate_universe.yaml.tmp"):
            raise OSError("simulated manifest replace failure")
        return real_replace(self, target)

    with patch.object(Path, "replace", _boom_on_manifest_replace):
        with pytest.raises(CandidateUniverseError, match="atomic dual-persist failed"):
            write_canonical_universe_artifacts(
                tmp_path, csv_bytes=csv_bytes, manifest=manifest
            )

    assert not csv_final.exists()
    assert not man_final.exists()
    assert not list(csv_final.parent.glob("*.tmp"))


def test_missing_authorization_refuses_build(tmp_path: Path) -> None:
    with pytest.raises(CandidateUniverseError, match="authorization"):
        build_authorized_d5_candidate_universe(
            repo_root=tmp_path,
            hits=_hits_ab(),
            required_sweep_families=_FAMILIES,
            family_completion_attestations=_ATTEST,
            persist=False,
        )


def test_missing_required_families_arg_refuses(tmp_path: Path) -> None:
    from grainsys.discovery import candidate_universe as cu

    monkey = pytest.MonkeyPatch()
    monkey.setattr(cu, "assert_sweep_authorized", _ok_auth)
    try:
        with pytest.raises(CandidateUniverseError, match="required_sweep_families is absent"):
            build_authorized_d5_candidate_universe(
                repo_root=tmp_path,
                hits=_hits_ab(),
                required_sweep_families=None,
                family_completion_attestations=_ATTEST,
            )
    finally:
        monkey.undo()


def test_non_null_supersedes_fail_closed(tmp_path: Path) -> None:
    from grainsys.discovery import candidate_universe as cu

    monkey = pytest.MonkeyPatch()
    monkey.setattr(cu, "assert_sweep_authorized", _ok_auth)
    try:
        with pytest.raises(UnsupportedCandidateUniverseSupersession):
            build_authorized_d5_candidate_universe(
                repo_root=tmp_path,
                hits=_hits_ab(),
                required_sweep_families=_FAMILIES,
                family_completion_attestations=_ATTEST,
                supersedes="d5cu-previous",
            )
    finally:
        monkey.undo()


def test_candidate_table_has_no_episode_id_field() -> None:
    assert "episode_id" not in CANDIDATES_CSV_FIELDNAMES
    csv_bytes = render_candidates_csv_bytes(mint_d5_candidate_ids(_hits_ab()))
    assert b"episode_id" not in csv_bytes


def test_frozen_at_does_not_affect_identity(tmp_path: Path) -> None:
    from grainsys.discovery import candidate_universe as cu

    monkey = pytest.MonkeyPatch()
    monkey.setattr(cu, "assert_sweep_authorized", _ok_auth)
    try:
        a = build_authorized_d5_candidate_universe(
            repo_root=tmp_path,
            hits=_hits_ab(),
            required_sweep_families=_FAMILIES,
            family_completion_attestations=_ATTEST,
            persist=False,
            frozen_at="2099-01-01T00:00:00Z",
        )
        b = build_authorized_d5_candidate_universe(
            repo_root=tmp_path,
            hits=_hits_ab(),
            required_sweep_families=_FAMILIES,
            family_completion_attestations=_ATTEST,
            persist=False,
            frozen_at="1999-12-31T23:59:59Z",
        )
        assert a.frozen_hit_set.hit_set_digest == b.frozen_hit_set.hit_set_digest
        assert a.candidates_digest == b.candidates_digest
        assert (
            a.manifest.candidate_universe_version
            == b.manifest.candidate_universe_version
        )
        assert a.candidates_csv_bytes == b.candidates_csv_bytes
        assert a.manifest.frozen_at != b.manifest.frozen_at
        # Identity layer must not call wall-clock helpers (docstring may name them).
        src = inspect.getsource(cu)
        assert "datetime.now(" not in src
        assert "time.time(" not in src
        assert "datetime.utcnow(" not in src
        assert "import datetime" not in src
        assert "from datetime" not in src
        assert "import time" not in src
        assert "from time" not in src
    finally:
        monkey.undo()


def test_authorized_build_persist_roundtrip_dual_artifacts(tmp_path: Path) -> None:
    from grainsys.discovery import candidate_universe as cu

    monkey = pytest.MonkeyPatch()
    monkey.setattr(cu, "assert_sweep_authorized", _ok_auth)
    try:
        result = build_authorized_d5_candidate_universe(
            repo_root=tmp_path,
            hits=_hits_ab(),
            required_sweep_families=_FAMILIES,
            family_completion_attestations=_ATTEST,
            persist=True,
            frozen_at="2099-01-01T00:00:00Z",
        )
        assert result.written_candidates_path is not None
        assert result.written_manifest_path is not None
        assert result.written_candidates_path.read_bytes() == result.candidates_csv_bytes
        assert result.written_manifest_path.is_file()
        assert result.manifest.supersedes is None
        assert result.manifest.id_prefix == "CAND"
        assert result.manifest.ordering_keys == ("sweep_id", "source_reference")
        assert result.manifest.stable_id_key is None
        assert result.manifest.candidate_count == 2
        assert result.manifest.hit_set_digest == result.frozen_hit_set.hit_set_digest
        assert result.manifest.candidate_universe_version == (
            f"d5cu-{result.frozen_hit_set.hit_set_digest}"
        )
        assert len(result.manifest.candidate_universe_version) == len("d5cu-") + 64

        again = build_authorized_d5_candidate_universe(
            repo_root=tmp_path,
            hits=list(reversed(_hits_ab())),
            required_sweep_families=_FAMILIES,
            family_completion_attestations=_ATTEST,
            persist=False,
        )
        assert again.candidates_csv_bytes == result.candidates_csv_bytes
        assert again.frozen_hit_set.hit_set_digest == result.frozen_hit_set.hit_set_digest
        assert again.candidates_digest == result.candidates_digest
        assert (
            again.manifest.candidate_universe_version
            == result.manifest.candidate_universe_version
        )
        with pytest.raises(CandidateUniverseError, match="already exists"):
            build_authorized_d5_candidate_universe(
                repo_root=tmp_path,
                hits=_hits_ab(),
                required_sweep_families=_FAMILIES,
                family_completion_attestations=_ATTEST,
                persist=True,
            )
    finally:
        monkey.undo()


def test_no_live_candidates_or_manifest_in_repo() -> None:
    repo = Path(__file__).resolve().parents[1]
    assert not (repo / CANONICAL_CANDIDATES_RELATIVE).exists()
    assert not (repo / CANONICAL_CANDIDATE_UNIVERSE_MANIFEST_RELATIVE).exists()


def test_future_canonical_manifest_path_constant() -> None:
    assert CANONICAL_CANDIDATE_UNIVERSE_MANIFEST_RELATIVE.as_posix() == (
        "research/episodes/discovery/candidates/candidate_universe.yaml"
    )
