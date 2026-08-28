"""D6 fail-closed evidence inventory (ADR-0010 / ADR-0013).

Candidate-keyed pointer verification and field-sufficiency recording only.
Does not mint D5 IDs, author episodes, collapse S4 hits, or invent capture bytes.
"""

from __future__ import annotations

import csv
import hashlib
import os
import re
import urllib.error
import urllib.request
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

import yaml

from grainsys.discovery.candidate_universe import (
    CANDIDATES_CSV_FIELDNAMES,
    CANONICAL_CANDIDATE_UNIVERSE_MANIFEST_RELATIVE,
    CANONICAL_CANDIDATES_RELATIVE,
)
from grainsys.discovery.capture import (
    MANIFEST_FILENAME,
    CaptureRecord,
    capture_candidate_evidence,
)
from grainsys.discovery.config import REPO_ROOT

INVENTORY_SCHEMA_VERSION = "1.0"
INVENTORY_RECORD_KIND = "d6_evidence_inventory"
INVENTORY_CSV_RELATIVE = Path("research/episodes/discovery/d6_evidence_inventory.csv")
INVENTORY_SUMMARY_RELATIVE = Path("research/episodes/discovery/d6_evidence_inventory.yaml")
INVENTORY_SCHEMA_RELATIVE = Path(
    "research/episodes/discovery/d6_evidence_inventory.schema.yaml"
)

FROZEN_CANDIDATE_COUNT = 4234
FROZEN_S1_COUNT = 37
FROZEN_S4_COUNT = 4197
FROZEN_CANDIDATE_UNIVERSE_VERSION = (
    "d5cu-1cb416ee3b6e9103b4edd60748865d7dd147c80611adfb6c6b5b37eba5258d97"
)
FROZEN_HIT_SET_DIGEST = (
    "1cb416ee3b6e9103b4edd60748865d7dd147c80611adfb6c6b5b37eba5258d97"
)
FROZEN_CANDIDATES_DIGEST = (
    "df7f7ffb41f339d75d6a8a2ef68ab113c70490822e03ad21c9ebd8e26dae2c66"
)

S4_CENSUS_NODES = 677
S4_TRACK_GEOMETRY = "POINT_ONLY"
S4_PROXIMITY_RADIUS_NM = 100

BLOCKER_CAPTURE_STORE_MISSING = "CAPTURE_STORE_MISSING"
BLOCKER_EXTERNAL_ACCESS_BLOCKED = "EXTERNAL_ACCESS_BLOCKED"

POINTER_STATUSES = frozenset({"verified", "missing", "corrupt", "unknown"})
MANIFEST_STATUSES = frozenset(
    {"verified", "missing", "mismatch", "unknown", "invalid_pointer"}
)

I2_NEEDS_PRIMARY = "needs_additional_primary_operational"
I2_UNKNOWN = "unknown"
I2_BODY_NOT_ADJUDICATED = "body_present_not_adjudicated"
DRIVER_HURDAT2_REGISTRY = "sufficient_from_hurdat2_registry"
DRIVER_S1_NOTICE = "sufficient_from_captured_notice_identity"
DRIVER_UNKNOWN = "unknown"

INVENTORY_CSV_FIELDNAMES: tuple[str, ...] = (
    "candidate_id",
    "sweep_id",
    "raw_capture_pointer",
    "capture_dir",
    "expected_sha256",
    "pointer_status",
    "observed_sha256",
    "manifest_status",
    "i2_field_sufficiency",
    "driver_identity_sufficiency",
    "public_anchor_sufficiency",
    "event_mechanism_sufficiency",
    "enrichment_records_appended",
)

FORBIDDEN_INVENTORY_FIELDS = frozenset(
    {
        "episode_id",
        "event_name",
        "severity",
        "severity_class",
        "market_outcome",
        "market_outcomes_reviewed",
        "price",
        "futures",
        "basis",
        "decision",
        "accept",
        "reject",
        "reason_code",
        "h7",
        "cluster_id",
        "public_anchor",
    }
)

