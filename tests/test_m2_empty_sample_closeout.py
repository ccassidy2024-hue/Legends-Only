"""M2–M5 empty-sample closeout invariants.

Locks catalog emptiness and not-estimable M3/M4. Does not mint series YAML,
observations, episode YAML, or reopen D5/prereg. Does not touch panel.py.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from grainsys.catalog import SKIP_STEMS, load_catalog
from grainsys.discovery.evidence_inventory import FROZEN_CANDIDATE_COUNT
from grainsys.episodes import check, load_schema, render_summary

REPO = Path(__file__).resolve().parents[1]
CLOSEOUT_YAML = REPO / "research/milestones/empty_sample_closeout.yaml"
M2_MD = REPO / "research/milestones/M2_NEGATIVE_RESULT_EMPTY_SAMPLE.md"
M34_MD = REPO / "research/milestones/M3_M4_NOT_ESTIMABLE.md"
M5_MD = REPO / "research/memos/M5_EMPTY_SAMPLE_FOUR_STATEMENTS.md"
SETTINGS_PATH = REPO / "config/settings.yaml"
ENTRIES_DIR = REPO / "research/episodes/entries"
CATALOG_DIR = REPO / "catalog/series"
MARKER = "M2_NEGATIVE_RESULT_EMPTY_SAMPLE"
M1_MAIN = "b7d402713ef5eaed33cdff44f4128382e3b38be7"
M1_HEAD = "9812df348c053af3024fd007a4ee486494aac954"


def _closeout() -> dict:
    return yaml.safe_load(CLOSEOUT_YAML.read_text(encoding="utf-8"))


def test_closeout_yaml_records_empty_m2() -> None:
    doc = _closeout()
    assert doc["marker"] == MARKER
    assert doc["m1_merged_main"] == M1_MAIN
    assert doc["m1_reviewed_head"] == M1_HEAD
    m2 = doc["m2"]
    assert m2["result"] == MARKER
    assert m2["catalogued_real_series"] == 0
    assert m2["real_asof_panel_rows"] == 0
    assert m2["fabricated_observations"] is False
    assert m2["panel_py_changed"] is False
    assert m2["episode_anchored_sample"] == "empty"


def test_zero_catalogued_real_series() -> None:
    df = load_catalog(CATALOG_DIR)
    assert df.empty
    yaml_files = list(CATALOG_DIR.glob("*.yaml")) + list(CATALOG_DIR.glob("*.yml"))
    assert yaml_files
    assert all(p.stem in SKIP_STEMS for p in yaml_files)


def test_m3_m4_not_estimable_and_kill() -> None:
    doc = _closeout()
    assert doc["m3"]["result"] == "NOT_ESTIMABLE"
    assert doc["m3"]["reason"] == "zero_ledger_windows"
    assert doc["m3"]["n_episodes"] == 0
    assert doc["m3"]["n_independent_driver_clusters"] == 0
    assert doc["m3"]["universe_screen_authorized"] is False
    assert doc["m3"]["min_obs_default"] == 104
    assert doc["m4"]["result"] == "NOT_ESTIMABLE"
    assert doc["m4"]["reason"] == "zero_identified_shocks"
    assert doc["m4"]["local_projections_require_one_identified_shock"] is True
    assert doc["m4"]["residual_threshold_shock_would_be_tier_a"] is True
    assert doc["m4"]["early_networkx"] is False
    assert doc["kill_condition"]["sample_p"] == 0
    assert doc["kill_condition"]["threshold_usable_episodes"] == 6
    assert doc["kill_condition"]["triggered"] is True
    rows, fx = check(ENTRIES_DIR, REPO / "research/episodes/episode_schema.yaml")
    assert fx.errors == []
    real = [r for r in rows if not r.get("example")]
    assert real == []
    summary = render_summary(rows, load_schema())
    assert "N_episodes (accepted rows): **0**" in summary
    assert "N_independent_driver_clusters: **0**" in summary


def test_m5_four_statements_and_honesty() -> None:
    doc = _closeout()
    assert doc["m5"]["four_statements_required"] is True
    assert doc["m5"]["market_outcomes_opened"] is False
    assert doc["m5"]["gate_f_default"] == "no_mispricing"
    memo = M5_MD.read_text(encoding="utf-8")
    m2 = M2_MD.read_text(encoding="utf-8")
    m34 = M34_MD.read_text(encoding="utf-8")
    for text in (memo, m2, m34):
        assert "UNKNOWN is not zero" in text or "UNKNOWN ≠ 0" in text or "UNKNOWN != 0" in text
    assert "not proof of no physical disruption" in memo
    assert "driver identity only" in memo
    assert "What the data show" in memo
    assert "Why we think it happens" in memo
    assert "What we expect next" in memo
    assert "How it could be traded" in memo
    assert "It cannot" in memo
    assert MARKER in m2
    assert "NOT_ESTIMABLE" in m34
    assert str(FROZEN_CANDIDATE_COUNT) in memo
    settings = yaml.safe_load(SETTINGS_PATH.read_text(encoding="utf-8"))
    assert settings["project"]["phase"] == "m8_written_negative_result"
    assert settings["project"]["next_milestone"] == "none_kill_closed"
    assert settings["data_policy"]["invent_source_metadata"] is False
