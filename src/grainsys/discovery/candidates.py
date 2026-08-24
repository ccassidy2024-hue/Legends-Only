"""Candidate-hit schema and deterministic ID minting (N1)."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from typing import Any

FORBIDDEN_CANDIDATE_FIELDS = frozenset(
    {
        "episode_id",
        "event_name",
        "market_outcomes_reviewed",
        "market_outcome",
        "price",
        "futures",
        "basis",
        "freight_rate",
        "severity_class",
        "public_anchor",
        "decision",
        "accept",
        "reject",
    }
)


@dataclass(frozen=True)
class CandidateHit:
    """One Phase 1 hit after a registered sweep (scaffolding; no live rows here)."""

    candidate_id: str
    sweep_id: str
    source_reference: str
    raw_capture_pointer: str | None
    document_date: str | None
    ordering_key: str
    authority: str | None = None
    district: str | None = None
    vehicle: str | None = None
    endpoint: str | None = None
    retrieved_on: str | None = None
    notes: str | None = None
    stable_source_id: str | None = None
    full_text: str | None = None  # D3/D4: local normalized extracted linked-document text

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class CandidateValidationError(ValueError):
    """Invalid or contaminated candidate-hit payload."""


class CandidateIdError(ValueError):
    """Ordering / minting / dedup rule incomplete or violated."""


def validate_candidate_hit(data: Mapping[str, Any]) -> CandidateHit:
    forbidden = FORBIDDEN_CANDIDATE_FIELDS.intersection(data.keys())
    if forbidden:
        raise CandidateValidationError(
            f"Candidate hit must not contain episode/market fields: {sorted(forbidden)}"
        )

    required = (
        "candidate_id",
        "sweep_id",
        "source_reference",
        "ordering_key",
    )
    for field in required:
        if data.get(field) in (None, ""):
            raise CandidateValidationError(f"candidate hit missing required field: {field}")

    return CandidateHit(
        candidate_id=str(data["candidate_id"]),
        sweep_id=str(data["sweep_id"]),
        source_reference=str(data["source_reference"]),
        raw_capture_pointer=data.get("raw_capture_pointer"),
        document_date=data.get("document_date"),
        ordering_key=str(data["ordering_key"]),
        authority=data.get("authority"),
        district=data.get("district"),
        vehicle=data.get("vehicle"),
        endpoint=data.get("endpoint"),
        retrieved_on=data.get("retrieved_on"),
        notes=data.get("notes"),
        stable_source_id=data.get("stable_source_id"),
        full_text=data.get("full_text"),
    )


def _ordering_tuple(row: Mapping[str, Any], ordering_keys: Sequence[str]) -> tuple[str, ...]:
    values: list[str] = []
    for key in ordering_keys:
        if key not in row:
            raise CandidateIdError(
                f"ordering key {key!r} missing from hit row; "
                "refusing to invent a default sort."
            )
        values.append("" if row[key] is None else str(row[key]))
    return tuple(values)


def _canonical_row(row: Mapping[str, Any]) -> tuple[tuple[str, str], ...]:
    """Stable comparable form of sweep-relevant metadata (all provided keys)."""
    items: list[tuple[str, str]] = []
    for key in sorted(row.keys()):
        val = row[key]
        items.append((key, "" if val is None else str(val)))
    return tuple(items)


def _dedupe_stable_source_ids(
    hits: Sequence[Mapping[str, Any]],
    *,
    stable_id_key: str,
) -> list[dict[str, Any]]:
    """Collapse exact duplicate representations of the same source-native ID.

    Distinct records must not share a stable ID with conflicting metadata.
    Rows lacking the key (or with empty id) are left untouched — no invented IDs.
    """
    groups: dict[str, list[dict[str, Any]]] = {}
    passthrough: list[dict[str, Any]] = []
    for row in hits:
        raw = row.get(stable_id_key) if stable_id_key in row else None
        if raw in (None, ""):
            passthrough.append(dict(row))
            continue
        sid = str(raw)
        groups.setdefault(sid, []).append(dict(row))

    out: list[dict[str, Any]] = []
    for sid, rows in groups.items():
        canon = _canonical_row(rows[0])
        for other in rows[1:]:
            if _canonical_row(other) != canon:
                raise CandidateIdError(
                    f"conflicting representations for {stable_id_key}={sid!r}; "
                    "refuse silent merge of distinct records."
                )
        out.append(rows[0])
    out.extend(passthrough)
    return out


def mint_candidate_ids(
    hits: Sequence[Mapping[str, Any]],
    *,
    ordering_keys: Sequence[str],
    id_prefix: str,
    stable_id_key: str | None = None,
) -> list[dict[str, Any]]:
    """Assign deterministic candidate_ids under an explicit ordering rule.

    Ordering is determined **only** by ``ordering_keys``. Duplicate ordering
    tuples raise ``CandidateIdError`` — input position never breaks ties.

    Optional ``stable_id_key`` enables source-native deduplication before minting
    when the source provides an ID. No ID is invented when the key is absent.
    """
    if not ordering_keys:
        raise CandidateIdError(
            "ordering_keys must be a non-empty sequence (D5); no silent default."
        )
    if not id_prefix:
        raise CandidateIdError("id_prefix is required (D5); no silent default.")

    for i, row in enumerate(hits):
        forbidden = FORBIDDEN_CANDIDATE_FIELDS.intersection(row.keys())
        if forbidden:
            raise CandidateValidationError(
                f"hits[{i}] contains forbidden fields: {sorted(forbidden)}"
            )

    working: list[dict[str, Any]] = [dict(r) for r in hits]
    if stable_id_key is not None:
        if not stable_id_key:
            raise CandidateIdError("stable_id_key must be a non-empty field name when set.")
        working = _dedupe_stable_source_ids(working, stable_id_key=stable_id_key)

    keyed: list[tuple[tuple[str, ...], dict[str, Any]]] = []
    seen: dict[tuple[str, ...], int] = {}
    for row in working:
        ot = _ordering_tuple(row, ordering_keys)
        if ot in seen:
            raise CandidateIdError(
                f"duplicate ordering tuple {ot!r} after stable-id dedup; "
                "input/enumeration position must not break ties (N1)."
            )
        seen[ot] = 1
        keyed.append((ot, row))

    keyed.sort(key=lambda item: item[0])

    out: list[dict[str, Any]] = []
    width = max(4, len(str(len(keyed))))
    for seq, (ot, row) in enumerate(keyed, start=1):
        minted = dict(row)
        minted["candidate_id"] = f"{id_prefix}-{seq:0{width}d}"
        minted["ordering_key"] = "|".join(ot)
        out.append(minted)
    return out


def researcher_parity_for_candidate_id(candidate_id: str) -> str:
    """Map a minted candidate_id sequence to researcher parity (pure).

    Odd sequence numbers → ``"A"``; even sequence numbers → ``"B"``.
    Derives only from the numeric suffix of ``candidate_id``. Does not read
    config, filesystem, or clocks, and does not alter mint ordering.
    """
    if not isinstance(candidate_id, str) or not candidate_id.strip():
        raise CandidateIdError(
            f"candidate_id must be a nonempty string (got {candidate_id!r})"
        )
    if "-" not in candidate_id:
        raise CandidateIdError(
            f"candidate_id {candidate_id!r} lacks a '-' sequence separator"
        )
    _, _, seq_text = candidate_id.rpartition("-")
    if not seq_text.isdigit():
        raise CandidateIdError(
            f"candidate_id {candidate_id!r} has non-numeric sequence {seq_text!r}"
        )
    seq = int(seq_text, 10)
    if seq < 1:
        raise CandidateIdError(
            f"candidate_id {candidate_id!r} sequence must be >= 1 (got {seq})"
        )
    return "A" if (seq % 2 == 1) else "B"