_POINTER_RE = re.compile(
    r"^(?P<subdir>[^/]+)/(?P<sweep>S[0-9]+)/(?P<capdir>[^/]+)/objects/"
    r"(?P<sha>[0-9a-f]{64})$"
)
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")

HURDAT2_ARCHIVES: tuple[dict[str, str], ...] = (
    {
        "basin": "atlantic",
        "dir_prefix": "S4-hurdat-acff99953be3",
        "expected_sha256": (
            "1b9b0c7beed5b4505838658b1d30e159fc84330c60891a58cfcf43ae55c37202"
        ),
        "source_reference": (
            "https://www.nhc.noaa.gov/data/hurdat/hurdat2-1851-2025-02272026.txt"
        ),
    },
    {
        "basin": "pacific",
        "dir_prefix": "S4-hurdat-11be4a281f9a",
        "expected_sha256": (
            "db65f8bc538d5c05e15f738c96111861d6ce3572c007879de58e44d4d05a9cd6"
        ),
        "source_reference": (
            "https://www.nhc.noaa.gov/data/hurdat/hurdat2-nepac-1949-2025-02272026.txt"
        ),
    },
)


class EvidenceInventoryError(ValueError):
    """Fail-closed D6 inventory error."""


@dataclass(frozen=True)
class PointerRow:
    candidate_id: str
    sweep_id: str
    raw_capture_pointer: str
    capture_dir: str
    expected_sha256: str
    pointer_status: str
    observed_sha256: str
    manifest_status: str
    i2_field_sufficiency: str
    driver_identity_sufficiency: str
    public_anchor_sufficiency: str
    event_mechanism_sufficiency: str
    enrichment_records_appended: int

    def to_mapping(self) -> dict[str, str]:
        out = {k: getattr(self, k) for k in INVENTORY_CSV_FIELDNAMES}
        out["enrichment_records_appended"] = str(self.enrichment_records_appended)
        return out


@dataclass(frozen=True)
class Hurdat2ArchiveCheck:
    basin: str
    dir_prefix: str
    expected_sha256: str
    pointer_status: str
    observed_sha256: str
    manifest_status: str
    capture_dir: str
    public_refetch_status: str = "not_attempted"
    public_observed_sha256: str = ""


@dataclass(frozen=True)
class InventoryResult:
    candidate_universe_version: str
    hit_set_digest: str
    candidates_digest: str
    candidate_count: int
    data_root_status: str
    data_root: str
    searched_paths: tuple[str, ...]
    access_gate: str
    rows: tuple[PointerRow, ...]
    hurdat2: tuple[Hurdat2ArchiveCheck, ...]
    counts: dict[str, dict[str, int]]
    hurdat2_counts: dict[str, int]
    hurdat2_public_verified: int
    enrichment_count: int
    inventory_csv_digest: str | None
    notes: tuple[str, ...]


def _sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def default_search_hints() -> tuple[Path, ...]:
    home = Path.home()
    return (
        Path("/data"),
        Path("/data/grain"),
        Path("/data/grainsys"),
        Path("/data/grain_data"),
        Path("/workspace/data"),
        Path("/workspace/data/raw"),
        Path("/tmp/grain_data"),
        Path("/tmp/grainsys"),
        Path("/opt/grain_data"),
        Path("/opt/grainsys"),
        Path("/var/lib/grain"),
        Path("/var/lib/grainsys"),
        home / "grain_data",
        home / "grainsys-data",
        Path("/mnt/grain_data"),
        Path("/mnt/data"),
    )


def _looks_like_capture_root(path: Path) -> bool:
    sweeps = path / "sweeps"
    if (sweeps / "S1").is_dir() or (sweeps / "S4").is_dir():
        return True
    if path.name == "sweeps" and ((path / "S1").is_dir() or (path / "S4").is_dir()):
        return True
    return False


