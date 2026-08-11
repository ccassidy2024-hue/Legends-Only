"""Source-coverage metadata: archive existence / date ranges only."""

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


@dataclass(frozen=True)
class CoverageRecord:
    """Coverage census row — no event content."""

    source_family: str | None
    authority: str | None
    district: str | None
    vehicle: str | None
    endpoint: str | None
    earliest_available: str | None
    latest_available: str | None
    retrieved_on: str | None
    coverage_status: str
    notes: str | None = None
    schema_version: str = "0.1"
    record_kind: str = "source_coverage"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class CoverageValidationError(ValueError):
    """Invalid or contaminated coverage metadata."""


def validate_coverage_record(data: Mapping[str, Any]) -> CoverageRecord:
    """Validate a coverage mapping; reject event/market fields."""
    forbidden = FORBIDDEN_COVERAGE_FIELDS.intersection(data.keys())
    if forbidden:
        raise CoverageValidationError(
            f"Coverage record must not contain event/market fields: {sorted(forbidden)}"
        )

    status = data.get("coverage_status")
    if status not in ALLOWED_COVERAGE_STATUS:
        raise CoverageValidationError(
            "coverage_status must be one of present|absent|unknown "
            f"(got {status!r}); missing coverage must be explicit."
        )

    # Absent rows still need identity fields so a silent gap is impossible.
    for field in ("authority", "district", "vehicle"):
        if data.get(field) in (None, ""):
            raise CoverageValidationError(
                f"coverage record requires {field} even when coverage_status=absent"
            )

    if status == "present" and data.get("endpoint") in (None, ""):
        raise CoverageValidationError(
            "coverage_status=present requires a non-empty endpoint"
        )

    if data.get("retrieved_on") in (None, ""):
        raise CoverageValidationError("retrieved_on is required for every coverage row")

    return CoverageRecord(
        source_family=data.get("source_family"),
        authority=data.get("authority"),
        district=data.get("district"),
        vehicle=data.get("vehicle"),
        endpoint=data.get("endpoint"),
        earliest_available=data.get("earliest_available"),
        latest_available=data.get("latest_available"),
        retrieved_on=data.get("retrieved_on"),
        coverage_status=status,
        notes=data.get("notes"),
        schema_version=str(data.get("schema_version", "0.1")),
        record_kind=str(data.get("record_kind", "source_coverage")),
    )
