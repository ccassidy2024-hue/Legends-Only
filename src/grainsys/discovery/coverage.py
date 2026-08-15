"""Source-coverage metadata and sweep-execution axis (N2).

Two axes are kept distinct:

* ``coverage_status`` — whether an archive/source exists (present|absent|unknown)
* ``sweep_status`` — whether a registered sweep was run on that present source

Archive history bounds (``earliest_available`` / ``latest_available``) are NOT
sweep-scope intervals. Enumeration scope uses ``scope_start`` / ``scope_end``.

P5 / R-013 (ADR-0005): for absence-generating families, covered exposure =
union(enumerated scopes) minus union(known-gap intervals). Known gaps are
explicit absent/unknown rows with both scope bounds — never prose in ``notes``.
Unknown / failed / not-attempted rows never silently become swept-zero.
Supplementary families never generate absence exposure / swept-zero intervals.
Covered intervals are clipped to the registered D1 sample period. Per-event-class
coverage masks are not yet a mechanical input (future obligation; see
``compute_covered_exposure``).
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from datetime import date, datetime, timedelta
from typing import Any

from grainsys.discovery.config import (
    ALLOWED_SOURCE_IDENTITY_KEYS,
    PROTOCOL_SWEEP_FAMILIES,
)

FORBIDDEN_COVERAGE_FIELDS = frozenset(
    {
        "event_name",
        "episode_id",
        "candidate_id",
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
        "notice_title",
        "notice_body",
        "quote",
    }
)

ALLOWED_COVERAGE_STATUS = frozenset({"present", "absent", "unknown"})
ALLOWED_SWEEP_STATUS = frozenset({"not_attempted", "attempted_failed", "enumerated"})
ALLOWED_IDENTITY_KEYS = ALLOWED_SOURCE_IDENTITY_KEYS
ALLOWED_COVERAGE_RECORD_KEYS = frozenset(
    {
        "schema_version",
        "record_kind",
        "source_family",
        "authority",
        "district",
        "vehicle",
        "endpoint",
        "earliest_available",
        "latest_available",
        "retrieved_on",
        "coverage_status",
        "sweep_status",
        "records_matched",
        "scope_start",
        "scope_end",
        "notes",
    }
)

_ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


@dataclass(frozen=True)
class CoverageRecord:
    """Coverage census + optional sweep-execution row — no event content."""

    source_family: str | None
    authority: str | None
    district: str | None
    vehicle: str | None
    endpoint: str | None
    earliest_available: str | None
    latest_available: str | None
    retrieved_on: str | None
    coverage_status: str
    sweep_status: str
    records_matched: int | None = None
    scope_start: str | None = None
    scope_end: str | None = None
    notes: str | None = None
    schema_version: str = "0.2"
    record_kind: str = "source_coverage"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DateInterval:
    """Inclusive calendar-day interval."""

    start: date
    end: date

    def overlaps(self, other: DateInterval) -> bool:
        return self.start <= other.end and other.start <= self.end

    def adjacent_or_overlaps(self, other: DateInterval) -> bool:
        if self.overlaps(other):
            return True
        return (
            self.end + timedelta(days=1) == other.start
            or other.end + timedelta(days=1) == self.start
        )

    def to_pair(self) -> tuple[str, str]:
        return (self.start.isoformat(), self.end.isoformat())


@dataclass(frozen=True)
class CoveredExposure:
    """Net covered exposure for one explicit source-identity group (P5 / R-013).

    Supplementary / non-absence-generating groups always have ``intervals=()``.
    ``has_enumeration`` remains available as audit metadata only.
    """

    source_key: tuple[Any, ...]
    intervals: tuple[DateInterval, ...]
    has_enumeration: bool
    is_absence_generating: bool
    all_enumerated_records_matched_zero: bool

    @property
    def is_swept_zero_eligible(self) -> bool:
        return (
            self.is_absence_generating
            and self.has_enumeration
            and len(self.intervals) > 0
            and self.all_enumerated_records_matched_zero
        )


class CoverageValidationError(ValueError):
    """Invalid or contaminated coverage / sweep-execution metadata."""


def _require_nonempty_str(value: Any, *, field: str) -> str:
    if not isinstance(value, str):
        raise CoverageValidationError(
            f"{field} must be a nonempty string (got {type(value).__name__})"
        )
    if not value.strip():
        raise CoverageValidationError(f"{field} must be a nonempty string")
    return value.strip()


def parse_coverage_iso_date(value: Any, *, field: str) -> date:
    text = _require_nonempty_str(value, field=field)
    if not _ISO_DATE_RE.fullmatch(text):
        raise CoverageValidationError(
            f"{field}={text!r} must be strict ISO calendar date YYYY-MM-DD"
        )
    try:
        return datetime.strptime(text, "%Y-%m-%d").date()
    except ValueError as exc:
        raise CoverageValidationError(
            f"{field}={text!r} is not a valid calendar date"
        ) from exc


def _optional_scope_interval(data: Mapping[str, Any], *, where: str) -> DateInterval | None:
    start_raw = data.get("scope_start")
    end_raw = data.get("scope_end")
    start_missing = start_raw in (None, "")
    end_missing = end_raw in (None, "")
    if start_missing and end_missing:
        return None
    if start_missing or end_missing:
        raise CoverageValidationError(
            f"{where}: scope_start and scope_end must both be set when either is "
            "present (refuse partial gap/scope bounds)"
        )
    start = parse_coverage_iso_date(start_raw, field=f"{where}.scope_start")
    end = parse_coverage_iso_date(end_raw, field=f"{where}.scope_end")
    if start > end:
        raise CoverageValidationError(
            f"{where}: scope_start ({start.isoformat()}) must be <= "
            f"scope_end ({end.isoformat()})"
        )
    return DateInterval(start=start, end=end)


def _validate_identity_value(key: str, value: Any, *, where: str) -> Any:
    """Identity values: nonempty str, or None only for endpoint."""
    if value is None:
        if key == "endpoint":
            return None
        raise CoverageValidationError(
            f"{where}: identity key {key!r} may not be null "
            "(only endpoint may be null)"
        )
    if isinstance(value, bool) or isinstance(value, (int, float)) or isinstance(
        value, (list, dict)
    ):
        raise CoverageValidationError(
            f"{where}: identity key {key!r} must be nonempty string or None "
            f"(got {type(value).__name__})"
        )
    if not isinstance(value, str) or not value.strip():
        raise CoverageValidationError(
            f"{where}: identity key {key!r} must be nonempty string or None"
        )
    return value.strip()


def _parse_absence_generating_families(
    families: Sequence[Any] | set[Any] | frozenset[Any],
) -> frozenset[str]:
    if not isinstance(families, (set, frozenset, list, tuple)):
        raise CoverageValidationError(
            "absence_generating_families must be an explicit set/sequence"
        )
    if len(families) == 0:
        raise CoverageValidationError(
            "absence_generating_families must be nonempty"
        )
    out: list[str] = []
    seen: set[str] = set()
    for i, item in enumerate(families):
        if not isinstance(item, str):
            raise CoverageValidationError(
                f"absence_generating_families[{i}] must be an actual nonempty string "
                f"(got {type(item).__name__}); refuse coercion"
            )
        text = item.strip()
        if not text:
            raise CoverageValidationError(
                f"absence_generating_families[{i}] must be nonempty"
            )
        if text not in PROTOCOL_SWEEP_FAMILIES:
            raise CoverageValidationError(
                f"absence_generating_families[{i}]={text!r} must be one of "
                f"{sorted(PROTOCOL_SWEEP_FAMILIES)}"
            )
        if text in seen:
            raise CoverageValidationError(
                f"absence_generating_families contains duplicate {text!r}"
            )
        seen.add(text)
        out.append(text)
    return frozenset(out)


def _parse_source_identity_keys(keys: Sequence[Any]) -> tuple[str, ...]:
    if not isinstance(keys, (list, tuple)) or len(keys) == 0:
        raise CoverageValidationError(
            "source_identity_keys must be a nonempty sequence"
        )
    out: list[str] = []
    seen: set[str] = set()
    for i, item in enumerate(keys):
        if not isinstance(item, str) or not item.strip():
            raise CoverageValidationError(
                f"source_identity_keys[{i}] must be an actual nonempty string"
            )
        key = item.strip()
        if key not in ALLOWED_IDENTITY_KEYS:
            raise CoverageValidationError(
                f"source_identity_keys[{i}]={key!r} not in allowed identity keys "
                f"{sorted(ALLOWED_IDENTITY_KEYS)}"
            )
        if key in seen:
            raise CoverageValidationError(
                f"source_identity_keys contains duplicate {key!r}"
            )
        seen.add(key)
        out.append(key)
    return tuple(out)


def validate_coverage_record(data: Mapping[str, Any]) -> CoverageRecord:
    """Validate coverage + sweep-execution mapping; reject unknown/forbidden keys."""
    forbidden = FORBIDDEN_COVERAGE_FIELDS.intersection(data.keys())
    if forbidden:
        raise CoverageValidationError(
            f"Coverage record must not contain event/market fields: {sorted(forbidden)}"
        )
    unknown = sorted(set(data.keys()) - ALLOWED_COVERAGE_RECORD_KEYS)
    if unknown:
        raise CoverageValidationError(
            f"Coverage record has unknown keys {unknown}; refuse silent discard"
        )

    coverage_status = data.get("coverage_status")
    if coverage_status not in ALLOWED_COVERAGE_STATUS:
        raise CoverageValidationError(
            "coverage_status must be one of present|absent|unknown "
            f"(got {coverage_status!r}); missing coverage must be explicit."
        )

    sweep_status = data.get("sweep_status")
    if sweep_status not in ALLOWED_SWEEP_STATUS:
        raise CoverageValidationError(
            "sweep_status must be one of not_attempted|attempted_failed|enumerated "
            f"(got {sweep_status!r}); refuse silent default."
        )

    authority = _require_nonempty_str(data.get("authority"), field="authority")
    district = _require_nonempty_str(data.get("district"), field="district")
    vehicle = _require_nonempty_str(data.get("vehicle"), field="vehicle")

    endpoint_raw = data.get("endpoint")
    if coverage_status == "present":
        endpoint = _require_nonempty_str(endpoint_raw, field="endpoint")
    elif endpoint_raw is None:
        endpoint = None
    else:
        endpoint = _require_nonempty_str(endpoint_raw, field="endpoint")

    source_family_raw = data.get("source_family")
    if source_family_raw is None:
        source_family = None
    else:
        source_family = _require_nonempty_str(source_family_raw, field="source_family")
        if source_family not in PROTOCOL_SWEEP_FAMILIES:
            raise CoverageValidationError(
                f"source_family={source_family!r} must be one of "
                f"{sorted(PROTOCOL_SWEEP_FAMILIES)}"
            )

    retrieved_on_s = _require_nonempty_str(data.get("retrieved_on"), field="retrieved_on")
    parse_coverage_iso_date(retrieved_on_s, field="retrieved_on")

    earliest = data.get("earliest_available")
    latest = data.get("latest_available")
    earliest_d = None
    latest_d = None
    if earliest not in (None, ""):
        earliest_d = parse_coverage_iso_date(earliest, field="earliest_available")
    if latest not in (None, ""):
        latest_d = parse_coverage_iso_date(latest, field="latest_available")
    if earliest_d is not None and latest_d is not None and earliest_d > latest_d:
        raise CoverageValidationError(
            "earliest_available must be <= latest_available when both are set"
        )

    records_matched = data.get("records_matched", None)
    if records_matched is not None:
        if not isinstance(records_matched, int) or isinstance(records_matched, bool):
            raise CoverageValidationError("records_matched must be int | null")
        if records_matched < 0:
            raise CoverageValidationError("records_matched must be >= 0")

    if sweep_status != "enumerated" and records_matched is not None:
        raise CoverageValidationError(
            "records_matched MUST be null unless sweep_status == enumerated"
        )

    scope = _optional_scope_interval(data, where="coverage_record")

    if sweep_status == "enumerated":
        if coverage_status != "present":
            raise CoverageValidationError(
                "enumerated requires coverage_status == present "
                f"(got coverage_status={coverage_status!r})"
            )
        if records_matched is None:
            raise CoverageValidationError(
                "enumerated requires records_matched (use 0 for genuine swept-zero)"
            )
        if scope is None:
            raise CoverageValidationError(
                "enumerated requires explicit scope_start and scope_end "
                "(do not reuse earliest_available/latest_available as sweep scope)"
            )

    if sweep_status == "attempted_failed" and coverage_status != "present":
        raise CoverageValidationError(
            "attempted_failed requires coverage_status == present"
        )

    if coverage_status in {"absent", "unknown"} and sweep_status == "enumerated":
        raise CoverageValidationError(
            f"coverage_status={coverage_status!r} cannot be enumerated"
        )

    return CoverageRecord(
        source_family=source_family,
        authority=authority,
        district=district,
        vehicle=vehicle,
        endpoint=endpoint,
        earliest_available=earliest if earliest not in (None, "") else None,
        latest_available=latest if latest not in (None, "") else None,
        retrieved_on=retrieved_on_s,
        coverage_status=coverage_status,
        sweep_status=sweep_status,
        records_matched=records_matched,
        scope_start=data.get("scope_start"),
        scope_end=data.get("scope_end"),
        notes=data.get("notes"),
        schema_version=str(data.get("schema_version", "0.2")),
        record_kind=str(data.get("record_kind", "source_coverage")),
    )


def _merge_intervals(intervals: Sequence[DateInterval]) -> tuple[DateInterval, ...]:
    if not intervals:
        return ()
    ordered = sorted(intervals, key=lambda iv: (iv.start, iv.end))
    merged: list[DateInterval] = [ordered[0]]
    for iv in ordered[1:]:
        cur = merged[-1]
        if cur.adjacent_or_overlaps(iv):
            merged[-1] = DateInterval(cur.start, max(cur.end, iv.end))
        else:
            merged.append(iv)
    return tuple(merged)


def _subtract_intervals(
    bases: Sequence[DateInterval],
    gaps: Sequence[DateInterval],
) -> tuple[DateInterval, ...]:
    current: list[DateInterval] = list(_merge_intervals(bases))
    for gap in _merge_intervals(gaps):
        next_round: list[DateInterval] = []
        for base in current:
            if not base.overlaps(gap):
                next_round.append(base)
                continue
            if base.start < gap.start:
                left_end = gap.start - timedelta(days=1)
                if base.start <= left_end:
                    next_round.append(DateInterval(base.start, left_end))
            if base.end > gap.end:
                right_start = gap.end + timedelta(days=1)
                if right_start <= base.end:
                    next_round.append(DateInterval(right_start, base.end))
        current = next_round
    return _merge_intervals(current)


def _clip_to_sample(
    intervals: Sequence[DateInterval],
    window: DateInterval,
) -> tuple[DateInterval, ...]:
    clipped: list[DateInterval] = []
    for iv in intervals:
        start = max(iv.start, window.start)
        end = min(iv.end, window.end)
        if start <= end:
            clipped.append(DateInterval(start, end))
    return _merge_intervals(clipped)


def compute_covered_exposure(
    rows: Sequence[Mapping[str, Any]],
    *,
    absence_generating_families: Sequence[Any] | set[Any] | frozenset[Any],
    source_identity_keys: Sequence[Any],
    sample_start: Any,
    sample_end: Any,
) -> list[CoveredExposure]:
    """Compute P5 covered exposure from validated synthetic/coverage rows.

    Every row must carry an explicit nonempty ``source_family`` in S1–S8.
    Family is never inferred from peer rows. Supplementary families always
    return ``intervals=()``.

    Net intervals are clipped to the registered D1 ``sample_start`` /
    ``sample_end`` window. Per-event-class coverage masks (ADR-0003 D1
    architecture item 2) are **not** a mechanical input here. Future
    obligation: when class masks are registered, intersect net exposure with
    the applicable class mask. Until then this function must not be described
    as applying event-class masks.
    """
    absence_set = _parse_absence_generating_families(absence_generating_families)
    identity_keys = _parse_source_identity_keys(source_identity_keys)
    window_start = parse_coverage_iso_date(sample_start, field="sample_start")
    window_end = parse_coverage_iso_date(sample_end, field="sample_end")
    if window_start > window_end:
        raise CoverageValidationError(
            f"sample_start ({window_start.isoformat()}) must be <= "
            f"sample_end ({window_end.isoformat()})"
        )
    sample_window = DateInterval(start=window_start, end=window_end)

    grouped: dict[tuple[Any, ...], list[CoverageRecord]] = {}
    for i, raw in enumerate(rows):
        if not isinstance(raw, Mapping):
            raise CoverageValidationError(f"rows[{i}] must be a mapping")
        # Exposure computation cannot infer missing family from group peers.
        family = raw.get("source_family")
        if family is None or (isinstance(family, str) and not family.strip()):
            raise CoverageValidationError(
                f"rows[{i}]: source_family is required for covered-exposure "
                "computation (actual nonempty S1–S8 string)"
            )
        family_s = _require_nonempty_str(family, field=f"rows[{i}].source_family")
        if family_s not in PROTOCOL_SWEEP_FAMILIES:
            raise CoverageValidationError(
                f"rows[{i}].source_family={family_s!r} must be one of "
                f"{sorted(PROTOCOL_SWEEP_FAMILIES)}"
            )

        key_vals: list[Any] = []
        for key in identity_keys:
            if key not in raw:
                raise CoverageValidationError(
                    f"rows[{i}]: identity key {key!r} missing from row; "
                    "refuse invented identity values"
                )
            key_vals.append(
                _validate_identity_value(key, raw[key], where=f"rows[{i}]")
            )
        key = tuple(key_vals)
        row = validate_coverage_record(raw)
        grouped.setdefault(key, []).append(row)

    results: list[CoveredExposure] = []
    for key, group in sorted(grouped.items(), key=lambda item: repr(item[0])):
        enumerated: list[DateInterval] = []
        enumerated_rows: list[CoverageRecord] = []
        gaps: list[DateInterval] = []
        whole_source_nonpresent = False
        families: set[str] = set()

        for row in group:
            if row.source_family is None:
                raise CoverageValidationError(
                    f"source {key!r}: source_family missing after validation"
                )
            families.add(row.source_family)
            scope = None
            if row.scope_start not in (None, "") or row.scope_end not in (None, ""):
                scope = _optional_scope_interval(row.to_dict(), where="coverage_record")

            if row.sweep_status == "enumerated":
                assert scope is not None
                enumerated.append(scope)
                enumerated_rows.append(row)
                continue

            if row.coverage_status in {"absent", "unknown"}:
                if scope is not None:
                    gaps.append(scope)
                else:
                    whole_source_nonpresent = True
                continue

        if whole_source_nonpresent and enumerated:
            raise CoverageValidationError(
                f"source {key!r}: whole-source absent/unknown cannot coexist with "
                "enumerated scopes; refuse contradictory coverage"
            )

        if len(families) != 1:
            raise CoverageValidationError(
                f"source {key!r}: mixed/missing source_family values "
                f"{sorted(families)}; refuse ambiguous classification"
            )
        family = next(iter(families))
        is_absence_generating = family in absence_set
        has_enumeration = len(enumerated) > 0

        if not has_enumeration:
            results.append(
                CoveredExposure(
                    source_key=key,
                    intervals=(),
                    has_enumeration=False,
                    is_absence_generating=is_absence_generating,
                    all_enumerated_records_matched_zero=False,
                )
            )
            continue

        all_zero = all(r.records_matched == 0 for r in enumerated_rows)
        if is_absence_generating:
            net = _clip_to_sample(_subtract_intervals(enumerated, gaps), sample_window)
        else:
            # Supplementary: never expose absence intervals / swept-zero denominators.
            net = ()
        results.append(
            CoveredExposure(
                source_key=key,
                intervals=net,
                has_enumeration=True,
                is_absence_generating=is_absence_generating,
                all_enumerated_records_matched_zero=all_zero,
            )
        )

    return results


def validate_coverage_collection(
    rows: Sequence[Mapping[str, Any]],
    *,
    absence_generating_families: Sequence[Any] | set[Any] | frozenset[Any],
    source_identity_keys: Sequence[Any],
    sample_start: Any,
    sample_end: Any,
) -> list[CoveredExposure]:
    """Validate each row and cross-row P5 exposure semantics; return exposure."""
    return compute_covered_exposure(
        rows,
        absence_generating_families=absence_generating_families,
        source_identity_keys=source_identity_keys,
        sample_start=sample_start,
        sample_end=sample_end,
    )
