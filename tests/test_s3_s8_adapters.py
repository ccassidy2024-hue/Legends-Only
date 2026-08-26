"""Synthetic tests for S3-S8 positive-evidence-only adapters.

Tests cover:
- S3: USCG MSIB (uscg_msib.py)
- S5: AMS GTR (ams_gtr.py)
- S6: USACE LPMS (usace_lpms.py)
- S7: STB dockets (stb_dockets.py)
- S8: Port advisories (port_advisory.py)
"""

from __future__ import annotations

from datetime import date

import pytest

# S5 - AMS GTR
from grainsys.ingest.ams_gtr import (
    GTR_SAMPLE_END_YEAR,
    GTR_SAMPLE_START_YEAR,
    GtrNormalizationError,
    extract_date_from_pdf_filename,
    gtr_archive_endpoint,
    parse_report_date,
)
from grainsys.ingest.ams_gtr import (
    get_registered_years as gtr_get_years,
)

# S8 - Port advisories
from grainsys.ingest.port_advisory import (
    PORT_AUTHORITIES,
    TERMINAL_OPERATORS,
    PortAdvisoryNormalizationError,
    PortReference,
    TerminalReference,
    get_official_archive_ports,
    get_public_notice_terminals,
    is_grain_corridor_port,
    is_official_source_supported,
    validate_s4_node_coverage,
)
from grainsys.ingest.port_advisory import (
    get_registered_years as port_get_years,
)

# S7 - STB dockets
from grainsys.ingest.stb_dockets import (
    CLASS_I_GRAIN_RAILROADS,
    STB_RELEVANT_DOCKET_PREFIXES,
    StbNormalizationError,
    docket_search_url,
    get_registered_railroads,
    is_grain_relevant_docket,
    parse_docket_number,
)

# S6 - USACE LPMS
from grainsys.ingest.usace_lpms import (
    LPMS_GRAIN_CORRIDOR_LOCKS,
    LPMS_RIVERS,
    LockReference,
    LpmsNormalizationError,
    get_registered_locks,
    get_registered_rivers,
    lock_queue_endpoint,
    parse_lock_queue_xml,
)

# S3 - USCG MSIB
from grainsys.ingest.uscg_msib import (
    MSIB_DISTRICTS,
    MSIB_SAMPLE_END_YEAR,
    MSIB_SAMPLE_START_YEAR,
    MsibNormalizationError,
    district_covers_basin,
    get_registered_years,
    national_msib_endpoint,
    parse_msib_number,
)

# =============================================================================
# S3 - USCG MSIB Tests
# =============================================================================

class TestUscgMsib:
    """Tests for S3 USCG MSIB adapter."""

    def test_msib_districts_cover_grain_corridors(self) -> None:
        """MSIB districts cover registered grain navigation basins."""
        assert len(MSIB_DISTRICTS) >= 4
        basins = {basin for _, _, basin in MSIB_DISTRICTS}
        assert "lower_mississippi" in basins
        assert "ohio" in basins
        assert "columbia_snake" in basins

    def test_national_msib_endpoint_for_valid_year(self) -> None:
        """Endpoint generation succeeds for registered sample years."""
        url = national_msib_endpoint(2022)
        assert "navcen.uscg.gov/msib-national" in url
        assert "field_msib_year_value=22" in url

    def test_national_msib_endpoint_rejects_invalid_year(self) -> None:
        """Endpoint generation fails for years outside sample period."""
        with pytest.raises(MsibNormalizationError, match="outside the registered"):
            national_msib_endpoint(2000)  # Before sample start

    def test_parse_msib_number_standard_format(self) -> None:
        """MSIB number parsing handles standard format."""
        num, year = parse_msib_number("04-26")
        assert num == 4
        assert year == 26

    def test_parse_msib_number_with_prefix(self) -> None:
        """MSIB number parsing handles MSIB prefix."""
        num, year = parse_msib_number("MSIB 03-26")
        assert num == 3
        assert year == 26

    def test_parse_msib_number_underscore_format(self) -> None:
        """MSIB number parsing handles underscore format."""
        num, year = parse_msib_number("018_14")
        assert num == 18
        assert year == 14

    def test_get_registered_years_covers_sample_period(self) -> None:
        """Registered years cover full sample period."""
        years = get_registered_years()
        assert min(years) == MSIB_SAMPLE_START_YEAR
        assert max(years) == MSIB_SAMPLE_END_YEAR
        assert len(years) == MSIB_SAMPLE_END_YEAR - MSIB_SAMPLE_START_YEAR + 1

    def test_district_covers_basin_positive(self) -> None:
        """District basin coverage returns True for registered pairs."""
        assert district_covers_basin("D8", "lower_mississippi")

    def test_district_covers_basin_negative(self) -> None:
        """District basin coverage returns False for unregistered pairs."""
        assert not district_covers_basin("D8", "columbia_snake")


