"""Synthetic tests for the D3/D4 positive-evidence-only NTNI adapter."""

from __future__ import annotations

import json

import pytest

from grainsys.ingest.ntni import (
    NTNI_DISTRICTS,
    NTNI_ITEM_FIELDS,
    NtniNormalizationError,
    district_endpoint,
    normalize_full_text,
    parse_active_notice_listing,
)


def _listing(**overrides) -> bytes:
    item = {
        "controlnumber": 123456,
        "noticeno": "123456-1",
        "issuedate": "01-JAN-2099",
        "begindate": "02-JAN-2099",
        "waterways": "SYNTHETIC WATERWAY",
        "noticelink": (
            "https://ndc.ops.usace.army.mil/ords/ntni/"
            "print_nav_notice?in_nav_notice_number=123456"
        ),
    }
    item.update(overrides)
    return json.dumps(
        {
            "items": [item],
            "hasMore": False,
            "limit": 25,
            "offset": 0,
            "count": 1,
            "links": [],
        }
    ).encode()


def test_frozen_district_universe_and_endpoints() -> None:
    assert [code for code, _ in NTNI_DISTRICTS] == [
        "MVP",
        "MVR",
        "MVS",
        "MVM",
        "MVK",
        "MVN",
        "LRL",
        "LRH",
        "LRP",
        "LRN",
    ]
    for code, _ in NTNI_DISTRICTS:
        assert district_endpoint(code).endswith(f"/notices_by_district/{code}")


def test_unknown_district_fails_closed() -> None:
    with pytest.raises(NtniNormalizationError, match="outside the frozen"):
        district_endpoint("SWL")


def test_listing_uses_only_documented_fields() -> None:
    refs = parse_active_notice_listing(_listing())
    assert len(refs) == 1
    assert refs[0].controlnumber == "123456"
    assert set(refs[0].__dataclass_fields__) == NTNI_ITEM_FIELDS


def test_empty_listing_is_valid_but_proves_no_absence() -> None:
    raw = json.dumps(
        {
            "items": [],
            "hasMore": False,
            "limit": 25,
            "offset": 0,
            "count": 0,
            "links": [],
        }
    ).encode()
    assert parse_active_notice_listing(raw) == ()


@pytest.mark.parametrize("bad", [b"not json", b"\xff", b"[]"])
def test_invalid_listing_fails_closed(bad: bytes) -> None:
    with pytest.raises(NtniNormalizationError):
        parse_active_notice_listing(bad)


def test_unknown_or_missing_item_field_fails_closed() -> None:
    with pytest.raises(NtniNormalizationError, match="do not equal documented"):
        parse_active_notice_listing(_listing(extra="not-registered"))


def test_duplicate_controlnumber_fails_closed() -> None:
    payload = json.loads(_listing())
    payload["items"].append(dict(payload["items"][0]))
    with pytest.raises(NtniNormalizationError, match="duplicate"):
        parse_active_notice_listing(json.dumps(payload).encode())


@pytest.mark.parametrize(
    "link",
    [
        "http://ndc.ops.usace.army.mil/ords/ntni/print_nav_notice?x=1",
        "https://example.com/ords/ntni/print_nav_notice?x=1",
        "https://ndc.ops.usace.army.mil/ords/ntni/not_the_print_endpoint",
    ],
)
def test_unregistered_notice_link_fails_closed(link: str) -> None:
    with pytest.raises(NtniNormalizationError):
        parse_active_notice_listing(_listing(noticelink=link))


def test_html_normalizes_visible_full_text() -> None:
    html = b"""
    <html><head><title>Notice Title</title><style>.x { display:none }</style></head>
    <body><h1>NOTICE TO NAVIGATION INTERESTS</h1>
    <p>Lock &amp; channel restriction.</p><script>invented event</script></body></html>
    """
    assert normalize_full_text(html, content_type="text/html; charset=UTF-8") == (
        "Notice Title NOTICE TO NAVIGATION INTERESTS Lock & channel restriction."
    )


@pytest.mark.parametrize(
    ("payload", "content_type"),
    [
        (b"%PDF-1.7", "application/pdf"),
        (b"plain", "text/plain"),
        (b"\xff", "text/html; charset=utf-8"),
        (b"<script>only hidden</script>", "text/html"),
        (b"<p>text</p>", "text/html; charset=windows-1252"),
    ],
)
def test_unregistered_or_unusable_full_text_fails_closed(
    payload: bytes, content_type: str
) -> None:
    with pytest.raises(NtniNormalizationError):
        normalize_full_text(payload, content_type=content_type)