def find_capture_data_root(
    *,
    explicit: Path | str | None = None,
    search_hints: Sequence[Path] | None = None,
) -> tuple[Path | None, str, tuple[str, ...]]:
    """Resolve an existing capture root. Never creates directories or bytes."""
    searched: list[str] = []
    if explicit is not None:
        root = Path(explicit)
        searched.append(str(root))
        return root, "explicit", tuple(searched)

    env = os.environ.get("GRAIN_DATA_ROOT")
    if env:
        root = Path(env)
        searched.append(f"GRAIN_DATA_ROOT={root}")
        return root, "environment", tuple(searched)

    hints = tuple(search_hints) if search_hints is not None else default_search_hints()
    found: list[Path] = []
    for hint in hints:
        searched.append(str(hint))
        if not hint.exists():
            continue
        if _looks_like_capture_root(hint):
            found.append(hint if hint.name != "sweeps" else hint.parent)
            continue
        sweeps = hint / "sweeps"
        if _looks_like_capture_root(hint) or _looks_like_capture_root(sweeps.parent):
            found.append(hint)
    unique: list[Path] = []
    seen: set[str] = set()
    for path in found:
        key = str(path.resolve()) if path.exists() else str(path)
        if key not in seen:
            seen.add(key)
            unique.append(path)
    if len(unique) == 1:
        return unique[0], "discovered", tuple(searched)
    if len(unique) > 1:
        raise EvidenceInventoryError(
            "multiple capture trees found without GRAIN_DATA_ROOT; refuse to pick: "
            + ", ".join(str(p) for p in unique)
        )
    return None, "unavailable", tuple(searched)


def _require_frozen_d5(repo_root: Path) -> dict[str, object]:
    csv_path = repo_root / CANONICAL_CANDIDATES_RELATIVE
    man_path = repo_root / CANONICAL_CANDIDATE_UNIVERSE_MANIFEST_RELATIVE
    if not csv_path.is_file() or not man_path.is_file():
        raise EvidenceInventoryError("frozen D5 artifacts missing; refuse")
    csv_bytes = csv_path.read_bytes()
    digest = _sha256_hex(csv_bytes)
    if digest != FROZEN_CANDIDATES_DIGEST:
        raise EvidenceInventoryError(
            f"candidates.csv digest {digest} != frozen {FROZEN_CANDIDATES_DIGEST}; refuse"
        )
    man = yaml.safe_load(man_path.read_text(encoding="utf-8"))
    if not isinstance(man, dict):
        raise EvidenceInventoryError("candidate_universe.yaml is not a mapping; refuse")
    version = man.get("candidate_universe_version")
    hit = man.get("hit_set_digest")
    cand = man.get("candidates_digest")
    count = man.get("candidate_count")
    if version != FROZEN_CANDIDATE_UNIVERSE_VERSION:
        raise EvidenceInventoryError(
            f"candidate_universe_version {version!r} != frozen; refuse"
        )
    if hit != FROZEN_HIT_SET_DIGEST or cand != FROZEN_CANDIDATES_DIGEST:
        raise EvidenceInventoryError("frozen D5 digest drift; refuse")
    if count != FROZEN_CANDIDATE_COUNT:
        raise EvidenceInventoryError(
            f"candidate_count {count!r} != frozen {FROZEN_CANDIDATE_COUNT}; refuse"
        )
    return man


