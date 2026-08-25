"""Execute authorized S1-S8 sweeps against registered source archives.

This module performs the actual network fetch, keyword filtering, capture
persistence, and candidate universe construction for the preregistered
discovery sweep.

Requires N3 ratification (prereg-rules-v1 tag + digest match + ancestry).
"""

from __future__ import annotations

import hashlib
import os
import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from grainsys.discovery.capture import capture_candidate_evidence
from grainsys.discovery.config import REPO_ROOT, load_prereg_rules
from grainsys.discovery.governance import SweepProvenance, assert_sweep_authorized
from grainsys.discovery.sweep import KeywordPolicy, SweepEnumerator
from grainsys.ingest.ntni import (
    NtniNormalizationError,
    normalize_full_text,
    parse_active_notice_listing,
)


class SweepExecutionError(RuntimeError):
    """Sweep execution failed in a way that requires manual intervention."""


@dataclass(frozen=True)
class FetchResult:
    """Result of fetching a single source endpoint."""
    endpoint: str
    success: bool
    raw_bytes: bytes | None
    content_type: str | None
    error: str | None
    retrieved_at: str


@dataclass(frozen=True)
class NoticeHit:
    """A notice that matched the keyword policy."""
    sweep_id: str
    source_reference: str
    document_date: str | None
    authority: str
    district: str
    endpoint: str
    notice_link: str
    matched_terms: tuple[str, ...]
    full_text: str
    raw_bytes: bytes
    content_type: str


@dataclass(frozen=True)
class SweepResult:
    """Complete result of an S1 sweep execution."""
    provenance: SweepProvenance
    fetched_endpoints: int
    failed_endpoints: int
    total_notices: int
    keyword_hits: int
    capture_failures: int
    hits: tuple[NoticeHit, ...]
    errors: tuple[str, ...]


def _iso_utc_now() -> str:
    """Current UTC timestamp in ISO format."""
    return datetime.now(UTC).isoformat()


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _fetch_url(url: str, *, timeout: int = 30) -> FetchResult:
    """Fetch a URL and return the result."""
    retrieved_at = _iso_utc_now()
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "grainsys-discovery/1.0 (research)"}
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw_bytes = resp.read()
            content_type = resp.headers.get("Content-Type", "")
            return FetchResult(
                endpoint=url,
                success=True,
                raw_bytes=raw_bytes,
                content_type=content_type,
                error=None,
                retrieved_at=retrieved_at,
            )
    except urllib.error.URLError as exc:
        return FetchResult(
            endpoint=url,
            success=False,
            raw_bytes=None,
            content_type=None,
            error=str(exc),
            retrieved_at=retrieved_at,
        )
    except Exception as exc:
        return FetchResult(
            endpoint=url,
            success=False,
            raw_bytes=None,
            content_type=None,
            error=f"{type(exc).__name__}: {exc}",
            retrieved_at=retrieved_at,
        )


def _apply_keyword_policy(
    text: str,
    policy: KeywordPolicy,
) -> tuple[str, ...]:
    """Apply keyword policy and return matched terms."""
    if policy.case_sensitive:
        haystack = text
        terms = policy.terms
    else:
        haystack = text.casefold()
        terms = tuple(t.casefold() for t in policy.terms)
    
    matched: list[str] = []
    for i, term in enumerate(terms):
        if policy.match == "substring":
            if term in haystack:
                matched.append(policy.terms[i])
        elif policy.match == "whole_word":
            pattern = r"(?<!\w)" + re.escape(term) + r"(?!\w)"
            if re.search(pattern, haystack):
                matched.append(policy.terms[i])
    
    return tuple(matched)


