"""Contamination-safe Phase 0 / Phase 1 discovery plumbing.

Does not search archives, open notices, or write episode ledger rows.
Live sweeps require committed ``config/discovery/prereg_rules.yaml`` **and**
the N3 ratification guard (accepted ADR, ``prereg-rules-v1`` tag, digests,
descendant commit).
"""

from grainsys.discovery.candidates import (
    FORBIDDEN_CANDIDATE_FIELDS,
    CandidateHit,
    CandidateIdError,
    mint_candidate_ids,
    validate_candidate_hit,
)
from grainsys.discovery.capture import candidate_capture_dir, sweeps_root
from grainsys.discovery.config import (
    DiscoveryConfigError,
    load_prereg_rules,
    prereg_rules_path,
)
from grainsys.discovery.coverage import (
    FORBIDDEN_COVERAGE_FIELDS,
    CoverageRecord,
    validate_coverage_record,
)
from grainsys.discovery.governance import (
    LOAD_BEARING_RELATIVE_PATHS,
    PREREG_TAG,
    RatificationError,
    SweepProvenance,
    assert_sweep_authorized,
    make_sweep_provenance,
)
from grainsys.discovery.sweep import SweepEnumerator, SweepError

__all__ = [
    "FORBIDDEN_CANDIDATE_FIELDS",
    "FORBIDDEN_COVERAGE_FIELDS",
    "LOAD_BEARING_RELATIVE_PATHS",
    "PREREG_TAG",
    "CandidateHit",
    "CandidateIdError",
    "CoverageRecord",
    "DiscoveryConfigError",
    "RatificationError",
    "SweepEnumerator",
    "SweepError",
    "SweepProvenance",
    "assert_sweep_authorized",
    "candidate_capture_dir",
    "load_prereg_rules",
    "make_sweep_provenance",
    "mint_candidate_ids",
    "prereg_rules_path",
    "sweeps_root",
    "validate_candidate_hit",
    "validate_coverage_record",
]