def _load_frozen_candidates(repo_root: Path) -> list[dict[str, str]]:
    path = repo_root / CANONICAL_CANDIDATES_RELATIVE
    with path.open(encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        if reader.fieldnames != list(CANDIDATES_CSV_FIELDNAMES):
            raise EvidenceInventoryError(
                f"candidates.csv fieldnames {reader.fieldnames!r} != frozen; refuse"
            )
        rows = list(reader)
    if len(rows) != FROZEN_CANDIDATE_COUNT:
        raise EvidenceInventoryError(
            f"candidates.csv rows {len(rows)} != frozen {FROZEN_CANDIDATE_COUNT}; refuse"
        )
    s1 = sum(1 for r in rows if r["sweep_id"] == "S1")
    s4 = sum(1 for r in rows if r["sweep_id"] == "S4")
    if s1 != FROZEN_S1_COUNT or s4 != FROZEN_S4_COUNT:
        raise EvidenceInventoryError(
            f"family counts S1={s1} S4={s4} != frozen "
            f"{FROZEN_S1_COUNT}/{FROZEN_S4_COUNT}; refuse"
        )
    return rows


def _parse_pointer(pointer: str) -> dict[str, str] | None:
    if not isinstance(pointer, str) or not pointer:
        return None
    match = _POINTER_RE.fullmatch(pointer)
    if match is None:
        return None
    return match.groupdict()


def _manifest_sha_set(manifest_path: Path) -> tuple[str, set[str]]:
    try:
        data = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError):
        return "mismatch", set()
    if not isinstance(data, dict):
        return "mismatch", set()
    records = data.get("records")
    if not isinstance(records, list):
        return "mismatch", set()
    shas: set[str] = set()
    for item in records:
        if not isinstance(item, dict):
            return "mismatch", set()
        sha = item.get("sha256")
        if not isinstance(sha, str) or not _SHA256_RE.fullmatch(sha):
            return "mismatch", set()
        shas.add(sha)
    return "ok", shas


def _check_object_and_manifest(
    *,
    data_root: Path | None,
    pointer: str,
) -> tuple[str, str, str]:
    """Return (pointer_status, observed_sha256, manifest_status)."""
    parsed = _parse_pointer(pointer)
    if parsed is None:
        return "corrupt", "", "invalid_pointer"
    if data_root is None:
        return "unknown", "", "unknown"

    obj_path = data_root.joinpath(*pointer.split("/"))
    cap_dir = data_root / parsed["subdir"] / parsed["sweep"] / parsed["capdir"]
    manifest_path = cap_dir / MANIFEST_FILENAME
    expected = parsed["sha"]

    if not obj_path.is_file():
        if not manifest_path.is_file():
            return "missing", "", "missing"
        return "missing", "", "mismatch"

    try:
        raw = obj_path.read_bytes()
    except OSError:
        return "corrupt", "", "unknown"
    observed = _sha256_hex(raw)
    if observed != expected or observed != obj_path.name:
        if not manifest_path.is_file():
            return "corrupt", observed, "missing"
        return "corrupt", observed, "mismatch"

    if not manifest_path.is_file():
        return "corrupt", observed, "missing"
    status, shas = _manifest_sha_set(manifest_path)
    if status != "ok" or expected not in shas:
        return "corrupt", observed, "mismatch"
    return "verified", observed, "verified"


def s4_field_sufficiency(*, pointer_status: str) -> dict[str, str]:
    """Closed protocol mapping. Storm track is a driver, not an episode."""
    driver = DRIVER_HURDAT2_REGISTRY if pointer_status == "verified" else DRIVER_UNKNOWN
    return {
        "i2_field_sufficiency": I2_NEEDS_PRIMARY,
        "driver_identity_sufficiency": driver,
        "public_anchor_sufficiency": I2_NEEDS_PRIMARY,
        "event_mechanism_sufficiency": I2_NEEDS_PRIMARY,
    }


def s1_field_sufficiency(*, pointer_status: str) -> dict[str, str]:
    if pointer_status == "verified":
        return {
            "i2_field_sufficiency": I2_BODY_NOT_ADJUDICATED,
            "driver_identity_sufficiency": DRIVER_S1_NOTICE,
            "public_anchor_sufficiency": I2_BODY_NOT_ADJUDICATED,
            "event_mechanism_sufficiency": I2_BODY_NOT_ADJUDICATED,
        }
    return {
        "i2_field_sufficiency": I2_UNKNOWN,
        "driver_identity_sufficiency": DRIVER_UNKNOWN,
        "public_anchor_sufficiency": I2_UNKNOWN,
        "event_mechanism_sufficiency": I2_UNKNOWN,
    }


