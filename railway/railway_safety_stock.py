"""
railway_safety_stock.py
=======================
STEP 24 -- Safety-Stock Recalibration for MAS (ADDITIVE; reuses existing formula).

Computes a calibrated safety-stock layer per PL using the repository's existing
inventory-theory form  Safety_Stock = z * sigma_LT  (z = norm.ppf(service level)),
with monthly demand variability and the STEP23.6B derived lead times. Modifies NO
forecasting / lead-time / procurement / ROP / SRRS / enterprise logic and writes
only two new files.

Inputs (all real, traceable):
  * demand variability sigma  : demand_classification.Std_Deviation  (monthly, STEP22)
  * lead time                 : lead_time_master.Lead_Time_Days       (STEP23.6B; no synthesis)
  * criticality (binary)      : SUMMARY OF STOCK HELD col4 Type        (STEP23.8: Safety/Vital->Critical, NA->Non-Critical)
  * forecast                  : forecast_results.Forecast_2026_27

Method (agreed STEP24):
  Service level : Critical 95% (z=1.645) / Non-Critical 85% (z=1.036)
  sigma_LT      : sigma_monthly * sqrt(Lead_Time_Days / 30.4375)
  Safety_Stock  : z * sigma_LT
PLs without a derived lead time are FLAGGED separately, never fabricated.
"""

from __future__ import annotations

import os

import numpy as np
import pandas as pd
from scipy import stats

from railway import railway_config as cfg
from railway.ingestion import excel_reader, csv_reader   # consolidated I/O (Phase A)
from railway.governance import config as gcfg            # centralized config (Phase B)

H = gcfg.HISTORY_DIR
SUMMARY = gcfg.SUMMARY_WORKBOOK

DAYS_PER_MONTH = gcfg.DAYS_PER_MONTH
SERVICE_LEVEL = gcfg.SERVICE_LEVEL


def _rd(p):
    return csv_reader.read_pl_csv(p)


def _criticality_by_pl() -> dict:
    """Binary criticality per PL from the SUMMARY col4 Type token (STEP23.8 validated)."""
    out = {}
    for r in excel_reader.read_sheet_rows(SUMMARY)[1:]:
        v = r.get(4)
        if not v:
            continue
        parts = [p.strip() for p in str(v).split("/")]
        pl = parts[0].strip()
        tail = " / ".join(parts[1:]).lower()
        if "safety" in tail or "vital" in tail:
            cls = "Critical"
        elif tail.strip().startswith("na"):
            cls = "Non-Critical"
        else:
            cls = "Unknown"
        out.setdefault(pl, cls)
    return out


def build(write: bool = True):
    dc = _rd(H / "demand_classification.csv")          # Std_Deviation (monthly sigma)
    fr = _rd(H / "forecast_results.csv")                # Forecast_2026_27 + method
    lt = _rd(H / "lead_time_master.csv")                # Lead_Time_Days

    sigma = dict(zip(dc["PL_Code"], pd.to_numeric(dc["Std_Deviation"], errors="coerce")))
    desc = dict(zip(dc["PL_Code"], dc["Description"]))
    fmethod = dict(zip(fr["PL_Code"], fr["Forecast_Method"]))
    fannual = dict(zip(fr["PL_Code"], pd.to_numeric(fr["Forecast_2026_27"], errors="coerce")))
    lt_days = dict(zip(lt["PL_Code"], pd.to_numeric(lt["Lead_Time_Days"], errors="coerce")))
    crit = _criticality_by_pl()

    forecastable = list(fr["PL_Code"])                 # 961 (Dead excluded upstream)
    rows = []
    uncovered_lt = []          # forecastable but no derived lead time
    uncovered_crit = []        # no criticality signal
    for pl in forecastable:
        if pl not in lt_days or pd.isna(lt_days[pl]):
            uncovered_lt.append(pl); continue
        cls = crit.get(pl, "Unknown")
        if cls == "Unknown":
            uncovered_crit.append(pl); continue        # no synthetic criticality
        sl = SERVICE_LEVEL[cls]
        z = float(stats.norm.ppf(sl))
        sd = float(sigma.get(pl) or 0.0)
        ltd = float(lt_days[pl])
        sigma_lt = sd * np.sqrt(ltd / DAYS_PER_MONTH)
        ss = z * sigma_lt
        rows.append({
            "PL_Code": pl, "Description": desc.get(pl, ""), "Business_Unit": gcfg.DIVISION,
            "Criticality_Class": cls, "Forecast_Method": fmethod.get(pl, ""),
            "Forecast_Annual": round(float(fannual.get(pl) or 0.0), 2),
            "Lead_Time_Days": round(ltd, 1), "Demand_STD": round(sd, 4),
            "Service_Level": sl, "Z_Value": round(z, 4),
            "Safety_Stock": round(max(ss, 0.0), 2),
        })
    res = pd.DataFrame(rows, columns=["PL_Code", "Description", "Business_Unit",
        "Criticality_Class", "Forecast_Method", "Forecast_Annual", "Lead_Time_Days",
        "Demand_STD", "Service_Level", "Z_Value", "Safety_Stock"]).sort_values(
        "Safety_Stock", ascending=False).reset_index(drop=True)

    # summary
    totvol = fannual_sum = sum(v for v in fannual.values() if not pd.isna(v))
    covered_vol = res["Forecast_Annual"].sum()
    summ = pd.DataFrame([{
        "PL_Count_With_Safety_Stock": len(res),
        "Forecastable_PLs": len(forecastable),
        "PL_Coverage_Pct_of_Forecastable": round(100 * len(res) / len(forecastable), 1),
        "Forecast_Volume_Coverage_Pct": round(100 * covered_vol / totvol, 1) if totvol else 0,
        "Critical_PLs": int((res["Criticality_Class"] == "Critical").sum()),
        "NonCritical_PLs": int((res["Criticality_Class"] == "Non-Critical").sum()),
        "Total_Safety_Stock_Units": round(res["Safety_Stock"].sum(), 1),
        "Critical_Safety_Stock_Units": round(res.loc[res["Criticality_Class"] == "Critical", "Safety_Stock"].sum(), 1),
        "NonCritical_Safety_Stock_Units": round(res.loc[res["Criticality_Class"] == "Non-Critical", "Safety_Stock"].sum(), 1),
        "Uncovered_No_LeadTime": len(uncovered_lt),
        "Uncovered_No_Criticality": len(uncovered_crit),
    }])
    if write:
        H.mkdir(parents=True, exist_ok=True)
        res.to_csv(H / "safety_stock_results.csv", index=False)
        summ.to_csv(H / "safety_stock_summary.csv", index=False)
    return res, summ, {"uncovered_lt": uncovered_lt, "uncovered_crit": uncovered_crit}


def run():
    res, summ, unc = build(write=True)
    print("STEP 24 -- safety-stock recalibration (MAS)")
    print(summ.to_string(index=False))
    print(f"  uncovered: no-LT={len(unc['uncovered_lt'])}  no-criticality={len(unc['uncovered_crit'])}")
    return res, summ, unc


if __name__ == "__main__":
    run()
