"""Deterministic D2 corridor construction primitives.

This module implements the already-ratified ADR-0006/0007 architecture without
embedding a live reference interval, topology profile, source-code universe, or
membership result.  Callers must supply those frozen inputs explicitly.
"""

from __future__ import annotations

import hashlib
import math
from collections import defaultdict
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum


class CorridorConstructionError(ValueError):
    """A D2 input is malformed or cannot be interpreted deterministically."""


def _canonical_token(value: object, *, field: str) -> str:
    if not isinstance(value, str):
        raise CorridorConstructionError(f"{field} must be a string")
    token = value.strip()
    if not token or token != value:
        raise CorridorConstructionError(f"{field} must be nonempty and canonical")
    return token


@dataclass(frozen=True, order=True)
class TopologyLink:
    """One already-profile-filtered undirected topology link."""

    edge_id: str
    a_node: str
    b_node: str
    source_code: str

    def __post_init__(self) -> None:
        edge_id = _canonical_token(self.edge_id, field="edge_id")
        a_node = _canonical_token(self.a_node, field=f"{edge_id}.a_node")
        b_node = _canonical_token(self.b_node, field=f"{edge_id}.b_node")
        source_code = _canonical_token(self.source_code, field=f"{edge_id}.source_code")
        if a_node == b_node:
            raise CorridorConstructionError(f"self-loop is not permitted: {edge_id}")
        object.__setattr__(self, "edge_id", edge_id)
        object.__setattr__(self, "a_node", a_node)
        object.__setattr__(self, "b_node", b_node)
        object.__setattr__(self, "source_code", source_code)


@dataclass(frozen=True)
class AtomicCorridor:
    corridor_id: str
    member_edge_ids: tuple[str, ...]
    member_node_ids: tuple[str, ...]
    endpoint_node_ids: tuple[str, ...]
    is_cycle: bool


def _bundle_key(a_node: str, b_node: str) -> tuple[str, str]:
    return (a_node, b_node) if a_node < b_node else (b_node, a_node)


def _corridor_id(member_edge_ids: Sequence[str], *, id_prefix: str) -> str:
    prefix = _canonical_token(id_prefix, field="id_prefix")
    if any(ch in prefix for ch in "/\\") or prefix in {".", ".."}:
        raise CorridorConstructionError("id_prefix must be a safe single token")
    payload = "\x1f".join(member_edge_ids).encode("utf-8")
    return f"{prefix}-{hashlib.sha256(payload).hexdigest()[:16]}"