def _empty_counts() -> dict[str, dict[str, int]]:
    zero = {status: 0 for status in ("verified", "missing", "corrupt", "unknown")}
    return {"S1": dict(zero), "S4": dict(zero)}


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


def _check_hurdat2_archive(
    *,
    data_root: Path | None,
    archive: Mapping[str, str],
    refetch: bool,
    fetch_fn=_fetch_bytes,
) -> Hurdat2ArchiveCheck:
    pointer = (
        f"sweeps/S4/{archive['dir_prefix']}/objects/{archive['expected_sha256']}"
    )
    status, observed, man = _check_object_and_manifest(
        data_root=data_root, pointer=pointer
    )
    public_status = "not_attempted"
    public_observed = ""
    if refetch:
        ok, raw, _err = fetch_fn(archive["source_reference"])
        if not ok or raw is None:
            public_status = "fetch_failed"
            public_observed = ""
        else:
            public_observed = _sha256_hex(raw)
            if public_observed == archive["expected_sha256"]:
                public_status = "verified"
            else:
                public_status = "mismatch"
    return Hurdat2ArchiveCheck(
        basin=archive["basin"],
        dir_prefix=archive["dir_prefix"],
        expected_sha256=archive["expected_sha256"],
        pointer_status=status,
        observed_sha256=observed,
        manifest_status=man,
        capture_dir=archive["dir_prefix"],
        public_refetch_status=public_status,
        public_observed_sha256=public_observed,
    )


