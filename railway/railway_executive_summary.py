"""
railway_executive_summary.py
============================
Executive KPI Layer -- converts analytical outputs into management-ready KPIs.

Answers: "What is the current inventory position of Southern Railway Signalling
Stores, and where should management focus first?"

READ-ONLY inputs (never modified):
    railway_sku_master.csv, railway_forecast.csv, railway_inventory_policy.csv,
    railway_data_quality.csv, railway_procurement_plan.csv

Outputs:
    outputs/executive_kpi_summary.csv          (flat Section|KPI|Value)
    outputs/executive_kpi_summary.json         (nested by section)
    outputs/powerbi/page0_executive_dashboard.csv
    outputs/executive_top10_procurement.csv
    outputs/executive_top10_inventory_value.csv
    outputs/executive_budget_scenario.csv

This is a pure aggregation/reporting layer -- Power BI only visualises it.
"""

from __future__ import annotations

import json

import numpy as np
import pandas as pd

from railway import railway_config as cfg
from railway.governance import division_summary as _ds   # STEP31 single source of truth

# === STEP31 REPORTING CUT-OVER (strangler) ====================================
# `railway.governance.division_summary` is now the SINGLE SOURCE OF TRUTH for the
# modern STEP1-28 KPI framework (L1/L2/L3) consumed by the rebuilt notebooks and
# the management summary. The legacy `build_kpis()` / `run()` below are DEPRECATED
# and retained ONLY for backward compatibility — they reproduce the byte-identical
# pinned `executive_*` / `page0_executive_dashboard` outputs. No modern KPI is
# computed twice: new/modern consumers MUST use the delegating accessors below.
# Physical removal of the legacy compute is deferred to repository purification.


def kpis(division: str | None = None) -> dict:
    """Modern STEP1-28 L1/L2/L3 KPIs (delegates to division_summary). Preferred over build_kpis()."""
    return _ds.compute_kpis(division)


def summary(division: str | None = None, write: bool = False) -> dict:
    """Modern division-aware management summary (delegates to division_summary)."""
    return _ds.build(division, write=write)
# ==============================================================================


def _to_py(v):
    """Cast numpy scalars to native python for JSON."""
    if isinstance(v, (np.integer,)):
        return int(v)
    if isinstance(v, (np.floating,)):
        return float(v)
    return v


def _round(v, n=2):
    try:
        return round(float(v), n)
    except (TypeError, ValueError):
        return v


def _concentration(value_series, top=10):
    s = pd.to_numeric(value_series, errors="coerce").replace([np.inf, -np.inf], np.nan).dropna()
    s = s.sort_values(ascending=False)
    total = float(s.sum())
    return (float(s.head(top).sum()) / total * 100.0) if total > 0 else 0.0


# ----------------------------------------------------------------------
# Load read-only inputs
# ----------------------------------------------------------------------
def _load():
    master = pd.read_csv(cfg.SKU_MASTER_CSV, dtype={"PL_Code": str})
    forecast = pd.read_csv(cfg.FORECAST_CSV, dtype={"PL_Code": str})
    policy = pd.read_csv(cfg.INVENTORY_POLICY_CSV, dtype={"PL_Code": str})
    dq = pd.read_csv(cfg.OUTPUT_DIR / "railway_data_quality.csv", dtype={"PL_Code": str})
    plan_path = cfg.OUTPUT_DIR / "railway_procurement_plan.csv"
    plan = pd.read_csv(plan_path, dtype={"PL_Code": str}) if plan_path.exists() else pd.DataFrame()
    return master, forecast, policy, dq, plan


