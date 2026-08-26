"""Deterministic adapter for USACE Lock Performance Monitoring System.

This module implements S6 source enumeration per EPISODE_PROTOCOL.md §J:
"USACE LPMS - Outage/queue records exceeding pre-registered thresholds"

Under D8 mode=binding_operational_restriction_only, this adapter enumerates
documented lock closures and unavailability only. No physical threshold
breach detection is performed (that would require class_thresholds which
are empty under current D8 configuration).

Authority: U.S. Army Corps of Engineers
Data source: Corps Locks portal (https://ndc.ops.usace.army.mil/ords/r/lpms/corps-locks/)
Vehicle: Annual Lock Unavailability Reports
Sample period: 2010-01-01 to 2024-12-31 (D1 registered)
Archive coverage: 2016-2025 (UNKNOWN for 2010-2015)

This module performs no candidate minting, capture persistence, or
absence inference. Raw source bytes must be captured by the separately
governed D6 machinery before a caller uses normalized data in a live sweep.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import StrEnum

LPMS_AUTHORITY = "U.S. Army Corps of Engineers"
LPMS_VEHICLE = "Corps Locks Annual Lock Unavailability Report"
LPMS_PORTAL_BASE = "https://ndc.ops.usace.army.mil/ords/r/lpms/corps-locks"

LPMS_SAMPLE_START = date(2010, 1, 1)
LPMS_SAMPLE_END = date(2024, 12, 31)

LPMS_ARCHIVE_START_YEAR = 2016
LPMS_ARCHIVE_END_YEAR = 2025

D2_NAVIGATION_BASINS: tuple[str, ...] = (
    "lower_mississippi",
    "middle_mississippi",
    "upper_mississippi",
    "ohio",
    "illinois",
    "columbia_snake",
)


class LpmsNormalizationError(ValueError):
    """LPMS data or metadata do not satisfy the frozen contract."""


class LpmsReportType(StrEnum):
    """Available LPMS report types relevant to S6."""

    ANNUAL_UNAVAILABILITY = "annual_unavailability"
    ANNUAL_USAGE = "annual_usage"
    MONTHLY_TONNAGE = "monthly_tonnage"
    MONTHLY_KEY_LOCK = "monthly_key_lock"


class LpmsCoverageStatus(StrEnum):
    """Coverage status for LPMS archive by year."""

    COVERED = "COVERED"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class LpmsLockReference:
    """Reference for a single lock in the D2 waterborne corridor scope."""

    lock_id: str
    lock_name: str
    river: str
    navigation_basin: str
    river_mile: float | None

    def __post_init__(self) -> None:
        if not self.lock_id or not self.lock_id.strip():
            raise LpmsNormalizationError("lock_id must be nonempty")
        if not self.lock_name or not self.lock_name.strip():
            raise LpmsNormalizationError("lock_name must be nonempty")
        if self.navigation_basin not in D2_NAVIGATION_BASINS:
            raise LpmsNormalizationError(
                f"navigation_basin {self.navigation_basin!r} not in D2 scope"
            )


@dataclass(frozen=True)
class LpmsUnavailabilityRecord:
    """Single unavailability record from LPMS report.

    Under D8 binding_operational_restriction_only mode, this represents
    documented hours the lock was unavailable (closed/restricted).
    """

    lock_id: str
    year: int
    unavailable_hours: float
    scheduled_hours: float | None
    unscheduled_hours: float | None
    total_hours_year: float

    def __post_init__(self) -> None:
        if self.year < LPMS_ARCHIVE_START_YEAR or self.year > LPMS_ARCHIVE_END_YEAR:
            raise LpmsNormalizationError(
                f"year {self.year} outside LPMS archive coverage "
                f"[{LPMS_ARCHIVE_START_YEAR}, {LPMS_ARCHIVE_END_YEAR}]"
            )
        if self.unavailable_hours < 0:
            raise LpmsNormalizationError(
                f"unavailable_hours cannot be negative: {self.unavailable_hours}"
            )
        if self.total_hours_year <= 0:
            raise LpmsNormalizationError(
                f"total_hours_year must be positive: {self.total_hours_year}"
            )


@dataclass(frozen=True)
class LpmsYearCoverage:
    """Coverage status for a single year in LPMS archive."""

    year: int
    status: LpmsCoverageStatus
    reason: str

    @classmethod
    def for_year(cls, year: int) -> LpmsYearCoverage:
        """Determine coverage status for a year."""
        if LPMS_ARCHIVE_START_YEAR <= year <= LPMS_ARCHIVE_END_YEAR:
            return cls(
                year=year,
                status=LpmsCoverageStatus.COVERED,
                reason=f"LPMS Annual Unavailability Report available {LPMS_ARCHIVE_START_YEAR}-{LPMS_ARCHIVE_END_YEAR}",
            )
        elif year < LPMS_ARCHIVE_START_YEAR:
            return cls(
                year=year,
                status=LpmsCoverageStatus.UNKNOWN,
                reason=f"LPMS archive begins {LPMS_ARCHIVE_START_YEAR}; no data for {year}",
            )
        else:
            return cls(
                year=year,
                status=LpmsCoverageStatus.UNKNOWN,
                reason=f"year {year} after current LPMS archive end {LPMS_ARCHIVE_END_YEAR}",
            )


def enumerate_d1_years_with_coverage() -> tuple[tuple[int, LpmsCoverageStatus], ...]:
    """Return D1 sample period years with LPMS coverage status.

    Returns UNKNOWN for 2010-2015 (before LPMS public archive).
    Returns COVERED for 2016-2024 (within LPMS archive).
    """
    result: list[tuple[int, LpmsCoverageStatus]] = []
    for year in range(LPMS_SAMPLE_START.year, LPMS_SAMPLE_END.year + 1):
        coverage = LpmsYearCoverage.for_year(year)
        result.append((year, coverage.status))
    return tuple(result)


def annual_unavailability_report_url(year: int) -> str:
    """Return the expected URL for LPMS Annual Unavailability Report.

    Note: Actual URL structure may vary; this provides the portal entry point.
    Reports are typically Excel/PDF downloads from the Corps Locks portal.
    """
    if year < LPMS_ARCHIVE_START_YEAR or year > LPMS_ARCHIVE_END_YEAR:
        raise LpmsNormalizationError(
            f"year {year} outside LPMS archive coverage "
            f"[{LPMS_ARCHIVE_START_YEAR}, {LPMS_ARCHIVE_END_YEAR}]"
        )
    return f"{LPMS_PORTAL_BASE}/annual-unavailability?p_year={year}"


def derive_d2_lock_universe() -> tuple[str, ...]:
    """Return the registered D2 navigation basin identifiers.

    The actual lock enumeration within these basins requires:
    1. USACE LPMS lock characteristics catalog
    2. Mapping of locks to D2 corridors via waterway codes

    This function returns the D2 basin scope only. Lock-level enumeration
    is deferred to execution with official LPMS lock catalog data.
    """
    return D2_NAVIGATION_BASINS


@dataclass(frozen=True)
class LpmsSourceRegistration:
    """D3 source registration record for USACE LPMS."""

    sweep_id: str = "S6"
    authority: str = LPMS_AUTHORITY
    vehicle: str = LPMS_VEHICLE
    portal_base: str = LPMS_PORTAL_BASE
    sample_start: date = LPMS_SAMPLE_START
    sample_end: date = LPMS_SAMPLE_END
    archive_start_year: int = LPMS_ARCHIVE_START_YEAR
    archive_end_year: int = LPMS_ARCHIVE_END_YEAR
    d8_mode: str = "binding_operational_restriction_only"
    enumeration_coverage: str = "annual_unavailability_2016_to_2024_UNKNOWN_2010_to_2015"


def get_source_registration() -> LpmsSourceRegistration:
    """Return the D3 source registration for USACE LPMS."""
    return LpmsSourceRegistration()


def parse_unavailability_hours(raw_value: str) -> float:
    """Parse unavailability hours from LPMS report cell value.

    Handles common formats:
    - Numeric: "1,234.5" -> 1234.5
    - Empty/dash: "-", "", "N/A" -> 0.0 (no unavailability)
    """
    if not isinstance(raw_value, str):
        raise LpmsNormalizationError(f"raw_value must be a string, got {type(raw_value)}")

    cleaned = raw_value.strip().replace(",", "")
    if not cleaned or cleaned in ("-", "N/A", "n/a", "--"):
        return 0.0

    try:
        return float(cleaned)
    except ValueError as exc:
        raise LpmsNormalizationError(
            f"cannot parse unavailability hours from {raw_value!r}"
        ) from exc


def validate_lock_in_d2_scope(lock_river: str, lock_system: str) -> bool:
    """Check if a lock's river/system maps to D2 navigation basins.

    This is a placeholder for actual D2-to-LPMS mapping logic.
    The mapping requires official USACE waterway code crosswalks.
    """
    lower_river = lock_river.lower()
    lower_system = lock_system.lower()

    d2_river_patterns = {
        "lower_mississippi": ["lower mississippi", "vicksburg", "new orleans"],
        "middle_mississippi": ["middle mississippi", "st. louis", "st louis"],
        "upper_mississippi": ["upper mississippi", "st. paul", "rock island"],
        "ohio": ["ohio", "louisville", "huntington", "pittsburgh", "nashville"],
        "illinois": ["illinois"],
        "columbia_snake": ["columbia", "snake"],
    }

    for _basin, patterns in d2_river_patterns.items():
        for pattern in patterns:
            if pattern in lower_river or pattern in lower_system:
                return True
    return False
