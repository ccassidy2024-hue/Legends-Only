"""Episode Ledger validator tests.

These are pre-registration integrity tests. They plant synthetic entries that
violate the protocol and assert the validator catches them. Do not weaken one
to make CI green (CLAUDE.md hard rule 16) — fix the entry or fix the
implementation. No historical events.
"""

from __future__ import annotations

import copy
from datetime import date, datetime
from pathlib import Path

import pytest
import yaml

from grainsys.episodes import (
    Findings,
    assert_severity_kind_honesty,
    check,
    compute_derived,
    first_usable_analysis_anchor,
    independence_audit,
    load_entries,
    load_schema,
    render_summary,
    validate_entry,
)

REPO = Path(__file__).resolve().parents[1]
SCHEMA_PATH = REPO / "research/episodes/episode_schema.yaml"
ENTRIES_DIR = REPO / "research/episodes/entries"
LEDGER_PATH = REPO / "research/episodes/EPISODE_LEDGER.md"


@pytest.fixture(scope="module")
def schema() -> dict:
    return load_schema(SCHEMA_PATH)


@pytest.fixture()
def entry() -> dict:
    """The fictional worked example, used as a known-good baseline."""
    path = ENTRIES_DIR / "EP-0000-000-example.yaml"
    with path.open(encoding="utf-8") as fh:
        d = yaml.safe_load(fh)
    d["_file"] = path.name
    return d


def codes(fx: Findings) -> set[str]:
    return {msg.split("[")[1].split("]")[0] for msg in fx.errors + fx.warnings}


def run(entry: dict, schema: dict) -> Findings:
    fx = Findings()
    validate_entry(entry, schema, fx)
    return fx


# --------------------------------------------------------------------------- #
# Baseline
# --------------------------------------------------------------------------- #
def test_repo_entries_validate_clean() -> None:
    """Everything under entries/ must pass with zero errors."""
    rows, fx = check(ENTRIES_DIR, SCHEMA_PATH)
    assert fx.errors == [], fx.errors
    assert rows, "no episode entries found"


def test_valid_example_entry_passes(entry: dict, schema: dict) -> None:
    fx = run(entry, schema)
    assert fx.errors == [], fx.errors
    assert entry["example"] is True
    assert entry["episode_id"] in schema["sample"]["example_ids_excluded"]


# --------------------------------------------------------------------------- #
# Pre-registration lock / severity / sources / governance
# --------------------------------------------------------------------------- #
def test_market_outcomes_reviewed_true_is_an_error(entry: dict, schema: dict) -> None:
    bad = copy.deepcopy(entry)
    bad["market_outcomes_reviewed"] = True
    assert "E07" in codes(run(bad, schema))


def test_hand_assigned_severity_is_rejected(entry: dict, schema: dict) -> None:
    for fld, value in [
        ("severity_class", "S3"),
        ("severity_score", 12),
        ("severity_subscores", {"d1_magnitude": 3}),
        ("severity_class_kind", "ex_post_descriptive"),
        ("sample_membership", "primary"),
    ]:
        bad = copy.deepcopy(entry)
        bad[fld] = value
        assert "E06" in codes(run(bad, schema)), fld


def test_market_derived_severity_metric_is_rejected(entry: dict, schema: dict) -> None:
    for name in ["gulf_basis_cents", "barge_freight_rate_pct_tariff", "dec_mar_spread"]:
        bad = copy.deepcopy(entry)
        bad["severity_metrics"] = copy.deepcopy(entry["severity_metrics"])
        bad["severity_metrics"][0]["name"] = name
        assert "E22" in codes(run(bad, schema)), name


def test_accepted_requires_two_tier1_sources(entry: dict, schema: dict) -> None:
    bad = copy.deepcopy(entry)
    bad["primary_sources"] = bad["primary_sources"][:1]
    assert "E10" in codes(run(bad, schema))


def test_source_without_quote_or_url_is_rejected(entry: dict, schema: dict) -> None:
    bad = copy.deepcopy(entry)
    bad["primary_sources"][0]["quote"] = None
    bad["primary_sources"][1]["url"] = None
    assert "E11" in codes(run(bad, schema))


def test_tier3_source_is_never_citable(entry: dict, schema: dict) -> None:
    bad = copy.deepcopy(entry)
    bad["primary_sources"][0]["tier"] = 3
    assert "E24" in codes(run(bad, schema))