# =============================================================================
# S5 - AMS GTR Tests
# =============================================================================

class TestAmsGtr:
    """Tests for S5 AMS GTR adapter."""

    def test_gtr_archive_endpoint_for_valid_year(self) -> None:
        """Archive endpoint generation succeeds for registered years."""
        url = gtr_archive_endpoint(2024)
        assert "ams.usda.gov" in url
        assert "gtr/archive-2024" in url

    def test_gtr_archive_endpoint_rejects_invalid_year(self) -> None:
        """Archive endpoint fails for years outside sample period."""
        with pytest.raises(GtrNormalizationError, match="outside the registered"):
            gtr_archive_endpoint(2000)

    def test_parse_report_date_standard_format(self) -> None:
        """Report date parsing handles standard format."""
        d = parse_report_date("December 26, 2024")
        assert d == date(2024, 12, 26)

    def test_parse_report_date_no_comma(self) -> None:
        """Report date parsing handles format without comma."""
        d = parse_report_date("January 4 2024")
        assert d == date(2024, 1, 4)

    def test_extract_date_from_pdf_filename(self) -> None:
        """Date extraction from GTR PDF filename."""
        d = extract_date_from_pdf_filename("GTR10242024.pdf")
        assert d == date(2024, 10, 24)

    def test_extract_date_from_pdf_filename_with_path(self) -> None:
        """Date extraction handles full URL path."""
        d = extract_date_from_pdf_filename(
            "https://www.ams.usda.gov/sites/default/files/media/GTR01042024.pdf"
        )
        assert d == date(2024, 1, 4)

    def test_get_registered_years_covers_sample_period(self) -> None:
        """Registered years cover full sample period."""
        years = gtr_get_years()
        assert min(years) == GTR_SAMPLE_START_YEAR
        assert max(years) == GTR_SAMPLE_END_YEAR


# =============================================================================
# S6 - USACE LPMS Tests
# =============================================================================

class TestUsaceLpms:
    """Tests for S6 USACE LPMS adapter."""

    def test_lpms_rivers_cover_grain_corridors(self) -> None:
        """LPMS rivers include registered grain navigation basins."""
        river_codes = {code for code, _ in LPMS_RIVERS}
        assert "MS" in river_codes  # Mississippi
        assert "OH" in river_codes  # Ohio
        assert "IL" in river_codes  # Illinois

    def test_lpms_locks_have_registered_grain_corridors(self) -> None:
        """LPMS locks include key grain corridor locks."""
        assert len(LPMS_GRAIN_CORRIDOR_LOCKS) >= 10
        lock_names = {name for _, _, name in LPMS_GRAIN_CORRIDOR_LOCKS}
        # Should include key locks
        assert any("27" in name or "Chain of Rocks" in name for name in lock_names)

    def test_lock_queue_endpoint_for_valid_river(self) -> None:
        """Lock queue endpoint generation succeeds for registered rivers."""
        url = lock_queue_endpoint("MS", "27")
        assert "corpslocks.usace.army.mil" in url
        assert "in_river=MS" in url
        assert "in_lock=27" in url

    def test_lock_queue_endpoint_rejects_invalid_river(self) -> None:
        """Lock queue endpoint fails for unregistered rivers."""
        with pytest.raises(LpmsNormalizationError, match="outside the registered"):
            lock_queue_endpoint("INVALID", "99")

    def test_parse_lock_queue_xml_valid(self) -> None:
        """Lock queue XML parsing handles valid response."""
        xml = b"""<?xml version="1.0"?>
        <rowset>
          <row>
            <vessel_name>TEST VESSEL</vessel_name>
            <vessel_no>12345</vessel_no>
            <direction>UP</direction>
            <num_barges>15</num_barges>
            <arrival_date>2024-10-15 08:00</arrival_date>
            <end_of_lockage>2024-10-15 09:30</end_of_lockage>
          </row>
        </rowset>"""
        records = parse_lock_queue_xml(xml, lock_code="27")
        assert len(records) == 1
        assert records[0].vessel_name == "TEST VESSEL"
        assert records[0].num_barges == 15

    def test_parse_lock_queue_xml_empty(self) -> None:
        """Lock queue XML parsing handles empty response."""
        xml = b"""<?xml version="1.0"?><rowset></rowset>"""
        records = parse_lock_queue_xml(xml, lock_code="27")
        assert records == ()

    def test_get_registered_rivers(self) -> None:
        """Get registered rivers returns expected set."""
        rivers = get_registered_rivers()
        assert len(rivers) >= 6
        assert ("MS", "Mississippi River") in rivers

    def test_get_registered_locks(self) -> None:
        """Get registered locks returns LockReference objects."""
        locks = get_registered_locks()
        assert all(isinstance(lock, LockReference) for lock in locks)
        assert len(locks) >= 10


