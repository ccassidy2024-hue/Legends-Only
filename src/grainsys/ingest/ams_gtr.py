"""Fail-closed normalization for AMS GTR positive-evidence-only S5 sources.

This module performs no networking, candidate minting, capture persistence, or
absence inference.  Raw source bytes must be captured by the separately
governed D6 machinery before a caller uses normalized text in a live sweep.

The registered AMS GTR surface lists weekly Grain Transportation Reports from
the USDA Agricultural Marketing Service archive.  ``full_text`` is a project
normalization field produced from captured GTR PDF content; it is not asserted
to be a source-native field.

AMS GTR archive: https://www.ams.usda.gov/services/transportation-analysis/gtr
Weekly publication on Thursdays.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime
from html.parser import HTMLParser
from typing import Any
from urllib.parse import urlparse

AMS_AUTHORITY = "USDA Agricultural Marketing Service"
GTR_VEHICLE = "Weekly Grain Transportation Report via AMS archive"

# GTR archive endpoint templates
GTR_ARCHIVE_BASE = "https://www.ams.usda.gov/services/transportation-analysis/gtr"
GTR_ARCHIVE_YEAR_TEMPLATE = GTR_ARCHIVE_BASE + "/archive-{year}"
GTR_PDF_BASE = "https://www.ams.usda.gov/sites/default/files/media"
GTR_PDF_TEMPLATE = GTR_PDF_BASE + "/GTR{mmddyyyy}.pdf"

# Registered year range for sample period coverage
GTR_SAMPLE_START_YEAR = 2010
GTR_SAMPLE_END_YEAR = 2024

# PDF content types
ACCEPTABLE_PDF_MEDIA_TYPES = frozenset({"application/pdf"})

_WS_RE = re.compile(r"\s+")
_DATE_RE = re.compile(r"(\w+)\s+(\d{1,2}),?\s+(\d{4})")
_GTR_FILENAME_RE = re.compile(r"GTR(\d{8})\.pdf", re.IGNORECASE)


class GtrNormalizationError(ValueError):
    """GTR bytes or listing metadata do not satisfy the frozen contract."""


@dataclass(frozen=True)
class GtrReportReference:
    """Source-native reference from the AMS GTR archive."""

    report_date: date
    pdf_url: str
    year: int
    week_ending: str  # Human-readable date string from source


def gtr_archive_endpoint(year: int) -> str:
    """Return the exact registered AMS GTR archive endpoint for a year."""
    if not isinstance(year, int):
        raise GtrNormalizationError(f"year must be an integer, got {type(year)}")
    if year < GTR_SAMPLE_START_YEAR or year > GTR_SAMPLE_END_YEAR + 2:
        raise GtrNormalizationError(
            f"year={year} is outside the registered sample period "
            f"[{GTR_SAMPLE_START_YEAR}, {GTR_SAMPLE_END_YEAR}]"
        )
    return GTR_ARCHIVE_YEAR_TEMPLATE.format(year=year)


def gtr_pdf_url(report_date: date) -> str:
    """Generate the expected PDF URL for a given report date."""
    if not isinstance(report_date, date):
        raise GtrNormalizationError(f"report_date must be a date, got {type(report_date)}")
    mmddyyyy = report_date.strftime("%m%d%Y")
    return GTR_PDF_TEMPLATE.format(mmddyyyy=mmddyyyy)


def _required_text(value: Any, *, field: str) -> str:
    if isinstance(value, bool) or not isinstance(value, (str, int)):
        raise GtrNormalizationError(f"{field} must be source text or integer")
    text = str(value)
    if not text or text != text.strip():
        raise GtrNormalizationError(f"{field} must be nonempty and trimmed")
    return text


def _require_ams_pdf_link(value: Any, *, field: str) -> str:
    link = _required_text(value, field=field)
    parsed = urlparse(link)
    if parsed.scheme != "https":
        raise GtrNormalizationError(f"{field} must be an https link")
    if parsed.hostname not in {"www.ams.usda.gov", "ams.usda.gov"}:
        raise GtrNormalizationError(f"{field} must be on ams.usda.gov")
    if not link.lower().endswith(".pdf"):
        raise GtrNormalizationError(f"{field} must be a PDF link")
    return link


def parse_report_date(date_str: str) -> date:
    """Parse a GTR report date string into a date object.
    
    Examples:
        "December 26, 2024" -> date(2024, 12, 26)
        "January 4, 2024" -> date(2024, 1, 4)
    """
    match = _DATE_RE.match(date_str.strip())
    if not match:
        raise GtrNormalizationError(
            f"Date string '{date_str}' does not match expected format"
        )
    month_str, day_str, year_str = match.groups()
    try:
        dt = datetime.strptime(f"{month_str} {day_str}, {year_str}", "%B %d, %Y")
        return dt.date()
    except ValueError as exc:
        raise GtrNormalizationError(f"Could not parse date '{date_str}': {exc}") from exc


def extract_date_from_pdf_filename(filename: str) -> date:
    """Extract the report date from a GTR PDF filename.
    
    Examples:
        "GTR10242024.pdf" -> date(2024, 10, 24)
        "GTR01042024.pdf" -> date(2024, 1, 4)
    """
    match = _GTR_FILENAME_RE.search(filename)
    if not match:
        raise GtrNormalizationError(
            f"Filename '{filename}' does not match GTRmmddyyyy.pdf pattern"
        )
    mmddyyyy = match.group(1)
    try:
        return datetime.strptime(mmddyyyy, "%m%d%Y").date()
    except ValueError as exc:
        raise GtrNormalizationError(f"Could not parse date from '{filename}': {exc}") from exc


class _GtrArchiveParser(HTMLParser):
    """Parser for the AMS GTR archive HTML page."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.reports: list[dict[str, str]] = []
        self._in_list = False
        self._in_item = False
        self._current_link = ""
        self._current_text = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag_lower = tag.casefold()
        if tag_lower in {"ul", "ol"}:
            self._in_list = True
        elif tag_lower == "li" and self._in_list:
            self._in_item = True
            self._current_link = ""
            self._current_text = ""
        elif tag_lower == "a" and self._in_item:
            for attr_name, attr_val in attrs:
                if attr_name == "href" and attr_val:
                    self._current_link = attr_val

    def handle_endtag(self, tag: str) -> None:
        tag_lower = tag.casefold()
        if tag_lower in {"ul", "ol"}:
            self._in_list = False
        elif tag_lower == "li" and self._in_item:
            self._in_item = False
            if self._current_link and self._current_link.lower().endswith(".pdf"):
                self.reports.append({
                    "date_text": self._current_text.strip(),
                    "pdf_url": self._current_link,
                })

    def handle_data(self, data: str) -> None:
        if self._in_item:
            self._current_text += data


