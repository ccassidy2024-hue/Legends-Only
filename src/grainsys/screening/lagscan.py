"""Pairwise lead-lag screening (exploratory only).

Two design decisions that separate this from a correlation matrix:

1. HAC (Newey-West) standard errors. Overlapping windows and persistent
   commodity series make OLS standard errors roughly twice too small. Naive
   t-stats here are not merely imprecise, they are wrong in a known direction.

2. A max-t null for lag mining. If you scan many lags and report the best one,
   the reported naive p-value is meaningless. `maxt_pvalue` resamples the
   predictor in blocks, re-runs the ENTIRE scan on each resample, and compares
   the observed best |t| to the distribution of best |t| under the null.

Sign convention: `beta` is the response of y at time t to x at time t-lag.
A positive lag always means x LEADS y. There is no configuration option for
this; it is fixed so that edges cannot silently reverse direction.

Inferential statistics from this module are EXPLORATORY. Do not present a
best-of-many-lags naive p-value as ordinary statistical validation.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
import statsmodels.api as sm


@dataclass
class ScanConfig:
    lags: tuple[int, ...] = tuple(range(0, 27))
    min_obs: int = 104
    hac_lags: int | None = None  # None -> auto: 1.5 * max lag
    add_woy: bool = False  # week-of-year dummies as controls
    add_ar1: bool = True  # control for y[t-1]
    standardize: bool = True  # report beta in sd(y) per sd(x)


def _hac_maxlags(cfg: ScanConfig) -> int:
    if cfg.hac_lags is not None:
        return int(cfg.hac_lags)
    return max(4, int(1.5 * max(cfg.lags)))


def _design(
    x: pd.Series,
    y: pd.Series,
    lag: int,
    cfg: ScanConfig,
) -> tuple[np.ndarray, np.ndarray, pd.Index] | None:
    """Build (X, y) for y[t] ~ x[t-lag] with optional controls."""
    xl = x.shift(lag)
    cols: dict[str, pd.Series] = {"x_lag": xl}

    if cfg.add_ar1:
        # Controlling for y[t-1] is the difference between "x predicts y" and
        # "x predicts something already visible in y's own history".
        cols["y_lag1"] = y.shift(1)

    frame = pd.DataFrame(cols)
    frame["y"] = y

    if cfg.add_woy:
        woy = pd.DatetimeIndex(y.index).isocalendar().week.to_numpy()
        dummies = pd.get_dummies(pd.Series(woy, index=y.index), prefix="w", drop_first=True)
        frame = frame.join(dummies.astype(float))

    frame = frame.replace([np.inf, -np.inf], np.nan).dropna()
    if len(frame) < cfg.min_obs:
        return None

    yv = frame.pop("y").to_numpy(dtype=float)
    xv = sm.add_constant(frame.to_numpy(dtype=float), has_constant="add")
    return xv, yv, frame.index


def scan_lags(
    panel: pd.DataFrame,
    x_id: str,
    y_id: str,
    cfg: ScanConfig | None = None,
) -> pd.DataFrame:
    """Scan y[t] ~ x[t-lag] over a range of lags. Returns one row per lag.

    Results are exploratory. Prefer `maxt_pvalue` before any claim language.
    """
    cfg = cfg or ScanConfig()
    x = panel[x_id].astype(float)
    y = panel[y_id].astype(float)
    maxlags = _hac_maxlags(cfg)

    rows = []
    for lag in cfg.lags:
        built = _design(x, y, lag, cfg)
        if built is None:
            continue
        xv, yv, idx = built

        try:
            res = sm.OLS(yv, xv).fit(cov_type="HAC", cov_kwds={"maxlags": maxlags})
        except Exception:
            continue

        b, se = res.params[1], res.bse[1]
        scale = 1.0
        if cfg.standardize:
            sx, sy = x.reindex(idx).std(ddof=1), y.reindex(idx).std(ddof=1)
            scale = (sx / sy) if (sy and np.isfinite(sy) and sy > 0) else 1.0

        rows.append(
            {
                "x": x_id,
                "y": y_id,
                "lag": lag,
                "n": int(len(yv)),
                "beta": float(b * scale),
                "beta_raw": float(b),
                "se": float(se * scale),
                "t": float(b / se) if se > 0 else np.nan,
                "p_naive": float(res.pvalues[1]),
                "r2": float(res.rsquared),
                "corr": float(pd.Series(x.shift(lag)).corr(y)),
                "inferential_status": "exploratory",
            }
        )

    out = pd.DataFrame(rows)
    if not out.empty:
        out["sign"] = np.sign(out["beta"]).map({1.0: "+", -1.0: "-", 0.0: "0"})
    return out


def _stationary_bootstrap_index(n: int, mean_block: float, rng: np.random.Generator) -> np.ndarray:
    """Politis-Romano stationary bootstrap indices (wraps around)."""
    p = 1.0 / max(mean_block, 1.0)
    idx = np.empty(n, dtype=int)
    i = rng.integers(0, n)
    for t in range(n):
        idx[t] = i
        if rng.random() < p:
            i = rng.integers(0, n)
        else:
            i = (i + 1) % n
    return idx


def maxt_pvalue(
    panel: pd.DataFrame,
    x_id: str,
    y_id: str,
    cfg: ScanConfig | None = None,
    n_boot: int = 500,
    mean_block: float = 26.0,
    seed: int = 0,
) -> dict:
    """Lag-mining-corrected p-value for the best lag in a scan.

    Null: x carries no predictive information about y at any lag. Simulated by
    block-resampling x (preserving its own autocorrelation, destroying its
    alignment with y), re-running the full scan, and recording max |t|.
    """
    cfg = cfg or ScanConfig()
    observed = scan_lags(panel, x_id, y_id, cfg)
    if observed.empty:
        return {"x": x_id, "y": y_id, "status": "insufficient_data"}

    best = observed.loc[observed["t"].abs().idxmax()]
    obs_max_t = float(abs(best["t"]))

    rng = np.random.default_rng(seed)
    x_vals = panel[x_id].to_numpy(dtype=float)
    n = len(x_vals)
    null_max_t = np.empty(n_boot)

    for b in range(n_boot):
        boot_x = pd.Series(
            x_vals[_stationary_bootstrap_index(n, mean_block, rng)],
            index=panel.index,
            name=x_id,
        )
        boot_panel = panel.copy()
        boot_panel[x_id] = boot_x
        r = scan_lags(boot_panel, x_id, y_id, cfg)
        null_max_t[b] = r["t"].abs().max() if not r.empty else 0.0

    p_maxt = float((null_max_t >= obs_max_t).mean())

    return {
        "x": x_id,
        "y": y_id,
        "best_lag": int(best["lag"]),
        "beta": float(best["beta"]),
        "sign": best["sign"],
        "t": float(best["t"]),
        "p_naive": float(best["p_naive"]),
        "p_maxt": p_maxt,
        "n": int(best["n"]),
        "n_boot": n_boot,
        "null_max_t_p95": float(np.quantile(null_max_t, 0.95)),
        "status": "ok",
        "inferential_status": "exploratory_with_maxt_correction",
    }


def scan_universe(
    panel: pd.DataFrame,
    pairs: list[tuple[str, str]],
    cfg: ScanConfig | None = None,
) -> pd.DataFrame:
    """Scan a list of structurally plausible (x, y) pairs.

    `pairs` is deliberately explicit rather than all-vs-all. Pair selection is
    an economic decision made in the catalog, not a combinatorial default.
    """
    cfg = cfg or ScanConfig()
    frames = []
    for x_id, y_id in pairs:
        if x_id not in panel.columns or y_id not in panel.columns:
            continue
        r = scan_lags(panel, x_id, y_id, cfg)
        if r.empty:
            continue
        frames.append(r.loc[[r["t"].abs().idxmax()]])
    if not frames:
        return pd.DataFrame()
    out = pd.concat(frames, ignore_index=True)
    out["review_status"] = "unreviewed"
    out["notes"] = ""
    return out.sort_values("t", key=lambda s: s.abs(), ascending=False).reset_index(drop=True)


def benjamini_hochberg(p: pd.Series, alpha: float = 0.10) -> pd.Series:
    """BH false-discovery-rate flags. Apply across the whole scan, once."""
    p = p.astype(float)
    order = p.sort_values().index
    m = len(p)
    thresh = pd.Series(np.arange(1, m + 1) / m * alpha, index=order)
    passed = p.loc[order] <= thresh
    cutoff = passed[::-1].idxmax() if passed.any() else None
    keep = pd.Series(False, index=p.index)
    if cutoff is not None and passed.any():
        k = list(order).index(cutoff) + 1
        keep.loc[order[:k]] = True
    return keep
