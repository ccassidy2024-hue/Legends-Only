"""Tests for D2-EXACT-v1 waterborne profile and execution."""

from __future__ import annotations

import pytest

from grainsys.discovery.corridors import (
    AnnualCargoInput,
    CargoInputState,
    CargoObservation,
    MembershipStatus,
    TopologyLink,
)
from grainsys.discovery.d2_waterborne import (
    D2_EXACT_V1_PROFILE_ID,
    D2_EXACT_V1_TOPOLOGY_PROFILE,
    D2_REFERENCE_END_YEAR,
    D2_REFERENCE_START_YEAR,
    D2_REQUIRED_YEARS,
    WCSC_MASTER_TO_PUBLICATION,
    WCUS_COMMODITY_PUBLICATION_CODES,
    D2ExecutionInputs,
    D2ProfileError,
    D2TopologyProfile,
    NTAD2009Link,
    TopologyLinkType,
    build_cargo_dimension_key,
    cargo_observation_from_row,
    execute_d2_membership,
    make_d2_exact_v1_inputs,
    validate_cargo_row_key,
)


def test_reference_interval_is_2000_to_2009() -> None:
    assert D2_REFERENCE_START_YEAR == 2000
    assert D2_REFERENCE_END_YEAR == 2009
    assert D2_REQUIRED_YEARS == tuple(range(2000, 2010))
    assert len(D2_REQUIRED_YEARS) == 10


def test_wcus_commodity_codes_match_evidence_document() -> None:
    expected = {"6241", "6344", "6442", "6443", "6445", "6447", "6522"}
    assert WCUS_COMMODITY_PUBLICATION_CODES == expected


def test_wcsc_master_to_publication_mapping() -> None:
    assert WCSC_MASTER_TO_PUBLICATION["4100"] == "6241"
    assert WCSC_MASTER_TO_PUBLICATION["4200"] == "6442"
    assert WCSC_MASTER_TO_PUBLICATION["4300"] == "6443"
    assert WCSC_MASTER_TO_PUBLICATION["4400"] == "6344"
    assert WCSC_MASTER_TO_PUBLICATION["4510"] == "6443"
    assert WCSC_MASTER_TO_PUBLICATION["4520"] == "6445"
    assert WCSC_MASTER_TO_PUBLICATION["4530"] == "6447"
    assert WCSC_MASTER_TO_PUBLICATION["22220"] == "6522"


def test_d2_exact_v1_topology_profile_retains_only_corps() -> None:
    assert D2_EXACT_V1_TOPOLOGY_PROFILE.profile_id == "WATERBORNE-NTAD2009-CORPS"
    assert D2_EXACT_V1_TOPOLOGY_PROFILE.retained_link_types == frozenset(
        {TopologyLinkType.CORPS}
    )
    assert D2_EXACT_V1_TOPOLOGY_PROFILE.scope_node_ids is None


def test_topology_profile_filters_by_link_type() -> None:
    links = [
        NTAD2009Link("F001", "N1", "N2", "CORPS", "09"),
        NTAD2009Link("F002", "N2", "N3", "VANDERBILT", "09"),
        NTAD2009Link("F003", "N3", "N4", "CORPS", "09"),
        NTAD2009Link("F004", "N4", "N5", "LOCK", "09"),
    ]
    profile = D2TopologyProfile(
        profile_id="TEST",
        retained_link_types=frozenset({"CORPS"}),
        scope_node_ids=None,
    )
    filtered = profile.filter_links(links)
    assert len(filtered) == 2
    assert filtered[0].featurid == "F001"
    assert filtered[1].featurid == "F003"


def test_topology_profile_filters_by_scope_nodes() -> None:
    links = [
        NTAD2009Link("F001", "N1", "N2", "CORPS", "09"),
        NTAD2009Link("F002", "N2", "N3", "CORPS", "09"),
        NTAD2009Link("F003", "N3", "N4", "CORPS", "09"),
    ]
    profile = D2TopologyProfile(
        profile_id="TEST",
        retained_link_types=frozenset({"CORPS"}),
        scope_node_ids=frozenset({"N2"}),
    )
    filtered = profile.filter_links(links)
    assert len(filtered) == 2
    assert {lnk.featurid for lnk in filtered} == {"F001", "F002"}


def test_ntad2009_link_to_topology_link() -> None:
    link = NTAD2009Link("F001", "N1", "N2", "CORPS", "09")
    topo = link.to_topology_link(source_code="W001")
    assert topo.edge_id == "F001"
    assert topo.a_node == "N1"
    assert topo.b_node == "N2"
    assert topo.source_code == "W001"


