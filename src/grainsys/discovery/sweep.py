"""Sweep enumerator interface — config-driven, fail closed, no content fetch.

Match modes (algorithm capability only — D4 terms/fields remain unset in live config):

* ``substring`` — literal substring
* ``whole_word`` — whole-word boundaries; case folding only when configured;
  no stemmer; no hidden morphological expansion; explicit variants are just
  additional configured terms
"""

from __future__ import annotations

import re
from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from grainsys.discovery.config import DiscoveryConfigError, load_prereg_rules
from grainsys.discovery.governance import RatificationError, assert_sweep_authorized


class SweepError(RuntimeError):
    """Sweep cannot proceed under current configuration / ratification."""


@dataclass(frozen=True)
class ArchiveTarget:
    sweep_id: str
    authority: str
    district: str | None
    vehicle: str
    endpoint: str | None


@dataclass(frozen=True)
class KeywordPolicy:
    terms: tuple[str, ...]
    match: str
    case_sensitive: bool
    fields: tuple[str, ...]


_WORD_BOUNDARY_LEFT = r"(?<!\w)"
_WORD_BOUNDARY_RIGHT = r"(?!\w)"


def _whole_word_match(haystack: str, term: str) -> bool:
    if not term:
        return False
    pattern = _WORD_BOUNDARY_LEFT + re.escape(term) + _WORD_BOUNDARY_RIGHT
    return re.search(pattern, haystack) is not None


class SweepEnumerator:
    """Enumerate registered archives and apply a registered keyword policy.

    This class does **not** open remote archives or download documents.
    ``from_repo`` requires the N3 ratification guard (tag + digests + ancestry).
    Unit tests of matching may construct via ``SweepEnumerator(config)`` only.
    """

    def __init__(self, config: Mapping[str, Any]) -> None:
        self._config = dict(config)
        archives = config.get("source_archives")
        if not isinstance(archives, list) or not archives:
            raise SweepError("source_archives empty; fail closed (D3).")
        built: list[ArchiveTarget] = []
        for a in archives:
            if not isinstance(a, Mapping):
                raise SweepError("source_archives entry is not a mapping; fail closed.")
            raw_district = a.get("district")
            district = str(raw_district) if raw_district is not None else None
            raw_endpoint = a.get("endpoint")
            endpoint = str(raw_endpoint) if raw_endpoint is not None else None
            built.append(
                ArchiveTarget(
                    sweep_id=str(a["sweep_id"]),
                    authority=str(a["authority"]),
                    district=district,
                    vehicle=str(a["vehicle"]),
                    endpoint=endpoint,
                )
            )
        self._archives = tuple(built)
        kp = config["keyword_policy"]
        self._keywords = KeywordPolicy(
            terms=tuple(str(t) for t in kp["terms"]),
            match=str(kp["match"]),
            case_sensitive=bool(kp["case_sensitive"]),
            fields=tuple(str(f) for f in kp["fields"]),
        )

    @classmethod
    def from_repo(cls, repo_root: Path | None = None) -> SweepEnumerator:
        """Load live config only after fail-closed ratification succeeds."""
        try:
            assert_sweep_authorized(repo_root)
        except RatificationError as exc:
            raise SweepError(f"ratification guard blocked sweep: {exc}") from exc
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
        match = self._keywords.match
        if self._keywords.case_sensitive:
            haystack = text
            terms = self._keywords.terms
        else:
            haystack = text.casefold()
            terms = tuple(t.casefold() for t in self._keywords.terms)

        if match == "substring":
            return any(term in haystack for term in terms)
        if match == "whole_word":
            return any(_whole_word_match(haystack, term) for term in terms)
        raise SweepError(
            f"keyword_policy.match={match!r} is not implemented; "
            "only explicitly coded match modes may run (no silent fallback)."
        )