def build_atomic_corridors(
    links: Iterable[TopologyLink],
    *,
    id_prefix: str,
) -> tuple[AtomicCorridor, ...]:
    """Apply ADR-0007 maximal-chain atomicity to an explicit filtered graph.

    Parallel links are retained as separate member edges but bundled into one
    undirected adjacency for degree and traversal.  Thus degree is the number
    of distinct retained neighbouring nodes, never raw edge incidence count.
    """

    ordered_links = sorted(links, key=lambda link: link.edge_id)
    if not ordered_links:
        return ()
    edge_ids = [link.edge_id for link in ordered_links]
    if len(edge_ids) != len(set(edge_ids)):
        raise CorridorConstructionError("topology edge_id values must be unique")

    bundles: dict[tuple[str, str], list[TopologyLink]] = defaultdict(list)
    for link in ordered_links:
        bundles[_bundle_key(link.a_node, link.b_node)].append(link)
    for members in bundles.values():
        members.sort(key=lambda link: link.edge_id)

    incident: dict[str, set[tuple[str, str]]] = defaultdict(set)
    for key in bundles:
        a_node, b_node = key
        incident[a_node].add(key)
        incident[b_node].add(key)
    degree = {node: len(keys) for node, keys in incident.items()}

    visited: set[tuple[str, str]] = set()
    raw_atoms: list[tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...], bool]] = []

    def other_node(key: tuple[str, str], node: str) -> str:
        if node == key[0]:
            return key[1]
        if node == key[1]:
            return key[0]
        raise CorridorConstructionError(f"node {node!r} is not incident to bundle {key!r}")

    def walk_from_boundary(start: str, first: tuple[str, str]) -> None:
        member_edges: list[str] = []
        member_nodes = {start}
        current_node = start
        current_bundle = first
        while True:
            if current_bundle in visited:
                raise CorridorConstructionError("atomic traversal revisited a bundle")
            visited.add(current_bundle)
            member_edges.extend(link.edge_id for link in bundles[current_bundle])
            next_node = other_node(current_bundle, current_node)
            member_nodes.add(next_node)
            if degree[next_node] != 2:
                raw_atoms.append(
                    (
                        tuple(sorted(member_edges)),
                        tuple(sorted(member_nodes)),
                        tuple(sorted((start, next_node))),
                        False,
                    )
                )
                return
            candidates = sorted(incident[next_node] - {current_bundle})
            if len(candidates) != 1:
                raise CorridorConstructionError(
                    f"degree-2 node {next_node!r} has {len(candidates)} continuation bundles"
                )
            next_bundle = candidates[0]
            if next_bundle in visited:
                raise CorridorConstructionError(
                    "boundary-started chain closed onto visited topology before a boundary"
                )
            current_node = next_node
            current_bundle = next_bundle

    boundary_nodes = sorted(node for node, value in degree.items() if value != 2)
    for node in boundary_nodes:
        for bundle in sorted(incident[node]):
            if bundle not in visited:
                walk_from_boundary(node, bundle)

    # Any unvisited component is a pure degree-2 cycle.
    for first in sorted(bundles):
        if first in visited:
            continue
        start = first[0]
        current_node = start
        current_bundle = first
        member_edges: list[str] = []
        member_nodes = {start}
        while True:
            if current_bundle in visited:
                raise CorridorConstructionError("cycle traversal reached an earlier atom")
            visited.add(current_bundle)
            member_edges.extend(link.edge_id for link in bundles[current_bundle])
            next_node = other_node(current_bundle, current_node)
            member_nodes.add(next_node)
            candidates = sorted(incident[next_node] - {current_bundle})
            if len(candidates) != 1:
                raise CorridorConstructionError(
                    f"unvisited component is not a pure degree-2 cycle at {next_node!r}"
                )
            next_bundle = candidates[0]
            if next_bundle == first:
                if next_node != start:
                    raise CorridorConstructionError("cycle returned to first edge at wrong node")
                break
            if next_bundle in visited:
                raise CorridorConstructionError("cycle intersects previously visited topology")
            current_node = next_node
            current_bundle = next_bundle
        raw_atoms.append(
            (tuple(sorted(member_edges)), tuple(sorted(member_nodes)), (), True)
        )

    if visited != set(bundles):
        raise CorridorConstructionError("not every retained topology bundle was assigned")

    atoms: list[AtomicCorridor] = []
    seen_ids: set[str] = set()
    for member_edges, member_nodes, endpoints, is_cycle in sorted(raw_atoms):
        corridor_id = _corridor_id(member_edges, id_prefix=id_prefix)
        if corridor_id in seen_ids:
            raise CorridorConstructionError("corridor ID digest collision")
        seen_ids.add(corridor_id)
        atoms.append(
            AtomicCorridor(
                corridor_id=corridor_id,
                member_edge_ids=member_edges,
                member_node_ids=member_nodes,
                endpoint_node_ids=endpoints,
                is_cycle=is_cycle,
            )
        )
    return tuple(sorted(atoms, key=lambda atom: atom.corridor_id))


class CrosswalkDisposition(StrEnum):
    CONTAINED = "contained"
    SPANS_MULTIPLE = "spans_multiple"
    OUT_OF_SCOPE = "out_of_scope"
    UNRESOLVED = "unresolved"


@dataclass(frozen=True)
class SourceCrosswalkEntry:
    source_code: str
    disposition: CrosswalkDisposition
    corridor_ids: tuple[str, ...]
    retained_edge_ids: tuple[str, ...]


