"""Exploratory screening only. Pairwise lag scans are hypothesis-generating, not evidence."""

from grainsys.screening.lagscan import (
    ScanConfig,
    benjamini_hochberg,
    maxt_pvalue,
    scan_lags,
    scan_universe,
)

__all__ = [
    "ScanConfig",
    "benjamini_hochberg",
    "maxt_pvalue",
    "scan_lags",
    "scan_universe",
]
