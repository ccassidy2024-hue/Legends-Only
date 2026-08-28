"""Outcome-blind S2-S8 execution against the ratified v2 prereg config.

Does not read market outcomes. Does not modify load-bearing N3 blobs.
UNKNOWN is never treated as zero. Inner PDF text extraction remains UNKNOWN.
"""

from __future__ import annotations

import csv
import hashlib
import math
import os
import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from grainsys.discovery.candidate_universe import (
    CANONICAL_CANDIDATE_UNIVERSE_MANIFEST_RELATIVE,
    CANONICAL_CANDIDATES_RELATIVE,
    build_authorized_d5_candidate_universe,
)
from grainsys.discovery.capture import MANIFEST_FILENAME, capture_candidate_evidence
from grainsys.discovery.config import REPO_ROOT, load_prereg_rules
from grainsys.discovery.coverage import validate_coverage_record
from grainsys.discovery.governance import assert_sweep_authorized
from grainsys.discovery.sweep import KeywordPolicy
from grainsys.ingest.uscg_msib import MsibNormalizationError, parse_navcen_msib_listing

S4_ATLANTIC_SHA256 = "1b9b0c7beed5b4505838658b1d30e159fc84330c60891a58cfcf43ae55c37202"
S4_PACIFIC_SHA256 = "db65f8bc538d5c05e15f738c96111861d6ce3572c007879de58e44d4d05a9cd6"
S4_EARTH_RADIUS_M = 6366707.019493707
S4_RADIUS_M = 185200
_WORD_BOUNDARY_LEFT = r"(?<!\w)"
_WORD_BOUNDARY_RIGHT = r"(?!\w)"
_LAT_RE = re.compile(r"^(\d+(?:\.\d+)?)([NS])$", re.IGNORECASE)
_LON_RE = re.compile(r"^(\d+(?:\.\d+)?)([EW])$", re.IGNORECASE)


class V2FamilyExecutionError(RuntimeError):
    """S2-S8 execution failed closed."""


@dataclass(frozen=True)
class FamilyOutcome:
    sweep_id: str
    coverage_status: str
    sweep_status: str
    records_matched: int | None
    hits: int
    unknown_notes: str
    errors: tuple[str, ...]


def _iso_utc_now() -> str:
    return datetime.now(UTC).isoformat()


def _today() -> str:
    return datetime.now(UTC).date().isoformat()


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _fetch(url: str, *, timeout: int = 60) -> tuple[bool, bytes | None, str | None, str | None]:
    try:
        req = urllib.request.Request(
            url, headers={"User-Agent": "grainsys-discovery/1.0 (research)"}
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
            ctype = resp.headers.get("Content-Type", "")
            return True, raw, ctype, None
    except urllib.error.URLError as exc:
        return False, None, None, str(exc)
    except Exception as exc:
        return False, None, None, f"{type(exc).__name__}: {exc}"


def _keyword_policy(cfg: dict[str, Any]) -> KeywordPolicy:
    kp = cfg["keyword_policy"]
    return KeywordPolicy(
        terms=tuple(str(t) for t in kp["terms"]),
        match=str(kp["match"]),
        case_sensitive=bool(kp["case_sensitive"]),
        fields=tuple(str(f) for f in kp["fields"]),
    )


def _matched_terms(text: str, policy: KeywordPolicy) -> tuple[str, ...]:
    haystack = text if policy.case_sensitive else text.casefold()
    terms = policy.terms if policy.case_sensitive else tuple(t.casefold() for t in policy.terms)
    matched: list[str] = []
    for i, term in enumerate(terms):
        if policy.match == "substring":
            if term in haystack:
                matched.append(policy.terms[i])
        elif policy.match == "whole_word":
            pattern = _WORD_BOUNDARY_LEFT + re.escape(term) + _WORD_BOUNDARY_RIGHT
            if re.search(pattern, haystack):
                matched.append(policy.terms[i])
    return tuple(matched)


def _visible_text(raw: bytes) -> str:
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        text = raw.decode("latin-1", errors="replace")
    text = re.sub(r"(?is)<script[^>]*>.*?</script>", " ", text)
    text = re.sub(r"(?is)<style[^>]*>.*?</style>", " ", text)
    text = re.sub(r"(?s)<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _write_coverage(path: Path, record: dict[str, Any]) -> None:
    validate_coverage_record(record)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(record, sort_keys=False), encoding="utf-8")


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    p1 = math.radians(lat1)
    p2 = math.radians(lat2)
    dphi = p2 - p1
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlam / 2) ** 2
    return 2 * S4_EARTH_RADIUS_M * math.asin(min(1.0, math.sqrt(a)))