def build_evidence_inventory(
    *,
    repo_root: Path | None = None,
    data_root_path: Path | str | None = None,
    search_hints: Sequence[Path] | None = None,
    persist: bool = False,
    refetch_hurdat2: bool = False,
    fetch_fn=_fetch_bytes,
) -> InventoryResult:
    """Verify frozen D5 pointers and record field-sufficiency. Read-only on D5."""
    root = repo_root if repo_root is not None else REPO_ROOT
    _require_frozen_d5(root)
    candidates = _load_frozen_candidates(root)
    csv_before = (root / CANONICAL_CANDIDATES_RELATIVE).read_bytes()
    man_before = (root / CANONICAL_CANDIDATE_UNIVERSE_MANIFEST_RELATIVE).read_bytes()

    data_root, origin, searched = find_capture_data_root(
        explicit=data_root_path, search_hints=search_hints
    )
    if data_root is None:
        data_root_status = "unavailable"
        access_gate = BLOCKER_CAPTURE_STORE_MISSING
        usable_root: Path | None = None
    else:
        usable_root = data_root
        if not data_root.exists():
            data_root_status = f"{origin}_missing_path"
            access_gate = BLOCKER_CAPTURE_STORE_MISSING
        elif not _looks_like_capture_root(data_root):
            data_root_status = f"{origin}_no_sweeps_tree"
            access_gate = BLOCKER_CAPTURE_STORE_MISSING
        else:
            data_root_status = origin
            access_gate = "ok"

    counts = _empty_counts()
    rows: list[PointerRow] = []
    for rec in candidates:
        sweep_id = rec["sweep_id"]
        pointer = rec["raw_capture_pointer"]
        parsed = _parse_pointer(pointer)
        capture_dir = parsed["capdir"] if parsed else ""
        expected = parsed["sha"] if parsed else ""
        pointer_status, observed, man_status = _check_object_and_manifest(
            data_root=usable_root, pointer=pointer
        )
        if sweep_id == "S4":
            fields = s4_field_sufficiency(pointer_status=pointer_status)
        elif sweep_id == "S1":
            fields = s1_field_sufficiency(pointer_status=pointer_status)
        else:
            raise EvidenceInventoryError(
                f"unexpected sweep_id {sweep_id!r} in frozen D5; refuse"
            )
        if pointer_status not in POINTER_STATUSES:
            raise EvidenceInventoryError(f"invalid pointer_status {pointer_status!r}")
        counts[sweep_id][pointer_status] += 1
        rows.append(
            PointerRow(
                candidate_id=rec["candidate_id"],
                sweep_id=sweep_id,
                raw_capture_pointer=pointer,
                capture_dir=capture_dir,
                expected_sha256=expected,
                pointer_status=pointer_status,
                observed_sha256=observed,
                manifest_status=man_status,
                enrichment_records_appended=0,
                **fields,
            )
        )

    hurdat2 = tuple(
        _check_hurdat2_archive(
            data_root=usable_root,
            archive=arch,
            refetch=refetch_hurdat2,
            fetch_fn=fetch_fn,
        )
        for arch in HURDAT2_ARCHIVES
    )
    hurdat2_counts = {status: 0 for status in ("verified", "missing", "corrupt", "unknown")}
    for item in hurdat2:
        hurdat2_counts[item.pointer_status] += 1
    hurdat2_public_verified = sum(
        1 for item in hurdat2 if item.public_refetch_status == "verified"
    )
    public_fetch_failed = any(
        item.public_refetch_status == "fetch_failed" for item in hurdat2
    )
    if public_fetch_failed and hurdat2_counts["verified"] < 2:
        if access_gate == "ok":
            access_gate = BLOCKER_EXTERNAL_ACCESS_BLOCKED
        elif access_gate == BLOCKER_CAPTURE_STORE_MISSING:
            # Store remains the primary blocker; public fetch failure is recorded
            # on each HURDAT2 row rather than replacing CAPTURE_STORE_MISSING.
            pass

    if access_gate != "ok":
        notes = (
            "GRAIN_DATA_ROOT capture tree is not available on this host.",
            "Inaccessible bodies are UNKNOWN (not zero, not coverage-absent).",
            "No capture bytes were invented. HURDAT2 storm-node objects were not rebuilt.",
            "HURDAT2 public re-fetch verifies digest only and is not a new candidate.",
            "S4 I2/public_anchor/event-mechanism remain needs_additional_primary_operational.",
            "H1/H2/H4 grouping and episode admission are deferred to Phase 2.",
        )
    else:
        notes = (
            "Pointer verification used live candidate-keyed capture dirs from GRAIN_DATA_ROOT.",
            "HURDAT2 public re-fetch verifies digest only and is not a new candidate.",
            "S4 I2/public_anchor/event-mechanism remain needs_additional_primary_operational.",
            "H1/H2/H4 grouping and episode admission are deferred to Phase 2.",
        )

    csv_digest: str | None = None
    if persist:
        csv_digest = _persist_inventory(
            repo_root=root,
            rows=rows,
            data_root_status=data_root_status,
            data_root=str(usable_root) if usable_root is not None else "",
            searched=searched,
            access_gate=access_gate,
            counts=counts,
            hurdat2=hurdat2,
            hurdat2_counts=hurdat2_counts,
            hurdat2_public_verified=hurdat2_public_verified,
            notes=notes,
        )

    if (root / CANONICAL_CANDIDATES_RELATIVE).read_bytes() != csv_before:
        raise EvidenceInventoryError("inventory mutated candidates.csv; refuse")
    if (root / CANONICAL_CANDIDATE_UNIVERSE_MANIFEST_RELATIVE).read_bytes() != man_before:
        raise EvidenceInventoryError("inventory mutated candidate_universe.yaml; refuse")

    return InventoryResult(
        candidate_universe_version=FROZEN_CANDIDATE_UNIVERSE_VERSION,
        hit_set_digest=FROZEN_HIT_SET_DIGEST,
        candidates_digest=FROZEN_CANDIDATES_DIGEST,
        candidate_count=FROZEN_CANDIDATE_COUNT,
        data_root_status=data_root_status,
        data_root=str(usable_root) if usable_root is not None else "",
        searched_paths=searched,
        access_gate=access_gate,
        rows=tuple(rows),
        hurdat2=hurdat2,
        counts=counts,
        hurdat2_counts=hurdat2_counts,
        hurdat2_public_verified=hurdat2_public_verified,
        enrichment_count=0,
        inventory_csv_digest=csv_digest,
        notes=notes,
    )


