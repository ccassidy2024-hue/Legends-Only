"""Source-independent in-memory archive listing → candidate-hit adapter.

Converts a caller-supplied synthetic listing into normalized candidate-hit rows.
No network I/O, URLs, publishers, districts, document bodies, keywords, or
market data are fetched or invented here. Ordering keys and optional stable-ID
inputs are explicit; input position never breaks ties.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Protocol

from grainsys.discovery.candidates import (
    FORBIDDEN_CANDIDATE_FIELDS,
    CandidateHit,
    mint_candidate_ids,
    validate_candidate_hit,
)
from grainsys.discovery.config import (
    PRE_MINT_CANDIDATE_FIELDS,
    PROTOCOL_SWEEP_FAMILIES,
    DiscoveryConfigError,
    parse_iso_calendar_date,
    require_nonempty_str,
    require_safe_path_component,
    validate_pre_mint_field_keys,
    validate_stable_id_key_name,
)


class ArchiveListingError(ValueError):
    """Synthetic archive listing cannot be normalized honestly."""


class ArchiveListingRow(Protocol):
    """Minimal structural protocol for a caller-supplied listing row."""

    def get(self, key: str, default: Any = None) -> Any: ...


REQUIRED_LISTING_FIELDS: tuple[str, ...] = ("source_reference",)


def _require_non_empty_str(value: Any, *, field: str) -> str:
    try:
        return require_nonempty_str(value, field=field)
    except DiscoveryConfigError as exc:
        raise ArchiveListingError(str(exc)) from exc


def _optional_text(value: Any, *, field: str) -> str | None:
    if value is None:
        return None
    return _require_non_empty_str(value, field=field)


def _optional_iso_date(value: Any, *, field: str) -> str | None:
    text = _optional_text(value, field=field)
    if text is None:
        return None
    try:
        return parse_iso_calendar_date(text, field=field).isoformat()
    except DiscoveryConfigError as exc:
        raise ArchiveListingError(str(exc)) from exc


def _require_sequence_of_mappings(value: Any, *, field: str) -> Sequence[Mapping[str, Any]]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise ArchiveListingError(
            f"{field} must be a sequence of mappings "
            f"(got {type(value).__name__})"
        )
    return value


def _validate_ordering_keys(ordering_keys: Any) -> list[str]:
    if isinstance(ordering_keys, (str, bytes)) or not isinstance(
        ordering_keys, (list, tuple)
    ):
        raise ArchiveListingError(
            f"ordering_keys must be a list/tuple of strings "
            f"(got {type(ordering_keys).__name__})"
        )
    try:
        return validate_pre_mint_field_keys(
            list(ordering_keys),
            field="ordering_keys",
        )
    except DiscoveryConfigError as exc:
        raise ArchiveListingError(str(exc)) from exc


def _validate_stable_id_key(stable_id_key: Any) -> str | None:
    if stable_id_key is None:
        return None
    try:
        return validate_stable_id_key_name(stable_id_key, field="stable_id_key")
    except DiscoveryConfigError as exc:
        raise ArchiveListingError(str(exc)) from exc


def _bound_registered_context(
    row: Mapping[str, Any],
    *,
    key: str,
    context: str | None,
    index: int,
) -> str | None:
    """Registered authority/district/vehicle/endpoint may not be overridden."""
    if key not in row:
        return context
    raw = _optional_text(row.get(key), field=f"listings[{index}].{key}")
    if context is not None and raw != context:
        raise ArchiveListingError(
            f"listings[{index}].{key}={raw!r} conflicts with registered "
            f"context {context!r}; refuse override"
        )
    if context is not None:
        return context
    return raw


def _reject_unknown_raw_fields(
    row: Mapping[str, Any],
    *,
    index: int,
    stable_key: str | None,
) -> None:
    allowed = set(PRE_MINT_CANDIDATE_FIELDS)
    if stable_key is not None:
        allowed.add(stable_key)
    unknown = sorted(set(row.keys()) - allowed)
    if unknown:
        forbidden = sorted(set(unknown) & FORBIDDEN_CANDIDATE_FIELDS)
        raise ArchiveListingError(
            f"listings[{index}] has unknown/contamination raw fields {unknown}"
            + (f" (forbidden {forbidden})" if forbidden else "")
            + "; refuse silent discard"
        )


def normalize_archive_listing(
    listings: Sequence[Mapping[str, Any]],
    *,
    sweep_id: str,
    ordering_keys: Sequence[Any],
    stable_id_key: str | None = None,
    authority: str | None = None,
    district: str | None = None,
    vehicle: str | None = None,
    endpoint: str | None = None,
    retrieved_on: str | None = None,
) -> list[dict[str, Any]]:
    """Pure normalizer: listing rows → candidate-shaped dicts (no IDs minted).

    Ordering keys are validated as unique nonempty pre-mint fields before any
    row is read. Optional ``stable_id_key`` is a source-native raw field name;
    its value is copied **only** into ``stable_source_id`` (never overwrites
    sweep_id or other metadata fields).
    """
    rows = _require_sequence_of_mappings(listings, field="listings")
    sid = _require_non_empty_str(sweep_id, field="sweep_id")
    if sid not in PROTOCOL_SWEEP_FAMILIES:
        raise ArchiveListingError(
            f"sweep_id={sid!r} must be one of protocol families "
            f"{sorted(PROTOCOL_SWEEP_FAMILIES)}"
        )
    keys = _validate_ordering_keys(ordering_keys)
    stable_key = _validate_stable_id_key(stable_id_key)

    ctx_authority = _optional_text(authority, field="authority")
    ctx_district = _optional_text(district, field="district")
    ctx_vehicle = _optional_text(vehicle, field="vehicle")
    ctx_endpoint = _optional_text(endpoint, field="endpoint")
    ctx_retrieved = _optional_text(retrieved_on, field="retrieved_on")

    working: list[dict[str, Any]] = []
    for i, row in enumerate(rows):
        if not isinstance(row, Mapping):
            raise ArchiveListingError(f"listings[{i}] must be a mapping")
        source_reference = _require_non_empty_str(
            row.get("source_reference"),
            field=f"listings[{i}].source_reference",
        )
        _reject_unknown_raw_fields(row, index=i, stable_key=stable_key)
        if "sweep_id" in row:
            row_sid = _require_non_empty_str(
                row.get("sweep_id"), field=f"listings[{i}].sweep_id"
            )
            if row_sid != sid:
                raise ArchiveListingError(
                    f"listings[{i}].sweep_id={row_sid!r} conflicts with "
                    f"registered sweep_id {sid!r}; refuse override"
                )
        for key in keys:
            if key not in row:
                raise ArchiveListingError(
                    f"listings[{i}] missing ordering key {key!r}; "
                    "refuse positional fallback"
                )

        normalized: dict[str, Any] = {
            "sweep_id": sid,
            "source_reference": source_reference,
            "document_date": _optional_iso_date(
                row.get("document_date"), field=f"listings[{i}].document_date"
            ),
            "raw_capture_pointer": _optional_text(
                row.get("raw_capture_pointer"),
                field=f"listings[{i}].raw_capture_pointer",
            ),
            "notes": _optional_text(row.get("notes"), field=f"listings[{i}].notes"),
            "authority": _bound_registered_context(
                row, key="authority", context=ctx_authority, index=i
            ),
            "district": _bound_registered_context(
                row, key="district", context=ctx_district, index=i
            ),
            "vehicle": _bound_registered_context(
                row, key="vehicle", context=ctx_vehicle, index=i
            ),
            "endpoint": _bound_registered_context(
                row, key="endpoint", context=ctx_endpoint, index=i
            ),
            "retrieved_on": _optional_text(
                row["retrieved_on"] if "retrieved_on" in row else ctx_retrieved,
                field=f"listings[{i}].retrieved_on",
            ),
        }
        # Ensure validated ordering keys are present with str-or-null discipline.
        for key in keys:
            if key in {"sweep_id", "source_reference"}:
                continue
            if key in normalized:
                if key in row:
                    normalized[key] = _optional_text(
                        row.get(key), field=f"listings[{i}].{key}"
                    )
                continue
            normalized[key] = _optional_text(
                row.get(key), field=f"listings[{i}].{key}"
            )

        if stable_key is not None:
            if stable_key not in row:
                raise ArchiveListingError(
                    f"listings[{i}] missing explicit stable_id_key "
                    f"{stable_key!r}; refuse invented source ids"
                )
            sid_val = _require_non_empty_str(
                row.get(stable_key),
                field=f"listings[{i}].{stable_key}",
            )
            # Copy into stable_source_id only — never overwrite sweep_id/metadata.
            normalized["stable_source_id"] = sid_val
        working.append(normalized)
    return working


def normalize_and_mint_archive_listing(
    listings: Sequence[Mapping[str, Any]],
    *,
    sweep_id: str,
    ordering_keys: Sequence[Any],
    id_prefix: str,
    stable_id_key: str | None = None,
    authority: str | None = None,
    district: str | None = None,
    vehicle: str | None = None,
    endpoint: str | None = None,
    retrieved_on: str | None = None,
) -> list[CandidateHit]:
    """Compose pure normalize + deterministic mint into validated candidate hits.

    Dedup uses ``stable_source_id`` after the normalizer copies any configured
    source-native stable_id_key value into that field.
    """
    try:
        prefix = require_safe_path_component(id_prefix, field="id_prefix")
    except DiscoveryConfigError as exc:
        raise ArchiveListingError(str(exc)) from exc
    keys = _validate_ordering_keys(ordering_keys)
    stable_key = _validate_stable_id_key(stable_id_key)
    working = normalize_archive_listing(
        listings,
        sweep_id=sweep_id,
        ordering_keys=keys,
        stable_id_key=stable_key,
        authority=authority,
        district=district,
        vehicle=vehicle,
        endpoint=endpoint,
        retrieved_on=retrieved_on,
    )
    minted = mint_candidate_ids(
        working,
        ordering_keys=keys,
        id_prefix=prefix,
        stable_id_key="stable_source_id" if stable_key is not None else None,
    )
    return [validate_candidate_hit(row) for row in minted]
