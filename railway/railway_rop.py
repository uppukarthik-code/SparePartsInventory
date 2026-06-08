"""
railway_rop.py
==============
STEP 25 -- Division Reorder Point (ROP) + Reorder-Gap Analysis for MAS
(ADDITIVE; reuses the repository's existing ROP form).

Reuses railway_inventory_optimization's ROP convention EXACTLY:
    Demand_During_LT = Forecast_Annual * (Lead_Time_Months / 12)   (= repo 'edlt')
    ROP              = Demand_During_LT + Safety_Stock
    Reorder_Gap      = ROP - Current_Stock

Safety stock is read VERBATIM from STEP24 (safety_stock_results.csv) -- never
recomputed. Current stock comes ONLY from SUMMARY OF STOCK HELD (depot 027534) --
no synthetic/inferred/back-calculated stock, no depot-027029 substitution.
Modifies NO forecasting / safety-stock / procurement / SRRS / enterprise logic.
"""

from __future__ import annotations

import pandas as pd

from railway import railway_config as cfg
from railway.ingestion import excel_reader, csv_reader   # consolidated I/O (Phase A)
from railway.governance import config as gcfg            # centralized config (Phase B)

H = gcfg.HISTORY_DIR
SUMMARY = gcfg.SUMMARY_WORKBOOK
DAYS_PER_MONTH = gcfg.DAYS_PER_MONTH


def _rd(p):
    return csv_reader.read_pl_csv(p)


def _current_stock_027534() -> dict:
    """Sum current stock per PL from SUMMARY OF STOCK HELD (depot 027534 only)."""
    out = {}
    for r in excel_reader.read_sheet_rows(SUMMARY)[1:]:
        v = r.get(4)
        if not v:
            continue
        pl = str(v).split("/")[0].strip()
        try:
            q = float(str(r.get(8)).replace(",", ""))
        except Exception:
            q = 0.0
        out[pl] = out.get(pl, 0.0) + q
    return out


def _status(cur, rop):
    if cur is None:
        return "No_Stock_Data"
    if rop == 0:
        return "Excess" if cur > 0 else "No_Demand"
    if cur < gcfg.ROP_CRITICAL_FACTOR * rop:
        return "Critical Shortage"
    if cur < rop:
        return "Shortage"
    if cur <= gcfg.ROP_EXCESS_FACTOR * rop:
        return "Healthy"
    return "Excess"


def build(write: bool = True):
    ss = _rd(H / "safety_stock_results.csv")     # 626 PLs; SS reused verbatim
    fmeth = _rd(H / "forecast_results.csv")
    method = dict(zip(fmeth["PL_Code"], fmeth["Forecast_Method"]))
    stock = _current_stock_027534()

    rows = []
    for _, r in ss.iterrows():
        pl = r["PL_Code"]
        f_annual = float(r["Forecast_Annual"])
        f_monthly = f_annual / 12.0
        ltd = float(r["Lead_Time_Days"])
        lt_months = ltd / DAYS_PER_MONTH
        ddlt = f_annual * (lt_months / 12.0)         # repo 'edlt' form
        sstock = float(r["Safety_Stock"])
        rop = ddlt + sstock
        cur = stock.get(pl)                          # None if not in SUMMARY
        gap = (rop - cur) if cur is not None else None
        rows.append({
            "PL_Code": pl, "Description": r["Description"], "Business_Unit": gcfg.DIVISION,
            "Criticality_Class": r["Criticality_Class"],
            "Forecast_Method": method.get(pl, r.get("Forecast_Method", "")),
            "Forecast_Annual": round(f_annual, 2), "Forecast_Monthly": round(f_monthly, 3),
            "Lead_Time_Days": round(ltd, 1),
            "Demand_During_LT": round(ddlt, 2), "Safety_Stock": round(sstock, 2),
            "ROP": round(rop, 2),
            "Current_Stock": (round(cur, 2) if cur is not None else ""),
            "Reorder_Gap": (round(gap, 2) if gap is not None else ""),
            "Stock_Status": _status(cur, rop),
        })
    res = pd.DataFrame(rows, columns=["PL_Code", "Description", "Business_Unit",
        "Criticality_Class", "Forecast_Method", "Forecast_Annual", "Forecast_Monthly",
        "Lead_Time_Days", "Demand_During_LT", "Safety_Stock", "ROP", "Current_Stock",
        "Reorder_Gap", "Stock_Status"]).sort_values("ROP", ascending=False).reset_index(drop=True)

    # summary
    have_gap = res[res["Reorder_Gap"] != ""].copy()
    have_gap["g"] = pd.to_numeric(have_gap["Reorder_Gap"])
    pos = have_gap[have_gap["g"] > 0]["g"].sum()
    fr = _rd(H / "forecast_results.csv")
    totvol = pd.to_numeric(fr["Forecast_2026_27"], errors="coerce").sum()
    covvol = res["Forecast_Annual"].sum()
    statusd = res["Stock_Status"].value_counts().to_dict()
    summ = pd.DataFrame([{
        "PL_Count_ROP": len(res),
        "Forecast_Volume_Coverage_Pct": round(100 * covvol / totvol, 1) if totvol else 0,
        "Critical_PLs": int((res["Criticality_Class"] == "Critical").sum()),
        "NonCritical_PLs": int((res["Criticality_Class"] == "Non-Critical").sum()),
        "Total_ROP_Units": round(res["ROP"].sum(), 1),
        "Total_Positive_Reorder_Gap_Units": round(float(pos), 1),
        "Critical_Shortage_PLs": statusd.get("Critical Shortage", 0),
        "Shortage_PLs": statusd.get("Shortage", 0),
        "Healthy_PLs": statusd.get("Healthy", 0),
        "Excess_PLs": statusd.get("Excess", 0),
        "No_Demand_PLs": statusd.get("No_Demand", 0),
        "No_Stock_Data_PLs": statusd.get("No_Stock_Data", 0),
    }])
    if write:
        H.mkdir(parents=True, exist_ok=True)
        res.to_csv(H / "rop_results.csv", index=False)
        summ.to_csv(H / "rop_summary.csv", index=False)
    return res, summ


def run():
    res, summ = build(write=True)
    print("STEP 25 -- Division ROP + reorder gap (MAS)")
    print(summ.to_string(index=False))
    return res, summ


if __name__ == "__main__":
    run()
