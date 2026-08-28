"""Exact S1 original-object recovery for frozen D5 pointers.

The 37 frozen S1 ``raw_capture_pointer`` SHA-256 values match the committed
synthetic HTML in ``scripts/create_s1_fixtures.py`` exactly. Restoring those
bytes is content-addressed recovery, not a new candidate and not a live NTNI
mint. Live NTNI listing re-fetch is attempted only as corroboration and never
overwrites a mismatched original.
"""

from __future__ import annotations

import csv
import hashlib
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from grainsys.discovery.candidate_universe import CANONICAL_CANDIDATES_RELATIVE
from grainsys.discovery.capture import capture_candidate_evidence
from grainsys.discovery.config import REPO_ROOT, load_prereg_rules
from grainsys.discovery.recover_s4 import reconstruct_s4_store
from grainsys.ingest.ntni import NtniNormalizationError, parse_active_notice_listing

DISTRICT_HITS: dict[str, int] = {
    "MVR": 11,
    "LRH": 9,
    "LRL": 6,
    "LRN": 5,
    "MVS": 3,
    "MVK": 2,
    "MVM": 1,
}
BASE_YEAR = 2020
NTNI_USER_AGENT = "grainsys-discovery/1.0 (research)"
SEARCH_ROOTS: tuple[Path, ...] = (
    Path("/tmp/grain_data_v2"),
    Path("/tmp/grain_data"),
    Path("/workspace/data"),
    Path("/workspace/data/interim/grain_root"),
    Path("/data"),
    Path("/opt/cursor"),
    Path("/mnt"),
)


class S1RecoveryError(ValueError):
    """Fail-closed S1 recovery error."""


@dataclass(frozen=True)
class S1Expected:
    candidate_id: str
    control_number: str
    district: str
    capture_dir: str
    expected_sha256: str
    retrieved_on: str
    html_bytes: bytes


@dataclass(frozen=True)
class S1RecoveryResult:
    original_exact_restored: int
    current_corrob_retrieved: int
    still_missing_original: int
    failed_urls: int
    listing_controls_seen: int
    not_in_listing: int
    data_root: str
    notes: tuple[str, ...]


def fixture_html_bytes(control_number: str, district_code: str) -> bytes:
    """Exact HTML template from ``scripts/create_s1_fixtures.py``."""
    return (
        f"""<!DOCTYPE html>
<html>
<head><title>NTNI Notice {control_number}</title></head>
<body>
<h1>Notice to Navigation Interests</h1>
<p>District: {district_code}</p>
<p>Control Number: {control_number}</p>
<p>This notice contains information about dredging operations.</p>
</body>
</html>""".encode()
    )


def expected_s1_from_fixtures() -> dict[str, S1Expected]:
    """Map control_number -> expected original object derived from fixtures."""
    out: dict[str, S1Expected] = {}
    total_hits = 0
    for district_code, hit_count in DISTRICT_HITS.items():
        for i in range(1, hit_count + 1):
            total_hits += 1
            control_number = f"{district_code}-2020-{i:04d}"
            month = ((total_hits - 1) % 12) + 1
            day = ((total_hits - 1) % 28) + 1
            issue_date = f"{BASE_YEAR}-{month:02d}-{day:02d}"
            raw = fixture_html_bytes(control_number, district_code)
            out[control_number] = S1Expected(
                candidate_id="",
                control_number=control_number,
                district=district_code,
                capture_dir=f"S1-{control_number}",
                expected_sha256=hashlib.sha256(raw).hexdigest(),
                retrieved_on=f"{issue_date}T12:00:00Z",
                html_bytes=raw,
            )
    return out


def load_frozen_s1_rows(repo_root: Path | None = None) -> list[dict[str, str]]:
    root = repo_root if repo_root is not None else REPO_ROOT
    path = root / CANONICAL_CANDIDATES_RELATIVE
    with path.open(encoding="utf-8", newline="") as fh:
        rows = [r for r in csv.DictReader(fh) if r.get("sweep_id") == "S1"]
    if len(rows) != 37:
        raise S1RecoveryError(f"frozen S1 rows {len(rows)} != 37; refuse")
    return rows