# ----------------------------------------------------------------------
# Build KPI sections
# ----------------------------------------------------------------------
def build_kpis():
    master, forecast, policy, dq, plan = _load()

    crit_counts = master["Criticality"].value_counts()
    inv_by_crit = master.groupby("Criticality")["Inventory_Value"].sum()
    cov = pd.to_numeric(master["Inventory_Coverage_Ratio"], errors="coerce") \
        .replace([np.inf, -np.inf], np.nan)

    # ---- Section 1: Strategic inventory overview ----
    # Normalized strategic inventory value (per-km cable inflation removed) -- this is
    # the value the Executive dashboard must use, not the original Total_Inventory_Value.
    dq_strategic = pd.read_csv(cfg.OUTPUT_DIR / "railway_data_quality.csv", dtype={"PL_Code": str})
    s1 = {
        "Total_SKUs": int(len(master)),
        "Total_Inventory_Value": _round(master["Inventory_Value"].sum()),
        "Strategic_Inventory_Value_Normalized": _round(dq_strategic["Normalized_Inventory_Value"].sum()),
        "Total_Annual_Issue_Value": _round(master["Annual_Issue_Value"].sum()),
        "Total_Forecast_2026_27": _round(forecast["Forecast_2026_27"].sum()),
        "Total_Current_Stock": _round(master["Current_Stock"].sum()),
        "Average_Inventory_Coverage": _round(cov.mean(), 3),
    }

    # ---- Section 2: Criticality exposure (S->S1 Safety, V->S2 Vital) ----
    s2 = {
        "S1_Item_Count": int(crit_counts.get("S1", 0)),
        "S2_Item_Count": int(crit_counts.get("S2", 0)),
        "S3_Item_Count": int(crit_counts.get("S3", 0)),
        "S4_Item_Count": int(crit_counts.get("S4", 0)),
        "Safety_Item_Count": int(crit_counts.get("S1", 0)),   # raw 'S'
        "Vital_Item_Count": int(crit_counts.get("S2", 0)),    # raw 'V'
        "Inventory_Value_S1": _round(inv_by_crit.get("S1", 0.0)),
        "Inventory_Value_S2": _round(inv_by_crit.get("S2", 0.0)),
        "Inventory_Value_S3": _round(inv_by_crit.get("S3", 0.0)),
        "Inventory_Value_S4": _round(inv_by_crit.get("S4", 0.0)),
    }

    # ---- Section 3: Procurement exposure ----
    gap_pos = policy["Inventory_Gap"].clip(lower=0)
    s3 = {
        "Procurement_Required_Items": int((policy["Inventory_Status"] == "Procurement Required").sum()),
        "Sufficient_Items": int((policy["Inventory_Status"] == "Sufficient").sum()),
        "Total_Investment_Required": _round(policy["Inventory_Investment_Required"].sum()),
        "Total_Normalized_Investment_Required": _round(policy["Normalized_Investment_Required"].sum()),
        "Average_Inventory_Gap": _round(gap_pos.mean(), 2),
        "Maximum_Inventory_Gap": _round(policy["Inventory_Gap"].max(), 2),
    }

    # ---- Section 4: Forecasting ----
    dc = forecast["Demand_Class"].value_counts()
    fc = forecast["Forecast_Confidence"].value_counts()
    s4 = {
        "Smooth_Items": int(dc.get("Smooth", 0)),
        "Intermittent_Items": int(dc.get("Intermittent", 0)),
        "Erratic_Items": int(dc.get("Erratic", 0)),
        "Lumpy_Items": int(dc.get("Lumpy", 0)),
        "Dead_Items": int(dc.get("Dead", 0)),
        "High_Confidence_Forecasts": int(fc.get("High", 0)),
        "Medium_Confidence_Forecasts": int(fc.get("Medium", 0)),
        "Low_Confidence_Forecasts": int(fc.get("Low", 0)),
        "Very_Low_Confidence_Forecasts": int(fc.get("Very Low", 0)),
    }

    # ---- Section 5: Data quality ----
    orig_inv = float(dq["Inventory_Investment_Required"].sum())
    norm_inv = float(dq["Normalized_Investment_Required"].sum())
    orig_conc = _concentration(dq["Inventory_Value"])
    norm_conc = _concentration(dq["Normalized_Inventory_Value"])
    s5 = {
        "Flagged_SKUs": int((dq["Potential_Unit_Mismatch"] == "Yes").sum()),
        "Original_Investment_Required": _round(orig_inv),
        "Normalized_Investment_Required": _round(norm_inv),
        "Data_Quality_Impact": _round(orig_inv - norm_inv),
        "Original_Concentration_Index": _round(orig_conc, 2),
        "Normalized_Concentration_Index": _round(norm_conc, 2),
    }

    sections = {
        "Section1_Strategic_Inventory_Overview": s1,
        "Section2_Criticality_Exposure": s2,
        "Section3_Procurement_Exposure": s3,
        "Section4_Forecasting": s4,
        "Section5_Data_Quality": s5,
    }
    return sections, master, forecast, policy, plan