def test_cargo_row_key_extraction() -> None:
    obs = CargoObservation(
        source_code="W001",
        commodity_code="6241",
        short_tons=100,
        ton_miles=500,
        dimension_key=("2005", "R01", "W001", "T01", "6241", "A1", "A2"),
    )
    key = validate_cargo_row_key(obs)
    assert key.completed_year == 2005
    assert key.region_code == "R01"
    assert key.waterway_code == "W001"
    assert key.traffic_code == "T01"
    assert key.commodity_code == "6241"
    assert key.allo1_code == "A1"
    assert key.allo2_code == "A2"


def test_cargo_row_key_rejects_wrong_dimension_length() -> None:
    obs = CargoObservation(
        source_code="W001",
        commodity_code="6241",
        short_tons=100,
        ton_miles=500,
        dimension_key=("2005", "R01", "W001"),
    )
    with pytest.raises(D2ProfileError, match="7 elements"):
        validate_cargo_row_key(obs)


def test_build_cargo_dimension_key() -> None:
    key = build_cargo_dimension_key(
        completed_year=2005,
        region_code="R01",
        waterway_code="W001",
        traffic_code="T01",
        commodity_code="6241",
        allo1_code="A1",
        allo2_code="A2",
    )
    assert key == ("2005", "R01", "W001", "T01", "6241", "A1", "A2")


def test_cargo_observation_from_row() -> None:
    obs = cargo_observation_from_row(
        waterway_code="W001",
        completed_year=2005,
        region_code="R01",
        traffic_code="T01",
        commodity_code="6241",
        allo1_code="A1",
        allo2_code="A2",
        short_tons=100,
        ton_miles=500,
    )
    assert obs.source_code == "W001"
    assert obs.commodity_code == "6241"
    assert obs.short_tons == 100
    assert obs.ton_miles == 500
    assert obs.dimension_key == ("2005", "R01", "W001", "T01", "6241", "A1", "A2")


def test_d2_execution_inputs_validation() -> None:
    with pytest.raises(D2ProfileError, match="profile_id"):
        D2ExecutionInputs(
            profile_id="",
            reference_years=(2000,),
            registered_commodity_codes=frozenset({"6241"}),
            topology_links=(),
            source_codes=(),
            unresolved_codes=(),
            annual_inputs=(AnnualCargoInput(2000, CargoInputState.MISSING),),
        )

    with pytest.raises(D2ProfileError, match="reference_years"):
        D2ExecutionInputs(
            profile_id="TEST",
            reference_years=(),
            registered_commodity_codes=frozenset({"6241"}),
            topology_links=(),
            source_codes=(),
            unresolved_codes=(),
            annual_inputs=(),
        )

    with pytest.raises(D2ProfileError, match="sorted"):
        D2ExecutionInputs(
            profile_id="TEST",
            reference_years=(2001, 2000),
            registered_commodity_codes=frozenset({"6241"}),
            topology_links=(),
            source_codes=(),
            unresolved_codes=(),
            annual_inputs=(
                AnnualCargoInput(2000, CargoInputState.MISSING),
                AnnualCargoInput(2001, CargoInputState.MISSING),
            ),
        )


def test_d2_execution_inputs_annual_year_mismatch() -> None:
    with pytest.raises(D2ProfileError, match="do not match"):
        D2ExecutionInputs(
            profile_id="TEST",
            reference_years=(2000, 2001),
            registered_commodity_codes=frozenset({"6241"}),
            topology_links=(),
            source_codes=(),
            unresolved_codes=(),
            annual_inputs=(AnnualCargoInput(2000, CargoInputState.MISSING),),
        )


def test_execute_d2_membership_empty_topology() -> None:
    inputs = D2ExecutionInputs(
        profile_id="TEST",
        reference_years=(2000,),
        registered_commodity_codes=frozenset({"6241"}),
        topology_links=(),
        source_codes=(),
        unresolved_codes=(),
        annual_inputs=(AnnualCargoInput(2000, CargoInputState.MISSING),),
    )
    result = execute_d2_membership(inputs)
    assert result.profile_id == "TEST"
    assert result.corridors == ()
    assert result.crosswalk == ()
    assert result.membership == ()
    assert result.manifest_hash


def test_execute_d2_membership_simple_eligible() -> None:
    links = [TopologyLink("e1", "n1", "n2", "W001")]
    obs = cargo_observation_from_row(
        waterway_code="W001",
        completed_year=2000,
        region_code="R01",
        traffic_code="T01",
        commodity_code="6241",
        allo1_code="A1",
        allo2_code="A2",
        short_tons=100,
        ton_miles=500,
    )
    inputs = D2ExecutionInputs(
        profile_id="TEST",
        reference_years=(2000,),
        registered_commodity_codes=frozenset({"6241"}),
        topology_links=tuple(links),
        source_codes=("W001",),
        unresolved_codes=(),
        annual_inputs=(
            AnnualCargoInput(2000, CargoInputState.PRESENT, (obs,)),
        ),
    )
    result = execute_d2_membership(inputs)
    assert len(result.corridors) == 1
    assert len(result.membership) == 1
    corridor_id, status, reasons = result.membership[0]
    assert status is MembershipStatus.ELIGIBLE
    assert "QUALIFYING_POSITIVE" in reasons
    assert result.eligible_corridor_ids == (corridor_id,)
    assert result.ineligible_corridor_ids == ()
    assert result.unknown_corridor_ids == ()


