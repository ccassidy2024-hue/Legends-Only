"""Pre-episode raw-capture path helpers and D6 evidence persistence.

Architecture: ADR-0010. Concrete values: ADR-0013
(``capture.sweeps_subdir = "sweeps"``,
``capture.rehome_policy = "candidate_keyed_no_move"``).

Canonical layout under ``$GRAIN_DATA_ROOT/<sweeps_subdir>/<sweep_id>/<candidate_id>/``:

- ``objects/<sha256>`` — immutable content-addressed raw bytes
- ``manifest.yaml`` — append-only capture/provenance records

Assumption (this PR): one writer per candidate directory. No locking /
distributed-concurrency infrastructure.

Does not download, select sources, invent metadata, move evidence under
episodes, or implement rehome policies other than candidate-keyed no-move.
"""

from __future__ import annotations

import hashlib
import os
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from grainsys.discovery.config import (
    DiscoveryConfigError,
    require_nonempty_str,
    require_safe_path_component,
    require_safe_relative_path,
)

CAPTURE_MANIFEST_SCHEMA_VERSION = "1.0"
MANIFEST_FILENAME = "manifest.yaml"
OBJECTS_DIRNAME = "objects"

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_OPTIONAL_RECORD_KEYS = ("retrieved_on", "original_filename", "content_type")


class CapturePathError(ValueError):
    """Invalid capture path arguments."""


class CaptureError(ValueError):
    """Fail-closed capture / provenance persistence error."""


@dataclass(frozen=True)
class CaptureRecord:
    """One append-only capture/provenance record (not a D5 identity row)."""

    source_reference: str
    sha256: str
    byte_length: int
    retrieved_on: str | None = None
    original_filename: str | None = None
    content_type: str | None = None

    def to_mapping(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "source_reference": self.source_reference,
            "sha256": self.sha256,
            "byte_length": self.byte_length,
        }
        for key in _OPTIONAL_RECORD_KEYS:
            val = getattr(self, key)
            if val is not None:
                out[key] = val
        return out


def _as_capture_error(exc: DiscoveryConfigError) -> CapturePathError:
    return CapturePathError(str(exc))


def _require_component(value: Any, *, field: str) -> str:
    try:
        return require_safe_path_component(value, field=field)
    except DiscoveryConfigError as exc:
        raise _as_capture_error(exc) from exc


def _require_subdir(value: Any, *, field: str) -> str:
    try:
        return require_safe_relative_path(value, field=field)
    except DiscoveryConfigError as exc:
        raise _as_capture_error(exc) from exc


def _assert_contained(*, path: Path, root: Path, field: str) -> Path:
    """Resolve ``path`` and require it stays under ``root``."""
    try:
        root_resolved = root.resolve()
        path_resolved = path.resolve()
    except OSError as exc:
        raise CapturePathError(f"{field} could not be resolved: {exc}") from exc
    try:
        path_resolved.relative_to(root_resolved)
    except ValueError as exc:
        raise CapturePathError(
            f"{field} resolves outside data root ({path_resolved} not under "
            f"{root_resolved}); refuse"
        ) from exc
    return path_resolved


def data_root(explicit: Path | str | None = None) -> Path:
    """Resolve GRAIN_DATA_ROOT or an explicit root. Does not create directories.

    Explicit roots may be absolute. Environment / explicit values are not
    invented; absence fails closed.
    """
    if explicit is not None:
        if isinstance(explicit, bool) or not isinstance(explicit, (Path, str)):
            raise CapturePathError(
                f"data_root must be a path or string (got {type(explicit).__name__})"
            )
        if isinstance(explicit, str) and ("\x00" in explicit or not explicit.strip()):
            raise CapturePathError("data_root string must be nonempty without NUL")
        return Path(explicit)
    env = os.environ.get("GRAIN_DATA_ROOT")
    if not env:
        raise CapturePathError(
            "GRAIN_DATA_ROOT is unset and no explicit root was provided. "
            "Refuse to invent a data root."
        )
    if "\x00" in env:
        raise CapturePathError("GRAIN_DATA_ROOT contains NUL; refuse")
    return Path(env)


def sweeps_root(
    *,
    data_root_path: Path | str | None = None,
    sweeps_subdir: str,
) -> Path:
    """Root for Phase 1 hits before any episode_id exists."""
    subdir = _require_subdir(sweeps_subdir, field="sweeps_subdir")
    root = data_root(data_root_path)
    joined = root.joinpath(*subdir.split("/"))
    _assert_contained(path=joined, root=root, field="sweeps_root")
    return joined


