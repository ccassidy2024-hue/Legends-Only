"""Unit tests for outcome-blind v2 family execution helpers."""

from grainsys.discovery.execute_v2_families import (
    haversine_m,
    parse_hurdat2_positions,
    parse_hurdat_latlon,
)


def test_haversine_zero_and_100nm_scale() -> None:
    assert haversine_m(0.0, 0.0, 0.0, 0.0) == 0.0
    # 100 NM along equator on the NM-sphere is 100 arc-minutes of longitude.
    dist = haversine_m(0.0, 0.0, 0.0, 100.0 / 60.0)
    assert abs(dist - 185200.0) < 1.0


def test_parse_hurdat_latlon() -> None:
    assert parse_hurdat_latlon("29.1N", "90.2W") == (29.1, -90.2)
    assert parse_hurdat_latlon("16.5S", "78.9E") == (-16.5, 78.9)
    assert parse_hurdat_latlon("", "90.2W") is None


def test_parse_hurdat2_sample_period_and_skip_missing() -> None:
    raw = (
        b"AL092021,            IDA,     2,\n"
        b"20210826, 1800,  , TS, 20.1N,  86.6W,  40, 1006,\n"
        b"20090826, 1800,  , TS, 20.1N,  86.6W,  40, 1006,\n"
        b"20210827, 0000,  , TS,     ,  86.6W,  40, 1006,\n"
    )
    pos = parse_hurdat2_positions(raw, sample_start="2010-01-01", sample_end="2024-12-31")
    assert pos == [("AL092021", "202108261800", 20.1, -86.6)]
