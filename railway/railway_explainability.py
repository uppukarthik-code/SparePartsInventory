"""
railway_explainability.py
=========================
STEP 17 -- Funding explainability layer (additive, read-only).

For every procurement-required item, explains WHY it scored / was funded, by
decomposing the (frozen) objective  SRRS = Criticality_Weight * Service_Factor *
Positive_Gap  into per-driver contribution shares, and flagging whether the item
was funded through the Safety Reserve (stage 1) of the budget allocation.

This module does NOT modify any frozen output. It reads the produced policy +
procurement plan and writes a NEW artefact:

    outputs/railway_funding_explainability.csv

Columns: PL_Code, Description, Criticality, Service_Risk_Reduction_Score,
         Criticality_Contribution, Service_Contribution, Gap_Contribution,
         Reserve_Allocation_Flag, Funding_Decision

Run:  python -m railway.railway_explainability
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from railway import railway_config as cfg
from railway import railway_inventory_optimization as opt


def build_explainability(write: bool = True) -> pd.DataFrame:
    pol = pd.read_csv(cfg.INVENTORY_POLICY_CSV, dtype={"PL_Code": str})

    # --- reconstruct the EXACT candidate frame used by allocate_procurement_budget ---
    budget = cfg.PROCUREMENT_BUDGET
    cand = pol[pol["Inventory_Status"] == "Procurement Required"].copy()
    cand = cand[cand["Inventory_Investment_Required"] <= budget].reset_index(drop=True)

    # read-only re-derivation of the funded + reserve-funded sets (selection unchanged)
    sel, reserve_sel = opt.allocate_with_reserve(
        cand, budget, "Service_Risk_Reduction_Score", "Inventory_Investment_Required",
        return_stages=True)
    funded_pl = set(cand.loc[list(sel), "PL_Code"])
    reserve_pl = set(cand.loc[list(reserve_sel), "PL_Code"])

    # --- per-driver contribution shares of the multiplicative objective ---
    # ln(SRRS) = ln(C_w) + ln(Service_Factor) + ln(Positive_Gap); negative log terms
    # (factor below its unit baseline) clamp to 0 so shares stay in [0, 100] and sum to 100.
    d = pol[pol["Inventory_Status"] == "Procurement Required"].copy()
    cw = d["Criticality_Weight"].clip(lower=1e-9)
    sf = d["Service_Factor"].clip(lower=1e-9)
    gp = d["Positive_Gap"].clip(lower=1e-9)
    lc = np.log(cw).clip(lower=0.0)
    ls = np.log(sf).clip(lower=0.0)
    lg = np.log(gp).clip(lower=0.0)
    tot = (lc + ls + lg).replace(0, np.nan)
    d["Criticality_Contribution"] = (lc / tot * 100).round(1).fillna(0.0)
    d["Service_Contribution"] = (ls / tot * 100).round(1).fillna(0.0)
    d["Gap_Contribution"] = (lg / tot * 100).round(1).fillna(0.0)
    d["Reserve_Allocation_Flag"] = d["PL_Code"].isin(reserve_pl)
    d["Funding_Decision"] = np.where(d["PL_Code"].isin(funded_pl), "Funded", "Not Funded")

    out = d[["PL_Code", "Description", "Criticality", "Service_Risk_Reduction_Score",
             "Criticality_Contribution", "Service_Contribution", "Gap_Contribution",
             "Reserve_Allocation_Flag", "Funding_Decision"]] \
        .sort_values("Service_Risk_Reduction_Score", ascending=False).reset_index(drop=True)

    if write:
        cfg.ensure_output_dirs()
        out.to_csv(cfg.OUTPUT_DIR / "railway_funding_explainability.csv", index=False)
    return out


def run():
    out = build_explainability(write=True)
    funded = out[out["Funding_Decision"] == "Funded"]
    print("=" * 78)
    print("STEP 17 -- FUNDING EXPLAINABILITY")
    print("=" * 78)
    print(f"Procurement-required items : {len(out)}")
    print(f"Funded                     : {len(funded)} "
          f"(reserve-funded: {int(out['Reserve_Allocation_Flag'].sum())})")
    print("\nFunded items -- mean contribution split:")
    print(f"   Criticality : {funded['Criticality_Contribution'].mean():.1f}%")
    print(f"   Service     : {funded['Service_Contribution'].mean():.1f}%")
    print(f"   Gap         : {funded['Gap_Contribution'].mean():.1f}%")
    print(f"\nWrote: {cfg.OUTPUT_DIR / 'railway_funding_explainability.csv'}")
    return out


if __name__ == "__main__":
    run()