def parse_hurdat_latlon(lat_tok: str, lon_tok: str) -> tuple[float, float] | None:
    lat_m = _LAT_RE.fullmatch(lat_tok.strip())
    lon_m = _LON_RE.fullmatch(lon_tok.strip())
    if lat_m is None or lon_m is None:
        return None
    lat = float(lat_m.group(1))
    lon = float(lon_m.group(1))
    if lat_m.group(2).upper() == "S":
        lat = -lat
    if lon_m.group(2).upper() == "W":
        lon = -lon
    return lat, lon


def parse_hurdat2_positions(
    raw: bytes, *, sample_start: str, sample_end: str
) -> list[tuple[str, str, float, float]]:
    """Return (storm_id, yyyymmddhhmm, lat, lon) inside the sample period."""
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        text = raw.decode("latin-1")
    start = int(sample_start.replace("-", ""))
    end = int(sample_end.replace("-", ""))
    storm_id = ""
    out: list[tuple[str, str, float, float]] = []
    seen: set[tuple[str, str, float, float]] = set()
    for line in text.splitlines():
        if not line.strip():
            continue
        parts = [p.strip() for p in line.split(",")]
        if len(parts) >= 3 and re.fullmatch(r"[A-Z]{2}\d{6}", parts[0]):
            storm_id = parts[0]
            continue
        if not storm_id or len(parts) < 7:
            continue
        ymd, hhmm = parts[0], parts[1]
        if not re.fullmatch(r"\d{8}", ymd) or not re.fullmatch(r"\d{4}", hhmm):
            continue
        day = int(ymd)
        if day < start or day > end:
            continue
        parsed = parse_hurdat_latlon(parts[4], parts[5])
        if parsed is None:
            continue
        lat, lon = parsed
        key = (storm_id, ymd + hhmm, lat, lon)
        if key in seen:
            continue
        seen.add(key)
        out.append(key)
    return out


def _replace_s1_only_intermediate(root: Path) -> None:
    """Authorized replacement of the S1-only intermediate D5 universe."""
    csv_path = root / CANONICAL_CANDIDATES_RELATIVE
    man_path = root / CANONICAL_CANDIDATE_UNIVERSE_MANIFEST_RELATIVE
    if not csv_path.is_file() or not man_path.is_file():
        return
    man = yaml.safe_load(man_path.read_text(encoding="utf-8"))
    if not isinstance(man, dict):
        raise V2FamilyExecutionError("existing D5 manifest is not a mapping")
    families = man.get("required_sweep_families")
    if families != ["S1"]:
        raise V2FamilyExecutionError(
            f"refuse to replace D5 universe with families {families!r}; "
            "only the S1-only intermediate may be replaced"
        )
    csv_path.unlink()
    man_path.unlink()


