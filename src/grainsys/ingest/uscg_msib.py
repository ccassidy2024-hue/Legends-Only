"""Fail-closed normalization for USCG MSIB positive-evidence-only S3 sources.

This module performs no networking, candidate minting, capture persistence, or
absence inference.  Raw source bytes must be captured by the separately
governed D6 machinery before a caller uses normalized text in a live sweep.

The registered USCG MSIB surface lists Marine Safety Information Bulletins
by year from NAVCEN.  ``full_text`` is a project normalization field produced
from captured MSIB PDF or HTML content; it is not asserted to be a
source-native field.

NAVCEN MSIB archive: https://navcen.uscg.gov/msib-national
District-level bulletins via VTS and Homeport systems.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from html.parser import HTMLParser
from typing import Any
from urllib.parse import urlparse

USCG_AUTHORITY = "U.S. Coast Guard"
MSIB_VEHICLE = "Marine Safety Information Bulletins via NAVCEN archive"

# Districts relevant to grain logistics corridors per EPISODE_PROTOCOL.md §J
# 8th District covers the Mississippi River system (primary grain corridor)
# 13th District covers Pacific Northwest (Columbia-Snake corridor)
MSIB_DISTRICTS: tuple[tuple[str, str, str], ...] = (
    ("D8", "8th District", "lower_mississippi"),
    ("D8", "8th District", "middle_mississippi"),
    ("D8", "8th District", "ohio"),
    ("D13", "13th District", "columbia_snake"),
)

# NAVCEN national MSIB archive endpoint template
NAVCEN_NATIONAL_MSIB_ENDPOINT = "https://navcen.uscg.gov/msib-national"
NAVCEN_YEAR_FILTER_PARAM = "field_msib_year_value"

# VTS Lower Mississippi River bulletins (GovDelivery)
VTS_LMR_BULLETINS_BASE = "https://content.govdelivery.com/accounts/USDHSCG/bulletins"

# PDF content types
ACCEPTABLE_PDF_MEDIA_TYPES = frozenset({"application/pdf"})

# Registered year range for sample period coverage
MSIB_SAMPLE_START_YEAR = 2010
MSIB_SAMPLE_END_YEAR = 2024

_WS_RE = re.compile(r"\s+")
_MSIB_NUMBER_RE = re.compile(
    r"^(?:MSIB\s*)?(\d{2,3})[-_](\d{2,4})$", re.IGNORECASE
)


class MsibNormalizationError(ValueError):
    """MSIB bytes or listing metadata do not satisfy the frozen contract."""


@dataclass(frozen=True)
class MsibReference:
    """Source-native reference from the NAVCEN MSIB archive."""

    msib_number: str
    date: str
    title: str
    pdf_url: str
    year: int


@dataclass(frozen=True)
class VtsBulletinReference:
    """Reference to a VTS bulletin (e.g., LMR 5-day outlook)."""

    bulletin_id: str
    date: str
    title: str
    url: str
    district: str


def national_msib_endpoint(year: int) -> str:
    """Return the exact registered NAVCEN MSIB archive endpoint for a year."""
    if not isinstance(year, int):
        raise MsibNormalizationError(f"year must be an integer, got {type(year)}")
    if year < MSIB_SAMPLE_START_YEAR or year > MSIB_SAMPLE_END_YEAR + 2:
        raise MsibNormalizationError(
            f"year={year} is outside the registered sample period "
            f"[{MSIB_SAMPLE_START_YEAR}, {MSIB_SAMPLE_END_YEAR}]"
        )
    # NAVCEN uses 2-digit year codes for the filter
    year_code = year - 2000 if year >= 2000 else year
    return f"{NAVCEN_NATIONAL_MSIB_ENDPOINT}?{NAVCEN_YEAR_FILTER_PARAM}={year_code}"


def _required_text(value: Any, *, field: str) -> str:
    if isinstance(value, bool) or not isinstance(value, (str, int)):
        raise MsibNormalizationError(f"{field} must be source text or integer")
    text = str(value)
    if not text or text != text.strip():
        raise MsibNormalizationError(f"{field} must be nonempty and trimmed")
    return text


def _require_navcen_pdf_link(value: Any, *, field: str) -> str:
    link = _required_text(value, field=field)
    parsed = urlparse(link)
    if parsed.scheme != "https":
        raise MsibNormalizationError(f"{field} must be an https link")
    if parsed.hostname not in {"navcen.uscg.gov", "www.navcen.uscg.gov"}:
        raise MsibNormalizationError(f"{field} must be on navcen.uscg.gov")
    if not link.lower().endswith(".pdf"):
        raise MsibNormalizationError(f"{field} must be a PDF link")
    return link


def parse_msib_number(msib_str: str) -> tuple[int, int]:
    """Parse an MSIB number string into (number, year) tuple.
    
    Examples:
        "04-26" -> (4, 26)
        "MSIB 03-26" -> (3, 26)
        "018_14" -> (18, 14)
    """
    match = _MSIB_NUMBER_RE.match(msib_str.strip())
    if not match:
        raise MsibNormalizationError(
            f"MSIB number '{msib_str}' does not match expected format"
        )
    return int(match.group(1)), int(match.group(2))


class _NazcenMsibListParser(HTMLParser):
    """Parser for the NAVCEN MSIB archive HTML page."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.msibs: list[dict[str, str]] = []
        self._in_table = False
        self._in_row = False
        self._in_cell = False
        self._current_row: list[str] = []
        self._current_cell_text = ""
        self._current_link = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag_lower = tag.casefold()
        if tag_lower == "table":
            self._in_table = True
        elif tag_lower == "tr" and self._in_table:
            self._in_row = True
            self._current_row = []
        elif tag_lower == "td" and self._in_row:
            self._in_cell = True
            self._current_cell_text = ""
            self._current_link = ""
        elif tag_lower == "a" and self._in_cell:
            for attr_name, attr_val in attrs:
                if attr_name == "href" and attr_val:
                    self._current_link = attr_val

    def handle_endtag(self, tag: str) -> None:
        tag_lower = tag.casefold()
        if tag_lower == "table":
            self._in_table = False
        elif tag_lower == "tr" and self._in_row:
            self._in_row = False
            if len(self._current_row) >= 3:
                # Row format: [MSIB Number, Active MSIB (link), Date, ...]
                self.msibs.append({
                    "msib_number": self._current_row[0],
                    "title": self._current_row[1] if len(self._current_row) > 1 else "",
                    "date": self._current_row[2] if len(self._current_row) > 2 else "",
                    "link": self._current_link,
                })
        elif tag_lower == "td" and self._in_cell:
            self._in_cell = False
            self._current_row.append(self._current_cell_text.strip())

    def handle_data(self, data: str) -> None:
        if self._in_cell:
            self._current_cell_text += data


