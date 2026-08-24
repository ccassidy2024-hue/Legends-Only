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
SAMPLE_PERIOD_KEYS: tuple[str, ...] = ("sample_start", "sample_end")
CORRIDORS_KEYS: tuple[str, ...] = ("navigation_basins",)
SOURCE_ARCHIVE_ENTRY_KEYS: tuple[str, ...] = (
    "sweep_id",
    "authority",
    "district",
    "vehicle",
    "endpoint",
)
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


def _require_s1_s8_subset(value: Any, *, field: str) -> list[str]:
    families = require_unique_nonempty_str_list(value, field=field)
    unknown = sorted(set(families) - PROTOCOL_SWEEP_FAMILIES)
    if unknown:
        raise DiscoveryConfigError(
            f"{field} contains values outside S1–S8: {unknown}"
        )
    return families


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
    require_exact_mapping_keys(
        data, field="prereg_rules.yaml", required=PREREG_TOP_LEVEL_KEYS
    )

    schema_version = require_nonempty_str(
        data.get("schema_version"), field="schema_version"
    )
    if schema_version != PREREG_SCHEMA_VERSION:
        raise DiscoveryConfigError(
            f"schema_version={schema_version!r} is not {PREREG_SCHEMA_VERSION!r}; refuse"
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

    return data
