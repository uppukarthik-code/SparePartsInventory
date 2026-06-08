"""STEP35-OPT: enterprise budget optimization & capital allocation tests."""
import math
import numpy as np
import pandas as pd
import pytest

from railway import railway_config as cfg


def test_step35opt_config_constants_exist():
    labels = [lbl for lbl, _ in cfg.FRONTIER_BUDGETS]
    assert labels == ["Rs 1 Cr", "Rs 5 Cr", "Rs 10 Cr", "Rs 25 Cr",
                      "Rs 50 Cr", "Rs 100 Cr", "Rs 200 Cr", "Rs 500 Cr", "Unlimited"]
    assert cfg.FRONTIER_BUDGETS[0][1] == 1_00_00_000.0
    assert cfg.FRONTIER_BUDGETS[5][1] == 1_00_00_00_000.0
    assert math.isinf(cfg.FRONTIER_BUDGETS[-1][1])
    assert cfg.ENTERPRISE_BUDGET == 1_00_00_00_000.0
    assert cfg.ANNUAL_PROCUREMENT_BUDGET is None
    assert cfg.ROADMAP_YEARS == ["FY2026-27", "FY2027-28", "FY2028-29"]
    assert cfg.RISK_REDUCTION_TARGETS == [0.50, 0.75, 0.90]
    exec_labels = [lbl for lbl, _ in cfg.EXECUTIVE_SCENARIO_BUDGETS]
    assert exec_labels == ["Rs 25 Cr", "Rs 50 Cr", "Rs 100 Cr", "Rs 200 Cr", "Unlimited"]


from railway import railway_inventory_optimization as opt


def _toy_opt():
    return pd.DataFrame({
        "PL_Code": ["P1", "P2", "P3", "P4"],
        "Description": ["a", "b", "c", "d"],
        "ABC_Class": ["A", "A", "B1", "C"],
        "Criticality": ["S1", "S2", "S3", "S4"],
        "Inventory_Status": ["Procurement Required"] * 4,
        "Service_Risk_Reduction_Score": [100.0, 40.0, 30.0, 10.0],
        "Inventory_Investment_Required": [1_00_00_000.0, 50_00_000.0, 30_00_000.0, 10_00_000.0],
    })


def test_frontier_monotonic_and_unlimited_funds_all():
    fr = opt.solve_budget_frontier(_toy_opt(), budgets=cfg.FRONTIER_BUDGETS, write=False)
    rr = fr["Risk_Reduction_Pct"].tolist()
    assert all(b >= a - 1e-9 for a, b in zip(rr, rr[1:]))
    last = fr.iloc[-1]
    assert last["Budget_Label"] == "Unlimited"
    assert last["PLs_Funded"] == 4
    assert abs(last["Risk_Reduction_Pct"] - 100.0) < 1e-6
    for col in ["Budget_Label", "Budget_Rupees", "PLs_Funded", "Critical_PLs_Funded",
                "SRRS_Mitigated", "SRRS_Remaining", "Risk_Reduction_Pct",
                "Budget_Utilized", "Marginal_SRRS_Per_Rupee"]:
        assert col in fr.columns