def parse_navcen_msib_listing(raw_html: bytes, *, year: int) -> tuple[MsibReference, ...]:
    """Validate a captured NAVCEN MSIB archive listing without inferring coverage."""
    if not isinstance(raw_html, bytes):
        raise MsibNormalizationError("raw_html must be bytes")
    if not isinstance(year, int):
        raise MsibNormalizationError("year must be an integer")

    try:
        decoded = raw_html.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise MsibNormalizationError(f"NAVCEN HTML decode failed: {exc}") from exc

    parser = _NazcenMsibListParser()
    try:
        parser.feed(decoded)
        parser.close()
    except Exception as exc:
        raise MsibNormalizationError(f"NAVCEN HTML parse failed: {exc}") from exc

    out: list[MsibReference] = []
    seen: set[str] = set()
    for item in parser.msibs:
        msib_number = item.get("msib_number", "").strip()
        if not msib_number:
            continue  # Skip header rows or empty rows

        if msib_number in seen:
            raise MsibNormalizationError(
                f"duplicate MSIB number {msib_number!r} in listing"
            )
        seen.add(msib_number)

        pdf_link = item.get("link", "")
        if not pdf_link or not pdf_link.lower().endswith(".pdf"):
            continue  # Skip rows without PDF links

        # Validate the link
        try:
            validated_link = _require_navcen_pdf_link(pdf_link, field="pdf_url")
        except MsibNormalizationError:
            continue  # Skip invalid links

        out.append(
            MsibReference(
                msib_number=msib_number,
                date=item.get("date", ""),
                title=item.get("title", ""),
                pdf_url=validated_link,
                year=year,
            )
        )

    return tuple(out)


