"""P0 formula-invariant tests for the MAS planning pipeline (STEP24-26).

These re-derive Safety Stock, ROP, and SRRS from their own input columns in the
produced outputs and assert the pipeline's values match the documented inventory
formulas to numerical tolerance. They cover the highest-risk previously-untested
analytics (SS / ROP / SRRS = 0 coverage before this suite) and are robust to a
behavior-preserving refactor: they pin the MATH, not the code structure.

Formulas (per railway_safety_stock / railway_rop / railway_srrs_mas docstrings):
  Safety_Stock     = Z_Value * Demand_STD * sqrt(Lead_Time_Days / 30.4375)
  Demand_During_LT = Forecast_Annual * (Lead_Time_Days / 30.4375) / 12
  ROP              = Demand_During_LT + Safety_Stock
  Positive_Gap     = max(0, ROP - Current_Stock)
  SRRS             >= 0 and is rank-consistent (desc) with SRRS_Rank
"""
import numpy as np
import pandas as pd
import pytest

from railway import railway_config as cfg

H = cfg.OUTPUT_DIR / "MAS" / "history"
DPM = 30.4375  # DAYS_PER_MONTH (documented constant)
TOL = 1e-6
# Outputs are stored rounded to 2 decimals AND recomputed from already-rounded
# input columns, so the invariant is checked to output-rounding precision: a
# real formula error is off by >>1%, far outside these bounds.
RTOL, ATOL = 1e-2, 0.5


def _read(name):
    p = H / name
    if not p.exists():
        pytest.skip(f"{name} not present")
    return pd.read_csv(p, dtype={"PL_Code": str}, keep_default_na=False)


def _close(a, b, msg):
    assert np.isclose(np.asarray(a, float), np.asarray(b, float),
                      rtol=RTOL, atol=ATOL).all(), msg


def test_safety_stock_formula():
    df = _read("safety_stock_results.csv")
    expected = df["Z_Value"] * df["Demand_STD"] * (df["Lead_Time_Days"] / DPM) ** 0.5
    _close(df["Safety_Stock"], expected, "SS deviates from z*sigma*sqrt(LT/30.44)")
    assert (df["Safety_Stock"] >= -TOL).all(), "negative safety stock"
    assert (df["Z_Value"] >= 0).all(), "negative z (service level < 0.5?)"


def test_rop_formula():
    df = _read("rop_results.csv")
    ddlt = df["Forecast_Annual"] * (df["Lead_Time_Days"] / DPM) / 12.0
    _close(df["Demand_During_LT"], ddlt, "DDLT != Fcst*(LT/30.44)/12")
    _close(df["ROP"], df["Demand_During_LT"] + df["Safety_Stock"], "ROP != DDLT + SS")
    _close(df["Reorder_Gap"], df["ROP"] - df["Current_Stock"], "Reorder_Gap != ROP - Current_Stock")
    assert (df["ROP"] >= -TOL).all(), "negative ROP"


def test_srrs_invariants():
    df = _read("srss_results.csv")
    assert (df["Positive_Gap"] >= -TOL).all(), "negative Positive_Gap"
    # Positive_Gap is the clamped reorder gap
    clamped = (df["ROP"] - df["Current_Stock"]).clip(lower=0)
    _close(df["Positive_Gap"], clamped, "Positive_Gap != max(0, ROP-stock)")
    assert (df["SRRS"] >= -TOL).all(), "negative SRRS"
    # rank consistency: sorting by SRRS desc reproduces SRRS_Rank order
    ordered = df.sort_values("SRRS", ascending=False).reset_index(drop=True)
    assert (ordered["SRRS_Rank"].values == sorted(df["SRRS_Rank"].values)).all() or \
        ordered["SRRS_Rank"].is_monotonic_increasing, "SRRS_Rank not consistent with SRRS desc"
    # zero gap => zero SRRS (gap is a multiplicative factor)
    zero_gap = df[df["Positive_Gap"] <= TOL]
    assert (zero_gap["SRRS"].abs() < 1e-6).all(), "nonzero SRRS at zero gap"
