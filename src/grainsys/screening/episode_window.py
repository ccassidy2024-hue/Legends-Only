"""Episode-relative window extraction on a caller-supplied analysis grid.

Consumes an as-of Panel (``.values``, ``.age_days``, ``.anchors``) and episode
records keyed by the canonical ledger field ``public_anchor``.

t=0 mapping is delegated to ``grainsys.episodes.first_usable_analysis_anchor``
(R-001 / EPISODE_PROTOCOL §B.3). Date-only pretreatment baseline follows R-004
(last analysis anchor with calendar date strictly before ``public_anchor``).

Timestamp-precision pretreatment baseline is **not ratified**. This module
fail-closes: it will not invent ``last analysis_ts < event_ts`` as project
policy. Timestamp episodes may still locate t=0 and extract relative windows,
but ``baseline_available`` is False and ``status`` reports
``timestamp_baseline_unratified``.

Ex-post fields (``peak_severity_date``, ``end_date``, ``duration_days``) are
never used for alignment (R-006).
"""
from __future__ import annotations

import datetime as dt
from collections.abc import Iterable
from dataclasses import dataclass

import numpy as np
import pandas as pd

from grainsys.episodes import first_usable_analysis_anchor

_VALID_PRECISION = frozenset({"date", "timestamp"})


@dataclass
class EpisodeWindowPanel:
    """Event-relative panel slice across one or more episodes.

    values / age_days: MultiIndex (episode_id, relative_week), columns = series_id
    metadata: index = episode_id
    """

    values: pd.DataFrame
    age_days: pd.DataFrame
    metadata: pd.DataFrame


def _to_calendar_date(value: object) -> dt.date:
    if isinstance(value, dt.datetime):
        return value.date()
    if isinstance(value, dt.date):
        return value
    ts = pd.Timestamp(value)
    if pd.isna(ts):
        raise ValueError("public_anchor is missing or unparseable")
    return ts.date()


def _validate_precision(precision: str) -> str:
    if precision not in _VALID_PRECISION:
        raise ValueError(
            f"public_anchor_precision must be 'date' or 'timestamp', got {precision!r}"
        )
    return precision


def validate_analysis_anchors(anchors: pd.DatetimeIndex) -> pd.DatetimeIndex:
    """Require a deterministic, strictly increasing analysis-anchor grid."""
    anchors = pd.DatetimeIndex(anchors)
    if len(anchors) == 0:
        raise ValueError("analysis anchors must be non-empty")
    if anchors.isna().any():
        raise ValueError("analysis anchors must not contain null timestamps")
    if not anchors.is_unique:
        raise ValueError("analysis anchors must be unique; duplicate grid points are ambiguous")
    if len(anchors) > 1 and not bool((anchors[1:] > anchors[:-1]).all()):
        raise ValueError("analysis anchors must be strictly increasing")
    return anchors


def date_only_pretreatment_baseline_index(
    anchors: pd.DatetimeIndex,
    public_anchor: object,
) -> int:
    """R-004: last analysis anchor with calendar date strictly before public_anchor.

    Returns -1 when no qualifying baseline exists. Does not use remapped t=0.
    """
    anchors = validate_analysis_anchors(anchors)
    pa = _to_calendar_date(public_anchor)
    earlier = [
        i
        for i, a in enumerate(anchors)
        if _to_calendar_date(a.to_pydatetime() if hasattr(a, "to_pydatetime") else a) < pa
    ]
    if not earlier:
        return -1
    return int(earlier[-1])


def _anchor_index(anchors: pd.DatetimeIndex, target: object) -> int:
    """Locate ``target`` in ``anchors``; raise if absent."""
    tgt = pd.Timestamp(target)
    for i, a in enumerate(anchors):
        if pd.Timestamp(a) == tgt:
            return i
    raise ValueError(
        "analysis anchor returned by first_usable_analysis_anchor not found in grid: "
        f"{target!r}"
    )


