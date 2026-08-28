"""M1 empty-ledger negative-result closeout invariants.

Locks already-merged Phase-2 triage facts. Does not mint episode YAML,
reopen D5/prereg/H7, or treat UNKNOWN / missing I2 as zero.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from grainsys.discovery.candidate_universe import (
    CANONICAL_CANDIDATE_UNIVERSE_MANIFEST_RELATIVE,
    CANONICAL_CANDIDATES_RELATIVE,
)
from grainsys.discovery.evidence_inventory import (
    FROZEN_CANDIDATE_COUNT,
    FROZEN_S1_COUNT,
    FROZEN_S4_COUNT,
)
from grainsys.discovery.phase2_triage import (
    NO_EPISODE_DISPOSITIONS_RELATIVE,
    S1_REASON,
    S4_REASON,
    triage_frozen_universe,
)
from grainsys.episodes import check, load_schema, render_summary
from grainsys.lineage import check_universe_accounting

REPO = Path(__file__).resolve().parents[1]
LEDGER_PATH = REPO / "research/episodes/EPISODE_LEDGER.md"
SETTINGS_PATH = REPO / "config/settings.yaml"
ENTRIES_DIR = REPO / "research/episodes/entries"
CLOSEOUT_MARKER = "M1_CLOSEOUT_RETRY_AFTER_CURSOR_LAUNCH_FAILURE"
SCIENCE_HEAD = "e213aab007150d5287b07e476d0bb438ad1374a9"
PR50_REVIEWED_HEAD = "5a76e2e3c8e83aed0956f8b8804c043ae8729206"


def test_frozen_d5_counts_unchanged() -> None:
    assert FROZEN_CANDIDATE_COUNT == 4234
    assert FROZEN_S1_COUNT == 37
    assert FROZEN_S4_COUNT == 4197
    assert FROZEN_S1_COUNT + FROZEN_S4_COUNT == FROZEN_CANDIDATE_COUNT


def test_zero_real_episode_yaml() -> None:
    real = [
        p
        for p in ENTRIES_DIR.glob("EP-*.yaml")
        if not p.name.startswith("EP-0000-000")
    ]
    assert real == []
    example = ENTRIES_DIR / "EP-0000-000-example.yaml"
    assert example.is_file()


def test_triage_is_full_universe_no_survivors() -> None:
    result = triage_frozen_universe(repo_root=REPO)
    assert len(result.rows) == FROZEN_CANDIDATE_COUNT
    assert result.survivor_count == 0
    assert result.s1_by_reason == {S1_REASON: FROZEN_S1_COUNT}
    assert result.s4_by_reason == {S4_REASON: FROZEN_S4_COUNT}


def test_empty_ledger_generated_summary_is_zero_rows() -> None:
    rows, fx = check(ENTRIES_DIR, REPO / "research/episodes/episode_schema.yaml")
    assert fx.errors == []
    real = [r for r in rows if not r.get("example")]
    assert real == []
    summary = render_summary(rows, load_schema())
    assert "N_episodes (accepted rows): **0**" in summary
    assert "N_independent_driver_clusters: **0**" in summary
    assert "primary sample (Sample P): **0**" in summary
    assert "*(none yet)*" in summary
    assert "blank during pre-registration" in summary
    assert "EP-0000-000" not in summary
    ledger = LEDGER_PATH.read_text(encoding="utf-8")
    assert summary in ledger


def test_universe_accounting_e_union_n_equals_c() -> None:
    fx = check_universe_accounting(
        [],
        candidates_csv=REPO / CANONICAL_CANDIDATES_RELATIVE,
        candidate_universe_manifest=REPO / CANONICAL_CANDIDATE_UNIVERSE_MANIFEST_RELATIVE,
        no_episode_dispositions=REPO / NO_EPISODE_DISPOSITIONS_RELATIVE,
    )
    assert fx.ok, fx.errors


def test_closeout_status_artifacts() -> None:
    ledger = LEDGER_PATH.read_text(encoding="utf-8")
    assert CLOSEOUT_MARKER in ledger
    assert "| Admissible episode rows | **0** |" in ledger
    assert "UNKNOWN is not zero" in ledger
    assert "not proof of no physical disruption" in ledger
    assert "driver identity only" in ledger
    assert SCIENCE_HEAD in ledger
    assert PR50_REVIEWED_HEAD in ledger
    assert "market data remains unopened" in ledger
    settings = yaml.safe_load(SETTINGS_PATH.read_text(encoding="utf-8"))
    assert settings["project"]["phase"] == "milestone_1_negative_result_empty_ledger"
    assert settings["project"]["next_milestone"] == "2_asof_panel"
