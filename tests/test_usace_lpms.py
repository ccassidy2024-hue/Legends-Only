"""Tests for USACE LPMS adapter (S6).

These tests verify:
1. Source registration contract
2. D2 lock universe derivation
3. Coverage status determination (COVERED vs UNKNOWN)
4. D8 mode enforcement (binding_operational_restriction_only)
5. Fail-closed behavior on invalid inputs
"""

from __future__ import annotations

from datetime import date

import pytest

from grainsys.ingest.usace_lpms import (
    D2_NAVIGATION_BASINS,
    LPMS_ARCHIVE_END_YEAR,
    LPMS_ARCHIVE_START_YEAR,
    LPMS_AUTHORITY,
    LPMS_SAMPLE_END,
    LPMS_SAMPLE_START,
    LPMS_VEHICLE,
    LpmsCoverageStatus,
    LpmsLockReference,
    LpmsNormalizationError,
    LpmsUnavailabilityRecord,
    LpmsYearCoverage,
    annual_unavailability_report_url,
    derive_d2_lock_universe,
    enumerate_d1_years_with_coverage,
    get_source_registration,
    parse_unavailability_hours,
    validate_lock_in_d2_scope,
)


class TestSourceRegistration:
    """Test D3 source registration contract."""

    def test_registration_returns_frozen_values(self) -> None:
        reg = get_source_registration()
        assert reg.sweep_id == "S6"
        assert reg.authority == LPMS_AUTHORITY
        assert reg.vehicle == LPMS_VEHICLE
        assert reg.sample_start == LPMS_SAMPLE_START
        assert reg.sample_end == LPMS_SAMPLE_END

    def test_d8_mode_is_binding_operational_restriction_only(self) -> None:
        reg = get_source_registration()
        assert reg.d8_mode == "binding_operational_restriction_only"

    def test_archive_years_documented(self) -> None:
        reg = get_source_registration()
        assert reg.archive_start_year == 2016
        assert reg.archive_end_year == 2025


class TestD2LockUniverse:
    """Test D2 navigation basin derivation."""

    def test_returns_frozen_d2_basins(self) -> None:
        basins = derive_d2_lock_universe()
        assert basins == D2_NAVIGATION_BASINS
        assert len(basins) == 6

    def test_expected_basins_present(self) -> None:
        basins = derive_d2_lock_universe()
        expected = {
            "lower_mississippi",
            "middle_mississippi",
            "upper_mississippi",
            "ohio",
            "illinois",
            "columbia_snake",
        }
        assert set(basins) == expected


class TestYearCoverage:
    """Test LPMS archive coverage by year."""

    def test_d1_years_enumerated_with_coverage(self) -> None:
        years_coverage = enumerate_d1_years_with_coverage()
        assert len(years_coverage) == 15  # 2010-2024

    def test_2010_to_2015_unknown(self) -> None:
        years_coverage = dict(enumerate_d1_years_with_coverage())
        for year in range(2010, 2016):
            assert years_coverage[year] == LpmsCoverageStatus.UNKNOWN

    def test_2016_to_2024_covered(self) -> None:
        years_coverage = dict(enumerate_d1_years_with_coverage())
        for year in range(2016, 2025):
            assert years_coverage[year] == LpmsCoverageStatus.COVERED

    def test_year_coverage_class_for_covered(self) -> None:
        coverage = LpmsYearCoverage.for_year(2020)
        assert coverage.status == LpmsCoverageStatus.COVERED
        assert "available" in coverage.reason.lower()

    def test_year_coverage_class_for_unknown(self) -> None:
        coverage = LpmsYearCoverage.for_year(2012)
        assert coverage.status == LpmsCoverageStatus.UNKNOWN
        assert "no data" in coverage.reason.lower()


class TestReportUrl:
    """Test report URL construction."""

    def test_valid_year_produces_url(self) -> None:
        url = annual_unavailability_report_url(2020)
        assert "corps-locks" in url
        assert "p_year=2020" in url

    def test_year_before_archive_raises(self) -> None:
        with pytest.raises(LpmsNormalizationError, match="outside LPMS archive"):
            annual_unavailability_report_url(2015)

    def test_year_after_archive_raises(self) -> None:
        with pytest.raises(LpmsNormalizationError, match="outside LPMS archive"):
            annual_unavailability_report_url(2030)