def test_reviewer_must_differ_from_recorder(entry: dict, schema: dict) -> None:
    bad = copy.deepcopy(entry)
    bad["reviewed_by"] = bad["recorded_by"]
    assert "E16" in codes(run(bad, schema))


def test_anchor_source_ref_must_resolve(entry: dict, schema: dict) -> None:
    bad = copy.deepcopy(entry)
    bad["anchor_source_ref"] = "src_does_not_exist"
    assert "E20" in codes(run(bad, schema))


def test_reject_requires_a_reason_code(entry: dict, schema: dict) -> None:
    bad = copy.deepcopy(entry)
    bad["decision"] = "reject"
    bad["decision_reasons"] = []
    assert "E17" in codes(run(bad, schema))


# --------------------------------------------------------------------------- #
# Anchor discipline + precision honesty
# --------------------------------------------------------------------------- #
def test_anchor_precision_days_vocabulary(entry: dict, schema: dict) -> None:
    bad = copy.deepcopy(entry)
    bad["anchor_precision_days"] = 14
    assert "E08" in codes(run(bad, schema))


def test_public_anchor_precision_is_required(entry: dict, schema: dict) -> None:
    bad = copy.deepcopy(entry)
    del bad["public_anchor_precision"]
    assert "E04" in codes(run(bad, schema))


def test_date_precision_forbids_invented_timestamp(entry: dict, schema: dict) -> None:
    bad = copy.deepcopy(entry)
    bad["public_anchor_precision"] = "date"
    bad["anchor_ts"] = "2099-03-14T00:00:00"
    assert "E27" in codes(run(bad, schema))


def test_timestamp_precision_requires_real_anchor_ts(entry: dict, schema: dict) -> None:
    bad = copy.deepcopy(entry)
    bad["public_anchor_precision"] = "timestamp"
    bad["anchor_ts"] = None
    assert "E27" in codes(run(bad, schema))


def test_timestamp_precision_rejects_date_only_string(entry: dict, schema: dict) -> None:
    bad = copy.deepcopy(entry)
    bad["public_anchor_precision"] = "timestamp"
    bad["anchor_ts"] = "2099-03-14"  # date masquerading as timestamp
    assert "E27" in codes(run(bad, schema))


def test_timestamp_precision_accepts_real_datetime(entry: dict, schema: dict) -> None:
    good = copy.deepcopy(entry)
    good["public_anchor_precision"] = "timestamp"
    good["anchor_ts"] = "2099-03-14T15:30:00-05:00"
    assert "E27" not in codes(run(good, schema))


def test_physical_onset_after_public_anchor_is_an_error(entry: dict, schema: dict) -> None:
    bad = copy.deepcopy(entry)
    bad["physical_onset"] = "2099-03-20"
    assert "E09" in codes(run(bad, schema))


def test_peak_severity_outside_window_is_an_error(entry: dict, schema: dict) -> None:
    bad = copy.deepcopy(entry)
    bad["peak_severity_date"] = "2099-06-01"
    assert "E09" in codes(run(bad, schema))


def test_malformed_public_anchor_fails(entry: dict, schema: dict) -> None:
    bad = copy.deepcopy(entry)
    bad["public_anchor"] = "not-a-date"
    assert "E09" in codes(run(bad, schema))


def test_anchor_disagreement_warns(entry: dict, schema: dict) -> None:
    warn = copy.deepcopy(entry)
    warn["anchor_agreement"] = "disagree"
    assert "W09" in codes(run(warn, schema))


# --------------------------------------------------------------------------- #
# Contamination, substitution, sweeps
# --------------------------------------------------------------------------- #
def test_contamination_class_c_requires_rationale_and_warns(entry: dict, schema: dict) -> None:
    bad = copy.deepcopy(entry)
    bad["crop_contamination_class"] = "C"
    bad["contamination_rationale"] = None
    found = codes(run(bad, schema))
    assert "E18" in found and "W03" in found


def test_empty_concurrent_shocks_requires_a_sweep(entry: dict, schema: dict) -> None:
    bad = copy.deepcopy(entry)
    bad["concurrent_shocks"] = []
    bad["sweep_performed"] = False
    assert "E19" in codes(run(bad, schema))


def test_accepted_requires_three_substitution_channels(entry: dict, schema: dict) -> None:
    bad = copy.deepcopy(entry)
    bad["substitution_channels"] = bad["substitution_channels"][:2]
    assert "E13" in codes(run(bad, schema))


