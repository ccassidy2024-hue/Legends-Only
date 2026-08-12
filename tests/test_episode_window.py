"""Unit tests for leakage-safe episode window construction (current-main API)."""
from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from grainsys.episodes import first_usable_analysis_anchor
from grainsys.panel import Panel, build_asof_panel, weekly_anchors

_FIXTURES = Path(__file__).resolve().parent / "fixtures"
if str(_FIXTURES) not in sys.path:
    sys.path.insert(0, str(_FIXTURES))

from make_synthetic_panel import make_synthetic_observations  # noqa: E402

from grainsys.screening.episode_window import (  # noqa: E402
    EpisodeWindowPanel,
    date_only_pretreatment_baseline_index,
    extract_episode_windows,
    to_long_format,
    validate_analysis_anchors,
)


@pytest.fixture(scope="module")
def synthetic_panel():
    obs, truth = make_synthetic_observations()
    anchors = weekly_anchors(obs["period_end"].min(), obs["period_end"].max(), weekday="FRI")
    panel = build_asof_panel(obs, anchors)
    return panel, truth


def _tiny_panel(anchors: pd.DatetimeIndex) -> Panel:
    n = len(anchors)
    values = pd.DataFrame({"synth_x": np.arange(n, dtype=float)}, index=anchors)
    age_days = pd.DataFrame({"synth_x": np.zeros(n, dtype=float)}, index=anchors)
    return Panel(values=values, age_days=age_days, anchors=anchors)


def _oct_grid() -> pd.DatetimeIndex:
    return pd.DatetimeIndex(
        [
            pd.Timestamp("2015-10-12 23:59"),
            pd.Timestamp("2015-10-19 23:59"),
            pd.Timestamp("2015-10-26 23:59"),
        ]
    )


def test_date_only_exact_on_grid_oct19_regression():
    """Person A / R-004: Oct 19 date-only → baseline Oct 12, t=0 Oct 26."""
    anchors = _oct_grid()
    panel = _tiny_panel(anchors)
    ep_panel = extract_episode_windows(
        panel,
        [
            {
                "episode_id": "EP-OCT19",
                "public_anchor": "2015-10-19",
                "public_anchor_precision": "date",
            }
        ],
        pre_weeks=1,
        post_weeks=0,
    )
    assert ep_panel.metadata.loc["EP-OCT19", "anchor_date"] == pd.Timestamp("2015-10-26 23:59")
    assert ep_panel.metadata.loc["EP-OCT19", "baseline_date"] == pd.Timestamp("2015-10-12 23:59")
    assert ep_panel.metadata.loc["EP-OCT19", "status"] == "ok"
    # R-004 baseline is Oct 12 = grid index 0; t=0 is index 2 → relative_week -2.
    # pre_weeks=1 emits [-1, 0], so baseline exists but is outside the window.
    assert ep_panel.metadata.loc["EP-OCT19", "baseline_relative_week"] == -2
    assert not bool(ep_panel.metadata.loc["EP-OCT19", "baseline_in_window"])
    assert bool(ep_panel.metadata.loc["EP-OCT19", "baseline_available"])
    # Delegated t=0 matches canonical helper.
    assert first_usable_analysis_anchor("2015-10-19", "date", list(anchors)) == anchors[2]


def test_date_only_between_grid_maps_forward():
    anchors = _oct_grid()
    t0 = first_usable_analysis_anchor("2015-10-15", "date", list(anchors))
    assert t0 == anchors[1]
    panel = _tiny_panel(anchors)
    ep = extract_episode_windows(
        panel,
        [
            {
                "episode_id": "EP-BETWEEN",
                "public_anchor": "2015-10-15",
                "public_anchor_precision": "date",
            }
        ],
        pre_weeks=0,
        post_weeks=0,
    )
    assert ep.metadata.loc["EP-BETWEEN", "anchor_date"] == anchors[1]


