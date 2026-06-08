"""
schema_validation.py
====================
Fail-fast schema & integrity validation for the railway outputs. Designed to
catch silent data drift before it reaches Power BI / AnyLogistix as the platform
scales from 59 -> 907 -> N rows.

Checks: required columns present, numeric types coercible, no duplicate PL codes,
no negative inventory / forecast / safety stock, valid Criticality / ABC vocab.

Usage:
    from railway import schema_validation as sv
    sv.validate_all()          # raises SchemaError on first violation
    sv.validate_all(raise_on_error=False)  # returns list of violations
"""

from __future__ import annotations

import pandas as pd

from railway import railway_config as cfg


class SchemaError(Exception):
    pass


# file -> required columns (subset that must always exist)
REQUIRED_COLUMNS = {
    "railway_demand_history.csv": ["PL_Code", "AAC", "EAR_Qty", "Unit_Cost"],
    "railway_sku_master.csv": ["PL_Code", "ABC_Class", "Criticality", "Annual_Issue_Value",
                               "Demand_Class", "Inventory_Coverage_Ratio"],
    "railway_forecast.csv": ["PL_Code", "Forecast_2026_27", "Recommended_Model",
                             "Forecast_Confidence", "Demand_Class"],
    "railway_inventory_policy.csv": ["PL_Code", "Criticality", "ABC_Class", "Safety_Stock",
                                     "ROP", "Lead_Time_Months", "Inventory_Status"],
    "railway_operational_inventory.csv": ["PL_Code", "Current_Stock", "Inventory_Value",
                                          "Movement_Status", "Inventory_Aging_Class"],
}


def _load(name):
    return pd.read_csv(cfg.OUTPUT_DIR / name, dtype={"PL_Code": str})


def _check_columns(name, df, violations):
    for col in REQUIRED_COLUMNS[name]:
        if col not in df.columns:
            violations.append(f"{name}: missing required column '{col}'")


def _check_numeric(name, df, cols, violations, allow_negative=False):
    for col in cols:
        if col not in df.columns:
            continue
        s = pd.to_numeric(df[col], errors="coerce")
        # NaN allowed (sparse data), but non-coercible strings are not
        bad = df[col].notna() & s.isna()
        if bad.any():
            violations.append(f"{name}: column '{col}' has {int(bad.sum())} non-numeric values")
        if not allow_negative and (s.dropna() < 0).any():
            violations.append(f"{name}: column '{col}' has negative values")


def _check_no_nulls(name, df, cols, violations):
    """Range/presence: listed columns must have no null values."""
    for col in cols:
        if col in df.columns and df[col].isna().any():
            violations.append(f"{name}: column '{col}' has {int(df[col].isna().sum())} null value(s)")


def _check_duplicates(name, df, violations, key="PL_Code"):
    """Integrity: the primary key must be unique."""
    if key in df.columns and df[key].duplicated().any():
        violations.append(f"{name}: {int(df[key].duplicated().sum())} duplicate {key} value(s)")


def _check_range(name, df, col, lo, hi, violations):
    """Range: numeric column must lie strictly inside (lo, hi)."""
    if col not in df.columns:
        return
    s = pd.to_numeric(df[col], errors="coerce").dropna()
    bad = (s <= lo) | (s >= hi)
    if bad.any():
        violations.append(f"{name}: column '{col}' has {int(bad.sum())} value(s) outside ({lo}, {hi})")


def validate_all(raise_on_error=True):
    violations = []

    # --- demand history ---
    dh = _load("railway_demand_history.csv")
    _check_columns("railway_demand_history.csv", dh, violations)
    if dh["PL_Code"].duplicated().any():
        violations.append("railway_demand_history.csv: duplicate PL_Code")
    _check_numeric("railway_demand_history.csv", dh, ["Current_Stock", "Unit_Cost", "AAC", "EAR_Qty"], violations)

    # --- sku master ---
    sm = _load("railway_sku_master.csv")
    _check_columns("railway_sku_master.csv", sm, violations)
    _check_duplicates("railway_sku_master.csv", sm, violations)
    _check_no_nulls("railway_sku_master.csv", sm, ["Criticality", "ABC_Class"], violations)
    bad_abc = set(sm["ABC_Class"].dropna().unique()) - cfg.VALID_ABC_CLASSES
    if bad_abc:
        violations.append(f"railway_sku_master.csv: invalid ABC class(es) {bad_abc}")
    bad_crit = set(sm["Criticality"].dropna().unique()) - cfg.VALID_CRITICALITY
    if bad_crit:
        violations.append(f"railway_sku_master.csv: invalid Criticality {bad_crit}")
    bad_dc = set(sm["Demand_Class"].dropna().unique()) - cfg.VALID_DEMAND_CLASSES
    if bad_dc:
        violations.append(f"railway_sku_master.csv: invalid Demand_Class {bad_dc}")

    # --- forecast ---
    fc = _load("railway_forecast.csv")
    _check_columns("railway_forecast.csv", fc, violations)
    _check_duplicates("railway_forecast.csv", fc, violations)
    _check_numeric("railway_forecast.csv", fc, ["Forecast_2026_27"], violations)   # no negative forecast
    bad_conf = set(fc["Forecast_Confidence"].dropna().unique()) - cfg.VALID_FORECAST_CONFIDENCE
    if bad_conf:
        violations.append(f"railway_forecast.csv: invalid Forecast_Confidence {bad_conf}")

    # --- inventory policy ---
    pol = _load("railway_inventory_policy.csv")
    _check_columns("railway_inventory_policy.csv", pol, violations)
    _check_duplicates("railway_inventory_policy.csv", pol, violations)
    _check_no_nulls("railway_inventory_policy.csv", pol, ["Criticality"], violations)
    # non-negative: safety stock, ROP, lead time, investment, positive-gap, SRRS
    _check_numeric("railway_inventory_policy.csv", pol,
                   ["Safety_Stock", "ROP", "Lead_Time_Months", "Inventory_Investment_Required"],
                   violations)
    if "Positive_Gap" in pol.columns:
        _check_numeric("railway_inventory_policy.csv", pol,
                       ["Positive_Gap", "Service_Risk_Reduction_Score"], violations)
    # service level must be a probability strictly inside (0, 1)
    _check_range("railway_inventory_policy.csv", pol, "Target_Service_Level", 0.0, 1.0, violations)
    bad_status = set(pol["Inventory_Status"].dropna().unique()) - cfg.VALID_INVENTORY_STATUS
    if bad_status:
        violations.append(f"railway_inventory_policy.csv: invalid Inventory_Status {bad_status}")

    # --- operational ---
    op = _load("railway_operational_inventory.csv")
    _check_columns("railway_operational_inventory.csv", op, violations)
    _check_duplicates("railway_operational_inventory.csv", op, violations)
    _check_numeric("railway_operational_inventory.csv", op, ["Current_Stock", "Inventory_Value"], violations)

    if raise_on_error and violations:
        raise SchemaError("Schema validation failed:\n  - " + "\n  - ".join(violations))
    return violations


if __name__ == "__main__":
    v = validate_all(raise_on_error=False)
    if v:
        print("VIOLATIONS:")
        for x in v:
            print("  -", x)
    else:
        print("Schema validation: ALL CHECKS PASSED")
