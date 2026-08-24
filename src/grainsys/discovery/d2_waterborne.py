"""D2-EXACT-v1 waterborne corridor profile and execution rules.

This module implements the frozen D2-EXACT-v1 profile values for waterborne
corridor membership determination. It does NOT execute discovery, enumerate
candidates, form episodes, or produce market outcomes.

Profile contract: D2-EXACT-v1 (ratified 2026-08-24)
Reference interval: R = calendar years 2000-2009
Topology vintage: NTAD2009 Navigable Waterway Network
Physical evidence: WCUS annual Cargo artifacts 2000-2009
"""

from __future__ import annotations

import hashlib
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum
from typing import NamedTuple

from grainsys.discovery.corridors import (
    AnnualCargoInput,
    AtomicCorridor,
    CargoObservation,
    MembershipStatus,
    SourceCrosswalkEntry,
    TopologyLink,
    build_atomic_corridors,
    build_exact_code_crosswalk,
    construct_d2_membership,
)


class D2ProfileError(ValueError):
    """A D2 profile input is malformed or violates the frozen contract."""


D2_EXACT_V1_PROFILE_ID = "D2-EXACT-v1"
D2_EXACT_V1_RATIFICATION_DATE = "2026-08-24"

D2_REFERENCE_START_YEAR = 2000
D2_REFERENCE_END_YEAR = 2009
D2_REQUIRED_YEARS: tuple[int, ...] = tuple(
    range(D2_REFERENCE_START_YEAR, D2_REFERENCE_END_YEAR + 1)
)

WCUS_COMMODITY_PUBLICATION_CODES: frozenset[str] = frozenset(
    {
        "6241",
        "6344",
        "6442",
        "6443",
        "6445",
        "6447",
        "6522",
    }
)

WCSC_MASTER_TO_PUBLICATION: dict[str, str] = {
    "4100": "6241",
    "4200": "6442",
    "4300": "6443",
    "4400": "6344",
    "4510": "6443",
    "4520": "6445",
    "4530": "6447",
    "22220": "6522",
}


class CargoRowKey(NamedTuple):
    """Deterministic row key for WCUS Cargo deduplication.

    The key excludes ShortTons/TonMiles (the observed values) and includes
    all source-defined classification dimensions that distinguish physical
    traffic observations within a single annual artifact.
    """

    completed_year: int
    region_code: str
    waterway_code: str
    traffic_code: str
    commodity_code: str
    allo1_code: str
    allo2_code: str

    @classmethod
    def from_cargo_observation(cls, obs: CargoObservation) -> CargoRowKey:
        """Extract the deduplication key from a CargoObservation."""
        key = obs.dimension_key
        if len(key) != 7:
            raise D2ProfileError(
                f"dimension_key must have 7 elements for Cargo row key, got {len(key)}"
            )
        year_str, region, waterway, traffic, commodity, allo1, allo2 = key
        try:
            year = int(year_str)
        except ValueError as exc:
            raise D2ProfileError(
                f"dimension_key[0] (completed_year) must be an integer string, got {year_str!r}"
            ) from exc
        return cls(
            completed_year=year,
            region_code=region,
            waterway_code=waterway,
            traffic_code=traffic,
            commodity_code=commodity,
            allo1_code=allo1,
            allo2_code=allo2,
        )


class TopologyLinkType(StrEnum):
    """NTAD2009 link source types."""

    CORPS = "CORPS"
    VANDERBILT = "VANDERBILT"
    ORNL = "ORNL"
    CWIS = "CWIS"
    LOCK = "LOCK"
    NONCOMM = "NONCOMM"


@dataclass(frozen=True)
class NTAD2009Link:
    """Raw link record from NTAD2009 waterway.dbf."""

    featurid: str
    anode: str
    bnode: str
    link_type: str
    version: str

    def to_topology_link(self, *, source_code: str) -> TopologyLink:
        """Convert to a corridors.TopologyLink for atomicity processing."""
        return TopologyLink(
            edge_id=self.featurid,
            a_node=self.anode,
            b_node=self.bnode,
            source_code=source_code,
        )