# =============================================================================
# S7 - STB Dockets Tests
# =============================================================================

class TestStbDockets:
    """Tests for S7 STB dockets adapter."""

    def test_class_i_railroads_include_grain_carriers(self) -> None:
        """Class I railroads include major grain carriers."""
        codes = {code for code, _ in CLASS_I_GRAIN_RAILROADS}
        assert "BNSF" in codes
        assert "UP" in codes
        assert "NS" in codes
        assert "CSX" in codes

    def test_relevant_docket_prefixes(self) -> None:
        """Relevant docket types include EP (exemption proceedings)."""
        assert "EP" in STB_RELEVANT_DOCKET_PREFIXES

    def test_docket_search_url_for_valid_prefix(self) -> None:
        """Docket search URL generation succeeds for valid prefix."""
        url = docket_search_url("EP", year=2024)
        assert "stb.gov" in url
        assert "docket_type=EP" in url
        assert "year=2024" in url

    def test_docket_search_url_rejects_invalid_prefix(self) -> None:
        """Docket search URL fails for invalid prefix."""
        with pytest.raises(StbNormalizationError, match="outside the registered"):
            docket_search_url("INVALID")

    def test_parse_docket_number_standard(self) -> None:
        """Docket number parsing handles standard format."""
        prefix, num = parse_docket_number("EP 772")
        assert prefix == "EP"
        assert num == 772

    def test_parse_docket_number_with_dash(self) -> None:
        """Docket number parsing handles dash format."""
        prefix, num = parse_docket_number("STB-12345")
        assert prefix == "STB"
        assert num == 12345

    def test_is_grain_relevant_docket_title_match(self) -> None:
        """Grain relevance detection by title keywords."""
        assert is_grain_relevant_docket(
            "Oversight of Grain Shuttle Car Supply",
            parties=()
        )
        assert is_grain_relevant_docket(
            "Agricultural Transportation Service",
            parties=()
        )

    def test_is_grain_relevant_docket_railroad_match(self) -> None:
        """Grain relevance detection by railroad party."""
        assert is_grain_relevant_docket(
            "Service Proceeding",
            parties=("BNSF Railway Company",)
        )

    def test_is_grain_relevant_docket_negative(self) -> None:
        """Grain relevance returns False for unrelated dockets."""
        assert not is_grain_relevant_docket(
            "Pipeline Rate Case",
            parties=("Generic Pipeline Company",)
        )

    def test_get_registered_railroads(self) -> None:
        """Get registered railroads returns expected set."""
        railroads = get_registered_railroads()
        assert len(railroads) >= 6
        assert ("BNSF", "BNSF Railway") in railroads


# =============================================================================
# S8 - Port Advisory Tests
# =============================================================================

