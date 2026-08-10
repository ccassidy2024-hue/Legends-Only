"""Deterministic SYNTHETIC observation fixture with known planted relationships.

ALL DATA PRODUCED HERE IS SYNTHETIC. It is not empirical grain-market data.
Do not mistake fixture output for research findings.

Canonical observation schema:
    series_id, period_end, release_ts, value

Planted ground truth (fixed seed=20240601):
  1. Positive lead:   X_t -> Y_(t+4)  with beta ≈ +0.85
  2. Negative lead:   A_t -> B_(t+8)  with beta ≈ -1.10
  3. Two independent persistent AR(1) noise series: noise_u, noise_v
  4. Seasonal decoy: season_p and season_q share week-of-year seasonality,
     with NO causal relationship
  5. Accounting identity: dest_price ≈ origin_price + transport_cost
     (near-identity that dominates naive correlation rankings)
  6. Missing observations planted in X and Y
  7. Publication delay: release_ts = period_end + 4 days + 12 hours
     (period_end != release_ts)
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from grainsys.panel import OBS_COLUMNS, build_asof_panel, weekly_anchors

SEED = 20240601
N_WEEKS = 520
RELEASE_DELAY_DAYS = 4
RELEASE_HOUR = 12
START = "2014-01-03"  # Friday


@dataclass(frozen=True)
class SyntheticGroundTruth:
    """Documented planted relationships for tests."""

    seed: int
    n_weeks: int
    release_delay_days: int
    positive_pair: tuple[str, str]
    positive_lag: int
    positive_beta: float
    negative_pair: tuple[str, str]
    negative_lag: int
    negative_beta: float
    noise_series: tuple[str, str]
    seasonal_decoy_pair: tuple[str, str]
    accounting_identity: dict
    missing_series: tuple[str, ...]
    label: str = "SYNTHETIC — not empirical data"


GROUND_TRUTH = SyntheticGroundTruth(
    seed=SEED,
    n_weeks=N_WEEKS,
    release_delay_days=RELEASE_DELAY_DAYS,
    positive_pair=("synth_x", "synth_y"),
    positive_lag=4,
    positive_beta=0.85,
    negative_pair=("synth_a", "synth_b"),
    negative_lag=8,
    negative_beta=-1.10,
    noise_series=("synth_noise_u", "synth_noise_v"),
    seasonal_decoy_pair=("synth_season_p", "synth_season_q"),
    accounting_identity={
        "origin": "synth_origin_price",
        "transport": "synth_transport_cost",
        "destination": "synth_dest_price",
        "relation": "dest ≈ origin + transport (+ tiny noise)",
        "is_accounting_identity": True,
    },
    missing_series=("synth_x", "synth_y"),
)


def _ar1(rng: np.random.Generator, n: int, phi: float, scale: float = 1.0) -> np.ndarray:
    eps = rng.normal(0.0, scale, size=n)
    out = np.empty(n)
    out[0] = eps[0]
    for t in range(1, n):
        out[t] = phi * out[t - 1] + eps[t]
    return out


def make_synthetic_observations() -> tuple[pd.DataFrame, SyntheticGroundTruth]:
    """Return long-format synthetic observations + ground-truth metadata."""
    rng = np.random.default_rng(SEED)
    period_ends = pd.date_range(START, periods=N_WEEKS, freq="W-FRI")
    weeks = period_ends.isocalendar().week.to_numpy().astype(float)

    x = _ar1(rng, N_WEEKS, phi=0.55, scale=1.0)
    y = np.full(N_WEEKS, np.nan)
    for t in range(N_WEEKS):
        noise = 0.35 * rng.normal()
        if t >= GROUND_TRUTH.positive_lag:
            y[t] = GROUND_TRUTH.positive_beta * x[t - GROUND_TRUTH.positive_lag] + noise
        else:
            y[t] = noise

    a = _ar1(rng, N_WEEKS, phi=0.50, scale=1.0)
    b = np.full(N_WEEKS, np.nan)
    for t in range(N_WEEKS):
        noise = 0.40 * rng.normal()
        if t >= GROUND_TRUTH.negative_lag:
            b[t] = GROUND_TRUTH.negative_beta * a[t - GROUND_TRUTH.negative_lag] + noise
        else:
            b[t] = noise

    noise_u = _ar1(rng, N_WEEKS, phi=0.90, scale=1.0)
    noise_v = _ar1(rng, N_WEEKS, phi=0.90, scale=1.0)

    # Shared seasonality, independent idiosyncratic shocks — no causal link.
    season = np.sin(2 * np.pi * weeks / 52.0)
    season_p = 2.0 * season + rng.normal(0.0, 0.25, size=N_WEEKS)
    season_q = 2.0 * season + rng.normal(0.0, 0.25, size=N_WEEKS)

    origin = 4.0 + 0.15 * _ar1(rng, N_WEEKS, phi=0.80, scale=0.5)
    transport = 0.8 + 0.05 * _ar1(rng, N_WEEKS, phi=0.70, scale=0.3)
    dest = origin + transport + rng.normal(0.0, 0.02, size=N_WEEKS)

    series = {
        "synth_x": x,
        "synth_y": y,
        "synth_a": a,
        "synth_b": b,
        "synth_noise_u": noise_u,
        "synth_noise_v": noise_v,
        "synth_season_p": season_p,
        "synth_season_q": season_q,
        "synth_origin_price": origin,
        "synth_transport_cost": transport,
        "synth_dest_price": dest,
    }

    # Plant missing observations (never silently interpolate elsewhere).
    miss_idx = rng.choice(N_WEEKS, size=18, replace=False)
    for i in miss_idx[:9]:
        series["synth_x"][i] = np.nan
    for i in miss_idx[9:]:
        series["synth_y"][i] = np.nan

    rows = []
    for sid, values in series.items():
        for pe, val in zip(period_ends, values, strict=True):
            if np.isnan(val):
                continue  # missing = absent row, not interpolated
            release = pe + pd.Timedelta(days=RELEASE_DELAY_DAYS, hours=RELEASE_HOUR)
            rows.append(
                {
                    "series_id": sid,
                    "period_end": pe,
                    "release_ts": release,
                    "value": float(val),
                }
            )

    obs = pd.DataFrame(rows, columns=OBS_COLUMNS)
    obs.attrs["synthetic"] = True
    obs.attrs["label"] = GROUND_TRUTH.label
    return obs, GROUND_TRUTH


def make_synthetic_panel() -> tuple[pd.DataFrame, pd.DataFrame, SyntheticGroundTruth]:
    """Build an as-of wide panel from synthetic observations.

    Returns (values_panel, age_days, ground_truth).
    """
    obs, truth = make_synthetic_observations()
    anchors = weekly_anchors(period_end_min(obs), period_end_max(obs), weekday="FRI")
    panel = build_asof_panel(obs, anchors)
    return panel.values, panel.age_days, truth


def period_end_min(obs: pd.DataFrame) -> pd.Timestamp:
    return pd.to_datetime(obs["period_end"]).min()


def period_end_max(obs: pd.DataFrame) -> pd.Timestamp:
    return pd.to_datetime(obs["period_end"]).max()


if __name__ == "__main__":  # pragma: no cover
    observations, gt = make_synthetic_observations()
    print(gt.label)
    print(f"rows={len(observations)} series={observations['series_id'].nunique()}")
    print(f"positive: {gt.positive_pair} lag=+{gt.positive_lag} beta={gt.positive_beta}")
    print(f"negative: {gt.negative_pair} lag=+{gt.negative_lag} beta={gt.negative_beta}")
    print(f"release delay days={gt.release_delay_days}")
