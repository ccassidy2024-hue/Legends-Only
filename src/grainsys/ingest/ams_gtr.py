"""Deterministic adapter for USDA AMS Grain Transportation Report archive.

This module implements S5 source enumeration per EPISODE_PROTOCOL.md §J:
"AMS Grain Transportation Report archive - Weekly issues; keyword scan of
transportation-conditions sections."

The registered USDA AMS GTR archive surface provides weekly PDF reports
covering grain transportation conditions. This adapter performs deterministic
URL construction and PDF text extraction for keyword matching under D4 policy.

Authority: U.S. Department of Agriculture, Agricultural Marketing Service
Archive URL: https://www.ams.usda.gov/services/transportation-analysis/gtr/archive
Vehicle: Weekly PDF reports (typically Thursday publication)
Sample period: 2010-01-01 to 2024-12-31 (D1 registered)

This module performs no candidate minting, capture persistence, or
absence inference. Raw source bytes must be captured by the separately
governed D6 machinery before a caller uses normalized text in a live sweep.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from urllib.parse import urljoin

AMS_GTR_AUTHORITY = "U.S. Department of Agriculture, Agricultural Marketing Service"
AMS_GTR_VEHICLE = "Weekly Grain Transportation Report PDF archive"
AMS_GTR_ARCHIVE_BASE = "https://www.ams.usda.gov/services/transportation-analysis/gtr/archive"
AMS_GTR_PDF_URL_PATTERN = re.compile(
    r"^https://www\.ams\.usda\.gov/sites/default/files/media/"
    r"GTR(?:DataSet)?[^/]*/\d{4}/[^/]+\.pdf$",
    re.IGNORECASE,
)

AMS_GTR_SAMPLE_START = date(2010, 1, 1)
AMS_GTR_SAMPLE_END = date(2024, 12, 31)

AMS_GTR_YEAR_ARCHIVE_TEMPLATE = (
    "https://www.ams.usda.gov/services/transportation-analysis/gtr/archive-{year}"
)


class AmsGtrNormalizationError(ValueError):
    """AMS GTR bytes or metadata do not satisfy the frozen contract."""


@dataclass(frozen=True)
class AmsGtrReportReference:
    """Source-native reference for a single GTR weekly report."""

    year: int
    report_date: date
    pdf_url: str
    archive_page_url: str

    def __post_init__(self) -> None:
        if not AMS_GTR_SAMPLE_START <= self.report_date <= AMS_GTR_SAMPLE_END:
            raise AmsGtrNormalizationError(
                f"report_date {self.report_date} outside D1 sample period "
                f"[{AMS_GTR_SAMPLE_START}, {AMS_GTR_SAMPLE_END}]"
            )
        if self.year != self.report_date.year:
            raise AmsGtrNormalizationError(
                f"year {self.year} does not match report_date year {self.report_date.year}"
            )


@dataclass(frozen=True)
class AmsGtrArchiveEntry:
    """Captured metadata for a GTR PDF from archive enumeration."""

    report_reference: AmsGtrReportReference
    captured_bytes_sha256: str | None
    capture_status: str
    normalized_text: str | None


def year_archive_url(year: int) -> str:
    """Return the official AMS GTR archive page URL for a given year."""
    if year < 2010 or year > 2026:
        raise AmsGtrNormalizationError(
            f"year {year} outside AMS GTR archive coverage (2010-2026 per source)"
        )
    return AMS_GTR_YEAR_ARCHIVE_TEMPLATE.format(year=year)


def enumerate_d1_years() -> tuple[int, ...]:
    """Return the D1 sample period years for GTR enumeration."""
    return tuple(range(AMS_GTR_SAMPLE_START.year, AMS_GTR_SAMPLE_END.year + 1))


def parse_report_date_from_url(pdf_url: str) -> date | None:
    """Extract report date from a GTR PDF URL if deterministically parseable.

    GTR PDF URLs typically contain date patterns like:
    - GTR01022020.pdf (January 2, 2020 format: MMDDYYYY)
    - GTRJanuary022020.pdf (month name format)
    - 2020/GTR_01_02_2020.pdf (underscore-separated)

    Returns None if date cannot be reliably extracted.
    """
    filename = pdf_url.rsplit("/", 1)[-1].lower()
    filename_base = filename.replace(".pdf", "").replace("gtr", "")

    mmddyyyy_match = re.match(r"^(\d{2})(\d{2})(\d{4})$", filename_base)
    if mmddyyyy_match:
        try:
            month, day, year = map(int, mmddyyyy_match.groups())
            return date(year, month, day)
        except ValueError:
            pass

    month_names = {
        "january": 1, "february": 2, "march": 3, "april": 4,
        "may": 5, "june": 6, "july": 7, "august": 8,
        "september": 9, "october": 10, "november": 11, "december": 12,
    }
    for name, month_num in month_names.items():
        pattern = rf"^{name}(\d{{1,2}})(\d{{4}})$"
        match = re.match(pattern, filename_base)
        if match:
            try:
                day, year = int(match.group(1)), int(match.group(2))
                return date(year, month_num, day)
            except ValueError:
                pass

    filename_stripped = filename_base.lstrip("_")
    underscore_match = re.match(r"^(\d{1,2})_(\d{1,2})_(\d{4})$", filename_stripped)
    if underscore_match:
        try:
            month, day, year = map(int, underscore_match.groups())
            return date(year, month, day)
        except ValueError:
            pass

    return None


def validate_pdf_url(url: str) -> str:
    """Validate that a URL matches the expected AMS GTR PDF pattern."""
    if not isinstance(url, str) or not url.strip():
        raise AmsGtrNormalizationError("PDF URL must be a nonempty string")
    if not url.startswith("https://www.ams.usda.gov/"):
        raise AmsGtrNormalizationError(
            f"PDF URL must be on ams.usda.gov domain: {url}"
        )
    if not url.lower().endswith(".pdf"):
        raise AmsGtrNormalizationError(f"PDF URL must end with .pdf: {url}")
    return url


def construct_report_reference(
    *,
    year: int,
    report_date: date,
    pdf_url: str,
) -> AmsGtrReportReference:
    """Construct a validated GTR report reference."""
    validated_url = validate_pdf_url(pdf_url)
    return AmsGtrReportReference(
        year=year,
        report_date=report_date,
        pdf_url=validated_url,
        archive_page_url=year_archive_url(year),
    )


def extract_pdf_links_from_archive_html(
    raw_html: bytes,
    *,
    year: int,
    content_type: str,
) -> tuple[str, ...]:
    """Extract PDF links from captured AMS GTR year archive HTML.

    This parser extracts href attributes pointing to .pdf files from the
    archive page HTML. It does NOT perform PDF text extraction.
    """
    if not isinstance(raw_html, bytes):
        raise AmsGtrNormalizationError("raw_html must be bytes")
    if not isinstance(content_type, str) or not content_type.strip():
        raise AmsGtrNormalizationError("content_type must be a nonempty string")

    media_type = content_type.split(";", 1)[0].strip().lower()
    if media_type != "text/html":
        raise AmsGtrNormalizationError(
            f"unsupported content_type {content_type!r}; expected text/html"
        )

    try:
        decoded = raw_html.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise AmsGtrNormalizationError(f"HTML decode failed: {exc}") from exc

    href_pattern = re.compile(r'href=["\']([^"\']+\.pdf)["\']', re.IGNORECASE)
    matches = href_pattern.findall(decoded)

    pdf_urls: list[str] = []
    base_url = year_archive_url(year)
    for href in matches:
        if href.startswith("http://") or href.startswith("https://"):
            full_url = href
        else:
            full_url = urljoin(base_url, href)

        if "ams.usda.gov" in full_url.lower() and full_url not in pdf_urls:
            pdf_urls.append(full_url)

    return tuple(sorted(pdf_urls))


def normalize_pdf_text(
    raw_pdf: bytes,
    *,
    content_type: str,
) -> str:
    """Extract and normalize text from a captured GTR PDF.

    This function requires a PDF extraction library (e.g., pdfplumber).
    Returns normalized text suitable for D4 keyword matching.

    IMPORTANT: This function is a stub. PDF text extraction requires
    additional dependencies that must be declared in requirements.txt.
    The actual implementation will use pdfplumber or similar.
    """
    if not isinstance(raw_pdf, bytes):
        raise AmsGtrNormalizationError("raw_pdf must be bytes")
    if not isinstance(content_type, str) or not content_type.strip():
        raise AmsGtrNormalizationError("content_type must be a nonempty string")

    media_type = content_type.split(";", 1)[0].strip().lower()
    if media_type != "application/pdf":
        raise AmsGtrNormalizationError(
            f"unsupported content_type {content_type!r}; expected application/pdf"
        )

    if len(raw_pdf) < 10 or not raw_pdf[:5].startswith(b"%PDF-"):
        raise AmsGtrNormalizationError("raw_pdf does not appear to be a valid PDF")

    raise NotImplementedError(
        "PDF text extraction requires pdfplumber or similar dependency. "
        "Add to requirements.txt and implement extraction logic."
    )


@dataclass(frozen=True)
class AmsGtrSourceRegistration:
    """D3 source registration record for AMS GTR archive."""

    sweep_id: str = "S5"
    authority: str = AMS_GTR_AUTHORITY
    vehicle: str = AMS_GTR_VEHICLE
    archive_base: str = AMS_GTR_ARCHIVE_BASE
    sample_start: date = AMS_GTR_SAMPLE_START
    sample_end: date = AMS_GTR_SAMPLE_END
    enumeration_coverage: str = "weekly_reports_by_year"
    historical_completeness: str = "EXPECTED_COMPLETE"


def get_source_registration() -> AmsGtrSourceRegistration:
    """Return the D3 source registration for AMS GTR."""
    return AmsGtrSourceRegistration()