class TestLockReference:
    """Test lock reference validation."""

    def test_valid_lock_reference(self) -> None:
        ref = LpmsLockReference(
            lock_id="L52",
            lock_name="Lock 52",
            river="Ohio River",
            navigation_basin="ohio",
            river_mile=962.2,
        )
        assert ref.lock_id == "L52"
        assert ref.navigation_basin == "ohio"

    def test_empty_lock_id_raises(self) -> None:
        with pytest.raises(LpmsNormalizationError, match="lock_id must be nonempty"):
            LpmsLockReference(
                lock_id="",
                lock_name="Test Lock",
                river="Ohio",
                navigation_basin="ohio",
                river_mile=100.0,
            )

    def test_invalid_basin_raises(self) -> None:
        with pytest.raises(LpmsNormalizationError, match="not in D2 scope"):
            LpmsLockReference(
                lock_id="L99",
                lock_name="Test Lock",
                river="Hudson River",
                navigation_basin="hudson",
                river_mile=50.0,
            )


class TestUnavailabilityRecord:
    """Test unavailability record validation."""

    def test_valid_record(self) -> None:
        rec = LpmsUnavailabilityRecord(
            lock_id="L52",
            year=2020,
            unavailable_hours=240.5,
            scheduled_hours=120.0,
            unscheduled_hours=120.5,
            total_hours_year=8760.0,
        )
        assert rec.unavailable_hours == 240.5

    def test_year_outside_archive_raises(self) -> None:
        with pytest.raises(LpmsNormalizationError, match="outside LPMS archive"):
            LpmsUnavailabilityRecord(
                lock_id="L52",
                year=2012,
                unavailable_hours=100.0,
                scheduled_hours=50.0,
                unscheduled_hours=50.0,
                total_hours_year=8760.0,
            )

    def test_negative_hours_raises(self) -> None:
        with pytest.raises(LpmsNormalizationError, match="cannot be negative"):
            LpmsUnavailabilityRecord(
                lock_id="L52",
                year=2020,
                unavailable_hours=-10.0,
                scheduled_hours=None,
                unscheduled_hours=None,
                total_hours_year=8760.0,
            )


class TestHoursParsing:
    """Test unavailability hours parsing."""

    def test_numeric_value(self) -> None:
        assert parse_unavailability_hours("1234.5") == 1234.5

    def test_comma_separated(self) -> None:
        assert parse_unavailability_hours("1,234.5") == 1234.5

    def test_dash_means_zero(self) -> None:
        assert parse_unavailability_hours("-") == 0.0

    def test_empty_means_zero(self) -> None:
        assert parse_unavailability_hours("") == 0.0

    def test_na_means_zero(self) -> None:
        assert parse_unavailability_hours("N/A") == 0.0

    def test_invalid_raises(self) -> None:
        with pytest.raises(LpmsNormalizationError, match="cannot parse"):
            parse_unavailability_hours("abc")


class TestD2ScopeValidation:
    """Test D2 scope validation for locks."""

    def test_ohio_river_in_scope(self) -> None:
        assert validate_lock_in_d2_scope("Ohio River", "Louisville District")

    def test_upper_mississippi_in_scope(self) -> None:
        assert validate_lock_in_d2_scope("Upper Mississippi", "St. Paul District")

    def test_columbia_in_scope(self) -> None:
        assert validate_lock_in_d2_scope("Columbia River", "Portland District")

    def test_unrelated_river_not_in_scope(self) -> None:
        assert not validate_lock_in_d2_scope("Hudson River", "New York District")


class TestSamplePeriodBoundaries:
    """Test D1 sample period boundary enforcement."""

    def test_sample_start_is_2010_01_01(self) -> None:
        assert LPMS_SAMPLE_START == date(2010, 1, 1)

    def test_sample_end_is_2024_12_31(self) -> None:
        assert LPMS_SAMPLE_END == date(2024, 12, 31)

    def test_archive_starts_2016(self) -> None:
        assert LPMS_ARCHIVE_START_YEAR == 2016

    def test_archive_ends_2025(self) -> None:
        assert LPMS_ARCHIVE_END_YEAR == 2025


class TestD8ModeEnforcement:
    """Test D8 binding_operational_restriction_only mode."""

    def test_registration_mode_matches_prereg_rules(self) -> None:
        reg = get_source_registration()
        assert reg.d8_mode == "binding_operational_restriction_only"

    def test_enumeration_coverage_documents_unknown(self) -> None:
        reg = get_source_registration()
        assert "UNKNOWN" in reg.enumeration_coverage
        assert "2010" in reg.enumeration_coverage
        assert "2015" in reg.enumeration_coverage
