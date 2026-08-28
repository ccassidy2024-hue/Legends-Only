"""Episode Ledger: schema validation, derived severity, and ledger rendering.

Milestone 1 pre-registration. Rules live in `research/episodes/EPISODE_PROTOCOL.md`;
the machine-readable field spec is `research/episodes/episode_schema.yaml`, which is
the single source of truth. This module enforces it.

Load-bearing properties:

1. `market_outcomes_reviewed` must be False on every entry before the freeze tag.
2. Severity metrics are RAW physical evidence; `severity_class` is DERIVED and stays
   null until Phase 0 cutpoints are registered.
3. Date-only anchors must not invent clock times (`public_anchor_precision`).
4. Report both N_episodes and N_independent_driver_clusters — no 1.5 ratio rule.

Do not weaken a check to make CI green (CLAUDE.md hard rule 16).
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from collections import Counter
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any

import yaml

from grainsys.lineage import (
    LineageError,
    check_universe_accounting,
    validate_candidate_ids_shape,
    validate_candidate_universe_version,
)

SCHEMA_PATH = Path("research/episodes/episode_schema.yaml")
ENTRIES_DIR = Path("research/episodes/entries")
LEDGER_PATH = Path("research/episodes/EPISODE_LEDGER.md")

BEGIN_MARK = "<!-- BEGIN GENERATED: episode-summary -->"
END_MARK = "<!-- END GENERATED: episode-summary -->"

DERIVED_FIELDS = (
    "duration_days",
    "severity_subscores",
    "severity_score",
    "severity_class",
    "severity_class_kind",
    "severity_completeness",
    "sample_membership",
    "preregistration_frozen_at",
    "freeze_commit",
    "content_hash",
    "lineage_candidate_id",
)

BANNED_METRIC_TOKENS = (
    "price",
    "spread",
    "basis",
    "premium",
    "bid",
    "offer",
    "freight_rate",
    "freight_cost",
    "tariff",
    "futures",
    "settle",
    "open_interest",
    "positioning",
    "return",
)

SOURCE_REQUIRED_KEYS = ("ref", "tier", "publisher", "title", "url", "retrieved_on", "quote")

WATERWAY_CLASSES = {
    "low_water",
    "high_water_flood",
    "lock_outage",
    "channel_obstruction",
    "waterway_closure_other",
    "ice_or_seasonal_closure",
}
NODE_CLASSES = {
    "gulf_terminal_disruption",
    "port_infrastructure_outage",
    "rail_service_disruption",
    "bridge_or_landside_outage",
}


@dataclass
class Findings:
    """Errors fail the build; warnings force a `needs_review` conversation."""

    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def error(self, where: str, code: str, msg: str) -> None:
        self.errors.append(f"{where}: [{code}] {msg}")

    def warn(self, where: str, code: str, msg: str) -> None:
        self.warnings.append(f"{where}: [{code}] {msg}")

    @property
    def ok(self) -> bool:
        return not self.errors


def load_schema(path: str | Path = SCHEMA_PATH) -> dict[str, Any]:
    with Path(path).open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def load_entries(entries_dir: str | Path = ENTRIES_DIR) -> list[dict[str, Any]]:
    """Load every episode YAML. `_file` carries the filename for error messages."""
    entries_dir = Path(entries_dir)
    files = sorted(entries_dir.glob("*.yaml")) + sorted(entries_dir.glob("*.yml"))
    out: list[dict[str, Any]] = []
    for f in files:
        if f.stem.startswith("_"):
            continue
        with f.open(encoding="utf-8") as fh:
            d = yaml.safe_load(fh) or {}
        d["_file"] = f.name
        out.append(d)
    return out


def _as_date(v: Any) -> date | None:
    if isinstance(v, datetime):
        return v.date()
    if isinstance(v, date):
        return v
    if isinstance(v, str):
        try:
            return date.fromisoformat(v[:10])
        except ValueError:
            return None
    return None


def _as_datetime(v: Any) -> datetime | None:
    """Parse an exact timestamp. Bare dates are not timestamps."""
    if isinstance(v, datetime):
        return v
    if isinstance(v, date) and not isinstance(v, datetime):
        return None
    if isinstance(v, str):
        s = v.strip()
        if len(s) <= 10:
            return None
        try:
            return datetime.fromisoformat(s.replace("Z", "+00:00"))
        except ValueError:
            return None
    return None


def _requirement_map(schema: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {f["name"]: f for f in schema["fields"]}


def _is_blank(v: Any) -> bool:
    return v is None or v == "" or v == [] or v == {}


def validate_entry(entry: dict[str, Any], schema: dict[str, Any], fx: Findings) -> None:
    """Apply the per-entry error and warning rules from the schema."""
    where = entry.get("_file", entry.get("episode_id", "<unknown>"))
    vocab = schema["vocabularies"]
    fields = _requirement_map(schema)
    status = entry.get("status")
    accepted = status == "accepted"

    if entry.get("schema_version") not in schema["supported_versions"]:
        fx.error(where, "E01", f"unsupported schema_version {entry.get('schema_version')!r}")

    eid = entry.get("episode_id", "")
    if not re.fullmatch(r"EP-[0-9]{4}-[0-9]{3}", str(eid)):
        fx.error(where, "E02", f"episode_id {eid!r} must match EP-YYYY-NNN")
    elif "_file" in entry and not Path(entry["_file"]).stem.startswith(str(eid)):
        fx.error(where, "E02", f"filename must start with episode_id {eid!r}")

    for name, spec in fields.items():
        if spec.get("requirement") != "always":
            continue
        if name not in entry:
            fx.error(where, "E04", f"missing required field '{name}'")
            continue
        v = entry[name]
        scalar = spec.get("type") in {"str", "enum", "date", "datetime", "int", "float"}
        if scalar and not spec.get("nullable") and _is_blank(v) and not isinstance(v, bool):
            fx.error(where, "E04", f"required field '{name}' is empty")

    for name, spec in fields.items():
        v = entry.get(name)
        if _is_blank(v):
            continue
        vname = spec.get("vocab")
        if vname and vname in vocab and spec.get("type") in {"enum", "int", "str"}:
            allowed = vocab[vname]
            allowed = list(allowed.keys()) if isinstance(allowed, dict) else allowed
            if v not in allowed:
                fx.error(where, "E05", f"{name}={v!r} not in vocabulary '{vname}'")
        iname = spec.get("item_vocab")
        if iname and iname in vocab and isinstance(v, list):
            allowed = vocab[iname]
            allowed = list(allowed.keys()) if isinstance(allowed, dict) else allowed
            for item in v:
                key = item.get("code") if isinstance(item, dict) else item
                if key not in allowed:
                    fx.error(where, "E05", f"{name} item {key!r} not in vocabulary '{iname}'")

    for name in DERIVED_FIELDS:
        if name in entry and not _is_blank(entry[name]):
            fx.error(where, "E06", f"derived field '{name}' must be null/empty in the entry file")

    if entry.get("market_outcomes_reviewed") is not False:
        fx.error(
            where,
            "E07",
            "market_outcomes_reviewed must be false before the pre-registration freeze",
        )

    if entry.get("anchor_precision_days") not in vocab["anchor_precision_days"]:
        fx.error(where, "E08", "anchor_precision_days must be one of 0, 1, 3, 7")

    pap = entry.get("public_anchor_precision")
    if pap in vocab.get("public_anchor_precision", ["date", "timestamp"]):
        ats = entry.get("anchor_ts")
        if pap == "date" and not _is_blank(ats):
            fx.error(
                where,
                "E27",
                "public_anchor_precision=date requires anchor_ts null "
                "(do not invent a clock time for date-only evidence)",
            )
        if pap == "timestamp" and (_is_blank(ats) or _as_datetime(ats) is None):
            fx.error(
                where,
                "E27",
                "public_anchor_precision=timestamp requires a real anchor_ts datetime",
            )

    anchor = _as_date(entry.get("public_anchor"))
    onset = _as_date(entry.get("physical_onset"))
    end = _as_date(entry.get("end_date"))
    peak = _as_date(entry.get("peak_severity_date"))
    if anchor is None:
        fx.error(where, "E09", "public_anchor missing or unparseable")
    else:
        if onset and onset > anchor:
            fx.error(where, "E09", "physical_onset is after public_anchor")
        if end and end < anchor:
            fx.error(where, "E09", "end_date is before public_anchor")
        if peak and (peak < anchor or (end and peak > end)):
            fx.error(where, "E09", "peak_severity_date outside [public_anchor, end_date]")
        if str(eid)[3:7].isdigit() and int(str(eid)[3:7]) not in {anchor.year, 0}:
            fx.warn(where, "W13", "episode_id year does not match public_anchor year")

    primary = entry.get("primary_sources") or []
    secondary = entry.get("secondary_sources") or []
    n_tier1 = sum(1 for s in primary if s.get("tier") == 1)
    if accepted and n_tier1 < 2:
        fx.error(where, "E10", f"accepted needs >= 2 tier-1 primary_sources, found {n_tier1}")
    for s in list(primary) + list(secondary):
        missing = [k for k in SOURCE_REQUIRED_KEYS if _is_blank(s.get(k))]
        if missing:
            fx.error(where, "E11", f"source {s.get('ref')!r} missing {missing}")
        if s.get("tier") not in (1, 2):
            fx.error(where, "E24", f"source {s.get('ref')!r} tier must be 1 or 2 (never tier 3)")

    refs = {s.get("ref") for s in primary}
    if entry.get("anchor_source_ref") and entry["anchor_source_ref"] not in refs:
        fx.error(where, "E20", "anchor_source_ref does not resolve to a primary_sources ref")

    metrics = entry.get("severity_metrics") or []
    if accepted and len(metrics) < 2:
        fx.error(where, "E12", f"accepted needs >= 2 severity_metrics, found {len(metrics)}")
    dims = set(schema["severity"]["dimensions"])
    for m in metrics:
        if m.get("dimension") not in dims:
            fx.error(where, "E21", f"severity metric dimension {m.get('dimension')!r} unknown")
        blob = f"{m.get('name', '')} {m.get('units', '')}".lower()
        hit = [t for t in BANNED_METRIC_TOKENS if t in blob]
        if hit:
            fx.error(where, "E22", f"severity metric {m.get('name')!r} looks market-derived: {hit}")
        if not _is_blank(m.get("as_of_date")) and _as_date(m.get("as_of_date")) is None:
            fx.error(where, "E09", f"severity metric {m.get('name')!r} has malformed as_of_date")

    subs = entry.get("substitution_channels") or []
    if accepted and len(subs) < 3:
        fx.error(where, "E13", f"accepted needs >= 3 substitution_channels, found {len(subs)}")
    for s in subs:
        if s.get("channel") not in vocab["substitution_channel"]:
            fx.error(where, "E05", f"substitution channel {s.get('channel')!r} not in vocabulary")
        if s.get("documented_use") not in vocab["documented_use"]:
            fx.error(where, "E05", f"documented_use {s.get('documented_use')!r} not in vocabulary")

    if accepted and entry.get("publicly_knowable_at_anchor") is not True:
        fx.error(where, "E14", "accepted requires publicly_knowable_at_anchor == true")
    if accepted and entry.get("source_confidence") == "low":
        fx.error(where, "E15", "accepted requires source_confidence != low")

    if status in {"accepted", "rejected"}:
        for name in ("reviewed_by", "reviewed_date", "anchor_agreement"):
            if _is_blank(entry.get(name)):
                fx.error(where, "E18", f"'{name}' required when status is {status}")
        if entry.get("reviewed_by") and entry.get("reviewed_by") == entry.get("recorded_by"):
            fx.error(where, "E16", "reviewed_by must differ from recorded_by")
    if entry.get("decision") in {"reject", "review"} and not (entry.get("decision_reasons") or []):
        fx.error(where, "E17", "reject/review requires at least one decision_reason code")

    ec = entry.get("event_class")
    if ec in WATERWAY_CLASSES and _is_blank(entry.get("river_reaches")):
        fx.error(where, "E18", f"river_reaches required for event_class '{ec}'")
    if ec in NODE_CLASSES and _is_blank(entry.get("ports_or_nodes")):
        fx.error(where, "E18", f"ports_or_nodes required for event_class '{ec}'")
    if entry.get("growing_region_overlap") != "none" and _is_blank(entry.get("growing_regions")):
        fx.error(where, "E18", "growing_regions required when growing_region_overlap != none")
    classes = {entry.get("crop_contamination_class"), entry.get("macro_contamination_class")}
    if classes & {"C", "D"} and _is_blank(entry.get("contamination_rationale")):
        fx.error(where, "E18", "contamination_rationale required for class C or D")
    if not entry.get("ongoing_at_sample_end") and _is_blank(entry.get("end_date")):
        fx.error(where, "E18", "end_date required unless ongoing_at_sample_end is true")

    if not (entry.get("concurrent_shocks") or []) and entry.get("sweep_performed") is not True:
        fx.error(where, "E19", "empty concurrent_shocks requires sweep_performed: true")

    mech = entry.get("physical_mechanism") or ""
    if len(mech.split()) > 150:
        fx.error(where, "E23", f"physical_mechanism is {len(mech.split())} words (max 150)")

    example_ids = set(schema["sample"]["example_ids_excluded"])
    if entry.get("example") and eid not in example_ids:
        fx.error(where, "E25", "example: true is reserved for the registered example entry")

    if entry.get("anchor_precision_days") == 7:
        fx.warn(where, "W01", "anchor_precision_days == 7; review the anchor")
    if n_tier1 == 1 or entry.get("source_confidence") == "medium":
        fx.warn(where, "W02", "single tier-1 source or medium confidence; review")
    if classes & {"C", "D"}:
        fx.warn(where, "W03", f"contamination class {sorted(classes & {'C', 'D'})}; review")
    if entry.get("source_conflicts"):
        fx.warn(where, "W08", "source_conflicts recorded; review")
    if entry.get("anchor_agreement") == "disagree":
        fx.warn(where, "W09", "researchers disagree on the anchor; resolve before freeze")
    origins = {d.get("origin") for d in entry.get("discovery_trail") or []}
    if origins & {"memory", "llm"} and "sweep" not in origins:
        fx.warn(where, "W06", "candidate from memory/LLM with no sweep confirmation (see R6/R2)")
    if entry.get("outcome_exposure_log"):
        fx.warn(where, "W14", "outcome exposure logged; hand this entry to the other researcher")

    uid = entry.get("underlying_driver_id")
    cid = entry.get("cluster_id")
    if uid and cid and uid != cid:
        fx.warn(
            where,
            "W15",
            "cluster_id differs from underlying_driver_id; default is equality "
            "unless a documented independence/dependence ruling justifies otherwise",
        )

    try:
        validate_candidate_ids_shape(entry.get("candidate_ids"))
    except LineageError as exc:
        fx.error(where, "E30", str(exc))

    cu_version = entry.get("candidate_universe_version")
    if not _is_blank(cu_version):
        try:
            validate_candidate_universe_version(cu_version)
        except LineageError as exc:
            fx.error(where, "E31", str(exc))


def compute_derived(entry: dict[str, Any], schema: dict[str, Any]) -> dict[str, Any]:
    """Return derived fields. Severity class stays None until cutpoints are registered."""
    sev = schema["severity"]
    dims: list[str] = sev["dimensions"]
    out: dict[str, Any] = {}

    anchor, end = _as_date(entry.get("public_anchor")), _as_date(entry.get("end_date"))
    out["duration_days"] = (end - anchor).days if anchor and end else None

    metrics = entry.get("severity_metrics") or []
    by_dim: dict[str, list[dict[str, Any]]] = {d: [] for d in dims}
    for m in metrics:
        if m.get("dimension") in by_dim:
            by_dim[m["dimension"]].append(m)

    out["severity_completeness"] = round(sum(1 for d in dims if by_dim[d]) / len(dims), 3)

    cutpoints = sev.get("cutpoints") or {}
    registered = bool(sev.get("cutpoints_registered")) and bool(cutpoints)
    ec = entry.get("event_class")
    subscores: dict[str, int | None] = {}
    for d in dims:
        if not by_dim[d]:
            subscores[d] = None
            continue
        if d == "d5_restrictiveness":
            ordinal = sev["restrictiveness_ordinal"]
            vals = [ordinal.get(str(m.get("value"))) for m in by_dim[d]]
            vals = [v for v in vals if v is not None]
            subscores[d] = max(vals) if vals else None
            continue
        cuts = (cutpoints.get(ec) or {}).get(d) if registered else None
        if not cuts:
            subscores[d] = None
            continue
        numeric = [m.get("value") for m in by_dim[d] if isinstance(m.get("value"), (int, float))]
        if not numeric:
            subscores[d] = None
            continue
        x = max(numeric)
        p50, p90, p99 = cuts
        subscores[d] = 0 if x < p50 else 1 if x < p90 else 2 if x < p99 else 3

    out["severity_subscores"] = subscores
    # Score only when cutpoints are registered AND every dimension is scored.
    # d5 alone must not produce a severity_class while Phase 0 is incomplete.
    if registered and all(v is not None for v in subscores.values()):
        score = int(sum(v for v in subscores.values() if v is not None))
        out["severity_score"] = score
        out["severity_class"] = next(
            (k for k, (lo, hi) in sev["bands"].items() if lo <= score <= hi),
            None,
        )
        # Full-sample percentile bands are descriptive ex post by default.
        out["severity_class_kind"] = sev.get(
            "default_classification_kind", "ex_post_descriptive"
        )
    else:
        out["severity_score"] = None
        out["severity_class"] = None
        out["severity_class_kind"] = None

    prim = set(schema["sample"]["primary_contamination_classes"])
    ext = set(schema["sample"]["extended_contamination_classes"])
    cls = {entry.get("crop_contamination_class"), entry.get("macro_contamination_class")}
    if cls - (prim | ext):
        out["sample_membership"] = "excluded"
    elif cls & ext:
        out["sample_membership"] = "extended"
    else:
        out["sample_membership"] = "primary"

    payload = {k: v for k, v in entry.items() if k not in DERIVED_FIELDS and k != "_file"}
    out["content_hash"] = hashlib.sha256(
        json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
    ).hexdigest()[:16]
    return out


def assert_severity_kind_honesty(
    entry: dict[str, Any],
    derived: dict[str, Any],
    fx: Findings,
) -> None:
    """Prevent ex-post metric timing from masquerading as contemporaneous class."""
    where = entry.get("_file", entry.get("episode_id", "<unknown>"))
    if derived.get("severity_class_kind") != "contemporaneous":
        return
    anchor = _as_date(entry.get("public_anchor"))
    if anchor is None:
        return
    for m in entry.get("severity_metrics") or []:
        as_of = _as_date(m.get("as_of_date"))
        if as_of and as_of > anchor:
            fx.error(
                where,
                "E28",
                "severity_class_kind=contemporaneous but metric "
                f"{m.get('name')!r} has as_of_date after public_anchor",
            )


def first_usable_analysis_anchor(
    public_anchor: Any,
    public_anchor_precision: str,
    analysis_anchors: list[Any] | tuple[Any, ...] | Any,
    anchor_ts: Any = None,
) -> Any | None:
    """Map a public_anchor to the first usable analysis/panel anchor.

    PRIMARY conservative convention (preregistered):

    - precision ``date``: first analysis anchor whose **calendar date is
      strictly after** ``public_anchor``. Never treat the date as midnight,
      noon, BOD, or EOD. Same-calendar-day weekly anchors are **not** usable.
    - precision ``timestamp``: first analysis anchor with
      ``anchor_ts <= analysis_anchor_ts``, only when ``anchor_ts`` is a real
      source-supported timestamp.

    Does not modify ``panel.py``. Other same-day/date-only mappings are
    robustness assumptions only and must be labeled as such.
    """
    anchors = list(analysis_anchors)
    if not anchors:
        return None

    if public_anchor_precision == "date":
        pa = _as_date(public_anchor)
        if pa is None:
            raise ValueError("public_anchor is missing or unparseable")
        for a in anchors:
            ad = _as_date(a)
            if ad is not None and ad > pa:
                return a
        return None

    if public_anchor_precision == "timestamp":
        ts = _as_datetime(anchor_ts)
        if ts is None:
            raise ValueError(
                "timestamp precision requires a real anchor_ts; "
                "do not invent a clock time from a date"
            )
        for a in anchors:
            if isinstance(a, datetime):
                at: datetime | None = a
            elif isinstance(a, date):
                # Date-only analysis anchors cannot establish intraday order
                # against a timestamp; require a later calendar day.
                if a > ts.date():
                    return a
                continue
            elif isinstance(a, str):
                at = _as_datetime(a)
                if at is None:
                    ad = _as_date(a)
                    if ad is not None and ad > ts.date():
                        return a
                    continue
            else:
                continue
            if at is not None and ts <= at:
                return a
        return None

    raise ValueError(f"unknown public_anchor_precision: {public_anchor_precision!r}")


def independence_audit(rows: list[dict[str, Any]], schema: dict[str, Any]) -> dict[str, Any]:
    """Report N_episodes and N_independent_driver_clusters as primary counts.

    N_underlying_drivers is descriptive metadata only. No ratio threshold.
    """
    accepted = [r for r in rows if r.get("status") == "accepted" and not r.get("example")]
    clusters = Counter(r.get("cluster_id") for r in accepted if r.get("cluster_id"))
    drivers = Counter(
        r.get("underlying_driver_id") for r in accepted if r.get("underlying_driver_id")
    )
    primary = [r for r in accepted if r.get("sample_membership") == "primary"]
    return {
        "n_episodes": len(accepted),
        "n_independent_driver_clusters": len(clusters),
        "n_underlying_drivers": len(drivers),
        "n_clusters": len(clusters),
        "n_drivers": len(drivers),
        "max_episodes_in_one_cluster": max(clusters.values()) if clusters else 0,
        "max_episodes_for_one_driver": max(drivers.values()) if drivers else 0,
        "n_primary_sample": len(primary),
        "n_extended_sample": sum(1 for r in accepted if r.get("sample_membership") == "extended"),
        "below_kill_condition": len(primary) < schema["sample"]["kill_condition_primary_sample_min"],
        "shared_driver_present": any(v > 1 for v in drivers.values()),
        "shared_cluster_present": any(v > 1 for v in clusters.values()),
    }


def render_summary(rows: list[dict[str, Any]], schema: dict[str, Any]) -> str:
    """Render the generated block for EPISODE_LEDGER.md. Never hand-edit the output."""
    real = [r for r in rows if not r.get("example")]
    header = (
        "| episode_id | event_name | event_class | public_anchor | end_date "
        "| navigation_basin | severity_class | sample | status | outcomes_reviewed |\n"
        "|---|---|---|---|---|---|---|---|---|---|\n"
    )
    if not real:
        body = (
            "| *(none)* | | | | | | | | | "
            "*0 admissible rows; market outcomes unopened* |\n"
        )
    else:
        body = ""
        for r in sorted(real, key=lambda x: str(x.get("public_anchor"))):
            basin = ", ".join(r.get("navigation_basin") or [])
            body += (
                f"| {r.get('episode_id', '')} | {r.get('event_name', '')} "
                f"| {r.get('event_class', '')} | {r.get('public_anchor', '')} "
                f"| {r.get('end_date', '') or 'ongoing'} | {basin} "
                f"| {r.get('severity_class') or 'unscored'} "
                f"| {r.get('sample_membership') or ''} | {r.get('status', '')} "
                f"| {str(r.get('market_outcomes_reviewed')).lower()} |\n"
            )
    audit = independence_audit(rows, schema)
    lines = [
        BEGIN_MARK,
        "",
        "<!-- Regenerate with `make episodes-write`. Do not hand-edit this block. -->",
        "",
        header + body,
        "**Independence audit (protocol H.2)**",
        "",
        f"- N_episodes (accepted rows): **{audit['n_episodes']}**",
        f"- N_independent_driver_clusters: **{audit['n_independent_driver_clusters']}** "
        f"(primary inferential effective-N concept)",
        f"- N_underlying_drivers (descriptive only): **{audit['n_underlying_drivers']}**",
        f"- max episodes in one cluster: **{audit['max_episodes_in_one_cluster']}** · "
        f"max episodes for one driver: **{audit['max_episodes_for_one_driver']}**",
        f"- primary sample (Sample P): **{audit['n_primary_sample']}** · "
        f"extended (Sample X): **{audit['n_extended_sample']}**",
        f"- shared driver present: **{str(audit['shared_driver_present']).lower()}** · "
        f"below kill condition: **"
        f"{str(audit['below_kill_condition']).lower()}**",
        "",
        "Primary reporting: N_episodes and N_independent_driver_clusters. "
        "Do not auto-drop physically distinct rows that share a driver.",
        "",
        f"Excluded from counts: {len(rows) - len(real)} fictional example entry/entries.",
        "",
        END_MARK,
    ]
    return "\n".join(lines)


def write_summary(rows: list[dict[str, Any]], schema: dict[str, Any], path: Path) -> bool:
    """Replace the generated block in the ledger. Returns True if the file changed."""
    text = path.read_text(encoding="utf-8")
    block = render_summary(rows, schema)
    if BEGIN_MARK not in text or END_MARK not in text:
        raise ValueError(f"{path} has no generated-block markers")
    head, rest = text.split(BEGIN_MARK, 1)
    _, tail = rest.split(END_MARK, 1)
    new = head + block + tail
    if new != text:
        path.write_text(new, encoding="utf-8", newline="\n")
        return True
    return False


def check_committed_universe_accounting(
    rows: list[dict[str, Any]],
    fx: Findings,
    *,
    repo_root: str | Path | None = None,
) -> None:
    """Enforce ADR-0009 E ∪ N = C when frozen D5 artifacts exist.

    Ordinary synthetic validation against a temp entries dir does not require
    a live candidate universe. Live `research/episodes/entries` closeout does.
    """
    from grainsys.discovery.candidate_universe import (
        CANONICAL_CANDIDATE_UNIVERSE_MANIFEST_RELATIVE,
        CANONICAL_CANDIDATES_RELATIVE,
    )
    from grainsys.discovery.phase2_triage import NO_EPISODE_DISPOSITIONS_RELATIVE

    root = Path(repo_root) if repo_root is not None else Path(".")
    cand = root / CANONICAL_CANDIDATES_RELATIVE
    man = root / CANONICAL_CANDIDATE_UNIVERSE_MANIFEST_RELATIVE
    disp = root / NO_EPISODE_DISPOSITIONS_RELATIVE
    if not cand.is_file() or not man.is_file():
        return
    if not disp.is_file():
        fx.error(
            "<universe-accounting>",
            "L15",
            "frozen D5 present but no_episode_dispositions.csv missing",
        )
        return
    lfx = check_universe_accounting(
        rows,
        candidates_csv=cand,
        candidate_universe_manifest=man,
        no_episode_dispositions=disp,
    )
    fx.errors.extend(lfx.errors)


def check(
    entries_dir: str | Path = ENTRIES_DIR,
    schema_path: str | Path = SCHEMA_PATH,
) -> tuple[list[dict[str, Any]], Findings]:
    schema = load_schema(schema_path)
    rows = load_entries(entries_dir)
    fx = Findings()

    seen: set[str] = set()
    for entry in rows:
        eid = entry.get("episode_id")
        if eid in seen:
            fx.error(entry.get("_file", "?"), "E03", f"duplicate episode_id {eid!r}")
        seen.add(str(eid))
        validate_entry(entry, schema, fx)
        derived = compute_derived(entry, schema)
        assert_severity_kind_honesty(entry, derived, fx)
        entry.update(derived)

    audit = independence_audit(rows, schema)
    if audit["shared_driver_present"]:
        fx.warn(
            "<ledger>",
            "W11",
            "multiple accepted episodes share an underlying_driver_id; "
            "preserve rows; N_underlying_drivers is descriptive metadata",
        )
    if audit["below_kill_condition"]:
        fx.warn("<ledger>", "W12", f"primary sample = {audit['n_primary_sample']} (kill condition)")
    if Path(entries_dir).resolve() == ENTRIES_DIR.resolve():
        check_committed_universe_accounting(rows, fx)
    lo, hi = schema["sample"]["target_accepted_min"], schema["sample"]["target_accepted_max"]
    if audit["n_episodes"] and not lo <= audit["n_episodes"] <= hi:
        fx.warn("<ledger>", "W10", f"accepted count {audit['n_episodes']} outside [{lo}, {hi}]")
    clusters = Counter(
        r.get("cluster_id") for r in rows if r.get("status") == "accepted" and not r.get("example")
    )
    for cid, n in clusters.items():
        if n > 1:
            fx.warn("<ledger>", "W07", f"cluster {cid!r} holds {n} accepted episodes (H6)")
    return rows, fx


def main(argv: list[str] | None = None) -> int:  # pragma: no cover - CLI
    argv = list(sys.argv[1:] if argv is None else argv)
    write = "--write" in argv

    schema = load_schema()
    rows, fx = check()

    for w in fx.warnings:
        print(f"WARN  {w}")
    for e in fx.errors:
        print(f"ERROR {e}")

    changed = False
    if LEDGER_PATH.exists():
        if write:
            changed = write_summary(rows, schema, LEDGER_PATH)
        else:
            current = LEDGER_PATH.read_text(encoding="utf-8")
            expected = render_summary(rows, schema)
            if BEGIN_MARK in current and expected not in current:
                fx.error(
                    str(LEDGER_PATH),
                    "E26",
                    "ledger summary is stale; run `make episodes-write`",
                )
                print(f"ERROR {fx.errors[-1]}")

    real = [r for r in rows if not r.get("example")]
    print(
        f"\nepisodes: {len(real)} real ({len(rows) - len(real)} example) | "
        f"errors: {len(fx.errors)} | warnings: {len(fx.warnings)}"
        + (" | ledger updated" if changed else "")
    )
    if not schema["severity"].get("cutpoints_registered"):
        print("note: severity cutpoints not registered (Phase 0) - severity_class remains null")
    return 1 if fx.errors else 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
