"""Phase-2 I1/I2/I3 triage over the frozen D5 universe.

Mechanical admission against EPISODE_PROTOCOL.md §A.4 X1–X3 / I1 I2 I3.
Does not mint candidates, author episode YAML, open market data, or run H7.
UNKNOWN is never treated as zero. Quote-or-null: no quote ⇒ no episode fields.
"""

from __future__ import annotations

import csv
import hashlib
from collections import Counter
from dataclasses import dataclass
from io import StringIO
from pathlib import Path

import yaml

from grainsys.discovery.candidate_universe import (
    CANONICAL_CANDIDATE_UNIVERSE_MANIFEST_RELATIVE,
    CANONICAL_CANDIDATES_RELATIVE,
)
from grainsys.discovery.config import REPO_ROOT
from grainsys.discovery.evidence_inventory import (
    FROZEN_CANDIDATE_COUNT,
    FROZEN_CANDIDATE_UNIVERSE_VERSION,
    FROZEN_CANDIDATES_DIGEST,
    FROZEN_S1_COUNT,
    FROZEN_S4_COUNT,
)
from grainsys.lineage import check_universe_accounting

NO_EPISODE_DISPOSITIONS_RELATIVE = Path(
    "research/episodes/discovery/candidates/no_episode_dispositions.csv"
)
DISPOSITION_FIELDNAMES: tuple[str, ...] = ("candidate_id", "reason_code", "note")

S4_REASON = "R3"
S1_REASON = "R12"

S4_NOTE = (
    "I2 fail (X1): POINT_ONLY 100NM HURDAT2 storm-node proximity is driver "
    "identity only. Protocol: a storm track is not an episode. No documented "
    "operational consequence (closure, restriction, outage, embargo, queueing, "
    "capacity reduction, or documented throughput decline)."
)
S1_NOTE = (
    "SHA-bound capture body is committed fixture HTML matching frozen D5 "
    "(scripts/create_s1_fixtures.py), not a live NTNI notice. Fixture prose is "
    "not a dated operational restriction. Originating source unverifiable "
    "(X10/R12). Live NTNI re-fetch is not historical completeness."
)


class Phase2TriageError(ValueError):
    """Fail-closed Phase-2 triage error."""


@dataclass(frozen=True)
class DispositionRow:
    candidate_id: str
    reason_code: str
    note: str
    sweep_id: str

    def to_csv_row(self) -> dict[str, str]:
        return {
            "candidate_id": self.candidate_id,
            "reason_code": self.reason_code,
            "note": self.note,
        }


@dataclass(frozen=True)
class Phase2TriageResult:
    rows: tuple[DispositionRow, ...]
    s1_by_reason: dict[str, int]
    s4_by_reason: dict[str, int]
    survivor_count: int
    dispositions_relative: str