def test_date_only_baseline_is_not_mechanical_t_minus_1():
    anchors = _oct_grid()
    # t=0 is index 2 (Oct 26); mechanical t-1 would be Oct 19 (public date).
    t0 = first_usable_analysis_anchor("2015-10-19", "date", list(anchors))
    t0_idx = list(anchors).index(t0)
    assert t0_idx - 1 == 1
    base_idx = date_only_pretreatment_baseline_index(anchors, "2015-10-19")
    assert base_idx == 0
    assert base_idx != t0_idx - 1


def test_date_only_same_calendar_day_not_usable_as_t0():
    anchors = _oct_grid()
    t0 = first_usable_analysis_anchor("2015-10-19", "date", list(anchors))
    assert t0 != anchors[1]
    assert t0 == anchors[2]


def test_timestamp_t0_maps_first_analysis_ge_event_ts():
    anchors = _oct_grid()
    event_ts = dt.datetime(2015, 10, 19, 12, 0, 0)
    t0 = first_usable_analysis_anchor(
        dt.date(2015, 10, 19), "timestamp", list(anchors), anchor_ts=event_ts
    )
    assert t0 == anchors[1]
    panel = _tiny_panel(anchors)
    ep = extract_episode_windows(
        panel,
        [
            {
                "episode_id": "EP-TS",
                "public_anchor": "2015-10-19",
                "public_anchor_precision": "timestamp",
                "anchor_ts": event_ts,
            }
        ],
        pre_weeks=0,
        post_weeks=0,
    )
    assert ep.metadata.loc["EP-TS", "anchor_date"] == anchors[1]


def test_timestamp_date_only_input_not_converted_to_midnight():
    anchors = _oct_grid()
    with pytest.raises(ValueError, match="real anchor_ts"):
        first_usable_analysis_anchor("2015-10-19", "timestamp", list(anchors), anchor_ts=None)
    panel = _tiny_panel(anchors)
    with pytest.raises(ValueError, match="real anchor_ts"):
        extract_episode_windows(
            panel,
            [
                {
                    "episode_id": "EP-BAD",
                    "public_anchor": "2015-10-19",
                    "public_anchor_precision": "timestamp",
                }
            ],
            pre_weeks=0,
            post_weeks=0,
        )


def test_timestamp_baseline_fail_closed_unratified():
    """Person A: no automatic timestamp baseline policy."""
    anchors = _oct_grid()
    panel = _tiny_panel(anchors)
    event_ts = dt.datetime(2015, 10, 19, 12, 0, 0)
    ep = extract_episode_windows(
        panel,
        [
            {
                "episode_id": "EP-TS-BASE",
                "public_anchor": "2015-10-19",
                "public_anchor_precision": "timestamp",
                "anchor_ts": event_ts,
            }
        ],
        pre_weeks=0,
        post_weeks=0,
    )
    assert ep.metadata.loc["EP-TS-BASE", "status"] == "timestamp_baseline_unratified"
    assert not bool(ep.metadata.loc["EP-TS-BASE", "baseline_available"])
    assert pd.isna(ep.metadata.loc["EP-TS-BASE", "baseline_date"])
    assert pd.isna(ep.metadata.loc["EP-TS-BASE", "baseline_relative_week"])
    assert not bool(ep.metadata.loc["EP-TS-BASE", "baseline_in_window"])
    # t=0 still located; window cells present.
    assert ep.metadata.loc["EP-TS-BASE", "anchor_date"] == anchors[1]
    assert not ep.values.loc[("EP-TS-BASE", 0)].isna().all()


def test_ex_post_fields_do_not_determine_alignment():
    anchors = _oct_grid()
    panel = _tiny_panel(anchors)
    ep = extract_episode_windows(
        panel,
        [
            {
                "episode_id": "EP-EXPOST",
                "public_anchor": "2015-10-19",
                "public_anchor_precision": "date",
                "end_date": "2015-10-12",
                "peak_severity_date": "2015-10-12",
                "duration_days": 90,
            }
        ],
        pre_weeks=1,
        post_weeks=0,
    )
    assert ep.metadata.loc["EP-EXPOST", "anchor_date"] == anchors[2]
    assert ep.metadata.loc["EP-EXPOST", "baseline_date"] == anchors[0]
    assert ep.metadata.loc["EP-EXPOST", "end_date"] == "2015-10-12"