def bind_frozen_s1_expectations(repo_root: Path | None = None) -> list[S1Expected]:
    fixtures = expected_s1_from_fixtures()
    bound: list[S1Expected] = []
    for row in load_frozen_s1_rows(repo_root):
        src = row["source_reference"]
        pointer = row["raw_capture_pointer"]
        expected_sha = pointer.rsplit("/", 1)[-1]
        fx = fixtures.get(src)
        if fx is None:
            raise S1RecoveryError(f"no fixture template for {src!r}; refuse")
        if fx.expected_sha256 != expected_sha:
            raise S1RecoveryError(
                f"{src}: fixture sha {fx.expected_sha256} != frozen {expected_sha}"
            )
        capture_dir = pointer.split("/")[2]
        bound.append(
            S1Expected(
                candidate_id=row["candidate_id"],
                control_number=src,
                district=fx.district,
                capture_dir=capture_dir,
                expected_sha256=expected_sha,
                retrieved_on=fx.retrieved_on,
                html_bytes=fx.html_bytes,
            )
        )
    return bound


def search_existing_s1_objects(
    expected: list[S1Expected],
    *,
    extra_roots: tuple[Path, ...] = (),
) -> dict[str, Path]:
    """Locate files named with the frozen object digest. Do not guess contents."""
    wanted = {item.expected_sha256: item for item in expected}
    found: dict[str, Path] = {}
    roots = tuple(SEARCH_ROOTS) + extra_roots
    for root in roots:
        if not root.exists():
            continue
        for sha, item in wanted.items():
            if sha in found:
                continue
            direct = (
                root / "sweeps" / "S1" / item.capture_dir / "objects" / sha
            )
            candidates = [direct]
            if root.name == "sweeps":
                candidates.append(root / "S1" / item.capture_dir / "objects" / sha)
            for path in candidates:
                if path.is_file():
                    digest = hashlib.sha256(path.read_bytes()).hexdigest()
                    if digest == sha:
                        found[sha] = path
    return found


def restore_s1_original_objects(
    *,
    data_root: Path,
    repo_root: Path | None = None,
    sweeps_subdir: str = "sweeps",
) -> S1RecoveryResult:
    """Write SHA-matching original S1 objects via append-only capture."""
    expected = bind_frozen_s1_expectations(repo_root)
    found = search_existing_s1_objects(expected)
    restored = 0
    from_disk = 0
    for item in expected:
        raw = item.html_bytes
        disk = found.get(item.expected_sha256)
        if disk is not None:
            disk_bytes = disk.read_bytes()
            if hashlib.sha256(disk_bytes).hexdigest() != item.expected_sha256:
                raise S1RecoveryError(
                    f"{item.control_number}: on-disk object {disk} hash mismatch; refuse"
                )
            raw = disk_bytes
            from_disk += 1
        rec = capture_candidate_evidence(
            sweep_id="S1",
            candidate_id=item.capture_dir,
            raw_bytes=raw,
            source_reference=item.control_number,
            sweeps_subdir=sweeps_subdir,
            data_root_path=data_root,
            retrieved_on=item.retrieved_on,
            original_filename=f"{item.control_number}.html",
            content_type="text/html",
        )
        if rec.sha256 != item.expected_sha256:
            raise S1RecoveryError(
                f"{item.control_number}: persisted sha {rec.sha256} != expected "
                f"{item.expected_sha256}; refuse"
            )
        restored += 1
    return S1RecoveryResult(
        original_exact_restored=restored,
        current_corrob_retrieved=0,
        still_missing_original=37 - restored,
        failed_urls=0,
        listing_controls_seen=0,
        not_in_listing=0,
        data_root=str(data_root),
        notes=(
            "Original S1 object bytes match committed create_s1_fixtures.py HTML.",
            f"On-disk SHA-named objects reused: {from_disk}/37; remainder from fixture template.",
            "Restored via capture_candidate_evidence using fixture retrieved_on metadata.",
            "Lock-1 live NTNI root /workspace/data/sweeps/S1 is not present on this host.",
        ),
    )


def _fetch_url(url: str, *, timeout: int = 60) -> tuple[bool, bytes | None, str | None]:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": NTNI_USER_AGENT})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return True, resp.read(), None
    except urllib.error.URLError as exc:
        return False, None, str(exc)
    except Exception as exc:
        return False, None, f"{type(exc).__name__}: {exc}"


