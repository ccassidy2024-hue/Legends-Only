"""Series transformations.

Agricultural data is violently seasonal. Two series that both peak every
October will correlate strongly with a "significant" t-stat and mean nothing.
Every exploratory screen in this repo should consider seasonal handling.

Transform names here should match the `transformation` field in
catalog/series/*.yaml so the pipeline is catalog-driven.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

__all__ = [
    "REGISTRY",
    "apply_chain",
    "apply_transform",
    "diff",
    "expanding_seasonal_demean",
    "level",
    "log_diff",
    "pct_change",
    "seasonal_demean",
    "trailing_percentile",
    "yoy",
    "zscore",
]


def level(s: pd.Series) -> pd.Series:
    return s.astype(float)


def diff(s: pd.Series, periods: int = 1) -> pd.Series:
    return s.astype(float).diff(periods)


def log_diff(s: pd.Series, periods: int = 1) -> pd.Series:
    x = s.astype(float)
    if (x <= 0).any():
        raise ValueError(
            "log_diff requires strictly positive values; use `diff` for series "
            "that can be zero or negative (basis, spreads, residuals)."
        )
    return np.log(x).diff(periods)


def pct_change(s: pd.Series, periods: int = 1) -> pd.Series:
    return s.astype(float).pct_change(periods)


def yoy(s: pd.Series, periods: int = 52) -> pd.Series:
    """Year-over-year difference. Kills additive seasonality, but induces
    an MA(52) error structure — always pair with HAC standard errors."""
    return s.astype(float).diff(periods)


def zscore(s: pd.Series, window: int | None = None, min_periods: int = 52) -> pd.Series:
    """Z-score. If `window` is given, uses a TRAILING window (no look-ahead).

    A full-sample z-score uses the whole history's mean and sd, which is
    look-ahead. It is permitted only for descriptive charts, never for a
    variable that feeds a screen or a model claimed as real-time evidence.
    """
    x = s.astype(float)
    if window is None:
        return (x - x.mean()) / x.std(ddof=1)
    r = x.rolling(window, min_periods=min_periods)
    return (x - r.mean()) / r.std(ddof=1)


def trailing_percentile(s: pd.Series, window: int = 260, min_periods: int = 104) -> pd.Series:
    """Rank of the current value within its own trailing window, in [0, 1]."""
    x = s.astype(float)
    return x.rolling(window, min_periods=min_periods).apply(
        lambda w: (w[:-1] < w[-1]).mean() if len(w) > 1 else np.nan,
        raw=True,
    )


def seasonal_demean(s: pd.Series, by: str = "week") -> pd.Series:
    """Subtract the week-of-year (or month) mean.

    NOTE: this uses the full sample and is therefore mildly look-ahead. It is
    acceptable for *exploratory screening* and unacceptable in any walk-forward
    evaluation. Use `expanding_seasonal_demean` there.
    """
    x = s.astype(float)
    key = _season_key(x.index, by)
    return x - x.groupby(key).transform("mean")


def expanding_seasonal_demean(s: pd.Series, by: str = "week", min_years: int = 3) -> pd.Series:
    """Seasonal demeaning using only prior observations at each point in time.

    Slower, but honest. Required for anything reported as out-of-sample.
    """
    x = s.astype(float)
    key = pd.Series(_season_key(x.index, by), index=x.index)
    out = pd.Series(np.nan, index=x.index, dtype=float)
    for _, grp in x.groupby(key):
        prior_mean = grp.shift(1).expanding(min_periods=min_years).mean()
        out.loc[grp.index] = grp - prior_mean
    return out


def _season_key(idx: pd.Index, by: str) -> np.ndarray:
    idx = pd.DatetimeIndex(idx)
    if by == "week":
        return idx.isocalendar().week.to_numpy()
    if by == "month":
        return idx.month.to_numpy()
    raise ValueError(f"unknown seasonal key: {by!r}")


REGISTRY = {
    "level": level,
    "diff": diff,
    "log_diff": log_diff,
    "pct_change": pct_change,
    "yoy": yoy,
    "zscore": zscore,
    "trailing_percentile": trailing_percentile,
    "seasonal_demean": seasonal_demean,
    "expanding_seasonal_demean": expanding_seasonal_demean,
}


def apply_transform(s: pd.Series, name: str, **kwargs) -> pd.Series:
    if name not in REGISTRY:
        raise KeyError(f"unknown transform {name!r}; known: {sorted(REGISTRY)}")
    return REGISTRY[name](s, **kwargs)


def apply_chain(s: pd.Series, chain: list[str] | str) -> pd.Series:
    """Apply a pipe-delimited transform chain, e.g. 'log_diff|seasonal_demean'."""
    if isinstance(chain, str):
        chain = [c.strip() for c in chain.split("|") if c.strip()]
    out = s
    for name in chain:
        out = apply_transform(out, name)
    return out