def test_missing_values_preserved(synthetic_panel):
    panel, _ = synthetic_panel
    col = "synth_x"
    nan_idx = panel.values[col].isna()
    assert nan_idx.any()
    # Pick a Friday grid date strictly before a known NaN anchor's calendar date
    # so date-only t=0 can land on that NaN row.
    anchor_idx = int(np.where(nan_idx)[0][0])
    # Use timestamp precision with event_ts == that anchor so t=0 is that row.
    start_ts = panel.anchors[anchor_idx]
    ep = extract_episode_windows(
        panel,
        [
            {
                "episode_id": "EP-NAN",
                "public_anchor": start_ts.date(),
                "public_anchor_precision": "timestamp",
                "anchor_ts": start_ts.to_pydatetime(),
            }
        ],
        pre_weeks=0,
        post_weeks=0,
    )
    assert pd.isna(ep.values.loc[("EP-NAN", 0), col])


def test_out_of_range_window_is_nan_not_fabricated():
    anchors = _oct_grid()
    panel = _tiny_panel(anchors)
    ep = extract_episode_windows(
        panel,
        [
            {
                "episode_id": "EP-SHORT",
                "public_anchor": "2015-10-19",
                "public_anchor_precision": "date",
            }
        ],
        pre_weeks=0,
        post_weeks=2,
    )
    assert not bool(ep.metadata.loc["EP-SHORT", "window_complete"])
    assert ep.metadata.loc["EP-SHORT", "status"] == "insufficient_window"
    assert ep.values.loc[("EP-SHORT", 1)].isna().all()
    assert ep.values.loc[("EP-SHORT", 2)].isna().all()
    assert list(ep.values.index.get_level_values("relative_week")) == [0, 1, 2]


def test_source_panel_and_episode_frame_immutable(synthetic_panel):
    panel, _ = synthetic_panel
    before_v = panel.values.copy()
    before_a = panel.age_days.copy()
    episodes = pd.DataFrame(
        [
            {
                "episode_id": "EP-MUT",
                "public_anchor": "2015-06-15",
                "public_anchor_precision": "date",
                "cluster_id": "C1",
            }
        ]
    )
    before_eps = episodes.copy()
    extract_episode_windows(panel, episodes, pre_weeks=1, post_weeks=1)
    pd.testing.assert_frame_equal(panel.values, before_v)
    pd.testing.assert_frame_equal(panel.age_days, before_a)
    pd.testing.assert_frame_equal(episodes, before_eps)


def test_duplicate_unsorted_empty_analysis_anchors_fail():
    with pytest.raises(ValueError, match="unique"):
        validate_analysis_anchors(
            pd.DatetimeIndex([pd.Timestamp("2015-10-12 23:59"), pd.Timestamp("2015-10-12 23:59")])
        )
    with pytest.raises(ValueError, match="strictly increasing"):
        validate_analysis_anchors(
            pd.DatetimeIndex([pd.Timestamp("2015-10-26 23:59"), pd.Timestamp("2015-10-12 23:59")])
        )
    with pytest.raises(ValueError, match="non-empty"):
        validate_analysis_anchors(pd.DatetimeIndex([]))


def test_metadata_preservation_cluster_driver_anticipation():
    anchors = _oct_grid()
    panel = _tiny_panel(anchors)
    ep = extract_episode_windows(
        panel,
        [
            {
                "episode_id": "EP-META",
                "public_anchor": "2015-10-19",
                "public_anchor_precision": "date",
                "cluster_id": "CL-7",
                "underlying_driver_id": "DRV-1",
                "anticipation_status": "unscheduled",
            }
        ],
        pre_weeks=1,
        post_weeks=0,
    )
    assert ep.metadata.loc["EP-META", "cluster_id"] == "CL-7"
    assert ep.metadata.loc["EP-META", "underlying_driver_id"] == "DRV-1"
    assert ep.metadata.loc["EP-META", "anticipation_status"] == "unscheduled"
    assert "weight" not in ep.metadata.columns
    assert "aggregation" not in ep.metadata.columns


