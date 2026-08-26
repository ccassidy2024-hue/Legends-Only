"""Data ingestion: load raw sources without mutating immutable raw archives.

Adapters for sweep families:
- S1: USACE NTNI (ntni.py) - ratified
- S3: USCG MSIB (uscg_msib.py) - registered
- S5: AMS GTR (ams_gtr.py) - registered
- S6: USACE LPMS (usace_lpms.py) - registered
- S7: STB dockets (stb_dockets.py) - registered
- S8: Port advisories (port_advisory.py) - registered

S2 (USGS gauges) and S4 (NHC storms) require A+B scientific decisions
before adapters can be implemented.
"""

from grainsys.ingest.ntni import (
    NtniNormalizationError,
    NtniNoticeReference,
    NTNI_AUTHORITY,
    NTNI_DISTRICTS,
    NTNI_VEHICLE,
    district_endpoint,
    normalize_full_text,
    parse_active_notice_listing,
)

from grainsys.ingest.uscg_msib import (
    MsibNormalizationError,
    MsibReference,
    USCG_AUTHORITY,
    MSIB_VEHICLE,
    MSIB_DISTRICTS,
    national_msib_endpoint,
    parse_navcen_msib_listing,
    normalize_full_text_html as msib_normalize_html,
    get_registered_years as msib_get_years,
)

from grainsys.ingest.ams_gtr import (
    GtrNormalizationError,
    GtrReportReference,
    AMS_AUTHORITY,
    GTR_VEHICLE,
    gtr_archive_endpoint,
    parse_gtr_archive_listing,
    get_registered_years as gtr_get_years,
)

from grainsys.ingest.usace_lpms import (
    LpmsNormalizationError,
    LockReference,
    LockQueueRecord,
    LockUnavailabilityRecord,
    USACE_AUTHORITY,
    LPMS_VEHICLE,
    lock_queue_endpoint,
    parse_lock_queue_xml,
    enumerate_operational_outages,
    get_registered_rivers,
    get_registered_locks,
    get_registered_years as lpms_get_years,
)

from grainsys.ingest.stb_dockets import (
    StbNormalizationError,
    StbDocketReference,
    ServiceOrderRecord,
    STB_AUTHORITY,
    STB_VEHICLE,
    docket_search_url,
    enumerate_service_orders,
    get_registered_railroads,
    get_registered_years as stb_get_years,
    get_relevant_docket_types,
)

from grainsys.ingest.port_advisory import (
    PortAdvisoryNormalizationError,
    PortReference,
    TerminalReference,
    PortAdvisoryRecord,
    get_official_archive_ports,
    get_public_notice_terminals,
    port_archive_endpoint,
    is_official_source_supported,
    validate_s4_node_coverage,
    get_registered_years as port_get_years,
)

__all__ = [
    # S1 - NTNI
    "NtniNormalizationError",
    "NtniNoticeReference",
    "NTNI_AUTHORITY",
    "NTNI_DISTRICTS",
    "NTNI_VEHICLE",
    "district_endpoint",
    "normalize_full_text",
    "parse_active_notice_listing",
    # S3 - USCG MSIB
    "MsibNormalizationError",
    "MsibReference",
    "USCG_AUTHORITY",
    "MSIB_VEHICLE",
    "MSIB_DISTRICTS",
    "national_msib_endpoint",
    "parse_navcen_msib_listing",
    "msib_normalize_html",
    "msib_get_years",
    # S5 - AMS GTR
    "GtrNormalizationError",
    "GtrReportReference",
    "AMS_AUTHORITY",
    "GTR_VEHICLE",
    "gtr_archive_endpoint",
    "parse_gtr_archive_listing",
    "gtr_get_years",
    # S6 - LPMS
    "LpmsNormalizationError",
    "LockReference",
    "LockQueueRecord",
    "LockUnavailabilityRecord",
    "USACE_AUTHORITY",
    "LPMS_VEHICLE",
    "lock_queue_endpoint",
    "parse_lock_queue_xml",
    "enumerate_operational_outages",
    "get_registered_rivers",
    "get_registered_locks",
    "lpms_get_years",
    # S7 - STB
    "StbNormalizationError",
    "StbDocketReference",
    "ServiceOrderRecord",
    "STB_AUTHORITY",
    "STB_VEHICLE",
    "docket_search_url",
    "enumerate_service_orders",
    "get_registered_railroads",
    "stb_get_years",
    "get_relevant_docket_types",
    # S8 - Port Advisory
    "PortAdvisoryNormalizationError",
    "PortReference",
    "TerminalReference",
    "PortAdvisoryRecord",
    "get_official_archive_ports",
    "get_public_notice_terminals",
    "port_archive_endpoint",
    "is_official_source_supported",
    "validate_s4_node_coverage",
    "port_get_years",
]
