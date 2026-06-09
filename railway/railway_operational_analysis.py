"""
railway_operational_analysis.py
===============================
OPERATIONAL Inventory Pipeline -- answers "what is currently happening inside
the stores?" (aging, dead stock, slow-moving, valuation, depot health).

SOURCE: raw_data/Railway_Operations/<DIV>/SUMMARY OF STOCK HELD*.xlsx  ONLY
  (STEP37: per-division current-stock snapshots; the consolidated
   railway_stock_summary.xlsx is retired).
  * Loaded via the existing XML-based loader (railway_data_preparation.load_operational_stock).
  * NEVER joined with railways.xlsx -- strict source lineage preserved.

Reference date for aging: 2026-06-07 (the workbook extract date).

Outputs:
  outputs/railway_operational_inventory.csv          (main, 13 fields)
  outputs/operational_data_quality.csv               (DQ checks)
  outputs/operational_top50_dead_stock.csv
  outputs/operational_top50_slow_moving.csv
  outputs/operational_top50_value.csv
  outputs/operational_top50_zero_stock.csv
  outputs/powerbi/page1_operational_inventory.csv
  outputs/powerbi/page2_inventory_aging.csv
  outputs/powerbi/page3_dead_stock.csv
  outputs/powerbi/page4_inventory_value.csv
  outputs/powerbi/page5_operational_abc.csv
"""

from __future__ import annotations

from datetime import datetime, date

import numpy as np
import pandas as pd

from railway import railway_config as cfg
from railway import railway_data_preparation as dp

REFERENCE_DATE = date(2026, 6, 7)        # aging "today"

OPERATIONAL_FIELDS = [
    "PL_Code", "Description", "Current_Stock", "Unit", "Unit_Cost",
    "Inventory_Value", "Last_Receipt_Date", "Last_Issue_Date",
    "Days_Since_Movement", "Inventory_Aging_Class", "Movement_Status",
    "Inventory_Value_Band", "Depot",
]


# ----------------------------------------------------------------------
# classification helpers
# ----------------------------------------------------------------------
def _parse_dt(s):
    if not s or (isinstance(s, float) and pd.isna(s)):
        return None
    try:
        return datetime.strptime(str(s).strip(), "%d-%m-%Y").date()
    except ValueError:
        return None


def days_since_movement(receipt, issue):
    dts = [d for d in (_parse_dt(receipt), _parse_dt(issue)) if d is not None]
    if not dts:
        return None
    last = max(dts)
    return (REFERENCE_DATE - last).days


def aging_class(days):
    if days is None or (isinstance(days, float) and pd.isna(days)):
        return "Unknown"
    if days <= 90:
        return "Active"
    if days <= 180:
        return "Monitor"
    if days <= 365:
        return "Slow Moving"
    if days <= 730:
        return "Very Slow Moving"
    return "Dead Stock"


def movement_status(aging):
    if aging in ("Active", "Monitor"):
        return "Active"
    if aging in ("Slow Moving", "Very Slow Moving"):
        return "Slow Moving"
    if aging == "Dead Stock":
        return "Dead Stock"
    return "Unknown"


def value_band(v):
    v = 0.0 if (v is None or pd.isna(v)) else float(v)
    if v < 10_000:
        return "< Rs 10,000"
    if v < 1_00_000:
        return "Rs 10,000 - 1 Lakh"
    if v < 10_00_000:
        return "Rs 1 Lakh - 10 Lakh"
    if v < 1_00_00_000:
        return "Rs 10 Lakh - 1 Crore"
    return ">= Rs 1 Crore"


def operational_abc(df: pd.DataFrame) -> pd.Series:
    """Pareto ABC on Inventory_Value only: A<=70% cum, B<=90%, C rest."""
    order = df["Inventory_Value"].fillna(0).sort_values(ascending=False)
    total = float(order.sum())
    classes = {}
    cum = 0.0
    for idx, v in order.items():
        cum += float(v)
        frac = (cum / total) if total > 0 else 1.0
        classes[idx] = "A" if frac <= 0.70 else ("B" if frac <= 0.90 else "C")
    return pd.Series(classes).reindex(df.index)


# ----------------------------------------------------------------------
# main build
# ----------------------------------------------------------------------
def build_operational_inventory(write: bool = True) -> pd.DataFrame:
    df = dp.load_operational_stock()       # XML loader -- stock_summary ONLY

    df["Days_Since_Movement"] = [days_since_movement(r, i)
                                 for r, i in zip(df["Last_Receipt_Date"], df["Last_Issue_Date"])]
    df["Inventory_Aging_Class"] = df["Days_Since_Movement"].apply(aging_class)
    df["Movement_Status"] = df["Inventory_Aging_Class"].apply(movement_status)
    df["Inventory_Value_Band"] = df["Inventory_Value"].apply(value_band)
    df["Operational_ABC"] = operational_abc(df)

    out = df[OPERATIONAL_FIELDS].copy()
    if write:
        cfg.ensure_output_dirs()
        out.to_csv(cfg.OUTPUT_DIR / "railway_operational_inventory.csv", index=False)
    return df          # full frame (incl Operational_ABC) for downstream aggregates