@dataclass(frozen=True)
class D2TopologyProfile:
    """Frozen topology filtering profile for D2 waterborne corridors.

    The profile determines which NTAD2009 links are retained for atomicity
    and how parallel links are treated for degree calculation.
    """

    profile_id: str
    retained_link_types: frozenset[str]
    scope_node_ids: frozenset[str] | None

    def filter_links(
        self, links: Iterable[NTAD2009Link]
    ) -> tuple[NTAD2009Link, ...]:
        """Apply profile filtering to raw NTAD2009 links."""
        retained: list[NTAD2009Link] = []
        for link in links:
            if link.link_type not in self.retained_link_types:
                continue
            if self.scope_node_ids is not None:
                if (
                    link.anode not in self.scope_node_ids
                    and link.bnode not in self.scope_node_ids
                ):
                    continue
            retained.append(link)
        return tuple(sorted(retained, key=lambda lnk: lnk.featurid))


D2_EXACT_V1_TOPOLOGY_PROFILE = D2TopologyProfile(
    profile_id="WATERBORNE-NTAD2009-CORPS",
    retained_link_types=frozenset({TopologyLinkType.CORPS}),
    scope_node_ids=None,
)


def validate_cargo_row_key(obs: CargoObservation) -> CargoRowKey:
    """Validate and extract the row key from a Cargo observation."""
    return CargoRowKey.from_cargo_observation(obs)


def build_cargo_dimension_key(
    *,
    completed_year: int,
    region_code: str,
    waterway_code: str,
    traffic_code: str,
    commodity_code: str,
    allo1_code: str,
    allo2_code: str,
) -> tuple[str, ...]:
    """Build a dimension_key tuple for CargoObservation construction."""
    return (
        str(completed_year),
        region_code,
        waterway_code,
        traffic_code,
        commodity_code,
        allo1_code,
        allo2_code,
    )


def cargo_observation_from_row(
    *,
    waterway_code: str,
    completed_year: int,
    region_code: str,
    traffic_code: str,
    commodity_code: str,
    allo1_code: str,
    allo2_code: str,
    short_tons: int | float | Decimal | None,
    ton_miles: int | float | Decimal | None,
) -> CargoObservation:
    """Construct a CargoObservation from WCUS Cargo row fields.

    The waterway_code serves as the source_code for crosswalk mapping.
    """
    return CargoObservation(
        source_code=waterway_code,
        commodity_code=commodity_code,
        short_tons=short_tons,
        ton_miles=ton_miles,
        dimension_key=build_cargo_dimension_key(
            completed_year=completed_year,
            region_code=region_code,
            waterway_code=waterway_code,
            traffic_code=traffic_code,
            commodity_code=commodity_code,
            allo1_code=allo1_code,
            allo2_code=allo2_code,
        ),
    )


@dataclass(frozen=True)
class D2ExecutionInputs:
    """Frozen inputs for a D2 membership execution."""

    profile_id: str
    reference_years: tuple[int, ...]
    registered_commodity_codes: frozenset[str]
    topology_links: tuple[TopologyLink, ...]
    source_codes: tuple[str, ...]
    unresolved_codes: tuple[str, ...]
    annual_inputs: tuple[AnnualCargoInput, ...]

    def __post_init__(self) -> None:
        if not self.profile_id:
            raise D2ProfileError("profile_id must be nonempty")
        if not self.reference_years:
            raise D2ProfileError("reference_years must be nonempty")
        if not self.registered_commodity_codes:
            raise D2ProfileError("registered_commodity_codes must be nonempty")
        sorted_years = tuple(sorted(self.reference_years))
        if self.reference_years != sorted_years:
            raise D2ProfileError("reference_years must be sorted ascending")
        input_years = {annual.year for annual in self.annual_inputs}
        if input_years != set(self.reference_years):
            raise D2ProfileError(
                f"annual_inputs years {sorted(input_years)} do not match "
                f"reference_years {list(self.reference_years)}"
            )


