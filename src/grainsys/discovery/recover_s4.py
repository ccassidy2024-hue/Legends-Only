"""SHA-faithful reconstruction of D5 S4 capture objects.

Does not mint candidates, write coverage YAML, or persist D5. Pairing matches
``execute_v2_families`` Census A / POINT_ONLY / 100 NM inclusive first-match.
``retrieved_on`` is omitted because original capture timestamps are unknown
on this host; inventory verifies object SHA + manifest linkage only.
"""

from __future__ import annotations

import csv
import hashlib
import urllib.error
import urllib.request
from pathlib import Path

from grainsys.discovery.candidate_universe import CANONICAL_CANDIDATES_RELATIVE
from grainsys.discovery.capture import capture_candidate_evidence
from grainsys.discovery.config import REPO_ROOT, load_prereg_rules
from grainsys.discovery.execute_v2_families import (
    S4_ATLANTIC_SHA256,
    S4_PACIFIC_SHA256,
    S4_RADIUS_M,
    haversine_m,
    parse_hurdat2_positions,
)

_USER_AGENT = "grainsys-discovery/1.0 (research)"


class S4RecoveryError(ValueError):
    """Fail-closed S4 reconstruction error."""


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _fetch(url: str, *, timeout: int = 120) -> tuple[bool, bytes | None, str | None]:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return True, resp.read(), None
    except urllib.error.URLError as exc:
        return False, None, str(exc)
    except Exception as exc:
        return False, None, f"{type(exc).__name__}: {exc}"


def _frozen_s4_expected(repo_root: Path) -> dict[str, str]:
    path = repo_root / CANONICAL_CANDIDATES_RELATIVE
    out: dict[str, str] = {}
    with path.open(encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            if row.get("sweep_id") != "S4":
                continue
            pointer = row["raw_capture_pointer"]
            capdir = pointer.split("/")[2]
            sha = pointer.rsplit("/", 1)[-1]
            out[capdir] = sha
    if len(out) != 4197:
        raise S4RecoveryError(f"frozen S4 rows {len(out)} != 4197; refuse")
    return out


def reconstruct_s4_store(
    *,
    data_root: Path,
    repo_root: Path | None = None,
    timeout_s: int = 120,
) -> dict[str, int | str]:
    """Rebuild S4 storm-node objects + HURDAT2 archives if SHA matches D5."""
    root = repo_root if repo_root is not None else REPO_ROOT
    expected_s4 = _frozen_s4_expected(root)
    cfg = load_prereg_rules(root)
    sweeps_subdir = cfg["capture"]["sweeps_subdir"]
    sample_start = cfg["sample_period"]["sample_start"]
    sample_end = cfg["sample_period"]["sample_end"]
    s4_archives = [a for a in cfg["source_archives"] if a.get("sweep_id") == "S4"]
    if len(s4_archives) != 1:
        raise S4RecoveryError(f"expected one S4 archive, got {len(s4_archives)}")
    endpoints = list(s4_archives[0]["endpoints"])
    expected_hurdat = {endpoints[0]: S4_ATLANTIC_SHA256, endpoints[1]: S4_PACIFIC_SHA256}
    positions: list[tuple[str, str, float, float]] = []
    failed_urls = 0
    hurdat_ok = 0
    errors: list[str] = []
    for url in endpoints:
        ok, raw, err = _fetch(url, timeout=timeout_s)
        if not ok or raw is None:
            failed_urls += 1
            errors.append(f"{url}: {err}")
            continue
        digest = _sha256(raw)
        if digest != expected_hurdat[url]:
            failed_urls += 1
            errors.append(f"{url}: digest {digest} != {expected_hurdat[url]}")
            continue
        cid = "S4-hurdat-" + _sha256(url.encode())[:12]
        rec = capture_candidate_evidence(
            sweep_id="S4",
            candidate_id=cid,
            raw_bytes=raw,
            source_reference=url,
            sweeps_subdir=sweeps_subdir,
            data_root_path=data_root,
            original_filename=url.rsplit("/", 1)[-1],
            content_type="text/plain",
        )
        if rec.sha256 != digest:
            raise S4RecoveryError(f"{cid}: persisted sha mismatch; refuse")
        hurdat_ok += 1
        positions.extend(
            parse_hurdat2_positions(raw, sample_start=sample_start, sample_end=sample_end)
        )
    if hurdat_ok != 2:
        return {
            "s4_pairs_sha_matched": 0,
            "s4_pairs_sha_mismatch": 0,
            "s4_pairs_captured": 0,
            "hurdat2_archives": hurdat_ok,
            "failed_urls": failed_urls,
            "error": "; ".join(errors) or "HURDAT2 fetch incomplete",
        }

    nodes = cfg["s4_node_registry"]["nodes"]
    pair_seen: set[tuple[str, str]] = set()
    restored = 0
    sha_mismatch = 0
    for storm_id, stamp, lat, lon in positions:
        for node in nodes:
            key = (storm_id, str(node["node_id"]))
            if key in pair_seen:
                continue
            dist = haversine_m(lat, lon, float(node["lat"]), float(node["lon"]))
            if dist <= S4_RADIUS_M:
                pair_seen.add(key)
                src = f"{storm_id}:{node['node_id']}"
                cid = f"S4-{storm_id}-{node['node_id']}"
                payload = (
                    f"{src}\n{stamp}\n{lat}\n{lon}\n{node['lat']}\n"
                    f"{node['lon']}\n{dist}\n"
                ).encode()
                got = _sha256(payload)
                expected = expected_s4.get(cid)
                if expected is not None and got != expected:
                    sha_mismatch += 1
                    continue
                rec = capture_candidate_evidence(
                    sweep_id="S4",
                    candidate_id=cid,
                    raw_bytes=payload,
                    source_reference=src,
                    sweeps_subdir=sweeps_subdir,
                    data_root_path=data_root,
                    original_filename=f"{src}.txt",
                    content_type="text/plain",
                )
                if rec.sha256 != got:
                    raise S4RecoveryError(f"{cid}: persisted sha mismatch; refuse")
                if expected is not None:
                    restored += 1
    if sha_mismatch:
        raise S4RecoveryError(
            f"S4 payload SHA mismatched frozen pointers for {sha_mismatch} pairs; refuse"
        )
    if restored != 4197:
        raise S4RecoveryError(f"S4 SHA-matched pairs {restored} != 4197; refuse")
    return {
        "s4_pairs_sha_matched": restored,
        "s4_pairs_sha_mismatch": sha_mismatch,
        "s4_pairs_captured": len(pair_seen),
        "hurdat2_archives": hurdat_ok,
        "failed_urls": failed_urls,
        "error": "",
    }
