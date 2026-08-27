import numpy as np
import pandas as pd
import pytest

from grainsys.screening import lagscan
from grainsys.screening.lagscan import ScanConfig


def make_simple_panel(n=200, seed=0):
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2018-01-01", periods=n, freq="W-WED")
    df = pd.DataFrame(index=dates)
    df["x"] = rng.normal(size=n)
    df["y"] = rng.normal(size=n)
    return df


def test_maxt_pvalue_finite_sample_floor(monkeypatch):
    panel = make_simple_panel(n=120)

    calls = {"i": 0}

    def fake_scan_lags(ob_panel, x_id, y_id, cfg):
        # First call: observed scan returns a best |t| = 5
        if calls["i"] == 0:
            calls["i"] += 1
            return pd.DataFrame([
                {"lag": 0, "t": 5.0, "p_naive": 0.0001, "beta": 1.0, "sign": "+", "n": 100}
            ])
        # Bootstrap replicates: return small t-values that never exceed observed
        calls["i"] += 1
        return pd.DataFrame([
            {"lag": 0, "t": 0.1, "p_naive": 0.9, "beta": 0.01, "sign": "+", "n": 100}
        ])

    monkeypatch.setattr(lagscan, "scan_lags", fake_scan_lags)

    res = lagscan.maxt_pvalue(panel, "x", "y", cfg=ScanConfig(), n_boot=10, seed=1)
    # With 10 successful replicates and none >= obs, finite-sample p should be (0+1)/(10+1)
    assert res["status"] == "ok"
    assert pytest.approx(res["p_maxt"], rel=1e-6) == (1.0 / 11.0)
    assert res["n_boot_success"] == 10


def test_maxt_pvalue_handles_failed_replicates(monkeypatch):
    panel = make_simple_panel(n=120)

    calls = {"i": 0}

    def fake_scan_lags_mixture(ob_panel, x_id, y_id, cfg):
        # observed
        if calls["i"] == 0:
            calls["i"] += 1
            return pd.DataFrame([
                {"lag": 0, "t": 2.0, "p_naive": 0.05, "beta": 0.5, "sign": "+", "n": 100}
            ])
        calls["i"] += 1
        # Let half of bootstraps fail (empty)
        if calls["i"] % 2 == 0:
            return pd.DataFrame()
        return pd.DataFrame([
            {"lag": 0, "t": 0.5, "p_naive": 0.6, "beta": 0.05, "sign": "+", "n": 100}
        ])

    monkeypatch.setattr(lagscan, "scan_lags", fake_scan_lags_mixture)

    res = lagscan.maxt_pvalue(panel, "x", "y", cfg=ScanConfig(), n_boot=10, seed=2)
    # Should report number of successful bootstraps (~5)
    assert res["status"] == "ok"
    assert res["n_boot_success"] > 0
    assert res["n_boot_success"] < 10


def test_bh_rejects_naive_best_lag_composition():
    # Build a fake scan_universe output with naive p-values
    p = pd.Series([0.01, 0.02, 0.05], index=["a", "b", "c"])
    # Default should refuse
    with pytest.raises(ValueError):
        _ = lagscan.benjamini_hochberg(p)
    # But caller can explicitly accept responsibility
    keep = lagscan.benjamini_hochberg(p, exploratory_ok=True)
    assert isinstance(keep, pd.Series)


def test_scan_lags_with_woy_flag():
    panel = make_simple_panel(n=150)
    cfg = ScanConfig()
    cfg.add_woy = True
    res = lagscan.scan_lags(panel, "x", "y", cfg=cfg)
    # Function should run and return either empty or a DataFrame; ensure no exception
    assert isinstance(res, pd.DataFrame)


def test_hac_maxlags_guard():
    # Create a cfg with huge lags so that 1.5 * max(lags) exceeds min_obs/2
    cfg = ScanConfig()
    cfg.lags = tuple(range(0, 201))
    cfg.min_obs = 100
    # _hac_maxlags itself returns a number, but scan_lags will compute and then
    # apply the guard. We provoke the guard by calling scan_lags with tiny panel
    panel = pd.DataFrame({"x": np.random.normal(size=10), "y": np.random.normal(size=10)},
                         index=pd.date_range("2020-01-01", periods=10, freq="W"))
    with pytest.raises(RuntimeError):
        _ = lagscan.scan_lags(panel, "x", "y", cfg=cfg)


def test_maxt_pvalue_default_contract_unchanged(monkeypatch):
    panel = make_simple_panel(n=120)
    calls = {"i": 0}

    def fake_scan_lags(ob_panel, x_id, y_id, cfg):
        if calls["i"] == 0:
            calls["i"] += 1
            return pd.DataFrame([
                {"lag": 0, "t": 5.0, "p_naive": 0.0001, "beta": 1.0, "sign": "+", "n": 100}
            ])
        calls["i"] += 1
        return pd.DataFrame([
            {"lag": 0, "t": 0.1, "p_naive": 0.9, "beta": 0.01, "sign": "+", "n": 100}
        ])

    monkeypatch.setattr(lagscan, "scan_lags", fake_scan_lags)

    res = lagscan.maxt_pvalue(panel, "x", "y", cfg=ScanConfig(), n_boot=10, seed=1)
    assert res["status"] == "ok"
    assert res["n_boot_success"] == 10
    assert res["min_boot_success_required"] is None
    assert res["valid"] is True


def test_maxt_pvalue_rejects_low_bootstrap_success(monkeypatch):
    panel = make_simple_panel(n=120)
    calls = {"i": 0}

    def fake_scan_lags(ob_panel, x_id, y_id, cfg):
        if calls["i"] == 0:
            calls["i"] += 1
            return pd.DataFrame([
                {"lag": 0, "t": 5.0, "p_naive": 0.0001, "beta": 1.0, "sign": "+", "n": 100}
            ])
        calls["i"] += 1
        return pd.DataFrame([
            {"lag": 0, "t": 0.1, "p_naive": 0.9, "beta": 0.01, "sign": "+", "n": 100}
        ])

    monkeypatch.setattr(lagscan, "scan_lags", fake_scan_lags)

    res = lagscan.maxt_pvalue(
        panel, "x", "y", cfg=ScanConfig(), n_boot=10, seed=1, min_boot_success=1000
    )
    assert res["status"] == "bootstrap_low_success"
    assert res["inferential_status"] == "bootstrap_low_success"
    assert res["n_boot_success"] == 10
    assert res["min_boot_success_required"] == 1000
    assert res["valid"] is False
    assert np.isnan(res["p_maxt"])


def test_maxt_pvalue_accepts_achievable_min_boot_success(monkeypatch):
    panel = make_simple_panel(n=120)
    calls = {"i": 0}

    def fake_scan_lags(ob_panel, x_id, y_id, cfg):
        if calls["i"] == 0:
            calls["i"] += 1
            return pd.DataFrame([
                {"lag": 0, "t": 5.0, "p_naive": 0.0001, "beta": 1.0, "sign": "+", "n": 100}
            ])
        calls["i"] += 1
        return pd.DataFrame([
            {"lag": 0, "t": 0.1, "p_naive": 0.9, "beta": 0.01, "sign": "+", "n": 100}
        ])

    monkeypatch.setattr(lagscan, "scan_lags", fake_scan_lags)

    res = lagscan.maxt_pvalue(
        panel, "x", "y", cfg=ScanConfig(), n_boot=10, seed=1, min_boot_success=1
    )
    assert res["status"] == "ok"
    assert res["valid"] is True
    assert res["min_boot_success_required"] == 1
    assert pytest.approx(res["p_maxt"], rel=1e-6) == (1.0 / 11.0)