def extract_episode_windows(
    panel,
    episodes: pd.DataFrame | Iterable[dict],
    pre_weeks: int,
    post_weeks: int,
) -> EpisodeWindowPanel:
    """Extract event-relative windows on a caller-supplied analysis grid.

    Parameters
    ----------
    panel :
        As-of panel from ``build_asof_panel``.
    episodes :
        Records with required ``episode_id``, ``public_anchor``, and
        ``public_anchor_precision``. Timestamp precision also requires
        ``anchor_ts`` (passed through to ``first_usable_analysis_anchor``).
    pre_weeks / post_weeks :
        Required grid-step counts (not a preregistered horizon policy).
    """
    if pre_weeks < 0 or post_weeks < 0:
        raise ValueError("pre_weeks and post_weeks must be non-negative")

    if isinstance(episodes, pd.DataFrame):
        ep_df = episodes.copy()
    else:
        ep_df = pd.DataFrame(list(episodes))

    required = {"episode_id", "public_anchor", "public_anchor_precision"}
    if not required.issubset(set(ep_df.columns)):
        missing = sorted(required - set(ep_df.columns))
        raise ValueError(f"episodes input missing required fields: {missing}")

    if "start_date" in ep_df.columns:
        raise ValueError(
            "episodes must not supply start_date as an event clock; "
            "use canonical public_anchor (and anchor_ts when timestamp-precision)"
        )

    if ep_df["episode_id"].duplicated().any():
        dup = ep_df.loc[ep_df["episode_id"].duplicated(), "episode_id"].unique().tolist()
        raise ValueError(f"duplicate episode_id(s) in episodes: {dup}")
    if ep_df["episode_id"].isna().any():
        raise ValueError("episodes contain null episode_id values")

    ep_df = ep_df.reset_index(drop=True)
    anchors = validate_analysis_anchors(pd.DatetimeIndex(panel.anchors))
    n_anchors = len(anchors)
    series_cols = list(panel.values.columns)
    rel_weeks = list(range(-pre_weeks, post_weeks + 1))
    anchor_list = list(anchors)

    rows_values: list[pd.Series] = []
    rows_age: list[pd.Series] = []
    ep_index: list[tuple[object, int]] = []
    metadata_rows: list[dict] = []

    for _, ep in ep_df.iterrows():
        eid = ep["episode_id"]
        precision = _validate_precision(str(ep["public_anchor_precision"]))
        public_anchor = ep["public_anchor"]
        anchor_ts = ep["anchor_ts"] if "anchor_ts" in ep_df.columns else None

        try:
            t0_anchor = first_usable_analysis_anchor(
                public_anchor,
                precision,
                anchor_list,
                anchor_ts=anchor_ts,
            )
        except ValueError:
            raise

        if t0_anchor is None:
            i0 = n_anchors
            t0_ok = False
        else:
            i0 = _anchor_index(anchors, t0_anchor)
            t0_ok = True

        if precision == "date":
            i_base = date_only_pretreatment_baseline_index(anchors, public_anchor)
            baseline_ok = i_base >= 0
            baseline_status_ok = True
        else:
            # Timestamp baseline is unratified — fail closed (do not invent).
            i_base = -1
            baseline_ok = False
            baseline_status_ok = False

        window_complete = t0_ok and (0 <= i0 - pre_weeks) and (i0 + post_weeks < n_anchors)

        # Grid-relative location of the R-004 baseline vs t=0 (date precision only).
        # Never invent a timestamp baseline relative week.
        if precision == "date" and baseline_ok and t0_ok:
            baseline_relative_week: int | float = int(i_base - i0)
            baseline_in_window = bool(-pre_weeks <= baseline_relative_week <= post_weeks)
        else:
            baseline_relative_week = np.nan
            baseline_in_window = False

        if not t0_ok:
            status = "no_t0_anchor"
        elif not baseline_status_ok:
            status = "timestamp_baseline_unratified"
        elif not baseline_ok:
            status = "insufficient_baseline"
        elif not window_complete:
            status = "insufficient_window"
        else:
            status = "ok"

        meta = {
            "episode_id": eid,
            "public_anchor": public_anchor,
            "public_anchor_precision": precision,
            "anchor_date": anchors[i0] if t0_ok else pd.NaT,
            "baseline_date": anchors[i_base] if baseline_ok else pd.NaT,
            "baseline_available": bool(baseline_ok),
            "baseline_relative_week": baseline_relative_week,
            "baseline_in_window": bool(baseline_in_window),
            "window_complete": bool(window_complete),
            "status": status,
        }
        if "anchor_ts" in ep_df.columns:
            meta["anchor_ts"] = ep["anchor_ts"]

        # Carry remaining episode fields as metadata only. Alignment reads solely
        # public_anchor / public_anchor_precision / anchor_ts above (R-006: ex-post
        # fields such as end_date / peak_severity_date / duration_days are never
        # consulted for t=0 or baseline).
        for c in ep_df.columns:
            if c in (
                "episode_id",
                "public_anchor",
                "public_anchor_precision",
                "anchor_ts",
                "start_date",
            ):
                continue
            meta[c] = ep[c]
        metadata_rows.append(meta)

        for k in rel_weeks:
            idx = i0 + int(k)
            if 0 <= idx < n_anchors:
                row_vals = panel.values.iloc[idx].copy()
                row_age = panel.age_days.iloc[idx].copy()
            else:
                row_vals = pd.Series(np.nan, index=series_cols, dtype=float)
                row_age = pd.Series(np.nan, index=series_cols, dtype=float)
            rows_values.append(row_vals)
            rows_age.append(row_age)
            ep_index.append((eid, int(k)))

    multi = pd.MultiIndex.from_tuples(ep_index, names=["episode_id", "relative_week"])
    values_df = pd.DataFrame(rows_values, index=multi).reindex(columns=series_cols)
    age_df = pd.DataFrame(rows_age, index=multi).reindex(columns=series_cols)
    metadata_df = pd.DataFrame(metadata_rows).set_index("episode_id")

    return EpisodeWindowPanel(values=values_df, age_days=age_df, metadata=metadata_df)


def to_long_format(ep_panel: EpisodeWindowPanel) -> pd.DataFrame:
    """Long format with per-episode alignment state preserved.

    Columns: episode_id, relative_week, anchor_date, series_id, value, age_days,
    status, baseline_available, baseline_date, baseline_relative_week,
    baseline_in_window.
    """
    vals = ep_panel.values.reset_index()
    long_vals = vals.melt(
        id_vars=["episode_id", "relative_week"], var_name="series_id", value_name="value"
    )
    ages = ep_panel.age_days.reset_index()
    long_ages = ages.melt(
        id_vars=["episode_id", "relative_week"], var_name="series_id", value_name="age_days"
    )
    merged = pd.merge(
        long_vals, long_ages, on=["episode_id", "relative_week", "series_id"], how="left"
    )
    state_cols = [
        "episode_id",
        "anchor_date",
        "status",
        "baseline_available",
        "baseline_date",
        "baseline_relative_week",
        "baseline_in_window",
    ]
    meta = ep_panel.metadata.reset_index()[state_cols]
    out = pd.merge(merged, meta, on="episode_id", how="left")
    return out[
        [
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
        ]
    ]