def test_llm_origin_without_sweep_warns(entry: dict, schema: dict) -> None:
    bad = copy.deepcopy(entry)
    bad["discovery_trail"] = [{"origin": "llm", "detail": "model suggested this event"}]
    assert "W06" in codes(run(bad, schema))


def test_memory_origin_without_sweep_warns(entry: dict, schema: dict) -> None:
    bad = copy.deepcopy(entry)
    bad["discovery_trail"] = [{"origin": "memory", "detail": "I remember this one"}]
    assert "W06" in codes(run(bad, schema))


# --------------------------------------------------------------------------- #
# Derived severity honesty
# --------------------------------------------------------------------------- #
def test_severity_unscored_while_cutpoints_unregistered(entry: dict, schema: dict) -> None:
    assert schema["severity"]["cutpoints_registered"] is False
    d = compute_derived(entry, schema)
    assert d["severity_class"] is None
    assert d["severity_score"] is None
    assert d["severity_class_kind"] is None
    assert d["severity_subscores"]["d5_restrictiveness"] == 3
    assert 0.0 < d["severity_completeness"] <= 1.0


def test_severity_scores_once_cutpoints_registered(entry: dict, schema: dict) -> None:
    reg = copy.deepcopy(schema)
    reg["severity"]["cutpoints_registered"] = True
    reg["severity"]["cutpoints"] = {
        "lock_outage": {
            "d1_magnitude": [1, 2, 3],
            "d2_duration": [3, 10, 30],
            "d3_scope": [1, 3, 6],
            "d4_throughput": [5, 20, 50],
        }
    }
    e = copy.deepcopy(entry)
    e["severity_metrics"].append(
        {
            "dimension": "d1_magnitude",
            "name": "chamber_capacity_offline_share",
            "value": 1,
            "units": "share",
            "as_of_date": "2099-03-14",
            "source_ref": "src_ntni_0000_99",
            "quote_ref": "q_closure_notice",
        }
    )
    d = compute_derived(e, reg)
    assert d["severity_score"] is not None
    assert d["severity_class"] in reg["severity"]["bands"]
    assert d["severity_class_kind"] == "ex_post_descriptive"
    assert d["severity_completeness"] == 1.0


def test_ex_post_kind_cannot_masquerade_as_contemporaneous(
    entry: dict, schema: dict
) -> None:
    """Post-anchor metric dates must not be labelled contemporaneous."""
    e = copy.deepcopy(entry)
    derived = {
        "severity_class": "S2",
        "severity_class_kind": "contemporaneous",
    }
    # Example already has metrics with as_of after public_anchor (duration/end).
    fx = Findings()
    assert_severity_kind_honesty(e, derived, fx)
    assert "E28" in codes(fx)


def test_duration_and_hash_are_derived(entry: dict, schema: dict) -> None:
    d = compute_derived(entry, schema)
    assert d["duration_days"] == 19
    assert len(d["content_hash"]) == 16
    other = copy.deepcopy(entry)
    other["event_name"] = "changed"
    assert compute_derived(other, schema)["content_hash"] != d["content_hash"]


def test_sample_membership_follows_contamination(entry: dict, schema: dict) -> None:
    cases = {
        ("A", "A"): "primary",
        ("B", "A"): "primary",
        ("C", "A"): "extended",
        ("A", "C"): "extended",
        ("D", "A"): "excluded",
        ("A", "D"): "excluded",
    }
    for (crop, macro), expected in cases.items():
        e = copy.deepcopy(entry)
        e["crop_contamination_class"] = crop
        e["macro_contamination_class"] = macro
        assert compute_derived(e, schema)["sample_membership"] == expected, (crop, macro)


# --------------------------------------------------------------------------- #
# Independence — separate counts, no 1.5 rule
# --------------------------------------------------------------------------- #
def _accepted(eid: str, cluster: str, driver: str) -> dict:
    return {
        "episode_id": eid,
        "status": "accepted",
        "cluster_id": cluster,
        "underlying_driver_id": driver,
        "sample_membership": "primary",
        "public_anchor": "2099-01-01",
        "navigation_basin": ["ohio"],
        "market_outcomes_reviewed": False,
    }


