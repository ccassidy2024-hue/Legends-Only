from __future__ import annotations

from grainsys.discovery.corridors import (
    AnnualCargoInput,
    CargoInputState,
    CargoObservation,
    CorridorConstructionError,
    CrosswalkDisposition,
    MembershipStatus,
    SourceCrosswalkEntry,
    TopologyLink,
    build_atomic_corridors,
    build_exact_code_crosswalk,
    construct_d2_membership,
)


def link(edge: str, a: str, b: str, code: str = "X") -> TopologyLink:
    return TopologyLink(edge, a, b, code)


def observation(
    source_code: str,
    short_tons,
    *,
    commodity_code: str = "GRAIN",
    key: tuple[str, ...] | None = None,
    ton_miles=1,
) -> CargoObservation:
    return CargoObservation(
        source_code=source_code,
        commodity_code=commodity_code,
        short_tons=short_tons,
        ton_miles=ton_miles,
        dimension_key=key or ("2000", source_code, commodity_code, "ROW"),
    )


def test_atomicity_splits_at_degree_one_and_three_and_not_at_direction() -> None:
    links = [
        link("e1", "a", "b"),
        link("e2", "b", "c"),
        link("e3", "c", "d"),
        link("e4", "c", "x"),
        link("e5", "c", "y"),
    ]
    atoms = build_atomic_corridors(links, id_prefix="TEST")
    assert {atom.member_edge_ids for atom in atoms} == {
        ("e1", "e2"),
        ("e3",),
        ("e4",),
        ("e5",),
    }
    assert all(not atom.is_cycle for atom in atoms)


def test_atomicity_preserves_pure_degree_two_cycle_as_one_atom() -> None:
    atoms = build_atomic_corridors(
        [link("a", "n1", "n2"), link("b", "n2", "n3"), link("c", "n3", "n1")],
        id_prefix="TEST",
    )
    assert len(atoms) == 1
    assert atoms[0].member_edge_ids == ("a", "b", "c")
    assert atoms[0].endpoint_node_ids == ()
    assert atoms[0].is_cycle is True


def test_parallel_edges_share_one_degree_adjacency_but_are_both_members() -> None:
    atoms = build_atomic_corridors(
        [
            link("p1", "a", "b"),
            link("p2", "a", "b"),
            link("tail", "b", "c"),
        ],
        id_prefix="TEST",
    )
    assert len(atoms) == 1
    assert atoms[0].member_edge_ids == ("p1", "p2", "tail")
    assert atoms[0].endpoint_node_ids == ("a", "c")


def test_atomicity_is_input_order_invariant_and_rejects_bad_topology() -> None:
    links = [link("b", "n2", "n3"), link("a", "n1", "n2")]
    assert build_atomic_corridors(links, id_prefix="TEST") == build_atomic_corridors(
        reversed(links), id_prefix="TEST"
    )
    try:
        build_atomic_corridors([link("dup", "a", "b"), link("dup", "b", "c")], id_prefix="T")
    except CorridorConstructionError as exc:
        assert "unique" in str(exc)
    else:
        raise AssertionError("duplicate edge IDs must fail closed")


def test_crosswalk_exact_code_dispositions() -> None:
    links = [
        link("a", "n1", "n2", "ONE"),
        link("b", "n2", "n3", "MULTI"),
        link("c", "n2", "n4", "MULTI"),
    ]
    atoms = build_atomic_corridors(links, id_prefix="TEST")
    entries = build_exact_code_crosswalk(
        source_codes=["ONE", "MULTI", "OUT", "UNKNOWN"],
        retained_links=links,
        corridors=atoms,
        unresolved_codes=["UNKNOWN"],
    )
    by_code = {entry.source_code: entry for entry in entries}
    assert by_code["ONE"].disposition is CrosswalkDisposition.CONTAINED
    assert by_code["MULTI"].disposition is CrosswalkDisposition.SPANS_MULTIPLE
    assert by_code["OUT"].disposition is CrosswalkDisposition.OUT_OF_SCOPE
    assert by_code["UNKNOWN"].disposition is CrosswalkDisposition.UNRESOLVED


