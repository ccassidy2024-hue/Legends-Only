"""Build D5 candidate universe from captured sweep hits.

This module loads captured hits from GRAIN_DATA_ROOT sweep manifests and
builds the D5 candidate universe following ADR-0008 deterministic ordering.

Requires N3 ratification (prereg-rules-v1 tag + digest match + ancestry).
"""

from __future__ import annotations

import os
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from grainsys.discovery.candidate_universe import build_authorized_d5_candidate_universe
from grainsys.discovery.capture import MANIFEST_FILENAME, data_root
from grainsys.discovery.config import REPO_ROOT


class D5BuildError(ValueError):
    """D5 candidate universe build failed."""


@dataclass(frozen=True)
class SweepHit:
    """Normalized hit record for D5 candidate universe construction."""

    sweep_id: str
    source_reference: str
    raw_capture_pointer: str
    document_date: str
    stable_source_id: str

    def to_mapping(self) -> dict[str, str]:
        return {
            "sweep_id": self.sweep_id,
            "source_reference": self.source_reference,
            "raw_capture_pointer": self.raw_capture_pointer,
            "document_date": self.document_date,
            "stable_source_id": self.stable_source_id,
        }


def load_sweep_manifests(
    *,
    sweep_id: str,
    data_root_path: Path | str | None = None,
    sweeps_subdir: str = "sweeps",
) -> list[SweepHit]:
    """Load all capture manifests for a sweep family from GRAIN_DATA_ROOT.

    Returns normalized SweepHit records suitable for D5 candidate universe
    construction. Each capture manifest in
    ``$GRAIN_DATA_ROOT/<sweeps_subdir>/<sweep_id>/<candidate_id>/manifest.yaml``
    contributes one hit per capture record.
    """
    root = data_root(data_root_path)
    sweep_dir = root / sweeps_subdir / sweep_id

    if not sweep_dir.is_dir():
        raise D5BuildError(
            f"sweep directory does not exist: {sweep_dir}"
        )

    hits: list[SweepHit] = []

    for cand_dir in sorted(sweep_dir.iterdir()):
        if not cand_dir.is_dir():
            continue

        manifest_path = cand_dir / MANIFEST_FILENAME
        if not manifest_path.is_file():
            raise D5BuildError(
                f"candidate directory missing manifest: {cand_dir}"
            )

        with manifest_path.open(encoding="utf-8") as fh:
            try:
                data = yaml.safe_load(fh)
            except yaml.YAMLError as exc:
                raise D5BuildError(
                    f"invalid manifest YAML at {manifest_path}: {exc}"
                ) from exc

        if not isinstance(data, dict):
            raise D5BuildError(
                f"manifest is not a mapping: {manifest_path}"
            )

        manifest_sweep = data.get("sweep_id", "")
        manifest_cand = data.get("candidate_id", "")
        records = data.get("records", [])

        if manifest_sweep != sweep_id:
            raise D5BuildError(
                f"sweep_id mismatch in {manifest_path}: "
                f"expected {sweep_id!r}, got {manifest_sweep!r}"
            )

        if not isinstance(records, list):
            raise D5BuildError(
                f"records is not a list: {manifest_path}"
            )

        for i, rec in enumerate(records):
            if not isinstance(rec, dict):
                raise D5BuildError(
                    f"records[{i}] is not a mapping: {manifest_path}"
                )

            source_ref = rec.get("source_reference", "")
            sha256 = rec.get("sha256", "")

            if not source_ref:
                raise D5BuildError(
                    f"records[{i}].source_reference is empty: {manifest_path}"
                )

            raw_pointer = f"{sweeps_subdir}/{sweep_id}/{manifest_cand}/objects/{sha256}"

            hits.append(
                SweepHit(
                    sweep_id=sweep_id,
                    source_reference=source_ref,
                    raw_capture_pointer=raw_pointer,
                    document_date="",
                    stable_source_id="",
                )
            )

    return hits


