"""Fail-closed preregistration ratification / execution guard (N3).

A live ``prereg_rules.yaml`` is **not** sufficient to authorize a sweep.

Authorization requires ALL of:

1. Live config identifies its governing ADR (repo-relative load-bearing path)
2. Governing ADR status is ``accepted``
3. Every load-bearing ``docs/decisions/*.md`` ADR status is ``accepted``
4. An authorizing **chain** tag exists: live auth selects the newest valid
   tag among ``prereg-rules-v2`` (preferred) and ``prereg-rules-v1``
   (historical S1-era) whose tagged commit is an ancestor of HEAD
5. The v2 tagged commit must itself descend from v1
6. Tagged commit contains a ratification manifest with the config digest
7. Current live config digest matches the ratified digest
8. Executing commit is a **descendant** of the selected tagged commit
9. Manifest also binds digests of load-bearing interpretation files
10. Manifest binds append-only RULINGS section digests (prefix-stable) with
    canonical path ``research/episodes/RULINGS.md``
11. Undecidable conditions ⇒ **block**

v2 supersedes v1 for sweeps that require v2-added source families (S2–S8).
v1 remains historically valid when HEAD descends from ``prereg-rules-v1``
and live bytes match that tagged manifest. Config/manifest bytes cannot
self-select an unauthorized v2. UNKNOWN is never treated as zero.
The guard does not read unauthorized outcomes, candidates, or captures.

Manifest **build** additionally requires a fresh normalized checkout: the live
prereg config and every load-bearing working-tree file must match its committed
HEAD blob byte-for-byte (dirty trees and CRLF drift fail closed).

No permanent tag is created by this module. Tests use isolated temporary repos.

ADR-0004 is deliberately **not** load-bearing on this branch (file absent until
PR #6 merges). It must be added to ``LOAD_BEARING_RELATIVE_PATHS`` before a
real authorizing tag that includes it.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import yaml

from grainsys.discovery.config import DiscoveryConfigError, load_prereg_rules, prereg_rules_path

PREREG_TAG_V1 = "prereg-rules-v1"
PREREG_TAG_V2 = "prereg-rules-v2"
PREREG_TAG = PREREG_TAG_V1  # historical alias; v2 is preferred when both apply
ALLOWED_PREREG_TAGS = frozenset({PREREG_TAG_V1, PREREG_TAG_V2})
MANIFEST_RELATIVE = Path("config") / "discovery" / "prereg_ratification_manifest.yaml"
RULINGS_RELATIVE = Path("research") / "episodes" / "RULINGS.md"
RULINGS_PATH_CANONICAL = RULINGS_RELATIVE.as_posix()

LOAD_BEARING_RELATIVE_PATHS: tuple[str, ...] = (
    "src/grainsys/discovery/config.py",
    "src/grainsys/discovery/sweep.py",
    "src/grainsys/discovery/candidates.py",
    "src/grainsys/discovery/coverage.py",
    "src/grainsys/discovery/governance.py",
    "src/grainsys/discovery/archive_listing.py",
    "src/grainsys/discovery/capture.py",
    "src/grainsys/ingest/ntni.py",
    "src/grainsys/ingest/uscg_msib.py",
    "src/grainsys/ingest/ams_gtr.py",
    "src/grainsys/ingest/usace_lpms.py",
    "src/grainsys/ingest/stb_dockets.py",
    "src/grainsys/ingest/port_advisory.py",
    "src/grainsys/episodes.py",
    "research/episodes/EPISODE_PROTOCOL.md",
    "research/episodes/ADMISSION_CHECKLIST.md",
    "research/episodes/episode_schema.yaml",
    "research/episodes/discovery/candidates/_schema.yaml",
    "docs/decisions/0002-episode-preregistration.md",
    "docs/decisions/0003-phase0-prereg-hardening.md",
    "docs/decisions/0005-source-handling-and-vintage-rules.md",
    "docs/decisions/0015-d3-d4-positive-only-s1.md",
)

LOAD_BEARING_ADR_RELATIVE_PATHS: tuple[str, ...] = tuple(
    p
    for p in LOAD_BEARING_RELATIVE_PATHS
    if p.startswith("docs/decisions/") and p.endswith(".md")
)

MANIFEST_TOP_LEVEL_KEYS = frozenset(
    {
        "governing_adr",
        "prereg_config_digest",
        "interpretation_digests",
        "rulings_binding",
    }
)

_RULING_HEADING_RE = re.compile(
    r"^###\s+\d{4}-\d{2}-\d{2}\s+·\s+(R-\d{3})\s+·\s+\S.*$"
)
_RULING_ID_RE = re.compile(r"^R-\d{3}$")
_SHA256_HEX_RE = re.compile(r"^[0-9a-f]{64}$")
_COMMIT_SHA_RE = re.compile(r"^[0-9a-f]{40}$")

# Filename used by the existing ADR-0004 tripwire. Do not invent ADR-0004 content.
# Add this path to LOAD_BEARING_RELATIVE_PATHS only when the file exists, and
# before the real prereg-rules-v1 tag.
DEFERRED_ADR0004_RELATIVE = "docs/decisions/0004-phase0-inference-rules.md"


class RatificationError(RuntimeError):
    """Sweep execution is blocked — undecidable or failed ratification check."""


@dataclass(frozen=True)
class SweepProvenance:
    """Stamp for future Phase-1 rows / capture manifests (no live rows here)."""

    prereg_tag: str
    prereg_config_digest: str
    execution_commit_sha: str
    governing_adr: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RulingSection:
    ruling_id: str
    body: str

    @property
    def digest(self) -> str:
        return sha256_bytes(self.body.encode("utf-8"))


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def require_full_commit_sha(value: Any, *, field: str) -> str:
    """Require an actual lowercase 40-hex commit SHA — never coerce."""
    if not isinstance(value, str):
        raise RatificationError(
            f"{field} must be a full lowercase 40-hex commit SHA "
            f"(got {type(value).__name__}); refuse coercion"
        )
    if not _COMMIT_SHA_RE.fullmatch(value):
        raise RatificationError(
            f"{field} must be a full lowercase 40-hex commit SHA (got {value!r}); block"
        )
    return value


def assert_deferred_adr0004_policy(repo_root: Path) -> None:
    """Keep ADR-0004 out of the load-bearing set until the file exists.

    Pre-merge / pre-tag stop: if the file appears, it must be added to
    ``LOAD_BEARING_RELATIVE_PATHS`` before ``prereg-rules-v1``. Do not invent
    the ADR.
    """
    path = repo_root / DEFERRED_ADR0004_RELATIVE
    listed = DEFERRED_ADR0004_RELATIVE in LOAD_BEARING_RELATIVE_PATHS
    if path.is_file() and not listed:
        raise RatificationError(
            "ADR-0004 is present but not load-bearing; add it to "
            "LOAD_BEARING_RELATIVE_PATHS before an authorizing prereg tag; block"
        )
    if listed and not path.is_file():
        raise RatificationError(
            "ADR-0004 is listed as load-bearing but the file is absent; block"
        )


def require_sha256_hex_digest(value: Any, *, field: str) -> str:
    """Require an actual lowercase hex SHA-256 digest string — never coerce."""
    if not isinstance(value, str):
        raise RatificationError(
            f"{field} must be a lowercase hex sha256 string "
            f"(got {type(value).__name__}); refuse coercion"
        )
    if not _SHA256_HEX_RE.fullmatch(value):
        raise RatificationError(
            f"{field} must match ^[0-9a-f]{{64}}$ (got {value!r}); block"
        )
    return value


def _git(
    repo_root: Path,
    *args: str,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            ["git", *args],
            cwd=repo_root,
            check=check,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as exc:
        raise RatificationError("git unavailable; undecidable ⇒ block sweep") from exc
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or exc.stdout or "").strip()
        raise RatificationError(
            f"git command failed ({' '.join(args)}): {detail or 'undecidable'}; block"
        ) from exc


def _git_bytes(
    repo_root: Path,
    *args: str,
    check: bool = True,
) -> subprocess.CompletedProcess[bytes]:
    try:
        return subprocess.run(
            ["git", *args],
            cwd=repo_root,
            check=check,
            capture_output=True,
        )
    except FileNotFoundError as exc:
        raise RatificationError("git unavailable; undecidable ⇒ block sweep") from exc
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or exc.stdout or b"").decode("utf-8", errors="replace").strip()
        raise RatificationError(
            f"git command failed ({' '.join(args)}): {detail or 'undecidable'}; block"
        ) from exc


def git_show_blob_bytes(repo_root: Path, *, rev: str, relative_path: str) -> bytes:
    """Byte-safe ``git show rev:path`` (no text decoding / newline munging)."""
    proc = _git_bytes(repo_root, "show", f"{rev}:{relative_path}")
    return proc.stdout


def assert_paths_match_head_blobs(
    repo_root: Path,
    relative_paths: Sequence[str],
    *,
    rev: str = "HEAD",
) -> None:
    """Fail closed unless each working-tree file matches its committed blob bytes.

    Requires a fresh normalized checkout (LF, no dirty / CRLF drift).
    """
    try:
        _git(repo_root, "rev-parse", rev)
    except RatificationError as exc:
        raise RatificationError(
            f"cannot resolve {rev} for byte-identity check; "
            "fresh normalized checkout required; block"
        ) from exc

    for rel in relative_paths:
        path = repo_root / rel
        if not path.is_file():
            raise RatificationError(
                f"working-tree file missing for HEAD byte check: {rel}; "
                "fresh normalized checkout required; block"
            )
        live = path.read_bytes()
        try:
            blob = git_show_blob_bytes(repo_root, rev=rev, relative_path=rel)
        except RatificationError as exc:
            raise RatificationError(
                f"{rel} absent from {rev}; fresh normalized checkout required; block"
            ) from exc
        if live != blob:
            raise RatificationError(
                f"working tree drift vs {rev} for {rel} (dirty or CRLF); "
                "fresh normalized checkout required; block"
            )


def parse_adr_status(adr_path: Path) -> str:
    try:
        text = adr_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise RatificationError(f"ADR unreadable ({adr_path}): {exc}; block") from exc
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.lower().startswith("- **status:**"):
            value = stripped.split(":", 1)[1].strip().lstrip("*").strip().lower()
            if not value:
                raise RatificationError(
                    f"ADR status empty in {adr_path}; undecidable ⇒ block"
                )
            return value
    raise RatificationError(f"ADR status field missing in {adr_path}; undecidable ⇒ block")


def assert_load_bearing_adrs_accepted(repo_root: Path) -> None:
    """Every load-bearing docs/decisions ADR must be status accepted."""
    for rel in LOAD_BEARING_ADR_RELATIVE_PATHS:
        path = repo_root / rel
        if not path.is_file():
            raise RatificationError(
                f"load-bearing ADR missing: {rel}; undecidable ⇒ block"
            )
        status = parse_adr_status(path)
        if status != "accepted":
            raise RatificationError(
                f"load-bearing ADR {rel} status is {status!r}, not 'accepted'; block"
            )


def canonicalize_governing_adr(repo_root: Path, governing_adr: str) -> str:
    """Return repo-relative load-bearing docs/decisions path; reject unbound paths."""
    if not isinstance(governing_adr, str) or not governing_adr.strip():
        raise RatificationError("governing_adr empty; undecidable ⇒ block")
    raw = governing_adr.strip().replace("\\", "/")
    candidate = Path(raw)
    if candidate.is_absolute():
        raise RatificationError(
            f"governing_adr must be repo-relative (got absolute {governing_adr!r}); block"
        )
    # Disallow path escape.
    parts = Path(raw).parts
    if ".." in parts:
        raise RatificationError(
            f"governing_adr must not escape the repository ({governing_adr!r}); block"
        )
    rel = Path(raw).as_posix()
    if rel not in LOAD_BEARING_ADR_RELATIVE_PATHS:
        # Allow bare filename only if it uniquely maps to a load-bearing ADR.
        name = Path(raw).name
        matches = [p for p in LOAD_BEARING_ADR_RELATIVE_PATHS if Path(p).name == name]
        if len(matches) == 1:
            rel = matches[0]
        else:
            raise RatificationError(
                f"governing_adr={governing_adr!r} is not a load-bearing "
                f"docs/decisions path; block"
            )
    path = repo_root / rel
    if not path.is_file():
        raise RatificationError(f"governing ADR not found: {rel!r}; block")
    return rel


def resolve_governing_adr_path(repo_root: Path, governing_adr: str) -> Path:
    """Resolve ADR path from config value to an on-disk load-bearing ADR file."""
    rel = canonicalize_governing_adr(repo_root, governing_adr)
    return repo_root / rel


def build_interpretation_digests(repo_root: Path) -> dict[str, str]:
    digests: dict[str, str] = {}
    for rel in LOAD_BEARING_RELATIVE_PATHS:
        path = repo_root / rel
        if not path.is_file():
            raise RatificationError(
                f"load-bearing interpretation file missing: {rel}; undecidable ⇒ block"
            )
        digests[rel] = sha256_file(path)
    return digests


def canonicalize_ruling_section_body(raw: str) -> str:
    """Strip trailing blank CR/LF separator lines; end with exactly one LF.

    Interior content, fenced blocks, and substantive trailing spaces on content
    lines are preserved. Only blank separator lines at the section tail are
    removed so natural blank-line append and immediate-heading append remain
    prefix-stable.
    """
    lines = raw.splitlines(keepends=True)
    while lines and lines[-1].strip() == "":
        lines.pop()
    if not lines:
        return "\n"
    body = "".join(lines)
    if body.endswith("\r\n"):
        body = body[:-2]
    elif body.endswith("\n") or body.endswith("\r"):
        body = body[:-1]
    return body + "\n"


def parse_ruling_sections(text: str) -> list[RulingSection]:
    """Parse concrete R-NNN sections with a line/fence state machine.

    Headings inside fenced examples are ignored. Fenced content inside a real
    ruling body is preserved so edits change the section digest. Supports
    backtick and tilde fences. Duplicate concrete ruling IDs fail closed.
    Section bodies are canonicalized (trailing blank separators stripped;
    exactly one terminating LF).
    """
    lines = text.splitlines(keepends=True)
    fence_marker: str | None = None
    headings: list[tuple[int, str]] = []

    for i, line in enumerate(lines):
        stripped = line.strip()
        if fence_marker is None:
            if stripped.startswith("```"):
                fence_marker = "```"
                continue
            if stripped.startswith("~~~"):
                fence_marker = "~~~"
                continue
            match = _RULING_HEADING_RE.match(stripped)
            if match:
                headings.append((i, match.group(1)))
            continue
        if stripped.startswith(fence_marker):
            fence_marker = None

    if not headings:
        raise RatificationError("RULINGS.md contains no concrete R-NNN sections; block")

    ids = [rid for _, rid in headings]
    if len(ids) != len(set(ids)):
        raise RatificationError(
            f"duplicate concrete ruling IDs in RULINGS.md: "
            f"{sorted({r for r in ids if ids.count(r) > 1})}; block"
        )

    sections: list[RulingSection] = []
    for j, (start_i, rid) in enumerate(headings):
        end_i = headings[j + 1][0] if j + 1 < len(headings) else len(lines)
        raw_body = "".join(lines[start_i:end_i])
        body = canonicalize_ruling_section_body(raw_body)
        sections.append(RulingSection(ruling_id=rid, body=body))
    return sections


def _validate_rulings_binding_shape(bound: Mapping[str, Any]) -> tuple[list[str], dict[str, str]]:
    path = bound.get("path")
    if path != RULINGS_PATH_CANONICAL:
        raise RatificationError(
            f"rulings_binding.path must be exactly {RULINGS_PATH_CANONICAL!r} "
            f"(got {path!r}); block"
        )
    bound_ids = bound.get("bound_ruling_ids")
    digests = bound.get("ruling_digests")
    if not isinstance(bound_ids, list) or not bound_ids:
        raise RatificationError("rulings_binding.bound_ruling_ids missing/invalid; block")
    if not isinstance(digests, Mapping) or not digests:
        raise RatificationError("rulings_binding.ruling_digests missing/invalid; block")

    cleaned_ids: list[str] = []
    seen: set[str] = set()
    for i, rid in enumerate(bound_ids):
        if not isinstance(rid, str) or not _RULING_ID_RE.fullmatch(rid):
            raise RatificationError(
                f"rulings_binding.bound_ruling_ids[{i}] must be R-NNN string; block"
            )
        if rid in seen:
            raise RatificationError(
                f"rulings_binding.bound_ruling_ids duplicate {rid}; block"
            )
        seen.add(rid)
        cleaned_ids.append(rid)

    if set(digests.keys()) != set(cleaned_ids):
        missing = sorted(set(cleaned_ids) - set(digests.keys()))
        extra = sorted(set(digests.keys()) - set(cleaned_ids))
        raise RatificationError(
            "rulings_binding digests must match bound IDs exactly "
            f"(missing={missing}, extra={extra}); block"
        )
    cleaned_digests: dict[str, str] = {}
    for rid in cleaned_ids:
        cleaned_digests[rid] = require_sha256_hex_digest(
            digests.get(rid),
            field=f"rulings_binding.ruling_digests[{rid}]",
        )
    return cleaned_ids, cleaned_digests


def build_rulings_binding(repo_root: Path) -> dict[str, Any]:
    """Build append-only RULINGS binding (ids + digests in document order)."""
    path = repo_root / RULINGS_RELATIVE
    if not path.is_file():
        raise RatificationError(
            f"RULINGS.md missing at {RULINGS_PATH_CANONICAL}; undecidable ⇒ block"
        )
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise RatificationError(f"RULINGS.md unreadable: {exc}; block") from exc
    sections = parse_ruling_sections(text)
    binding = {
        "path": RULINGS_PATH_CANONICAL,
        "bound_ruling_ids": [s.ruling_id for s in sections],
        "ruling_digests": {s.ruling_id: s.digest for s in sections},
    }
    _validate_rulings_binding_shape(binding)
    return binding


def assert_rulings_binding_holds(
    repo_root: Path,
    bound: Mapping[str, Any],
) -> None:
    """Fail closed unless bound ruling prefix exists with identical content/order."""
    if not isinstance(bound, Mapping):
        raise RatificationError("manifest rulings_binding missing/invalid; block")
    bound_ids, bound_digests = _validate_rulings_binding_shape(bound)

    current = build_rulings_binding(repo_root)
    current_ids: list[str] = list(current["bound_ruling_ids"])
    current_digests: dict[str, str] = dict(current["ruling_digests"])

    if len(current_ids) < len(bound_ids):
        raise RatificationError(
            "RULINGS bound prefix shortened/deleted; refuse (append-only)"
        )
    if current_ids[: len(bound_ids)] != list(bound_ids):
        raise RatificationError(
            "RULINGS bound prefix reordered or mutated; refuse (append-only)"
        )
    for rid in bound_ids:
        if current_digests[rid] != bound_digests[rid]:
            raise RatificationError(
                f"bound ruling {rid} content digest drift; refuse edit of frozen prefix"
            )


def validate_ratification_manifest_mapping(
    manifest: Mapping[str, Any],
    *,
    load_bearing: Sequence[str] | None = LOAD_BEARING_RELATIVE_PATHS,
) -> None:
    """Reject unknown keys and malformed digests / interpretation sets.

    When ``load_bearing`` is provided, interpretation paths must match that set
    exactly (v2 / current-era build and authorization). When ``load_bearing``
    is None, any nonempty exact path-to-digest mapping is accepted (historical
    v1 tagged manifests whose bound set is smaller than the current era).
    """
    if not isinstance(manifest, Mapping):
        raise RatificationError("manifest must be a mapping; block")
    unknown = sorted(set(manifest.keys()) - MANIFEST_TOP_LEVEL_KEYS)
    if unknown:
        raise RatificationError(
            f"manifest has unknown top-level keys {unknown}; block"
        )
    missing = sorted(MANIFEST_TOP_LEVEL_KEYS - set(manifest.keys()))
    if missing:
        raise RatificationError(f"manifest missing required keys {missing}; block")

    require_sha256_hex_digest(
        manifest["prereg_config_digest"],
        field="prereg_config_digest",
    )
    if not isinstance(manifest["governing_adr"], str) or not manifest["governing_adr"]:
        raise RatificationError("manifest governing_adr must be a nonempty string; block")

    interp = manifest["interpretation_digests"]
    if not isinstance(interp, Mapping):
        raise RatificationError("interpretation_digests must be a mapping; block")
    if not interp:
        raise RatificationError("interpretation_digests is empty; block")
    for rel, digest in interp.items():
        if not isinstance(rel, str) or not rel or rel != rel.strip() or ".." in Path(rel).parts:
            raise RatificationError(
                f"interpretation_digests has unsafe path {rel!r}; block"
            )
        require_sha256_hex_digest(
            digest,
            field=f"interpretation_digests[{rel}]",
        )
    if load_bearing is not None:
        expected = set(load_bearing)
        got = set(interp.keys())
        if got != expected:
            raise RatificationError(
                "interpretation_digests paths must match load-bearing set exactly "
                f"(missing={sorted(expected - got)}, extra={sorted(got - expected)}); block"
            )

    if not isinstance(manifest["rulings_binding"], Mapping):
        raise RatificationError("rulings_binding must be a mapping; block")
    _validate_rulings_binding_shape(manifest["rulings_binding"])


def load_ratification_manifest(
    repo_root: Path,
    *,
    at_ref: str,
    load_bearing: Sequence[str] | None = LOAD_BEARING_RELATIVE_PATHS,
) -> dict[str, Any]:
    """Load manifest from a git ref (typically a prereg-rules-vN tagged commit)."""
    try:
        proc = _git(repo_root, "show", f"{at_ref}:{MANIFEST_RELATIVE.as_posix()}")
    except RatificationError as exc:
        raise RatificationError(
            f"ratification manifest missing at {at_ref}:{MANIFEST_RELATIVE.as_posix()}; "
            "block"
        ) from exc
    try:
        data = yaml.safe_load(proc.stdout)
    except yaml.YAMLError as exc:
        raise RatificationError("manifest YAML unparseable; undecidable ⇒ block") from exc
    if not isinstance(data, dict):
        raise RatificationError("manifest must be a YAML mapping; block")
    validate_ratification_manifest_mapping(data, load_bearing=load_bearing)
    return data


def is_descendant_commit(repo_root: Path, *, head: str, ancestor: str) -> bool:
    """True iff ``head`` equals ``ancestor`` or is a descendant of it."""
    if head == ancestor:
        return True
    proc = _git(
        repo_root,
        "merge-base",
        "--is-ancestor",
        ancestor,
        head,
        check=False,
    )
    if proc.returncode == 0:
        return True
    if proc.returncode == 1:
        return False
    raise RatificationError(
        f"unable to establish ancestry between {ancestor} and {head}; undecidable ⇒ block"
    )


def _list_tags(repo_root: Path) -> set[str]:
    tag_proc = _git(repo_root, "tag", "-l")
    return {t.strip() for t in tag_proc.stdout.splitlines() if t.strip()}


def _resolve_tag_commit(repo_root: Path, tag: str) -> str:
    tagged = _git(repo_root, "rev-list", "-n", "1", tag).stdout.strip()
    if not tagged:
        raise RatificationError(f"tag {tag} could not be resolved; block")
    return tagged.lower() if re.fullmatch(r"[0-9a-fA-F]{40}", tagged) else tagged


def _authorize_against_tag(
    repo_root: Path,
    *,
    head: str,
    tag: str,
    tagged_commit: str,
    governing_adr: str,
    cfg_path: Path,
    require_current_load_bearing: bool,
) -> SweepProvenance:
    if not is_descendant_commit(repo_root, head=head, ancestor=tagged_commit):
        raise RatificationError(
            f"execution commit {head} is not a descendant of {tag} "
            f"({tagged_commit}); block"
        )

    load_bearing: Sequence[str] | None = (
        LOAD_BEARING_RELATIVE_PATHS if require_current_load_bearing else None
    )
    manifest = load_ratification_manifest(
        repo_root, at_ref=tagged_commit, load_bearing=load_bearing
    )
    ratified_digest = require_sha256_hex_digest(
        manifest.get("prereg_config_digest"),
        field="prereg_config_digest",
    )

    live_digest = sha256_file(cfg_path)
    if live_digest != ratified_digest:
        raise RatificationError(
            "live prereg config digest does not match ratified digest; block"
        )

    interp = manifest.get("interpretation_digests")
    if not isinstance(interp, dict) or not interp:
        raise RatificationError(
            "manifest missing interpretation_digests; undecidable ⇒ block"
        )
    current_interp = build_interpretation_digests(repo_root)
    bound_paths = tuple(interp.keys())
    if require_current_load_bearing:
        extra = sorted(set(bound_paths) - set(LOAD_BEARING_RELATIVE_PATHS))
        missing = sorted(set(LOAD_BEARING_RELATIVE_PATHS) - set(bound_paths))
        if extra or missing:
            raise RatificationError(
                "interpretation_digests paths must match load-bearing set exactly "
                f"(missing={missing}, extra={extra}); block"
            )
        compare_paths = LOAD_BEARING_RELATIVE_PATHS
    else:
        compare_paths = bound_paths
        unbound = sorted(set(bound_paths) - set(current_interp))
        if unbound:
            raise RatificationError(
                f"manifest has extra interpretation paths {unbound}; block"
            )

    for rel in compare_paths:
        if rel not in interp:
            raise RatificationError(
                f"manifest omits load-bearing path {rel}; block"
            )
        require_sha256_hex_digest(interp[rel], field=f"interpretation_digests[{rel}]")
        if rel not in current_interp:
            raise RatificationError(
                f"load-bearing interpretation file missing: {rel}; undecidable ⇒ block"
            )
        if interp[rel] != current_interp[rel]:
            raise RatificationError(
                f"interpretation digest drift for {rel}; block "
                "(ratified interpretation must match executing tree)"
            )

    manifest_adr = manifest.get("governing_adr")
    if manifest_adr in (None, ""):
        raise RatificationError("manifest missing governing_adr; block")
    manifest_rel = canonicalize_governing_adr(repo_root, str(manifest_adr))
    if manifest_rel != governing_adr:
        raise RatificationError(
            "manifest governing_adr does not match live config governing_adr; block"
        )

    rulings_binding = manifest.get("rulings_binding")
    if not isinstance(rulings_binding, Mapping):
        raise RatificationError("manifest missing rulings_binding; block")
    assert_rulings_binding_holds(repo_root, rulings_binding)

    return SweepProvenance(
        prereg_tag=tag,
        prereg_config_digest=live_digest,
        execution_commit_sha=head,
        governing_adr=governing_adr,
    )


def assert_sweep_authorized(
    repo_root: Path | None = None,
    *,
    execution_commit: str | None = None,
) -> SweepProvenance:
    """Fail-closed ratification gate. Does not create tags or mutate history.

    Always validates and stamps **actual HEAD**. If ``execution_commit`` is
    supplied, it must be the full lowercase 40-hex SHA of that HEAD — never a
    caller-claimed different commit. Live config and every load-bearing
    working-tree file must match the actual-HEAD blob byte-for-byte before
    those bytes are compared to the tagged manifest (restoring old ratified
    files over a drifted HEAD does not bypass).

    Prefer ``prereg-rules-v2`` when that tag exists, the tagged commit descends
    from ``prereg-rules-v1``, HEAD descends from the v2 tagged commit, and live
    bytes match the v2 tagged manifest (current load-bearing set). Otherwise
    fall back to ``prereg-rules-v1`` when HEAD descends from it and live bytes
    match that historical tagged manifest. UNKNOWN is never treated as zero.
    """
    from grainsys.discovery.config import REPO_ROOT

    root = repo_root if repo_root is not None else REPO_ROOT

    try:
        head_raw = _git(root, "rev-parse", "HEAD").stdout.strip()
    except RatificationError:
        raise
    if not re.fullmatch(r"[0-9a-fA-F]{40}", head_raw):
        raise RatificationError(
            f"HEAD is not a full 40-hex commit ({head_raw!r}); block"
        )
    head = head_raw.lower()
    if execution_commit is not None:
        claimed = require_full_commit_sha(execution_commit, field="execution_commit")
        if claimed != head:
            raise RatificationError(
                "execution_commit must equal actual HEAD; "
                "refuse caller-claimed different commit"
            )

    assert_deferred_adr0004_policy(root)

    try:
        cfg = load_prereg_rules(root)
    except DiscoveryConfigError as exc:
        raise RatificationError(f"prereg config load failed: {exc}; block") from exc

    governing_adr = canonicalize_governing_adr(root, str(cfg.get("governing_adr")))
    assert_load_bearing_adrs_accepted(root)
    adr_path = root / governing_adr
    status = parse_adr_status(adr_path)
    if status != "accepted":
        raise RatificationError(
            f"governing ADR status is {status!r}, not 'accepted'; block"
        )

    cfg_path = prereg_rules_path(root)
    cfg_rel = cfg_path.relative_to(root).as_posix()
    assert_paths_match_head_blobs(
        root,
        (cfg_rel, *LOAD_BEARING_RELATIVE_PATHS),
        rev=head,
    )

    tags = _list_tags(root)
    failures: list[RatificationError] = []

    if PREREG_TAG_V2 in tags:
        tagged_v2 = _resolve_tag_commit(root, PREREG_TAG_V2)
        try:
            if PREREG_TAG_V1 not in tags:
                raise RatificationError(
                    "prereg-rules-v2 requires ancestral prereg-rules-v1; block"
                )
            tagged_v1_for_chain = _resolve_tag_commit(root, PREREG_TAG_V1)
            if not is_descendant_commit(
                root, head=tagged_v2, ancestor=tagged_v1_for_chain
            ):
                raise RatificationError(
                    "prereg-rules-v2 is not a descendant of prereg-rules-v1; block"
                )
            return _authorize_against_tag(
                root,
                head=head,
                tag=PREREG_TAG_V2,
                tagged_commit=tagged_v2,
                governing_adr=governing_adr,
                cfg_path=cfg_path,
                require_current_load_bearing=True,
            )
        except RatificationError as exc:
            failures.append(exc)

    if PREREG_TAG_V1 in tags:
        tagged_v1 = _resolve_tag_commit(root, PREREG_TAG_V1)
        try:
            return _authorize_against_tag(
                root,
                head=head,
                tag=PREREG_TAG_V1,
                tagged_commit=tagged_v1,
                governing_adr=governing_adr,
                cfg_path=cfg_path,
                require_current_load_bearing=False,
            )
        except RatificationError as exc:
            failures.append(exc)

    if PREREG_TAG_V1 not in tags and PREREG_TAG_V2 not in tags:
        raise RatificationError(f"tag {PREREG_TAG_V1} absent; block")
    if failures:
        raise failures[0]
    raise RatificationError("prereg authorization undecidable; block")


def make_sweep_provenance(
    *,
    prereg_config_digest: str,
    execution_commit_sha: str,
    governing_adr: str,
    prereg_tag: str = PREREG_TAG,
) -> SweepProvenance:
    """Helper for future Phase-1 emitters — does not write rows."""
    if not isinstance(prereg_tag, str) or prereg_tag not in ALLOWED_PREREG_TAGS:
        raise RatificationError(
            f"prereg_tag must be one of {sorted(ALLOWED_PREREG_TAGS)}; refuse stamp"
        )
    digest = require_sha256_hex_digest(
        prereg_config_digest, field="prereg_config_digest"
    )
    sha = require_full_commit_sha(
        execution_commit_sha, field="execution_commit_sha"
    )
    if not isinstance(governing_adr, str) or not governing_adr:
        raise RatificationError("governing_adr must be a nonempty canonical string")
    if governing_adr != governing_adr.strip():
        raise RatificationError("governing_adr must be a canonical trimmed string")
    return SweepProvenance(
        prereg_tag=prereg_tag,
        prereg_config_digest=digest,
        execution_commit_sha=sha,
        governing_adr=governing_adr,
    )


def build_ratification_manifest(repo_root: Path | None = None) -> dict[str, Any]:
    """Build N3 ratification manifest mapping from repository inputs.

    Requires a fresh normalized checkout: live config + every load-bearing file
    must match its HEAD blob byte-for-byte before digests are computed.
    """
    from grainsys.discovery.config import REPO_ROOT

    root = repo_root if repo_root is not None else REPO_ROOT
    cfg_path = prereg_rules_path(root)
    if not cfg_path.is_file():
        raise RatificationError(
            f"cannot build manifest: live prereg config missing at {cfg_path}; block"
        )

    cfg_rel = cfg_path.relative_to(root).as_posix()
    assert_deferred_adr0004_policy(root)
    assert_paths_match_head_blobs(
        root,
        (cfg_rel, *LOAD_BEARING_RELATIVE_PATHS),
    )

    try:
        cfg = load_prereg_rules(root)
    except DiscoveryConfigError as exc:
        raise RatificationError(f"cannot build manifest: {exc}; block") from exc

    adr = canonicalize_governing_adr(root, str(cfg.get("governing_adr")))
    assert_load_bearing_adrs_accepted(root)

    interp = build_interpretation_digests(root)
    ordered_interp = {rel: interp[rel] for rel in LOAD_BEARING_RELATIVE_PATHS}
    rulings = build_rulings_binding(root)
    manifest = {
        "governing_adr": adr,
        "prereg_config_digest": sha256_file(cfg_path),
        "interpretation_digests": ordered_interp,
        "rulings_binding": rulings,
    }
    validate_ratification_manifest_mapping(manifest)
    return manifest


def serialize_ratification_manifest(manifest: Mapping[str, Any]) -> bytes:
    """Canonical UTF-8 JSON bytes (valid YAML) independent of insertion order."""
    validate_ratification_manifest_mapping(manifest)

    interp = manifest["interpretation_digests"]
    ordered_interp = {
        rel: require_sha256_hex_digest(
            interp[rel], field=f"interpretation_digests[{rel}]"
        )
        for rel in LOAD_BEARING_RELATIVE_PATHS
    }

    rulings = manifest["rulings_binding"]
    bound_ids, ordered_ruling_digests = _validate_rulings_binding_shape(rulings)

    payload = {
        "governing_adr": manifest["governing_adr"],
        "interpretation_digests": ordered_interp,
        "prereg_config_digest": require_sha256_hex_digest(
            manifest["prereg_config_digest"],
            field="prereg_config_digest",
        ),
        "rulings_binding": {
            "bound_ruling_ids": list(bound_ids),
            "path": RULINGS_PATH_CANONICAL,
            "ruling_digests": ordered_ruling_digests,
        },
    }
    text = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return (text + "\n").encode("utf-8")


def emit_ratification_manifest_bytes(repo_root: Path | None = None) -> bytes:
    """Deterministically emit N3 manifest content bytes (no write / no tag)."""
    return serialize_ratification_manifest(build_ratification_manifest(repo_root))
