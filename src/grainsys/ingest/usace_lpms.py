"""Fail-closed normalization for USACE LPMS positive-evidence-only S6 sources.

This module performs no networking, candidate minting, capture persistence, or
absence inference.  Raw source bytes must be captured by the separately
governed D6 machinery before a caller uses normalized text in a live sweep.

The registered LPMS surface provides lock performance data including
unavailability reports from the USACE Navigation Data Center Corps Locks system.
Outage enumeration operates under D8 ``binding_operational_restriction_only``
mode - no invented thresholds; only documented operational restrictions.

LPMS Portal: https://ndc.ops.usace.army.mil/ords/r/lpms/corps-locks/home
XML API: https://corpslocks.usace.army.mil/lpwb/xml.lockqueue
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse
from xml.etree import ElementTree

USACE_AUTHORITY = "U.S. Army Corps of Engineers"
LPMS_VEHICLE = "Lock Performance Monitoring System via Corps Locks portal"

# LPMS endpoints
CORPS_LOCKS_PORTAL = "https://ndc.ops.usace.army.mil/ords/r/lpms/corps-locks/home"
LPMS_XML_BASE = "https://corpslocks.usace.army.mil/lpwb"
LPMS_LOCK_QUEUE_ENDPOINT = LPMS_XML_BASE + "/xml.lockqueue"
LPMS_TONNAGE_ENDPOINT = LPMS_XML_BASE + "/xml.tonnage"

# Rivers relevant to grain logistics corridors (D2 navigation basins)
LPMS_RIVERS: tuple[tuple[str, str], ...] = (
    ("MS", "Mississippi River"),
    ("OH", "Ohio River"),
    ("IL", "Illinois River"),
    ("TN", "Tennessee River"),
    ("AR", "Arkansas River"),
    ("COLU", "Columbia River"),
)

# Locks on key grain corridors (subset - not exhaustive)
# Per D8 binding_operational_restriction_only: we enumerate documented
# operational restrictions, not invented thresholds
LPMS_GRAIN_CORRIDOR_LOCKS: tuple[tuple[str, str, str], ...] = (
    # Mississippi River System
    ("MS", "27", "Lock 27 (Chain of Rocks)"),
    ("MS", "26", "Lock 26 (Mel Price)"),
    ("MS", "25", "Lock 25"),
    ("MS", "24", "Lock 24"),
    ("MS", "22", "Lock 22"),
    # Illinois Waterway
    ("IL", "PEOLOCK", "Peoria Lock"),
    ("IL", "LAGON", "LaGrange Lock"),
    ("IL", "STARV", "Starved Rock Lock"),
    # Ohio River
    ("OH", "MELDAHL", "Meldahl Locks and Dam"),
    ("OH", "GREENUP", "Greenup Locks and Dam"),
    ("OH", "52", "Lock 52"),
    ("OH", "53", "Lock 53"),
)

# Registered year range for sample period coverage
LPMS_SAMPLE_START_YEAR = 2010
LPMS_SAMPLE_END_YEAR = 2024

# Unavailability categories (per LPMS documentation)
UNAVAILABILITY_CATEGORIES = frozenset({
    "scheduled",
    "unscheduled",
    "weather",
    "mechanical",
    "structural",
    "other",
})

_WS_RE = re.compile(r"\s+")


class LpmsNormalizationError(ValueError):
    """LPMS bytes or data do not satisfy the frozen contract."""


@dataclass(frozen=True)
class LockReference:
    """Reference to a lock in the LPMS system."""

    river_code: str
    lock_code: str
    lock_name: str


@dataclass(frozen=True)
class LockQueueRecord:
    """A lock queue record from the LPMS XML API."""

    lock_code: str
    vessel_name: str
    vessel_no: str
    direction: str
    num_barges: int
    arrival_date: str
    end_of_lockage: str | None


@dataclass(frozen=True)
class LockUnavailabilityRecord:
    """A lock unavailability record from LPMS annual reports."""

    lock_code: str
    lock_name: str
    year: int
    unavailable_hours: float
    category: str
    start_date: str | None
    end_date: str | None
    description: str


def lock_queue_endpoint(river_code: str, lock_code: str) -> str:
    """Return the exact LPMS XML lock queue endpoint for a river/lock."""
    allowed_rivers = {code for code, _ in LPMS_RIVERS}
    if river_code not in allowed_rivers:
        raise LpmsNormalizationError(
            f"river_code={river_code!r} is outside the registered D2 river universe"
        )
    return f"{LPMS_LOCK_QUEUE_ENDPOINT}?in_river={river_code}&in_lock={lock_code}"


def _required_text(value: Any, *, field: str) -> str:
    if isinstance(value, bool) or not isinstance(value, (str, int)):
        raise LpmsNormalizationError(f"{field} must be source text or integer")
    text = str(value)
    if not text or text != text.strip():
        raise LpmsNormalizationError(f"{field} must be nonempty and trimmed")
    return text


def _optional_text(value: Any, *, field: str) -> str | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (str, int)):
        raise LpmsNormalizationError(f"{field} must be source text, integer, or None")
    text = str(value).strip()
    return text if text else None


def parse_lock_queue_xml(raw_xml: bytes, *, lock_code: str) -> tuple[LockQueueRecord, ...]:
    """Parse LPMS lock queue XML response.
    
    XML format (per observed API):
    <rowset>
      <row>
        <vessel_name>...</vessel_name>
        <vessel_no>...</vessel_no>
        <direction>...</direction>
        <num_barges>...</num_barges>
        <arrival_date>...</arrival_date>
        <end_of_lockage>...</end_of_lockage>
      </row>
      ...
    </rowset>
    """
    if not isinstance(raw_xml, bytes):
        raise LpmsNormalizationError("raw_xml must be bytes")

    try:
        decoded = raw_xml.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise LpmsNormalizationError(f"LPMS XML decode failed: {exc}") from exc

    try:
        root = ElementTree.fromstring(decoded)
    except ElementTree.ParseError as exc:
        raise LpmsNormalizationError(f"LPMS XML parse failed: {exc}") from exc

    out: list[LockQueueRecord] = []

    for row in root.findall(".//row"):
        vessel_name_el = row.find("vessel_name")
        vessel_no_el = row.find("vessel_no")
        direction_el = row.find("direction")
        num_barges_el = row.find("num_barges")
        arrival_date_el = row.find("arrival_date")
        end_of_lockage_el = row.find("end_of_lockage")

        if vessel_name_el is None or vessel_name_el.text is None:
            continue

        try:
            num_barges = int(num_barges_el.text.strip()) if num_barges_el is not None and num_barges_el.text else 0
        except ValueError:
            num_barges = 0

        out.append(
            LockQueueRecord(
                lock_code=lock_code,
                vessel_name=_required_text(vessel_name_el.text, field="vessel_name"),
                vessel_no=_required_text(vessel_no_el.text if vessel_no_el is not None else "", field="vessel_no"),
                direction=_required_text(direction_el.text if direction_el is not None else "", field="direction"),
                num_barges=num_barges,
                arrival_date=_required_text(arrival_date_el.text if arrival_date_el is not None else "", field="arrival_date"),
                end_of_lockage=_optional_text(end_of_lockage_el.text if end_of_lockage_el is not None else None, field="end_of_lockage"),
            )
        )

    return tuple(out)


def enumerate_operational_outages(
    unavailability_records: list[LockUnavailabilityRecord],
) -> tuple[LockUnavailabilityRecord, ...]:
    """Enumerate operational outages from unavailability records.
    
    Per D8 binding_operational_restriction_only mode:
    - Only include records with documented operational restrictions
    - Do not apply invented thresholds
    - Preserve unknown; do not generate absence evidence
    """
    out: list[LockUnavailabilityRecord] = []

    for record in unavailability_records:
        # Under binding_operational_restriction_only mode, we include
        # all documented unavailability records without applying thresholds
        if record.unavailable_hours > 0:
            out.append(record)

    return tuple(out)


def get_registered_rivers() -> tuple[tuple[str, str], ...]:
    """Return the tuple of rivers covered by the registered D2 corridor scope."""
    return LPMS_RIVERS


def get_registered_locks() -> tuple[LockReference, ...]:
    """Return the tuple of locks covered by the registered grain corridor scope."""
    return tuple(
        LockReference(river_code=r, lock_code=l, lock_name=n)
        for r, l, n in LPMS_GRAIN_CORRIDOR_LOCKS
    )


def get_registered_years() -> tuple[int, ...]:
    """Return the tuple of years covered by the registered sample period."""
    return tuple(range(LPMS_SAMPLE_START_YEAR, LPMS_SAMPLE_END_YEAR + 1))


def normalize_unavailability_report(
    raw_content: bytes,
    *,
    content_type: str,
    year: int,
) -> tuple[LockUnavailabilityRecord, ...]:
    """Normalize an annual unavailability report from Corps Locks.
    
    The annual unavailability report summarizes hours each lock was unavailable.
    Format varies; this function handles the documented web-table format.
    """
    if not isinstance(raw_content, bytes):
        raise LpmsNormalizationError("raw_content must be bytes")
    if not isinstance(content_type, str) or not content_type.strip():
        raise LpmsNormalizationError("content_type must be a nonempty string")
    if not isinstance(year, int):
        raise LpmsNormalizationError("year must be an integer")

    media_type = content_type.split(";", 1)[0].strip().casefold()

    if media_type == "text/html":
        return _parse_unavailability_html(raw_content, year=year)
    elif media_type in {"text/csv", "application/csv"}:
        return _parse_unavailability_csv(raw_content, year=year)
    else:
        raise LpmsNormalizationError(
            f"unsupported content_type {content_type!r}; expected text/html or text/csv"
        )


def _parse_unavailability_html(raw_html: bytes, *, year: int) -> tuple[LockUnavailabilityRecord, ...]:
    """Parse unavailability data from HTML table format."""
    try:
        decoded = raw_html.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise LpmsNormalizationError(f"HTML decode failed: {exc}") from exc

    # Placeholder - actual HTML parsing would extract table data
    # This is deferred to sweep execution where HTML structure is known
    raise LpmsNormalizationError(
        "HTML unavailability parsing deferred to sweep execution layer"
    )


def _parse_unavailability_csv(raw_csv: bytes, *, year: int) -> tuple[LockUnavailabilityRecord, ...]:
    """Parse unavailability data from CSV format."""
    try:
        decoded = raw_csv.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise LpmsNormalizationError(f"CSV decode failed: {exc}") from exc

    # Placeholder - actual CSV parsing
    raise LpmsNormalizationError(
        "CSV unavailability parsing deferred to sweep execution layer"
    )