def build_exact_code_crosswalk(
    *,
    source_codes: Iterable[str],
    retained_links: Iterable[TopologyLink],
    corridors: Sequence[AtomicCorridor],
    unresolved_codes: Iterable[str] = (),
) -> tuple[SourceCrosswalkEntry, ...]:
    """Map source codes to atoms by exact canonical code equality only."""

    canonical_codes = sorted({_canonical_token(code, field="source_code") for code in source_codes})
    unresolved = {
        _canonical_token(code, field="unresolved_code") for code in unresolved_codes
    }
    if not unresolved.issubset(canonical_codes):
        raise CorridorConstructionError("unresolved_codes must be source-attested source_codes")

    edge_to_corridor: dict[str, str] = {}
    for corridor in corridors:
        if not corridor.member_edge_ids:
            raise CorridorConstructionError(
                f"corridor has no retained edges: {corridor.corridor_id}"
            )
        for edge_id in corridor.member_edge_ids:
            if edge_id in edge_to_corridor:
                raise CorridorConstructionError(f"edge assigned to multiple corridors: {edge_id}")
            edge_to_corridor[edge_id] = corridor.corridor_id

    links_by_code: dict[str, list[TopologyLink]] = defaultdict(list)
    retained = tuple(retained_links)
    retained_edge_ids = [link.edge_id for link in retained]
    if len(retained_edge_ids) != len(set(retained_edge_ids)):
        raise CorridorConstructionError("retained topology edge_id values must be unique")
    registered_edges = set(edge_to_corridor)
    supplied_edges = set(retained_edge_ids)
    if supplied_edges != registered_edges:
        missing = sorted(registered_edges - supplied_edges)
        extra = sorted(supplied_edges - registered_edges)
        raise CorridorConstructionError(
            "atomic registry and retained topology edge sets differ: "
            f"missing={missing!r}, extra={extra!r}"
        )
    retained_codes: set[str] = set()
    for link in retained:
        if link.edge_id not in edge_to_corridor:
            raise CorridorConstructionError(
                f"retained edge absent from atomic registry: {link.edge_id}"
            )
        links_by_code[link.source_code].append(link)
        retained_codes.add(link.source_code)
    unattested_codes = retained_codes - set(canonical_codes)
    if unattested_codes:
        raise CorridorConstructionError(
            "retained topology contains source codes absent from source_codes: "
            f"{sorted(unattested_codes)!r}"
        )

    entries: list[SourceCrosswalkEntry] = []
    for code in canonical_codes:
        links = sorted(links_by_code.get(code, ()), key=lambda link: link.edge_id)
        edge_ids = tuple(link.edge_id for link in links)
        corridor_ids = tuple(sorted({edge_to_corridor[edge_id] for edge_id in edge_ids}))
        if code in unresolved:
            disposition = CrosswalkDisposition.UNRESOLVED
        elif not links:
            disposition = CrosswalkDisposition.OUT_OF_SCOPE
        elif len(corridor_ids) == 1:
            disposition = CrosswalkDisposition.CONTAINED
        else:
            disposition = CrosswalkDisposition.SPANS_MULTIPLE
        entries.append(
            SourceCrosswalkEntry(
                source_code=code,
                disposition=disposition,
                corridor_ids=corridor_ids,
                retained_edge_ids=edge_ids,
            )
        )
    return tuple(entries)


class CargoInputState(StrEnum):
    PRESENT = "present"
    MISSING = "missing"
    UNREADABLE = "unreadable"


@dataclass(frozen=True)
class CargoObservation:
    source_code: str
    commodity_code: str
    short_tons: int | float | Decimal | None
    ton_miles: int | float | Decimal | None
    dimension_key: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "source_code", _canonical_token(self.source_code, field="source_code")
        )
        object.__setattr__(
            self,
            "commodity_code",
            _canonical_token(self.commodity_code, field="commodity_code"),
        )
        if not isinstance(self.dimension_key, tuple) or not self.dimension_key:
            raise CorridorConstructionError("dimension_key must be a nonempty tuple")
        for index, value in enumerate(self.dimension_key):
            if not isinstance(value, str) or value != value.strip():
                raise CorridorConstructionError(
                    f"dimension_key[{index}] must be a canonical string"
                )


