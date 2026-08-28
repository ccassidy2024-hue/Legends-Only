"""M8 kill closeout: unanswerable sample, skipped M6/M7, 0-test family.

Does not mint episode YAML, series, observations, or reopen D5/prereg.
Does not touch panel.py. Empty lagscan output is not a discovery.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import yaml

from grainsys.discovery.evidence_inventory import FROZEN_CANDIDATE_COUNT
from grainsys.screening.lagscan import ScanConfig, maxt_pvalue, scan_universe

REPO = Path(__file__).resolve().parents[1]
CLOSEOUT_YAML = REPO / "research/milestones/empty_sample_closeout.yaml"
MULTIPLICITY_YAML = REPO / "research/milestones/m3_empty_family_multiplicity.yaml"
M67_MD = REPO / "research/milestones/M6_M7_SKIPPED_UNDER_KILL.md"
M8_MD = REPO / "research/milestones/M8_WRITTEN_NEGATIVE_RESULT.md"
LEDGER_PATH = REPO / "research/episodes/EPISODE_LEDGER.md"
SETTINGS_PATH = REPO / "config/settings.yaml"
ENTRIES_DIR = REPO / "research/episodes/entries"
M8_MARKER = "M8_WRITTEN_NEGATIVE_RESULT_UNANSWERABLE"
TAKEOVER_MARKER = "M1_CLOSEOUT_GROK_TAKEOVER"


def _closeout() -> dict:
    return yaml.safe_load(CLOSEOUT_YAML.read_text(encoding="utf-8"))


def _multiplicity() -> dict:
    return yaml.safe_load(MULTIPLICITY_YAML.read_text(encoding="utf-8"))


def test_kill_triggered_and_m6_m7_skipped() -> None:
    doc = _closeout()
    assert doc["kill_condition"]["sample_p"] == 0
    assert doc["kill_condition"]["threshold_usable_episodes"] == 6
    assert doc["kill_condition"]["triggered"] is True
    assert doc["kill_condition"]["stop"] is True
    assert doc["kill_condition"]["next_milestone"] == "none_kill_closed"
    assert doc["m6"]["result"] == "SKIPPED_UNDER_KILL"
    assert doc["m6"]["instrument_invented"] is False
    assert doc["m7"]["result"] == "SKIPPED_UNDER_KILL"
    assert doc["m7"]["replay_invented"] is False
    assert doc["m8"]["result"] == M8_MARKER
    assert doc["m8"]["estimated_null"] is False
    assert doc["m8"]["question_answerable"] is False
    assert doc["m8"]["market_outcomes_opened"] is False
    assert doc["m8"]["gate_f"] == "no_mispricing"
    assert doc["m8_marker"] == M8_MARKER


def test_m3_family_is_never_run_not_ran_and_null() -> None:
    doc = _closeout()
    m3m = doc["m3"]["multiplicity"]
    assert m3m["planned_family_size"] == 0
    assert m3m["tests_performed"] == 0
    assert m3m["status"] == "never_run"
    assert m3m["ran_and_null"] is False
    rec = _multiplicity()
    assert rec["planned_family_size"] == 0
    assert rec["tests_performed"] == 0
    assert rec["status"] == "never_run"
    assert rec["ran_and_null"] is False
    assert rec["universe_screen_authorized"] is False
    assert rec["min_obs_default"] == ScanConfig.min_obs == 104
    empty_pairs = scan_universe(pd.DataFrame(), pairs=[])
    assert isinstance(empty_pairs, pd.DataFrame)
    assert empty_pairs.empty
    maxt = maxt_pvalue(pd.DataFrame({"x": [], "y": []}), "x", "y")
    assert maxt["status"] == "insufficient_data"
    assert "p_maxt" not in maxt


def test_m8_honesty_and_not_estimated_null() -> None:
    m8 = M8_MD.read_text(encoding="utf-8")
    m67 = M67_MD.read_text(encoding="utf-8")
    ledger = LEDGER_PATH.read_text(encoding="utf-8")
    for text in (m8, m67, ledger):
        assert "UNKNOWN is not zero" in text or "UNKNOWN ≠ 0" in text
    assert "not proof of no physical disruption" in m8
    assert "driver identity only" in m8
    assert "unanswerable" in m8.lower()
    assert "That test was never run" in m8
    assert "nothing survived max-t" in m8
    assert M8_MARKER in m8
    assert TAKEOVER_MARKER in ledger
    assert "SKIPPED_UNDER_KILL" in m67
    assert str(FROZEN_CANDIDATE_COUNT) in m8 or "4234" in m8
    real = [
        p
        for p in ENTRIES_DIR.glob("EP-*.yaml")
        if not p.name.startswith("EP-0000-000")
    ]
    assert real == []
    settings = yaml.safe_load(SETTINGS_PATH.read_text(encoding="utf-8"))
    assert settings["project"]["phase"] == "m8_written_negative_result"
    assert settings["project"]["next_milestone"] == "none_kill_closed"
    assert settings["data_policy"]["invent_source_metadata"] is False