def test_crosswalk_requires_exact_registry_link_and_source_code_universes() -> None:
    links = [link("a", "n1", "n2", "ONE"), link("b", "n2", "n3", "TWO")]
    corridors = build_atomic_corridors(links, id_prefix="TEST")
    try:
        build_exact_code_crosswalk(
            source_codes=["ONE", "TWO"],
            retained_links=links[:1],
            corridors=corridors,
        )
    except CorridorConstructionError as exc:
        assert "edge sets differ" in str(exc)
    else:
        raise AssertionError("omitting a registered edge must fail closed")

    try:
        build_exact_code_crosswalk(
            source_codes=["ONE"],
            retained_links=links,
            corridors=corridors,
        )
    except CorridorConstructionError as exc:
        assert "absent from source_codes" in str(exc)
    else:
        raise AssertionError("omitting a retained source code must fail closed")


def test_membership_positive_is_existential_even_with_missing_year() -> None:
    links = [link("a", "n1", "n2", "W1")]
    corridors = build_atomic_corridors(links, id_prefix="TEST")
    crosswalk = build_exact_code_crosswalk(
        source_codes=["W1"], retained_links=links, corridors=corridors
    )
    result = construct_d2_membership(
        corridors=corridors,
        crosswalk=crosswalk,
        annual_inputs=[
            AnnualCargoInput(2000, CargoInputState.PRESENT, (observation("W1", 1),)),
            AnnualCargoInput(2001, CargoInputState.MISSING),
        ],
        required_years=[2000, 2001],
        registered_commodity_codes=["GRAIN"],
    )
    assert result[0].status is MembershipStatus.ELIGIBLE
    assert result[0].reason_codes == ("QUALIFYING_POSITIVE",)


def test_membership_unknown_never_coerces_to_ineligible() -> None:
    links = [link("a", "n1", "n2", "W1")]
    corridors = build_atomic_corridors(links, id_prefix="TEST")
    crosswalk = build_exact_code_crosswalk(
        source_codes=["W1"], retained_links=links, corridors=corridors
    )
    for annual, reason in [
        (AnnualCargoInput(2000, CargoInputState.MISSING), "REQUIRED_INPUT_MISSING"),
        (AnnualCargoInput(2000, CargoInputState.UNREADABLE), "REQUIRED_INPUT_UNREADABLE"),
        (
            AnnualCargoInput(
                2000, CargoInputState.PRESENT, (observation("W1", None),)
            ),
            "NONNUMERIC_SHORT_TONS",
        ),
    ]:
        result = construct_d2_membership(
            corridors=corridors,
            crosswalk=crosswalk,
            annual_inputs=[annual],
            required_years=[2000],
            registered_commodity_codes=["GRAIN"],
        )
        assert result[0].status is MembershipStatus.UNKNOWN
        assert reason in result[0].reason_codes


def test_membership_ineligible_requires_complete_enumeration() -> None:
    links = [link("a", "n1", "n2", "W1")]
    corridors = build_atomic_corridors(links, id_prefix="TEST")
    crosswalk = build_exact_code_crosswalk(
        source_codes=["W1"], retained_links=links, corridors=corridors
    )
    result = construct_d2_membership(
        corridors=corridors,
        crosswalk=crosswalk,
        annual_inputs=[
            AnnualCargoInput(2000, CargoInputState.PRESENT, (observation("W1", 0),))
        ],
        required_years=[2000],
        registered_commodity_codes=["GRAIN"],
    )
    assert result[0].status is MembershipStatus.INELIGIBLE


def test_spans_multiple_and_unresolved_mapping_produce_unknown() -> None:
    links = [link("a", "j", "x", "M"), link("b", "j", "y", "M"), link("c", "j", "z", "M")]
    corridors = build_atomic_corridors(links, id_prefix="TEST")
    crosswalk = build_exact_code_crosswalk(
        source_codes=["M", "U"],
        retained_links=links,
        corridors=corridors,
        unresolved_codes=["U"],
    )
    result = construct_d2_membership(
        corridors=corridors,
        crosswalk=crosswalk,
        annual_inputs=[
            AnnualCargoInput(
                2000,
                CargoInputState.PRESENT,
                (observation("M", 2), observation("U", 2, key=("2000", "U", "GRAIN"))),
            )
        ],
        required_years=[2000],
        registered_commodity_codes=["GRAIN"],
    )
    assert {row.status for row in result} == {MembershipStatus.UNKNOWN}
    assert all("AMBIGUOUS_SOURCE_MAPPING" in row.reason_codes for row in result)


