"""Phase-2 I1/I2/I3 triage: mechanical drops, no D5 mutation, no episode YAML."""

from __future__ import annotations

import csv
import hashlib
from pathlib import Path

import yaml

from grainsys.discovery.candidate_universe import (
    CANONICAL_CANDIDATE_UNIVERSE_MANIFEST_RELATIVE,
    CANONICAL_CANDIDATES_RELATIVE,
)
from grainsys.discovery.evidence_inventory import (
    FROZEN_CANDIDATE_COUNT,
    FROZEN_CANDIDATE_UNIVERSE_VERSION,
    FROZEN_CANDIDATES_DIGEST,
    FROZEN_S1_COUNT,
    FROZEN_S4_COUNT,
)
from grainsys.discovery.phase2_triage import (
    NO_EPISODE_DISPOSITIONS_RELATIVE,
    S1_NOTE,
    S1_REASON,
    S4_NOTE,
    S4_REASON,
    persist_phase2_dispositions,
    render_dispositions_csv,
    triage_frozen_universe,
)
from grainsys.lineage import check_universe_accounting

REPO = Path(__file__).resolve().parents[1]


def test_s4_dispositions_are_r3_per_candidate_not_collapsed() -> None:
    result = triage_frozen_universe(repo_root=REPO)
    s4 = [r for r in result.rows if r.sweep_id == "S4"]
    assert len(s4) == FROZEN_S4_COUNT
    assert {r.reason_code for r in s4} == {S4_REASON}
    ids = [r.candidate_id for r in s4]
    assert len(set(ids)) == FROZEN_S4_COUNT
    assert all(cid.startswith("CAND-") for cid in ids)
    assert not any(cid.startswith("S4-") for cid in ids)
    assert result.s4_by_reason == {S4_REASON: FROZEN_S4_COUNT}


def test_s1_fixture_html_is_r12_not_treated_as_zero() -> None:
    result = triage_frozen_universe(repo_root=REPO)
    s1 = [r for r in result.rows if r.sweep_id == "S1"]
    assert len(s1) == FROZEN_S1_COUNT
    assert {r.reason_code for r in s1} == {S1_REASON}
    assert all("fixture HTML" in r.note for r in s1)
    assert all("not a live NTNI notice" in r.note for r in s1)
    assert "dredging operations" not in S1_NOTE.casefold()
    assert "not a dated operational restriction" in S1_NOTE
    assert result.s1_by_reason == {S1_REASON: FROZEN_S1_COUNT}
    assert result.survivor_count == 0


def test_d5_identity_unchanged_by_triage_persist(tmp_path: Path) -> None:
    cand = REPO / CANONICAL_CANDIDATES_RELATIVE
    man = REPO / CANONICAL_CANDIDATE_UNIVERSE_MANIFEST_RELATIVE
    before_csv = cand.read_bytes()
    before_man = man.read_bytes()
    dest = tmp_path / "repo"
    cand_dir = dest / cand.parent.relative_to(REPO)
    cand_dir.mkdir(parents=True)
    (cand_dir / cand.name).write_bytes(before_csv)
    (cand_dir / man.name).write_bytes(before_man)
    persist_phase2_dispositions(repo_root=dest)
    assert (dest / CANONICAL_CANDIDATES_RELATIVE).read_bytes() == before_csv
    assert (dest / CANONICAL_CANDIDATE_UNIVERSE_MANIFEST_RELATIVE).read_bytes() == before_man
    assert hashlib.sha256(before_csv).hexdigest() == FROZEN_CANDIDATES_DIGEST
    live_man = yaml.safe_load(before_man)
    assert live_man["candidate_universe_version"] == FROZEN_CANDIDATE_UNIVERSE_VERSION
    assert live_man["candidate_count"] == FROZEN_CANDIDATE_COUNT


def test_no_episode_yaml_added() -> None:
    real = [
        p
        for p in (REPO / "research/episodes/entries").glob("EP-*.yaml")
        if not p.name.startswith("EP-0000-000")
    ]
    assert real == []


def test_committed_dispositions_account_full_universe() -> None:
    path = REPO / NO_EPISODE_DISPOSITIONS_RELATIVE
    assert path.is_file()
    with path.open(encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    assert list(rows[0].keys()) == ["candidate_id", "reason_code", "note"]
    assert len(rows) == FROZEN_CANDIDATE_COUNT
    expected = triage_frozen_universe(repo_root=REPO)
    assert path.read_text(encoding="utf-8") == render_dispositions_csv(expected.rows)
    s4 = [r for r in rows if r["reason_code"] == S4_REASON]
    s1 = [r for r in rows if r["reason_code"] == S1_REASON]
    assert len(s4) == FROZEN_S4_COUNT
    assert len(s1) == FROZEN_S1_COUNT
    assert all(r["note"] == S4_NOTE for r in s4)
    assert all(r["note"] == S1_NOTE for r in s1)
    fx = check_universe_accounting(
        [],
        candidates_csv=REPO / CANONICAL_CANDIDATES_RELATIVE,
        candidate_universe_manifest=REPO / CANONICAL_CANDIDATE_UNIVERSE_MANIFEST_RELATIVE,
        no_episode_dispositions=path,
    )
    assert fx.ok, fx.errors
    assert expected.survivor_count == 0
    assert FROZEN_S1_COUNT + FROZEN_S4_COUNT == FROZEN_CANDIDATE_COUNT
