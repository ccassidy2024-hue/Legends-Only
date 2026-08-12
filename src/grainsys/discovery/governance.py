"""Fail-closed preregistration ratification / execution guard (N3).

A live ``prereg_rules.yaml`` is **not** sufficient to authorize a sweep.

Authorization requires ALL of:

1. Live config identifies its governing ADR
2. Governing ADR status is ``accepted``
3. Git tag ``prereg-rules-v1`` exists
4. Tagged commit contains a ratification manifest with the config digest
5. Current live config digest matches the ratified digest
6. Executing commit is a **descendant** of the tagged commit (mandatory)
7. Manifest also binds digests of load-bearing interpretation files
8. Undecidable conditions (git unavailable, unreadable ADR, missing manifest,
   ancestry unknown, digest mismatch) ⇒ **block**

No permanent tag is created by this module. Tests use isolated temporary repos.
"""

from __future__ import annotations

import hashlib
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import yaml

from grainsys.discovery.config import DiscoveryConfigError, load_prereg_rules, prereg_rules_path

PREREG_TAG = "prereg-rules-v1"
MANIFEST_RELATIVE = Path("config") / "discovery" / "prereg_ratification_manifest.yaml"

# Smallest explicit set of load-bearing interpretation files bound at ratification.
# Documented here and in docs/decisions/0003-phase0-prereg-hardening.md.
LOAD_BEARING_RELATIVE_PATHS: tuple[str, ...] = (
    "src/grainsys/discovery/config.py",
    "src/grainsys/discovery/sweep.py",
    "src/grainsys/discovery/candidates.py",
    "src/grainsys/discovery/coverage.py",
    "src/grainsys/discovery/governance.py",
    "research/episodes/EPISODE_PROTOCOL.md",
    "docs/decisions/0002-episode-preregistration.md",
    "docs/decisions/0003-phase0-prereg-hardening.md",
)


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


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


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


def resolve_governing_adr_path(repo_root: Path, governing_adr: str) -> Path:
    """Resolve ADR path from config value (repo-relative path or bare filename)."""
    raw = governing_adr.strip()
    if not raw:
        raise RatificationError("governing_adr empty; undecidable ⇒ block")
    candidate = Path(raw)
    if not candidate.is_absolute():
        candidate = repo_root / candidate
    if candidate.is_file():
        return candidate
    # Allow short id like "0003-phase0-prereg-hardening.md"
    alt = repo_root / "docs" / "decisions" / Path(raw).name
    if alt.is_file():
        return alt
    raise RatificationError(f"governing ADR not found: {governing_adr!r}; block")


def parse_adr_status(adr_path: Path) -> str:
    try:
        text = adr_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise RatificationError(f"ADR unreadable ({adr_path}): {exc}; block") from exc
    for line in text.splitlines():
        stripped = line.strip()
        # ADR lines look like: - **Status:** proposed
        # First ":" sits inside the bold markers; take the trailing token.
        if stripped.lower().startswith("- **status:**"):
            value = stripped.split(":", 1)[1].strip().lstrip("*").strip().lower()
            if not value:
                raise RatificationError(
                    f"ADR status empty in {adr_path}; undecidable ⇒ block"
                )
            return value
    raise RatificationError(f"ADR status field missing in {adr_path}; undecidable ⇒ block")


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


def load_ratification_manifest(repo_root: Path, *, at_ref: str) -> dict[str, Any]:
    """Load manifest from a git ref (typically the prereg-rules-v1 tagged commit)."""
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


def assert_sweep_authorized(
    repo_root: Path | None = None,
    *,
    execution_commit: str | None = None,
) -> SweepProvenance:
    """Fail-closed ratification gate. Does not create tags or mutate history."""
    from grainsys.discovery.config import REPO_ROOT

    root = repo_root if repo_root is not None else REPO_ROOT

    # Probe git early — undecidable if unavailable / not a repo.
    try:
        head_proc = _git(root, "rev-parse", "HEAD")
    except RatificationError:
        raise
    head = (execution_commit or head_proc.stdout.strip()).strip()
    if not head:
        raise RatificationError("execution commit undecidable; block")

    try:
        cfg = load_prereg_rules(root)
    except DiscoveryConfigError as exc:
        raise RatificationError(f"prereg config load failed: {exc}; block") from exc

    governing_adr = cfg.get("governing_adr")
    if governing_adr in (None, ""):
        raise RatificationError(
            "live prereg_rules.yaml must identify governing_adr; block"
        )

    adr_path = resolve_governing_adr_path(root, str(governing_adr))
    status = parse_adr_status(adr_path)
    if status != "accepted":
        raise RatificationError(
            f"governing ADR status is {status!r}, not 'accepted'; block"
        )

    tag_proc = _git(root, "tag", "-l", PREREG_TAG)
    if PREREG_TAG not in {t.strip() for t in tag_proc.stdout.splitlines()}:
        raise RatificationError(f"tag {PREREG_TAG} absent; block")

    tagged = _git(root, "rev-list", "-n", "1", PREREG_TAG).stdout.strip()
    if not tagged:
        raise RatificationError(f"tag {PREREG_TAG} could not be resolved; block")

    if not is_descendant_commit(root, head=head, ancestor=tagged):
        raise RatificationError(
            f"execution commit {head} is not a descendant of {PREREG_TAG} "
            f"({tagged}); block"
        )

    manifest = load_ratification_manifest(root, at_ref=tagged)
    ratified_digest = manifest.get("prereg_config_digest")
    if ratified_digest in (None, ""):
        raise RatificationError("manifest missing prereg_config_digest; block")

    cfg_path = prereg_rules_path(root)
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
    current_interp = build_interpretation_digests(root)
    for rel in LOAD_BEARING_RELATIVE_PATHS:
        if rel not in interp:
            raise RatificationError(
                f"manifest omits load-bearing path {rel}; block"
            )
        if interp[rel] != current_interp[rel]:
            raise RatificationError(
                f"interpretation digest drift for {rel}; block "
                "(ratified interpretation must match executing tree)"
            )

    manifest_adr = manifest.get("governing_adr")
    if manifest_adr not in (None, "") and str(manifest_adr) != str(governing_adr):
        raise RatificationError(
            "manifest governing_adr does not match live config governing_adr; block"
        )

    return SweepProvenance(
        prereg_tag=PREREG_TAG,
        prereg_config_digest=live_digest,
        execution_commit_sha=head,
        governing_adr=str(governing_adr),
    )


def make_sweep_provenance(
    *,
    prereg_config_digest: str,
    execution_commit_sha: str,
    governing_adr: str,
    prereg_tag: str = PREREG_TAG,
) -> SweepProvenance:
    """Helper for future Phase-1 emitters — does not write rows."""
    if not prereg_config_digest or not execution_commit_sha or not governing_adr:
        raise RatificationError("provenance fields incomplete; refuse stamp")
    return SweepProvenance(
        prereg_tag=prereg_tag,
        prereg_config_digest=prereg_config_digest,
        execution_commit_sha=execution_commit_sha,
        governing_adr=governing_adr,
    )
