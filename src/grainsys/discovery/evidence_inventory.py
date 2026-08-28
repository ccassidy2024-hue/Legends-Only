"""D6 evidence-pack inventory: verify frozen D5 capture pointers (outcome-blind).

Does not remint candidates, rewrite ``candidates.csv`` identity/lineage, open
market outcomes, or invent capture objects. Missing store/objects fail closed.
UNKNOWN is never treated as zero verified.

Capture persistence, when used, is append-only via
``capture_candidate_evidence`` against already-present candidate directories.
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import urllib.error
import urllib.request
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from grainsys.discovery.candidate_universe import (
    CANONICAL_CANDIDATE_UNIVERSE_MANIFEST_RELATIVE,
    CANONICAL_CANDIDATES_RELATIVE,
)
from grainsys.discovery.capture import (
    MANIFEST_FILENAME,
    OBJECTS_DIRNAME,
    CapturePathError,
    capture_candidate_evidence,
    data_root,
)
from grainsys.discovery.config import REPO_ROOT
from grainsys.discovery.execute_v2_families import S4_ATLANTIC_SHA256, S4_PACIFIC_SHA256

INVENTORY_SCHEMA_VERSION = "1.0"
INVENTORY_RELATIVE = Path(
    "research/episodes/discovery/candidates/d6_evidence_pack_inventory.yaml"
)
INVENTORY_SCHEMA_RELATIVE = Path(
    "research/episodes/discovery/candidates/d6_evidence_pack_inventory.schema.yaml"
)

FROZEN_CANDIDATE_COUNT = 4234
FROZEN_S1_COUNT = 37
FROZEN_S4_COUNT = 4197
FROZEN_HIT_SET_DIGEST = (
    "1cb416ee3b6e9103b4edd60748865d7dd147c80611adfb6c6b5b37eba5258d97"
)
FROZEN_CANDIDATES_DIGEST = (
    "df7f7ffb41f339d75d6a8a2ef68ab113c70490822e03ad21c9ebd8e26dae2c66"
)
FROZEN_CANDIDATE_UNIVERSE_VERSION = (
    "d5cu-1cb416ee3b6e9103b4edd60748865d7dd147c80611adfb6c6b5b37eba5258d97"
)
FROZEN_REQUIRED_SWEEP_FAMILIES: tuple[str, ...] = ("S1", "S4")
SWEEPS_SUBDIR = "sweeps"

HURDAT2_ATLANTIC_URL = (
    "https://www.nhc.noaa.gov/data/hurdat/hurdat2-1851-2025-02272026.txt"
)
HURDAT2_PACIFIC_URL = (
    "https://www.nhc.noaa.gov/data/hurdat/hurdat2-nepac-1949-2025-02272026.txt"
)

STATUS_VERIFIED = "verified"
STATUS_MISSING = "missing"
STATUS_MISMATCH = "mismatch"
STATUS_MANIFEST_GAP = "manifest_gap"
STATUS_UNKNOWN = "unknown"
STATUS_FETCH_FAILED = "fetch_failed"
STATUS_NOT_ATTEMPTED = "not_attempted"

BLOCKER_CAPTURE_STORE_MISSING = "CAPTURE_STORE_MISSING"
BLOCKER_EXTERNAL_ACCESS_BLOCKED = "EXTERNAL_ACCESS_BLOCKED"
BLOCKER_IDENTITY_DRIFT = "FROZEN_D5_IDENTITY_DRIFT"

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_POINTER_RE = re.compile(
    r"^(?P<subdir>[^/]+)/(?P<sweep_id>[^/]+)/(?P<capture_id>[^/]+)/"
    r"objects/(?P<sha256>[0-9a-f]{64})$"
)


class EvidenceInventoryError(ValueError):
    """Fail-closed D6 evidence-pack inventory error."""


@dataclass(frozen=True)
class FrozenPointer:
    candidate_id: str
    sweep_id: str
    source_reference: str
    raw_capture_pointer: str
    expected_sha256: str
    capture_id: str


@dataclass(frozen=True)
class PointerCheck:
    candidate_id: str
    sweep_id: str
    source_reference: str
    raw_capture_pointer: str
    status: str
    detail: str


@dataclass(frozen=True)
class Hurdat2ArchiveSpec:
    basin: str
    url: str
    expected_sha256: str

    @property
    def capture_id(self) -> str:
        return hurdat2_capture_candidate_id(self.url)


@dataclass(frozen=True)
class Hurdat2Check:
    basin: str
    url: str
    expected_sha256: str
    capture_id: str
    capture_object_status: str
    public_refetch_status: str
    observed_sha256: str | None
    detail: str


@dataclass(frozen=True)
class FrozenIdentity:
    candidate_count: int
    s1_count: int
    s4_count: int
    hit_set_digest: str
    candidates_digest: str
    candidate_universe_version: str
    required_sweep_families: tuple[str, ...]
    first_candidate_id: str
    last_candidate_id: str
    cand_ids_unchanged: bool
    candidate_universe_version_unchanged: bool
    candidates_csv_bytes: bytes


@dataclass(frozen=True)
class InventoryReport:
    blocker: str | None
    blocker_detail: str
    complete: bool
    grain_data_root_set: bool
    capture_store_present: bool
    pointers_expected: int
    pointers_verified: int
    pointers_missing: int
    pointers_unknown: int
    pointers_mismatch: int
    pointers_manifest_gap: int
    hurdat2_expected: int
    hurdat2_capture_verified: int
    hurdat2_capture_missing: int
    hurdat2_capture_unknown: int
    hurdat2_public_verified: int
    cand_ids_unchanged: bool
    candidate_universe_version_unchanged: bool
    enrichment_appended: int
    identity: FrozenIdentity
    pointer_checks: tuple[PointerCheck, ...]
    hurdat2_checks: tuple[Hurdat2Check, ...]

    def to_mapping(self) -> dict[str, Any]:
        by_family: dict[str, dict[str, int]] = {}
        for chk in self.pointer_checks:
            fam = by_family.setdefault(
                chk.sweep_id,
                {
                    "expected": 0,
                    "verified": 0,
                    "missing": 0,
                    "unknown": 0,
                    "mismatch": 0,
                    "manifest_gap": 0,
                },
            )
            fam["expected"] += 1
            if chk.status in fam:
                fam[chk.status] += 1
        return {
            "schema_version": INVENTORY_SCHEMA_VERSION,
            "record_kind": "d6_evidence_pack_inventory",
            "outcome_blind": True,
            "blocker": self.blocker,
            "blocker_detail": self.blocker_detail,
            "complete": self.complete,
            "grain_data_root_set": self.grain_data_root_set,
            "capture_store_present": self.capture_store_present,
            "frozen_d5": {
                "candidate_count": self.identity.candidate_count,
                "s1_count": self.identity.s1_count,
                "s4_count": self.identity.s4_count,
                "hit_set_digest": self.identity.hit_set_digest,
                "candidates_digest": self.identity.candidates_digest,
                "candidate_universe_version": self.identity.candidate_universe_version,
                "required_sweep_families": list(self.identity.required_sweep_families),
                "first_candidate_id": self.identity.first_candidate_id,
                "last_candidate_id": self.identity.last_candidate_id,
                "cand_ids_unchanged": self.cand_ids_unchanged,
                "candidate_universe_version_unchanged": (
                    self.candidate_universe_version_unchanged
                ),
            },
            "pointers": {
                "expected": self.pointers_expected,
                "verified": self.pointers_verified,
                "missing": self.pointers_missing,
                "unknown": self.pointers_unknown,
                "mismatch": self.pointers_mismatch,
                "manifest_gap": self.pointers_manifest_gap,
                "by_family": by_family,
            },
            "hurdat2_archives": {
                "expected": self.hurdat2_expected,
                "capture_verified": self.hurdat2_capture_verified,
                "capture_missing": self.hurdat2_capture_missing,
                "capture_unknown": self.hurdat2_capture_unknown,
                "public_refetch_verified": self.hurdat2_public_verified,
                "records": [
                    {
                        "basin": h.basin,
                        "url": h.url,
                        "expected_sha256": h.expected_sha256,
                        "capture_id": h.capture_id,
                        "capture_object_status": h.capture_object_status,
                        "public_refetch_status": h.public_refetch_status,
                        "observed_sha256": h.observed_sha256,
                        "detail": h.detail,
                    }
                    for h in self.hurdat2_checks
                ],
            },
            "enrichment_appended": self.enrichment_appended,
            "notes": [
                "UNKNOWN is not zero; missing/unreadable objects are not verified.",
                "No candidate remint. No candidates.csv identity rewrite.",
                "No episode YAML. No market outcomes.",
                "HURDAT2 public re-fetch verifies digest only; it is not a new candidate.",
            ],
        }


def _sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def hurdat2_capture_candidate_id(url: str) -> str:
    """Capture-dir id used by the v2 executor for HURDAT2 archive bytes."""
    return "S4-hurdat-" + _sha256_hex(url.encode())[:12]


def hurdat2_archive_specs() -> tuple[Hurdat2ArchiveSpec, ...]:
    return (
        Hurdat2ArchiveSpec("atlantic", HURDAT2_ATLANTIC_URL, S4_ATLANTIC_SHA256),
        Hurdat2ArchiveSpec("pacific", HURDAT2_PACIFIC_URL, S4_PACIFIC_SHA256),
    )


def _yaml_scalar(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int) and not isinstance(value, bool):
        return str(value)
    return json.dumps(str(value))


def render_inventory_yaml(report: InventoryReport) -> bytes:
    """Deterministic UTF-8 YAML for the mechanical inventory record."""
    data = report.to_mapping()
    lines: list[str] = [
        f"schema_version: {_yaml_scalar(data['schema_version'])}",
        f"record_kind: {_yaml_scalar(data['record_kind'])}",
        f"outcome_blind: {_yaml_scalar(data['outcome_blind'])}",
        f"blocker: {_yaml_scalar(data['blocker'])}",
        f"blocker_detail: {_yaml_scalar(data['blocker_detail'])}",
        f"complete: {_yaml_scalar(data['complete'])}",
        f"grain_data_root_set: {_yaml_scalar(data['grain_data_root_set'])}",
        f"capture_store_present: {_yaml_scalar(data['capture_store_present'])}",
        "frozen_d5:",
    ]
    frozen = data["frozen_d5"]
    for key in (
        "candidate_count",
        "s1_count",
        "s4_count",
        "hit_set_digest",
        "candidates_digest",
        "candidate_universe_version",
    ):
        lines.append(f"  {key}: {_yaml_scalar(frozen[key])}")
    lines.append("  required_sweep_families:")
    for fam in frozen["required_sweep_families"]:
        lines.append(f"    - {_yaml_scalar(fam)}")
    for key in (
        "first_candidate_id",
        "last_candidate_id",
        "cand_ids_unchanged",
        "candidate_universe_version_unchanged",
    ):
        lines.append(f"  {key}: {_yaml_scalar(frozen[key])}")
    ptr = data["pointers"]
    lines.append("pointers:")
    for key in (
        "expected",
        "verified",
        "missing",
        "unknown",
        "mismatch",
        "manifest_gap",
    ):
        lines.append(f"  {key}: {_yaml_scalar(ptr[key])}")
    lines.append("  by_family:")
    for fam in sorted(ptr["by_family"]):
        lines.append(f"    {fam}:")
        for key, val in ptr["by_family"][fam].items():
            lines.append(f"      {key}: {_yaml_scalar(val)}")
    hur = data["hurdat2_archives"]
    lines.append("hurdat2_archives:")
    for key in (
        "expected",
        "capture_verified",
        "capture_missing",
        "capture_unknown",
        "public_refetch_verified",
    ):
        lines.append(f"  {key}: {_yaml_scalar(hur[key])}")
    lines.append("  records:")
    for rec in hur["records"]:
        first = True
        for key, val in rec.items():
            if first:
                lines.append(f"  - {key}: {_yaml_scalar(val)}")
                first = False
            else:
                lines.append(f"    {key}: {_yaml_scalar(val)}")
    lines.append(f"enrichment_appended: {_yaml_scalar(data['enrichment_appended'])}")
    lines.append("notes:")
    for note in data["notes"]:
        lines.append(f"- {_yaml_scalar(note)}")
    return ("\n".join(lines) + "\n").encode("utf-8")


def load_frozen_d5_identity(repo_root: Path | None = None) -> FrozenIdentity:
    """Read committed D5 artifacts; refuse identity drift. Does not remint."""
    root = Path(repo_root) if repo_root is not None else REPO_ROOT
    csv_path = root / CANONICAL_CANDIDATES_RELATIVE
    man_path = root / CANONICAL_CANDIDATE_UNIVERSE_MANIFEST_RELATIVE
    if not csv_path.is_file():
        raise EvidenceInventoryError(f"frozen candidates.csv missing: {csv_path}")
    if not man_path.is_file():
        raise EvidenceInventoryError(f"frozen candidate_universe.yaml missing: {man_path}")
    csv_bytes = csv_path.read_bytes()
    digest = _sha256_hex(csv_bytes)
    with man_path.open(encoding="utf-8") as fh:
        man = yaml.safe_load(fh)
    if not isinstance(man, dict):
        raise EvidenceInventoryError("candidate_universe.yaml is not a mapping")
    rows = list(csv.DictReader(csv_bytes.decode("utf-8").splitlines()))
    s1 = sum(1 for r in rows if r.get("sweep_id") == "S1")
    s4 = sum(1 for r in rows if r.get("sweep_id") == "S4")
    families = tuple(man.get("required_sweep_families") or ())
    version = str(man.get("candidate_universe_version") or "")
    hit = str(man.get("hit_set_digest") or "")
    cand_digest = str(man.get("candidates_digest") or "")
    count = man.get("candidate_count")
    first_id = rows[0]["candidate_id"] if rows else ""
    last_id = rows[-1]["candidate_id"] if rows else ""
    cand_ids_ok = (
        len(rows) == FROZEN_CANDIDATE_COUNT
        and first_id == "CAND-0001"
        and last_id == "CAND-4234"
        and all(r["candidate_id"] == f"CAND-{i:04d}" for i, r in enumerate(rows, start=1))
    )
    version_ok = version == FROZEN_CANDIDATE_UNIVERSE_VERSION
    identity_ok = (
        digest == FROZEN_CANDIDATES_DIGEST
        and cand_digest == FROZEN_CANDIDATES_DIGEST
        and hit == FROZEN_HIT_SET_DIGEST
        and version_ok
        and count == FROZEN_CANDIDATE_COUNT
        and s1 == FROZEN_S1_COUNT
        and s4 == FROZEN_S4_COUNT
        and families == FROZEN_REQUIRED_SWEEP_FAMILIES
        and cand_ids_ok
    )
    if not identity_ok:
        raise EvidenceInventoryError(
            f"{BLOCKER_IDENTITY_DRIFT}: refuse remint/rewrite; "
            f"count={count} digest={digest} version={version!r} "
            f"hit={hit} families={families!r} s1={s1} s4={s4} "
            f"first={first_id} last={last_id} cand_ids_ok={cand_ids_ok}"
        )
    return FrozenIdentity(
        candidate_count=int(count),
        s1_count=s1,
        s4_count=s4,
        hit_set_digest=hit,
        candidates_digest=digest,
        candidate_universe_version=version,
        required_sweep_families=families,
        first_candidate_id=first_id,
        last_candidate_id=last_id,
        cand_ids_unchanged=True,
        candidate_universe_version_unchanged=True,
        candidates_csv_bytes=csv_bytes,
    )


def load_frozen_pointers(identity: FrozenIdentity) -> tuple[FrozenPointer, ...]:
    rows = list(csv.DictReader(identity.candidates_csv_bytes.decode("utf-8").splitlines()))
    out: list[FrozenPointer] = []
    for row in rows:
        pointer = (row.get("raw_capture_pointer") or "").strip()
        if not pointer:
            raise EvidenceInventoryError(
                f"{row.get('candidate_id')}: empty raw_capture_pointer; UNKNOWN != zero"
            )
        parsed = _POINTER_RE.fullmatch(pointer)
        if parsed is None:
            raise EvidenceInventoryError(
                f"{row.get('candidate_id')}: unparseable raw_capture_pointer {pointer!r}"
            )
        if parsed.group("subdir") != SWEEPS_SUBDIR:
            raise EvidenceInventoryError(
                f"{row.get('candidate_id')}: pointer subdir "
                f"{parsed.group('subdir')!r} != {SWEEPS_SUBDIR!r}"
            )
        if parsed.group("sweep_id") != row.get("sweep_id"):
            raise EvidenceInventoryError(
                f"{row.get('candidate_id')}: pointer sweep "
                f"{parsed.group('sweep_id')!r} != row sweep {row.get('sweep_id')!r}"
            )
        out.append(
            FrozenPointer(
                candidate_id=row["candidate_id"],
                sweep_id=row["sweep_id"],
                source_reference=row["source_reference"],
                raw_capture_pointer=pointer,
                expected_sha256=parsed.group("sha256"),
                capture_id=parsed.group("capture_id"),
            )
        )
    if len(out) != FROZEN_CANDIDATE_COUNT:
        raise EvidenceInventoryError(
            f"pointer count {len(out)} != frozen {FROZEN_CANDIDATE_COUNT}"
        )
    return tuple(out)


def _contained(*, path: Path, root: Path, field: str) -> Path:
    try:
        root_r = root.resolve()
        path_r = path.resolve()
    except OSError as exc:
        raise EvidenceInventoryError(f"{field} could not be resolved: {exc}") from exc
    try:
        path_r.relative_to(root_r)
    except ValueError as exc:
        raise EvidenceInventoryError(
            f"{field} resolves outside data root ({path_r} not under {root_r})"
        ) from exc
    return path_r


def resolve_capture_store(
    data_root_path: Path | str | None = None,
) -> tuple[Path | None, str | None, str]:
    """Return (root, blocker, detail). Does not invent a data root."""
    try:
        root = data_root(data_root_path)
    except CapturePathError as exc:
        return None, BLOCKER_CAPTURE_STORE_MISSING, str(exc)
    if not root.exists():
        return (
            None,
            BLOCKER_CAPTURE_STORE_MISSING,
            f"data root does not exist: {root}",
        )
    sweeps = root / SWEEPS_SUBDIR
    if not sweeps.is_dir():
        return (
            None,
            BLOCKER_CAPTURE_STORE_MISSING,
            f"sweeps directory missing: {sweeps}",
        )
    return root, None, f"capture store present at {root}"


def _manifest_sha256_set(manifest_path: Path) -> set[str] | str:
    """Return sha256 set, or an error token starting with 'unknown:' / 'missing:'."""
    if not manifest_path.is_file():
        return "missing"
    try:
        with manifest_path.open(encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
    except OSError as exc:
        return f"unknown: cannot read manifest: {exc}"
    except yaml.YAMLError as exc:
        return f"unknown: unparseable manifest: {exc}"
    if not isinstance(data, dict):
        return "unknown: manifest is not a mapping"
    records = data.get("records")
    if not isinstance(records, list):
        return "unknown: records is not a list"
    out: set[str] = set()
    for rec in records:
        if not isinstance(rec, dict):
            return "unknown: record is not a mapping"
        sha = rec.get("sha256")
        if isinstance(sha, str) and _SHA256_RE.fullmatch(sha):
            out.add(sha)
    return out


def verify_pointer_object(
    pointer: FrozenPointer,
    *,
    store_root: Path | None,
    store_blocker: str | None,
) -> PointerCheck:
    if store_root is None:
        return PointerCheck(
            candidate_id=pointer.candidate_id,
            sweep_id=pointer.sweep_id,
            source_reference=pointer.source_reference,
            raw_capture_pointer=pointer.raw_capture_pointer,
            status=STATUS_UNKNOWN,
            detail=store_blocker or BLOCKER_CAPTURE_STORE_MISSING,
        )
    obj = store_root / pointer.raw_capture_pointer
    try:
        obj_r = _contained(path=obj, root=store_root, field="raw_capture_pointer")
    except EvidenceInventoryError as exc:
        return PointerCheck(
            candidate_id=pointer.candidate_id,
            sweep_id=pointer.sweep_id,
            source_reference=pointer.source_reference,
            raw_capture_pointer=pointer.raw_capture_pointer,
            status=STATUS_UNKNOWN,
            detail=str(exc),
        )
    cap_dir = obj_r.parent.parent
    if not obj_r.is_file():
        return PointerCheck(
            candidate_id=pointer.candidate_id,
            sweep_id=pointer.sweep_id,
            source_reference=pointer.source_reference,
            raw_capture_pointer=pointer.raw_capture_pointer,
            status=STATUS_MISSING,
            detail=f"object not found: {obj_r}",
        )
    try:
        raw = obj_r.read_bytes()
    except OSError as exc:
        return PointerCheck(
            candidate_id=pointer.candidate_id,
            sweep_id=pointer.sweep_id,
            source_reference=pointer.source_reference,
            raw_capture_pointer=pointer.raw_capture_pointer,
            status=STATUS_UNKNOWN,
            detail=f"unreadable object: {exc}",
        )
    got = _sha256_hex(raw)
    if got != pointer.expected_sha256 or got != obj_r.name:
        return PointerCheck(
            candidate_id=pointer.candidate_id,
            sweep_id=pointer.sweep_id,
            source_reference=pointer.source_reference,
            raw_capture_pointer=pointer.raw_capture_pointer,
            status=STATUS_MISMATCH,
            detail=f"sha256 {got} != expected {pointer.expected_sha256}",
        )
    man_path = cap_dir / MANIFEST_FILENAME
    man_shas = _manifest_sha256_set(man_path)
    if isinstance(man_shas, str):
        if man_shas == "missing":
            return PointerCheck(
                candidate_id=pointer.candidate_id,
                sweep_id=pointer.sweep_id,
                source_reference=pointer.source_reference,
                raw_capture_pointer=pointer.raw_capture_pointer,
                status=STATUS_MANIFEST_GAP,
                detail=f"object verified but manifest missing: {man_path}",
            )
        return PointerCheck(
            candidate_id=pointer.candidate_id,
            sweep_id=pointer.sweep_id,
            source_reference=pointer.source_reference,
            raw_capture_pointer=pointer.raw_capture_pointer,
            status=STATUS_UNKNOWN,
            detail=man_shas,
        )
    if pointer.expected_sha256 not in man_shas:
        return PointerCheck(
            candidate_id=pointer.candidate_id,
            sweep_id=pointer.sweep_id,
            source_reference=pointer.source_reference,
            raw_capture_pointer=pointer.raw_capture_pointer,
            status=STATUS_MANIFEST_GAP,
            detail="object verified but sha256 absent from manifest records",
        )
    return PointerCheck(
        candidate_id=pointer.candidate_id,
        sweep_id=pointer.sweep_id,
        source_reference=pointer.source_reference,
        raw_capture_pointer=pointer.raw_capture_pointer,
        status=STATUS_VERIFIED,
        detail="object sha256 and manifest record match",
    )


def _fetch_bytes(url: str, *, timeout: int = 120) -> tuple[bool, bytes | None, str | None]:
    try:
        req = urllib.request.Request(
            url, headers={"User-Agent": "grainsys-discovery/1.0 (research)"}
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return True, resp.read(), None
    except urllib.error.URLError as exc:
        return False, None, str(exc)
    except Exception as exc:
        return False, None, f"{type(exc).__name__}: {exc}"


def verify_hurdat2_archive(
    spec: Hurdat2ArchiveSpec,
    *,
    store_root: Path | None,
    store_blocker: str | None,
    refetch: bool,
    fetch_fn=_fetch_bytes,
) -> Hurdat2Check:
    capture_status = STATUS_UNKNOWN
    capture_detail = store_blocker or BLOCKER_CAPTURE_STORE_MISSING
    if store_root is not None:
        obj = (
            store_root
            / SWEEPS_SUBDIR
            / "S4"
            / spec.capture_id
            / OBJECTS_DIRNAME
            / spec.expected_sha256
        )
        try:
            obj_r = _contained(path=obj, root=store_root, field="hurdat2_object")
        except EvidenceInventoryError as exc:
            capture_status = STATUS_UNKNOWN
            capture_detail = str(exc)
        else:
            if not obj_r.is_file():
                capture_status = STATUS_MISSING
                capture_detail = f"HURDAT2 capture object not found: {obj_r}"
            else:
                try:
                    raw = obj_r.read_bytes()
                except OSError as exc:
                    capture_status = STATUS_UNKNOWN
                    capture_detail = f"unreadable HURDAT2 object: {exc}"
                else:
                    got = _sha256_hex(raw)
                    if got != spec.expected_sha256:
                        capture_status = STATUS_MISMATCH
                        capture_detail = f"local sha256 {got} != {spec.expected_sha256}"
                    else:
                        man = _manifest_sha256_set(obj_r.parent.parent / MANIFEST_FILENAME)
                        if isinstance(man, str) and man == "missing":
                            capture_status = STATUS_MANIFEST_GAP
                            capture_detail = "HURDAT2 object hash ok; manifest missing"
                        elif isinstance(man, str):
                            capture_status = STATUS_UNKNOWN
                            capture_detail = man
                        elif spec.expected_sha256 not in man:
                            capture_status = STATUS_MANIFEST_GAP
                            capture_detail = "HURDAT2 object hash ok; sha absent from manifest"
                        else:
                            capture_status = STATUS_VERIFIED
                            capture_detail = "HURDAT2 capture object and manifest match"

    public_status = STATUS_NOT_ATTEMPTED
    observed: str | None = None
    public_detail = "public re-fetch not attempted"
    if refetch:
        ok, raw, err = fetch_fn(spec.url)
        if not ok or raw is None:
            public_status = STATUS_FETCH_FAILED
            public_detail = f"public re-fetch failed: {err}"
        else:
            observed = _sha256_hex(raw)
            if observed != spec.expected_sha256:
                public_status = STATUS_MISMATCH
                public_detail = (
                    f"public sha256 {observed} != expected {spec.expected_sha256}"
                )
            else:
                public_status = STATUS_VERIFIED
                public_detail = "public archive digest matches expected SHA256"
    detail = f"capture={capture_detail}; public={public_detail}"
    return Hurdat2Check(
        basin=spec.basin,
        url=spec.url,
        expected_sha256=spec.expected_sha256,
        capture_id=spec.capture_id,
        capture_object_status=capture_status,
        public_refetch_status=public_status,
        observed_sha256=observed,
        detail=detail,
    )


def enrich_hurdat2_archive_if_present(
    spec: Hurdat2ArchiveSpec,
    *,
    store_root: Path,
    raw_bytes: bytes,
) -> bool:
    """Append-only provenance if the HURDAT2 capture directory already exists.

    Does not create a new candidate directory. Does not remint D5 IDs.
    """
    cap_dir = store_root / SWEEPS_SUBDIR / "S4" / spec.capture_id
    if not cap_dir.is_dir():
        return False
    digest = _sha256_hex(raw_bytes)
    if digest != spec.expected_sha256:
        raise EvidenceInventoryError(
            f"refuse to enrich {spec.capture_id}: digest {digest} != {spec.expected_sha256}"
        )
    capture_candidate_evidence(
        sweep_id="S4",
        candidate_id=spec.capture_id,
        raw_bytes=raw_bytes,
        source_reference=spec.url,
        sweeps_subdir=SWEEPS_SUBDIR,
        data_root_path=store_root,
        original_filename=spec.url.rsplit("/", 1)[-1],
        content_type="text/plain",
    )
    return True


def _count_status(checks: Sequence[PointerCheck], status: str) -> int:
    return sum(1 for c in checks if c.status == status)


def run_d6_evidence_inventory(
    *,
    repo_root: Path | None = None,
    data_root_path: Path | str | None = None,
    refetch_hurdat2: bool = False,
    enrich_hurdat2: bool = False,
    persist: bool = False,
    fetch_fn=_fetch_bytes,
) -> InventoryReport:
    """Inventory frozen D5 pointers + HURDAT2 archive captures. Never remints."""
    root = Path(repo_root) if repo_root is not None else REPO_ROOT
    identity = load_frozen_d5_identity(root)
    csv_before = identity.candidates_csv_bytes
    man_before = (root / CANONICAL_CANDIDATE_UNIVERSE_MANIFEST_RELATIVE).read_bytes()
    pointers = load_frozen_pointers(identity)
    grain_set = bool(os.environ.get("GRAIN_DATA_ROOT")) or data_root_path is not None
    store_root, store_blocker, store_detail = resolve_capture_store(data_root_path)
    pointer_checks = tuple(
        verify_pointer_object(p, store_root=store_root, store_blocker=store_blocker)
        for p in pointers
    )
    fetch_cache: dict[str, tuple[bool, bytes | None, str | None]] = {}

    def fetch_cached(url: str, *, timeout: int = 120) -> tuple[bool, bytes | None, str | None]:
        if url not in fetch_cache:
            fetch_cache[url] = fetch_fn(url, timeout=timeout)
        return fetch_cache[url]

    hurdat_checks: list[Hurdat2Check] = []
    enrichment_appended = 0
    for spec in hurdat2_archive_specs():
        chk = verify_hurdat2_archive(
            spec,
            store_root=store_root,
            store_blocker=store_blocker,
            refetch=refetch_hurdat2,
            fetch_fn=fetch_cached,
        )
        hurdat_checks.append(chk)
        cached = fetch_cache.get(spec.url)
        if (
            enrich_hurdat2
            and store_root is not None
            and cached is not None
            and cached[0]
            and cached[1] is not None
        ):
            if enrich_hurdat2_archive_if_present(
                spec, store_root=store_root, raw_bytes=cached[1]
            ):
                enrichment_appended += 1

    verified = _count_status(pointer_checks, STATUS_VERIFIED)
    missing = _count_status(pointer_checks, STATUS_MISSING)
    unknown = _count_status(pointer_checks, STATUS_UNKNOWN)
    mismatch = _count_status(pointer_checks, STATUS_MISMATCH)
    gap = _count_status(pointer_checks, STATUS_MANIFEST_GAP)
    h_verified = sum(
        1 for h in hurdat_checks if h.capture_object_status == STATUS_VERIFIED
    )
    h_missing = sum(
        1 for h in hurdat_checks if h.capture_object_status == STATUS_MISSING
    )
    h_unknown = sum(
        1
        for h in hurdat_checks
        if h.capture_object_status
        in {STATUS_UNKNOWN, STATUS_MISMATCH, STATUS_MANIFEST_GAP}
    )
    h_public = sum(
        1 for h in hurdat_checks if h.public_refetch_status == STATUS_VERIFIED
    )

    blocker = store_blocker
    detail = store_detail
    public_fetch_failed = any(
        h.public_refetch_status == STATUS_FETCH_FAILED for h in hurdat_checks
    )
    if blocker is None and (missing or unknown or mismatch or gap or h_missing or h_unknown):
        blocker = BLOCKER_CAPTURE_STORE_MISSING
        detail = (
            f"unverified pointers verified={verified} missing={missing} "
            f"unknown={unknown} mismatch={mismatch} manifest_gap={gap}; "
            f"hurdat2 capture verified={h_verified} missing={h_missing} "
            f"unknown={h_unknown}"
        )
    if blocker is None and refetch_hurdat2 and public_fetch_failed and h_verified < 2:
        blocker = BLOCKER_EXTERNAL_ACCESS_BLOCKED
        detail = "HURDAT2 public re-fetch failed and capture objects not fully verified"
    if (
        blocker == BLOCKER_CAPTURE_STORE_MISSING
        and refetch_hurdat2
        and public_fetch_failed
        and store_root is None
    ):
        # Store missing remains the primary blocker; note access separately in detail.
        detail = f"{detail}; HURDAT2 public re-fetch also failed"

    complete = (
        blocker is None
        and verified == FROZEN_CANDIDATE_COUNT
        and missing == 0
        and unknown == 0
        and mismatch == 0
        and gap == 0
        and h_verified == 2
        and identity.cand_ids_unchanged
        and identity.candidate_universe_version_unchanged
    )
    if not complete and blocker is None:
        blocker = BLOCKER_CAPTURE_STORE_MISSING
        detail = "inventory incomplete; fail closed"

    report = InventoryReport(
        blocker=blocker,
        blocker_detail=detail,
        complete=complete,
        grain_data_root_set=grain_set,
        capture_store_present=store_root is not None,
        pointers_expected=FROZEN_CANDIDATE_COUNT,
        pointers_verified=verified,
        pointers_missing=missing,
        pointers_unknown=unknown,
        pointers_mismatch=mismatch,
        pointers_manifest_gap=gap,
        hurdat2_expected=2,
        hurdat2_capture_verified=h_verified,
        hurdat2_capture_missing=h_missing,
        hurdat2_capture_unknown=h_unknown,
        hurdat2_public_verified=h_public,
        cand_ids_unchanged=identity.cand_ids_unchanged,
        candidate_universe_version_unchanged=identity.candidate_universe_version_unchanged,
        enrichment_appended=enrichment_appended,
        identity=identity,
        pointer_checks=pointer_checks,
        hurdat2_checks=tuple(hurdat_checks),
    )

    csv_after = (root / CANONICAL_CANDIDATES_RELATIVE).read_bytes()
    man_after = (root / CANONICAL_CANDIDATE_UNIVERSE_MANIFEST_RELATIVE).read_bytes()
    if csv_after != csv_before or man_after != man_before:
        raise EvidenceInventoryError(
            "inventory mutated frozen D5 identity artifacts; refuse"
        )

    if persist:
        out = root / INVENTORY_RELATIVE
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(render_inventory_yaml(report))
        csv_post = (root / CANONICAL_CANDIDATES_RELATIVE).read_bytes()
        man_post = (root / CANONICAL_CANDIDATE_UNIVERSE_MANIFEST_RELATIVE).read_bytes()
        if csv_post != csv_before or man_post != man_before:
            raise EvidenceInventoryError(
                "persist mutated frozen D5 identity artifacts; refuse"
            )
    return report


def main(argv: Sequence[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="D6 evidence-pack inventory (outcome-blind; no remint)"
    )
    parser.add_argument("--repo-root", type=Path, default=None)
    parser.add_argument("--data-root", type=Path, default=None, help="Override GRAIN_DATA_ROOT")
    parser.add_argument(
        "--refetch-hurdat2",
        action="store_true",
        help="Re-fetch public HURDAT2 archives to verify digest only",
    )
    parser.add_argument(
        "--enrich-hurdat2",
        action="store_true",
        help="Append-only enrich existing HURDAT2 capture dirs (never create new)",
    )
    parser.add_argument(
        "--persist",
        action="store_true",
        help="Write d6_evidence_pack_inventory.yaml (does not rewrite candidates.csv)",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)
    report = run_d6_evidence_inventory(
        repo_root=args.repo_root,
        data_root_path=args.data_root,
        refetch_hurdat2=args.refetch_hurdat2,
        enrich_hurdat2=args.enrich_hurdat2,
        persist=args.persist,
    )
    print(f"complete={report.complete}")
    print(f"blocker={report.blocker}")
    print(f"blocker_detail={report.blocker_detail}")
    print(
        f"pointers expected={report.pointers_expected} verified={report.pointers_verified} "
        f"missing={report.pointers_missing} unknown={report.pointers_unknown} "
        f"mismatch={report.pointers_mismatch} manifest_gap={report.pointers_manifest_gap}"
    )
    print(
        f"hurdat2 capture verified={report.hurdat2_capture_verified} "
        f"missing={report.hurdat2_capture_missing} unknown={report.hurdat2_capture_unknown} "
        f"public_verified={report.hurdat2_public_verified}"
    )
    print(
        f"cand_ids_unchanged={report.cand_ids_unchanged} "
        f"universe_version_unchanged={report.candidate_universe_version_unchanged}"
    )
    return 0 if report.complete else 2


if __name__ == "__main__":
    raise SystemExit(main())