class TestPortAdvisory:
    """Tests for S8 port advisory adapter."""

    def test_port_authorities_include_grain_export_ports(self) -> None:
        """Port authorities include major grain export ports."""
        codes = {code for code, _, _, _ in PORT_AUTHORITIES}
        assert "NOLA" in codes  # New Orleans
        assert "HST" in codes   # Houston
        assert "PDX" in codes   # Portland

    def test_terminal_operators_exclude_temco_kalama(self) -> None:
        """Terminal operators exclude TEMCO Kalama (corporate-only)."""
        for code, name, _, _ in TERMINAL_OPERATORS:
            assert "TEMCO" not in code
            assert "Kalama" not in name

    def test_get_official_archive_ports(self) -> None:
        """Get official archive ports returns PortReference objects."""
        ports = get_official_archive_ports()
        assert all(isinstance(p, PortReference) for p in ports)
        assert all(p.archive_status == "official_archive" for p in ports)

    def test_get_public_notice_terminals(self) -> None:
        """Get public notice terminals returns TerminalReference objects."""
        terminals = get_public_notice_terminals()
        assert all(isinstance(t, TerminalReference) for t in terminals)
        assert all(t.archive_status == "public_notices" for t in terminals)

    def test_is_official_source_supported_positive(self) -> None:
        """Official source support returns True for registered ports."""
        assert is_official_source_supported("NOLA")
        assert is_official_source_supported("HST")

    def test_is_official_source_supported_negative(self) -> None:
        """Official source support returns False for unregistered ports."""
        assert not is_official_source_supported("INVALID")

    def test_is_grain_corridor_port(self) -> None:
        """Grain corridor port detection."""
        assert is_grain_corridor_port("NOLA")  # Lower Mississippi
        assert is_grain_corridor_port("PDX")   # Columbia-Snake

    def test_validate_s4_node_coverage(self) -> None:
        """S4 node coverage validation."""
        coverage = validate_s4_node_coverage(["NOLA", "HST", "INVALID"])
        assert coverage["NOLA"] is True
        assert coverage["HST"] is True
        assert coverage["INVALID"] is False

    def test_get_registered_years(self) -> None:
        """Get registered years returns expected range."""
        years = port_get_years()
        assert 2010 in years
        assert 2024 in years


# =============================================================================
# Cross-Adapter Integration Tests
# =============================================================================

class TestCrossAdapterIntegration:
    """Integration tests across S3-S8 adapters."""

    def test_all_adapters_use_consistent_sample_period(self) -> None:
        """All adapters use consistent sample period 2010-2024."""
        from grainsys.ingest.ams_gtr import GTR_SAMPLE_END_YEAR, GTR_SAMPLE_START_YEAR
        from grainsys.ingest.port_advisory import PORT_SAMPLE_END_YEAR, PORT_SAMPLE_START_YEAR
        from grainsys.ingest.stb_dockets import STB_SAMPLE_END_YEAR, STB_SAMPLE_START_YEAR
        from grainsys.ingest.usace_lpms import LPMS_SAMPLE_END_YEAR, LPMS_SAMPLE_START_YEAR
        from grainsys.ingest.uscg_msib import MSIB_SAMPLE_END_YEAR, MSIB_SAMPLE_START_YEAR

        starts = {
            MSIB_SAMPLE_START_YEAR,
            GTR_SAMPLE_START_YEAR,
            LPMS_SAMPLE_START_YEAR,
            STB_SAMPLE_START_YEAR,
            PORT_SAMPLE_START_YEAR,
        }
        ends = {
            MSIB_SAMPLE_END_YEAR,
            GTR_SAMPLE_END_YEAR,
            LPMS_SAMPLE_END_YEAR,
            STB_SAMPLE_END_YEAR,
            PORT_SAMPLE_END_YEAR,
        }

        assert starts == {2010}, f"Inconsistent start years: {starts}"
        assert ends == {2024}, f"Inconsistent end years: {ends}"

    def test_all_adapters_use_fail_closed_error_classes(self) -> None:
        """All adapters define fail-closed error classes."""
        # All error classes should be ValueError subclasses
        # (classes already imported at module level)
        assert issubclass(MsibNormalizationError, ValueError)
        assert issubclass(GtrNormalizationError, ValueError)
        assert issubclass(LpmsNormalizationError, ValueError)
        assert issubclass(StbNormalizationError, ValueError)
        assert issubclass(PortAdvisoryNormalizationError, ValueError)

    def test_all_adapters_define_authority_constants(self) -> None:
        """All adapters define authority constants."""
        from grainsys.ingest.ams_gtr import AMS_AUTHORITY
        from grainsys.ingest.stb_dockets import STB_AUTHORITY
        from grainsys.ingest.usace_lpms import USACE_AUTHORITY
        from grainsys.ingest.uscg_msib import USCG_AUTHORITY

        assert "Coast Guard" in USCG_AUTHORITY
        assert "Marketing Service" in AMS_AUTHORITY
        assert "Army Corps" in USACE_AUTHORITY
        assert "Transportation Board" in STB_AUTHORITY
