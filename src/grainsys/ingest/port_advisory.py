"""Fail-closed normalization for port advisory positive-evidence-only S8 sources.

This module performs no networking, candidate minting, capture persistence, or
absence inference.  Raw source bytes must be captured by the separately
governed D6 machinery before a caller uses normalized text in a live sweep.

The S8 source family covers port authority and terminal operator notices where
official archives exist.  Per the instruction:
- Verify port/advisory archives for currently official-source-supported S4 nodes
- Do not depend on TEMCO Kalama corporate-only evidence
- Positive-evidence-only semantics apply

This is the most heterogeneous source family - may require multiple adapters
per port/terminal archive format.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from typing import Any

# Port authorities with documented public advisory archives
# These are the official-source-supported nodes for S4 hurricane proximity analysis
# Per instruction: do not depend on corporate-only evidence (e.g., TEMCO Kalama)

PORT_AUTHORITIES: tuple[tuple[str, str, str, str], ...] = (
    # (port_code, port_name, navigation_basin, archive_status)
    # Gulf ports - primary grain export corridor
    ("NOLA", "Port of New Orleans", "lower_mississippi", "official_archive"),
    ("SBPT", "Port of South Louisiana", "lower_mississippi", "official_archive"),
    ("HST", "Port of Houston", "gulf_texas", "official_archive"),
    ("GVS", "Port of Galveston", "gulf_texas", "official_archive"),
    ("CRP", "Port of Corpus Christi", "gulf_texas", "official_archive"),
    # PNW ports - Columbia-Snake corridor
    ("PDX", "Port of Portland", "columbia_snake", "official_archive"),
    ("SEA", "Port of Seattle", "puget_sound", "official_archive"),
    ("TAC", "Port of Tacoma", "puget_sound", "official_archive"),
    ("VAN", "Port of Vancouver USA", "columbia_snake", "official_archive"),
    ("LON", "Port of Longview", "columbia_snake", "official_archive"),
    # Great Lakes - secondary grain corridor
    ("DUL", "Port of Duluth-Superior", "great_lakes", "official_archive"),
    ("TOL", "Port of Toledo", "great_lakes", "official_archive"),
)

# Terminal operators with public advisory capability
# Note: TEMCO Kalama excluded per instruction (corporate-only evidence)
# Only include terminals with official/public archive access
TERMINAL_OPERATORS: tuple[tuple[str, str, str, str], ...] = (
    # (terminal_code, terminal_name, port, archive_status)
    # Gulf export terminals
    ("ADM_NOLA", "ADM Ama Terminal", "NOLA", "public_notices"),
    ("CGB_NOLA", "CGB/Zen-Noh Convent", "SBPT", "public_notices"),
    ("BUNGE_NOLA", "Bunge Destrehan", "SBPT", "public_notices"),
    # PNW export terminals
    ("EGT_LON", "EGT Longview", "LON", "public_notices"),
    ("UGG_PDX", "United Grain Portland", "PDX", "public_notices"),
    # Excluded: TEMCO Kalama - corporate-only evidence not official archive
    # ("TEMCO_KAL", "TEMCO Kalama", "LON", "corporate_only"),  # EXCLUDED
)

# Archive endpoint patterns (official sources only)
PORT_ARCHIVE_ENDPOINTS: dict[str, str] = {
    "NOLA": "https://portnola.com/notices",
    "HST": "https://porthouston.com/trade-development/alerts-advisories/",
    "PDX": "https://www.portofportland.com/Marine/Marine-Notices",
}

# Registered year range for sample period coverage
PORT_SAMPLE_START_YEAR = 2010
PORT_SAMPLE_END_YEAR = 2024

_WS_RE = re.compile(r"\s+")


class PortAdvisoryNormalizationError(ValueError):
    """Port advisory bytes or data do not satisfy the frozen contract."""


@dataclass(frozen=True)
class PortReference:
    """Reference to a port authority."""

    port_code: str
    port_name: str
    navigation_basin: str
    archive_status: str


@dataclass(frozen=True)
class TerminalReference:
    """Reference to a terminal operator."""

    terminal_code: str
    terminal_name: str
    port: str
    archive_status: str


@dataclass(frozen=True)
class PortAdvisoryRecord:
    """A port advisory or notice from an official archive."""

    port_code: str
    advisory_id: str
    effective_date: date
    expiration_date: date | None
    advisory_type: str
    title: str
    description: str
    affected_facilities: tuple[str, ...]
    source_url: str


@dataclass(frozen=True)
class TerminalNoticeRecord:
    """A terminal operator notice."""

    terminal_code: str
    notice_id: str
    effective_date: date
    notice_type: str
    title: str
    description: str
    source_url: str


def get_official_archive_ports() -> tuple[PortReference, ...]:
    """Return ports with official public advisory archives.
    
    Excludes ports with corporate-only evidence.
    """
    return tuple(
        PortReference(
            port_code=code,
            port_name=name,
            navigation_basin=basin,
            archive_status=status,
        )
        for code, name, basin, status in PORT_AUTHORITIES
        if status == "official_archive"
    )


def get_public_notice_terminals() -> tuple[TerminalReference, ...]:
    """Return terminals with public notice capability.
    
    Excludes terminals with corporate-only evidence (e.g., TEMCO Kalama).
    """
    return tuple(
        TerminalReference(
            terminal_code=code,
            terminal_name=name,
            port=port,
            archive_status=status,
        )
        for code, name, port, status in TERMINAL_OPERATORS
        if status == "public_notices"
    )


def port_archive_endpoint(port_code: str) -> str | None:
    """Return the known archive endpoint for a port, if any.
    
    Returns None if no documented endpoint exists.
    """
    return PORT_ARCHIVE_ENDPOINTS.get(port_code)


def _required_text(value: Any, *, field: str) -> str:
    if isinstance(value, bool) or not isinstance(value, (str, int)):
        raise PortAdvisoryNormalizationError(f"{field} must be source text or integer")
    text = str(value)
    if not text or text != text.strip():
        raise PortAdvisoryNormalizationError(f"{field} must be nonempty and trimmed")
    return text


def is_grain_corridor_port(port_code: str) -> bool:
    """Check if a port is on a registered grain export corridor."""
    for code, _, basin, _ in PORT_AUTHORITIES:
        if code == port_code:
            return basin in {
                "lower_mississippi",
                "columbia_snake",
                "gulf_texas",
                "great_lakes",
            }
    return False


def is_official_source_supported(port_code: str) -> bool:
    """Check if a port has official archive support.
    
    Per instruction: verify official-source-supported S4 nodes.
    """
    for code, _, _, status in PORT_AUTHORITIES:
        if code == port_code:
            return status == "official_archive"
    return False


def enumerate_port_advisories(
    advisory_records: list[PortAdvisoryRecord],
) -> tuple[PortAdvisoryRecord, ...]:
    """Enumerate port advisories for officially-supported ports.
    
    Filters to only include advisories from ports with official archives.
    Positive-evidence-only semantics apply.
    """
    out: list[PortAdvisoryRecord] = []

    for record in advisory_records:
        if is_official_source_supported(record.port_code):
            out.append(record)

    return tuple(out)


def get_registered_years() -> tuple[int, ...]:
    """Return the tuple of years covered by the registered sample period."""
    return tuple(range(PORT_SAMPLE_START_YEAR, PORT_SAMPLE_END_YEAR + 1))


def validate_s4_node_coverage(s4_nodes: list[str]) -> dict[str, bool]:
    """Validate which S4 export nodes have official archive support.
    
    Returns a dict mapping node to whether it has official source support.
    Use this to audit S4 node evidence quality per instruction:
    "verify official port/advisory archives for currently official-source-supported S4 nodes"
    """
    result: dict[str, bool] = {}
    
    for node in s4_nodes:
        # Check if node matches a port code
        if is_official_source_supported(node):
            result[node] = True
            continue
        
        # Check if node matches a terminal code
        for term_code, _, _port, status in TERMINAL_OPERATORS:
            if term_code == node or node in term_code:
                result[node] = status == "public_notices"
                break
        else:
            # No match - no official source support
            result[node] = False
    
    return result


def normalize_port_notice(
    raw_content: bytes,
    *,
    content_type: str,
    port_code: str,
) -> str:
    """Normalize a captured port advisory into text for keyword search.
    
    Port notices come in various formats (HTML, PDF, plain text).
    This function handles HTML; PDF extraction deferred to sweep layer.
    """
    if not isinstance(raw_content, bytes):
        raise PortAdvisoryNormalizationError("raw_content must be bytes")
    if not isinstance(content_type, str) or not content_type.strip():
        raise PortAdvisoryNormalizationError("content_type must be a nonempty string")
    if not is_official_source_supported(port_code):
        raise PortAdvisoryNormalizationError(
            f"port_code={port_code!r} is not official-source-supported"
        )

    media_type = content_type.split(";", 1)[0].strip().casefold()

    if media_type == "text/html":
        try:
            decoded = raw_content.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise PortAdvisoryNormalizationError(f"HTML decode failed: {exc}") from exc
        # Simple text extraction (more sophisticated parsing at sweep layer)
        normalized = _WS_RE.sub(" ", decoded).strip()
        if not normalized:
            raise PortAdvisoryNormalizationError(
                "Port notice produced empty normalized text"
            )
        return normalized
    elif media_type == "application/pdf":
        if not raw_content.startswith(b"%PDF-"):
            raise PortAdvisoryNormalizationError(
                "raw_content does not start with PDF magic bytes"
            )
        raise PortAdvisoryNormalizationError(
            "PDF text extraction deferred to sweep execution layer"
        )
    elif media_type == "text/plain":
        try:
            decoded = raw_content.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise PortAdvisoryNormalizationError(f"Text decode failed: {exc}") from exc
        normalized = _WS_RE.sub(" ", decoded).strip()
        if not normalized:
            raise PortAdvisoryNormalizationError(
                "Port notice produced empty normalized text"
            )
        return normalized
    else:
        raise PortAdvisoryNormalizationError(
            f"unsupported content_type {content_type!r}"
        )