# ----------------------------------------------------------------------
# KPIs
# ----------------------------------------------------------------------
def operational_kpis(df: pd.DataFrame) -> dict:
    val = df["Inventory_Value"].fillna(0)
    total = float(val.sum())
    dead = float(val[df["Movement_Status"] == "Dead Stock"].sum())
    slow = float(val[df["Movement_Status"] == "Slow Moving"].sum())
    active = float(val[df["Movement_Status"] == "Active"].sum())
    pct = lambda x: round(x / total * 100.0, 2) if total > 0 else 0.0
    return {
        "Total_Operational_Inventory_Value": round(total, 2),
        "Dead_Stock_Value": round(dead, 2),
        "Slow_Moving_Value": round(slow, 2),
        "Active_Inventory_Value": round(active, 2),
        "Dead_Stock_Pct": pct(dead),
        "Slow_Moving_Pct": pct(slow),
        "Inventory_Turn_Risk_Pct": pct(dead + slow),
    }


# ----------------------------------------------------------------------
# data quality checks
# ----------------------------------------------------------------------
def data_quality_checks(df: pd.DataFrame) -> pd.DataFrame:
    checks = [
        ("Duplicate PL Codes", int(df["PL_Code"].duplicated().sum())),
        ("Negative Stock", int((df["Current_Stock"].fillna(0) < 0).sum())),
        ("Negative Value", int((df["Inventory_Value"].fillna(0) < 0).sum())),
        ("Missing Dates (no movement)", int(df["Days_Since_Movement"].isna().sum())),
        ("Missing Description", int((df["Description"].fillna("").str.strip() == "").sum())),
        ("Missing Unit", int((df["Unit"].fillna("").str.strip() == "").sum())),
    ]
    return pd.DataFrame(checks, columns=["Check", "Count"])


# ----------------------------------------------------------------------
# Power BI pages + top lists
# ----------------------------------------------------------------------
def _agg(df, by):
    g = df.groupby(by).agg(Count=("PL_Code", "size"),
                           Inventory_Value=("Inventory_Value", "sum")).reset_index()
    g["Inventory_Value"] = g["Inventory_Value"].round(2)
    return g


def write_powerbi_and_tops(df: pd.DataFrame):
    cfg.ensure_output_dirs()
    pbi = cfg.POWERBI_DIR
    out = cfg.OUTPUT_DIR

    # op_inventory_summary: full operational detail (incl Operational_ABC)
    df[OPERATIONAL_FIELDS + ["Operational_ABC"]].to_csv(pbi / "op_inventory_summary.csv", index=False)
    # op_inventory_aging
    aging_order = ["Active", "Monitor", "Slow Moving", "Very Slow Moving", "Dead Stock", "Unknown"]
    a = _agg(df, "Inventory_Aging_Class").set_index("Inventory_Aging_Class").reindex(aging_order).fillna(0).reset_index()
    a.to_csv(pbi / "op_inventory_aging.csv", index=False)
    # op_dead_stock detail
    dead = df[df["Movement_Status"] == "Dead Stock"].sort_values("Inventory_Value", ascending=False)
    dead[["PL_Code", "Description", "Current_Stock", "Inventory_Value",
          "Days_Since_Movement", "Depot"]].to_csv(pbi / "op_dead_stock.csv", index=False)
    # op_inventory_value bands
    band_order = ["< Rs 10,000", "Rs 10,000 - 1 Lakh", "Rs 1 Lakh - 10 Lakh",
                  "Rs 10 Lakh - 1 Crore", ">= Rs 1 Crore"]
    b = _agg(df, "Inventory_Value_Band").set_index("Inventory_Value_Band").reindex(band_order).fillna(0).reset_index()
    b.to_csv(pbi / "op_inventory_value.csv", index=False)
    # op_operational_abc
    ab = _agg(df, "Operational_ABC").set_index("Operational_ABC").reindex(["A", "B", "C"]).fillna(0).reset_index()
    tot = ab["Inventory_Value"].sum()
    ab["Value_Pct"] = (ab["Inventory_Value"] / tot * 100).round(2) if tot > 0 else 0
    ab.to_csv(pbi / "op_operational_abc.csv", index=False)

    # top-50 lists
    cols = ["PL_Code", "Description", "Current_Stock", "Inventory_Value",
            "Days_Since_Movement", "Inventory_Aging_Class", "Depot"]
    df[df["Movement_Status"] == "Dead Stock"].sort_values("Inventory_Value", ascending=False) \
        .head(50)[cols].to_csv(out / "operational_top50_dead_stock.csv", index=False)
    df[df["Movement_Status"] == "Slow Moving"].sort_values("Inventory_Value", ascending=False) \
        .head(50)[cols].to_csv(out / "operational_top50_slow_moving.csv", index=False)
    df.sort_values("Inventory_Value", ascending=False) \
        .head(50)[cols].to_csv(out / "operational_top50_value.csv", index=False)
    df[df["Current_Stock"].fillna(0) == 0].sort_values("Days_Since_Movement", ascending=False, na_position="last") \
        .head(50)[cols].to_csv(out / "operational_top50_zero_stock.csv", index=False)