def _persist_inventory(
    *,
    repo_root: Path,
    rows: Sequence[PointerRow],
    data_root_status: str,
    data_root: str,
    searched: Sequence[str],
    access_gate: str,
    counts: Mapping[str, Mapping[str, int]],
    hurdat2: Sequence[Hurdat2ArchiveCheck],
    hurdat2_counts: Mapping[str, int],
    hurdat2_public_verified: int,
    notes: Sequence[str],
) -> str:
    csv_path = repo_root / INVENTORY_CSV_RELATIVE
    summary_path = repo_root / INVENTORY_SUMMARY_RELATIVE
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(
            fh, fieldnames=list(INVENTORY_CSV_FIELDNAMES), lineterminator="\n"
        )
        writer.writeheader()
        for row in rows:
            mapping = row.to_mapping()
            overlap = FORBIDDEN_INVENTORY_FIELDS.intersection(mapping)
            if overlap:
                raise EvidenceInventoryError(
                    f"forbidden inventory fields {sorted(overlap)}; refuse"
                )
            writer.writerow(mapping)
    csv_digest = _sha256_hex(csv_path.read_bytes())
    summary = {
        "schema_version": INVENTORY_SCHEMA_VERSION,
        "record_kind": INVENTORY_RECORD_KIND,
        "candidate_universe_version": FROZEN_CANDIDATE_UNIVERSE_VERSION,
        "hit_set_digest": FROZEN_HIT_SET_DIGEST,
        "candidates_digest": FROZEN_CANDIDATES_DIGEST,
        "candidate_count": FROZEN_CANDIDATE_COUNT,
        "inventory_csv_relative": INVENTORY_CSV_RELATIVE.as_posix(),
        "inventory_csv_digest": csv_digest,
        "access_gate": access_gate,
        "data_root_status": data_root_status,
        "data_root": data_root or None,
        "searched_paths": list(searched),
        "pointer_counts": {
            "S1": dict(counts["S1"]),
            "S4": dict(counts["S4"]),
        },
        "hurdat2_archives": [
            {
                "basin": item.basin,
                "dir_prefix": item.dir_prefix,
                "expected_sha256": item.expected_sha256,
                "pointer_status": item.pointer_status,
                "observed_sha256": item.observed_sha256 or None,
                "manifest_status": item.manifest_status,
                "capture_dir": item.capture_dir,
                "public_refetch_status": item.public_refetch_status,
                "public_observed_sha256": item.public_observed_sha256 or None,
            }
            for item in hurdat2
        ],
        "hurdat2_counts": dict(hurdat2_counts),
        "hurdat2_public_verified": hurdat2_public_verified,
        "enrichment_count": 0,
        "s4_field_sufficiency": {
            "census_variant": "S4_CENSUS_A_WCSC_D2GRAIN_DOCK_COMMPURP",
            "census_nodes": S4_CENSUS_NODES,
            "track_geometry": S4_TRACK_GEOMETRY,
            "proximity_radius_nm": S4_PROXIMITY_RADIUS_NM,
            "boundary_inequality": "inclusive_<=",
            "already_sufficient_from_hurdat2_and_registry_when_object_verified": [
                "storm_id",
                "node_id",
                "node_coordinates",
                "point_only_100nm_proximity_fact",
                "first_matching_position_timestamp",
                "driver_identity",
            ],
            "needs_additional_primary_operational_evidence": [
                "i2_operational_materiality",
                "public_anchor",
                "event_mechanism_logistics_consequence",
            ],
            "protocol_note": (
                "A storm track is a driver, not an episode. No blind pre-collapse "
                "of 4197 storm-node hits into storm-level D5 rows. H1/H2/H4 grouping "
                "happens later at episode authoring."
            ),
        },
        "s1_field_sufficiency": {
            "when_body_unreadable": "unknown",
            "when_body_verified": "body_present_not_adjudicated",
            "protocol_note": (
                "I1/I2/I3 admission is Phase 2. Inventory does not score or drop "
                "candidates."
            ),
        },
        "notes": list(notes),
        "next_phase2_step": (
            "After GRAIN_DATA_ROOT restore and pointer re-verification: Phase-2 "
            "I1/I2/I3 triage per candidate (quote-or-null; S4 requires primary "
            "operational evidence beyond HURDAT2 proximity). No episode YAML and "
            "no no-episode dispositions in D6 inventory."
        ),
    }
    summary_path.write_text(
        yaml.safe_dump(summary, sort_keys=False, allow_unicode=False),
        encoding="utf-8",
    )
    return csv_digest