@dataclass(frozen=True)
class AnnualCargoInput:
    year: int
    state: CargoInputState
    rows: tuple[CargoObservation, ...] = ()
    complete: bool = True

    def __post_init__(self) -> None:
        if isinstance(self.year, bool) or not isinstance(self.year, int):
            raise CorridorConstructionError("annual input year must be an integer")
        if not isinstance(self.state, CargoInputState):
            raise CorridorConstructionError("annual input state must be CargoInputState")
        if not isinstance(self.complete, bool):
            raise CorridorConstructionError("annual input complete must be bool")
        if self.state is not CargoInputState.PRESENT and self.rows:
            raise CorridorConstructionError("missing/unreadable annual input cannot contain rows")
        if self.state is not CargoInputState.PRESENT and self.complete:
            object.__setattr__(self, "complete", False)


class MembershipStatus(StrEnum):
    ELIGIBLE = "ELIGIBLE"
    INELIGIBLE = "INELIGIBLE"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class CorridorMembership:
    corridor_id: str
    status: MembershipStatus
    reason_codes: tuple[str, ...]


def _observed_number(value: object) -> Decimal | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, Decimal):
        number = value
    elif isinstance(value, int):
        number = Decimal(value)
    elif isinstance(value, float):
        if not math.isfinite(value):
            return None
        number = Decimal(str(value))
    else:
        return None
    if not number.is_finite():
        return None
    return number


