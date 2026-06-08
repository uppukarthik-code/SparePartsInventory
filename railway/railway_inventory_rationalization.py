"""
railway_inventory_rationalization.py
====================================
READ-ONLY rationalization layer. Does NOT modify any existing output.

Combines the STRATEGIC view (criticality + procurement status, from railways.xlsx
outputs) with the OPERATIONAL view (movement status, from stock_summary outputs)
into a unified asset register, and assigns each PL code an Inventory_Action:

    Procure Immediately | Retain | Monitor | Rationalize | Dispose

The two domains overlap on only ~7 PL codes, so this is an OUTER merge by
PL_Code -- a derived analytical view, NOT a merged source table. Sources remain
untouched and independently traceable.

Inputs (read-only):
    railway_sku_master.csv            (Criticality, Inventory_Value)
    railway_inventory_policy.csv      (Inventory_Status)
    railway_operational_inventory.csv (Movement_Status, Inventory_Value)

Output:
    outputs/railway_inventory_rationalization.csv
    outputs/railway_rationalization_summary.csv   (executive: count + value per action)
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from railway import railway_config as cfg

RATIONALIZATION_FIELDS = [
    "PL_Code", "Description", "Criticality", "Inventory_Status",
    "Movement_Status", "Inventory_Action", "Inventory_Value", "Source_Universe",
]
ACTION_ORDER = ["Procure Immediately", "Retain", "Monitor", "Rationalize", "Dispose"]


# ----------------------------------------------------------------------
# rule engine
# ----------------------------------------------------------------------
def assign_action(criticality, inv_status, movement) -> str:
    """Locked 5-rule matrix (priority order) + documented fallbacks.

    Verbatim rules:
        S1/S2 & Procurement Required -> Procure Immediately
        S1/S2 & Sufficient           -> Retain
        S3    & Slow Moving          -> Monitor
        S4    & Slow Moving          -> Rationalize
        Dead Stock                   -> Dispose
    Fallbacks (for items lacking the dimension the rule needs):
        Slow Moving (no criticality) -> Rationalize
        Active                       -> Retain
        otherwise                    -> Monitor
    """
    crit = (criticality or "") if isinstance(criticality, str) else ""
    status = (inv_status or "") if isinstance(inv_status, str) else ""
    move = (movement or "") if isinstance(movement, str) else ""

    # --- verbatim rules ---
    if crit in ("S1", "S2") and status == "Procurement Required":
        return "Procure Immediately"
    if crit in ("S1", "S2") and status == "Sufficient":
        return "Retain"
    if crit == "S3" and move == "Slow Moving":
        return "Monitor"
    if crit == "S4" and move == "Slow Moving":
        return "Rationalize"
    if move == "Dead Stock":
        return "Dispose"
    # --- documented fallbacks ---
    if move == "Slow Moving":
        return "Rationalize"
    if move == "Active":
        return "Retain"
    return "Monitor"


# ----------------------------------------------------------------------
# build
# ----------------------------------------------------------------------
def build_rationalization(write: bool = True):
    # Strategic value is the NORMALIZED inventory value (Fix Group A: strategic rows
    # must not use the per-km-inflated original value).
    dq = pd.read_csv(cfg.OUTPUT_DIR / "railway_data_quality.csv", dtype={"PL_Code": str})[
        ["PL_Code", "Normalized_Inventory_Value"]
    ].rename(columns={"Normalized_Inventory_Value": "Value_strat"})

    master = pd.read_csv(cfg.SKU_MASTER_CSV, dtype={"PL_Code": str})[
        ["PL_Code", "Description", "Criticality"]
    ].rename(columns={"Description": "Description_strat"}).merge(dq, on="PL_Code", how="left")

    policy = pd.read_csv(cfg.INVENTORY_POLICY_CSV, dtype={"PL_Code": str})[
        ["PL_Code", "Inventory_Status"]
    ]

    op = pd.read_csv(cfg.OUTPUT_DIR / "railway_operational_inventory.csv", dtype={"PL_Code": str})[
        ["PL_Code", "Description", "Movement_Status", "Inventory_Value"]
    ].rename(columns={"Description": "Description_op", "Inventory_Value": "Value_op"})

    # outer merge -> unified asset register (derived view only)
    df = master.merge(policy, on="PL_Code", how="outer").merge(op, on="PL_Code", how="outer")

    # coalesce description (strategic first); value = operational (physical) for
    # operational rows, else NORMALIZED strategic value. Tag the source universe so
    # strategic and operational value are never silently summed together (Fix Group C).
    df["Description"] = df["Description_strat"].fillna(df["Description_op"]).fillna("")
    df["Source_Universe"] = np.where(df["Value_op"].notna(), "Operational", "Strategic")
    df["Inventory_Value"] = df["Value_op"].fillna(df["Value_strat"]).fillna(0.0).round(2)

    df["Inventory_Action"] = [
        assign_action(c, s, m)
        for c, s, m in zip(df["Criticality"], df["Inventory_Status"], df["Movement_Status"])
    ]

    out = df[RATIONALIZATION_FIELDS].copy()
    if write:
        cfg.ensure_output_dirs()
        out.to_csv(cfg.OUTPUT_DIR / "railway_inventory_rationalization.csv", index=False)
    return out


def executive_summary(out: pd.DataFrame, write: bool = True) -> pd.DataFrame:
    g = out.groupby("Inventory_Action").agg(
        Count=("PL_Code", "size"),
        Inventory_Value=("Inventory_Value", "sum")).reindex(ACTION_ORDER).fillna(0).reset_index()
    g["Count"] = g["Count"].astype(int)
    g["Inventory_Value"] = g["Inventory_Value"].round(2)
    if write:
        g.to_csv(cfg.OUTPUT_DIR / "railway_rationalization_summary.csv", index=False)
    return g


# ----------------------------------------------------------------------
# validation / run
# ----------------------------------------------------------------------
def run():
    out = build_rationalization(write=True)
    summary = executive_summary(out, write=True)

    print("=" * 80)
    print("STEP 6A -- INVENTORY RATIONALIZATION (read-only, strategic + operational)")
    print("=" * 80)
    print(f"Unified asset register rows: {len(out)}  "
          f"(strategic 59 + operational 907, ~7 overlapping PL codes)")

    print("\n--- Distribution of Inventory_Action ---")
    print(out["Inventory_Action"].value_counts().reindex(ACTION_ORDER).to_dict())

    print("\n--- Inventory Value by Inventory_Action ---")
    for _, r in summary.iterrows():
        print(f"   {r['Inventory_Action']:22s}: {r['Count']:4d} items  "
              f"Rs {r['Inventory_Value']:,.0f}")

    print("\n--- Top 20 DISPOSAL candidates (by Inventory_Value) ---")
    disp = out[out["Inventory_Action"] == "Dispose"].sort_values("Inventory_Value", ascending=False)
    with pd.option_context("display.width", 200, "display.max_colwidth", 50):
        print(disp.head(20)[["PL_Code", "Description", "Movement_Status", "Inventory_Value"]].to_string(index=False))

    print("\n--- Top 20 RATIONALIZATION candidates (by Inventory_Value) ---")
    rat = out[out["Inventory_Action"] == "Rationalize"].sort_values("Inventory_Value", ascending=False)
    with pd.option_context("display.width", 200, "display.max_colwidth", 50):
        print(rat.head(20)[["PL_Code", "Description", "Movement_Status", "Inventory_Value"]].to_string(index=False))

    print("\n--- MANAGEMENT ANSWER (12-month inventory-health plan) ---")
    sd = summary.set_index("Inventory_Action")
    print(f"   Procure   : {int(sd.loc['Procure Immediately','Count'])} vital items short of ROP "
          f"(Rs {sd.loc['Procure Immediately','Inventory_Value']:,.0f}).")
    print(f"   Retain    : {int(sd.loc['Retain','Count'])} healthy/active items "
          f"(Rs {sd.loc['Retain','Inventory_Value']:,.0f}).")
    print(f"   Review    : {int(sd.loc['Monitor','Count'])} items to monitor "
          f"(Rs {sd.loc['Monitor','Inventory_Value']:,.0f}).")
    print(f"   Rationalize: {int(sd.loc['Rationalize','Count'])} slow-movers to right-size "
          f"(Rs {sd.loc['Rationalize','Inventory_Value']:,.0f}).")
    print(f"   Dispose   : {int(sd.loc['Dispose','Count'])} dead-stock items for disposal review "
          f"(Rs {sd.loc['Dispose','Inventory_Value']:,.0f}).")

    # validation gate
    gate = {
        "rows_present": len(out) > 0,
        "all_actions_assigned": bool(out["Inventory_Action"].isin(ACTION_ORDER).all()),
        "no_null_action": bool(out["Inventory_Action"].notna().all()),
        "main_csv_written": (cfg.OUTPUT_DIR / "railway_inventory_rationalization.csv").exists(),
        "summary_csv_written": (cfg.OUTPUT_DIR / "railway_rationalization_summary.csv").exists(),
    }
    print("\n" + "-" * 80)
    print("VALIDATION GATE:")
    for k, v in gate.items():
        print(f"   {k:24s}: {v}")
    print(f"   ALL PASS: {all(gate.values())}")
    print("=" * 80)
    return out, gate


if __name__ == "__main__":
    run()