def _sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _require_frozen_d5(repo_root: Path) -> list[dict[str, str]]:
    csv_path = repo_root / CANONICAL_CANDIDATES_RELATIVE
    man_path = repo_root / CANONICAL_CANDIDATE_UNIVERSE_MANIFEST_RELATIVE
    if not csv_path.is_file() or not man_path.is_file():
        raise Phase2TriageError("frozen D5 artifacts missing; refuse")
    csv_bytes = csv_path.read_bytes()
    digest = _sha256_hex(csv_bytes)
    if digest != FROZEN_CANDIDATES_DIGEST:
        raise Phase2TriageError(
            f"candidates.csv digest {digest} != frozen {FROZEN_CANDIDATES_DIGEST}; refuse"
        )
    man = yaml.safe_load(man_path.read_text(encoding="utf-8"))
    if not isinstance(man, dict):
        raise Phase2TriageError("candidate_universe.yaml is not a mapping; refuse")
    version = man.get("candidate_universe_version")
    if version != FROZEN_CANDIDATE_UNIVERSE_VERSION:
        raise Phase2TriageError(
            f"candidate_universe_version {version!r} != frozen "
            f"{FROZEN_CANDIDATE_UNIVERSE_VERSION}; refuse"
        )
    count = man.get("candidate_count")
    if count != FROZEN_CANDIDATE_COUNT:
        raise Phase2TriageError(
            f"candidate_count {count!r} != frozen {FROZEN_CANDIDATE_COUNT}; refuse"
        )
    with csv_path.open(encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    if len(rows) != FROZEN_CANDIDATE_COUNT:
        raise Phase2TriageError(
            f"candidates.csv rows {len(rows)} != frozen {FROZEN_CANDIDATE_COUNT}; refuse"
        )
    return rows


def triage_frozen_universe(*, repo_root: Path | None = None) -> Phase2TriageResult:
    """Apply I1/I2/I3 mechanically. No new selector. Survivors only if all three pass."""
    root = repo_root if repo_root is not None else REPO_ROOT
    candidates = _require_frozen_d5(root)
    out: list[DispositionRow] = []
    for rec in candidates:
        sweep = rec["sweep_id"]
        cid = rec["candidate_id"]
        if sweep == "S4":
            out.append(
                DispositionRow(
                    candidate_id=cid,
                    reason_code=S4_REASON,
                    note=S4_NOTE,
                    sweep_id=sweep,
                )
            )
        elif sweep == "S1":
            out.append(
                DispositionRow(
                    candidate_id=cid,
                    reason_code=S1_REASON,
                    note=S1_NOTE,
                    sweep_id=sweep,
                )
            )
        else:
            raise Phase2TriageError(f"unexpected sweep_id {sweep!r} on {cid}; refuse")
    s1 = Counter(r.reason_code for r in out if r.sweep_id == "S1")
    s4 = Counter(r.reason_code for r in out if r.sweep_id == "S4")
    if s1[S1_REASON] != FROZEN_S1_COUNT or sum(s1.values()) != FROZEN_S1_COUNT:
        raise Phase2TriageError(f"S1 disposition counts {dict(s1)} != {FROZEN_S1_COUNT} R12")
    if s4[S4_REASON] != FROZEN_S4_COUNT or sum(s4.values()) != FROZEN_S4_COUNT:
        raise Phase2TriageError(f"S4 disposition counts {dict(s4)} != {FROZEN_S4_COUNT} R3")
    if len(out) != FROZEN_CANDIDATE_COUNT:
        raise Phase2TriageError(f"disposition rows {len(out)} != {FROZEN_CANDIDATE_COUNT}")
    return Phase2TriageResult(
        rows=tuple(out),
        s1_by_reason=dict(s1),
        s4_by_reason=dict(s4),
        survivor_count=0,
        dispositions_relative=NO_EPISODE_DISPOSITIONS_RELATIVE.as_posix(),
    )


def render_dispositions_csv(rows: tuple[DispositionRow, ...]) -> str:
    buf = StringIO()
    writer = csv.DictWriter(buf, fieldnames=list(DISPOSITION_FIELDNAMES), lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow(row.to_csv_row())
    return buf.getvalue()


def persist_phase2_dispositions(
    *,
    repo_root: Path | None = None,
) -> Phase2TriageResult:
    """Write the no-episode disposition ledger. Never mutates D5 identity files."""
    root = repo_root if repo_root is not None else REPO_ROOT
    csv_before = (root / CANONICAL_CANDIDATES_RELATIVE).read_bytes()
    man_before = (root / CANONICAL_CANDIDATE_UNIVERSE_MANIFEST_RELATIVE).read_bytes()
    result = triage_frozen_universe(repo_root=root)
    path = root / NO_EPISODE_DISPOSITIONS_RELATIVE
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_dispositions_csv(result.rows), encoding="utf-8")
    csv_after = (root / CANONICAL_CANDIDATES_RELATIVE).read_bytes()
    man_after = (root / CANONICAL_CANDIDATE_UNIVERSE_MANIFEST_RELATIVE).read_bytes()
    if csv_after != csv_before or man_after != man_before:
        raise Phase2TriageError("triage mutated frozen D5 identity; refuse")
    if _sha256_hex(csv_after) != FROZEN_CANDIDATES_DIGEST:
        raise Phase2TriageError("candidates.csv digest drifted during persist; refuse")
    fx = check_universe_accounting(
        [],
        candidates_csv=root / CANONICAL_CANDIDATES_RELATIVE,
        candidate_universe_manifest=root / CANONICAL_CANDIDATE_UNIVERSE_MANIFEST_RELATIVE,
        no_episode_dispositions=path,
    )
    if not fx.ok:
        raise Phase2TriageError("universe accounting failed: " + "; ".join(fx.errors))
    return result


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--persist", action="store_true")
    args = parser.parse_args(argv)
    if args.persist:
        result = persist_phase2_dispositions()
    else:
        result = triage_frozen_universe()
    print(
        "PHASE2_I1I2I3_AFTER_PR49_MERGE "
        f"s1_by_reason={result.s1_by_reason} "
        f"s4_by_reason={result.s4_by_reason} "
        f"survivors={result.survivor_count} "
        f"rows={len(result.rows)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