def test_execute_d2_membership_missing_input_produces_unknown() -> None:
    links = [TopologyLink("e1", "n1", "n2", "W001")]
    inputs = D2ExecutionInputs(
        profile_id="TEST",
        reference_years=(2000,),
        registered_commodity_codes=frozenset({"6241"}),
        topology_links=tuple(links),
        source_codes=("W001",),
        unresolved_codes=(),
        annual_inputs=(AnnualCargoInput(2000, CargoInputState.MISSING),),
    )
    result = execute_d2_membership(inputs)
    assert len(result.membership) == 1
    corridor_id, status, reasons = result.membership[0]
    assert status is MembershipStatus.UNKNOWN
    assert "REQUIRED_INPUT_MISSING" in reasons
    assert result.unknown_corridor_ids == (corridor_id,)


def test_execute_d2_membership_ineligible_with_complete_zero() -> None:
    links = [TopologyLink("e1", "n1", "n2", "W001")]
    obs = cargo_observation_from_row(
        waterway_code="W001",
        completed_year=2000,
        region_code="R01",
        traffic_code="T01",
        commodity_code="6241",
        allo1_code="A1",
        allo2_code="A2",
        short_tons=0,
        ton_miles=0,
    )
    inputs = D2ExecutionInputs(
        profile_id="TEST",
        reference_years=(2000,),
        registered_commodity_codes=frozenset({"6241"}),
        topology_links=tuple(links),
        source_codes=("W001",),
        unresolved_codes=(),
        annual_inputs=(
            AnnualCargoInput(2000, CargoInputState.PRESENT, (obs,)),
        ),
    )
    result = execute_d2_membership(inputs)
    corridor_id, status, reasons = result.membership[0]
    assert status is MembershipStatus.INELIGIBLE
    assert "COMPLETE_NO_QUALIFYING_POSITIVE" in reasons
    assert result.ineligible_corridor_ids == (corridor_id,)


def test_make_d2_exact_v1_inputs() -> None:
    links = [TopologyLink("e1", "n1", "n2", "W001")]
    annual_inputs = [
        AnnualCargoInput(year, CargoInputState.MISSING)
        for year in D2_REQUIRED_YEARS
    ]
    inputs = make_d2_exact_v1_inputs(
        topology_links=links,
        source_codes=["W001"],
        annual_inputs=annual_inputs,
    )
    assert inputs.profile_id == D2_EXACT_V1_PROFILE_ID
    assert inputs.reference_years == D2_REQUIRED_YEARS
    assert inputs.registered_commodity_codes == WCUS_COMMODITY_PUBLICATION_CODES


def test_execution_result_manifest_hash_is_deterministic() -> None:
    links = [TopologyLink("e1", "n1", "n2", "W001")]
    obs = cargo_observation_from_row(
        waterway_code="W001",
        completed_year=2000,
        region_code="R01",
        traffic_code="T01",
        commodity_code="6241",
        allo1_code="A1",
        allo2_code="A2",
        short_tons=100,
        ton_miles=500,
    )
    inputs = D2ExecutionInputs(
        profile_id="TEST",
        reference_years=(2000,),
        registered_commodity_codes=frozenset({"6241"}),
        topology_links=tuple(links),
        source_codes=("W001",),
        unresolved_codes=(),
        annual_inputs=(
            AnnualCargoInput(2000, CargoInputState.PRESENT, (obs,)),
        ),
    )
    result1 = execute_d2_membership(inputs)
    result2 = execute_d2_membership(inputs)
    assert result1.manifest_hash == result2.manifest_hash


def test_positive_is_existential_even_with_missing_year() -> None:
    links = [TopologyLink("e1", "n1", "n2", "W001")]
    obs = cargo_observation_from_row(
        waterway_code="W001",
        completed_year=2000,
        region_code="R01",
        traffic_code="T01",
        commodity_code="6241",
        allo1_code="A1",
        allo2_code="A2",
        short_tons=100,
        ton_miles=500,
    )
    inputs = D2ExecutionInputs(
        profile_id="TEST",
        reference_years=(2000, 2001),
        registered_commodity_codes=frozenset({"6241"}),
        topology_links=tuple(links),
        source_codes=("W001",),
        unresolved_codes=(),
        annual_inputs=(
            AnnualCargoInput(2000, CargoInputState.PRESENT, (obs,)),
            AnnualCargoInput(2001, CargoInputState.MISSING),
        ),
    )
    result = execute_d2_membership(inputs)
    corridor_id, status, reasons = result.membership[0]
    assert status is MembershipStatus.ELIGIBLE