@dataclass(frozen=True)
class D2ExecutionResult:
    """Result of a D2 membership execution."""

    profile_id: str
    corridors: tuple[AtomicCorridor, ...]
    crosswalk: tuple[SourceCrosswalkEntry, ...]
    membership: tuple[tuple[str, MembershipStatus, tuple[str, ...]], ...]
    manifest_hash: str

    @property
    def eligible_corridor_ids(self) -> tuple[str, ...]:
        """Registry-ordered set of ELIGIBLE corridor_ids."""
        return tuple(
            corridor_id
            for corridor_id, status, _ in self.membership
            if status is MembershipStatus.ELIGIBLE
        )

    @property
    def ineligible_corridor_ids(self) -> tuple[str, ...]:
        """Registry-ordered set of INELIGIBLE corridor_ids."""
        return tuple(
            corridor_id
            for corridor_id, status, _ in self.membership
            if status is MembershipStatus.INELIGIBLE
        )

    @property
    def unknown_corridor_ids(self) -> tuple[str, ...]:
        """Registry-ordered set of UNKNOWN corridor_ids."""
        return tuple(
            corridor_id
            for corridor_id, status, _ in self.membership
            if status is MembershipStatus.UNKNOWN
        )


def _compute_manifest_hash(
    *,
    profile_id: str,
    corridors: Sequence[AtomicCorridor],
    crosswalk: Sequence[SourceCrosswalkEntry],
    membership: Sequence[tuple[str, MembershipStatus, tuple[str, ...]]],
) -> str:
    """Compute a deterministic hash of the execution manifest."""
    parts: list[str] = [f"profile:{profile_id}"]
    for corridor in corridors:
        parts.append(
            f"corridor:{corridor.corridor_id}|{','.join(corridor.member_edge_ids)}"
        )
    for entry in crosswalk:
        parts.append(
            f"crosswalk:{entry.source_code}|{entry.disposition.value}|"
            f"{','.join(entry.corridor_ids)}"
        )
    for corridor_id, status, reasons in membership:
        parts.append(f"membership:{corridor_id}|{status.value}|{','.join(reasons)}")
    payload = "\n".join(parts).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def execute_d2_membership(inputs: D2ExecutionInputs) -> D2ExecutionResult:
    """Execute D2 membership determination from frozen inputs.

    This function:
    1. Builds atomic corridors from the topology links
    2. Builds the exact-code crosswalk from source codes to corridors
    3. Executes membership status assignment per ADR-0006 rules
    4. Returns a deterministic, hash-bound result

    It does NOT:
    - Execute discovery or search archives
    - Enumerate candidates or form episodes
    - Produce market outcomes or statistical results
    """
    if not inputs.topology_links:
        return D2ExecutionResult(
            profile_id=inputs.profile_id,
            corridors=(),
            crosswalk=(),
            membership=(),
            manifest_hash=_compute_manifest_hash(
                profile_id=inputs.profile_id,
                corridors=(),
                crosswalk=(),
                membership=(),
            ),
        )

    corridors = build_atomic_corridors(
        inputs.topology_links,
        id_prefix=inputs.profile_id,
    )

    crosswalk = build_exact_code_crosswalk(
        source_codes=inputs.source_codes,
        retained_links=inputs.topology_links,
        corridors=corridors,
        unresolved_codes=inputs.unresolved_codes,
    )

    membership_results = construct_d2_membership(
        corridors=corridors,
        crosswalk=crosswalk,
        annual_inputs=inputs.annual_inputs,
        required_years=inputs.reference_years,
        registered_commodity_codes=inputs.registered_commodity_codes,
    )

    membership = tuple(
        (m.corridor_id, m.status, m.reason_codes) for m in membership_results
    )

    return D2ExecutionResult(
        profile_id=inputs.profile_id,
        corridors=corridors,
        crosswalk=crosswalk,
        membership=membership,
        manifest_hash=_compute_manifest_hash(
            profile_id=inputs.profile_id,
            corridors=corridors,
            crosswalk=crosswalk,
            membership=membership,
        ),
    )


def make_d2_exact_v1_inputs(
    *,
    topology_links: Iterable[TopologyLink],
    source_codes: Iterable[str],
    annual_inputs: Iterable[AnnualCargoInput],
    unresolved_codes: Iterable[str] = (),
) -> D2ExecutionInputs:
    """Construct D2ExecutionInputs using the D2-EXACT-v1 frozen profile."""
    return D2ExecutionInputs(
        profile_id=D2_EXACT_V1_PROFILE_ID,
        reference_years=D2_REQUIRED_YEARS,
        registered_commodity_codes=WCUS_COMMODITY_PUBLICATION_CODES,
        topology_links=tuple(topology_links),
        source_codes=tuple(source_codes),
        unresolved_codes=tuple(unresolved_codes),
        annual_inputs=tuple(annual_inputs),
    )