def test_no_invented_weight_or_aggregation_fields():
    anchors = _oct_grid()
    panel = _tiny_panel(anchors)
    ep = extract_episode_windows(
        panel,
        [
            {
                "episode_id": "EP-W",
                "public_anchor": "2015-10-19",
                "public_anchor_precision": "date",
            }
        ],
        pre_weeks=0,
        post_weeks=0,
    )
    banned = {"weight", "weights", "aggregation", "agg", "cluster_weight"}
    assert banned.isdisjoint(set(ep.metadata.columns))
    assert banned.isdisjoint(set(ep.values.columns))


def test_one_metadata_row_per_episode_and_input_order():
    anchors = _oct_grid()
    panel = _tiny_panel(anchors)
    episodes = [
        {"episode_id": "EP-B", "public_anchor": "2015-10-12", "public_anchor_precision": "date"},
        {"episode_id": "EP-A", "public_anchor": "2015-10-19", "public_anchor_precision": "date"},
    ]
    ep = extract_episode_windows(panel, episodes, pre_weeks=0, post_weeks=0)
    assert list(ep.metadata.index) == ["EP-B", "EP-A"]
    assert len(ep.metadata) == 2


def test_left_censored_no_t0_is_explicit():
    anchors = _oct_grid()
    panel = _tiny_panel(anchors)
    ep = extract_episode_windows(
        panel,
        [
            {
                "episode_id": "EP-LATE",
                "public_anchor": "2015-10-26",
                "public_anchor_precision": "date",
            }
        ],
        pre_weeks=0,
        post_weeks=0,
    )
    assert ep.metadata.loc["EP-LATE", "status"] == "no_t0_anchor"
    assert pd.isna(ep.metadata.loc["EP-LATE", "anchor_date"])
    assert ("EP-LATE", 0) in ep.values.index
    assert ep.values.loc[("EP-LATE", 0)].isna().all()


def test_rejects_start_date_event_clock():
    anchors = _oct_grid()
    panel = _tiny_panel(anchors)
    with pytest.raises(ValueError, match="public_anchor"):
        extract_episode_windows(
            panel,
            [
                {
                    "episode_id": "EP-OLD",
                    "start_date": "2015-10-19",
                    "public_anchor": "2015-10-19",
                    "public_anchor_precision": "date",
                }
            ],
            pre_weeks=0,
            post_weeks=0,
        )


def test_requires_public_anchor_fields():
    anchors = _oct_grid()
    panel = _tiny_panel(anchors)
    with pytest.raises(ValueError, match="missing required fields"):
        extract_episode_windows(
            panel,
            [{"episode_id": "EP-X", "public_anchor": "2015-10-19"}],
            pre_weeks=0,
            post_weeks=0,
        )


def test_insufficient_date_baseline_marked():
    anchors = _oct_grid()
    panel = _tiny_panel(anchors)
    ep = extract_episode_windows(
        panel,
        [
            {
                "episode_id": "EP-NOBASE",
                "public_anchor": "2015-10-05",
                "public_anchor_precision": "date",
            }
        ],
        pre_weeks=0,
        post_weeks=0,
    )
    assert ep.metadata.loc["EP-NOBASE", "status"] == "insufficient_baseline"
    assert not bool(ep.metadata.loc["EP-NOBASE", "baseline_available"])
    assert ep.metadata.loc["EP-NOBASE", "anchor_date"] == anchors[0]
    assert pd.isna(ep.metadata.loc["EP-NOBASE", "baseline_relative_week"])
    assert not bool(ep.metadata.loc["EP-NOBASE", "baseline_in_window"])


def test_to_long_format_and_relative_grid_positions():
    anchors = pd.DatetimeIndex(
        [
            pd.Timestamp("2015-10-12 23:59"),
            pd.Timestamp("2015-10-15 23:59"),
            pd.Timestamp("2015-10-26 23:59"),
        ]
    )
    panel = _tiny_panel(anchors)
    ep = extract_episode_windows(
        panel,
        [
            {
                "episode_id": "EP-POS",
                "public_anchor": "2015-10-12",
                "public_anchor_precision": "date",
            }
        ],
        pre_weeks=0,
        post_weeks=1,
    )
    assert ep.metadata.loc["EP-POS", "anchor_date"] == anchors[1]
    assert ep.values.loc[("EP-POS", 1), "synth_x"] == 2.0
    long = to_long_format(ep)
    assert {
        "episode_id",
        "relative_week",
        "anchor_date",
        "series_id",
        "value",
        "age_days",
        "status",
        "baseline_available",
        "baseline_date",
        "baseline_relative_week",
        "baseline_in_window",
    } <= set(long.columns)