def _s4_hits_from_captures(data_root: Path, sweeps_subdir: str) -> list[dict[str, str]]:
    sweep_dir = data_root / sweeps_subdir / "S4"
    hits: list[dict[str, str]] = []
    if not sweep_dir.is_dir():
        return hits
    for cand_dir in sorted(sweep_dir.iterdir()):
        if not cand_dir.is_dir() or cand_dir.name.startswith("S4-hurdat-"):
            continue
        manifest_path = cand_dir / MANIFEST_FILENAME
        if not manifest_path.is_file():
            continue
        data = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
        records = data.get("records") or []
        if not records:
            continue
        rec = records[0]
        src = rec.get("source_reference", "")
        sha = rec.get("sha256", "")
        if ":" not in src:
            continue
        hits.append(
            {
                "sweep_id": "S4",
                "source_reference": src,
                "raw_capture_pointer": f"{sweeps_subdir}/S4/{cand_dir.name}/objects/{sha}",
                "document_date": "",
                "stable_source_id": src.split(":", 1)[0],
            }
        )
    return hits


def _s1_hits_from_repo(repo: Path) -> list[dict[str, str]]:
    path = repo / "research" / "episodes" / "discovery" / "candidates" / "candidates.csv"
    hits: list[dict[str, str]] = []
    with path.open(encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            if row.get("sweep_id") != "S1":
                continue
            hits.append(
                {
                    "sweep_id": "S1",
                    "source_reference": row["source_reference"],
                    "raw_capture_pointer": row["raw_capture_pointer"],
                    "document_date": row.get("document_date") or "",
                    "stable_source_id": row.get("stable_source_id") or "",
                }
            )
    if not hits:
        raise V2FamilyExecutionError("existing S1 D5 hits missing; refuse empty S1 set")
    return hits


def execute_v2_families(
    repo_root: Path | None = None,
    data_root: Path | None = None,
    *,
    persist_d5: bool = True,
) -> dict[str, Any]:
    root = repo_root if repo_root is not None else REPO_ROOT
    provenance = assert_sweep_authorized(root)
    cfg = load_prereg_rules(root)
    policy = _keyword_policy(cfg)
    sample_start = cfg["sample_period"]["sample_start"]
    sample_end = cfg["sample_period"]["sample_end"]
    retrieved_on = _today()
    if data_root is None:
        env = os.environ.get("GRAIN_DATA_ROOT")
        if not env:
            raise V2FamilyExecutionError("GRAIN_DATA_ROOT unset")
        data_root = Path(env)
    sweeps_subdir = cfg["capture"]["sweeps_subdir"]
    coverage_dir = root / cfg["coverage"]["records_dir"]
    archives = list(cfg["source_archives"])
    outcomes: dict[str, FamilyOutcome] = {}
    new_hits: list[dict[str, str]] = []

    # S2 registry-only: no archive endpoint, no independent candidates.
    _write_coverage(
        coverage_dir / "S2_gauge_registry.yaml",
        {
            "schema_version": "0.2",
            "record_kind": "source_coverage",
            "source_family": "S2",
            "authority": "USGS/AHPS",
            "district": "registered_gauges",
            "vehicle": "gauge registry corroboration only",
            "endpoint": None,
            "earliest_available": None,
            "latest_available": None,
            "retrieved_on": retrieved_on,
            "coverage_status": "unknown",
            "sweep_status": "not_attempted",
            "records_matched": None,
            "scope_start": None,
            "scope_end": None,
            "notes": (
                "S2 is registry-only OPERATIONAL_RESTRICTION_ONLY corroboration. "
                "No archive endpoint is registered. Independent candidates are not "
                "generated from raw stage. UNKNOWN is not zero."
            ),
        },
    )
    outcomes["S2"] = FamilyOutcome(
        "S2", "unknown", "not_attempted", None, 0,
        "registry-only; no independent candidates", (),
    )

    def _listing_family(sweep_id: str, archive: dict[str, Any], *, district: str) -> FamilyOutcome:
        endpoint = str(archive["endpoint"])
        ok, raw, ctype, err = _fetch(endpoint)
        errors: list[str] = []
        if not ok or raw is None:
            _write_coverage(
                coverage_dir / f"{sweep_id}_{district}.yaml",
                {
                    "schema_version": "0.2",
                    "record_kind": "source_coverage",
                    "source_family": sweep_id,
                    "authority": archive["authority"],
                    "district": district,
                    "vehicle": archive["vehicle"],
                    "endpoint": endpoint,
                    "earliest_available": None,
                    "latest_available": None,
                    "retrieved_on": retrieved_on,
                    "coverage_status": "unknown",
                    "sweep_status": "not_attempted",
                    "records_matched": None,
                    "scope_start": None,
                    "scope_end": None,
                    "notes": f"Fetch failed; UNKNOWN not zero. error={err}",
                },
            )
            return FamilyOutcome(sweep_id, "unknown", "not_attempted", None, 0, f"fetch failed: {err}", (str(err),))
        text = _visible_text(raw)
        matched = _matched_terms(text, policy)
        records_matched = 1 if matched else 0
        listed = 0
        if sweep_id == "S3":
            try:
                refs = parse_navcen_msib_listing(raw, year=int(sample_end[:4]))
                listed = len(refs)
            except MsibNormalizationError as exc:
                errors.append(f"MSIB listing parse: {exc}")
        cid = f"{sweep_id}-listing-{district}"
        rec = capture_candidate_evidence(
            sweep_id=sweep_id,
            candidate_id=cid,
            raw_bytes=raw,
            source_reference=endpoint,
            sweeps_subdir=sweeps_subdir,
            data_root_path=data_root,
            retrieved_on=_iso_utc_now(),
            original_filename=f"{sweep_id}-{district}.html",
            content_type=ctype,
        )
        hit_count = 0
        if matched:
            pointer = f"{sweeps_subdir}/{sweep_id}/{cid}/objects/{rec.sha256}"
            new_hits.append(
                {
                    "sweep_id": sweep_id,
                    "source_reference": f"{sweep_id}:{district}:listing",
                    "raw_capture_pointer": pointer,
                    "document_date": retrieved_on,
                    "stable_source_id": "",
                }
            )
            hit_count = 1
        notes = (
            "Listing-page keyword scan only. Inner PDF/document full_text extraction "
            f"is UNKNOWN. listed_inner_rows={listed}. matched_terms={list(matched)}."
        )
        _write_coverage(
            coverage_dir / f"{sweep_id}_{district}.yaml",
            {
                "schema_version": "0.2",
                "record_kind": "source_coverage",
                "source_family": sweep_id,
                "authority": archive["authority"],
                "district": district,
                "vehicle": archive["vehicle"],
                "endpoint": endpoint,
                "earliest_available": None,
                "latest_available": None,
                "retrieved_on": retrieved_on,
                "coverage_status": "present",
                "sweep_status": "enumerated",
                "records_matched": records_matched,
                "scope_start": sample_start,
                "scope_end": sample_end,
                "notes": notes,
            },
        )
        return FamilyOutcome(
            sweep_id, "present", "enumerated", records_matched, hit_count, notes, tuple(errors)
        )

    for archive in archives:
        sid = archive["sweep_id"]
        if sid == "S3":
            districts = list(archive.get("districts") or ["D8-D13"])
            parts: list[FamilyOutcome] = []
            # One national listing covers both registered districts.
            parts.append(_listing_family("S3", archive, district="D8-D13"))
            outcomes["S3"] = parts[0]
            del districts
        elif sid in {"S5", "S6", "S7"}:
            outcomes[sid] = _listing_family(sid, archive, district="national")
        elif sid == "S8":
            _write_coverage(
                coverage_dir / "S8_port_notices.yaml",
                {
                    "schema_version": "0.2",
                    "record_kind": "source_coverage",
                    "source_family": "S8",
                    "authority": archive["authority"],
                    "district": "census_A_nodes",
                    "vehicle": archive["vehicle"],
                    "endpoint": None,
                    "earliest_available": None,
                    "latest_available": None,
                    "retrieved_on": retrieved_on,
                    "coverage_status": "unknown",
                    "sweep_status": "not_attempted",
                    "records_matched": None,
                    "scope_start": None,
                    "scope_end": None,
                    "notes": (
                        "No verified notice URL in ratified v2 config "
                        f"(nodes={archive.get('nodes')!r}). UNKNOWN, not zero."
                    ),
                },
            )
            outcomes["S8"] = FamilyOutcome(
                "S8", "unknown", "not_attempted", None, 0,
                "no verified notice URL", (),
            )
        elif sid == "S4":
            endpoints = list(archive["endpoints"])
            expected = {endpoints[0]: S4_ATLANTIC_SHA256, endpoints[1]: S4_PACIFIC_SHA256}
            positions: list[tuple[str, str, float, float]] = []
            errors: list[str] = []
            fetched = 0
            for url in endpoints:
                ok, raw, ctype, err = _fetch(url, timeout=120)
                if not ok or raw is None:
                    errors.append(f"{url}: {err}")
                    continue
                digest = _sha256(raw)
                if digest != expected[url]:
                    errors.append(f"{url}: digest {digest} != {expected[url]}")
                    continue
                fetched += 1
                cid = "S4-hurdat-" + _sha256(url.encode())[:12]
                rec = capture_candidate_evidence(
                    sweep_id="S4",
                    candidate_id=cid,
                    raw_bytes=raw,
                    source_reference=url,
                    sweeps_subdir=sweeps_subdir,
                    data_root_path=data_root,
                    retrieved_on=_iso_utc_now(),
                    original_filename=url.rsplit("/", 1)[-1],
                    content_type=ctype,
                )
                positions.extend(
                    parse_hurdat2_positions(
                        raw, sample_start=sample_start, sample_end=sample_end
                    )
                )
                del rec
            if fetched != 2:
                _write_coverage(
                    coverage_dir / "S4_hurdat2.yaml",
                    {
                        "schema_version": "0.2",
                        "record_kind": "source_coverage",
                        "source_family": "S4",
                        "authority": archive["authority"],
                        "district": "NHC",
                        "vehicle": archive["vehicle"],
                        "endpoint": endpoints[0],
                        "earliest_available": None,
                        "latest_available": None,
                        "retrieved_on": retrieved_on,
                        "coverage_status": "unknown",
                        "sweep_status": "not_attempted",
                        "records_matched": None,
                        "scope_start": None,
                        "scope_end": None,
                        "notes": "HURDAT2 fetch/digest failed; UNKNOWN not zero. "
                        + "; ".join(errors),
                    },
                )
                outcomes["S4"] = FamilyOutcome(
                    "S4", "unknown", "not_attempted", None, 0,
                    "; ".join(errors), tuple(errors),
                )
            else:
                nodes = cfg["s4_node_registry"]["nodes"]
                pair_seen: set[tuple[str, str]] = set()
                s4_hits = 0
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
                            rec = capture_candidate_evidence(
                                sweep_id="S4",
                                candidate_id=cid,
                                raw_bytes=payload,
                                source_reference=src,
                                sweeps_subdir=sweeps_subdir,
                                data_root_path=data_root,
                                retrieved_on=_iso_utc_now(),
                                original_filename=f"{src}.txt",
                                content_type="text/plain",
                            )
                            new_hits.append(
                                {
                                    "sweep_id": "S4",
                                    "source_reference": src,
                                    "raw_capture_pointer": (
                                        f"{sweeps_subdir}/S4/{cid}/objects/{rec.sha256}"
                                    ),
                                    "document_date": f"{stamp[0:4]}-{stamp[4:6]}-{stamp[6:8]}",
                                    "stable_source_id": storm_id,
                                }
                            )
                            s4_hits += 1
                _write_coverage(
                    coverage_dir / "S4_hurdat2.yaml",
                    {
                        "schema_version": "0.2",
                        "record_kind": "source_coverage",
                        "source_family": "S4",
                        "authority": archive["authority"],
                        "district": "NHC",
                        "vehicle": archive["vehicle"],
                        "endpoint": endpoints[0],
                        "earliest_available": None,
                        "latest_available": None,
                        "retrieved_on": retrieved_on,
                        "coverage_status": "present",
                        "sweep_status": "enumerated",
                        "records_matched": s4_hits,
                        "scope_start": sample_start,
                        "scope_end": sample_end,
                        "notes": (
                            "POINT_ONLY Haversine NM-sphere, radius_m=185200 inclusive, "
                            f"sample-period positions={len(positions)}, "
                            f"storm-node pairs within 100NM={s4_hits}. "
                            "No interpolation. Digest-verified HURDAT2 bytes."
                        ),
                    },
                )
                outcomes["S4"] = FamilyOutcome(
                    "S4", "present", "enumerated", s4_hits, s4_hits,
                    f"positions={len(positions)}", tuple(errors),
                )

    s1_hits = _s1_hits_from_repo(root)
    if not new_hits:
        new_hits.extend(_s4_hits_from_captures(data_root, sweeps_subdir))
    all_hits = s1_hits + new_hits
    families = sorted({h["sweep_id"] for h in all_hits})
    attest = {f: True for f in families}
    if persist_d5:
        _replace_s1_only_intermediate(root)
    d5 = build_authorized_d5_candidate_universe(
        repo_root=root,
        hits=all_hits,
        required_sweep_families=families,
        family_completion_attestations=attest,
        persist=persist_d5,
        frozen_at=None,
    )
    return {
        "provenance": provenance.to_dict(),
        "outcomes": {k: vars(v) for k, v in outcomes.items()},
        "new_hits": len(new_hits),
        "s1_hits": len(s1_hits),
        "d5": {
            "candidate_count": d5.manifest.candidate_count,
            "candidate_universe_version": d5.manifest.candidate_universe_version,
            "hit_set_digest": d5.manifest.hit_set_digest,
            "candidates_digest": d5.manifest.candidates_digest,
            "required_sweep_families": list(d5.manifest.required_sweep_families),
        },
    }


def rebuild_complete_d5(
    repo_root: Path | None = None,
    data_root: Path | None = None,
) -> dict[str, Any]:
    """Rebuild D5 from existing S1 table hits plus captured S4 proximity hits."""
    root = repo_root if repo_root is not None else REPO_ROOT
    provenance = assert_sweep_authorized(root)
    cfg = load_prereg_rules(root)
    if data_root is None:
        env = os.environ.get("GRAIN_DATA_ROOT")
        if not env:
            raise V2FamilyExecutionError("GRAIN_DATA_ROOT unset")
        data_root = Path(env)
    sweeps_subdir = cfg["capture"]["sweeps_subdir"]
    s1_hits = _s1_hits_from_repo(root)
    s4_hits = _s4_hits_from_captures(data_root, sweeps_subdir)
    all_hits = s1_hits + s4_hits
    families = sorted({h["sweep_id"] for h in all_hits})
    _replace_s1_only_intermediate(root)
    d5 = build_authorized_d5_candidate_universe(
        repo_root=root,
        hits=all_hits,
        required_sweep_families=families,
        family_completion_attestations={f: True for f in families},
        persist=True,
        frozen_at=None,
    )
    return {
        "provenance": provenance.to_dict(),
        "s1_hits": len(s1_hits),
        "s4_hits": len(s4_hits),
        "d5": {
            "candidate_count": d5.manifest.candidate_count,
            "candidate_universe_version": d5.manifest.candidate_universe_version,
            "hit_set_digest": d5.manifest.hit_set_digest,
            "candidates_digest": d5.manifest.candidates_digest,
            "required_sweep_families": list(d5.manifest.required_sweep_families),
        },
    }


def main() -> None:
    result = execute_v2_families()
    print(yaml.safe_dump(result, sort_keys=False))


if __name__ == "__main__":
    main()