def test_independence_reports_both_counts_without_ratio_threshold(schema: dict) -> None:
    rows = [_accepted(f"EP-2099-00{i}", "one_cluster", "one_driver") for i in range(1, 6)]
    audit = independence_audit(rows, schema)
    assert audit["n_episodes"] == 5
    assert audit["n_independent_driver_clusters"] == 1
    assert audit["n_underlying_drivers"] == 1
    assert "inflated" not in audit
    assert "independence_audit_max_episodes_per_driver" not in schema["sample"]
    assert audit["shared_driver_present"] is True


def test_independence_audit_preserves_distinct_rows(schema: dict) -> None:
    rows = [
        _accepted("EP-2099-001", "c1", "drought_ohio_2099"),
        _accepted("EP-2099-002", "c2", "drought_ohio_2099"),
    ]
    audit = independence_audit(rows, schema)
    assert audit["n_episodes"] == 2
    assert audit["n_underlying_drivers"] == 1
    assert audit["n_independent_driver_clusters"] == 2


def test_independence_audit_clean_sample(schema: dict) -> None:
    rows = [
        _accepted(f"EP-2099-00{i}", f"cluster_{i}", f"driver_{i}") for i in range(1, 8)
    ]
    audit = independence_audit(rows, schema)
    assert audit["shared_driver_present"] is False
    assert audit["below_kill_condition"] is False


def test_kill_condition_flags_small_primary_sample(schema: dict) -> None:
    rows = [_accepted(f"EP-2099-00{i}", f"c{i}", f"d{i}") for i in range(1, 4)]
    assert independence_audit(rows, schema)["below_kill_condition"] is True


def test_example_entries_excluded_from_audit(schema: dict) -> None:
    rows = [
        _accepted("EP-0000-000", "fictional", "fictional") | {"example": True}
    ]
    assert independence_audit(rows, schema)["n_episodes"] == 0


def test_shared_cluster_warns_at_ledger_level(tmp_path: Path) -> None:
    src = ENTRIES_DIR / "EP-0000-000-example.yaml"
    base = yaml.safe_load(src.read_text(encoding="utf-8"))
    for eid in ["EP-2099-001", "EP-2099-002"]:
        e = copy.deepcopy(base)
        e["episode_id"] = eid
        e.pop("example", None)
        (tmp_path / f"{eid}-dup.yaml").write_text(yaml.safe_dump(e), encoding="utf-8")
    _, fx = check(tmp_path, SCHEMA_PATH)
    assert "W07" in codes(fx)


def test_shared_driver_warns_without_dropping_rows(tmp_path: Path) -> None:
    src = ENTRIES_DIR / "EP-0000-000-example.yaml"
    base = yaml.safe_load(src.read_text(encoding="utf-8"))
    for i, eid in enumerate(["EP-2099-001", "EP-2099-002"], start=1):
        e = copy.deepcopy(base)
        e["episode_id"] = eid
        e.pop("example", None)
        e["cluster_id"] = f"cluster_{i}"
        e["underlying_driver_id"] = "shared_driver"
        (tmp_path / f"{eid}.yaml").write_text(yaml.safe_dump(e), encoding="utf-8")
    rows, fx = check(tmp_path, SCHEMA_PATH)
    assert "W11" in codes(fx)
    assert independence_audit(rows, load_schema(SCHEMA_PATH))["n_episodes"] == 2


def test_duplicate_episode_id_is_an_error(tmp_path: Path) -> None:
    src = ENTRIES_DIR / "EP-0000-000-example.yaml"
    base = yaml.safe_load(src.read_text(encoding="utf-8"))
    for suffix in ("a", "b"):
        (tmp_path / f"EP-0000-000-{suffix}.yaml").write_text(
            yaml.safe_dump(base), encoding="utf-8"
        )
    _, fx = check(tmp_path, SCHEMA_PATH)
    assert "E03" in codes(fx)


# --------------------------------------------------------------------------- #
# Ledger rendering
# --------------------------------------------------------------------------- #
def test_ledger_has_generated_block() -> None:
    text = LEDGER_PATH.read_text(encoding="utf-8")
    assert "<!-- BEGIN GENERATED: episode-summary -->" in text
    assert "<!-- END GENERATED: episode-summary -->" in text


def test_ledger_summary_is_current() -> None:
    rows, _ = check(ENTRIES_DIR, SCHEMA_PATH)
    expected = render_summary(rows, load_schema(SCHEMA_PATH))
    assert expected in LEDGER_PATH.read_text(encoding="utf-8")


def test_summary_excludes_example_entries(schema: dict) -> None:
    rows = load_entries(ENTRIES_DIR)
    for r in rows:
        r.update(compute_derived(r, schema))
    out = render_summary(rows, schema)
    assert "EP-0000-000" not in out
    assert "fictional example entry" in out