def construct_d2_membership(
    *,
    corridors: Sequence[AtomicCorridor],
    crosswalk: Sequence[SourceCrosswalkEntry],
    annual_inputs: Sequence[AnnualCargoInput],
    required_years: Iterable[int],
    registered_commodity_codes: Iterable[str],
) -> tuple[CorridorMembership, ...]:
    """Execute ADR-0006 statuses from explicitly frozen, caller-supplied inputs."""

    corridor_ids = [corridor.corridor_id for corridor in corridors]
    if len(corridor_ids) != len(set(corridor_ids)):
        raise CorridorConstructionError("registry corridor_id values must be unique")
    all_corridors = set(corridor_ids)

    crosswalk_by_code: dict[str, SourceCrosswalkEntry] = {}
    for entry in crosswalk:
        code = _canonical_token(entry.source_code, field="crosswalk.source_code")
        if code in crosswalk_by_code:
            raise CorridorConstructionError(f"duplicate crosswalk source_code: {code}")
        if not isinstance(entry.disposition, CrosswalkDisposition):
            raise CorridorConstructionError(
                f"crosswalk disposition must be CrosswalkDisposition: {code}"
            )
        if not set(entry.corridor_ids).issubset(all_corridors):
            raise CorridorConstructionError(f"crosswalk references unknown corridor: {code}")
        if len(entry.corridor_ids) != len(set(entry.corridor_ids)):
            raise CorridorConstructionError(f"duplicate crosswalk corridor_id: {code}")
        if len(entry.retained_edge_ids) != len(set(entry.retained_edge_ids)):
            raise CorridorConstructionError(f"duplicate crosswalk retained_edge_id: {code}")
        if entry.disposition is CrosswalkDisposition.CONTAINED and len(entry.corridor_ids) != 1:
            raise CorridorConstructionError("contained crosswalk entry must name one corridor")
        if entry.disposition is CrosswalkDisposition.SPANS_MULTIPLE and len(entry.corridor_ids) < 2:
            raise CorridorConstructionError("spans_multiple entry must name at least two corridors")
        if entry.disposition is CrosswalkDisposition.OUT_OF_SCOPE and (
            entry.corridor_ids or entry.retained_edge_ids
        ):
            raise CorridorConstructionError(
                "out_of_scope crosswalk entry cannot name retained topology"
            )
        crosswalk_by_code[code] = entry

    years = sorted(set(required_years))
    if not years or any(isinstance(year, bool) or not isinstance(year, int) for year in years):
        raise CorridorConstructionError("required_years must contain integers")
    inputs_by_year: dict[int, AnnualCargoInput] = {}
    for annual in annual_inputs:
        if annual.year in inputs_by_year:
            raise CorridorConstructionError(f"duplicate annual input year: {annual.year}")
        if annual.year not in years:
            raise CorridorConstructionError(f"unexpected annual input year: {annual.year}")
        inputs_by_year[annual.year] = annual

    commodity_codes = {
        _canonical_token(code, field="registered_commodity_code")
        for code in registered_commodity_codes
    }
    if not commodity_codes:
        raise CorridorConstructionError("registered_commodity_codes must be nonempty")

    positives: set[str] = set()
    unknown_reasons: dict[str, set[str]] = defaultdict(set)

    def mark_unknown(targets: Iterable[str], reason: str) -> None:
        for corridor_id in targets:
            unknown_reasons[corridor_id].add(reason)

    for year in years:
        annual = inputs_by_year.get(year)
        if annual is None or annual.state is CargoInputState.MISSING:
            mark_unknown(all_corridors, "REQUIRED_INPUT_MISSING")
            continue
        if annual.state is CargoInputState.UNREADABLE:
            mark_unknown(all_corridors, "REQUIRED_INPUT_UNREADABLE")
            continue
        if not annual.complete:
            mark_unknown(all_corridors, "INCOMPLETE_ENUMERATION")

        grouped: dict[tuple[str, ...], list[CargoObservation]] = defaultdict(list)
        for row in annual.rows:
            grouped[row.dimension_key].append(row)

        rows: list[CargoObservation] = []
        for group in grouped.values():
            first = group[0]
            exact = all(
                (
                    row.source_code,
                    row.commodity_code,
                    row.short_tons,
                    row.ton_miles,
                    row.dimension_key,
                )
                == (
                    first.source_code,
                    first.commodity_code,
                    first.short_tons,
                    first.ton_miles,
                    first.dimension_key,
                )
                for row in group[1:]
            )
            if not exact:
                for row in group:
                    if row.commodity_code not in commodity_codes:
                        continue
                    entry = crosswalk_by_code.get(row.source_code)
                    if entry is None:
                        mark_unknown(all_corridors, "CROSSWALK_ENTRY_MISSING")
                    elif entry.corridor_ids:
                        mark_unknown(entry.corridor_ids, "CONFLICTING_DUPLICATE")
                    elif entry.disposition is CrosswalkDisposition.UNRESOLVED:
                        mark_unknown(all_corridors, "CONFLICTING_DUPLICATE")
                continue
            rows.append(first)

        for row in rows:
            if row.commodity_code not in commodity_codes:
                continue
            entry = crosswalk_by_code.get(row.source_code)
            if entry is None:
                mark_unknown(all_corridors, "CROSSWALK_ENTRY_MISSING")
                continue
            if entry.disposition is CrosswalkDisposition.OUT_OF_SCOPE:
                continue
            if entry.disposition is CrosswalkDisposition.UNRESOLVED:
                mark_unknown(
                    entry.corridor_ids or all_corridors,
                    "AMBIGUOUS_SOURCE_MAPPING",
                )
                continue
            if entry.disposition is CrosswalkDisposition.SPANS_MULTIPLE:
                mark_unknown(entry.corridor_ids, "AMBIGUOUS_SOURCE_MAPPING")
                continue

            corridor_id = entry.corridor_ids[0]
            short_tons = _observed_number(row.short_tons)
            if short_tons is None:
                mark_unknown((corridor_id,), "NONNUMERIC_SHORT_TONS")
            elif short_tons < 0:
                mark_unknown((corridor_id,), "NEGATIVE_SHORT_TONS")
            elif short_tons > 0:
                positives.add(corridor_id)

    results: list[CorridorMembership] = []
    for corridor_id in sorted(corridor_ids):
        if corridor_id in positives:
            status = MembershipStatus.ELIGIBLE
            reasons = ("QUALIFYING_POSITIVE",)
        elif unknown_reasons[corridor_id]:
            status = MembershipStatus.UNKNOWN
            reasons = tuple(sorted(unknown_reasons[corridor_id]))
        else:
            status = MembershipStatus.INELIGIBLE
            reasons = ("COMPLETE_NO_QUALIFYING_POSITIVE",)
        results.append(
            CorridorMembership(
                corridor_id=corridor_id,
                status=status,
                reason_codes=reasons,
            )
        )
    return tuple(results)
