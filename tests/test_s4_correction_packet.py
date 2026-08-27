"""Deterministic checks for the PR42 S4 binding-correction proposal packet."""

from __future__ import annotations

import hashlib
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
)

HISTORICAL_B100 = "9e937523d31bc324d9b33628ffd81c78fb74e5141aab2d18174a1677da8ce3c1"
LIVE_D2 = (
    "lower_mississippi",
    "middle_mississippi",
    "upper_mississippi",
    "ohio",
    "illinois",
    "columbia_snake",
)
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


def _load(name: str) -> dict:
    path = PROPOSALS / name
    with path.open(encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    assert isinstance(data, dict), name
    return data


def _sha256(name: str) -> str:
    return hashlib.sha256((PROPOSALS / name).read_bytes()).hexdigest()


def test_packet_files_exist() -> None:
    schema = _load("s4_correction_packet.schema.yaml")
    for name in schema["required_packet_files"]:
        assert (PROPOSALS / name).is_file(), name
    for name in PACKET_FILES:
        assert (PROPOSALS / name).is_file(), name


def test_manifest_required_fields_and_fail_closed_status() -> None:
    schema = _load("s4_correction_packet.schema.yaml")
    man = _load("S4_CORRECTION_PACKET_MANIFEST.yaml")
    for field in schema["manifest_required_fields"]:
        assert field in man, field
    assert man["packet_status"] == "PR42_S4_CORRECTION_BLOCKED"
    assert man["implementation_authorization"] is False
    assert man["production_persistence"] == "forbidden"
    assert man["sweep_execution"] == "forbidden"
    assert man["frozen_pr42_head"] == "840d9891473d3ebf248c2d44a9bbeac270d614ca"
    assert man["current_main"] == "a6f1b81c40f15a6f986ecbbe4e2e3128242a3b9c"


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


def test_corrected_default_has_zero_s4_facilities() -> None:
    fac = _load("S4_FACILITY_BINDING.yaml")
    cfg = _load("FULL_CONFIG_B100_S4_CORRECTED.yaml")
    registry = cfg["s4_node_registry"]
    assert fac["default_facility_rows"] == []
    assert fac["row_count"] == 0
    assert fac["completeness_claim"] == "NOT_CLAIMED"
    assert registry["nodes"] == []
    assert registry["row_count"] == 0
    assert registry["proximity_radius_nm"] == 100
    assert registry["texas_gulf_in_default"] is False
    assert registry["puget_sound_in_default"] is False
    assert registry["great_lakes_in_default"] is False
    assert "NON_EXECUTABLE" in registry["status"]


def test_corrected_b100_does_not_reintroduce_defective_nodes() -> None:
    text = (PROPOSALS / "FULL_CONFIG_B100_S4_CORRECTED.yaml").read_text(encoding="utf-8")
    registry = _load("FULL_CONFIG_B100_S4_CORRECTED.yaml")["s4_node_registry"]
    dumped = yaml.safe_dump(registry)
    for token in FORBIDDEN_DEFAULT_TOKENS:
        assert token not in dumped, token
        if token.startswith(("GULF-", "PNW-")):
            assert token not in text


def test_unapproved_expansions_are_explicit_and_out_of_default() -> None:
    fac = _load("S4_FACILITY_BINDING.yaml")
    ids = {row["id"] for row in fac["unapproved_expansions"]}
    assert ids == {"TEXAS_GULF", "PUGET_SOUND", "GREAT_LAKES"}
    assert all(row["included_in_corrected_default"] is False for row in fac["unapproved_expansions"])


def test_irreducible_selector_is_census_not_s2_radius_or_v2() -> None:
    fac = _load("S4_FACILITY_BINDING.yaml")
    man = _load("S4_CORRECTION_PACKET_MANIFEST.yaml")
    ballot = _load("S4_DELTA_BALLOT.yaml")
    assert fac["irreducible_selector"]["field_id"] == "S4_NODE_CENSUS_SELECTOR"
    assert man["irreducible_selector"] == "S4_NODE_CENSUS_SELECTOR"
    preserved = ballot["preserved_without_reasking"]
    assert preserved["S2"] == "USE_B_OPERATIONAL_RESTRICTION_ONLY"
    assert preserved["S4_RADIUS"] == "100_NM"
    assert preserved["V2_GOVERNANCE"] == "APPROVE"
    asked = {row["field_id"] for row in ballot["human_fields"]}
    assert asked == {"S4_NODE_CENSUS_SELECTOR", "S4_TRACK_GEOMETRY", "S4_GEODESIC"}
    assert "S2" not in asked
    assert "S4_RADIUS" not in asked
    assert "V2_GOVERNANCE" not in asked


def test_distance_contract_binds_100nm_and_exposes_nonmechanical_fields() -> None:
    dist = _load("S4_DISTANCE_CONTRACT.yaml")
    schema = _load("s4_correction_packet.schema.yaml")
    for field in schema["distance_contract_required_fields"]:
        assert field in dist, field
    assert dist["proximity_radius_nm"] == 100
    assert dist["nautical_mile_m"] == 1852
    assert dist["radius_m"] == 185200
    assert dist["boundary_inequality"] == "<="
    assert dist["boundary_predicate"] == "distance_m <= 185200"
    assert dist["geodesic_mechanical"] is False
    assert set(dist["geodesic_options"]) == {"HAVERSINE_IUGG_MEAN", "WGS84_KARNEY"}
    haversine = dist["geodesic_options"]["HAVERSINE_IUGG_MEAN"]
    assert haversine["earth_radius_m"] == 6371008.8
    wgs84 = dist["geodesic_options"]["WGS84_KARNEY"]
    assert wgs84["semi_major_axis_m"] == 6378137.0
    assert wgs84["flattening"] == "1/298.257223563"
    hurdat = dist["hurdat2_treatment"]
    assert hurdat["interpolation_mechanical"] is False
    assert hurdat["interpolation_changes_membership"] is True
    exposed = {row["field_id"] for row in dist["exposed_fields"]}
    assert exposed == {"S4_GEODESIC", "S4_TRACK_GEOMETRY"}


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
    assert s4_archive["s4_nodes_executable"] is False


def test_packet_does_not_modify_production_guard_surfaces() -> None:
    # Correction branch may only add proposal artifacts / ordinary tests.
    assert LIVE_PREREG.is_file()
    assert PRODUCTION_MANIFEST.is_file()
    assert GOVERNANCE_PY.is_file()
    live = yaml.safe_load(LIVE_PREREG.read_text(encoding="utf-8"))
    assert "s4_node_registry" not in live
    assert live["schema_version"] == "0.2"