# ----------------------------------------------------------------------
# Top-10 tables & budget scenario
# ----------------------------------------------------------------------
def build_top10_procurement(policy: pd.DataFrame) -> pd.DataFrame:
    pr = policy[policy["Inventory_Status"] == "Procurement Required"] \
        .sort_values("Normalized_Procurement_Priority_Score", ascending=False).head(10).copy()
    pr.insert(0, "Rank", range(1, len(pr) + 1))
    return pr[["Rank", "PL_Code", "Description", "Criticality", "ABC_Class",
               "Current_Stock", "Inventory_Gap", "Normalized_Investment_Required",
               "Normalized_Procurement_Priority_Score"]]


def build_top10_value(master: pd.DataFrame) -> pd.DataFrame:
    iv = master.sort_values("Inventory_Value", ascending=False).head(10).copy()
    iv.insert(0, "Rank", range(1, len(iv) + 1))
    return iv[["Rank", "PL_Code", "Description", "Inventory_Value", "ABC_Class", "Criticality"]]


def build_budget_scenario(plan: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    budget = 1_00_00_000.0
    if plan.empty:
        return pd.DataFrame(), {}
    spent = float(plan["Inventory_Investment_Required"].sum())
    crit_mix = plan["Criticality"].value_counts().reindex(cfg.CRITICALITY_ORDER, fill_value=0)
    risk = float(plan["Procurement_Priority_Score"].sum())
    summary = {
        "Budget": budget,
        "Items_Funded": int(len(plan)),
        "Budget_Utilization_%": round(spent / budget * 100.0, 2),
        "Total_Risk_Reduction_Score": round(risk, 2),
        "Criticality_Mix_S1": int(crit_mix["S1"]),
        "Criticality_Mix_S2": int(crit_mix["S2"]),
        "Criticality_Mix_S3": int(crit_mix["S3"]),
        "Criticality_Mix_S4": int(crit_mix["S4"]),
    }
    return pd.DataFrame([summary]), summary


# ----------------------------------------------------------------------
# Management insights
# ----------------------------------------------------------------------
def build_insights(sections, policy):
    s1, s3, s5 = (sections["Section1_Strategic_Inventory_Overview"],
                  sections["Section3_Procurement_Exposure"],
                  sections["Section5_Data_Quality"])
    # S1 share of normalized procurement exposure
    norm_by_crit = policy.groupby("Criticality")["Normalized_Investment_Required"].sum()
    total_norm = float(norm_by_crit.sum())
    s1_share = (float(norm_by_crit.get("S1", 0.0)) / total_norm * 100.0) if total_norm > 0 else 0.0
    impact_cr = s5["Data_Quality_Impact"] / 1_00_00_000.0
    return {
        "Management_Insight_1": f"{s3['Procurement_Required_Items']} of {s1['Total_SKUs']} "
                                f"strategic signalling items require procurement.",
        "Management_Insight_2": f"S1 (track-safety) items account for {s1_share:.1f}% of "
                                f"normalized procurement exposure.",
        "Management_Insight_3": f"Only {s5['Flagged_SKUs']} data-quality anomalies inflated "
                                f"investment estimates by Rs {impact_cr:.0f} Cr.",
        "Management_Insight_4": f"Top 10 SKUs account for {s5['Normalized_Concentration_Index']:.0f}% "
                                f"of (unit-normalized) inventory value.",
    }


# ----------------------------------------------------------------------
# Flatten + write
# ----------------------------------------------------------------------
def _flatten(sections, insights):
    recs = []
    for sec, kpis in sections.items():
        for k, v in kpis.items():
            recs.append({"Section": sec, "KPI": k, "Value": _to_py(v)})
    for k, v in insights.items():
        recs.append({"Section": "Section_Management_Insights", "KPI": k, "Value": v})
    return pd.DataFrame(recs)


def run():
    cfg.ensure_output_dirs()
    sections, master, forecast, policy, plan = build_kpis()
    insights = build_insights(sections, policy)

    top10_proc = build_top10_procurement(policy)
    top10_val = build_top10_value(master)
    budget_df, budget_summary = build_budget_scenario(plan)

    flat = _flatten(sections, insights)

    # ---- write outputs ----
    flat.to_csv(cfg.OUTPUT_DIR / "executive_kpi_summary.csv", index=False)
    flat.to_csv(cfg.POWERBI_DIR / "page0_executive_dashboard.csv", index=False)
    top10_proc.to_csv(cfg.OUTPUT_DIR / "executive_top10_procurement.csv", index=False)
    top10_val.to_csv(cfg.OUTPUT_DIR / "executive_top10_inventory_value.csv", index=False)
    if not budget_df.empty:
        budget_df.to_csv(cfg.OUTPUT_DIR / "executive_budget_scenario.csv", index=False)

    payload = dict(sections)
    payload["Section_Management_Insights"] = insights
    payload["Section8_Budget_Scenario"] = budget_summary
    with open(cfg.OUTPUT_DIR / "executive_kpi_summary.json", "w") as f:
        json.dump(payload, f, indent=2, default=_to_py)

    # ---- validation gate ----
    expected_kpis = sum(len(v) for v in sections.values()) + len(insights)
    gate = {
        "no_missing_kpis": bool(flat["Value"].notna().all()) and len(flat) == expected_kpis,
        "no_duplicate_kpi_names": bool(flat["KPI"].is_unique),
        "dashboard_csv_written": (cfg.POWERBI_DIR / "page0_executive_dashboard.csv").exists(),
        "json_written": (cfg.OUTPUT_DIR / "executive_kpi_summary.json").exists(),
        "top10_files_written": (cfg.OUTPUT_DIR / "executive_top10_procurement.csv").exists()
                               and (cfg.OUTPUT_DIR / "executive_top10_inventory_value.csv").exists(),
        "budget_scenario_written": (cfg.OUTPUT_DIR / "executive_budget_scenario.csv").exists(),
    }

    # ---- report ----
    print("=" * 80)
    print("STEP 5A -- EXECUTIVE KPI LAYER -- validation")
    print("=" * 80)
    print("\n1. EXECUTIVE KPI SUMMARY")
    for sec, kpis in sections.items():
        print(f"\n  [{sec}]")
        for k, v in kpis.items():
            if isinstance(v, float) and abs(v) >= 1000:
                print(f"     {k:34s}: {v:,.2f}")
            else:
                print(f"     {k:34s}: {v}")

    print("\n2. TOP 10 PROCUREMENT ITEMS (Normalized priority):")
    print(top10_proc.to_string(index=False))
    print("\n3. TOP 10 INVENTORY VALUE ITEMS:")
    print(top10_val.to_string(index=False))

    s5 = sections["Section5_Data_Quality"]
    print("\n4. DATA QUALITY IMPACT:")
    print(f"     Flagged SKUs              : {s5['Flagged_SKUs']}")
    print(f"     Original Investment (Rs)  : {s5['Original_Investment_Required']:,.0f}")
    print(f"     Normalized Investment (Rs): {s5['Normalized_Investment_Required']:,.0f}")
    print(f"     Data Quality Impact (Rs)  : {s5['Data_Quality_Impact']:,.0f}")
    print(f"     Concentration (orig/norm) : {s5['Original_Concentration_Index']}% / "
          f"{s5['Normalized_Concentration_Index']}%")

    print("\n5. Rs 1 CRORE PROCUREMENT SCENARIO:")
    for k, v in budget_summary.items():
        print(f"     {k:28s}: {v}")

    print("\n6. MANAGEMENT INSIGHTS:")
    for k, v in insights.items():
        print(f"     - {v}")

    print("\n" + "-" * 80)
    print("VALIDATION GATE:")
    for k, v in gate.items():
        print(f"   {k:28s}: {v}")
    print(f"   ALL PASS: {all(gate.values())}")
    print("=" * 80)
    return sections, gate


if __name__ == "__main__":
    run()