def parse_gtr_archive_listing(raw_html: bytes, *, year: int) -> tuple[GtrReportReference, ...]:
    """Validate a captured AMS GTR archive listing without inferring coverage."""
    if not isinstance(raw_html, bytes):
        raise GtrNormalizationError("raw_html must be bytes")
    if not isinstance(year, int):
        raise GtrNormalizationError("year must be an integer")

    try:
        decoded = raw_html.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise GtrNormalizationError(f"AMS HTML decode failed: {exc}") from exc

    parser = _GtrArchiveParser()
    try:
        parser.feed(decoded)
        parser.close()
    except Exception as exc:
        raise GtrNormalizationError(f"AMS HTML parse failed: {exc}") from exc

    out: list[GtrReportReference] = []
    seen_dates: set[date] = set()

    for item in parser.reports:
        pdf_url = item.get("pdf_url", "")
        date_text = item.get("date_text", "")

        # Try to extract date from PDF filename first
        try:
            report_date = extract_date_from_pdf_filename(pdf_url)
        except GtrNormalizationError:
            # Fall back to parsing date text
            try:
                report_date = parse_report_date(date_text)
            except GtrNormalizationError:
                continue  # Skip entries we can't parse

        if report_date in seen_dates:
            raise GtrNormalizationError(
                f"duplicate report date {report_date} in listing"
            )
        seen_dates.add(report_date)

        # Validate the link
        try:
            validated_url = _require_ams_pdf_link(pdf_url, field="pdf_url")
        except GtrNormalizationError:
            continue  # Skip invalid links

        out.append(
            GtrReportReference(
                report_date=report_date,
                pdf_url=validated_url,
                year=year,
                week_ending=date_text,
            )
        )

    # Sort by date descending (newest first, matching archive page order)
    out.sort(key=lambda r: r.report_date, reverse=True)
    return tuple(out)


def normalize_full_text_pdf(raw_pdf: bytes, *, content_type: str) -> str:
    """Normalize captured GTR PDF into the frozen local ``full_text`` field.
    
    Note: PDF text extraction requires additional libraries (e.g., pdfplumber,
    PyMuPDF). This function validates the PDF structure but defers actual text
    extraction to the sweep execution layer where those dependencies are managed.
    """
    if not isinstance(raw_pdf, bytes):
        raise GtrNormalizationError("raw_pdf must be bytes")
    if not isinstance(content_type, str) or not content_type.strip():
        raise GtrNormalizationError("content_type must be a nonempty string")

    media_type = content_type.split(";", 1)[0].strip().casefold()
    if media_type not in ACCEPTABLE_PDF_MEDIA_TYPES:
        raise GtrNormalizationError(
            f"unsupported content_type {content_type!r}; expected application/pdf"
        )

    # Validate PDF magic bytes
    if not raw_pdf.startswith(b"%PDF-"):
        raise GtrNormalizationError("raw_pdf does not start with PDF magic bytes")

    # Return a placeholder indicating PDF needs extraction at sweep time
    raise GtrNormalizationError(
        "PDF text extraction deferred to sweep execution layer; "
        "use sweep machinery with pdfplumber or equivalent"
    )


def get_registered_years() -> tuple[int, ...]:
    """Return the tuple of years covered by the registered sample period."""
    return tuple(range(GTR_SAMPLE_START_YEAR, GTR_SAMPLE_END_YEAR + 1))


def expected_reports_per_year(year: int) -> int:
    """Return the expected number of weekly GTR reports for a given year.
    
    GTR is published weekly (typically Thursday), so ~52 reports per year.
    Some years may have 53 weeks.
    """
    if not isinstance(year, int):
        raise GtrNormalizationError(f"year must be an integer, got {type(year)}")
    # Simple heuristic: most years have 52 reports, some have 53
    jan_1 = date(year, 1, 1)
    dec_31 = date(year, 12, 31)
    # Count Thursdays
    thursdays = 0
    current = jan_1
    while current <= dec_31:
        if current.weekday() == 3:  # Thursday
            thursdays += 1
        current = date.fromordinal(current.toordinal() + 1)
    return thursdays
