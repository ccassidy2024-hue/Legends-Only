"""Candidate-to-episode lineage primitives (ADR-0009).

Pure mechanical helpers for D5-shaped candidate ancestry on episode records.
Cross-artifact freeze accounting is explicit and read-only — ordinary episode
validation does not require a live candidate universe.
"""

from __future__ import annotations

import csv
import io
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from grainsys.discovery.candidate_universe import D5_ID_PREFIX

_CU_VERSION_RE = re.compile(r"^d5cu-[0-9a-f]{64}$")

# Reuse episode-schema decision_reason vocabulary (R1–R13) for no-episode rows.
DECISION_REASON_CODES: frozenset[str] = frozenset(
    {
        "R1",
        "R2",
        "R3",
        "R4",
        "R5",
        "R6",
        "R7",
        "R8",
        "R9",
        "R10",
        "R11",
        "R12",
        "R13",
    }
)


class LineageError(ValueError):
    """Candidate-episode lineage validation error."""


@dataclass
class LineageFindings:
    """Errors from cross-artifact lineage / freeze accounting checks."""

    errors: list[str] = field(default_factory=list)

    def error(self, where: str, code: str, msg: str) -> None:
        self.errors.append(f"{where}: [{code}] {msg}")

    @property
    def ok(self) -> bool:
        return not self.errors


def parse_d5_candidate_sequence(candidate_id: str) -> tuple[int, int]:
    """Parse ``CAND-0001`` into ``(numeric_sequence, suffix_width)``.

    Fails closed on malformed IDs. Width is the digit count after the prefix.
    """
    if not isinstance(candidate_id, str) or not candidate_id.strip():
        raise LineageError(f"candidate_id must be a nonempty string (got {candidate_id!r})")
    prefix = f"{D5_ID_PREFIX}-"
    if not candidate_id.startswith(prefix):
        raise LineageError(
            f"candidate_id {candidate_id!r} must use D5 prefix {D5_ID_PREFIX!r}"
        )
    suffix = candidate_id[len(prefix) :]
    if not suffix or not suffix.isdigit():
        raise LineageError(
            f"candidate_id {candidate_id!r} requires a numeric D5 sequence suffix"
        )
    seq = int(suffix, 10)
    if seq < 1:
        raise LineageError(
            f"candidate_id {candidate_id!r} sequence must be >= 1 (got {seq})"
        )
    return seq, len(suffix)


def validate_candidate_universe_version(version: Any) -> None:
    """Syntactic validity for the D5 ``d5cu-{{64hex}}`` universe token."""
    if not isinstance(version, str):
        raise LineageError(
            f"candidate_universe_version must be a string (got {type(version).__name__})"
        )
    text = version.strip()
    if not _CU_VERSION_RE.fullmatch(text):
        raise LineageError(
            "candidate_universe_version must match d5cu-{64 lowercase hex SHA-256}"
        )


def _validate_candidate_ids_core(candidate_ids: Any, *, require_sorted: bool) -> list[str]:
    if not isinstance(candidate_ids, list):
        raise LineageError("candidate_ids must be a list")
    if not candidate_ids:
        raise LineageError("candidate_ids must be nonempty")

    seen: set[str] = set()
    parsed: list[tuple[int, int, str]] = []
    width: int | None = None

    for item in candidate_ids:
        if not isinstance(item, str):
            raise LineageError(f"candidate_ids element must be str (got {type(item).__name__})")
        if item in seen:
            raise LineageError(f"duplicate candidate_id {item!r} in candidate_ids")
        seen.add(item)
        seq, w = parse_d5_candidate_sequence(item)
        if width is None:
            width = w
        elif w != width:
            raise LineageError(
                "candidate_ids must use a consistent D5 sequence width "
                f"(mixed widths {width} and {w} for {item!r})"
            )
        parsed.append((seq, w, item))

    sequences = [p[0] for p in parsed]
    if require_sorted and sequences != sorted(sequences):
        raise LineageError(
            "candidate_ids must be stored in ascending D5 numeric order"
        )
    return [p[2] for p in parsed]


