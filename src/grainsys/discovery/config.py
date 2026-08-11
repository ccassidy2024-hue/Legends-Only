"""Fail-closed loader for Phase 0 preregistration discovery rules."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_PREREG_RELATIVE = Path("config") / "discovery" / "prereg_rules.yaml"


class DiscoveryConfigError(RuntimeError):
    """Raised when preregistration config is missing or incomplete."""


def prereg_rules_path(repo_root: Path | None = None) -> Path:
    root = repo_root if repo_root is not None else REPO_ROOT
    return root / DEFAULT_PREREG_RELATIVE


def _require_non_empty_list(block: dict[str, Any], key: str, *, where: str) -> list[Any]:
    value = block.get(key)
    if not isinstance(value, list) or len(value) == 0:
        raise DiscoveryConfigError(
            f"{where}.{key} must be a non-empty list in live prereg_rules.yaml "
            "(no hidden defaults; fill after Phase 0 decisions)."
        )
    return value


def _require_mapping(data: dict[str, Any], key: str) -> dict[str, Any]:
    value = data.get(key)
    if not isinstance(value, dict):
        raise DiscoveryConfigError(f"prereg_rules.yaml missing required mapping: {key}")
    return value


def load_prereg_rules(repo_root: Path | None = None) -> dict[str, Any]:
    """Load and validate live preregistration config.

    Fail closed if the file is absent or required blocks are empty/null.
    Does not invent districts, keywords, dates, or ordering keys.
    """
    path = prereg_rules_path(repo_root)
    if not path.is_file():
        raise DiscoveryConfigError(
            f"Missing live preregistration config: {path}. "
            "Copy _prereg_rules.template.yaml only after A+B close D1–D11. "
            "Sweeps are blocked until then."
        )

    with path.open(encoding="utf-8") as fh:
        data = yaml.safe_load(fh)

    if not isinstance(data, dict):
        raise DiscoveryConfigError(f"{path} must contain a YAML mapping")

    sample = _require_mapping(data, "sample_period")
    if sample.get("start_date") in (None, "") or sample.get("end_date") in (None, ""):
        raise DiscoveryConfigError(
            "sample_period.start_date and end_date must be set (D1); no defaults."
        )

    corridors = _require_mapping(data, "corridors")
    _require_non_empty_list(corridors, "navigation_basins", where="corridors")

    archives = data.get("source_archives")
    if not isinstance(archives, list) or len(archives) == 0:
        raise DiscoveryConfigError(
            "source_archives must be a non-empty list (D3); no hidden district defaults."
        )
    for i, entry in enumerate(archives):
        if not isinstance(entry, dict):
            raise DiscoveryConfigError(f"source_archives[{i}] must be a mapping")
        for field in ("sweep_id", "authority", "district", "vehicle", "endpoint"):
            if entry.get(field) in (None, ""):
                raise DiscoveryConfigError(
                    f"source_archives[{i}].{field} is required (D3); refuse null/empty."
                )

    keywords = _require_mapping(data, "keyword_policy")
    _require_non_empty_list(keywords, "terms", where="keyword_policy")
    if keywords.get("match") in (None, ""):
        raise DiscoveryConfigError("keyword_policy.match is required (D4); no default.")
    if keywords.get("case_sensitive") is None:
        raise DiscoveryConfigError(
            "keyword_policy.case_sensitive is required (D4); no default."
        )
    _require_non_empty_list(keywords, "fields", where="keyword_policy")

    candidates = _require_mapping(data, "candidates")
    if candidates.get("table_path") in (None, ""):
        raise DiscoveryConfigError("candidates.table_path is required (D5); no default.")
    if candidates.get("id_prefix") in (None, ""):
        raise DiscoveryConfigError("candidates.id_prefix is required (D5); no default.")
    _require_non_empty_list(candidates, "ordering_keys", where="candidates")

    capture = _require_mapping(data, "capture")
    if capture.get("sweeps_subdir") in (None, ""):
        raise DiscoveryConfigError("capture.sweeps_subdir is required (D6 path helper).")

    coverage = _require_mapping(data, "coverage")
    if coverage.get("absent_must_be_explicit") is not True:
        raise DiscoveryConfigError(
            "coverage.absent_must_be_explicit must be true (D7); silent gaps forbidden."
        )

    return data
