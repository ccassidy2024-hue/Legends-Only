"""Deterministic checks for the PR42 S4 binding-correction proposal packet."""

from __future__ import annotations

import hashlib
import json
import math
import re
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[1]
PROPOSALS = REPO / "research" / "episodes" / "discovery" / "proposals"
LIVE_PREREG = REPO / "config" / "discovery" / "prereg_rules.yaml"
PRODUCTION_MANIFEST = REPO / "config" / "discovery" / "prereg_ratification_manifest.yaml"
GOVERNANCE_PY = REPO / "src" / "grainsys" / "discovery" / "governance.py"

PACKET_FILES = (
    "S4_CORRECTION_PACKET_MANIFEST.yaml",
    "S4_FACILITY_BINDING.yaml",
    "S4_DISTANCE_CONTRACT.yaml",
    "S4_DELTA_BALLOT.yaml",
    "FULL_CONFIG_B100_S4_CORRECTED.yaml",
    "s4_correction_packet.schema.yaml",
    "S4_JOIN_RULES.yaml",
    "S4_SOURCE_RETRIEVAL_PROVENANCE.yaml",
    "S4_UNMATCHED_AND_EXPANSIONS.yaml",
    "S4_CENSUS_A_WCSC_D2GRAIN_DOCK_COMMPURP.yaml",
    "S4_CENSUS_B_WCSC_D2GRAIN_DOCK_COMMODITIES.yaml",
    "S4_CENSUS_C_WCSC_D2GRAIN_EXPORT_BASINS.yaml",
    "S4_DISTANCE_POINT_ONLY.yaml",
    "S4_DISTANCE_SEGMENT.yaml",
)

HISTORICAL_B100 = "9e937523d31bc324d9b33628ffd81c78fb74e5141aab2d18174a1677da8ce3c1"
CORRECTED_B100 = "f13589a240316c8d287bf25c63af9439bf5f52619175cbabbe6747f77c378551"
CENSUS_A_SHA = "0b38e45c31b6c3ef258cb63e39deaab51e819f70079d37c4b3efede531d0a37b"
CENSUS_B_SHA = "1c219297b0df6d1ddfe51318628893c9e9216681e2a04dfc78ae37bedc5ab9d3"
CENSUS_C_SHA = "294a38860e275b906312934eb9998a79972f089cc6c4f48705d3be4722412ff4"
EARTH_RADIUS_M = 1852 * 10800 / math.pi
LIVE_D2 = (
    "lower_mississippi",
    "middle_mississippi",
    "upper_mississippi",
    "ohio",
    "illinois",
    "columbia_snake",
)
EXPORT_BASINS = ("lower_mississippi", "columbia_snake")
FORBIDDEN_DEFAULT_TOKENS = (
    "texas_gulf",
    "texas_gulf_coast",
    "gulf_texas",
    "puget_sound",
    "PUGET_SOUND",
    "NORTH_TEXAS",
    "SOUTH_TEXAS",
    "great_lakes",
    "GULF-01",
    "GULF-02",
    "GULF-03",
    "GULF-04",
    "GULF-05",
    "PNW-01",
    "PNW-02",
    "PNW-03",
    "PNW-04",
    "PNW-05",
)
FORBIDDEN_ENDPOINTS = (
    "https://www.navcen.uscg.gov/msib",
    "https://corpslocks.usace.army.mil/",
    "https://portnola.com/notices",
)


