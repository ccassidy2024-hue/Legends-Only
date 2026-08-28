"""Fail-closed loader for Phase 0 preregistration discovery rules."""

from __future__ import annotations

import re
from datetime import date, datetime
from pathlib import Path
from typing import Any

import yaml

from grainsys.discovery.candidates import FORBIDDEN_CANDIDATE_FIELDS

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_PREREG_RELATIVE = Path("config") / "discovery" / "prereg_rules.yaml"
EPISODE_SCHEMA_RELATIVE = Path("research") / "episodes" / "episode_schema.yaml"
CANDIDATE_SCHEMA_RELATIVE = (
    Path("research") / "episodes" / "discovery" / "candidates" / "_schema.yaml"
)

# Algorithm capability already coded in sweep.py (N4 / ADR-0003). No new modes.
ALLOWED_KEYWORD_MATCH_MODES = frozenset({"substring", "whole_word"})

# Protocol §J Phase 1 families — registration of which archives are in-scope is D3.
PROTOCOL_SWEEP_FAMILIES = frozenset({f"S{i}" for i in range(1, 9)})

PREREG_SCHEMA_VERSION = "0.2"
PREREG_SCHEMA_VERSION_V2 = "0.3"
ALLOWED_PREREG_SCHEMA_VERSIONS = frozenset(
    {PREREG_SCHEMA_VERSION, PREREG_SCHEMA_VERSION_V2}
)

# Exact live-config key sets — unknown/missing keys fail closed (no silent retain).
PREREG_TOP_LEVEL_KEYS: tuple[str, ...] = (
    "schema_version",
    "governing_adr",
    "sample_period",
    "corridors",
    "source_archives",
    "keyword_policy",
    "candidates",
    "capture",
    "coverage",
    "physical_thresholds",
    "event_windows",
    "calibration_set",
    "concurrent_shocks",
    "analysis_anchor_grid",
)
PREREG_TOP_LEVEL_KEYS_V2: tuple[str, ...] = (
    *PREREG_TOP_LEVEL_KEYS,
    "s2_gauge_registry",
    "s4_node_registry",
    "marker",
)
SAMPLE_PERIOD_KEYS: tuple[str, ...] = ("sample_start", "sample_end")
CORRIDORS_KEYS: tuple[str, ...] = ("navigation_basins",)
SOURCE_ARCHIVE_ENTRY_KEYS: tuple[str, ...] = (
    "sweep_id",
    "authority",
    "district",
    "vehicle",
    "endpoint",
)
# Schema 0.3 per-family exact keys (approved A + POINT_ONLY packet).
# S2 is registry-only, not an archive row.
SOURCE_ARCHIVE_KEYS_BY_SWEEP_V2: dict[str, tuple[str, ...]] = {
    "S1": SOURCE_ARCHIVE_ENTRY_KEYS,
    "S3": (
        "sweep_id",
        "authority",
        "vehicle",
        "endpoint",
        "districts",
        "positive_evidence_only",
        "verification",
    ),
    "S4": (
        "sweep_id",
        "authority",
        "vehicle",
        "endpoints",
        "geodesic",
        "positive_evidence_only",
        "proximity_radius_nm",
        "track_geometry",
        "verification",
    ),
    "S5": (
        "sweep_id",
        "authority",
        "vehicle",
        "endpoint",
        "positive_evidence_only",
        "verification",
    ),
    "S6": (
        "sweep_id",
        "authority",
        "vehicle",
        "endpoint",
        "positive_evidence_only",
        "verification",
    ),
    "S7": (
        "sweep_id",
        "authority",
        "vehicle",
        "endpoint",
        "docket_prefixes",
        "positive_evidence_only",
        "verification",
    ),
    "S8": (
        "sweep_id",
        "authority",
        "vehicle",
        "nodes",
        "positive_evidence_only",
        "verification",
    ),
}
S2_GAUGE_REGISTRY_KEYS: tuple[str, ...] = (
    "interpretation",
    "semantics",
    "row_count",
    "gauges",
)
S2_GAUGE_ROW_KEYS: tuple[str, ...] = ("station_id", "name", "basin", "lat", "lon")
S2_GAUGE_INTERPRETATION_V2 = "OPERATIONAL_RESTRICTION_ONLY"
S2_GAUGE_ROW_COUNT_V2 = 10
S3_DISTRICTS_V2: tuple[str, ...] = ("D8", "D13")
S4_NODE_REGISTRY_KEYS: tuple[str, ...] = (
    "status",
    "census_variant",
    "census_source",
    "proximity_radius_nm",
    "nautical_mile_m",
    "radius_m",
    "boundary_inequality",
    "geodesic",
    "earth_radius_m",
    "track_geometry",
    "texas_gulf_in_default",
    "puget_sound_in_default",
    "great_lakes_in_default",
    "row_count",
    "nodes",
)
S4_NODE_ROW_KEYS: tuple[str, ...] = (
    "node_id",
    "name",
    "lat",
    "lon",
    "basin",
    "nav_unit_id",
)
S4_NODE_ROW_COUNT_V2 = 677
S4_PROXIMITY_RADIUS_NM_V2 = 100
S4_NAUTICAL_MILE_M_V2 = 1852
S4_RADIUS_M_V2 = 185200
S4_BOUNDARY_INEQUALITY_V2 = "<="
S4_GEODESIC_V2 = "haversine_nm_sphere"
S4_EARTH_RADIUS_M_V2 = 6366707.019493707
S4_TRACK_GEOMETRY_V2 = "POINT_ONLY"
S4_CENSUS_VARIANT_V2 = "S4_CENSUS_A_WCSC_D2GRAIN_DOCK_COMMPURP"
S4_CENSUS_SOURCE_V2 = "NDC Library Navigation Facilities DOCUMENTIDENTIFIER 08012026"
S4_STATUS_V2 = "PROPOSED_RECOMMENDED_CENSUS_A_POINT_ONLY"
S4_S8_NODES_V2 = "S4 node registry census A"
PREREG_MARKER_V2 = "FULL_CONFIG_B100_S4_CORRECTED_CENSUS_A_POINT_ONLY"
KEYWORD_POLICY_KEYS: tuple[str, ...] = ("terms", "match", "case_sensitive", "fields")
CANDIDATES_KEYS: tuple[str, ...] = (
    "table_path",
    "id_prefix",
    "ordering_keys",
    "stable_id_key",
)
CAPTURE_KEYS: tuple[str, ...] = ("sweeps_subdir", "rehome_policy")

