"""Fail-closed normalization for USACE NTNI positive-evidence-only S1 sources.

This module performs no networking, candidate minting, capture persistence, or
absence inference.  Raw source bytes must be captured by the separately
governed D6 machinery before a caller uses normalized text in a live sweep.

The registered NTNI JSON surface lists active notices and links to the source
notice.  ``full_text`` is a project normalization field produced from captured
NTNI HTML; it is not asserted to be a source-native JSON field.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from html.parser import HTMLParser
from typing import Any
from urllib.parse import urlparse

NTNI_AUTHORITY = "U.S. Army Corps of Engineers"
NTNI_DISTRICTS: tuple[tuple[str, str], ...] = (
    ("MVP", "St. Paul District"),
    ("MVR", "Rock Island District"),
    ("MVS", "St. Louis District"),
    ("MVM", "Memphis District"),
    ("MVK", "Vicksburg District"),
    ("MVN", "New Orleans District"),
    ("LRL", "Louisville District"),
    ("LRH", "Huntington District"),
    ("LRP", "Pittsburgh District"),
    ("LRN", "Nashville District"),
)
NTNI_VEHICLE = "NTNI active notices by district JSON with linked HTML notice"
NTNI_ENDPOINT_TEMPLATE = (
    "https://ndc.ops.usace.army.mil/ords/ntni/json_data/"
    "notices_by_district/{district_code}"
)
NTNI_ITEM_FIELDS = frozenset(
    {"controlnumber", "noticeno", "issuedate", "begindate", "waterways", "noticelink"}
)

_ALLOWED_LISTING_TOP_LEVEL = frozenset(
    {"items", "hasMore", "limit", "offset", "count", "links"}
)
_CHARSET_RE = re.compile(r"charset\s*=\s*[\"']?([^;\s\"']+)", re.IGNORECASE)
_WS_RE = re.compile(r"\s+")


class NtniNormalizationError(ValueError):
    """NTNI bytes or listing metadata do not satisfy the frozen contract."""


@dataclass(frozen=True)
class NtniNoticeReference:
    """Source-native reference from the documented active-notice JSON API."""

    controlnumber: str
    noticeno: str
    issuedate: str
    begindate: str
    waterways: str
    noticelink: str


def district_endpoint(district_code: str) -> str:
    """Return the exact registered active-notice endpoint for a district code."""
    allowed = {code for code, _ in NTNI_DISTRICTS}
    if district_code not in allowed:
        raise NtniNormalizationError(
            f"district_code={district_code!r} is outside the frozen D3 universe"
        )
    return NTNI_ENDPOINT_TEMPLATE.format(district_code=district_code)


def _required_text(value: Any, *, field: str) -> str:
    if isinstance(value, bool) or not isinstance(value, (str, int)):
        raise NtniNormalizationError(f"{field} must be source text or integer")
    text = str(value)
    if not text or text != text.strip():
        raise NtniNormalizationError(f"{field} must be nonempty and trimmed")
    return text


def _require_ntni_link(value: Any, *, field: str) -> str:
    link = _required_text(value, field=field)
    parsed = urlparse(link)
    if parsed.scheme != "https" or parsed.hostname != "ndc.ops.usace.army.mil":
        raise NtniNormalizationError(
            f"{field} must be an https link on ndc.ops.usace.army.mil"
        )
    if not parsed.path.startswith("/ords/ntni/print_nav_notice"):
        raise NtniNormalizationError(f"{field} is not an NTNI print notice link")
    return link


def parse_active_notice_listing(raw_json: bytes) -> tuple[NtniNoticeReference, ...]:
    """Validate a captured NTNI active-notice listing without inferring coverage."""
    if not isinstance(raw_json, bytes):
        raise NtniNormalizationError("raw_json must be bytes")
    try:
        payload = json.loads(raw_json.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise NtniNormalizationError(f"NTNI listing is not valid UTF-8 JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise NtniNormalizationError("NTNI listing must be a JSON object")
    unknown_top = set(payload) - _ALLOWED_LISTING_TOP_LEVEL
    if unknown_top:
        raise NtniNormalizationError(
            f"NTNI listing has unknown top-level fields {sorted(unknown_top)}"
        )
    items = payload.get("items")
    if not isinstance(items, list):
        raise NtniNormalizationError("NTNI listing items must be a list")

    out: list[NtniNoticeReference] = []
    seen: set[str] = set()
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            raise NtniNormalizationError(f"items[{index}] must be an object")
        fields = set(item)
        if fields != NTNI_ITEM_FIELDS:
            raise NtniNormalizationError(
                f"items[{index}] fields {sorted(fields)} do not equal documented "
                f"fields {sorted(NTNI_ITEM_FIELDS)}"
            )
        controlnumber = _required_text(
            item["controlnumber"], field=f"items[{index}].controlnumber"
        )
        if controlnumber in seen:
            raise NtniNormalizationError(
                f"duplicate source-native controlnumber {controlnumber!r}"
            )
        seen.add(controlnumber)
        out.append(
            NtniNoticeReference(
                controlnumber=controlnumber,
                noticeno=_required_text(item["noticeno"], field=f"items[{index}].noticeno"),
                issuedate=_required_text(
                    item["issuedate"], field=f"items[{index}].issuedate"
                ),
                begindate=_required_text(
                    item["begindate"], field=f"items[{index}].begindate"
                ),
                waterways=_required_text(
                    item["waterways"], field=f"items[{index}].waterways"
                ),
                noticelink=_require_ntni_link(
                    item["noticelink"], field=f"items[{index}].noticelink"
                ),
            )
        )
    return tuple(out)


class _VisibleTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self._suppressed_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.casefold() in {"script", "style", "noscript", "template"}:
            self._suppressed_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag.casefold() in {"script", "style", "noscript", "template"}:
            self._suppressed_depth = max(0, self._suppressed_depth - 1)

    def handle_data(self, data: str) -> None:
        if self._suppressed_depth == 0:
            self.parts.append(data)


def normalize_full_text(raw_html: bytes, *, content_type: str) -> str:
    """Normalize captured NTNI HTML into the frozen local ``full_text`` field."""
    if not isinstance(raw_html, bytes):
        raise NtniNormalizationError("raw_html must be bytes")
    if not isinstance(content_type, str) or not content_type.strip():
        raise NtniNormalizationError("content_type must be a nonempty string")
    media_type = content_type.split(";", 1)[0].strip().casefold()
    if media_type != "text/html":
        raise NtniNormalizationError(
            f"unsupported content_type {content_type!r}; only captured NTNI HTML is registered"
        )
    match = _CHARSET_RE.search(content_type)
    charset = match.group(1).casefold() if match else "utf-8"
    if charset not in {"utf-8", "utf8", "us-ascii", "ascii"}:
        raise NtniNormalizationError(f"unsupported declared charset {charset!r}")
    try:
        decoded = raw_html.decode("ascii" if charset in {"us-ascii", "ascii"} else "utf-8")
    except UnicodeDecodeError as exc:
        raise NtniNormalizationError(f"NTNI HTML decode failed: {exc}") from exc

    parser = _VisibleTextParser()
    try:
        parser.feed(decoded)
        parser.close()
    except Exception as exc:  # HTMLParser errors vary by Python patch release.
        raise NtniNormalizationError(f"NTNI HTML parse failed: {exc}") from exc
    normalized = _WS_RE.sub(" ", " ".join(parser.parts)).strip()
    if not normalized:
        raise NtniNormalizationError("NTNI HTML produced empty normalized full_text")
    return normalized
