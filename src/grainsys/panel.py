"""
As-of panel construction.

THE CENTRAL INVARIANT OF THIS PROJECT:

    A value may enter the panel at anchor date T if and only if
    its release timestamp is <= T.

Every observation carries two dates:

    period_end   what the observation is ABOUT (e.g. week ending 2023-10-14)
    release_ts   when it became PUBLICLY KNOWN (e.g. 2023-10-19 15:00 ET)

Nearly every look-ahead bug in applied time-series research comes from
indexing on `period_end` and forgetting `release_ts`. USDA data is
especially dangerous: Export Sales describes a week that ended days before
publication, Grain Stocks describes a quarter that ended weeks before
publication, and WASDE moves markets on release day.

Do not "fix" a leakage test by relaxing this module. Fix the caller.
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass

import numpy as np
import pandas as pd

OBS_COLUMNS = ["series_id", "period_end", "release_ts", "value"]


def validate_observations(obs: pd.DataFrame) -> pd.DataFrame:
    """Validate and normalise a long-format observation frame.

    Required columns: series_id, period_end, release_ts, value.
    Returns a sorted copy with datetime64 dates and float values.
    """
    missing = [c for c in OBS_COLUMNS if c not in obs.columns]
    if missing:
        raise ValueError(f"observations missing required columns: {missing}")

    out = obs.loc[:, OBS_COLUMNS].copy()
    out["period_end"] = pd.to_datetime(out["period_end"])
    out["release_ts"] = pd.to_datetime(out["release_ts"])
    out["value"] = pd.to_numeric(out["value"], errors="coerce")

    if out["release_ts"].isna().any():
        raise ValueError(
            "release_ts contains nulls. Every observation needs a release "
            "timestamp. If genuinely unknown, use period_end + the series' "
            "documented release_delay_days and record that assumption in the "
            "series YAML."
        )

    early = out["release_ts"] < out["period_end"]
    if early.any():
        bad = out.loc[early, "series_id"].unique().tolist()
        raise ValueError(
            f"release_ts precedes period_end for series {bad}. Data cannot be "
            "published before the period it describes has ended."
        )

    dup = out.duplicated(subset=["series_id", "period_end", "release_ts"])
    if dup.any():
        warnings.warn(
            f"{int(dup.sum())} duplicate (series_id, period_end, release_ts) rows "
            "dropped; keeping last.",
            stacklevel=2,
        )
        out = out.loc[~dup]

    return out.sort_values(["series_id", "release_ts", "period_end"]).reset_index(drop=True)


def weekly_anchors(start, end, weekday: str = "FRI") -> pd.DatetimeIndex:
    """Weekly decision timestamps.

    The anchor is the moment you would actually make a decision. Default is
    Friday, which sits after the AMS Grain Transportation Report (Thursday)
    and after FAS Export Sales (Thursday), so a Friday panel row can legally
    contain that week's transport and export data when those releases occurred.

    Anchors are timestamped at 23:59 so that a release earlier the same day
    counts as known.
    """
    idx = pd.date_range(start=start, end=end, freq=f"W-{weekday}")
    return pd.DatetimeIndex(idx.normalize() + pd.Timedelta(hours=23, minutes=59))


@dataclass
class Panel:
    """Wide as-of panel plus its staleness diagnostics."""

    values: pd.DataFrame  # index = anchor date, columns = series_id
    age_days: pd.DataFrame  # anchor - period_end of the value in use
    anchors: pd.DatetimeIndex

    def __repr__(self) -> str:  # pragma: no cover - cosmetic
        return (
            f"Panel(anchors={len(self.anchors)}, series={self.values.shape[1]}, "
            f"span={self.anchors.min():%Y-%m-%d}..{self.anchors.max():%Y-%m-%d})"
        )

    def stale(self, max_age_days: float) -> pd.DataFrame:
        """Boolean mask of cells whose underlying observation is too old."""
        return self.age_days > max_age_days

    def drop_stale(self, max_age_days: float) -> Panel:
        """Blank out values whose underlying observation has gone stale.

        Use this so a quarterly series does not silently masquerade as a
        current weekly reading for 12 weeks after each release.
        """
        mask = self.stale(max_age_days)
        vals = self.values.mask(mask)
        return Panel(vals, self.age_days.mask(mask), self.anchors)


def build_asof_panel(
    obs: pd.DataFrame,
    anchors: pd.DatetimeIndex,
    series_ids: list[str] | None = None,
    validate: bool = True,
) -> Panel:
    """Build a wide panel where each cell is the latest value KNOWN at that anchor.

    For each series and each anchor T, selects the observation with the
    greatest release_ts <= T. Where two observations share a release_ts
    (revision published alongside a new period), the later period_end wins.

    This is the only sanctioned way to build a modelling panel in this repo.
    """
    if validate:
        obs = validate_observations(obs)

    if series_ids is None:
        series_ids = sorted(obs["series_id"].unique())

    anchors = pd.DatetimeIndex(anchors).sort_values()
    anchor_frame = pd.DataFrame({"asof": anchors})

    value_cols: dict[str, pd.Series] = {}
    age_cols: dict[str, pd.Series] = {}

    for sid in series_ids:
        s = obs.loc[obs["series_id"] == sid, ["period_end", "release_ts", "value"]]
        if s.empty:
            value_cols[sid] = pd.Series(np.nan, index=anchors)
            age_cols[sid] = pd.Series(np.nan, index=anchors)
            continue

        # Sort so that within a release_ts, the newest period_end is last;
        # merge_asof takes the last matching row.
        s = s.sort_values(["release_ts", "period_end"]).reset_index(drop=True)

        merged = pd.merge_asof(
            anchor_frame,
            s,
            left_on="asof",
            right_on="release_ts",
            direction="backward",
            allow_exact_matches=True,
        )

        value_cols[sid] = pd.Series(merged["value"].to_numpy(), index=anchors)
        age = (merged["asof"] - merged["period_end"]).dt.total_seconds() / 86400.0
        age_cols[sid] = pd.Series(age.to_numpy(), index=anchors)

    values = pd.DataFrame(value_cols, index=anchors)
    age_days = pd.DataFrame(age_cols, index=anchors)
    values.index.name = age_days.index.name = "asof"
    return Panel(values=values, age_days=age_days, anchors=anchors)


def synthesise_release_ts(
    obs: pd.DataFrame,
    release_delay_days: float,
    release_hour: int = 12,
) -> pd.DataFrame:
    """Derive release_ts from period_end plus a documented publication delay.

    Only for series where a true release archive is unavailable. The delay
    must come from the series YAML, never from a guess in a notebook. Prefer
    a real vintage source (ALFRED, USDA release calendars) where one exists.
    """
    out = obs.copy()
    out["period_end"] = pd.to_datetime(out["period_end"])
    out["release_ts"] = (
        out["period_end"]
        + pd.Timedelta(days=float(release_delay_days))
        + pd.Timedelta(hours=int(release_hour))
    )
    return out