def execute_s1_ntni_sweep(
    repo_root: Path | None = None,
    data_root: Path | None = None,
    *,
    dry_run: bool = False,
) -> SweepResult:
    """Execute the S1 NTNI sweep against all registered district endpoints.
    
    Returns a SweepResult containing all hits that matched the keyword policy.
    If dry_run=True, fetches and filters but does not persist captures.
    """
    root = repo_root if repo_root is not None else REPO_ROOT
    
    # N3 authorization gate
    provenance = assert_sweep_authorized(root)
    print(f"Sweep authorized: {provenance.prereg_tag} @ {provenance.execution_commit_sha[:12]}")
    
    # Load config and create enumerator
    cfg = load_prereg_rules(root)
    enumerator = SweepEnumerator(cfg)
    
    # Get data root for captures
    if data_root is None:
        env_root = os.environ.get("GRAIN_DATA_ROOT")
        if not env_root:
            raise SweepExecutionError(
                "GRAIN_DATA_ROOT not set and no explicit data_root provided"
            )
        data_root = Path(env_root)
    
    sweeps_subdir = cfg.get("capture", {}).get("sweeps_subdir", "sweeps")
    
    # Collect S1 archives
    s1_archives = list(enumerator.iter_archives(sweep_id="S1"))
    print(f"Found {len(s1_archives)} S1 NTNI district endpoints")
    
    errors: list[str] = []
    all_hits: list[NoticeHit] = []
    fetched_count = 0
    failed_count = 0
    total_notices = 0
    capture_failures = 0
    
    for archive in s1_archives:
        print(f"\nProcessing: {archive.district} ({archive.endpoint})")
        
        # Fetch listing JSON
        listing_result = _fetch_url(archive.endpoint)
        if not listing_result.success:
            errors.append(f"{archive.district}: {listing_result.error}")
            failed_count += 1
            print(f"  FAILED: {listing_result.error}")
            continue
        
        fetched_count += 1
        
        # Parse listing
        try:
            notices = parse_active_notice_listing(listing_result.raw_bytes)
        except NtniNormalizationError as exc:
            errors.append(f"{archive.district}: listing parse failed: {exc}")
            failed_count += 1
            print(f"  PARSE ERROR: {exc}")
            continue
        
        total_notices += len(notices)
        print(f"  Found {len(notices)} active notices")
        
        # Process each notice
        for notice in notices:
            # Fetch the HTML notice
            html_result = _fetch_url(notice.noticelink)
            if not html_result.success:
                errors.append(
                    f"{archive.district}/{notice.controlnumber}: "
                    f"HTML fetch failed: {html_result.error}"
                )
                continue
            
            # Normalize to full_text
            try:
                full_text = normalize_full_text(
                    html_result.raw_bytes,
                    content_type=html_result.content_type or "text/html",
                )
            except NtniNormalizationError as exc:
                errors.append(
                    f"{archive.district}/{notice.controlnumber}: "
                    f"normalize failed: {exc}"
                )
                continue
            
            # Apply keyword policy
            matched = _apply_keyword_policy(full_text, enumerator.keyword_policy)
            if not matched:
                continue
            
            print(f"    HIT: {notice.controlnumber} - {notice.noticeno} [{', '.join(matched)}]")
            
            hit = NoticeHit(
                sweep_id="S1",
                source_reference=notice.controlnumber,
                document_date=notice.issuedate,
                authority=archive.authority,
                district=archive.district,
                endpoint=archive.endpoint,
                notice_link=notice.noticelink,
                matched_terms=matched,
                full_text=full_text,
                raw_bytes=html_result.raw_bytes,
                content_type=html_result.content_type or "text/html",
            )
            all_hits.append(hit)
            
            # Persist capture (unless dry run)
            if not dry_run:
                # Generate a temporary candidate ID for capture organization
                # Real candidate IDs will be minted during D5 universe build
                temp_cid = f"S1-{notice.controlnumber}"
                try:
                    capture_candidate_evidence(
                        sweep_id="S1",
                        candidate_id=temp_cid,
                        raw_bytes=html_result.raw_bytes,
                        source_reference=notice.controlnumber,
                        sweeps_subdir=sweeps_subdir,
                        data_root_path=data_root,
                        retrieved_on=html_result.retrieved_at,
                        original_filename=f"{notice.controlnumber}.html",
                        content_type=html_result.content_type,
                    )
                except Exception as exc:
                    errors.append(
                        f"Capture failed for {notice.controlnumber}: {exc}"
                    )
                    capture_failures += 1
    
    print("\n=== S1 Sweep Summary ===")
    print(f"Endpoints fetched: {fetched_count}/{len(s1_archives)}")
    print(f"Total notices scanned: {total_notices}")
    print(f"Keyword hits: {len(all_hits)}")
    print(f"Capture failures: {capture_failures}")
    if errors:
        print(f"Errors: {len(errors)}")
    
    return SweepResult(
        provenance=provenance,
        fetched_endpoints=fetched_count,
        failed_endpoints=failed_count,
        total_notices=total_notices,
        keyword_hits=len(all_hits),
        capture_failures=capture_failures,
        hits=tuple(all_hits),
        errors=tuple(errors),
    )


def main() -> None:
    """CLI entry point for sweep execution."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Execute authorized S1-S8 discovery sweeps"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Fetch and filter but do not persist captures",
    )
    parser.add_argument(
        "--data-root",
        type=Path,
        help="Override GRAIN_DATA_ROOT",
    )
    args = parser.parse_args()
    
    result = execute_s1_ntni_sweep(
        data_root=args.data_root,
        dry_run=args.dry_run,
    )
    
    print("\n=== Sweep Complete ===")
    print(f"Provenance: {result.provenance.prereg_tag}")
    print(f"Config digest: {result.provenance.prereg_config_digest[:16]}...")
    print(f"Execution commit: {result.provenance.execution_commit_sha[:12]}")
    print(f"\nKeyword hits: {result.keyword_hits}")
    
    if result.hits:
        print("\nHits by district:")
        by_district: dict[str, int] = {}
        for hit in result.hits:
            by_district[hit.district] = by_district.get(hit.district, 0) + 1
        for district, count in sorted(by_district.items()):
            print(f"  {district}: {count}")


if __name__ == "__main__":
    main()
