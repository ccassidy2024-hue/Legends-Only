"""Sweep enumerator interface — config-driven, fail closed, no content fetch."""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from grainsys.discovery.config import DiscoveryConfigError, load_prereg_rules


class SweepError(RuntimeError):
    """Sweep cannot proceed under current configuration."""


@dataclass(frozen=True)
class ArchiveTarget:
    sweep_id: str
    authority: str
    district: str
    vehicle: str
    endpoint: str


@dataclass(frozen=True)
class KeywordPolicy:
    terms: tuple[str, ...]
    match: str
    case_sensitive: bool
    fields: tuple[str, ...]


class SweepEnumerator:
    """Enumerate registered archives and apply a registered keyword policy.

    This class does **not** open remote archives or download documents.
    Callers that later add network I/O must keep that outside this module until
    Phase 0 is closed; here we only expose config-backed iteration and matching.
    """

    def __init__(self, config: Mapping[str, Any]) -> None:
        self._config = dict(config)
        archives = config.get("source_archives")
        if not isinstance(archives, list) or not archives:
            raise SweepError("source_archives empty; fail closed (D3).")
        self._archives = tuple(
            ArchiveTarget(
                sweep_id=str(a["sweep_id"]),
                authority=str(a["authority"]),
                district=str(a["district"]),
                vehicle=str(a["vehicle"]),
                endpoint=str(a["endpoint"]),
            )
            for a in archives
        )
        kp = config["keyword_policy"]
        self._keywords = KeywordPolicy(
            terms=tuple(str(t) for t in kp["terms"]),
            match=str(kp["match"]),
            case_sensitive=bool(kp["case_sensitive"]),
            fields=tuple(str(f) for f in kp["fields"]),
        )

    @classmethod
    def from_repo(cls, repo_root: Path | None = None) -> SweepEnumerator:
        try:
            cfg = load_prereg_rules(repo_root)
        except DiscoveryConfigError as exc:
            raise SweepError(str(exc)) from exc
        return cls(cfg)

    @property
    def archives(self) -> tuple[ArchiveTarget, ...]:
        return self._archives

    @property
    def keyword_policy(self) -> KeywordPolicy:
        return self._keywords

    def iter_archives(self, *, sweep_id: str | None = None) -> Iterator[ArchiveTarget]:
        for target in self._archives:
            if sweep_id is None or target.sweep_id == sweep_id:
                yield target

    def text_matches_policy(self, text: str, *, field: str) -> bool:
        """Apply the registered keyword policy to a caller-supplied string.

        Does not fetch documents. ``field`` must be listed in the registered
        policy fields; otherwise fail closed.
        """
        if field not in self._keywords.fields:
            raise SweepError(
                f"field {field!r} is not in registered keyword_policy.fields; fail closed."
            )
        haystack = text if self._keywords.case_sensitive else text.casefold()
        terms = (
            self._keywords.terms
            if self._keywords.case_sensitive
            else tuple(t.casefold() for t in self._keywords.terms)
        )
        match = self._keywords.match
        if match == "substring":
            return any(term in haystack for term in terms)
        raise SweepError(
            f"keyword_policy.match={match!r} is not implemented in this scaffold; "
            "only explicitly coded match modes may run (no silent fallback)."
        )