def corroborate_s1_from_live_ntni(
    *,
    data_root: Path,
    repo_root: Path | None = None,
    sweeps_subdir: str = "sweeps",
) -> S1RecoveryResult:
    """Fetch live NTNI listings; append HTML only when SHA differs from original.

    Control-number match against frozen ``source_reference``. Does not overwrite
    original objects. Absence from today's listing is UNKNOWN, not zero.
    """
    root = repo_root if repo_root is not None else REPO_ROOT
    expected = {item.control_number: item for item in bind_frozen_s1_expectations(root)}
    cfg = load_prereg_rules(root)
    archives = [a for a in cfg["source_archives"] if a.get("sweep_id") == "S1"]
    failed_urls = 0
    seen_controls = 0
    matched = 0
    corrob = 0
    listing_errors: list[str] = []
    retrieved_on = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    for archive in archives:
        endpoint = str(archive["endpoint"])
        ok, raw, err = _fetch_url(endpoint)
        if not ok or raw is None:
            failed_urls += 1
            listing_errors.append(f"{endpoint}: {err}")
            continue
        try:
            notices = parse_active_notice_listing(raw)
        except NtniNormalizationError as exc:
            failed_urls += 1
            listing_errors.append(f"{endpoint}: parse {exc}")
            continue
        for notice in notices:
            seen_controls += 1
            item = expected.get(notice.controlnumber)
            if item is None:
                continue
            matched += 1
            ok_html, html, html_err = _fetch_url(notice.noticelink)
            if not ok_html or html is None:
                failed_urls += 1
                listing_errors.append(f"{notice.noticelink}: {html_err}")
                continue
            digest = hashlib.sha256(html).hexdigest()
            if digest == item.expected_sha256:
                continue
            capture_candidate_evidence(
                sweep_id="S1",
                candidate_id=item.capture_dir,
                raw_bytes=html,
                source_reference=notice.noticelink,
                sweeps_subdir=sweeps_subdir,
                data_root_path=data_root,
                retrieved_on=retrieved_on,
                original_filename=f"{item.control_number}.live.html",
                content_type="text/html",
            )
            corrob += 1
    not_in_listing = len(expected) - matched
    notes = (
        "Live NTNI corroboration does not replace original SHA-matching objects.",
        "Controls absent from today's listing remain UNKNOWN for live re-fetch, not zero.",
        *tuple(listing_errors[:12]),
    )
    return S1RecoveryResult(
        original_exact_restored=0,
        current_corrob_retrieved=corrob,
        still_missing_original=0,
        failed_urls=failed_urls,
        listing_controls_seen=seen_controls,
        not_in_listing=not_in_listing,
        data_root=str(data_root),
        notes=notes,
    )


def main(argv: list[str] | None = None) -> int:
    """Restore fixture-exact S1 originals; optionally live-NTNI corroborate."""
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--restore", action="store_true")
    parser.add_argument("--corroborate", action="store_true")
    parser.add_argument("--reconstruct-s4", action="store_true")
    args = parser.parse_args(argv)
    data_root: Path = args.data_root
    data_root.mkdir(parents=True, exist_ok=True)
    restored = S1RecoveryResult(
        original_exact_restored=0,
        current_corrob_retrieved=0,
        still_missing_original=37,
        failed_urls=0,
        listing_controls_seen=0,
        not_in_listing=0,
        data_root=str(data_root),
        notes=(),
    )
    if args.restore:
        restored = restore_s1_original_objects(data_root=data_root)
    extra = S1RecoveryResult(
        original_exact_restored=0,
        current_corrob_retrieved=0,
        still_missing_original=0,
        failed_urls=0,
        listing_controls_seen=0,
        not_in_listing=0,
        data_root=str(data_root),
        notes=(),
    )
    if args.corroborate:
        extra = corroborate_s1_from_live_ntni(data_root=data_root)
    if args.reconstruct_s4:
        s4 = reconstruct_s4_store(data_root=data_root)
        extra = S1RecoveryResult(
            original_exact_restored=extra.original_exact_restored,
            current_corrob_retrieved=extra.current_corrob_retrieved,
            still_missing_original=extra.still_missing_original,
            failed_urls=extra.failed_urls + s4["failed_urls"],
            listing_controls_seen=extra.listing_controls_seen,
            not_in_listing=extra.not_in_listing,
            data_root=str(data_root),
            notes=extra.notes + (f"S4 reconstruct: {s4}",),
        )
    result = S1RecoveryResult(
        original_exact_restored=restored.original_exact_restored,
        current_corrob_retrieved=extra.current_corrob_retrieved,
        still_missing_original=restored.still_missing_original,
        failed_urls=restored.failed_urls + extra.failed_urls,
        listing_controls_seen=extra.listing_controls_seen,
        not_in_listing=extra.not_in_listing,
        data_root=str(data_root),
        notes=restored.notes + extra.notes,
    )
    print(
        "D6_S1_RECOVERY_RESULT "
        f"original_exact_restored={result.original_exact_restored}/37 "
        f"current_corrob_retrieved={result.current_corrob_retrieved} "
        f"still_missing_original={result.still_missing_original} "
        f"failed_urls={result.failed_urls} "
        f"listing_controls_seen={result.listing_controls_seen} "
        f"not_in_listing={result.not_in_listing} "
        f"data_root={result.data_root}"
    )
    for note in result.notes:
        print(note)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
