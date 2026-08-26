"""Fail-closed normalization for STB positive-evidence-only S7 sources.

This module performs no networking, candidate minting, capture persistence, or
absence inference.  Raw source bytes must be captured by the separately
governed D6 machinery before a caller uses normalized text in a live sweep.

The registered STB surface provides service orders, embargo dockets, and
railroad performance filings from the Surface Transportation Board.

STB Website: https://www.stb.gov
Docket Search: https://www.stb.gov/proceedings-actions/search-stb-records/

Per EPISODE_PROTOCOL.md §J S7: "Enumerate service orders and reported service
events" - no new selector unless canonical text proves one.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any
from urllib.parse import urlparse

STB_AUTHORITY = "Surface Transportation Board"
STB_VEHICLE = "STB service dockets and railroad performance filings"

# STB endpoints
STB_WEBSITE = "https://www.stb.gov"
STB_DOCKET_SEARCH = STB_WEBSITE + "/proceedings-actions/search-stb-records/"
STB_NEWS_BASE = STB_WEBSITE + "/news-communications/latest-news/"

# Docket type prefixes relevant to grain transportation (per STB classification)
# EP = Exemption Proceeding
# EX = Ex Parte (general rulemaking)
# FD = Finance Docket (mergers, abandonments)
# NOR = Notice of Exemption
STB_RELEVANT_DOCKET_PREFIXES = frozenset({
    "EP",   # Exemption Proceedings (includes embargo oversight)
    "EX",   # Ex Parte proceedings
    "STB",  # General STB proceedings
})

# Class I railroads serving grain corridors
CLASS_I_GRAIN_RAILROADS: tuple[tuple[str, str], ...] = (
    ("BNSF", "BNSF Railway"),
    ("UP", "Union Pacific Railroad"),
    ("NS", "Norfolk Southern Railway"),
    ("CSX", "CSX Transportation"),
    ("CN", "Canadian National Railway"),
    ("CP", "Canadian Pacific Kansas City"),
)

# Registered year range for sample period coverage
STB_SAMPLE_START_YEAR = 2010
STB_SAMPLE_END_YEAR = 2024

# Service event types documented in STB filings
SERVICE_EVENT_TYPES = frozenset({
    "embargo",
    "permit_restriction",
    "service_order",
    "service_advisory",
    "car_supply_shortage",
    "crew_shortage",
    "congestion",
    "network_disruption",
})

_WS_RE = re.compile(r"\s+")
_DOCKET_NUMBER_RE = re.compile(
    r"(EP|EX|FD|NOR|STB)\s*[-]?\s*(\d+)", re.IGNORECASE
)


class StbNormalizationError(ValueError):
    """STB bytes or data do not satisfy the frozen contract."""


@dataclass(frozen=True)
class StbDocketReference:
    """Reference to an STB docket."""

    docket_number: str
    docket_type: str
    title: str
    filed_date: date | None
    parties: tuple[str, ...]
    url: str


@dataclass(frozen=True)
class ServiceOrderRecord:
    """A service order or service event from STB filings."""

    docket_number: str
    railroad: str
    event_type: str
    effective_date: date | None
    description: str
    commodity_affected: str | None
    source_url: str


@dataclass(frozen=True)
class EmbargoRecord:
    """An embargo or permit restriction record."""

    railroad: str
    embargo_number: str | None
    effective_date: date
    expiration_date: date | None
    affected_traffic: str
    affected_locations: tuple[str, ...]
    reason: str
    source_ref: str


def docket_search_url(docket_prefix: str, year: int | None = None) -> str:
    """Return the STB docket search URL for a given prefix and optional year."""
    if docket_prefix not in STB_RELEVANT_DOCKET_PREFIXES:
        raise StbNormalizationError(
            f"docket_prefix={docket_prefix!r} is outside the registered docket types"
        )
    # STB search uses query parameters
    base = STB_DOCKET_SEARCH
    if year:
        return f"{base}?docket_type={docket_prefix}&year={year}"
    return f"{base}?docket_type={docket_prefix}"


def _required_text(value: Any, *, field: str) -> str:
    if isinstance(value, bool) or not isinstance(value, (str, int)):
        raise StbNormalizationError(f"{field} must be source text or integer")
    text = str(value)
    if not text or text != text.strip():
        raise StbNormalizationError(f"{field} must be nonempty and trimmed")
    return text


def _optional_text(value: Any, *, field: str) -> str | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (str, int)):
        raise StbNormalizationError(f"{field} must be source text, integer, or None")
    text = str(value).strip()
    return text if text else None


def parse_docket_number(docket_str: str) -> tuple[str, int]:
    """Parse an STB docket number string.
    
    Examples:
        "EP 772" -> ("EP", 772)
        "STB-12345" -> ("STB", 12345)
    """
    match = _DOCKET_NUMBER_RE.match(docket_str.strip())
    if not match:
        raise StbNormalizationError(
            f"Docket number '{docket_str}' does not match expected format"
        )
    return match.group(1).upper(), int(match.group(2))


def _require_stb_link(value: Any, *, field: str) -> str:
    link = _required_text(value, field=field)
    parsed = urlparse(link)
    if parsed.scheme != "https":
        raise StbNormalizationError(f"{field} must be an https link")
    if parsed.hostname not in {"www.stb.gov", "stb.gov"}:
        raise StbNormalizationError(f"{field} must be on stb.gov")
    return link


def is_grain_relevant_docket(title: str, parties: tuple[str, ...]) -> bool:
    """Check if a docket appears relevant to grain transportation.
    
    This is a heuristic filter; actual relevance determination requires
    human review per EPISODE_PROTOCOL.md positive-evidence-only semantics.
    """
    grain_keywords = {
        "grain", "corn", "wheat", "soybean", "agricultural",
        "shuttle", "unit train", "car supply", "car order",
    }
    
    # Check title
    title_lower = title.lower()
    for keyword in grain_keywords:
        if keyword in title_lower:
            return True
    
    # Check if any grain-corridor railroad is a party
    grain_railroads = {code.lower() for code, _ in CLASS_I_GRAIN_RAILROADS}
    for party in parties:
        party_lower = party.lower()
        for railroad in grain_railroads:
            if railroad in party_lower:
                return True
    
    return False


def enumerate_service_orders(
    docket_records: list[StbDocketReference],
) -> tuple[ServiceOrderRecord, ...]:
    """Enumerate service orders from docket records.
    
    Per §J S7: "Enumerate service orders and reported service events"
    No new selector unless canonical text proves one.
    """
    out: list[ServiceOrderRecord] = []

    for docket in docket_records:
        # Service orders are typically EP dockets
        if not docket.docket_number.startswith("EP"):
            continue

        # Extract railroad from parties
        railroad = ""
        for party in docket.parties:
            for code, name in CLASS_I_GRAIN_RAILROADS:
                if code.lower() in party.lower() or name.lower() in party.lower():
                    railroad = code
                    break
            if railroad:
                break

        if not railroad:
            continue

        # Determine event type from title
        title_lower = docket.title.lower()
        event_type = "service_order"  # Default
        if "embargo" in title_lower:
            event_type = "embargo"
        elif "permit" in title_lower:
            event_type = "permit_restriction"
        elif "congestion" in title_lower:
            event_type = "congestion"

        out.append(
            ServiceOrderRecord(
                docket_number=docket.docket_number,
                railroad=railroad,
                event_type=event_type,
                effective_date=docket.filed_date,
                description=docket.title,
                commodity_affected="grain" if is_grain_relevant_docket(docket.title, docket.parties) else None,
                source_url=docket.url,
            )
        )

    return tuple(out)


def get_registered_railroads() -> tuple[tuple[str, str], ...]:
    """Return the tuple of Class I railroads serving grain corridors."""
    return CLASS_I_GRAIN_RAILROADS


def get_registered_years() -> tuple[int, ...]:
    """Return the tuple of years covered by the registered sample period."""
    return tuple(range(STB_SAMPLE_START_YEAR, STB_SAMPLE_END_YEAR + 1))


def get_relevant_docket_types() -> frozenset[str]:
    """Return the set of docket type prefixes relevant to grain transportation."""
    return STB_RELEVANT_DOCKET_PREFIXES


def normalize_press_release(
    raw_content: bytes,
    *,
    content_type: str,
) -> str:
    """Normalize an STB press release or decision document.
    
    Press releases often announce service orders, embargo findings, or
    performance oversight actions.
    """
    if not isinstance(raw_content, bytes):
        raise StbNormalizationError("raw_content must be bytes")
    if not isinstance(content_type, str) or not content_type.strip():
        raise StbNormalizationError("content_type must be a nonempty string")

    media_type = content_type.split(";", 1)[0].strip().casefold()

    if media_type == "text/html":
        try:
            decoded = raw_content.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise StbNormalizationError(f"HTML decode failed: {exc}") from exc
        # Simple text extraction
        normalized = _WS_RE.sub(" ", decoded).strip()
        if not normalized:
            raise StbNormalizationError("Press release produced empty normalized text")
        return normalized
    elif media_type == "application/pdf":
        # Validate PDF magic bytes
        if not raw_content.startswith(b"%PDF-"):
            raise StbNormalizationError("raw_content does not start with PDF magic bytes")
        raise StbNormalizationError(
            "PDF text extraction deferred to sweep execution layer"
        )
    else:
        raise StbNormalizationError(
            f"unsupported content_type {content_type!r}; expected text/html or application/pdf"
        )
