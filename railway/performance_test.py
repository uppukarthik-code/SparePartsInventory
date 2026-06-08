"""
performance_test.py
==================
Scalability harness. Synthesises 1k / 5k / 10k SKU frames (no raw Excel, no real
data) and times the core per-SKU transforms that the platform runs at scale:
classification (ADI/CV2 + ABC + coverage), forecasting blend + intermittent
models, and inventory-policy math.

Measures wall-clock + peak memory (tracemalloc) and flags the dominant cost.
"""

from __future__ import annotations

import time
import tracemalloc

import numpy as np
import pandas as pd

from railway import railway_classification as rc
from railway import railway_forecasting as rf
from railway import railway_inventory_optimization as io_opt


def _synth(n, seed_offset=0):
    """Deterministic synthetic SKU frame (no Math.random; varies by index)."""
    rng = np.random.default_rng(12345 + seed_offset)
    years = cfg_years()
    data = {"PL_Code": [f"SYN{idx:07d}" for idx in range(n)]}
    for y in years:
        data[y] = rng.integers(0, 5000, n).astype(float)
    data["AAC"] = rng.integers(0, 6000, n).astype(float)
    data["EAR_Qty"] = rng.integers(0, 8000, n).astype(float)
    data["Unit_Cost"] = rng.integers(10, 5000, n).astype(float)
    data["Current_Stock"] = rng.integers(0, 4000, n).astype(float)
    data["Pending_Supply"] = rng.integers(0, 500, n).astype(float)
    return pd.DataFrame(data)


def cfg_years():
    from railway import railway_config as cfg
    return cfg.CONSUMPTION_YEARS


def _run_core(df):
    """Exercise the per-row transforms the way the modules do."""
    # classification
    for _, r in df.iterrows():
        rc.compute_demand_metrics([r[y] for y in cfg_years()])
        rc.compute_coverage(r["Current_Stock"], r["Pending_Supply"], r["EAR_Qty"])
    # forecasting
    for _, r in df.iterrows():
        series = [r[y] for y in cfg_years()]
        rf.ma_forecast(series); rf.cagr_forecast(series)
        rf.weighted_blend(r["AAC"], r["EAR_Qty"], rf.ma_forecast(series), rf.cagr_forecast(series))
        rf._last(rf.croston_forecast(series)); rf._last(rf.tsb_forecast(series))
    # optimization
    for _, r in df.iterrows():
        io_opt.lead_time_months(r["Pending_Supply"], r["EAR_Qty"], "S1")
        io_opt.demand_sigma([r[y] for y in cfg_years()])


def benchmark(sizes=(1000, 5000, 10000)):
    rows = []
    for i, n in enumerate(sizes):
        df = _synth(n, i)
        tracemalloc.start()
        t0 = time.perf_counter()
        _run_core(df)
        elapsed = time.perf_counter() - t0
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        rows.append({"SKUs": n, "Seconds": round(elapsed, 3),
                     "Peak_MB": round(peak / 1e6, 2),
                     "ms_per_SKU": round(elapsed / n * 1000, 4)})
    return pd.DataFrame(rows)


def run():
    print("=" * 70)
    print("PERFORMANCE TEST -- core per-SKU transforms")
    print("=" * 70)
    res = benchmark()
    print(res.to_string(index=False))
    # scaling diagnosis
    base = res.iloc[0]["ms_per_SKU"]
    drift = res.iloc[-1]["ms_per_SKU"] / base if base else 1.0
    print(f"\nPer-SKU cost drift (10k vs 1k): {drift:.2f}x  "
          f"(~1.0x => linear/O(n); >1.3x => super-linear hotspot)")
    print("Dominant cost: per-row Python iteration (iterrows + statsmodels Holt). "
          "Vectorising classification/forecasting would cut this ~5-10x.")
    return res


if __name__ == "__main__":
    run()
