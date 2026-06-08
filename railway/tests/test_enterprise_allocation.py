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