def candidate_capture_dir(
    *,
    sweep_id: str,
    candidate_id: str,
    data_root_path: Path | str | None = None,
    sweeps_subdir: str,
) -> Path:
    """Directory for one pre-episode sweep hit.

    Layout: ``$GRAIN_DATA_ROOT/<sweeps_subdir>/<sweep_id>/<candidate_id>/``

    Does not create directories or download documents. Rejects non-string/bool,
    absolute/rooted, dot/dot-dot, separators, NUL, and traversal.
    """
    sid = _require_component(sweep_id, field="sweep_id")
    cid = _require_component(candidate_id, field="candidate_id")
    base = sweeps_root(data_root_path=data_root_path, sweeps_subdir=sweeps_subdir)
    root = data_root(data_root_path)
    joined = base / sid / cid
    _assert_contained(path=joined, root=root, field="candidate_capture_dir")
    return joined


def _sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _require_sha256_hex(value: str, *, field: str) -> str:
    if not _SHA256_RE.fullmatch(value):
        raise CaptureError(f"{field} must be 64 lowercase hex chars (got {value!r})")
    return value


def _optional_str(value: Any, *, field: str) -> str | None:
    if value is None:
        return None
    try:
        return require_nonempty_str(value, field=field)
    except DiscoveryConfigError as exc:
        raise CaptureError(str(exc)) from exc


def _yaml_scalar(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int) and not isinstance(value, bool):
        return str(value)
    import json

    # Quote all strings so ISO dates / version-like tokens stay strings on reload.
    return json.dumps(str(value))


def render_capture_manifest_yaml(
    *,
    schema_version: str,
    candidate_id: str,
    sweep_id: str,
    records: list[CaptureRecord],
) -> bytes:
    """Deterministic UTF-8 YAML bytes for an ordered capture manifest."""
    lines: list[str] = [
        f"schema_version: {_yaml_scalar(schema_version)}",
        f"candidate_id: {_yaml_scalar(candidate_id)}",
        f"sweep_id: {_yaml_scalar(sweep_id)}",
        "records:",
    ]
    if not records:
        lines.append("  []")
    else:
        for rec in records:
            mapping = rec.to_mapping()
            first = True
            for key, val in mapping.items():
                if first:
                    lines.append(f"  - {key}: {_yaml_scalar(val)}")
                    first = False
                else:
                    lines.append(f"    {key}: {_yaml_scalar(val)}")
    return ("\n".join(lines) + "\n").encode("utf-8")


def _parse_manifest(data: dict[str, Any], *, where: str) -> tuple[str, str, str, list[CaptureRecord]]:
    if not isinstance(data, dict):
        raise CaptureError(f"{where}: manifest must be a mapping")
    schema_version = data.get("schema_version")
    candidate_id = data.get("candidate_id")
    sweep_id = data.get("sweep_id")
    records_raw = data.get("records")
    if not isinstance(schema_version, str) or not schema_version:
        raise CaptureError(f"{where}: missing schema_version")
    if not isinstance(candidate_id, str) or not candidate_id:
        raise CaptureError(f"{where}: missing candidate_id")
    if not isinstance(sweep_id, str) or not sweep_id:
        raise CaptureError(f"{where}: missing sweep_id")
    if not isinstance(records_raw, list):
        raise CaptureError(f"{where}: records must be a list")
    records: list[CaptureRecord] = []
    for i, item in enumerate(records_raw):
        if not isinstance(item, dict):
            raise CaptureError(f"{where}: records[{i}] must be a mapping")
        try:
            source_reference = require_nonempty_str(
                item.get("source_reference"), field=f"records[{i}].source_reference"
            )
            sha256 = _require_sha256_hex(
                require_nonempty_str(item.get("sha256"), field=f"records[{i}].sha256"),
                field=f"records[{i}].sha256",
            )
        except DiscoveryConfigError as exc:
            raise CaptureError(str(exc)) from exc
        byte_length = item.get("byte_length")
        if isinstance(byte_length, bool) or not isinstance(byte_length, int):
            raise CaptureError(f"{where}: records[{i}].byte_length must be an int")
        if byte_length < 0:
            raise CaptureError(f"{where}: records[{i}].byte_length must be >= 0")
        opt: dict[str, str | None] = {}
        for key in _OPTIONAL_RECORD_KEYS:
            if key in item and item[key] is not None:
                try:
                    opt[key] = require_nonempty_str(
                        item[key], field=f"records[{i}].{key}"
                    )
                except DiscoveryConfigError as exc:
                    raise CaptureError(str(exc)) from exc
            else:
                opt[key] = None
        forbidden = set(item) - {
            "source_reference",
            "sha256",
            "byte_length",
            *_OPTIONAL_RECORD_KEYS,
        }
        if forbidden:
            raise CaptureError(
                f"{where}: records[{i}] has unknown keys {sorted(forbidden)}; refuse"
            )
        records.append(
            CaptureRecord(
                source_reference=source_reference,
                sha256=sha256,
                byte_length=byte_length,
                retrieved_on=opt["retrieved_on"],
                original_filename=opt["original_filename"],
                content_type=opt["content_type"],
            )
        )
    return schema_version, candidate_id, sweep_id, records


