"""M1 empty admissible Episode Ledger closeout (negative result).

Pins the repo-native empty-ledger state. Does not author episode YAML,
reopen discovery, or treat UNKNOWN as zero.
"""

from __future__ import annotations

from pathlib import Path

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
    S1_NOTE,
    S1_REASON,
    S4_NOTE,
    S4_REASON,
    triage_frozen_universe,
)
from grainsys.episodes import (
    check,
    check_committed_universe_accounting,
    independence_audit,
    load_schema,
    render_summary,
)
from grainsys.lineage import check_universe_accounting

REPO = Path(__file__).resolve().parents[1]
ENTRIES_DIR = REPO / "research/episodes/entries"
LEDGER_PATH = REPO / "research/episodes/EPISODE_LEDGER.md"
EXAMPLE_PATH = ENTRIES_DIR / "EP-0000-000-example.yaml"
SCHEMA_PATH = REPO / "research/episodes/episode_schema.yaml"


def test_only_fictional_example_episode_yaml_exists() -> None:
    real = [
        p
        for p in ENTRIES_DIR.glob("EP-*.yaml")
        if not p.name.startswith("EP-0000-000")
    ]
    assert real == []
    assert EXAMPLE_PATH.is_file()


def test_live_ledger_is_empty_admissible_sample() -> None:
    rows, fx = check(ENTRIES_DIR, SCHEMA_PATH)
    assert fx.errors == [], fx.errors
    assert "W12" in {msg.split("[")[1].split("]")[0] for msg in fx.warnings}
    schema = load_schema(SCHEMA_PATH)
    audit = independence_audit(rows, schema)
    assert audit["n_episodes"] == 0
    assert audit["n_independent_driver_clusters"] == 0
    assert audit["n_primary_sample"] == 0
    assert audit["below_kill_condition"] is True
    summary = render_summary(rows, schema)
    assert "*(none)*" in summary
    assert "0 admissible rows; market outcomes unopened" in summary
    assert "N_episodes (accepted rows): **0**" in summary
    assert "below kill condition: **true**" in summary
    assert "n/a" not in summary
    assert summary in LEDGER_PATH.read_text(encoding="utf-8")


def test_universe_accounting_is_complete_empty_episode_side() -> None:
    rows, fx = check(ENTRIES_DIR, SCHEMA_PATH)
    check_committed_universe_accounting(rows, fx, repo_root=REPO)
    assert fx.errors == [], fx.errors
    lfx = check_universe_accounting(
        rows,
        candidates_csv=REPO / CANONICAL_CANDIDATES_RELATIVE,
        candidate_universe_manifest=REPO / CANONICAL_CANDIDATE_UNIVERSE_MANIFEST_RELATIVE,
        no_episode_dispositions=REPO / NO_EPISODE_DISPOSITIONS_RELATIVE,
    )
    assert lfx.ok, lfx.errors


def test_phase2_closeout_counts_and_unknown_semantics() -> None:
    result = triage_frozen_universe(repo_root=REPO)
    assert len(result.rows) == FROZEN_CANDIDATE_COUNT == 4234
    assert result.survivor_count == 0
    assert result.s1_by_reason == {S1_REASON: FROZEN_S1_COUNT}
    assert result.s4_by_reason == {S4_REASON: FROZEN_S4_COUNT}
    assert FROZEN_S1_COUNT + FROZEN_S4_COUNT == FROZEN_CANDIDATE_COUNT
    assert "driver identity only" in S4_NOTE
    assert "I2 fail" in S4_NOTE
    assert "not an episode" in S4_NOTE
    assert "no physical disruption" not in S4_NOTE.casefold()
    assert "zero" not in S4_NOTE.casefold()
    assert "fixture HTML" in S1_NOTE
    assert "unverifiable" in S1_NOTE.casefold()
    assert "zero" not in S1_NOTE.casefold()
    ledger = LEDGER_PATH.read_text(encoding="utf-8")
    assert "UNKNOWN is not zero" in ledger
    assert "S4 proximity is driver-only absent I2" in ledger
    assert "not** proof of no physical disruption" in ledger
    assert "negative result" in ledger


def test_no_real_series_catalogued() -> None:
    series_dir = REPO / "catalog" / "series"
    real = [
        p
        for p in list(series_dir.glob("*.yaml")) + list(series_dir.glob("*.yml"))
        if p.stem not in {"_template", "README"}
    ]
    assert real == []
