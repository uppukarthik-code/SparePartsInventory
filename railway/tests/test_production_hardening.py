"""
test_production_hardening.py
============================
STEP 17 automated production-hardening tests:
  * schema tests
  * row-count tests
  * total-preservation tests
  * ranking-stability tests
  * Power BI compatibility tests

Run:  pytest railway/tests/test_production_hardening.py -q
All tests are read-only and assert the frozen-methodology invariants.
"""

from __future__ import annotations

import json

import pandas as pd
import pytest

from railway import railway_config as cfg
from railway import schema_validation as sv

OUT = cfg.OUTPUT_DIR
PBI = cfg.POWERBI_DIR
TOL = 1e-6

EXPECTED_ROWS = {
    "page1_procurement": 59, "page2_forecasting": 59, "page3_criticality": 59,
    "page4_operational_health": 15913, "page5_rationalization": 5351,  # operational-volume counts pinned to current committed outputs (grew with multi-depot onboarding STEP18A)
    "page8_budget_scenarios": 4, "page9_management_actions": 5,
}
PAGES = [f"page{i}_{n}" for i, n in enumerate([
    "executive_dashboard", "procurement", "forecasting", "criticality",
    "operational_health", "rationalization", "data_quality",
    "abc_criticality_matrix", "budget_scenarios", "management_actions"])]
FORBIDDEN = ["Inventory_Value", "Inventory_Investment_Required", "Procurement_Priority_Score"]
ALIAS_EXEMPT = {"page4_operational_health", "page5_rationalization"}


def _read(name, sub=True):
    return pd.read_csv((PBI if sub else OUT) / name, dtype={"PL_Code": str})


# ---------------------------------------------------------------- schema
def test_schema_validation_passes():
    assert sv.validate_all(raise_on_error=False) == []


def test_policy_has_srrs_and_explainability_columns():
    pol = _read("railway_inventory_policy.csv", sub=False)
    for c in ["Service_Factor", "Positive_Gap", "Service_Risk_Reduction_Score",
              "SRRS_Rank", "SRRS_Per_Rupee", "Funding_Driver"]:
        assert c in pol.columns, f"policy missing {c}"


# ---------------------------------------------------------------- row counts
@pytest.mark.parametrize("page,n", EXPECTED_ROWS.items())
def test_row_counts_unchanged(page, n):
    assert len(_read(f"{page}.csv")) == n


def test_policy_row_count():
    assert len(_read("railway_inventory_policy.csv", sub=False)) == 59


# ---------------------------------------------------------------- totals preserved
def test_procurement_total_equals_policy():
    pol = _read("railway_inventory_policy.csv", sub=False)
    p0 = _read("page0_executive_dashboard.csv").set_index("KPI")["Value"].to_dict()
    assert abs(float(p0["Procurement Required Value"])
               - float(pol["Normalized_Investment_Required"].sum())) <= 1.0


def test_strategic_value_reconciles():
    p0 = _read("page0_executive_dashboard.csv").set_index("KPI")["Value"].to_dict()
    p7 = _read("page7_abc_criticality_matrix.csv")
    a = float(p0["Strategic Inventory Value (Normalized)"])
    b = float(p7["Normalized_Inventory_Value"].sum())
    assert abs(a - b) / abs(b) <= 1e-3


# ---------------------------------------------------------------- ranking stability
def test_srrs_identity():
    pol = _read("railway_inventory_policy.csv", sub=False)
    lhs = pol["Service_Risk_Reduction_Score"]
    rhs = pol["Criticality_Weight"] * pol["Service_Factor"] * pol["Inventory_Gap"].clip(lower=0)
    assert float((lhs - rhs).abs().max()) < 1e-2


def test_srrs_rank_consistent_with_score():
    pol = _read("railway_inventory_policy.csv", sub=False)
    ordered = pol.sort_values("SRRS_Rank")["Service_Risk_Reduction_Score"].values
    assert all(ordered[i] >= ordered[i + 1] - 1e-9 for i in range(len(ordered) - 1))


def test_plan_items_are_procurement_required_and_within_budget():
    plan = _read("railway_procurement_plan.csv", sub=False)
    pol = _read("railway_inventory_policy.csv", sub=False)
    req = set(pol[pol["Inventory_Status"] == "Procurement Required"]["PL_Code"])
    assert set(plan["PL_Code"]).issubset(req)
    assert float(plan["Inventory_Investment_Required"].sum()) <= cfg.PROCUREMENT_BUDGET + 1e-3


# ---------------------------------------------------------------- Power BI compatibility
@pytest.mark.parametrize("page", PAGES)
def test_all_pages_exist(page):
    assert (PBI / f"{page}.csv").exists()


def test_no_forbidden_raw_columns_on_strategic_pages():
    for page in PAGES:
        if page in ALIAS_EXEMPT:
            continue
        cols = pd.read_csv(PBI / f"{page}.csv", nrows=0).columns
        hits = [c for c in FORBIDDEN if c in cols]
        assert not hits, f"{page} carries forbidden raw column(s) {hits}"


def test_compatibility_columns_present():
    for page in ["page1_procurement", "page3_criticality",
                 "page4_operational_health", "page5_rationalization"]:
        assert "Description" in pd.read_csv(PBI / f"{page}.csv", nrows=0).columns
    for page in ["page1_procurement", "page3_criticality"]:
        assert "Criticality_Name" in pd.read_csv(PBI / f"{page}.csv", nrows=0).columns


# ---------------------------------------------------------------- golden invariance (optional)
def test_golden_manifest_if_present():
    """If a STEP17 baseline manifest exists, every baseline file must be byte-identical."""
    import hashlib
    manifest = OUT / ".step17_baseline" / "MANIFEST.json"
    if not manifest.exists():
        pytest.skip("no baseline manifest present")
    golden = json.loads(manifest.read_text())
    mismatched = []
    for rel, h in golden.items():
        p = OUT / rel
        if not p.exists() or hashlib.sha256(p.read_bytes()).hexdigest() != h:
            mismatched.append(rel)
    assert not mismatched, f"changed vs baseline: {mismatched}"
