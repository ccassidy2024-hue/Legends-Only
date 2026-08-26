"""Tests for USDA AMS Grain Transportation Report adapter (S5).

These tests verify:
1. Source registration contract
2. URL construction and validation
3. Date parsing from PDF URLs
4. HTML link extraction
5. Fail-closed behavior on invalid inputs
"""

from __future__ import annotations

from datetime import date

import pytest

from grainsys.ingest.ams_gtr import (
    AMS_GTR_AUTHORITY,
    AMS_GTR_SAMPLE_END,
    AMS_GTR_SAMPLE_START,
    AMS_GTR_VEHICLE,
    AmsGtrNormalizationError,
    AmsGtrReportReference,
    construct_report_reference,
    enumerate_d1_years,
    extract_pdf_links_from_archive_html,
    get_source_registration,
    parse_report_date_from_url,
    validate_pdf_url,
    year_archive_url,
)


class TestSourceRegistration:
    """Test D3 source registration contract."""

    def test_registration_returns_frozen_values(self) -> None:
        reg = get_source_registration()
        assert reg.sweep_id == "S5"
        assert reg.authority == AMS_GTR_AUTHORITY
        assert reg.vehicle == AMS_GTR_VEHICLE
        assert reg.sample_start == AMS_GTR_SAMPLE_START
        assert reg.sample_end == AMS_GTR_SAMPLE_END

    def test_d1_years_match_sample_period(self) -> None:
        years = enumerate_d1_years()
        assert years[0] == 2010
        assert years[-1] == 2024
        assert len(years) == 15
        assert years == tuple(range(2010, 2025))


class TestYearArchiveUrl:
    """Test year archive URL construction."""

    def test_valid_years_produce_correct_urls(self) -> None:
        assert year_archive_url(2020) == (
            "https://www.ams.usda.gov/services/transportation-analysis/"
            "gtr/archive-2020"
        )
        assert year_archive_url(2010) == (
            "https://www.ams.usda.gov/services/transportation-analysis/"
            "gtr/archive-2010"
        )
        assert year_archive_url(2024) == (
            "https://www.ams.usda.gov/services/transportation-analysis/"
            "gtr/archive-2024"
        )

    def test_year_before_archive_raises(self) -> None:
        with pytest.raises(AmsGtrNormalizationError, match="outside AMS GTR archive"):
            year_archive_url(2009)

    def test_year_after_coverage_raises(self) -> None:
        with pytest.raises(AmsGtrNormalizationError, match="outside AMS GTR archive"):
            year_archive_url(2027)


class TestPdfUrlValidation:
    """Test PDF URL validation."""

    def test_valid_ams_pdf_url(self) -> None:
        url = "https://www.ams.usda.gov/sites/default/files/media/GTR01022020.pdf"
        assert validate_pdf_url(url) == url

    def test_non_ams_domain_raises(self) -> None:
        with pytest.raises(AmsGtrNormalizationError, match="ams.usda.gov domain"):
            validate_pdf_url("https://example.com/report.pdf")

    def test_non_pdf_extension_raises(self) -> None:
        with pytest.raises(AmsGtrNormalizationError, match="must end with .pdf"):
            validate_pdf_url("https://www.ams.usda.gov/page.html")

    def test_empty_url_raises(self) -> None:
        with pytest.raises(AmsGtrNormalizationError, match="nonempty string"):
            validate_pdf_url("")

    def test_non_string_raises(self) -> None:
        with pytest.raises(AmsGtrNormalizationError, match="nonempty string"):
            validate_pdf_url(None)  # type: ignore[arg-type]


class TestReportDateParsing:
    """Test date extraction from PDF URLs."""

    def test_mmddyyyy_format(self) -> None:
        url = "https://www.ams.usda.gov/sites/default/files/GTR01022020.pdf"
        result = parse_report_date_from_url(url)
        assert result == date(2020, 1, 2)

    def test_month_name_format(self) -> None:
        url = "https://www.ams.usda.gov/files/GTRJanuary022020.pdf"
        result = parse_report_date_from_url(url)
        assert result == date(2020, 1, 2)

    def test_underscore_format(self) -> None:
        url = "https://www.ams.usda.gov/files/GTR_01_02_2020.pdf"
        result = parse_report_date_from_url(url)
        assert result == date(2020, 1, 2)

    def test_unparseable_returns_none(self) -> None:
        url = "https://www.ams.usda.gov/files/unknown_format.pdf"
        assert parse_report_date_from_url(url) is None


