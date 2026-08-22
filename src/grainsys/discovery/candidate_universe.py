"""D5 candidate-universe mechanics (ADR-0008).

Binds project constants around the generic mint; no lineage / D6 / prereg values.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from grainsys.discovery.candidates import (
    CandidateIdError,
    mint_candidate_ids,
    researcher_parity_for_candidate_id,
)
from grainsys.discovery.governance import RatificationError, assert_sweep_authorized

# --- ADR-0008 / D5 ratified constants (wrapper owns these; mint stays generic) ---

CANONICAL_CANDIDATES_RELATIVE = Path(
    "research/episodes/discovery/candidates/candidates.csv"
)
CANONICAL_CANDIDATE_UNIVERSE_MANIFEST_RELATIVE = Path(
    "research/episodes/discovery/candidates/candidate_universe.yaml"
)
CANDIDATE_UNIVERSE_SCHEMA_RELATIVE = Path(
    "research/episodes/discovery/candidates/candidate_universe.schema.yaml"
)

D5_ID_PREFIX = "CAND"
D5_ORDERING_KEYS: tuple[str, ...] = ("sweep_id", "source_reference")
D5_STABLE_ID_KEY: str | None = None

CANDIDATES_CSV_FIELDNAMES: tuple[str, ...] = (
    "candidate_id",
    "sweep_id",
    "source_reference",
    "raw_capture_pointer",
    "document_date",
    "stable_source_id",
)

_REQUIRED_HIT_KEYS: frozenset[str] = frozenset(
    {"sweep_id", "source_reference"}
)


class CandidateUniverseError(ValueError):
    """Fail-closed candidate-universe / completeness errors."""


class UnsupportedCandidateUniverseSupersession(CandidateUniverseError):
    """Cross-version universe supersession is not supported."""


@dataclass(frozen=True)
class FrozenHitSet:
    """Canonical frozen hit input for one candidate-universe build."""

    hits: tuple[dict[str, Any], ...]
    hit_set_digest: str
    required_sweep_families: frozenset[str]
    family_completion_attestations: Mapping[str, bool]


@dataclass(frozen=True)
class CandidateUniverseManifest:
    """In-memory candidate-universe identity record (schema companion)."""

    candidate_universe_version: str
    hit_set_digest: str
    candidates_digest: str
    id_prefix: str
    ordering_keys: tuple[str, ...]
    stable_id_key: None
    required_sweep_families: tuple[str, ...]
    completed_sweep_families: tuple[str, ...]
    candidate_count: int
    frozen_at: str | None
    supersedes: None
    candidates_table_relative: str = CANONICAL_CANDIDATES_RELATIVE.as_posix()
    manifest_relative: str = CANONICAL_CANDIDATE_UNIVERSE_MANIFEST_RELATIVE.as_posix()

    def to_mapping(self) -> dict[str, Any]:
        return {
            "candidate_universe_version": self.candidate_universe_version,
            "hit_set_digest": self.hit_set_digest,
            "candidates_digest": self.candidates_digest,
            "id_prefix": self.id_prefix,
            "ordering_keys": list(self.ordering_keys),
            "stable_id_key": self.stable_id_key,
            "required_sweep_families": list(self.required_sweep_families),
            "completed_sweep_families": list(self.completed_sweep_families),
            "candidate_count": self.candidate_count,
            "frozen_at": self.frozen_at,
            "supersedes": self.supersedes,
            "candidates_table_relative": self.candidates_table_relative,
            "manifest_relative": self.manifest_relative,
        }


@dataclass(frozen=True)
class CandidateUniverseBuildResult:
    """Result of an authorized D5 candidate-universe build (no lineage)."""

    frozen_hit_set: FrozenHitSet
    candidates: tuple[dict[str, Any], ...]
    candidates_csv_bytes: bytes
    candidates_digest: str
    manifest: CandidateUniverseManifest
    researcher_parity: Mapping[str, str]
    written_candidates_path: Path | None
    written_manifest_path: Path | None

    @property
    def written_path(self) -> Path | None:
        """Backward-compatible alias for the candidates.csv path."""
        return self.written_candidates_path


def candidates_table_path(repo_root: Path) -> Path:
    return Path(repo_root).resolve() / CANONICAL_CANDIDATES_RELATIVE


def candidate_universe_manifest_path(repo_root: Path) -> Path:
    return Path(repo_root).resolve() / CANONICAL_CANDIDATE_UNIVERSE_MANIFEST_RELATIVE


def candidate_universe_schema_path(repo_root: Path) -> Path:
    return Path(repo_root).resolve() / CANDIDATE_UNIVERSE_SCHEMA_RELATIVE


def _canonical_json_bytes(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode(
        "utf-8"
    )


def _sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def candidate_universe_version_from_hit_set_digest(hit_set_digest: str) -> str:
    """Full collision-safe identity token (ADR-0008); not truncated."""
    digest = str(hit_set_digest).strip().lower()
    if len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
        raise CandidateUniverseError(
            f"hit_set_digest must be 64-hex SHA-256; got {hit_set_digest!r}"
        )
    return f"d5cu-{digest}"


def _normalize_hit(raw: Mapping[str, Any], *, index: int) -> dict[str, Any]:
    from grainsys.discovery.candidates import FORBIDDEN_CANDIDATE_FIELDS

    missing = _REQUIRED_HIT_KEYS - set(raw)
    if missing:
        raise CandidateUniverseError(
            f"hit[{index}] missing required keys: {sorted(missing)}"
        )
    forbidden = FORBIDDEN_CANDIDATE_FIELDS & set(raw)
    if forbidden:
        raise CandidateUniverseError(
            f"hit[{index}] contains forbidden fields: {sorted(forbidden)}"
        )
    out: dict[str, Any] = {}
    for key, val in raw.items():
        if key == "candidate_id":
            continue
        out[str(key)] = "" if val is None else str(val).strip()
    if not out["sweep_id"]:
        raise CandidateUniverseError(f"hit[{index}] empty sweep_id")
    if not out["source_reference"]:
        raise CandidateUniverseError(f"hit[{index}] empty source_reference")
    # Ensure CSV columns exist with stable empty defaults where optional.
    out.setdefault("raw_capture_pointer", "")
    out.setdefault("document_date", "")
    out.setdefault("stable_source_id", "")
    return out


def _coerce_attestation_bool(family: str, raw: Any) -> bool:
    """Normalize attestation value; malformed / contradictory → fail closed."""
    if isinstance(raw, bool):
        return raw
    if isinstance(raw, Mapping):
        declared = raw.get("sweep_family")
        if declared is not None and str(declared).strip() != family:
            raise CandidateUniverseError(
                f"completion attestation family mismatch: key={family!r} "
                f"declared sweep_family={declared!r}"
            )
        if "complete" in raw and isinstance(raw["complete"], bool):
            return bool(raw["complete"])
        status = str(raw.get("status", "")).strip().lower()
        if status in {"complete", "attested", "ok", "true"}:
            return True
        if status in {"incomplete", "false", "pending", "missing", ""}:
            return False
        raise CandidateUniverseError(
            f"malformed completion attestation for {family!r}: {raw!r}"
        )
    if raw is True or raw == 1 or str(raw).strip().lower() in {"true", "complete", "ok"}:
        return True
    if raw is False or raw == 0 or str(raw).strip().lower() in {
        "false",
        "incomplete",
        "pending",
        "missing",
        "",
    }:
        return False
    raise CandidateUniverseError(
        f"malformed completion attestation for {family!r}: {raw!r}"
    )


def _validate_completion_attestations(
    required_sweep_families: frozenset[str],
    family_completion_attestations: Mapping[str, Any],
) -> dict[str, bool]:
    if not required_sweep_families:
        raise CandidateUniverseError(
            "required_sweep_families is empty/absent; refuse hidden S1–S8 default"
        )
    attested_keys = {str(k).strip() for k in family_completion_attestations}
    missing = required_sweep_families - attested_keys
    if missing:
        raise CandidateUniverseError(
            "complete-hit-set gate failed: required family lacks a completion "
            f"attestation: {sorted(missing)}"
        )
    extra = attested_keys - required_sweep_families
    if extra:
        raise CandidateUniverseError(
            "complete-hit-set gate failed: completion attestations for unexpected "
            f"families (fail closed): {sorted(extra)}"
        )
    normalized: dict[str, bool] = {}
    for family in sorted(required_sweep_families):
        ok = _coerce_attestation_bool(family, family_completion_attestations[family])
        if not ok:
            raise CandidateUniverseError(
                f"complete-hit-set gate failed: family {family!r} not attested complete"
            )
        normalized[family] = True
    return normalized


def freeze_hit_set(
    hits: Sequence[Mapping[str, Any]],
    *,
    required_sweep_families: Sequence[str] | frozenset[str] | set[str] | None,
    family_completion_attestations: Mapping[str, Any],
) -> FrozenHitSet:
    """Freeze hits after bidirectional complete-hit-set gating (fail closed).

    Direction A: every required_sweep_family is represented and completion-attested.
    Direction B: every hit's sweep_id belongs to required_sweep_families.
    Unexpected / unregistered families fail closed (not ignored, not auto-expanded).
    """
    if required_sweep_families is None:
        raise CandidateUniverseError(
            "required_sweep_families is absent; refuse hidden default"
        )
    required = frozenset(str(x).strip() for x in required_sweep_families if str(x).strip())
    attestations = _validate_completion_attestations(
        required, family_completion_attestations
    )

    normalized: list[dict[str, Any]] = []
    for i, raw in enumerate(hits):
        if not isinstance(raw, Mapping):
            raise CandidateUniverseError(f"hit[{i}] must be a mapping")
        normalized.append(_normalize_hit(raw, index=i))

    # Canonical order for digest (independent of enumeration order).
    normalized.sort(
        key=lambda h: tuple(str(h.get(k, "")) for k in D5_ORDERING_KEYS)
    )

    present_families = {h["sweep_id"] for h in normalized}
    missing_families = required - present_families
    if missing_families:
        raise CandidateUniverseError(
            "complete-hit-set gate failed: no hits for required families: "
            f"{sorted(missing_families)}"
        )
    unexpected = present_families - required
    if unexpected:
        raise CandidateUniverseError(
            "complete-hit-set gate failed: hits from unexpected/unregistered "
            f"sweep families outside required set (fail closed): {sorted(unexpected)}"
        )

    payload = {
        "hits": [
            {k: h.get(k, "") for k in CANDIDATES_CSV_FIELDNAMES if k != "candidate_id"}
            for h in normalized
        ],
        "required_sweep_families": sorted(required),
        "family_completion_attestations": {
            k: attestations[k] for k in sorted(attestations)
        },
    }
    digest = _sha256_hex(_canonical_json_bytes(payload))
    return FrozenHitSet(
        hits=tuple(normalized),
        hit_set_digest=digest,
        required_sweep_families=required,
        family_completion_attestations=attestations,
    )


def mint_d5_candidate_ids(hits: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """D5 wrapper: binds ratified ordering_keys / id_prefix / stable_id_key.

    Accepts raw or frozen hits. No override knobs — project constants only.
    """
    try:
        return mint_candidate_ids(
            list(hits),
            ordering_keys=D5_ORDERING_KEYS,
            id_prefix=D5_ID_PREFIX,
            stable_id_key=D5_STABLE_ID_KEY,
        )
    except CandidateIdError:
        raise
    except Exception as exc:
        raise CandidateUniverseError(str(exc)) from exc


def researcher_parity_map(candidate_ids: Sequence[str]) -> dict[str, str]:
    return {cid: researcher_parity_for_candidate_id(cid) for cid in candidate_ids}


def render_candidates_csv_bytes(rows: Sequence[Mapping[str, Any]]) -> bytes:
    lines = [",".join(CANDIDATES_CSV_FIELDNAMES)]
    for row in rows:
        fields: list[str] = []
        for col in CANDIDATES_CSV_FIELDNAMES:
            val = "" if row.get(col) is None else str(row.get(col, ""))
            if any(c in val for c in (",", '"', "\n", "\r")):
                val = '"' + val.replace('"', '""') + '"'
            fields.append(val)
        lines.append(",".join(fields))
    return ("\n".join(lines) + "\n").encode("utf-8")


def candidates_digest_for_csv_bytes(csv_bytes: bytes) -> str:
    return _sha256_hex(csv_bytes)


def build_manifest(
    *,
    frozen: FrozenHitSet,
    csv_bytes: bytes,
    candidate_count: int,
    frozen_at: str | None = None,
) -> CandidateUniverseManifest:
    """Build manifest. Digests/version do not depend on frozen_at."""
    return CandidateUniverseManifest(
        candidate_universe_version=candidate_universe_version_from_hit_set_digest(
            frozen.hit_set_digest
        ),
        hit_set_digest=frozen.hit_set_digest,
        candidates_digest=candidates_digest_for_csv_bytes(csv_bytes),
        id_prefix=D5_ID_PREFIX,
        ordering_keys=D5_ORDERING_KEYS,
        stable_id_key=None,
        required_sweep_families=tuple(sorted(frozen.required_sweep_families)),
        completed_sweep_families=tuple(sorted(frozen.required_sweep_families)),
        candidate_count=candidate_count,
        frozen_at=frozen_at,
        supersedes=None,
    )


def render_manifest_yaml(manifest: CandidateUniverseManifest) -> bytes:
    """Minimal YAML emitter for the manifest mapping (UTF-8)."""
    data = manifest.to_mapping()
    lines: list[str] = []

    def emit(key: str, value: Any, indent: int = 0) -> None:
        pad = "  " * indent
        if isinstance(value, dict):
            lines.append(f"{pad}{key}:")
            if not value:
                lines.append(f"{pad}  {{}}")
                return
            for sk, sv in value.items():
                emit(str(sk), sv, indent + 1)
        elif isinstance(value, list):
            lines.append(f"{pad}{key}:")
            if not value:
                lines.append(f"{pad}  []")
                return
            for item in value:
                if isinstance(item, (dict, list)):
                    raise CandidateUniverseError(
                        "nested list/dict unsupported in manifest YAML"
                    )
                lines.append(f"{pad}- {_yaml_scalar(item)}")
        else:
            lines.append(f"{pad}{key}: {_yaml_scalar(value)}")

    for key, value in data.items():
        emit(str(key), value, 0)
    return ("\n".join(lines) + "\n").encode("utf-8")


def _yaml_scalar(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int) and not isinstance(value, bool):
        return str(value)
    text = str(value)
    if text == "" or any(
        c in text for c in (":", "#", "\n", '"', "'", "{", "}", "[", "]", ",")
    ):
        return json.dumps(text)
    if text.lower() in {"true", "false", "null", "yes", "no", "on", "off"}:
        return json.dumps(text)
    return text


def write_canonical_universe_artifacts(
    repo_root: Path,
    *,
    csv_bytes: bytes,
    manifest: CandidateUniverseManifest,
) -> tuple[Path, Path]:
    """Atomically persist candidates.csv AND candidate_universe.yaml together.

    Fail-closed if either canonical path already exists. On any failure after a
    partial write of *new* artifacts, remove both new paths so one canonical
    artifact is never left without the other. Does not supersede an existing
    universe.
    """
    root = Path(repo_root).resolve()
    csv_path = root / CANONICAL_CANDIDATES_RELATIVE
    manifest_path = root / CANONICAL_CANDIDATE_UNIVERSE_MANIFEST_RELATIVE

    if csv_path.exists():
        raise CandidateUniverseError(
            f"refuse overwrite: candidates table already exists at {csv_path}"
        )
    if manifest_path.exists():
        raise CandidateUniverseError(
            f"refuse overwrite: candidate-universe manifest already exists at "
            f"{manifest_path}"
        )

    expected_digest = candidates_digest_for_csv_bytes(csv_bytes)
    if manifest.candidates_digest != expected_digest:
        raise CandidateUniverseError(
            "manifest.candidates_digest does not match exact candidates.csv bytes"
        )
    expected_version = candidate_universe_version_from_hit_set_digest(
        manifest.hit_set_digest
    )
    if manifest.candidate_universe_version != expected_version:
        raise CandidateUniverseError(
            "manifest.candidate_universe_version does not match hit_set_digest "
            "identity"
        )
    if manifest.supersedes is not None:
        raise UnsupportedCandidateUniverseSupersession(
            "universe supersession is unsupported; supersedes must be null"
        )

    csv_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    csv_tmp = csv_path.with_name(csv_path.name + ".tmp")
    manifest_tmp = manifest_path.with_name(manifest_path.name + ".tmp")
    written_final: list[Path] = []

    try:
        csv_tmp.write_bytes(csv_bytes)
        manifest_tmp.write_bytes(render_manifest_yaml(manifest))
        csv_tmp.replace(csv_path)
        written_final.append(csv_path)
        manifest_tmp.replace(manifest_path)
        written_final.append(manifest_path)
    except Exception as exc:
        for p in (csv_tmp, manifest_tmp, *written_final):
            try:
                if p.exists():
                    p.unlink()
            except OSError:
                pass
        raise CandidateUniverseError(
            f"atomic dual-persist failed; rolled back new artifacts: {exc}"
        ) from exc

    if not csv_path.is_file() or not manifest_path.is_file():
        for p in (csv_path, manifest_path):
            try:
                if p.exists():
                    p.unlink()
            except OSError:
                pass
        raise CandidateUniverseError(
            "atomic dual-persist incomplete; neither canonical artifact retained "
            "alone"
        )

    return csv_path, manifest_path


def write_canonical_candidates_csv(
    *,
    repo_root: Path,
    csv_bytes: bytes,
    manifest: CandidateUniverseManifest | None = None,
) -> Path:
    """Persist canonical candidates.csv with matching manifest (dual write).

    If ``manifest`` is omitted, refuses — authorized future builds must persist
    both artifacts coherently (ADR-0008 version discipline).
    """
    if manifest is None:
        raise CandidateUniverseError(
            "refuse CSV-only write: authorized build must persist candidates.csv "
            "and candidate_universe.yaml together"
        )
    csv_path, _manifest_path = write_canonical_universe_artifacts(
        repo_root, csv_bytes=csv_bytes, manifest=manifest
    )
    return csv_path


def build_authorized_d5_candidate_universe(
    *,
    repo_root: Path,
    hits: Sequence[Mapping[str, Any]],
    required_sweep_families: Sequence[str] | frozenset[str] | set[str] | None,
    family_completion_attestations: Mapping[str, Any],
    execution_commit: str | None = None,
    persist: bool = False,
    frozen_at: str | None = None,
    supersedes: str | None = None,
) -> CandidateUniverseBuildResult:
    """Authorized D5 build: auth → freeze → mint → digests → optional dual persist.

    ``frozen_at`` is optional caller-supplied observed metadata only. It must not
    be fabricated here (no datetime.now / time.time). Absence means no freeze-time
    observation was recorded. Digests and ``candidate_universe_version`` do not
    depend on ``frozen_at``.
    """
    if supersedes is not None:
        raise UnsupportedCandidateUniverseSupersession(
            "universe supersession is unsupported; supersedes must be null"
        )
    if required_sweep_families is None:
        raise CandidateUniverseError(
            "required_sweep_families is absent; refuse hidden default"
        )

    root = Path(repo_root).resolve()
    try:
        assert_sweep_authorized(root, execution_commit=execution_commit)
    except RatificationError as exc:
        raise CandidateUniverseError(f"authorization failed: {exc}") from exc

    frozen = freeze_hit_set(
        hits,
        required_sweep_families=required_sweep_families,
        family_completion_attestations=family_completion_attestations,
    )
    candidates = mint_d5_candidate_ids(list(frozen.hits))
    csv_bytes = render_candidates_csv_bytes(candidates)
    parity = researcher_parity_map([str(r["candidate_id"]) for r in candidates])
    manifest = build_manifest(
        frozen=frozen,
        csv_bytes=csv_bytes,
        candidate_count=len(candidates),
        frozen_at=frozen_at,
    )

    written_csv: Path | None = None
    written_manifest: Path | None = None
    if persist:
        written_csv, written_manifest = write_canonical_universe_artifacts(
            root, csv_bytes=csv_bytes, manifest=manifest
        )

    return CandidateUniverseBuildResult(
        frozen_hit_set=frozen,
        candidates=tuple(candidates),
        candidates_csv_bytes=csv_bytes,
        candidates_digest=manifest.candidates_digest,
        manifest=manifest,
        researcher_parity=parity,
        written_candidates_path=written_csv,
        written_manifest_path=written_manifest,
    )