def test_baseline_in_window_true_when_pre_weeks_covers_r004_baseline():
    anchors = _oct_grid()
    panel = _tiny_panel(anchors)
    ep = extract_episode_windows(
        panel,
        [
            {
                "episode_id": "EP-INWIN",
                "public_anchor": "2015-10-19",
                "public_anchor_precision": "date",
            }
        ],
        pre_weeks=2,
        post_weeks=0,
    )
    assert ep.metadata.loc["EP-INWIN", "baseline_relative_week"] == -2
    assert bool(ep.metadata.loc["EP-INWIN", "baseline_in_window"])
    assert ep.metadata.loc["EP-INWIN", "status"] == "ok"


def test_to_long_format_preserves_timestamp_fail_closed_state():
    anchors = _oct_grid()
    panel = _tiny_panel(anchors)
    event_ts = dt.datetime(2015, 10, 19, 12, 0, 0)
    ep = extract_episode_windows(
        panel,
        [
            {
                "episode_id": "EP-TS-LONG",
                "public_anchor": "2015-10-19",
                "public_anchor_precision": "timestamp",
                "anchor_ts": event_ts,
            }
        ],
        pre_weeks=1,
        post_weeks=0,
    )
    long = to_long_format(ep)
    assert (long["status"] == "timestamp_baseline_unratified").all()
    assert (~long["baseline_available"].astype(bool)).all()
    assert long["baseline_date"].isna().all()
    assert long["baseline_relative_week"].isna().all()
    assert (~long["baseline_in_window"].astype(bool)).all()
    assert set(long["episode_id"]) == {"EP-TS-LONG"}


def test_to_long_format_preserves_per_episode_baseline_state():
    anchors = _oct_grid()
    panel = _tiny_panel(anchors)
    ep = extract_episode_windows(
        panel,
        [
            {
                "episode_id": "EP-DATE",
                "public_anchor": "2015-10-19",
                "public_anchor_precision": "date",
            },
            {
                "episode_id": "EP-TS",
                "public_anchor": "2015-10-19",
                "public_anchor_precision": "timestamp",
                "anchor_ts": dt.datetime(2015, 10, 19, 12, 0, 0),
            },
        ],
        pre_weeks=1,
        post_weeks=0,
    )
    long = to_long_format(ep)
    date_rows = long[long["episode_id"] == "EP-DATE"]
    ts_rows = long[long["episode_id"] == "EP-TS"]
    assert (date_rows["status"] == "ok").all()
    assert date_rows["baseline_available"].astype(bool).all()
    assert (date_rows["baseline_relative_week"] == -2).all()
    assert (~date_rows["baseline_in_window"].astype(bool)).all()
    assert (ts_rows["status"] == "timestamp_baseline_unratified").all()
    assert (~ts_rows["baseline_available"].astype(bool)).all()
    assert ts_rows["baseline_relative_week"].isna().all()
    assert (~ts_rows["baseline_in_window"].astype(bool)).all()


def test_package_import_path_still_works_without_reexport():
    import grainsys.screening as screening
    from grainsys.screening import episode_window as ew

    assert not hasattr(screening, "extract_episode_windows")
    assert hasattr(ew, "extract_episode_windows")


def test_extract_returns_episode_window_panel_type():
    anchors = _oct_grid()
    panel = _tiny_panel(anchors)
    ep = extract_episode_windows(
        panel,
        [
            {
                "episode_id": "EP-T",
                "public_anchor": "2015-10-19",
                "public_anchor_precision": "date",
            }
        ],
        pre_weeks=0,
        post_weeks=0,
    )
    assert isinstance(ep, EpisodeWindowPanel)