def test_exact_duplicates_collapse_but_conflicting_duplicates_fail_closed() -> None:
    links = [link("a", "n1", "n2", "W1")]
    corridors = build_atomic_corridors(links, id_prefix="TEST")
    crosswalk = build_exact_code_crosswalk(
        source_codes=["W1"], retained_links=links, corridors=corridors
    )
    exact = observation("W1", 0)
    result = construct_d2_membership(
        corridors=corridors,
        crosswalk=crosswalk,
        annual_inputs=[AnnualCargoInput(2000, CargoInputState.PRESENT, (exact, exact))],
        required_years=[2000],
        registered_commodity_codes=["GRAIN"],
    )
    assert result[0].status is MembershipStatus.INELIGIBLE

    conflicting = observation("W1", 1, key=exact.dimension_key)
    result = construct_d2_membership(
        corridors=corridors,
        crosswalk=crosswalk,
        annual_inputs=[
            AnnualCargoInput(2000, CargoInputState.PRESENT, (exact, conflicting))
        ],
        required_years=[2000],
        registered_commodity_codes=["GRAIN"],
    )
    assert result[0].status is MembershipStatus.UNKNOWN
    assert "CONFLICTING_DUPLICATE" in result[0].reason_codes


def test_unregistered_commodity_never_qualifies() -> None:
    links = [link("a", "n1", "n2", "W1")]
    corridors = build_atomic_corridors(links, id_prefix="TEST")
    crosswalk = [
        SourceCrosswalkEntry(
            source_code="W1",
            disposition=CrosswalkDisposition.CONTAINED,
            corridor_ids=(corridors[0].corridor_id,),
            retained_edge_ids=("a",),
        )
    ]
    result = construct_d2_membership(
        corridors=corridors,
        crosswalk=crosswalk,
        annual_inputs=[
            AnnualCargoInput(
                2000,
                CargoInputState.PRESENT,
                (observation("W1", 10, commodity_code="OTHER"),),
            )
        ],
        required_years=[2000],
        registered_commodity_codes=["GRAIN"],
    )
    assert result[0].status is MembershipStatus.INELIGIBLE


def test_unregistered_conflicting_duplicates_do_not_block_ineligibility() -> None:
    links = [link("a", "n1", "n2", "W1")]
    corridors = build_atomic_corridors(links, id_prefix="TEST")
    crosswalk = build_exact_code_crosswalk(
        source_codes=["W1"], retained_links=links, corridors=corridors
    )
    first = observation("W1", 1, commodity_code="OTHER")
    second = observation(
        "W1", 2, commodity_code="OTHER", key=first.dimension_key
    )
    result = construct_d2_membership(
        corridors=corridors,
        crosswalk=crosswalk,
        annual_inputs=[
            AnnualCargoInput(2000, CargoInputState.PRESENT, (first, second))
        ],
        required_years=[2000],
        registered_commodity_codes=["GRAIN"],
    )
    assert result[0].status is MembershipStatus.INELIGIBLE


def test_incomplete_present_input_is_unknown() -> None:
    links = [link("a", "n1", "n2", "W1")]
    corridors = build_atomic_corridors(links, id_prefix="TEST")
    crosswalk = build_exact_code_crosswalk(
        source_codes=["W1"], retained_links=links, corridors=corridors
    )
    result = construct_d2_membership(
        corridors=corridors,
        crosswalk=crosswalk,
        annual_inputs=[
            AnnualCargoInput(
                2000,
                CargoInputState.PRESENT,
                (observation("W1", 0),),
                complete=False,
            )
        ],
        required_years=[2000],
        registered_commodity_codes=["GRAIN"],
    )
    assert result[0].status is MembershipStatus.UNKNOWN
    assert "INCOMPLETE_ENUMERATION" in result[0].reason_codes


def test_dimension_key_allows_source_blank_fields_but_not_whitespace_drift() -> None:
    row = CargoObservation("W1", "GRAIN", 1, 1, ("2000", "W1", ""))
    assert row.dimension_key[-1] == ""
    try:
        CargoObservation("W1", "GRAIN", 1, 1, ("2000", " drift "))
    except CorridorConstructionError as exc:
        assert "canonical string" in str(exc)
    else:
        raise AssertionError("dimension-key whitespace drift must fail closed")