# ADR-0013 closed vocabulary — first D6 implementation only.
REHOME_POLICIES = frozenset({"candidate_keyed_no_move"})
COVERAGE_KEYS: tuple[str, ...] = (
    "records_dir",
    "absent_must_be_explicit",
    "gap_policy_notes",
    "absence_generating_families",
    "source_identity_keys",
)
PHYSICAL_THRESHOLDS_KEYS: tuple[str, ...] = ("mode", "class_thresholds")
EVENT_WINDOWS_KEYS: tuple[str, ...] = (
    "pre_event_horizon",
    "reference_horizon",
    "response_horizon",
    "mapping_disposition",
)
CALIBRATION_SET_KEYS: tuple[str, ...] = ("count", "selection_rule")
CONCURRENT_SHOCKS_KEYS: tuple[str, ...] = ("shock_types", "sweep_rule")

# D8 explicit choice — no invented cutpoints; no third mode.
PHYSICAL_THRESHOLD_MODES = frozenset(
    {
        "registered_thresholds",
        "binding_operational_restriction_only",
    }
)
CALIBRATION_SET_COUNT = 3

# D13 shape only — values are not invented or defaulted by this loader.
ANALYSIS_ANCHOR_GRID_KEYS: tuple[str, ...] = (
    "frequency",
    "weekday_or_calendar_convention",
    "cutoff_time",
    "timezone",
    "holiday_treatment",
    "missing_anchor_handling",
    "target_date_mapping",
)

# P5 identity keys that may be registered in coverage.source_identity_keys.
ALLOWED_SOURCE_IDENTITY_KEYS = frozenset(
    {"source_family", "authority", "district", "vehicle", "endpoint"}
)

# Fields usable as ordering keys before minting (schema minus minted/forbidden).
POST_MINT_ONLY_FIELDS = frozenset({"candidate_id", "ordering_key"})
PRE_MINT_CANDIDATE_FIELDS = frozenset(
    {
        "sweep_id",
        "source_reference",
        "raw_capture_pointer",
        "document_date",
        "stable_source_id",
        "authority",
        "district",
        "vehicle",
        "endpoint",
        "retrieved_on",
        "notes",
    }
)

# Control fields that must never be used as the source-native stable_id_key.
# Post-mint and forbidden fields are rejected separately. Custom keys like
# notice_id are allowed; source_reference / stable_source_id are allowed.
RESERVED_STABLE_ID_CONTROL_FIELDS = frozenset({"sweep_id"})

_ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_SAFE_PATH_COMPONENT_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
_SAFE_STABLE_ID_KEY_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_WINDOWS_RESERVED_DEVICES = frozenset(
    {
        "CON",
        "PRN",
        "AUX",
        "NUL",
        *(f"COM{i}" for i in range(1, 10)),
        *(f"LPT{i}" for i in range(1, 10)),
    }
)
_PLACEHOLDER_DATES = frozenset(
    {
        "TO_BE_SET",
        "TBD",
        "TODO",
        "NULL",
        "NONE",
        "UNSET",
    }
)


class DiscoveryConfigError(RuntimeError):
    """Raised when preregistration config is missing or incomplete."""


class _UniqueKeySafeLoader(yaml.SafeLoader):
    """SafeLoader that refuses duplicate mapping keys."""


def _construct_mapping_no_duplicates(
    loader: yaml.SafeLoader, node: yaml.nodes.MappingNode, deep: bool = False
) -> dict[Any, Any]:
    mapping: dict[Any, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in mapping:
            raise yaml.constructor.ConstructorError(
                "while constructing a mapping",
                node.start_mark,
                f"found duplicate key {key!r}",
                key_node.start_mark,
            )
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


_UniqueKeySafeLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_mapping_no_duplicates,
)


def prereg_rules_path(repo_root: Path | None = None) -> Path:
    root = repo_root if repo_root is not None else REPO_ROOT
    return root / DEFAULT_PREREG_RELATIVE


def require_nonempty_str(value: Any, *, field: str) -> str:
    """Require an actual nonempty canonical str — never coerce or silently trim."""
    if not isinstance(value, str):
        raise DiscoveryConfigError(
            f"{field} must be a nonempty string (got {type(value).__name__}); "
            "refuse coercion"
        )
    if value != value.strip():
        raise DiscoveryConfigError(
            f"{field} must be a canonical trimmed string; refuse untrimmed"
        )
    if not value:
        raise DiscoveryConfigError(f"{field} must be a nonempty string; refuse blank")
    return value


def require_source_native_str(value: Any, *, field: str) -> str:
    """Nonempty string from a source-native field; do not trim or coerce."""
    if not isinstance(value, str):
        raise DiscoveryConfigError(
            f"{field} must be a nonempty string (got {type(value).__name__}); "
            "refuse coercion"
        )
    if "\x00" in value:
        raise DiscoveryConfigError(f"{field} contains NUL; refuse")
    if not value:
        raise DiscoveryConfigError(f"{field} must be a nonempty string; refuse blank")
    return value


def require_exact_mapping_keys(
    value: Any,
    *,
    field: str,
    required: tuple[str, ...],
) -> dict[str, Any]:
    """Require a mapping whose key set equals ``required`` exactly."""
    if not isinstance(value, dict):
        raise DiscoveryConfigError(f"{field} must be a mapping")
    got = set(value)
    expected = set(required)
    unknown = sorted(got - expected)
    missing = sorted(expected - got)
    if unknown:
        raise DiscoveryConfigError(f"{field} has unknown keys {unknown}; refuse")
    if missing:
        raise DiscoveryConfigError(f"{field} missing required keys {missing}; refuse")
    return value


def require_unique_nonempty_str_list(
    value: Any,
    *,
    field: str,
) -> list[str]:
    if not isinstance(value, list) or len(value) == 0:
        raise DiscoveryConfigError(f"{field} must be a nonempty list")
    out: list[str] = []
    seen: set[str] = set()
    for i, item in enumerate(value):
        text = require_nonempty_str(item, field=f"{field}[{i}]")
        if text in seen:
            raise DiscoveryConfigError(f"{field} contains duplicate {text!r}")
        seen.add(text)
        out.append(text)
    return out


