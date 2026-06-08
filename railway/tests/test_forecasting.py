"""Unit tests for forecasting engines and KPIs."""
import numpy as np
from railway import railway_forecasting as rf


def test_blend_weights_sum_to_one():
    assert abs(sum(rf.BLEND_WEIGHTS.values()) - 1.0) < 1e-9


def test_weighted_blend_value():
    # all inputs 100 -> blend 100 regardless of weights (they sum to 1)
    assert abs(rf.weighted_blend(100, 100, 100, 100) - 100.0) < 1e-9


def test_ma_and_cagr():
    assert rf.ma_forecast([10, 20, 30, 40, 50]) == 30.0
    # CAGR over 10->50 in 4 periods -> ~74.76
    assert 74.0 < rf.cagr_forecast([10, 20, 30, 40, 50]) < 75.5
    # endpoints not both positive -> falls back to MA
    assert rf.cagr_forecast([0, 0, 0, 0, 10]) == rf.ma_forecast([0, 0, 0, 0, 10])


def test_intermittent_models_nonnegative():
    series = [0, 0, 5, 0, 3]
    for fn in (rf.croston_forecast, rf.sba_forecast, rf.tsb_forecast):
        out = fn(series)
        assert (np.asarray(out) >= 0).all()


def test_forecast_confidence_rules():
    assert rf.forecast_confidence("Smooth", 0.1) == "High"
    assert rf.forecast_confidence("Smooth", 0.4) == "Medium"
    assert rf.forecast_confidence("Intermittent", 0.9) == "Medium"
    assert rf.forecast_confidence("Erratic", 1.0) == "Low"
    assert rf.forecast_confidence("Dead", float("nan")) == "Very Low"


def test_forecast_to_stock_classes():
    _, c = rf.forecast_to_stock(10, 0)       # zero stock, positive forecast -> risk
    assert c == "Procurement Risk"
    _, c = rf.forecast_to_stock(10, 100)     # 0.1 -> excess
    assert c == "Excess Inventory"
    _, c = rf.forecast_to_stock(150, 100)    # 1.5 -> monitor
    assert c == "Monitor"