def test_summary_reports_both_episode_and_cluster_counts(schema: dict) -> None:
    rows = [_accepted(f"EP-2099-00{i}", "one_cluster", "one_driver") for i in range(1, 4)]
    out = render_summary(rows, schema)
    assert "N_episodes (accepted rows): **3**" in out
    assert "N_independent_driver_clusters: **1**" in out
    assert "descriptive only" in out
    assert "threshold 1.5" not in out
    assert "sample inflated" not in out


# --------------------------------------------------------------------------- #
# Date-only / timestamp → analysis-anchor mapping (R-001)
# --------------------------------------------------------------------------- #
def test_date_only_anchor_skips_same_calendar_day_analysis_anchor() -> None:
    # Friday date-only public_anchor; Friday 23:59 analysis anchor must NOT be used.
    public = date(2023, 10, 13)  # Friday
    anchors = [
        datetime(2023, 10, 6, 23, 59),
        datetime(2023, 10, 13, 23, 59),  # same calendar day — ineligible
        datetime(2023, 10, 20, 23, 59),  # strictly after — primary mapping
    ]
    got = first_usable_analysis_anchor(public, "date", anchors)
    assert got == datetime(2023, 10, 20, 23, 59)


def test_date_only_anchor_does_not_invent_intraday_availability() -> None:
    public = "2023-10-13"
    # Even an "end of day" same-day anchor is not usable under the primary rule.
    anchors = [datetime(2023, 10, 13, 23, 59, 59)]
    assert first_usable_analysis_anchor(public, "date", anchors) is None


def test_timestamp_anchor_allows_same_day_when_ts_leq_analysis() -> None:
    public = date(2023, 10, 13)
    ts = datetime(2023, 10, 13, 15, 0, 0)
    anchors = [
        datetime(2023, 10, 13, 12, 0, 0),  # before release — not usable
        datetime(2023, 10, 13, 23, 59, 0),  # after release — usable
    ]
    got = first_usable_analysis_anchor(public, "timestamp", anchors, anchor_ts=ts)
    assert got == datetime(2023, 10, 13, 23, 59, 0)


def test_timestamp_precision_rejects_invented_clock_from_date_only() -> None:
    with pytest.raises(ValueError, match="real anchor_ts"):
        first_usable_analysis_anchor(
            date(2023, 10, 13),
            "timestamp",
            [datetime(2023, 10, 20, 23, 59)],
            anchor_ts=None,
        )


def test_driver_class_required(entry: dict, schema: dict) -> None:
    bad = copy.deepcopy(entry)
    del bad["driver_class"]
    assert "E04" in codes(run(bad, schema))


def test_cluster_defaults_equal_underlying_driver_no_warning(entry: dict, schema: dict) -> None:
    good = copy.deepcopy(entry)
    good["underlying_driver_id"] = "same_id"
    good["cluster_id"] = "same_id"
    assert "W15" not in codes(run(good, schema))


def test_cluster_differs_from_driver_warns(entry: dict, schema: dict) -> None:
    warn = copy.deepcopy(entry)
    warn["underlying_driver_id"] = "driver_a"
    warn["cluster_id"] = "cluster_b"
    assert "W15" in codes(run(warn, schema))


def test_cutpoints_remain_unregistered(schema: dict) -> None:
    assert schema["severity"]["cutpoints_registered"] is False
    assert schema["severity"]["cutpoints"] == {} or not schema["severity"]["cutpoints"]


def test_lineage_fields_required_on_example(entry: dict, schema: dict) -> None:
    assert entry["candidate_ids"] == ["CAND-0001", "CAND-0002"]
    assert entry["candidate_universe_version"].startswith("d5cu-")
    assert entry["schema_version"] == "1.2"
    assert "1.2" in schema["supported_versions"]


def test_stored_lineage_candidate_id_rejected(entry: dict, schema: dict) -> None:
    bad = copy.deepcopy(entry)
    bad["lineage_candidate_id"] = "CAND-0001"
    assert "E06" in codes(run(bad, schema))


def test_unsorted_candidate_ids_rejected(entry: dict, schema: dict) -> None:
    bad = copy.deepcopy(entry)
    bad["candidate_ids"] = ["CAND-0002", "CAND-0001"]
    assert "E30" in codes(run(bad, schema))