def _assert_safe_path_segment(part: str, *, field: str) -> None:
    """Reject traversal, reserved Windows devices, and trailing-dot/space aliases."""
    if part in {".", ".."}:
        raise DiscoveryConfigError(f"{field} must not contain '.' or '..' segments; refuse")
    if part.endswith(".") or part.endswith(" "):
        raise DiscoveryConfigError(
            f"{field} has trailing-dot/space alias {part!r}; refuse"
        )
    if not _SAFE_PATH_COMPONENT_RE.fullmatch(part):
        raise DiscoveryConfigError(f"{field} has unsafe path segment {part!r}; refuse")
    stem = part.split(".", 1)[0].upper()
    if stem in _WINDOWS_RESERVED_DEVICES:
        raise DiscoveryConfigError(
            f"{field} uses reserved Windows device name {part!r}; refuse"
        )


def require_safe_path_component(value: Any, *, field: str) -> str:
    """Single path component: no separators, traversal, devices, NUL, or bool coercion."""
    if isinstance(value, bool) or not isinstance(value, str):
        raise DiscoveryConfigError(
            f"{field} must be a nonempty string path component "
            f"(got {type(value).__name__}); refuse coercion"
        )
    if "\x00" in value:
        raise DiscoveryConfigError(f"{field} contains NUL; refuse")
    if not value or value.strip() != value:
        raise DiscoveryConfigError(f"{field} must be a nonempty trimmed path component")
    if "/" in value or "\\" in value:
        raise DiscoveryConfigError(f"{field} must not contain path separators; refuse")
    _assert_safe_path_segment(value, field=field)
    return value


def require_safe_relative_path(value: Any, *, field: str) -> str:
    """Safe relative path using '/' separators; reject abs/rooted/traversal/NUL."""
    if isinstance(value, bool) or not isinstance(value, str):
        raise DiscoveryConfigError(
            f"{field} must be a nonempty relative path string "
            f"(got {type(value).__name__}); refuse coercion"
        )
    if "\x00" in value:
        raise DiscoveryConfigError(f"{field} contains NUL; refuse")
    text = require_nonempty_str(value, field=field)
    if text.startswith("/") or text.startswith("\\"):
        raise DiscoveryConfigError(f"{field} must be relative (got rooted {text!r})")
    # Windows drive / UNC
    if len(text) >= 2 and text[1] == ":":
        raise DiscoveryConfigError(f"{field} must be relative (got drive path {text!r})")
    if text.startswith("\\\\") or text.startswith("//"):
        raise DiscoveryConfigError(f"{field} must be relative (got UNC/rooted {text!r})")
    normalized = text.replace("\\", "/")
    parts = [p for p in normalized.split("/")]
    if any(p == "" for p in parts):
        raise DiscoveryConfigError(f"{field} has empty path segment; refuse")
    for part in parts:
        _assert_safe_path_segment(part, field=field)
    return normalized


def require_repo_contained_relative_path(
    value: Any,
    *,
    field: str,
    repo_root: Path,
) -> str:
    """Require a safe relative path that resolves inside ``repo_root``."""
    rel = require_safe_relative_path(value, field=field)
    root = repo_root.resolve()
    target = (repo_root / Path(*rel.split("/"))).resolve()
    try:
        target.relative_to(root)
    except ValueError as exc:
        raise DiscoveryConfigError(
            f"{field}={rel!r} escapes repository root; refuse"
        ) from exc
    return rel


def validate_pre_mint_field_keys(
    keys: Any,
    *,
    field: str,
    allow_empty: bool = False,
) -> list[str]:
    """Validate ordering key names as unique nonempty pre-mint fields."""
    if not isinstance(keys, (list, tuple)):
        raise DiscoveryConfigError(f"{field} must be a list/tuple of strings")
    if len(keys) == 0:
        if allow_empty:
            return []
        raise DiscoveryConfigError(f"{field} must be a nonempty list")
    out: list[str] = []
    seen: set[str] = set()
    for i, raw in enumerate(keys):
        key = require_nonempty_str(raw, field=f"{field}[{i}]")
        if key in seen:
            raise DiscoveryConfigError(f"{field} contains duplicate {key!r}")
        seen.add(key)
        if key in POST_MINT_ONLY_FIELDS:
            raise DiscoveryConfigError(
                f"{field} may not include post-mint field {key!r}"
            )
        if key in FORBIDDEN_CANDIDATE_FIELDS:
            raise DiscoveryConfigError(
                f"{field} may not include forbidden field {key!r}"
            )
        if key not in PRE_MINT_CANDIDATE_FIELDS:
            raise DiscoveryConfigError(
                f"{field} contains unknown/non-pre-mint field {key!r}"
            )
        out.append(key)
    return out


def validate_stable_id_key_name(value: Any, *, field: str) -> str:
    """Validate a source-native raw field name used only to populate stable_source_id."""
    if isinstance(value, bool) or not isinstance(value, str):
        raise DiscoveryConfigError(
            f"{field} must be a nonempty string field name "
            f"(got {type(value).__name__}); refuse coercion"
        )
    if "\x00" in value:
        raise DiscoveryConfigError(f"{field} contains NUL; refuse")
    key = require_nonempty_str(value, field=field)
    if "/" in key or "\\" in key or key in {".", ".."}:
        raise DiscoveryConfigError(f"{field}={key!r} is an unsafe field name; refuse")
    if not _SAFE_STABLE_ID_KEY_RE.fullmatch(key):
        raise DiscoveryConfigError(f"{field}={key!r} is an unsafe field name; refuse")
    if key in POST_MINT_ONLY_FIELDS:
        raise DiscoveryConfigError(f"{field} may not be post-mint field {key!r}")
    if key in FORBIDDEN_CANDIDATE_FIELDS:
        raise DiscoveryConfigError(f"{field} may not be forbidden field {key!r}")
    if key in RESERVED_STABLE_ID_CONTROL_FIELDS:
        raise DiscoveryConfigError(
            f"{field} may not be reserved control/metadata field {key!r}"
        )
    return key