def _load_manifest(path: Path) -> tuple[str, str, str, list[CaptureRecord]]:
    import yaml

    try:
        with path.open(encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
    except OSError as exc:
        raise CaptureError(f"cannot read manifest {path}: {exc}") from exc
    except yaml.YAMLError as exc:
        raise CaptureError(f"manifest {path} unparseable: {exc}") from exc
    return _parse_manifest(data or {}, where=str(path))


def _records_equal(a: CaptureRecord, b: CaptureRecord) -> bool:
    return asdict(a) == asdict(b)


def _optionals_conflict(existing: CaptureRecord, new: CaptureRecord) -> bool:
    for key in _OPTIONAL_RECORD_KEYS:
        if getattr(existing, key) != getattr(new, key):
            return True
    return False


def _persist_raw_object(*, objects_dir: Path, digest: str, raw_bytes: bytes) -> Path:
    """Create ``objects/<sha256>`` without overwriting an existing object.

    Uses exclusive create / rename-fails-if-exists semantics. Never uses
    overwrite-replace against an existing canonical object.
    """
    objects_dir.mkdir(parents=True, exist_ok=True)
    obj_path = objects_dir / digest
    expected_len = len(raw_bytes)

    if obj_path.exists():
        try:
            existing = obj_path.read_bytes()
        except OSError as exc:
            raise CaptureError(f"cannot read existing object {obj_path}: {exc}") from exc
        got = _sha256_hex(existing)
        if got != digest or got != obj_path.name:
            raise CaptureError(
                f"existing object {obj_path} is corrupt/mismatched "
                f"(hash {got!r} != expected {digest!r}); refuse overwrite"
            )
        if len(existing) != expected_len:
            raise CaptureError(
                f"existing object {obj_path} byte_length {len(existing)} != "
                f"expected {expected_len}; refuse"
            )
        return obj_path

    tmp_path = objects_dir / f".{digest}.tmp"
    try:
        with open(tmp_path, "wb") as fh:
            fh.write(raw_bytes)
            fh.flush()
            os.fsync(fh.fileno())
        verified = tmp_path.read_bytes()
        got = _sha256_hex(verified)
        if got != digest or len(verified) != expected_len:
            raise CaptureError(
                f"temp object failed self-check (hash {got!r}, len {len(verified)})"
            )
        # os.rename fails if destination exists (POSIX and Windows) — never overwrite.
        try:
            os.rename(tmp_path, obj_path)
        except FileExistsError:
            try:
                tmp_path.unlink(missing_ok=True)
            except OSError:
                pass
            return _persist_raw_object(
                objects_dir=objects_dir, digest=digest, raw_bytes=raw_bytes
            )
    except CaptureError:
        try:
            tmp_path.unlink(missing_ok=True)
        except OSError:
            pass
        raise
    except OSError as exc:
        try:
            tmp_path.unlink(missing_ok=True)
        except OSError:
            pass
        raise CaptureError(f"failed to persist object {digest}: {exc}") from exc

    final = obj_path.read_bytes()
    final_hash = _sha256_hex(final)
    if final_hash != digest or final_hash != obj_path.name or len(final) != expected_len:
        raise CaptureError(
            f"persisted object {obj_path} failed post-write verification"
        )
    return obj_path


def _atomic_write_manifest(path: Path, payload: bytes) -> None:
    """Atomically replace the whole manifest file via tmp + replace."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    try:
        with open(tmp, "wb") as fh:
            fh.write(payload)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)
    except OSError as exc:
        try:
            tmp.unlink(missing_ok=True)
        except OSError:
            pass
        raise CaptureError(f"failed to write manifest {path}: {exc}") from exc


def capture_candidate_evidence(
    *,
    sweep_id: str,
    candidate_id: str,
    raw_bytes: bytes,
    source_reference: str,
    sweeps_subdir: str,
    data_root_path: Path | str | None = None,
    retrieved_on: str | None = None,
    original_filename: str | None = None,
    content_type: str | None = None,
) -> CaptureRecord:
    """Persist raw bytes under a candidate-keyed capture directory.

    Persistence only — no networking. ``original_filename`` is metadata only and
    never influences the on-disk path (always ``objects/<sha256>``).

    Assumption: one writer per candidate directory.
    """
    if not isinstance(raw_bytes, (bytes, bytearray)):
        raise CaptureError(
            f"raw_bytes must be bytes (got {type(raw_bytes).__name__})"
        )
    raw = bytes(raw_bytes)

    try:
        source_reference = require_nonempty_str(
            source_reference, field="source_reference"
        )
    except DiscoveryConfigError as exc:
        raise CaptureError(str(exc)) from exc

    sid = _require_component(sweep_id, field="sweep_id")
    cid = _require_component(candidate_id, field="candidate_id")
    # Path safety for sweeps_subdir / containment via candidate_capture_dir.
    cap_dir = candidate_capture_dir(
        sweep_id=sid,
        candidate_id=cid,
        data_root_path=data_root_path,
        sweeps_subdir=sweeps_subdir,
    )
    root = data_root(data_root_path)
    _assert_contained(path=cap_dir, root=root, field="candidate_capture_dir")

    retrieved_on = _optional_str(retrieved_on, field="retrieved_on")
    original_filename = _optional_str(original_filename, field="original_filename")
    content_type = _optional_str(content_type, field="content_type")

    digest = _sha256_hex(raw)
    byte_length = len(raw)
    new_record = CaptureRecord(
        source_reference=source_reference,
        sha256=digest,
        byte_length=byte_length,
        retrieved_on=retrieved_on,
        original_filename=original_filename,
        content_type=content_type,
    )

    objects_dir = cap_dir / OBJECTS_DIRNAME
    _assert_contained(path=objects_dir, root=root, field="objects_dir")
    _persist_raw_object(objects_dir=objects_dir, digest=digest, raw_bytes=raw)

    manifest_path = cap_dir / MANIFEST_FILENAME
    _assert_contained(path=manifest_path, root=root, field="manifest_path")

    if manifest_path.exists():
        schema_version, mid, msweep, old_records = _load_manifest(manifest_path)
        if mid != cid:
            raise CaptureError(
                f"manifest candidate_id {mid!r} != expected {cid!r}; refuse"
            )
        if msweep != sid:
            raise CaptureError(
                f"manifest sweep_id {msweep!r} != expected {sid!r}; refuse"
            )
        if schema_version != CAPTURE_MANIFEST_SCHEMA_VERSION:
            raise CaptureError(
                f"unsupported capture manifest schema_version {schema_version!r}"
            )
        for existing in old_records:
            if (
                existing.source_reference == new_record.source_reference
                and existing.sha256 == new_record.sha256
            ):
                if _optionals_conflict(existing, new_record):
                    raise CaptureError(
                        "conflicting optional provenance metadata for identical "
                        f"source_reference={source_reference!r} sha256={digest!r}; "
                        "refuse silent merge"
                    )
                return existing
        new_records = [*old_records, new_record]
        if new_records[:-1] != old_records:
            raise CaptureError("manifest append invariant violated; refuse")
    else:
        schema_version = CAPTURE_MANIFEST_SCHEMA_VERSION
        old_records = []
        new_records = [new_record]

    payload = render_capture_manifest_yaml(
        schema_version=schema_version,
        candidate_id=cid,
        sweep_id=sid,
        records=new_records,
    )
    # Re-read guard: if another writer changed the file between load and write,
    # fail closed (single-writer assumption; still refuse silent merge).
    if manifest_path.exists():
        _, _, _, recheck = _load_manifest(manifest_path)
        if recheck != old_records:
            raise CaptureError(
                "manifest changed unexpectedly during append; refuse merge"
            )
    _atomic_write_manifest(manifest_path, payload)

    # Post-condition: prior records unchanged; last record is the new one.
    _, _, _, written = _load_manifest(manifest_path)
    if written[:-1] != old_records:
        raise CaptureError("post-write prior-record invariant failed; refuse")
    if not _records_equal(written[-1], new_record):
        raise CaptureError("post-write new-record invariant failed; refuse")
    return new_record