def validate_candidate_ids_shape(candidate_ids: Any) -> list[str]:
    """Standalone shape check for episode ``candidate_ids`` (no filesystem I/O).

    Returns the validated ID list on success; raises ``LineageError`` on failure.
    """
    return _validate_candidate_ids_core(candidate_ids, require_sorted=True)


def lineage_candidate_id(candidate_ids: Sequence[str]) -> str:
    """Derived R-015 tie key: ``min(candidate_ids)`` under frozen D5 numeric order."""
    validated = _validate_candidate_ids_core(list(candidate_ids), require_sorted=False)
    best = min(validated, key=lambda cid: parse_d5_candidate_sequence(cid)[0])
    return best


def derive_candidate_to_episode_index(
    entries: Sequence[Mapping[str, Any]],
) -> dict[str, tuple[str, ...]]:
    """Derive candidate → episode IDs from episode records (many-to-many).

    Skips ``example: true`` rows. Returns deterministic ascending ordering.
    """
    index: dict[str, set[str]] = {}
    for entry in entries:
        if entry.get("example"):
            continue
        episode_id = entry.get("episode_id")
        if not episode_id:
            continue
        try:
            cids = validate_candidate_ids_shape(entry.get("candidate_ids"))
        except LineageError:
            continue
        for cid in cids:
            index.setdefault(cid, set()).add(str(episode_id))
    return {cid: tuple(sorted(eids)) for cid, eids in sorted(index.items())}


def _read_candidates_csv(
    candidates_csv: bytes | str | Path,
) -> list[dict[str, str]]:
    if isinstance(candidates_csv, Path):
        text = candidates_csv.read_text(encoding="utf-8")
    elif isinstance(candidates_csv, bytes):
        text = candidates_csv.decode("utf-8")
    else:
        text = str(candidates_csv)
    reader = csv.DictReader(io.StringIO(text))
    if reader.fieldnames is None or "candidate_id" not in reader.fieldnames:
        raise LineageError("candidates.csv missing candidate_id column")
    if "episode_id" in (reader.fieldnames or []):
        raise LineageError("candidates.csv must not contain episode_id")
    return [dict(row) for row in reader]