def _load(name: str) -> dict:
    path = PROPOSALS / name
    with path.open(encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    assert isinstance(data, dict), name
    return data


def _sha256(name: str) -> str:
    return hashlib.sha256((PROPOSALS / name).read_bytes()).hexdigest()


def _features(name: str) -> dict[str, dict]:
    data = json.loads((PROPOSALS / "s4_sources" / name).read_text(encoding="utf-8"))
    out: dict[str, dict] = {}
    for feat in data["features"]:
        attrs = feat["attributes"]
        out[attrs["NAV_UNIT_ID"]] = attrs
    return out


def _reconstruct_rows() -> tuple[list[dict], list[dict], list[dict], int]:
    rules = _load("S4_JOIN_RULES.yaml")
    wtwy = rules["wtwy_name_to_d2_basin"]
    rx = re.compile(rules["grain_token_regex"], re.I)
    union = _features("usace_bts_docks_query_grain.json")
    for nid, attrs in _features("usace_bts_docks_query_d2_commodity_tokens.json").items():
        union.setdefault(nid, attrs)

    def grain_in(text: str | None) -> bool:
        return bool(rx.search(text or ""))

    rows_a: list[dict] = []
    unmatched = 0
    for attrs in union.values():
        comm = attrs.get("COMMODITIES") or ""
        purpose = attrs.get("PURPOSE") or ""
        if not (grain_in(comm) or grain_in(purpose)):
            continue
        lat, lon = attrs.get("LATITUDE"), attrs.get("LONGITUDE")
        basin = wtwy.get(attrs.get("WTWY_NAME"))
        if attrs.get("FAC_TYPE") != "Dock" or basin is None or lat in (None, 0) or lon in (None, 0):
            unmatched += 1
            continue
        rows_a.append(attrs)
    rows_b = [row for row in rows_a if grain_in(row.get("COMMODITIES") or "")]
    rows_c = [row for row in rows_a if wtwy[row["WTWY_NAME"]] in EXPORT_BASINS]
    return rows_a, rows_b, rows_c, unmatched


def test_packet_files_exist() -> None:
    schema = _load("s4_correction_packet.schema.yaml")
    for name in schema["required_packet_files"]:
        assert (PROPOSALS / name).is_file(), name
    for name in schema["required_source_files"]:
        assert (PROPOSALS / name).is_file(), name
    for name in PACKET_FILES:
        assert (PROPOSALS / name).is_file(), name


def test_manifest_required_fields_and_ballot_ready_status() -> None:
    schema = _load("s4_correction_packet.schema.yaml")
    man = _load("S4_CORRECTION_PACKET_MANIFEST.yaml")
    for field in schema["manifest_required_fields"]:
        assert field in man, field
    assert man["packet_status"] == "PR44_EXACT_DELTA_BALLOT_READY"
    assert man["implementation_authorization"] is False
    assert man["production_persistence"] == "forbidden"
    assert man["sweep_execution"] == "forbidden"
    assert man["frozen_pr42_head"] == "840d9891473d3ebf248c2d44a9bbeac270d614ca"
    assert man["current_main"] == "a6f1b81c40f15a6f986ecbbe4e2e3128242a3b9c"
    assert man["irreducible_selectors"] == ["S4_NODE_CENSUS", "S4_TRACK_GEOMETRY"]
    assert man["recommended_choice"] == {
        "S4_NODE_CENSUS": "A",
        "S4_TRACK_GEOMETRY": "POINT_ONLY",
    }


def test_historical_b100_digest_is_evidence_only() -> None:
    schema = _load("s4_correction_packet.schema.yaml")
    man = _load("S4_CORRECTION_PACKET_MANIFEST.yaml")
    ballot = _load("S4_DELTA_BALLOT.yaml")
    assert man["historical_b100"]["digest_sha256"] == HISTORICAL_B100
    assert man["historical_b100"]["status"] == "historical_evidence_only_not_executable"
    assert schema["historical_b100_digest_sha256"] == HISTORICAL_B100
    preserved = ballot["preserved_without_reasking"]
    assert preserved["historical_b100_digest_sha256"] == HISTORICAL_B100
    assert preserved["historical_b100_digest_status"] == (
        "historical_evidence_only_not_executable"
    )


def test_corrected_b100_digest_matches_committed_bytes() -> None:
    man = _load("S4_CORRECTION_PACKET_MANIFEST.yaml")
    digest = _sha256("FULL_CONFIG_B100_S4_CORRECTED.yaml")
    assert digest == CORRECTED_B100
    assert man["corrected_b100_digest_sha256"] == digest
    assert man["packet_file_digests_sha256"]["FULL_CONFIG_B100_S4_CORRECTED.yaml"] == digest
    assert digest != HISTORICAL_B100


def test_packet_file_digests_match_bytes() -> None:
    man = _load("S4_CORRECTION_PACKET_MANIFEST.yaml")
    for name, expected in man["packet_file_digests_sha256"].items():
        assert _sha256(name) == expected, name


def test_live_d2_basins_match_production_prereg() -> None:
    live = yaml.safe_load(LIVE_PREREG.read_text(encoding="utf-8"))
    assert tuple(live["corridors"]["navigation_basins"]) == LIVE_D2
    fac = _load("S4_FACILITY_BINDING.yaml")
    cfg = _load("FULL_CONFIG_B100_S4_CORRECTED.yaml")
    schema = _load("s4_correction_packet.schema.yaml")
    assert tuple(fac["live_d2_basins"]) == LIVE_D2
    assert tuple(cfg["corridors"]["navigation_basins"]) == LIVE_D2
    assert tuple(schema["live_d2_basins"]) == LIVE_D2


def test_census_files_match_reconstruction_and_digests() -> None:
    rows_a, rows_b, rows_c, unmatched = _reconstruct_rows()
    census_a = _load("S4_CENSUS_A_WCSC_D2GRAIN_DOCK_COMMPURP.yaml")
    census_b = _load("S4_CENSUS_B_WCSC_D2GRAIN_DOCK_COMMODITIES.yaml")
    census_c = _load("S4_CENSUS_C_WCSC_D2GRAIN_EXPORT_BASINS.yaml")
    unmatched_doc = _load("S4_UNMATCHED_AND_EXPANSIONS.yaml")
    assert _sha256("S4_CENSUS_A_WCSC_D2GRAIN_DOCK_COMMPURP.yaml") == CENSUS_A_SHA
    assert _sha256("S4_CENSUS_B_WCSC_D2GRAIN_DOCK_COMMODITIES.yaml") == CENSUS_B_SHA
    assert _sha256("S4_CENSUS_C_WCSC_D2GRAIN_EXPORT_BASINS.yaml") == CENSUS_C_SHA
    assert census_a["row_count"] == 534 == len(rows_a) == len(census_a["nodes"])
    assert census_b["row_count"] == 405 == len(rows_b) == len(census_b["nodes"])
    assert census_c["row_count"] == 227 == len(rows_c) == len(census_c["nodes"])
    assert unmatched_doc["grain_token_rows_not_in_default"] == unmatched == 455
    assert {row["nav_unit_id"] for row in census_a["nodes"]} == {
        row["NAV_UNIT_ID"] for row in rows_a
    }
    assert {row["nav_unit_id"] for row in census_b["nodes"]} == {
        row["NAV_UNIT_ID"] for row in rows_b
    }
    assert {row["nav_unit_id"] for row in census_c["nodes"]} == {
        row["NAV_UNIT_ID"] for row in rows_c
    }
    assert census_a["completeness_claim"] == "NOT_CLAIMED"
    ids = [row["nav_unit_id"] for row in census_a["nodes"]]
    assert len(ids) == len(set(ids))


def test_recommended_default_is_census_a_live_d2_only() -> None:
    fac = _load("S4_FACILITY_BINDING.yaml")
    cfg = _load("FULL_CONFIG_B100_S4_CORRECTED.yaml")
    census_a = _load("S4_CENSUS_A_WCSC_D2GRAIN_DOCK_COMMPURP.yaml")
    registry = cfg["s4_node_registry"]
    assert fac["row_count"] == 534
    assert fac["completeness_claim"] == "NOT_CLAIMED"
    assert fac["recommended_census_id"] == "S4_CENSUS_A_WCSC_D2GRAIN_DOCK_COMMPURP"
    assert registry["row_count"] == 534
    assert registry["proximity_radius_nm"] == 100
    assert registry["texas_gulf_in_default"] is False
    assert registry["puget_sound_in_default"] is False
    assert registry["great_lakes_in_default"] is False
    assert registry["census_variant"] == "S4_CENSUS_A_WCSC_D2GRAIN_DOCK_COMMPURP"
    compact_ids = [row["node_id"] for row in registry["nodes"]]
    full_ids = [row["node_id"] for row in census_a["nodes"]]
    assert compact_ids == full_ids
    basins = {row["d2_basin"] for row in census_a["nodes"]}
    assert basins <= set(LIVE_D2)
    assert basins == set(LIVE_D2)


def test_corrected_b100_does_not_reintroduce_defective_nodes() -> None:
    text = (PROPOSALS / "FULL_CONFIG_B100_S4_CORRECTED.yaml").read_text(encoding="utf-8")
    nodes = _load("FULL_CONFIG_B100_S4_CORRECTED.yaml")["s4_node_registry"]["nodes"]
    dumped = yaml.safe_dump(nodes)
    for token in FORBIDDEN_DEFAULT_TOKENS:
        assert token not in dumped, token
        if token.startswith(("GULF-", "PNW-")):
            assert token not in text


def test_unapproved_expansions_are_explicit_and_out_of_default() -> None:
    fac = _load("S4_FACILITY_BINDING.yaml")
    ids = {row["id"] for row in fac["unapproved_expansions"]}
    assert ids == {"TEXAS_GULF", "PUGET_SOUND", "GREAT_LAKES"}
    assert all(row["included_in_corrected_default"] is False for row in fac["unapproved_expansions"])
    census_a = _load("S4_CENSUS_A_WCSC_D2GRAIN_DOCK_COMMPURP.yaml")
    waterways = {row["wtwy_name"] for row in census_a["nodes"]}
    for banned in (
        "Houston Ship Channel, TX",
        "Corpus Christi Ship Channel, TX",
        "Galveston, TX",
        "Seattle, WA",
        "Tacoma Harbor, WA",
        "Duluth MN",
        "Lake Michigan",
        "Lake Erie, Including Upper Niagara River",
        "Superior Wisconsin",
    ):
        assert banned not in waterways


def test_ballot_enumerates_census_and_track_only() -> None:
    fac = _load("S4_FACILITY_BINDING.yaml")
    man = _load("S4_CORRECTION_PACKET_MANIFEST.yaml")
    ballot = _load("S4_DELTA_BALLOT.yaml")
    assert fac["irreducible_selector"]["field_id"] == "S4_NODE_CENSUS"
    assert fac["irreducible_selector"]["options"] == ["A", "B", "C"]
    assert fac["irreducible_selector"]["recommended"] == "A"
    assert man["irreducible_selectors"] == ["S4_NODE_CENSUS", "S4_TRACK_GEOMETRY"]
    preserved = ballot["preserved_without_reasking"]
    assert preserved["S2"] == "USE_B_OPERATIONAL_RESTRICTION_ONLY"
    assert preserved["S4_RADIUS"] == "100_NM"
    assert preserved["V2_GOVERNANCE"] == "APPROVE"
    assert preserved["S4_GEODESIC"] == "HAVERSINE_NM_SPHERE"
    asked = {row["field_id"] for row in ballot["human_fields"]}
    assert asked == {"S4_NODE_CENSUS", "S4_TRACK_GEOMETRY"}
    census = next(row for row in ballot["human_fields"] if row["field_id"] == "S4_NODE_CENSUS")
    assert [opt["id"] for opt in census["options"]] == ["A", "B", "C"]
    assert census["recommended"] == "A"
    track = next(row for row in ballot["human_fields"] if row["field_id"] == "S4_TRACK_GEOMETRY")
    assert [opt["id"] for opt in track["options"]] == ["POINT_ONLY", "SEGMENT"]
    assert track["recommended"] == "POINT_ONLY"


def test_distance_contract_binds_100nm_and_haversine_nm_sphere() -> None:
    dist = _load("S4_DISTANCE_CONTRACT.yaml")
    schema = _load("s4_correction_packet.schema.yaml")
    for field in schema["distance_contract_required_fields"]:
        assert field in dist, field
    assert dist["proximity_radius_nm"] == 100
    assert dist["nautical_mile_m"] == 1852
    assert dist["radius_m"] == 185200
    assert dist["boundary_inequality"] == "<="
    assert dist["boundary_predicate"] == "distance_m <= 185200"
    assert dist["geodesic_mechanical"] is True
    geo = dist["geodesic"]
    assert geo["id"] == "HAVERSINE_NM_SPHERE"
    assert geo["algorithm"] == "haversine_sphere"
    assert abs(geo["earth_radius_m"] - EARTH_RADIUS_M) < 1e-9
    assert abs(geo["earth_radius_m"] - 6366707.019493707) < 1e-9
    hurdat = dist["hurdat2_treatment"]
    atlantic = hurdat["files"]["atlantic_current"]
    pacific = hurdat["files"]["pacific_ne_nc_current"]
    assert atlantic["url"].endswith("hurdat2-1851-2025-02272026.txt")
    assert atlantic["sha256"] == "1b9b0c7beed5b4505838658b1d30e159fc84330c60891a58cfcf43ae55c37202"
    assert pacific["url"].endswith("hurdat2-nepac-1949-2025-02272026.txt")
    assert pacific["sha256"] == "db65f8bc538d5c05e15f738c96111861d6ce3572c007879de58e44d4d05a9cd6"
    assert hurdat["interpolation_mechanical"] is False
    exposed = {row["field_id"] for row in dist["exposed_fields"]}
    assert exposed == {"S4_TRACK_GEOMETRY"}
    point = _load("S4_DISTANCE_POINT_ONLY.yaml")
    segment = _load("S4_DISTANCE_SEGMENT.yaml")
    assert point["recommended"] is True
    assert segment["recommended"] is False
    assert abs(point["geodesic"]["earth_radius_m"] - EARTH_RADIUS_M) < 1e-9
    assert abs(segment["geodesic"]["earth_radius_m"] - EARTH_RADIUS_M) < 1e-9


def test_fgis_location_name_all_null_and_not_joined() -> None:
    fgis = json.loads(
        (PROPOSALS / "s4_sources" / "fgis_GetFGISExportsList.json").read_text(encoding="utf-8")
    )
    rows = fgis["Data"]
    assert len(rows) == 655
    assert sum(1 for row in rows if row.get("LocationName")) == 0
    fac = _load("S4_FACILITY_BINDING.yaml")
    assert fac["fgis_registered_exporters"]["join"] == "NO_FACILITY_JOIN"
    assert fac["fgis_registered_exporters"]["location_name_nonnull"] == 0


def test_named_export_elevators_and_census_b_drops_purpose_only() -> None:
    census_a = _load("S4_CENSUS_A_WCSC_D2GRAIN_DOCK_COMMPURP.yaml")
    census_b = _load("S4_CENSUS_B_WCSC_D2GRAIN_DOCK_COMMODITIES.yaml")
    names_a = {row["name"] for row in census_a["nodes"]}
    names_b = {row["name"] for row in census_b["nodes"]}
    assert "PORT OF LONGVIEW BERTH 9 EGT" in names_a
    assert "PORT OF LONGVIEW BERTH 9 EGT" in names_b
    assert "TEMCO (CHS CARGILL), KALAMA GRAIN ELEVATOR" in names_a
    for name in (
        "ADM/GROWMARK, AMA GRAIN ELEVATOR DOCK",
        "ADM/GROWMARK, DESTREHAN ELEVATOR WHARF",
        "ZEN-NOH GRAIN CORP. WHARF.",
    ):
        assert name in names_a
        assert name not in names_b


def test_s2_b_gauges_preserved_on_corrected_b100() -> None:
    cfg = _load("FULL_CONFIG_B100_S4_CORRECTED.yaml")
    gauges = cfg["s2_gauge_registry"]
    assert gauges["interpretation"] == "OPERATIONAL_RESTRICTION_ONLY"
    assert gauges["row_count"] == 10
    ids = [row["station_id"] for row in gauges["gauges"]]
    assert ids == [
        "07010000",
        "07022000",
        "07032000",
        "07289000",
        "07374000",
        "07374510",
        "03612500",
        "03611500",
        "05586100",
        "05558300",
    ]
    assert cfg["physical_thresholds"]["mode"] == "binding_operational_restriction_only"
    s4_archive = next(row for row in cfg["source_archives"] if row["sweep_id"] == "S4")
    assert s4_archive["proximity_radius_nm"] == 100
    assert s4_archive["track_geometry"] == "POINT_ONLY"
    assert s4_archive["geodesic"] == "haversine_nm_sphere"


def test_source_family_endpoints_verified_and_no_out_of_d2_hidden() -> None:
    cfg = _load("FULL_CONFIG_B100_S4_CORRECTED.yaml")
    text = (PROPOSALS / "FULL_CONFIG_B100_S4_CORRECTED.yaml").read_text(encoding="utf-8")
    for banned in FORBIDDEN_ENDPOINTS:
        assert banned not in text
    s3 = next(row for row in cfg["source_archives"] if row["sweep_id"] == "S3")
    assert s3["endpoint"] == "https://navcen.uscg.gov/msib-national"
    assert s3["districts"] == ["D8", "D13"]
    assert "D9" not in s3["districts"]
    s4 = next(row for row in cfg["source_archives"] if row["sweep_id"] == "S4")
    assert s4["endpoints"] == [
        "https://www.nhc.noaa.gov/data/hurdat/hurdat2-1851-2025-02272026.txt",
        "https://www.nhc.noaa.gov/data/hurdat/hurdat2-nepac-1949-2025-02272026.txt",
    ]
    s6 = next(row for row in cfg["source_archives"] if row["sweep_id"] == "S6")
    assert s6["endpoint"] == "https://ndc.ops.usace.army.mil/ords/r/lpms/corps-locks/home"
    s7 = next(row for row in cfg["source_archives"] if row["sweep_id"] == "S7")
    assert s7["endpoint"] == "https://www.stb.gov/proceedings-actions/search-stb-records/"
    s8 = next(row for row in cfg["source_archives"] if row["sweep_id"] == "S8")
    assert "endpoint" not in s8
    provenance = _load("S4_SOURCE_RETRIEVAL_PROVENANCE.yaml")
    verified = provenance["endpoint_verification"]
    assert verified["https://www.navcen.uscg.gov/msib"] == 404
    assert verified["https://navcen.uscg.gov/msib-national"] == 200
    assert verified["https://corpslocks.usace.army.mil/"] == "DNS_FAIL"
    assert verified["https://ndc.ops.usace.army.mil/ords/r/lpms/corps-locks/home"] == 200
    assert verified["https://portnola.com/notices"] == 404
    assert provenance["sources"][-1]["id"] == "NOAA_USACE_IENC"
    assert provenance["sources"][-1]["retrieved"] is False


def test_packet_does_not_modify_production_guard_surfaces() -> None:
    assert LIVE_PREREG.is_file()
    assert PRODUCTION_MANIFEST.is_file()
    assert GOVERNANCE_PY.is_file()
    live = yaml.safe_load(LIVE_PREREG.read_text(encoding="utf-8"))
    assert "s4_node_registry" not in live
    assert live["schema_version"] == "0.2"
