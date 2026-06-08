"""
railway_regression.py
=====================
Regression guard. Captures key categorical distributions as a baseline, and
compares future runs against it to flag unexpected drift as data scales.

Tracked distributions:
    ABC_Class, Criticality, Demand_Class, Forecast_Confidence, Inventory_Status
"""

from __future__ import annotations

import json

import pandas as pd

from railway import railway_config as cfg

BASELINE_PATH = cfg.PACKAGE_DIR / "railway_regression_baseline.json"


def current_distributions() -> dict:
    sm = pd.read_csv(cfg.SKU_MASTER_CSV, dtype={"PL_Code": str})
    fc = pd.read_csv(cfg.FORECAST_CSV, dtype={"PL_Code": str})
    pol = pd.read_csv(cfg.INVENTORY_POLICY_CSV, dtype={"PL_Code": str})
    return {
        "row_counts": {"sku_master": len(sm), "forecast": len(fc), "policy": len(pol)},
        "ABC_Class": sm["ABC_Class"].value_counts().sort_index().to_dict(),
        "Criticality": sm["Criticality"].value_counts().sort_index().to_dict(),
        "Demand_Class": fc["Demand_Class"].value_counts().sort_index().to_dict(),
        "Forecast_Confidence": fc["Forecast_Confidence"].value_counts().sort_index().to_dict(),
        "Inventory_Status": pol["Inventory_Status"].value_counts().sort_index().to_dict(),
    }


def save_baseline():
    dist = current_distributions()
    with open(BASELINE_PATH, "w") as f:
        json.dump(dist, f, indent=2)
    return dist


def compare_to_baseline() -> list:
    """Return a list of drift messages (empty if identical to baseline)."""
    if not BASELINE_PATH.exists():
        return ["No baseline found -- run save_baseline() first."]
    baseline = json.load(open(BASELINE_PATH))
    current = current_distributions()
    drift = []
    for key in baseline:
        if baseline[key] != current.get(key):
            drift.append(f"DRIFT in {key}: baseline={baseline[key]} current={current.get(key)}")
    return drift


def run(mode="save"):
    if mode == "save":
        dist = save_baseline()
        print("Baseline saved:", BASELINE_PATH.name)
        for k, v in dist.items():
            print(f"   {k}: {v}")
    else:
        drift = compare_to_baseline()
        print("DRIFT DETECTED:" if drift else "No drift -- matches baseline.")
        for d in drift:
            print("  -", d)
    return BASELINE_PATH


if __name__ == "__main__":
    run("save")