class _VisibleTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self._suppressed_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.casefold() in {"script", "style", "noscript", "template"}:
            self._suppressed_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag.casefold() in {"script", "style", "noscript", "template"}:
            self._suppressed_depth = max(0, self._suppressed_depth - 1)

    def handle_data(self, data: str) -> None:
        if self._suppressed_depth == 0:
            self.parts.append(data)


def normalize_full_text_html(raw_html: bytes, *, content_type: str) -> str:
    """Normalize captured MSIB HTML into the frozen local ``full_text`` field."""
    if not isinstance(raw_html, bytes):
        raise MsibNormalizationError("raw_html must be bytes")
    if not isinstance(content_type, str) or not content_type.strip():
        raise MsibNormalizationError("content_type must be a nonempty string")

    media_type = content_type.split(";", 1)[0].strip().casefold()
    if media_type != "text/html":
        raise MsibNormalizationError(
            f"unsupported content_type {content_type!r}; only text/html is registered"
        )

    try:
        decoded = raw_html.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise MsibNormalizationError(f"MSIB HTML decode failed: {exc}") from exc

    parser = _VisibleTextParser()
    try:
        parser.feed(decoded)
        parser.close()
    except Exception as exc:
        raise MsibNormalizationError(f"MSIB HTML parse failed: {exc}") from exc

    normalized = _WS_RE.sub(" ", " ".join(parser.parts)).strip()
    if not normalized:
        raise MsibNormalizationError("MSIB HTML produced empty normalized full_text")
    return normalized


def normalize_full_text_pdf(raw_pdf: bytes, *, content_type: str) -> str:
    """Normalize captured MSIB PDF into the frozen local ``full_text`` field.
    
    Note: PDF text extraction requires additional libraries (e.g., pdfplumber,
    PyMuPDF). This function validates the PDF structure but defers actual text
    extraction to the sweep execution layer where those dependencies are managed.
    """
    if not isinstance(raw_pdf, bytes):
        raise MsibNormalizationError("raw_pdf must be bytes")
    if not isinstance(content_type, str) or not content_type.strip():
        raise MsibNormalizationError("content_type must be a nonempty string")

    media_type = content_type.split(";", 1)[0].strip().casefold()
    if media_type not in ACCEPTABLE_PDF_MEDIA_TYPES:
        raise MsibNormalizationError(
            f"unsupported content_type {content_type!r}; expected application/pdf"
        )

    # Validate PDF magic bytes
    if not raw_pdf.startswith(b"%PDF-"):
        raise MsibNormalizationError("raw_pdf does not start with PDF magic bytes")

    # Return a placeholder indicating PDF needs extraction at sweep time
    # The actual extraction requires pdfplumber or similar which may not be
    # available in all contexts
    raise MsibNormalizationError(
        "PDF text extraction deferred to sweep execution layer; "
        "use sweep machinery with pdfplumber or equivalent"
    )


def get_registered_years() -> tuple[int, ...]:
    """Return the tuple of years covered by the registered sample period."""
    return tuple(range(MSIB_SAMPLE_START_YEAR, MSIB_SAMPLE_END_YEAR + 1))


def district_covers_basin(district_code: str, basin: str) -> bool:
    """Check if a USCG district covers a given navigation basin."""
    for d_code, _, d_basin in MSIB_DISTRICTS:
        if d_code == district_code and d_basin == basin:
            return True
    return False