class TestReportReference:
    """Test report reference construction and validation."""

    def test_valid_reference(self) -> None:
        ref = construct_report_reference(
            year=2020,
            report_date=date(2020, 1, 2),
            pdf_url="https://www.ams.usda.gov/files/GTR01022020.pdf",
        )
        assert ref.year == 2020
        assert ref.report_date == date(2020, 1, 2)
        assert "GTR01022020.pdf" in ref.pdf_url
        assert "archive-2020" in ref.archive_page_url

    def test_date_outside_sample_period_raises(self) -> None:
        with pytest.raises(AmsGtrNormalizationError, match="outside D1 sample period"):
            AmsGtrReportReference(
                year=2009,
                report_date=date(2009, 1, 1),
                pdf_url="https://www.ams.usda.gov/files/GTR01012009.pdf",
                archive_page_url="https://www.ams.usda.gov/gtr/archive-2009",
            )

    def test_year_date_mismatch_raises(self) -> None:
        with pytest.raises(AmsGtrNormalizationError, match="does not match"):
            construct_report_reference(
                year=2020,
                report_date=date(2021, 1, 1),
                pdf_url="https://www.ams.usda.gov/files/GTR01012021.pdf",
            )


class TestHtmlLinkExtraction:
    """Test PDF link extraction from archive HTML."""

    def test_extracts_pdf_links(self) -> None:
        html = b"""
        <html>
        <body>
        <a href="https://www.ams.usda.gov/files/GTR01022020.pdf">Jan 2</a>
        <a href="https://www.ams.usda.gov/files/GTR01092020.pdf">Jan 9</a>
        </body>
        </html>
        """
        links = extract_pdf_links_from_archive_html(
            html, year=2020, content_type="text/html"
        )
        assert len(links) == 2
        assert "GTR01022020.pdf" in links[0] or "GTR01022020.pdf" in links[1]

    def test_deduplicates_links(self) -> None:
        html = b"""
        <html>
        <a href="https://www.ams.usda.gov/files/GTR01022020.pdf">Link 1</a>
        <a href="https://www.ams.usda.gov/files/GTR01022020.pdf">Link 2</a>
        </html>
        """
        links = extract_pdf_links_from_archive_html(
            html, year=2020, content_type="text/html"
        )
        assert len(links) == 1

    def test_filters_non_ams_links(self) -> None:
        html = b"""
        <html>
        <a href="https://www.ams.usda.gov/files/GTR01022020.pdf">AMS</a>
        <a href="https://example.com/other.pdf">Other</a>
        </html>
        """
        links = extract_pdf_links_from_archive_html(
            html, year=2020, content_type="text/html"
        )
        assert len(links) == 1
        assert "ams.usda.gov" in links[0]

    def test_non_html_content_type_raises(self) -> None:
        with pytest.raises(AmsGtrNormalizationError, match="expected text/html"):
            extract_pdf_links_from_archive_html(
                b"<html></html>", year=2020, content_type="application/json"
            )

    def test_non_bytes_raises(self) -> None:
        with pytest.raises(AmsGtrNormalizationError, match="must be bytes"):
            extract_pdf_links_from_archive_html(
                "<html></html>", year=2020, content_type="text/html"  # type: ignore[arg-type]
            )


class TestSamplePeriodBoundaries:
    """Test D1 sample period boundary enforcement."""

    def test_sample_start_is_2010_01_01(self) -> None:
        assert AMS_GTR_SAMPLE_START == date(2010, 1, 1)

    def test_sample_end_is_2024_12_31(self) -> None:
        assert AMS_GTR_SAMPLE_END == date(2024, 12, 31)

    def test_reference_at_sample_start_valid(self) -> None:
        ref = construct_report_reference(
            year=2010,
            report_date=date(2010, 1, 1),
            pdf_url="https://www.ams.usda.gov/files/GTR01012010.pdf",
        )
        assert ref.report_date == date(2010, 1, 1)

    def test_reference_at_sample_end_valid(self) -> None:
        ref = construct_report_reference(
            year=2024,
            report_date=date(2024, 12, 31),
            pdf_url="https://www.ams.usda.gov/files/GTR12312024.pdf",
        )
        assert ref.report_date == date(2024, 12, 31)

    def test_reference_after_sample_end_raises(self) -> None:
        with pytest.raises(AmsGtrNormalizationError, match="outside D1 sample period"):
            construct_report_reference(
                year=2025,
                report_date=date(2025, 1, 1),
                pdf_url="https://www.ams.usda.gov/files/GTR01012025.pdf",
            )
