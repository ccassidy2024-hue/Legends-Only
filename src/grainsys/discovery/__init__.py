"""Contamination-safe Phase 0 / Phase 1 discovery plumbing.

Does not search archives, open notices, or write episode ledger rows.
Live sweeps require committed ``config/discovery/prereg_rules.yaml`` **and**
the N3 ratification guard (accepted ADR, ``prereg-rules-v1`` or
``prereg-rules-v2`` tag, digests, descendant commit).
"""

from grainsys.discovery.archive_listing import (
    ArchiveListingError,
    normalize_and_mint_archive_listing,
    normalize_archive_listing,
)
from grainsys.discovery.candidate_universe import (
    CANDIDATES_CSV_FIELDNAMES,
    CANONICAL_CANDIDATE_UNIVERSE_MANIFEST_RELATIVE,
    CANONICAL_CANDIDATES_RELATIVE,
    D5_ID_PREFIX,
    D5_ORDERING_KEYS,
    D5_STABLE_ID_KEY,
    CandidateUniverseBuildResult,
    CandidateUniverseError,
    CandidateUniverseManifest,
    FrozenHitSet,
    UnsupportedCandidateUniverseSupersession,
    build_authorized_d5_candidate_universe,
    freeze_hit_set,
    mint_d5_candidate_ids,
    render_candidates_csv_bytes,
    write_canonical_candidates_csv,
    write_canonical_universe_artifacts,
)
from grainsys.discovery.candidates import (
    FORBIDDEN_CANDIDATE_FIELDS,
    CandidateHit,
    CandidateIdError,
    mint_candidate_ids,
    researcher_parity_for_candidate_id,
    validate_candidate_hit,
)
from grainsys.discovery.capture import candidate_capture_dir, sweeps_root
from grainsys.discovery.config import (
    ALLOWED_KEYWORD_MATCH_MODES,
    ANALYSIS_ANCHOR_GRID_KEYS,
    PROTOCOL_SWEEP_FAMILIES,
    DiscoveryConfigError,
    load_prereg_rules,
    prereg_rules_path,
)
from grainsys.discovery.coverage import (
    FORBIDDEN_COVERAGE_FIELDS,
    CoverageRecord,
    CoveredExposure,
    compute_covered_exposure,
    validate_coverage_collection,
    validate_coverage_record,
)
from grainsys.discovery.governance import (
    LOAD_BEARING_RELATIVE_PATHS,
    PREREG_TAG,
    RatificationError,
    SweepProvenance,
    assert_sweep_authorized,
    build_ratification_manifest,
    emit_ratification_manifest_bytes,
    make_sweep_provenance,
    serialize_ratification_manifest,
)
from grainsys.discovery.sweep import SweepEnumerator, SweepError

__all__ = [
    "ALLOWED_KEYWORD_MATCH_MODES",
    "ANALYSIS_ANCHOR_GRID_KEYS",
    "FORBIDDEN_CANDIDATE_FIELDS",
    "FORBIDDEN_COVERAGE_FIELDS",
    "LOAD_BEARING_RELATIVE_PATHS",
    "PREREG_TAG",
    "PROTOCOL_SWEEP_FAMILIES",
    "ArchiveListingError",
    "CandidateHit",
    "CandidateIdError",
    "CoverageRecord",
    "CoveredExposure",
    "DiscoveryConfigError",
    "RatificationError",
    "SweepEnumerator",
    "SweepError",
    "SweepProvenance",
    "assert_sweep_authorized",
    "build_ratification_manifest",
    "candidate_capture_dir",
    "compute_covered_exposure",
    "emit_ratification_manifest_bytes",
    "load_prereg_rules",
    "make_sweep_provenance",
    "mint_candidate_ids",
    "mint_d5_candidate_ids",
    "freeze_hit_set",
    "build_authorized_d5_candidate_universe",
    "render_candidates_csv_bytes",
    "write_canonical_candidates_csv",
    "write_canonical_universe_artifacts",
    "researcher_parity_for_candidate_id",
    "CandidateUniverseError",
    "CandidateUniverseManifest",
    "CandidateUniverseBuildResult",
    "FrozenHitSet",
    "UnsupportedCandidateUniverseSupersession",
    "D5_ID_PREFIX",
    "D5_ORDERING_KEYS",
    "D5_STABLE_ID_KEY",
    "CANONICAL_CANDIDATES_RELATIVE",
    "CANONICAL_CANDIDATE_UNIVERSE_MANIFEST_RELATIVE",
    "CANDIDATES_CSV_FIELDNAMES",
    "normalize_and_mint_archive_listing",
    "normalize_archive_listing",
    "prereg_rules_path",
    "serialize_ratification_manifest",
    "sweeps_root",
    "validate_candidate_hit",
    "validate_coverage_collection",
    "validate_coverage_record",
]
