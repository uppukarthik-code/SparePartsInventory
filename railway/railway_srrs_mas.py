"""
railway_srrs_mas.py
===================
STEP 26 -- Division SRRS Prioritization Engine for MAS (ADDITIVE; SRRS math reused).

Reuses the repository's EXACT Step-15 calibrated SRRS objective:
    SRRS = Criticality_Weight * Service_Factor * Positive_Gap
with `Service_Factor` taken verbatim from railway_inventory_optimization.service_factor
and `Positive_Gap = max(ROP - Current_Stock, 0)` from STEP25.

Criticality weights reuse the existing S1/S2/S4 values via the native STEP23.8 Type
signal: Safety Item->10 (S1), Vital Item->5 (S2), NA->1 (S4).  No cost is injected
into SRRS.

A SEPARATE value lens (NOT part of SRRS): Reorder_Gap_Value_Rs = Positive_Gap *
Average_Rate_Rs (unit cost from SUMMARY OF STOCK HELD, STEP25.5). Service risk and
capital exposure are kept independent.

Modifies NO forecasting / safety-stock / ROP / SRRS / procurement / enterprise logic
or output. Writes two new files only.
"""

from __future__ import annotations

import pandas as pd

from railway import railway_config as cfg
from railway import railway_inventory_optimization as opt   # reuse service_factor
from railway.ingestion import excel_reader                  # consolidated I/O (Phase A)
from railway.governance import config as gcfg               # centralized config (Phase B)

H = gcfg.HISTORY_DIR
SUMMARY = gcfg.SUMMARY_WORKBOOK

TYPE_WEIGHT = gcfg.TYPE_WEIGHT          # {"Safety Item":10,"Vital Item":5,"NA":1} = S1/S2/S4
SERVICE_LEVEL = gcfg.SERVICE_LEVEL


def _summary_signals():
    """Per-PL native Type (Safety/Vital/NA) + max Average Rate (unit cost)."""
    typ, rate = {}, {}
    for r in excel_reader.read_sheet_rows(SUMMARY)[1:]:
        v = r.get(4)
        if not v:
            continue
        pl = str(v).split("/")[0].strip()
        tail = " / ".join(str(v).split("/")[1:]).lower()
        if "safety" in tail:
            t = "Safety Item"
        elif "vital" in tail:
            t = "Vital Item"
        elif tail.strip().startswith("na"):
            t = "NA"
        else:
            t = "NA"
        typ.setdefault(pl, t)
        try:
            ar = float(str(r.get(11)).replace(",", ""))
        except Exception:
            ar = 0.0
        rate[pl] = max(rate.get(pl, 0.0), ar)
    return typ, rate


def build(write: bool = True):
    rop = pd.read_csv(H / "rop_results.csv", dtype={"PL_Code": str}, keep_default_na=False)
    typ, rate = _summary_signals()

    rows = []
    for _, r in rop.iterrows():
        pl = r["PL_Code"]
        cls = r["Criticality_Class"]                       # Critical / Non-Critical (binary view)
        t = typ.get(pl, "NA")
        weight = TYPE_WEIGHT[t]
        sl = SERVICE_LEVEL.get(cls, 0.85)
        sf = opt.service_factor(sl)                        # reused verbatim (0.95->2.0, 0.85->1.0)
        gap = pd.to_numeric(pd.Series([r["Reorder_Gap"]]), errors="coerce").iloc[0]
        pos_gap = max(float(gap), 0.0) if pd.notna(gap) else 0.0
        srrs = weight * sf * pos_gap
        ar = rate.get(pl, 0.0)
        gap_val = pos_gap * ar
        rows.append({
            "PL_Code": pl, "Description": r["Description"], "Criticality_Class": cls,
            "Forecast_Annual": float(r["Forecast_Annual"]),
            "Lead_Time_Days": float(r["Lead_Time_Days"]),
            "Current_Stock": (float(r["Current_Stock"]) if r["Current_Stock"] != "" else 0.0),
            "ROP": float(r["ROP"]), "Positive_Gap": round(pos_gap, 2),
            "SRRS": round(srrs, 4),
            "Average_Rate_Rs": round(ar, 2),
            "Reorder_Gap_Value_Rs": round(gap_val, 2),
        })
    df = pd.DataFrame(rows)
    df["SRRS_Rank"] = df["SRRS"].rank(ascending=False, method="first").astype(int)
    df["Value_Rank"] = df["Reorder_Gap_Value_Rs"].rank(ascending=False, method="first").astype(int)
    res = df[["PL_Code", "Description", "Criticality_Class", "Forecast_Annual",
              "Lead_Time_Days", "Current_Stock", "ROP", "Positive_Gap", "SRRS",
              "SRRS_Rank", "Average_Rate_Rs", "Reorder_Gap_Value_Rs", "Value_Rank"]] \
        .sort_values("SRRS_Rank").reset_index(drop=True)

    # summary
    tot_srrs = res["SRRS"].sum(); tot_val = res["Reorder_Gap_Value_Rs"].sum()
    def topn(col, n):
        s = res.sort_values(col, ascending=False)[col]
        tot = s.sum()
        return round(100 * s.head(n).sum() / tot, 1) if tot else 0.0
    summ = pd.DataFrame([{
        "PL_Count": len(res),
        "Total_SRRS": round(tot_srrs, 2),
        "Total_Positive_Gap": round(res["Positive_Gap"].sum(), 2),
        "Total_Reorder_Gap_Value_Rs": round(tot_val, 2),
        "Top10_SRRS_Pct": topn("SRRS", 10), "Top20_SRRS_Pct": topn("SRRS", 20),
        "Top50_SRRS_Pct": topn("SRRS", 50),
        "Top10_Value_Pct": topn("Reorder_Gap_Value_Rs", 10),
        "Top20_Value_Pct": topn("Reorder_Gap_Value_Rs", 20),
        "Top50_Value_Pct": topn("Reorder_Gap_Value_Rs", 50),
    }])
    if write:
        H.mkdir(parents=True, exist_ok=True)
        res.to_csv(H / "srss_results.csv", index=False)
        summ.to_csv(H / "srss_summary.csv", index=False)
    return res, summ


def run():
    res, summ = build(write=True)
    print("STEP 26 -- Division SRRS prioritization (MAS)")
    print(summ.to_string(index=False))
    return res, summ


if __name__ == "__main__":
    run()
