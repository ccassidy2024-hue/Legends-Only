"""Tests that must never be weakened.

Everything in this project rests on two claims:
  (a) lag direction is what we say it is, and
  (b) no value enters the panel before it was published.

Each is tested here against synthetic data where the truth is known by
construction. If a test here fails, the correct response is to fix the
pipeline, never to adjust the test.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from grainsys.panel import (
    build_asof_panel,
    synthesise_release_ts,
    validate_observations,
    weekly_anchors,
)
from grainsys.screening.lagscan import ScanConfig, scan_lags
from grainsys.transforms import apply_chain, diff, seasonal_demean

# Allow importing the fixture module from tests/fixtures/
_FIXTURES = Path(__file__).resolve().parent / "fixtures"
if str(_FIXTURES) not in sys.path:
    sys.path.insert(0, str(_FIXTURES))

from make_synthetic_panel import (  # noqa: E402
    GROUND_TRUTH,
    make_synthetic_observations,
    make_synthetic_panel,
)


@pytest.fixture(scope="module")
def synthetic_bundle():
    obs, truth = make_synthetic_observations()
    values, age_days, _ = make_synthetic_panel()
    return obs, values, age_days, truth


def test_package_version():
    from grainsys import __version__

    assert __version__ == "0.1.0"


def test_synthetic_schema_and_label(synthetic_bundle):
    obs, _, _, truth = synthetic_bundle
    assert list(obs.columns) == ["series_id", "period_end", "release_ts", "value"]
    assert truth.label.startswith("SYNTHETIC")
    assert (obs["release_ts"] > obs["period_end"]).all()
    assert truth.positive_lag == 4
    assert truth.negative_lag == 8


def test_value_never_appears_before_release():
    """Core invariant: release_ts gates panel membership."""
    obs = pd.DataFrame(
        {
            "series_id": ["barge_rate_ill"],
            "period_end": [pd.Timestamp("2023-10-10")],
            "release_ts": [pd.Timestamp("2023-10-19 15:00")],
            "value": [712.0],
        }
    )
    anchors = weekly_anchors("2023-10-06", "2023-10-27", weekday="FRI")
    panel = build_asof_panel(obs, anchors)
    col = panel.values["barge_rate_ill"]

    before = col[col.index < pd.Timestamp("2023-10-19")]
    after = col[col.index > pd.Timestamp("2023-10-19")]

    assert before.isna().all(), "value leaked into anchors before its release"
    assert (after == 712.0).all(), "value failed to appear after its release"


def test_changing_release_ts_changes_asof_panel():
    """Same period_end/value, later release_ts → later first appearance."""
    base = {
        "series_id": ["s"],
        "period_end": [pd.Timestamp("2023-10-10")],
        "value": [100.0],
    }
    early = pd.DataFrame({**base, "release_ts": [pd.Timestamp("2023-10-12 12:00")]})
    late = pd.DataFrame({**base, "release_ts": [pd.Timestamp("2023-10-26 12:00")]})
    anchors = weekly_anchors("2023-10-06", "2023-11-03", weekday="FRI")

    p_early = build_asof_panel(early, anchors).values["s"]
    p_late = build_asof_panel(late, anchors).values["s"]

    fri_13 = pd.Timestamp("2023-10-13 23:59")
    fri_27 = pd.Timestamp("2023-10-27 23:59")

    assert p_early[fri_13] == 100.0
    assert pd.isna(p_late[fri_13])
    assert p_late[fri_27] == 100.0


def test_period_end_indexing_would_have_leaked():
    """Documents the trap: period_end < anchor < release_ts."""
    period_end = pd.Timestamp("2023-10-10")
    release_ts = pd.Timestamp("2023-10-19 15:00")
    anchor = pd.Timestamp("2023-10-13 23:59")
    assert period_end < anchor < release_ts


def test_lag_plus_four_means_x_leads_y_at_t_plus_four(synthetic_bundle):
    """Canonical convention: lag=+4 means X_t predicts Y_(t+4)."""
    _, values, _, truth = synthetic_bundle
    assert truth.positive_lag == 4
    cfg = ScanConfig(lags=(4,), add_ar1=False, min_obs=50, standardize=False)
    res = scan_lags(values, "synth_x", "synth_y", cfg)
    assert len(res) == 1
    assert int(res.iloc[0]["lag"]) == 4
    assert res.iloc[0]["beta"] > 0


def test_planted_positive_lag4_recovered(synthetic_bundle):
    _, values, _, truth = synthetic_bundle
    cfg = ScanConfig(lags=tuple(range(0, 13)), add_ar1=False, min_obs=50, standardize=False)
    res = scan_lags(values, truth.positive_pair[0], truth.positive_pair[1], cfg)
    best = res.loc[res["t"].abs().idxmax()]
    assert int(best["lag"]) == truth.positive_lag
    assert best["sign"] == "+"
    assert best["beta"] > 0


def test_planted_negative_lag8_recovered(synthetic_bundle):
    _, values, _, truth = synthetic_bundle
    cfg = ScanConfig(lags=tuple(range(0, 15)), add_ar1=False, min_obs=50, standardize=False)
    res = scan_lags(values, truth.negative_pair[0], truth.negative_pair[1], cfg)
    best = res.loc[res["t"].abs().idxmax()]
    assert int(best["lag"]) == truth.negative_lag
    assert best["sign"] == "-"
    assert best["beta"] < 0


def test_lag_direction_is_not_symmetric(synthetic_bundle):
    _, values, _, _ = synthetic_bundle
    cfg = ScanConfig(lags=tuple(range(1, 13)), add_ar1=False, min_obs=50, standardize=False)
    fwd = scan_lags(values, "synth_x", "synth_y", cfg)
    rev = scan_lags(values, "synth_y", "synth_x", cfg)
    assert fwd["t"].abs().max() > 3.0 * rev["t"].abs().max()


def test_persistent_noise_not_validated_evidence(synthetic_bundle):
    """Highly autocorrelated independent series must not look like a discovery."""
    _, values, _, truth = synthetic_bundle
    u, v = truth.noise_series
    cfg = ScanConfig(lags=tuple(range(0, 27)), add_ar1=True, min_obs=50, standardize=False)
    res = scan_lags(values, u, v, cfg)
    # With AR(1) control on y, residual predictive |t| should stay modest.
    assert res["t"].abs().max() < 4.5
    assert (res["inferential_status"] == "exploratory").all()


def test_shared_seasonality_creates_misleading_naive_relationship(synthetic_bundle):
    _, values, _, truth = synthetic_bundle
    p, q = truth.seasonal_decoy_pair
    cfg = ScanConfig(lags=(0,), add_ar1=False, min_obs=50, standardize=False)
    naive = scan_lags(values, p, q, cfg)
    assert naive.iloc[0]["corr"] > 0.7

    # After seasonal demeaning, the decoy relationship collapses.
    demeaned = pd.DataFrame(
        {
            p: seasonal_demean(values[p]),
            q: seasonal_demean(values[q]),
        },
        index=values.index,
    ).dropna()
    adj = scan_lags(demeaned, p, q, cfg)
    assert abs(adj.iloc[0]["corr"]) < 0.25


def test_accounting_identity_dominates_naive_ranking(synthetic_bundle):
    _, values, _, truth = synthetic_bundle
    ident = truth.accounting_identity
    origin, transport, dest = ident["origin"], ident["transport"], ident["destination"]

    residual = values[dest] - (values[origin] + values[transport])
    assert residual.abs().median() < 0.05

    cfg = ScanConfig(lags=(0,), add_ar1=False, min_obs=50, standardize=False)
    pairs = [
        ("synth_x", "synth_y"),
        (origin, dest),
        ("synth_noise_u", "synth_noise_v"),
    ]
    scores = []
    for x_id, y_id in pairs:
        r = scan_lags(values[[x_id, y_id]].dropna(), x_id, y_id, cfg)
        scores.append((x_id, y_id, abs(float(r.iloc[0]["corr"]))))
    scores.sort(key=lambda t: t[2], reverse=True)
    assert scores[0][0] == origin and scores[0][1] == dest
    assert ident["is_accounting_identity"] is True


def test_missing_data_not_silently_created(synthetic_bundle):
    obs, values, _, _ = synthetic_bundle
    # Observations omit NaN rows rather than interpolating.
    x_obs = obs.loc[obs["series_id"] == "synth_x"]
    assert x_obs["value"].isna().sum() == 0
    assert len(x_obs) < GROUND_TRUTH.n_weeks

    # Panel may be NaN where nothing was known; we never fill.
    assert values["synth_x"].isna().any()


def test_transforms_are_deterministic():
    idx = pd.date_range("2015-01-02", periods=200, freq="W-FRI")
    s = pd.Series(np.sin(np.arange(200) / 8.0) + 2.0, index=idx)
    a = apply_chain(s, "diff|seasonal_demean")
    b = apply_chain(s, ["diff", "seasonal_demean"])
    pd.testing.assert_series_equal(a, b)
    pd.testing.assert_series_equal(diff(s), apply_chain(s, "diff"))


def test_revision_uses_latest_release_at_each_anchor():
    obs = pd.DataFrame(
        {
            "series_id": ["stocks"] * 2,
            "period_end": [pd.Timestamp("2023-09-01")] * 2,
            "release_ts": [pd.Timestamp("2023-09-29"), pd.Timestamp("2024-01-12")],
            "value": [1500.0, 1462.0],
        }
    )
    anchors = weekly_anchors("2023-09-01", "2024-02-01", weekday="FRI")
    panel = build_asof_panel(obs, anchors)
    col = panel.values["stocks"]

    assert col[pd.Timestamp("2023-10-06 23:59")] == 1500.0
    assert col[pd.Timestamp("2024-01-19 23:59")] == 1462.0


def test_release_before_period_end_is_rejected():
    obs = pd.DataFrame(
        {
            "series_id": ["bad"],
            "period_end": [pd.Timestamp("2023-10-10")],
            "release_ts": [pd.Timestamp("2023-10-01")],
            "value": [1.0],
        }
    )
    with pytest.raises(ValueError, match="precedes period_end"):
        validate_observations(obs)


def test_null_release_ts_is_rejected():
    obs = pd.DataFrame(
        {
            "series_id": ["bad"],
            "period_end": [pd.Timestamp("2023-10-10")],
            "release_ts": [pd.NaT],
            "value": [1.0],
        }
    )
    with pytest.raises(ValueError, match="release_ts contains nulls"):
        validate_observations(obs)


def test_age_days_exposes_staleness_of_low_frequency_series():
    obs = pd.DataFrame(
        {
            "series_id": ["stocks"],
            "period_end": [pd.Timestamp("2023-09-01")],
            "release_ts": [pd.Timestamp("2023-09-29")],
            "value": [1500.0],
        }
    )
    anchors = weekly_anchors("2023-09-01", "2023-12-29", weekday="FRI")
    panel = build_asof_panel(obs, anchors)

    assert panel.age_days["stocks"].max() > 100
    dropped = panel.drop_stale(max_age_days=45)
    assert dropped.values["stocks"].isna().sum() > 0


def test_synthesised_release_respects_documented_delay():
    obs = pd.DataFrame(
        {
            "series_id": ["exp_insp"],
            "period_end": [pd.Timestamp("2023-10-12")],
            "release_ts": [pd.NaT],
            "value": [55.0],
        }
    )
    out = synthesise_release_ts(obs, release_delay_days=4)
    assert out["release_ts"].iloc[0] == pd.Timestamp("2023-10-16 12:00")
    validate_observations(out)