def enrich_existing_capture_dir(
    *,
    sweep_id: str,
    capture_dir: str,
    raw_bytes: bytes,
    source_reference: str,
    sweeps_subdir: str = "sweeps",
    data_root_path: Path | str | None = None,
    retrieved_on: str | None = None,
    original_filename: str | None = None,
    content_type: str | None = None,
) -> CaptureRecord:
    """Append evidence to an existing source-derived capture dir only.

    ``capture_dir`` is the live D6 directory name (S1-<controlnumber> /
    S4-<storm>-<node>), not a minted CAND-* id. Refuses to create a new
    candidate identity.
    """
    if capture_dir.startswith("CAND-"):
        raise EvidenceInventoryError(
            "refuse to enrich a minted CAND-* directory; live capture dirs are "
            "source-derived"
        )
    root = Path(data_root_path) if data_root_path is not None else None
    if root is None:
        env = os.environ.get("GRAIN_DATA_ROOT")
        if not env:
            raise EvidenceInventoryError(
                "GRAIN_DATA_ROOT unset; refuse to invent a capture root for enrichment"
            )
        root = Path(env)
    existing = root / sweeps_subdir / sweep_id / capture_dir
    if not existing.is_dir():
        raise EvidenceInventoryError(
            f"capture dir does not exist ({existing}); refuse to mint a new home"
        )
    return capture_candidate_evidence(
        sweep_id=sweep_id,
        candidate_id=capture_dir,
        raw_bytes=raw_bytes,
        source_reference=source_reference,
        sweeps_subdir=sweeps_subdir,
        data_root_path=root,
        retrieved_on=retrieved_on,
        original_filename=original_filename,
        content_type=content_type,
    )


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description="Fail-closed D6 evidence inventory over the frozen D5 universe"
    )
    parser.add_argument("--data-root", type=Path, help="Override GRAIN_DATA_ROOT")
    parser.add_argument(
        "--persist",
        action="store_true",
        help="Write derived inventory CSV/YAML under research/episodes/discovery/",
    )
    parser.add_argument(
        "--refetch-hurdat2",
        action="store_true",
        help="Re-fetch public HURDAT2 archives to verify digest only (not a new candidate)",
    )
    args = parser.parse_args()
    result = build_evidence_inventory(
        data_root_path=args.data_root,
        persist=args.persist,
        refetch_hurdat2=args.refetch_hurdat2,
    )
    print(yaml.safe_dump(
        {
            "access_gate": result.access_gate,
            "data_root_status": result.data_root_status,
            "data_root": result.data_root or None,
            "candidate_universe_version": result.candidate_universe_version,
            "pointer_counts": result.counts,
            "hurdat2_counts": result.hurdat2_counts,
            "hurdat2_public_verified": result.hurdat2_public_verified,
            "enrichment_count": result.enrichment_count,
            "inventory_csv_digest": result.inventory_csv_digest,
        },
        sort_keys=False,
    ))


if __name__ == "__main__":
    main()