def parse_iso_calendar_date(value: Any, *, field: str) -> date:
    """Strict YYYY-MM-DD calendar date; rejects placeholders and non-dates."""
    text = require_nonempty_str(value, field=field)
    if text.upper() in _PLACEHOLDER_DATES or text.upper().startswith("TO_BE_"):
        raise DiscoveryConfigError(
            f"{field}={text!r} is a placeholder; refuse (no invented dates)."
        )
    if not _ISO_DATE_RE.fullmatch(text):
        raise DiscoveryConfigError(
            f"{field}={text!r} must be strict ISO calendar date YYYY-MM-DD"
        )
    try:
        return datetime.strptime(text, "%Y-%m-%d").date()
    except ValueError as exc:
        raise DiscoveryConfigError(
            f"{field}={text!r} is not a valid calendar date"
        ) from exc


def _load_yaml_mapping(path: Path) -> dict[str, Any]:
    try:
        with path.open(encoding="utf-8") as fh:
            data = yaml.load(fh, Loader=_UniqueKeySafeLoader)
    except yaml.constructor.ConstructorError as exc:
        raise DiscoveryConfigError(
            f"{path} has duplicate YAML keys; refuse ({exc.problem})"
        ) from exc
    except yaml.YAMLError as exc:
        raise DiscoveryConfigError(f"{path} YAML unparseable; refuse") from exc
    if not isinstance(data, dict):
        raise DiscoveryConfigError(f"{path} must contain a YAML mapping")
    return data


def _load_navigation_basin_vocab(repo_root: Path) -> frozenset[str]:
    path = repo_root / EPISODE_SCHEMA_RELATIVE
    if not path.is_file():
        raise DiscoveryConfigError(
            f"episode schema missing at {path}; cannot validate navigation_basins"
        )
    schema = _load_yaml_mapping(path)
    vocab = (schema.get("vocabularies") or {}).get("navigation_basin")
    if not isinstance(vocab, list) or not vocab:
        raise DiscoveryConfigError(
            f"{path} vocabularies.navigation_basin missing or empty; undecidable"
        )
    names: set[str] = set()
    for item in vocab:
        if not isinstance(item, str) or item != item.strip() or not item:
            raise DiscoveryConfigError(
                f"{path} vocabularies.navigation_basin has non-canonical entry"
            )
        names.add(item)
    return frozenset(names)


def _require_s1_s8_subset(
    value: Any, *, field: str, allow_empty: bool = False
) -> list[str]:
    """Validate a list as a subset of protocol sweep families S1-S8.

    When allow_empty is True, an empty list is valid (meaning no family is
    permitted to generate absence evidence and unknown remains unknown).
    When allow_empty is False, the list must be nonempty.
    Every nonempty member must still be unique and within S1-S8.
    """
    if not isinstance(value, list):
        raise DiscoveryConfigError(f"{field} must be a list")
    if len(value) == 0:
        if allow_empty:
            return []
        raise DiscoveryConfigError(f"{field} must be a nonempty list")
    # Nonempty list: validate each member is unique and in S1-S8
    out: list[str] = []
    seen: set[str] = set()
    for i, item in enumerate(value):
        text = require_nonempty_str(item, field=f"{field}[{i}]")
        if text in seen:
            raise DiscoveryConfigError(f"{field} contains duplicate {text!r}")
        seen.add(text)
        out.append(text)
    unknown = sorted(set(out) - PROTOCOL_SWEEP_FAMILIES)
    if unknown:
        raise DiscoveryConfigError(
            f"{field} contains values outside S1–S8: {unknown}"
        )
    return out


def _require_identity_key_subset(value: Any, *, field: str) -> list[str]:
    keys = require_unique_nonempty_str_list(value, field=field)
    unknown = sorted(set(keys) - ALLOWED_SOURCE_IDENTITY_KEYS)
    if unknown:
        raise DiscoveryConfigError(
            f"{field} contains values outside allowed identity keys "
            f"{sorted(ALLOWED_SOURCE_IDENTITY_KEYS)}: {unknown}"
        )
    return keys


def _validate_physical_thresholds(block: dict[str, Any]) -> None:
    mode = require_nonempty_str(block.get("mode"), field="physical_thresholds.mode")
    if mode not in PHYSICAL_THRESHOLD_MODES:
        raise DiscoveryConfigError(
            f"physical_thresholds.mode={mode!r} must be one of "
            f"{sorted(PHYSICAL_THRESHOLD_MODES)}; refuse invented D8 mode"
        )
    thresholds = block.get("class_thresholds")
    if not isinstance(thresholds, list):
        raise DiscoveryConfigError(
            "physical_thresholds.class_thresholds must be a list"
        )
    if mode == "binding_operational_restriction_only":
        if thresholds:
            raise DiscoveryConfigError(
                "physical_thresholds.class_thresholds must be empty when mode is "
                "binding_operational_restriction_only; refuse leftover thresholds"
            )
        return
    require_unique_nonempty_str_list(
        thresholds, field="physical_thresholds.class_thresholds"
    )


def _validate_event_windows(block: dict[str, Any]) -> None:
    for key in EVENT_WINDOWS_KEYS:
        require_nonempty_str(block.get(key), field=f"event_windows.{key}")


def _validate_calibration_set(block: dict[str, Any]) -> None:
    count = block.get("count")
    if isinstance(count, bool) or not isinstance(count, int) or count != CALIBRATION_SET_COUNT:
        raise DiscoveryConfigError(
            "calibration_set.count must be the actual integer 3 "
            f"(got {count!r}); refuse coercion/defaults"
        )
    require_nonempty_str(
        block.get("selection_rule"), field="calibration_set.selection_rule"
    )


def _validate_concurrent_shocks(block: dict[str, Any]) -> None:
    require_unique_nonempty_str_list(
        block.get("shock_types"), field="concurrent_shocks.shock_types"
    )
    require_nonempty_str(
        block.get("sweep_rule"), field="concurrent_shocks.sweep_rule"
    )


def require_actual_bool(value: Any, *, field: str) -> bool:
    if not isinstance(value, bool):
        raise DiscoveryConfigError(
            f"{field} must be an actual bool (got {type(value).__name__}); refuse coercion"
        )
    return value


