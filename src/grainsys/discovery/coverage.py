"""Source-coverage metadata and sweep-execution axis (N2).

Two axes are kept distinct:

* ``coverage_status`` — whether an archive/source exists (present|absent|unknown)
* ``sweep_status`` — whether a registered sweep was run on that present source

Archive history bounds (``earliest_available`` / ``latest_available``) are NOT
sweep-scope intervals. Enumeration scope uses ``scope_start`` / ``scope_end``.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass
from typing import Any

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
# present = covered / archive reachable; absent = unavailable; unknown = not yet verified.

ALLOWED_SWEEP_STATUS = frozenset({"not_attempted", "attempted_failed", "enumerated"})


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


class CoverageValidationError(ValueError):
    """Invalid or contaminated coverage / sweep-execution metadata."""


def validate_coverage_record(data: Mapping[str, Any]) -> CoverageRecord:
    """Validate coverage + sweep-execution mapping; reject event/market fields."""
    forbidden = FORBIDDEN_COVERAGE_FIELDS.intersection(data.keys())
    if forbidden:
        raise CoverageValidationError(
            f"Coverage record must not contain event/market fields: {sorted(forbidden)}"
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

    for field in ("authority", "district", "vehicle"):
        if data.get(field) in (None, ""):
            raise CoverageValidationError(
                f"coverage record requires {field} even when coverage_status=absent"
            )

    if coverage_status == "present" and data.get("endpoint") in (None, ""):
        raise CoverageValidationError(
            "coverage_status=present requires a non-empty endpoint"
        )

    if data.get("retrieved_on") in (None, ""):
        raise CoverageValidationError("retrieved_on is required for every coverage row")

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
        if data.get("scope_start") in (None, "") or data.get("scope_end") in (None, ""):
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
        source_family=data.get("source_family"),
        authority=data.get("authority"),
        district=data.get("district"),
        vehicle=data.get("vehicle"),
        endpoint=data.get("endpoint"),
        earliest_available=data.get("earliest_available"),
        latest_available=data.get("latest_available"),
        retrieved_on=data.get("retrieved_on"),
        coverage_status=coverage_status,
        sweep_status=sweep_status,
        records_matched=records_matched,
        scope_start=data.get("scope_start"),
        scope_end=data.get("scope_end"),
        notes=data.get("notes"),
        schema_version=str(data.get("schema_version", "0.2")),
        record_kind=str(data.get("record_kind", "source_coverage")),
    )
