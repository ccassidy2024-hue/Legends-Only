"""Candidate-hit schema and deterministic ID minting."""

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

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class CandidateValidationError(ValueError):
    """Invalid or contaminated candidate-hit payload."""


class CandidateIdError(ValueError):
    """Ordering / minting rule incomplete."""


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


def mint_candidate_ids(
    hits: Sequence[Mapping[str, Any]],
    *,
    ordering_keys: Sequence[str],
    id_prefix: str,
) -> list[dict[str, Any]]:
    """Assign deterministic candidate_ids under an explicit ordering rule.

    ``ordering_keys`` and ``id_prefix`` must be supplied by the caller (from
    committed prereg config). This function does not choose a default rule.
    """
    if not ordering_keys:
        raise CandidateIdError(
            "ordering_keys must be a non-empty sequence (D5); no silent default."
        )
    if not id_prefix:
        raise CandidateIdError("id_prefix is required (D5); no silent default.")

    # Reject contamination fields on input rows before minting.
    for i, row in enumerate(hits):
        forbidden = FORBIDDEN_CANDIDATE_FIELDS.intersection(row.keys())
        if forbidden:
            raise CandidateValidationError(
                f"hits[{i}] contains forbidden fields: {sorted(forbidden)}"
            )

    indexed = list(enumerate(hits))
    indexed.sort(key=lambda item: (_ordering_tuple(item[1], ordering_keys), item[0]))

    out: list[dict[str, Any]] = []
    width = max(4, len(str(len(indexed))))
    for seq, (_orig_i, row) in enumerate(indexed, start=1):
        minted = dict(row)
        minted["candidate_id"] = f"{id_prefix}-{seq:0{width}d}"
        minted["ordering_key"] = "|".join(_ordering_tuple(row, ordering_keys))
        out.append(minted)
    return out