def require_actual_int(value: Any, *, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise DiscoveryConfigError(
            f"{field} must be an actual int (got {type(value).__name__}); refuse coercion"
        )
    return value


def require_finite_number(value: Any, *, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise DiscoveryConfigError(
            f"{field} must be an actual number (got {type(value).__name__}); refuse coercion"
        )
    number = float(value)
    if number != number or number in {float("inf"), float("-inf")}:
        raise DiscoveryConfigError(f"{field} must be a finite number; refuse")
    return number


def require_latitude(value: Any, *, field: str) -> float:
    lat = require_finite_number(value, field=field)
    if lat < -90.0 or lat > 90.0:
        raise DiscoveryConfigError(f"{field}={lat!r} is outside [-90, 90]; refuse")
    return lat


def require_longitude(value: Any, *, field: str) -> float:
    lon = require_finite_number(value, field=field)
    if lon < -180.0 or lon > 180.0:
        raise DiscoveryConfigError(f"{field}={lon!r} is outside [-180, 180]; refuse")
    return lon


def _archive_identity(entry: dict[str, Any], *, index: int) -> tuple[str, ...]:
    identity: list[str] = []
    for field in ("sweep_id", "authority", "vehicle", "endpoint", "district"):
        if field not in entry:
            continue
        identity.append(
            require_nonempty_str(
                entry.get(field), field=f"source_archives[{index}].{field}"
            )
        )
    return tuple(identity)


def _validate_source_archives_v1(archives: list[Any]) -> None:
    seen_identities: set[tuple[str, ...]] = set()
    for i, entry in enumerate(archives):
        require_exact_mapping_keys(
            entry,
            field=f"source_archives[{i}]",
            required=SOURCE_ARCHIVE_ENTRY_KEYS,
        )
        identity: list[str] = []
        for field in SOURCE_ARCHIVE_ENTRY_KEYS:
            text = require_nonempty_str(
                entry.get(field), field=f"source_archives[{i}].{field}"
            )
            identity.append(text)
        sweep_id = identity[0]
        if sweep_id not in PROTOCOL_SWEEP_FAMILIES:
            raise DiscoveryConfigError(
                f"source_archives[{i}].sweep_id={sweep_id!r} must be one of "
                f"protocol families {sorted(PROTOCOL_SWEEP_FAMILIES)}"
            )
        ident = tuple(identity)
        if ident in seen_identities:
            raise DiscoveryConfigError(
                f"source_archives[{i}] duplicates archive identity {ident}; refuse"
            )
        seen_identities.add(ident)


def _validate_source_archives_v2(archives: list[Any]) -> None:
    seen_identities: set[tuple[str, ...]] = set()
    seen_sweep_non_s1: set[str] = set()
    for i, entry in enumerate(archives):
        if not isinstance(entry, dict):
            raise DiscoveryConfigError(f"source_archives[{i}] must be a mapping")
        sweep_id_raw = entry.get("sweep_id")
        sweep_id = require_nonempty_str(
            sweep_id_raw, field=f"source_archives[{i}].sweep_id"
        )
        if sweep_id == "S2":
            raise DiscoveryConfigError(
                "source_archives must not include S2 under schema 0.3; "
                "S2 is registry-only corroboration (binding_operational_restriction_only)"
            )
        required = SOURCE_ARCHIVE_KEYS_BY_SWEEP_V2.get(sweep_id)
        if required is None:
            raise DiscoveryConfigError(
                f"source_archives[{i}].sweep_id={sweep_id!r} is not a schema-0.3 "
                "archive family; refuse"
            )
        require_exact_mapping_keys(
            entry,
            field=f"source_archives[{i}]",
            required=required,
        )
        ident = _archive_identity(entry, index=i)
        if ident in seen_identities:
            raise DiscoveryConfigError(
                f"source_archives[{i}] duplicates archive identity {ident}; refuse"
            )
        seen_identities.add(ident)
        if sweep_id != "S1":
            if sweep_id in seen_sweep_non_s1:
                raise DiscoveryConfigError(
                    f"source_archives[{i}] duplicates non-S1 sweep_id {sweep_id!r}; refuse"
                )
            seen_sweep_non_s1.add(sweep_id)
        if sweep_id == "S3":
            districts = require_unique_nonempty_str_list(
                entry.get("districts"), field=f"source_archives[{i}].districts"
            )
            if tuple(districts) != S3_DISTRICTS_V2:
                raise DiscoveryConfigError(
                    f"source_archives[{i}].districts must be {list(S3_DISTRICTS_V2)}; "
                    "refuse"
                )
        if sweep_id == "S4":
            require_unique_nonempty_str_list(
                entry.get("endpoints"), field=f"source_archives[{i}].endpoints"
            )
            radius = require_actual_int(
                entry.get("proximity_radius_nm"),
                field=f"source_archives[{i}].proximity_radius_nm",
            )
            if radius != S4_PROXIMITY_RADIUS_NM_V2:
                raise DiscoveryConfigError(
                    f"source_archives[{i}].proximity_radius_nm must be "
                    f"{S4_PROXIMITY_RADIUS_NM_V2} (B100); refuse"
                )
            geodesic = require_nonempty_str(
                entry.get("geodesic"), field=f"source_archives[{i}].geodesic"
            )
            if geodesic != S4_GEODESIC_V2:
                raise DiscoveryConfigError(
                    f"source_archives[{i}].geodesic must be {S4_GEODESIC_V2!r}; refuse"
                )
            track_geometry = require_nonempty_str(
                entry.get("track_geometry"),
                field=f"source_archives[{i}].track_geometry",
            )
            if track_geometry != S4_TRACK_GEOMETRY_V2:
                raise DiscoveryConfigError(
                    f"source_archives[{i}].track_geometry must be "
                    f"{S4_TRACK_GEOMETRY_V2!r}; refuse"
                )
        if sweep_id == "S7":
            require_unique_nonempty_str_list(
                entry.get("docket_prefixes"),
                field=f"source_archives[{i}].docket_prefixes",
            )
        if sweep_id == "S8":
            nodes = require_nonempty_str(
                entry.get("nodes"), field=f"source_archives[{i}].nodes"
            )
            if nodes != S4_S8_NODES_V2:
                raise DiscoveryConfigError(
                    f"source_archives[{i}].nodes must be {S4_S8_NODES_V2!r}; refuse"
                )
        if "verification" in entry:
            require_nonempty_str(
                entry.get("verification"), field=f"source_archives[{i}].verification"
            )
        if "positive_evidence_only" in entry:
            flag = require_actual_bool(
                entry.get("positive_evidence_only"),
                field=f"source_archives[{i}].positive_evidence_only",
            )
            if flag is not True:
                raise DiscoveryConfigError(
                    f"source_archives[{i}].positive_evidence_only must be true; refuse"
                )


def _validate_s2_gauge_registry(
    block: dict[str, Any], *, allowed_basins: frozenset[str]
) -> None:
    require_exact_mapping_keys(
        block, field="s2_gauge_registry", required=S2_GAUGE_REGISTRY_KEYS
    )
    interpretation = require_nonempty_str(
        block.get("interpretation"), field="s2_gauge_registry.interpretation"
    )
    if interpretation != S2_GAUGE_INTERPRETATION_V2:
        raise DiscoveryConfigError(
            f"s2_gauge_registry.interpretation must be {S2_GAUGE_INTERPRETATION_V2!r}; "
            "refuse invented numeric-threshold mode"
        )
    require_nonempty_str(block.get("semantics"), field="s2_gauge_registry.semantics")
    row_count = require_actual_int(
        block.get("row_count"), field="s2_gauge_registry.row_count"
    )
    if row_count != S2_GAUGE_ROW_COUNT_V2:
        raise DiscoveryConfigError(
            f"s2_gauge_registry.row_count must be {S2_GAUGE_ROW_COUNT_V2} (B100); refuse"
        )
    gauges = block.get("gauges")
    if not isinstance(gauges, list):
        raise DiscoveryConfigError("s2_gauge_registry.gauges must be a list")
    if len(gauges) != S2_GAUGE_ROW_COUNT_V2:
        raise DiscoveryConfigError(
            f"s2_gauge_registry.gauges must contain exactly {S2_GAUGE_ROW_COUNT_V2} rows"
        )
    seen_ids: set[str] = set()
    for i, row in enumerate(gauges):
        require_exact_mapping_keys(
            row, field=f"s2_gauge_registry.gauges[{i}]", required=S2_GAUGE_ROW_KEYS
        )
        station_id = require_nonempty_str(
            row.get("station_id"), field=f"s2_gauge_registry.gauges[{i}].station_id"
        )
        if station_id in seen_ids:
            raise DiscoveryConfigError(
                f"s2_gauge_registry.gauges duplicate station_id {station_id!r}; refuse"
            )
        seen_ids.add(station_id)
        require_nonempty_str(row.get("name"), field=f"s2_gauge_registry.gauges[{i}].name")
        basin = require_nonempty_str(
            row.get("basin"), field=f"s2_gauge_registry.gauges[{i}].basin"
        )
        if basin not in allowed_basins:
            raise DiscoveryConfigError(
                f"s2_gauge_registry.gauges[{i}].basin={basin!r} is outside "
                "episode-schema navigation_basin vocabulary"
            )
        require_latitude(row.get("lat"), field=f"s2_gauge_registry.gauges[{i}].lat")
        require_longitude(row.get("lon"), field=f"s2_gauge_registry.gauges[{i}].lon")


def _validate_s4_node_registry(
    block: dict[str, Any], *, allowed_basins: frozenset[str]
) -> None:
    require_exact_mapping_keys(
        block, field="s4_node_registry", required=S4_NODE_REGISTRY_KEYS
    )
    status = require_nonempty_str(block.get("status"), field="s4_node_registry.status")
    if status != S4_STATUS_V2:
        raise DiscoveryConfigError(
            f"s4_node_registry.status must be {S4_STATUS_V2!r}; refuse"
        )
    census_variant = require_nonempty_str(
        block.get("census_variant"), field="s4_node_registry.census_variant"
    )
    if census_variant != S4_CENSUS_VARIANT_V2:
        raise DiscoveryConfigError(
            f"s4_node_registry.census_variant must be {S4_CENSUS_VARIANT_V2!r}; refuse"
        )
    census_source = require_nonempty_str(
        block.get("census_source"), field="s4_node_registry.census_source"
    )
    if census_source != S4_CENSUS_SOURCE_V2:
        raise DiscoveryConfigError(
            f"s4_node_registry.census_source must be {S4_CENSUS_SOURCE_V2!r}; refuse"
        )
    radius = require_actual_int(
        block.get("proximity_radius_nm"),
        field="s4_node_registry.proximity_radius_nm",
    )
    if radius != S4_PROXIMITY_RADIUS_NM_V2:
        raise DiscoveryConfigError(
            f"s4_node_registry.proximity_radius_nm must be {S4_PROXIMITY_RADIUS_NM_V2} "
            "(B100); refuse"
        )
    nautical_mile_m = require_actual_int(
        block.get("nautical_mile_m"), field="s4_node_registry.nautical_mile_m"
    )
    if nautical_mile_m != S4_NAUTICAL_MILE_M_V2:
        raise DiscoveryConfigError(
            f"s4_node_registry.nautical_mile_m must be {S4_NAUTICAL_MILE_M_V2}; refuse"
        )
    radius_m = require_actual_int(
        block.get("radius_m"), field="s4_node_registry.radius_m"
    )
    if radius_m != S4_RADIUS_M_V2:
        raise DiscoveryConfigError(
            f"s4_node_registry.radius_m must be {S4_RADIUS_M_V2}; refuse"
        )
    if radius_m != nautical_mile_m * radius:
        raise DiscoveryConfigError(
            "s4_node_registry.radius_m must equal nautical_mile_m * "
            "proximity_radius_nm; refuse"
        )
    boundary = require_nonempty_str(
        block.get("boundary_inequality"), field="s4_node_registry.boundary_inequality"
    )
    if boundary != S4_BOUNDARY_INEQUALITY_V2:
        raise DiscoveryConfigError(
            f"s4_node_registry.boundary_inequality must be {S4_BOUNDARY_INEQUALITY_V2!r}; "
            "refuse"
        )
    geodesic = require_nonempty_str(
        block.get("geodesic"), field="s4_node_registry.geodesic"
    )
    if geodesic != S4_GEODESIC_V2:
        raise DiscoveryConfigError(
            f"s4_node_registry.geodesic must be {S4_GEODESIC_V2!r}; refuse"
        )
    earth_radius_m = require_finite_number(
        block.get("earth_radius_m"), field="s4_node_registry.earth_radius_m"
    )
    if earth_radius_m != S4_EARTH_RADIUS_M_V2:
        raise DiscoveryConfigError(
            f"s4_node_registry.earth_radius_m must be {S4_EARTH_RADIUS_M_V2}; refuse"
        )
    track_geometry = require_nonempty_str(
        block.get("track_geometry"), field="s4_node_registry.track_geometry"
    )
    if track_geometry != S4_TRACK_GEOMETRY_V2:
        raise DiscoveryConfigError(
            f"s4_node_registry.track_geometry must be {S4_TRACK_GEOMETRY_V2!r}; refuse"
        )
    for flag_key in (
        "texas_gulf_in_default",
        "puget_sound_in_default",
        "great_lakes_in_default",
    ):
        flag = require_actual_bool(
            block.get(flag_key), field=f"s4_node_registry.{flag_key}"
        )
        if flag is not False:
            raise DiscoveryConfigError(
                f"s4_node_registry.{flag_key} must be false; refuse"
            )
    row_count = require_actual_int(
        block.get("row_count"), field="s4_node_registry.row_count"
    )
    if row_count != S4_NODE_ROW_COUNT_V2:
        raise DiscoveryConfigError(
            f"s4_node_registry.row_count must be {S4_NODE_ROW_COUNT_V2} (census A); refuse"
        )
    nodes = block.get("nodes")
    if not isinstance(nodes, list):
        raise DiscoveryConfigError("s4_node_registry.nodes must be a list")
    if len(nodes) != S4_NODE_ROW_COUNT_V2:
        raise DiscoveryConfigError(
            f"s4_node_registry.nodes must contain exactly {S4_NODE_ROW_COUNT_V2} rows"
        )
    seen_ids: set[str] = set()
    for i, row in enumerate(nodes):
        require_exact_mapping_keys(
            row, field=f"s4_node_registry.nodes[{i}]", required=S4_NODE_ROW_KEYS
        )
        node_id = require_nonempty_str(
            row.get("node_id"), field=f"s4_node_registry.nodes[{i}].node_id"
        )
        if node_id in seen_ids:
            raise DiscoveryConfigError(
                f"s4_node_registry.nodes duplicate node_id {node_id!r}; refuse"
            )
        seen_ids.add(node_id)
        require_source_native_str(
            row.get("name"), field=f"s4_node_registry.nodes[{i}].name"
        )
        require_latitude(row.get("lat"), field=f"s4_node_registry.nodes[{i}].lat")
        require_longitude(row.get("lon"), field=f"s4_node_registry.nodes[{i}].lon")
        basin = require_nonempty_str(
            row.get("basin"), field=f"s4_node_registry.nodes[{i}].basin"
        )
        if basin not in allowed_basins:
            raise DiscoveryConfigError(
                f"s4_node_registry.nodes[{i}].basin={basin!r} is outside "
                "episode-schema navigation_basin vocabulary"
            )
        require_nonempty_str(
            row.get("nav_unit_id"), field=f"s4_node_registry.nodes[{i}].nav_unit_id"
        )


def load_prereg_rules(repo_root: Path | None = None) -> dict[str, Any]:
    """Load and validate live preregistration config.

    Fail closed if the file is absent, keys are unknown/missing/duplicated, or
    required Lock-1 blocks (D1–D11, D13 including target-date mapping M) are
    empty/null. Does not invent districts, keywords, dates, thresholds, or
    D13 values. D12 remains deliberately unregistered.

    Note: loading a structurally complete config does **not** authorize a sweep.
    See ``grainsys.discovery.governance.assert_sweep_authorized`` (N3).
    """
    root = repo_root if repo_root is not None else REPO_ROOT
    path = prereg_rules_path(root)
    if not path.is_file():
        raise DiscoveryConfigError(
            f"Missing live preregistration config: {path}. "
            "Copy _prereg_rules.template.yaml only after A+B close Phase 0 decisions. "
            "Sweeps are blocked until then."
        )

    data = _load_yaml_mapping(path)
    schema_version = require_nonempty_str(
        data.get("schema_version"), field="schema_version"
    )
    if schema_version not in ALLOWED_PREREG_SCHEMA_VERSIONS:
        raise DiscoveryConfigError(
            f"schema_version={schema_version!r} is not one of "
            f"{sorted(ALLOWED_PREREG_SCHEMA_VERSIONS)}; refuse"
        )
    top_keys = (
        PREREG_TOP_LEVEL_KEYS_V2
        if schema_version == PREREG_SCHEMA_VERSION_V2
        else PREREG_TOP_LEVEL_KEYS
    )
    require_exact_mapping_keys(
        data, field="prereg_rules.yaml", required=top_keys
    )
    require_nonempty_str(data.get("governing_adr"), field="governing_adr")

    sample = require_exact_mapping_keys(
        data.get("sample_period"),
        field="sample_period",
        required=SAMPLE_PERIOD_KEYS,
    )
    start = parse_iso_calendar_date(
        sample.get("sample_start"), field="sample_period.sample_start"
    )
    end = parse_iso_calendar_date(
        sample.get("sample_end"), field="sample_period.sample_end"
    )
    if start > end:
        raise DiscoveryConfigError(
            f"sample_period.sample_start ({start.isoformat()}) must be <= "
            f"sample_end ({end.isoformat()})"
        )
    sample["sample_start"] = start.isoformat()
    sample["sample_end"] = end.isoformat()

    corridors = require_exact_mapping_keys(
        data.get("corridors"), field="corridors", required=CORRIDORS_KEYS
    )
    basins = require_unique_nonempty_str_list(
        corridors.get("navigation_basins"),
        field="corridors.navigation_basins",
    )
    allowed_basins = _load_navigation_basin_vocab(root)
    unknown_basins = sorted(set(basins) - allowed_basins)
    if unknown_basins:
        raise DiscoveryConfigError(
            "corridors.navigation_basins contains values outside episode-schema "
            f"vocabulary: {unknown_basins}"
        )

    archives = data.get("source_archives")
    if not isinstance(archives, list) or len(archives) == 0:
        raise DiscoveryConfigError(
            "source_archives must be a non-empty list (D3); no hidden district defaults."
        )
    if schema_version == PREREG_SCHEMA_VERSION_V2:
        _validate_source_archives_v2(archives)
    else:
        _validate_source_archives_v1(archives)

    keywords = require_exact_mapping_keys(
        data.get("keyword_policy"),
        field="keyword_policy",
        required=KEYWORD_POLICY_KEYS,
    )
    require_unique_nonempty_str_list(keywords.get("terms"), field="keyword_policy.terms")
    match = require_nonempty_str(keywords.get("match"), field="keyword_policy.match")
    if match not in ALLOWED_KEYWORD_MATCH_MODES:
        raise DiscoveryConfigError(
            f"keyword_policy.match={match!r} is not an allowed mode "
            f"({sorted(ALLOWED_KEYWORD_MATCH_MODES)}); refuse invented match policy."
        )
    case_sensitive = keywords.get("case_sensitive")
    if not isinstance(case_sensitive, bool):
        raise DiscoveryConfigError(
            "keyword_policy.case_sensitive must be an actual bool "
            f"(got {type(case_sensitive).__name__}); refuse coercion"
        )
    require_unique_nonempty_str_list(
        keywords.get("fields"), field="keyword_policy.fields"
    )

    candidates = require_exact_mapping_keys(
        data.get("candidates"), field="candidates", required=CANDIDATES_KEYS
    )
    table_path = require_repo_contained_relative_path(
        candidates.get("table_path"),
        field="candidates.table_path",
        repo_root=root,
    )
    candidates["table_path"] = table_path
    candidates["id_prefix"] = require_safe_path_component(
        candidates.get("id_prefix"),
        field="candidates.id_prefix",
    )
    validate_pre_mint_field_keys(
        candidates.get("ordering_keys"),
        field="candidates.ordering_keys",
    )
    stable_id_key = candidates.get("stable_id_key")
    if stable_id_key is not None:
        candidates["stable_id_key"] = validate_stable_id_key_name(
            stable_id_key,
            field="candidates.stable_id_key",
        )

    capture = require_exact_mapping_keys(
        data.get("capture"), field="capture", required=CAPTURE_KEYS
    )
    capture["sweeps_subdir"] = require_safe_relative_path(
        capture.get("sweeps_subdir"),
        field="capture.sweeps_subdir",
    )
    rehome_policy = require_nonempty_str(
        capture.get("rehome_policy"), field="capture.rehome_policy"
    )
    if rehome_policy not in REHOME_POLICIES:
        raise DiscoveryConfigError(
            f"capture.rehome_policy={rehome_policy!r} must be one of "
            f"{sorted(REHOME_POLICIES)}; refuse unauthorized rehome token "
            "(ADR-0013)"
        )
    capture["rehome_policy"] = rehome_policy

    coverage = require_exact_mapping_keys(
        data.get("coverage"), field="coverage", required=COVERAGE_KEYS
    )
    if coverage.get("absent_must_be_explicit") is not True:
        raise DiscoveryConfigError(
            "coverage.absent_must_be_explicit must be true (D7); silent gaps forbidden."
        )
    coverage["records_dir"] = require_repo_contained_relative_path(
        coverage.get("records_dir"),
        field="coverage.records_dir",
        repo_root=root,
    )
    require_nonempty_str(
        coverage.get("gap_policy_notes"), field="coverage.gap_policy_notes"
    )
    coverage["absence_generating_families"] = _require_s1_s8_subset(
        coverage.get("absence_generating_families"),
        field="coverage.absence_generating_families",
        allow_empty=True,
    )
    coverage["source_identity_keys"] = _require_identity_key_subset(
        coverage.get("source_identity_keys"),
        field="coverage.source_identity_keys",
    )

    physical = require_exact_mapping_keys(
        data.get("physical_thresholds"),
        field="physical_thresholds",
        required=PHYSICAL_THRESHOLDS_KEYS,
    )
    _validate_physical_thresholds(physical)

    windows = require_exact_mapping_keys(
        data.get("event_windows"),
        field="event_windows",
        required=EVENT_WINDOWS_KEYS,
    )
    _validate_event_windows(windows)

    calibration = require_exact_mapping_keys(
        data.get("calibration_set"),
        field="calibration_set",
        required=CALIBRATION_SET_KEYS,
    )
    _validate_calibration_set(calibration)

    shocks = require_exact_mapping_keys(
        data.get("concurrent_shocks"),
        field="concurrent_shocks",
        required=CONCURRENT_SHOCKS_KEYS,
    )
    _validate_concurrent_shocks(shocks)

    grid = require_exact_mapping_keys(
        data.get("analysis_anchor_grid"),
        field="analysis_anchor_grid",
        required=ANALYSIS_ANCHOR_GRID_KEYS,
    )
    for key in ANALYSIS_ANCHOR_GRID_KEYS:
        require_nonempty_str(grid[key], field=f"analysis_anchor_grid.{key}")

    if schema_version == PREREG_SCHEMA_VERSION_V2:
        s2 = data.get("s2_gauge_registry")
        if not isinstance(s2, dict):
            raise DiscoveryConfigError("s2_gauge_registry must be a mapping")
        _validate_s2_gauge_registry(s2, allowed_basins=allowed_basins)
        s4 = data.get("s4_node_registry")
        if not isinstance(s4, dict):
            raise DiscoveryConfigError("s4_node_registry must be a mapping")
        _validate_s4_node_registry(s4, allowed_basins=allowed_basins)
        s4_archives = [
            entry
            for entry in archives
            if isinstance(entry, dict) and entry.get("sweep_id") == "S4"
        ]
        for entry in s4_archives:
            if entry.get("proximity_radius_nm") != s4["proximity_radius_nm"]:
                raise DiscoveryConfigError(
                    "S4 source_archives.proximity_radius_nm must match "
                    "s4_node_registry.proximity_radius_nm; refuse"
                )
            if entry.get("track_geometry") != s4["track_geometry"]:
                raise DiscoveryConfigError(
                    "S4 source_archives.track_geometry must match "
                    "s4_node_registry.track_geometry; refuse"
                )
            if entry.get("geodesic") != s4["geodesic"]:
                raise DiscoveryConfigError(
                    "S4 source_archives.geodesic must match "
                    "s4_node_registry.geodesic; refuse"
                )
        marker = require_nonempty_str(data.get("marker"), field="marker")
        if marker != PREREG_MARKER_V2:
            raise DiscoveryConfigError(
                f"marker must be {PREREG_MARKER_V2!r}; refuse"
            )

    return data