def build_d5_from_sweeps(
    *,
    repo_root: Path | None = None,
    data_root_path: Path | str | None = None,
    required_sweep_families: Sequence[str],
    family_completion_attestations: Mapping[str, bool],
    persist: bool = False,
    frozen_at: str | None = None,
    sweeps_subdir: str = "sweeps",
) -> dict[str, Any]:
    """Build D5 candidate universe from sweep captures.

    Loads all captured hits from the specified sweep families and constructs
    the D5 candidate universe following ADR-0008 deterministic ordering.

    Parameters
    ----------
    repo_root : Path, optional
        Repository root for N3 authorization check. Defaults to REPO_ROOT.
    data_root_path : Path or str, optional
        Override GRAIN_DATA_ROOT for capture data location.
    required_sweep_families : Sequence[str]
        List of sweep family IDs (e.g., ["S1"]) that must be present.
    family_completion_attestations : Mapping[str, bool]
        Completion attestation for each required family (must all be True).
    persist : bool
        If True, write candidates.csv and candidate_universe.yaml to repo.
    frozen_at : str, optional
        ISO timestamp for freeze metadata (does not affect identity).
    sweeps_subdir : str
        Subdirectory under GRAIN_DATA_ROOT for sweep captures.

    Returns
    -------
    dict
        Build result summary including candidate count, digests, and paths.
    """
    root = repo_root if repo_root is not None else REPO_ROOT

    all_hits: list[dict[str, str]] = []
    for family in required_sweep_families:
        family_hits = load_sweep_manifests(
            sweep_id=family,
            data_root_path=data_root_path,
            sweeps_subdir=sweeps_subdir,
        )
        for hit in family_hits:
            all_hits.append(hit.to_mapping())

    if not all_hits:
        raise D5BuildError(
            "no hits loaded from sweep captures; cannot build empty universe"
        )

    result = build_authorized_d5_candidate_universe(
        repo_root=root,
        hits=all_hits,
        required_sweep_families=required_sweep_families,
        family_completion_attestations=family_completion_attestations,
        persist=persist,
        frozen_at=frozen_at,
    )

    summary = {
        "candidate_count": result.manifest.candidate_count,
        "candidate_universe_version": result.manifest.candidate_universe_version,
        "hit_set_digest": result.manifest.hit_set_digest,
        "candidates_digest": result.manifest.candidates_digest,
        "required_sweep_families": list(result.manifest.required_sweep_families),
        "completed_sweep_families": list(result.manifest.completed_sweep_families),
        "frozen_at": result.manifest.frozen_at,
        "persisted": persist,
    }

    if persist and result.written_candidates_path:
        summary["candidates_path"] = str(result.written_candidates_path)
        summary["manifest_path"] = str(result.written_manifest_path)

    return summary


def main() -> None:
    """CLI entry point for D5 candidate universe construction."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Build D5 candidate universe from captured sweep hits"
    )
    parser.add_argument(
        "--families",
        type=str,
        default="S1",
        help="Comma-separated sweep families (default: S1)",
    )
    parser.add_argument(
        "--data-root",
        type=Path,
        help="Override GRAIN_DATA_ROOT",
    )
    parser.add_argument(
        "--persist",
        action="store_true",
        help="Write candidates.csv and candidate_universe.yaml to repo",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Build universe without persisting (default)",
    )
    args = parser.parse_args()

    families = [f.strip() for f in args.families.split(",") if f.strip()]
    attestations = {f: True for f in families}

    print(f"Building D5 candidate universe from families: {families}")
    print(f"Data root: {args.data_root or os.environ.get('GRAIN_DATA_ROOT', '(not set)')}")

    result = build_d5_from_sweeps(
        data_root_path=args.data_root,
        required_sweep_families=families,
        family_completion_attestations=attestations,
        persist=args.persist and not args.dry_run,
    )

    print("\n=== D5 Build Result ===")
    print(f"Candidate count: {result['candidate_count']}")
    print(f"Universe version: {result['candidate_universe_version']}")
    print(f"Hit set digest: {result['hit_set_digest'][:16]}...")
    print(f"Candidates digest: {result['candidates_digest'][:16]}...")
    print(f"Required families: {result['required_sweep_families']}")
    print(f"Persisted: {result['persisted']}")

    if result.get("candidates_path"):
        print(f"Candidates path: {result['candidates_path']}")
        print(f"Manifest path: {result['manifest_path']}")


if __name__ == "__main__":
    main()