# ----------------------------------------------------------------------
# Validation / run
# ----------------------------------------------------------------------
def run():
    df = build_operational_inventory(write=True)
    kpis = operational_kpis(df)
    dq = data_quality_checks(df)
    dq.to_csv(cfg.OUTPUT_DIR / "operational_data_quality.csv", index=False)
    write_powerbi_and_tops(df)

    print("=" * 80)
    print("STEP 6 -- OPERATIONAL INVENTORY PIPELINE (per-division SUMMARY OF STOCK HELD)")
    print("=" * 80)
    print(f"Rows: {len(df)}   Reference date: {REFERENCE_DATE}")

    print("\n--- Inventory_Aging_Class distribution ---")
    print(df["Inventory_Aging_Class"].value_counts().to_dict())
    print("--- Movement_Status distribution ---")
    print(df["Movement_Status"].value_counts().to_dict())
    print("--- Operational_ABC distribution (count) ---")
    print(df["Operational_ABC"].value_counts().reindex(["A", "B", "C"]).to_dict())

    print("\n--- Top 20 DEAD STOCK items (by Inventory_Value) ---")
    c = ["PL_Code", "Description", "Current_Stock", "Inventory_Value", "Days_Since_Movement"]
    dead = df[df["Movement_Status"] == "Dead Stock"].sort_values("Inventory_Value", ascending=False)
    with pd.option_context("display.width", 220, "display.max_colwidth", 42):
        print(dead.head(20)[c].to_string(index=False))

    print("\n--- Top 20 HIGHEST Inventory Value items ---")
    with pd.option_context("display.width", 220, "display.max_colwidth", 42):
        print(df.sort_values("Inventory_Value", ascending=False).head(20)[c].to_string(index=False))

    print("\n--- OPERATIONAL KPIs ---")
    for k, v in kpis.items():
        print(f"   {k:36s}: {v:,.2f}" if isinstance(v, float) else f"   {k:36s}: {v}")

    print("\n--- DATA QUALITY CHECKS ---")
    print(dq.to_string(index=False))

    print("\n--- MANAGEMENT QUESTIONS ---")
    n_dead = int((df["Movement_Status"] == "Dead Stock").sum())
    n_2yr = int((df["Days_Since_Movement"].fillna(-1) > 730).sum())
    print(f"   1. Dead stock: {n_dead} items worth Rs {kpis['Dead_Stock_Value']:,.0f} "
          f"({kpis['Dead_Stock_Pct']}% of value).")
    print(f"   2. Not moved 2+ years (>730d): {n_2yr} items.")
    print(f"   3. Space-without-benefit: {n_dead} dead + "
          f"{int((df['Movement_Status']=='Slow Moving').sum())} slow-moving items.")
    print(f"   4. Value domination: Operational ABC 'A' holds "
          f"{df.loc[df['Operational_ABC']=='A','Inventory_Value'].sum()/df['Inventory_Value'].sum()*100:.1f}% of value.")
    print(f"   5. Disposal review: see operational_top50_dead_stock.csv ({n_dead} candidates).")
    print(f"   6. Monthly KPIs: Dead Stock %, Slow Moving %, Inventory Turn Risk % "
          f"(= {kpis['Inventory_Turn_Risk_Pct']}%).")

    # validation gate
    gate = {
        "rows_loaded": len(df) > 0,
        "no_duplicate_pl": bool(df["PL_Code"].is_unique),
        "no_negative_stock": bool((df["Current_Stock"].fillna(0) >= 0).all()),
        "no_negative_value": bool((df["Inventory_Value"].fillna(0) >= 0).all()),
        "main_csv_written": (cfg.OUTPUT_DIR / "railway_operational_inventory.csv").exists(),
        "powerbi_pages_written": all((cfg.POWERBI_DIR / f"{n}.csv").exists()
                                     for n in ["op_inventory_summary", "op_inventory_aging",
                                               "op_dead_stock", "op_inventory_value",
                                               "op_operational_abc"]),
        "dq_csv_written": (cfg.OUTPUT_DIR / "operational_data_quality.csv").exists(),
    }
    print("\n" + "-" * 80)
    print("VALIDATION GATE:")
    for k, v in gate.items():
        print(f"   {k:28s}: {v}")
    print(f"   ALL PASS: {all(gate.values())}")
    print("=" * 80)
    return df, gate


if __name__ == "__main__":
    run()
