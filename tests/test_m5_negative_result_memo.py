"""M5 Gate C FAIL memo invariants.

Does not mint episodes, series, observations, or reopen outcomes.
Does not forge A/B human signatures. Does not invent beta/lag/t/p.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from grainsys.discovery.evidence_inventory import FROZEN_CANDIDATE_COUNT

REPO = Path(__file__).resolve().parents[1]
CLOSEOUT_YAML = REPO / "research/milestones/empty_sample_closeout.yaml"
MEMO = REPO / "research/memos/M5_NEGATIVE_RESULT_MECHANISM.md"
STUB = REPO / "research/memos/M5_EMPTY_SAMPLE_FOUR_STATEMENTS.md"
SETTINGS_PATH = REPO / "config/settings.yaml"
MARKER = "GENUINE_M5_NEGATIVE_RESULT_MEMO_COMPLETION"
SECTIONS = [
    "## 1. Claim",
    "## 2. What the data show",
    "## 3. Why we think it happens",
    "## 4. Prior literature",
    "## 5. Confounders considered and how ruled out",
    "## 6. Why this is not an accounting identity",
    "## 7. Falsification",
    "## 8. Red-team output",
    "## 9. Gate decision",
]


def _closeout() -> dict:
    return yaml.safe_load(CLOSEOUT_YAML.read_text(encoding="utf-8"))


def test_m5_yaml_gate_c_fail_signatures_pending() -> None:
    doc = _closeout()
    m5 = doc["m5"]
    assert m5["artifact"] == "research/memos/M5_NEGATIVE_RESULT_MECHANISM.md"
    assert m5["gate_c"] == "FAIL_NEGATIVE_RESULT"
    assert m5["gate_c_complete"] is False
    assert m5["human_signatures"] == "pending"
    assert m5["school_database_search_performed"] is False
    assert m5["market_outcomes_opened"] is False
    assert m5["gate_f_default"] == "no_mispricing"
    settings = yaml.safe_load(SETTINGS_PATH.read_text(encoding="utf-8"))
    assert settings["project"]["phase"] == "m8_written_negative_result"
    assert settings["project"]["next_milestone"] == "none_kill_closed"
    assert settings["project"]["m5_gate_c"] == "FAIL_NEGATIVE_RESULT"
    assert settings["project"]["m5_human_signatures"] == "pending"


def test_m5_memo_template_sections_and_honesty() -> None:
    text = MEMO.read_text(encoding="utf-8")
    for heading in SECTIONS:
        assert heading in text
    assert MARKER in text
    assert str(FROZEN_CANDIDATE_COUNT) in text
    assert "Effective N = number of episodes = **0**" in text
    assert "not estimable" in text.lower()
    assert "UNKNOWN is not zero" in text
    assert "not proof of no physical disruption" in text
    assert "driver identity only" in text
    assert "Gate C: **fail / negative-result retained**" in text
    assert "Signed by: A (agent" not in text
    assert "| Person A | `SIGN_FAIL_NEGATIVE_RESULT` | pending |" in text
    assert "| Person B | `SIGN_FAIL_NEGATIVE_RESULT` | pending |" in text
    assert "School academic-database search" in text
    assert "**not performed**" in text
    assert "no mispricing" in text.lower()
    assert "not** in the Episode Ledger" in text
    stub = STUB.read_text(encoding="utf-8")
    assert "M5_NEGATIVE_RESULT_MECHANISM.md" in stub


def test_m5_memo_does_not_invent_estimates() -> None:
    text = MEMO.read_text(encoding="utf-8")
    for banned in ("beta =", "lag = +", "p_maxt =", "HAC t ="):
        assert banned not in text
    assert "Jordà" in text
    assert "10.1257/0002828053828518" in text
    assert "The Theory of Price of Storage" in text
    assert "1816601" in text
    assert "export-sales-reporting-program" in text
    assert "fgisonline" in text
    assert "Off-Farm_Grain_Stocks" in text
    assert "transportation-analysis/gtr" in text
    assert "hurdat2-format-atlantic.pdf" in text
    assert "PENDING_DRAFT_FREEZE" not in text
    assert "74c4120f195b701ed5f09a2c050c5d39abed1026" in text
    assert "FAIL_MEMO_OVERCLAIMS" in text
    assert "GPT-5.6" in text
    assert "bc-459fb6f8-3172-50ba-971d-0bfb19da93ac" in text
    doc = _closeout()
    assert doc["m5"]["red_team_status"] == "inserted_gpt56_fail_memo_overclaims"
    assert doc["m5"]["red_team_verdict"] == "FAIL_MEMO_OVERCLAIMS"