def _load_manifest(
    candidate_universe_manifest: Mapping[str, Any] | str | Path,
) -> dict[str, Any]:
    if isinstance(candidate_universe_manifest, Mapping):
        return dict(candidate_universe_manifest)
    path = Path(candidate_universe_manifest)
    import yaml

    with path.open(encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    if not isinstance(data, dict):
        raise LineageError("candidate_universe manifest must be a mapping")
    return data


def _normalize_dispositions(
    no_episode_dispositions: Sequence[Mapping[str, Any]] | str | Path | None,
) -> list[dict[str, Any]]:
    if no_episode_dispositions is None:
        return []
    if isinstance(no_episode_dispositions, Path):
        import csv as csv_mod

        text = no_episode_dispositions.read_text(encoding="utf-8")
        reader = csv_mod.DictReader(io.StringIO(text))
        return [dict(row) for row in reader]
    if isinstance(no_episode_dispositions, str):
        import csv as csv_mod

        reader = csv_mod.DictReader(io.StringIO(no_episode_dispositions))
        return [dict(row) for row in reader]
    return [dict(row) for row in no_episode_dispositions]


def check_universe_accounting(
    entries: Sequence[Mapping[str, Any]],
    *,
    candidates_csv: bytes | str | Path,
    candidate_universe_manifest: Mapping[str, Any] | str | Path,
    no_episode_dispositions: Sequence[Mapping[str, Any]] | str | Path | None = None,
) -> LineageFindings:
    """Read-only E ∪ N = C freeze accounting against one frozen D5 universe."""
    fx = LineageFindings()
    where = "<universe-accounting>"

    try:
        manifest = _load_manifest(candidate_universe_manifest)
    except LineageError as exc:
        fx.error(where, "L01", str(exc))
        return fx
    except Exception as exc:
        fx.error(where, "L01", f"malformed candidate_universe manifest: {exc}")
        return fx

    version = manifest.get("candidate_universe_version")
    try:
        validate_candidate_universe_version(version)
    except LineageError as exc:
        fx.error(where, "L02", str(exc))
        return fx

    try:
        csv_rows = _read_candidates_csv(candidates_csv)
    except LineageError as exc:
        fx.error(where, "L03", str(exc))
        return fx
    except Exception as exc:
        fx.error(where, "L03", f"malformed candidates.csv: {exc}")
        return fx

    universe_ids: set[str] = set()
    for i, row in enumerate(csv_rows):
        cid = (row.get("candidate_id") or "").strip()
        if not cid:
            fx.error(where, "L04", f"candidates.csv row {i + 2} missing candidate_id")
            continue
        try:
            parse_d5_candidate_sequence(cid)
        except LineageError as exc:
            fx.error(where, "L04", f"candidates.csv row {i + 2}: {exc}")
            continue
        universe_ids.add(cid)

    episode_ids: set[str] = set()
    for entry in entries:
        label = str(entry.get("_file") or entry.get("episode_id") or "<unknown>")
        if entry.get("example"):
            continue
        entry_version = entry.get("candidate_universe_version")
        if entry_version != version:
            fx.error(
                label,
                "L05",
                f"candidate_universe_version {entry_version!r} != manifest {version!r}",
            )
            continue
        try:
            cids = validate_candidate_ids_shape(entry.get("candidate_ids"))
        except LineageError as exc:
            fx.error(label, "L06", str(exc))
            continue
        for cid in cids:
            if cid not in universe_ids:
                fx.error(label, "L07", f"unknown candidate_id {cid!r} not in candidates.csv")
            episode_ids.add(cid)

    disposition_ids: set[str] = set()
    seen_disposition_rows: set[tuple[str, ...]] = set()
    for i, row in enumerate(_normalize_dispositions(no_episode_dispositions)):
        row_label = f"no_episode_dispositions row {i + 1}"
        cid = (row.get("candidate_id") or "").strip()
        reason = (row.get("reason_code") or "").strip()
        if not cid:
            fx.error(row_label, "L08", "missing candidate_id")
            continue
        if not reason:
            fx.error(row_label, "L09", "missing required reason_code")
            continue
        if reason not in DECISION_REASON_CODES:
            fx.error(
                row_label,
                "L10",
                f"reason_code {reason!r} not in decision_reason vocabulary",
            )
        try:
            parse_d5_candidate_sequence(cid)
        except LineageError as exc:
            fx.error(row_label, "L11", str(exc))
            continue
        if cid not in universe_ids:
            fx.error(row_label, "L12", f"unknown candidate_id {cid!r} not in candidates.csv")
        row_key = tuple(sorted((k, str(v)) for k, v in row.items()))
        if row_key in seen_disposition_rows:
            fx.error(row_label, "L13", f"duplicate disposition row for candidate_id {cid!r}")
        seen_disposition_rows.add(row_key)
        if cid in disposition_ids:
            fx.error(row_label, "L13", f"duplicate disposition row for candidate_id {cid!r}")
        disposition_ids.add(cid)

    overlap = episode_ids & disposition_ids
    for cid in sorted(overlap):
        fx.error(where, "L14", f"candidate_id {cid!r} appears in both episode and disposition ledgers")

    unaccounted = universe_ids - episode_ids - disposition_ids
    for cid in sorted(unaccounted):
        fx.error(where, "L15", f"unaccounted candidate_id {cid!r} in frozen universe")

    extra_episode = episode_ids - universe_ids
    for cid in sorted(extra_episode):
        fx.error(where, "L07", f"episode references unknown candidate_id {cid!r}")

    extra_disposition = disposition_ids - universe_ids
    for cid in sorted(extra_disposition):
        fx.error(where, "L12", f"disposition references unknown candidate_id {cid!r}")

    return fx
