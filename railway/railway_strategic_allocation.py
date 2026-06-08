"""
railway_strategic_allocation.py
===============================
STEP 19 -- Strategic Inventory Allocation Framework (additive; strategic layer only).

Converts the strategic inventory universe from a ZONE-LEVEL SHARED model (every
Business Unit inheriting the full 59-item zone stock by default) to a
BUSINESS-UNIT ALLOCATED model, using the per-store-depot stock columns already
present in railways.xlsx ('Stock as on 31.03.2026').

Allocation rule (verified in STEP19, configuration-driven via
`cfg.STRATEGIC_DEPOT_TO_BU`):

    GSD/PER -> MAS   GSD/ED  -> SA    LSD/MDU -> MDU
    DSD/QLN -> TVC   GSD/GOC -> TPJ   SSD/PTJ -> PGT   (Podanur / Palakkad)

Each strategic depot column is allocated to exactly one Business Unit, so the
sum of all per-BU strategic stock equals the original depot-column total
(conservation). Allocation is BY DEPOT COLUMN (the per-location source of truth);
where a PL's TOTAL column disagrees with its depot sum (a source data-entry
error) the depot columns win and the discrepancy is reported, not silently
reconciled.

DESIGN CONTRACT -- this module DOES NOT touch:
    operational analytics, forecasting, ROP/optimization, SRRS, procurement.
It only reads the strategic stock sheet (read-only) and emits a new allocation
artefact + helper aggregates consumed by the enterprise layer.

Output: <output>/strategic_inventory_allocation.csv
    PL_Code, Description, Business_Unit, Strategic_Stock,
    Allocation_Source, Source_Depot_Column
"""

from __future__ import annotations

import pandas as pd

from railway import railway_config as cfg
from railway import railway_business_unit_config as buc
from railway import railway_data_preparation as dp

ALLOCATION_FIELDS = [
    "PL_Code", "Description", "Business_Unit",
    "Strategic_Stock", "Allocation_Source", "Source_Depot_Column",
]
ALLOCATION_SOURCE = "Depot_Column_Allocation"


# ----------------------------------------------------------------------
# Core allocation (global, all Business Units)
# ----------------------------------------------------------------------
def allocate() -> pd.DataFrame:
    """Allocate every strategic PL's stock across Business Units by depot column.

    Returns one row per (PL_Code, Business_Unit) where that BU's depot column
    holds non-zero stock. Conserves total stock (Sum per-BU == Sum depot columns).
    """
    strat = dp.load_strategic_stock()
    rows = []
    for _, r in strat.iterrows():
        pl = r["PL_Code"]
        desc = r.get("Description", "")
        for depot, bu in cfg.STRATEGIC_DEPOT_TO_BU.items():
            qty = r.get(f"stock_{depot}")
            if qty is None or pd.isna(qty) or float(qty) == 0.0:
                continue
            rows.append({
                "PL_Code": pl,
                "Description": desc,
                "Business_Unit": bu,
                "Strategic_Stock": round(float(qty), 2),
                "Allocation_Source": ALLOCATION_SOURCE,
                "Source_Depot_Column": depot,
            })
    return pd.DataFrame(rows, columns=ALLOCATION_FIELDS)


# ----------------------------------------------------------------------
# Aggregates consumed by the enterprise de-inflation layer
# ----------------------------------------------------------------------
def strategic_stock_by_bu() -> dict:
    """Total strategic stock units per Business Unit (depot-column allocation)."""
    strat = dp.load_strategic_stock()
    out = {bu: 0.0 for bu in dict.fromkeys(cfg.STRATEGIC_DEPOT_TO_BU.values())}
    for _, r in strat.iterrows():
        for depot, bu in cfg.STRATEGIC_DEPOT_TO_BU.items():
            q = r.get(f"stock_{depot}")
            if pd.notna(q):
                out[bu] += float(q)
    return out


def strategic_value_by_bu() -> dict:
    """Raw strategic inventory value (stock x unit_cost) per Business Unit."""
    strat = dp.load_strategic_stock()
    out = {bu: 0.0 for bu in dict.fromkeys(cfg.STRATEGIC_DEPOT_TO_BU.values())}
    for _, r in strat.iterrows():
        cost = r.get("Unit_Cost")
        cost = 0.0 if (cost is None or pd.isna(cost)) else float(cost)
        for depot, bu in cfg.STRATEGIC_DEPOT_TO_BU.items():
            q = r.get(f"stock_{depot}")
            if pd.notna(q):
                out[bu] += float(q) * cost
    return out


def strategic_value_share() -> dict:
    """Each BU's fraction of total raw strategic value (sums to 1.0)."""
    val = strategic_value_by_bu()
    total = sum(val.values())
    if total <= 0:
        return {bu: 0.0 for bu in val}
    return {bu: v / total for bu, v in val.items()}


def dominant_bu_by_pl() -> dict:
    """For each strategic PL, the BU holding the most stock (tie -> config order).
    Used to tag a single-row-per-PL registry; the full split lives in the CSV."""
    strat = dp.load_strategic_stock()
    out = {}
    for _, r in strat.iterrows():
        best_bu, best_q = None, -1.0
        for depot, bu in cfg.STRATEGIC_DEPOT_TO_BU.items():
            q = r.get(f"stock_{depot}")
            q = 0.0 if (q is None or pd.isna(q)) else float(q)
            if q > best_q:
                best_bu, best_q = bu, q
        out[r["PL_Code"]] = best_bu or buc.DEFAULT_BUSINESS_UNIT
    return out


# ----------------------------------------------------------------------
# Pipeline entry point
# ----------------------------------------------------------------------
def _current_bu():
    """Infer the active Business Unit from the scoped output dir (outputs/<BU>)."""
    name = cfg.OUTPUT_DIR.name
    return name if name in buc.BUSINESS_UNITS else None


def run(write: bool = True) -> pd.DataFrame:
    """Write strategic_inventory_allocation.csv for the active context.

    In a Business-Unit context (outputs/<BU>) writes that BU's slice; in the
    default/consolidated context writes the full zone allocation.
    """
    full = allocate()
    bu = _current_bu()
    out = full[full["Business_Unit"] == bu].reset_index(drop=True) if bu else full
    if write:
        cfg.ensure_output_dirs()
        out.to_csv(cfg.OUTPUT_DIR / "strategic_inventory_allocation.csv", index=False)
    scope = bu or "ZONE (all BUs)"
    print(f"STEP 19 -- strategic allocation [{scope}] : {len(out)} rows "
          f"-> {cfg.OUTPUT_DIR / 'strategic_inventory_allocation.csv'}")
    return out


if __name__ == "__main__":
    run()
