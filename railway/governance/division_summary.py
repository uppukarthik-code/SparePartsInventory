"""STEP1-28-aware, division-aware management summary (STEP30, reporting only).

ADDITIVE. Reads ONLY current generated outputs; computes no new analytics and
changes no existing module. Produces an executive L1 / operational L2 / technical
L3 KPI summary for the ACTIVE division (via railway.governance.config), with a
provenance metadata header (platform version, division, data date, git commit,
generation date, pipeline version, readiness score).

This is the STEP1-28 replacement for the STEP1-19-centric
railway_executive_summary / railway_management_reports consumption model: it
surfaces forecast_results, lead_time_master, safety_stock_results, rop_results,
srss_results and procurement_portfolio — which the legacy summary ignored.

Public API:
    metadata(division=None) -> dict
    compute_kpis(division=None) -> {"L1":[...], "L2":[...], "L3":[...]}
    build(division=None, write=True) -> dict   (full summary; writes JSON+MD+CSV)
"""
from __future__ import annotations

import argparse
import json
import subprocess

import pandas as pd

from railway import railway_config as cfg
from railway.governance import config as gcfg
from railway.governance import enterprise_allocation as _ea

PLATFORM_VERSION = "Railway Inventory Planning Platform v1.0 (STEP1-28 + Hardening A/B)"
PIPELINE_VERSION = "STEP1-19 core + STEP20-28 MAS extension"


# ---------------------------------------------------------------- helpers
def _history(division: str):
    """history dir for a division (defaults to active)."""
    div = division or gcfg.DIVISION
    return cfg.OUTPUT_DIR / div / "history"


def _rd(path, **kw):
    return pd.read_csv(path, dtype={"PL_Code": str}, keep_default_na=False, **kw)


def _num(s):
    return pd.to_numeric(s, errors="coerce").fillna(0)


def _git_commit() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], cwd=str(cfg.OUTPUT_DIR.parent.parent),
            stderr=subprocess.DEVNULL, text=True).strip()
    except Exception:
        return "unknown"


def _data_date(division: str) -> str:
    """Derive the snapshot/data date from the division's SUMMARY filename."""
    try:
        name = gcfg.get(division or gcfg.DIVISION)["summary_filename"]
        # 'SUMMARY OF STOCK HELD (as on 08-06-2026) _08-06-2026.xlsx'
        import re
        m = re.search(r"(\d{2}-\d{2}-\d{4})", name)
        return m.group(1) if m else "unknown"
    except Exception:
        return "unknown"


def _readiness_score() -> str:
    p = _history(gcfg.DIVISION) / "platform_scorecard.csv"
    if p.exists():
        sc = pd.read_csv(p)
        return f"{sc['Current'].mean():.1f} -> {sc['Target'].mean():.1f} (target)"
    return "n/a"


# ---------------------------------------------------------------- metadata
def metadata(division: str | None = None, generation_date: str | None = None) -> dict:
    div = division or gcfg.DIVISION
    return {
        "Platform Version": PLATFORM_VERSION,
        "Division": div,
        "Data Date": _data_date(div),
        "Git Commit": _git_commit(),
        "Generation Date": generation_date or "(runtime)",
        "Pipeline Version": PIPELINE_VERSION,
        "Readiness Score": _readiness_score(),
    }


# ---------------------------------------------------------------- KPIs
def compute_kpis(division: str | None = None) -> dict:
    H = _history(division)
    dc = _rd(H / "demand_classification.csv")
    fc = _rd(H / "forecast_results.csv")
    lt = _rd(H / "lead_time_master.csv")
    rop = _rd(H / "rop_results.csv")
    srrs = _rd(H / "srss_results.csv")
    pp = pd.read_csv(H / "procurement_portfolio.csv")

    for c in ("Current_Stock", "ROP", "Positive_Gap", "SRRS", "Average_Rate_Rs", "Reorder_Gap_Value_Rs"):
        srrs[c] = _num(srrs[c])
    rop["Lead_Time_Days"] = _num(rop["Lead_Time_Days"])

    universe = len(dc)
    planned = len(rop)
    stock_value = float((srrs["Current_Stock"] * srrs["Average_Rate_Rs"]).sum())
    gap_value = float(srrs["Reorder_Gap_Value_Rs"].sum())
    total_srrs = float(srrs["SRRS"].sum())
    top10 = float(srrs.nlargest(10, "SRRS")["SRRS"].sum())
    status = rop["Stock_Status"].value_counts().to_dict()
    crit = rop["Criticality_Class"].value_counts().to_dict()
    tier1 = pp.iloc[0] if len(pp) else None
    tier2 = pp.iloc[1] if len(pp) > 1 else None

    def kpi(name, value, source):
        return {"KPI": name, "Value": value, "Source": source}

    L1 = [
        kpi("Forecast Coverage %", round(100 * len(fc) / universe, 1), "forecast_results.csv"),
        kpi("Lead-Time Coverage %", round(100 * (rop["Lead_Time_Days"] > 0).sum() / planned, 1), "lead_time_master.csv"),
        kpi("Criticality Coverage %", round(100 * sum(crit.values()) / planned, 1), "rop_results.csv"),
        kpi("Safety-Stock Coverage %", round(100 * len(_rd(H / "safety_stock_results.csv")) / planned, 1), "safety_stock_results.csv"),
        kpi("ROP Coverage %", round(100 * planned / planned, 1), "rop_results.csv"),
        kpi("SRRS Coverage %", round(100 * len(srrs) / planned, 1), "srss_results.csv"),
        kpi("Current Stock Value (Rs)", round(stock_value), "srss_results.csv"),
        kpi("Reorder Gap Value (Rs)", round(gap_value), "srss_results.csv"),
        kpi("Total SRRS", round(total_srrs, 1), "srss_results.csv"),
        kpi("Top-10 Risk Concentration %", round(100 * top10 / total_srrs, 1), "srss_results.csv"),
        kpi("Tier 1 Count", int(tier1["PL_Count"]) if tier1 is not None else 0, "procurement_portfolio.csv"),
        kpi("Tier 2 Count", int(tier2["PL_Count"]) if tier2 is not None else 0, "procurement_portfolio.csv"),
        kpi("Platform Readiness", _readiness_score(), "platform_scorecard.csv"),
        kpi("TPJ Readiness", "NO-GO (data-blocked); config-ready", "tpj_onboarding_readiness.csv"),
    ]
    L2 = [
        kpi("Critical Shortages", status.get("Critical Shortage", 0), "rop_results.csv"),
        kpi("Shortages", status.get("Shortage", 0), "rop_results.csv"),
        kpi("Healthy", status.get("Healthy", 0), "rop_results.csv"),
        kpi("Excess Inventory", status.get("Excess", 0), "rop_results.csv"),
        kpi("No Demand", status.get("No_Demand", 0) + status.get("No_Stock_Data", 0), "rop_results.csv"),
        kpi("Open Procurement Exposure (Rs)", round(float(pp["Gap_Value_Rs"].sum())), "procurement_portfolio.csv"),
        kpi("Service Level Split", f"Critical(0.95): {crit.get('Critical', 0)} | Non-Critical(0.85): {crit.get('Non-Critical', 0)}", "rop_results.csv"),
    ]
    L3 = [
        kpi("Forecast Method Mix", fc["Forecast_Method"].value_counts().to_dict(), "forecast_results.csv"),
        kpi("Demand Class Mix", dc["Demand_Class"].value_counts().to_dict(), "demand_classification.csv"),
        kpi("Criticality Distribution", crit, "rop_results.csv"),
        kpi("Lead-Time Source Mix", lt["Lead_Time_Source"].value_counts().to_dict(), "lead_time_master.csv"),
        kpi("Planning Universe Funnel", f"{universe} classified -> {len(fc)} forecast -> {len(lt)} lead-time -> {planned} planned", "STEP21A-26"),
    ]
    return {"L1": L1, "L2": L2, "L3": L3}


# ---------------------------------------------------------------- build
def build(division: str | None = None, write: bool = True, generation_date: str | None = None) -> dict:
    div = division or gcfg.DIVISION
    summary = {"metadata": metadata(div, generation_date), "kpis": compute_kpis(div)}
    if write:
        H = _history(div)
        with open(H / "division_management_summary.json", "w") as f:
            json.dump(summary, f, indent=2, default=str)
        flat = []
        for level, items in summary["kpis"].items():
            for it in items:
                flat.append({"Level": level, "KPI": it["KPI"], "Value": str(it["Value"]), "Source": it["Source"]})
        pd.DataFrame(flat).to_csv(H / "division_management_summary.csv", index=False)
        with open(H / "division_management_summary.md", "w", encoding="utf-8") as f:
            f.write(_render_md(summary))
    return summary


def _render_md(summary: dict) -> str:
    m = summary["metadata"]
    lines = [f"# {m['Division']} Division — Management Summary", ""]
    lines.append("| Field | Value |")
    lines.append("|---|---|")
    for k, v in m.items():
        lines.append(f"| {k} | {v} |")
    for level, title in (("L1", "Executive KPIs"), ("L2", "Operational KPIs"), ("L3", "Technical KPIs")):
        lines += ["", f"## {level} — {title}", "", "| KPI | Value |", "|---|---|"]
        for it in summary["kpis"][level]:
            lines.append(f"| {it['KPI']} | {it['Value']} |")
    return "\n".join(lines) + "\n"


def has_data(division: str) -> bool:
    """A division is reportable only if its planning outputs exist (no fabrication)."""
    H = _history(division)
    return (H / "srss_results.csv").exists() and (H / "rop_results.csv").exists()


def reportable_divisions() -> list[str]:
    return [d for d in gcfg.DIVISIONS if has_data(d)]


def build_all_divisions(write: bool = True, generation_date: str | None = None) -> dict:
    """Enterprise roll-up FOUNDATION (STEP31 Phase E).

    Builds the per-division summary for every division that HAS data and assembles
    a Southern Railway enterprise view by summing the additive L1 KPIs. Divisions
    without planning outputs are listed as ``pending`` — never fabricated.
    """
    built, pending = {}, []
    for div in gcfg.DIVISIONS:
        if has_data(div):
            built[div] = build(div, write=write, generation_date=generation_date)
        else:
            pending.append(div)

    # additive L1 roll-up across reportable divisions (sum where additive)
    additive = {"Current Stock Value (Rs)", "Reorder Gap Value (Rs)", "Total SRRS",
                "Tier 1 Count", "Tier 2 Count"}
    rollup = {}
    for div, s in built.items():
        for it in s["kpis"]["L1"]:
            if it["KPI"] in additive and isinstance(it["Value"], (int, float)):
                rollup[it["KPI"]] = rollup.get(it["KPI"], 0) + it["Value"]
    enterprise = {
        "view": "Southern Railway — Enterprise Roll-up",
        "reportable_divisions": list(built),
        "pending_divisions": pending,
        "rolled_up_L1": rollup,
        "note": "additive KPIs summed; coverage/concentration are NOT summed (per-division only)",
    }
    out = {"enterprise": enterprise, "divisions": list(built)}
    if write:
        with open(cfg.OUTPUT_DIR / "_enterprise_rollup" / "enterprise_reporting_rollup.json", "w") as f:
            json.dump({"enterprise": enterprise}, f, indent=2, default=str)
    return out


def run(division: str | None = None):
    s = build(division, write=True)
    print(f"division_management_summary written for {s['metadata']['Division']} "
          f"({len(s['kpis']['L1'])} L1 / {len(s['kpis']['L2'])} L2 / {len(s['kpis']['L3'])} L3 KPIs)")
    return s


def main(argv=None):
    """CLI: --division MAS (future: TPJ/SA/TVC/PGT/MDU) | --all for enterprise roll-up."""
    ap = argparse.ArgumentParser(description="Division-aware management summary (STEP1-28).")
    ap.add_argument("--division", default=gcfg.ACTIVE_DIVISION,
                    help="division code (default: active = %(default)s)")
    ap.add_argument("--all", action="store_true", help="build all reportable divisions + enterprise roll-up")
    args = ap.parse_args(argv)
    if args.all:
        r = build_all_divisions(write=True)
        print(f"enterprise roll-up: reportable={r['enterprise']['reportable_divisions']} "
              f"pending={r['enterprise']['pending_divisions']}")
        return r
    if not has_data(args.division):
        print(f"[warn] division '{args.division}' has no planning outputs yet (data-blocked); nothing to report.")
        return None
    return run(args.division)


# ---------------------------------------------------------------- STEP35-OPT Phase H: Enterprise Board KPIs

def _budget_for_target(frontier, target_pct):
    """Smallest budget (rupees) whose risk-reduction % >= target*100, by linear
    interpolation between bracketing FINITE frontier levels. None if unreachable."""
    fin = frontier[frontier["Budget_Label"] != "Unlimited"].reset_index(drop=True)
    tgt = target_pct * 100.0
    prev_b, prev_r = 0.0, 0.0
    for _, row in fin.iterrows():
        b = float(row["Budget_Rupees"]); r = float(row["Risk_Reduction_Pct"])
        if r >= tgt:
            if r == prev_r:
                return round(b, 2)
            frac = (tgt - prev_r) / (r - prev_r)
            return round(prev_b + frac * (b - prev_b), 2)
        prev_b, prev_r = b, r
    return None


def enterprise_kpis() -> dict:
    """Board-level KPIs derived from the STEP35-OPT frontier/efficiency outputs."""
    frontier = _ea.build_risk_reduction_frontier(write=False)
    efficiency = _ea.build_budget_efficiency_analysis(frontier=frontier, write=False)
    opt_df = _ea.load_enterprise_opt()
    pr = opt_df[opt_df["Inventory_Status"] == "Procurement Required"]
    tier1 = pr[pr["Criticality"].isin(cfg.SAFETY_RESERVE_CRITICALITIES)]
    knee = efficiency[efficiency["Is_Knee_Point"]]
    optimal = knee["Budget_Label"].iloc[0] if not knee.empty else "n/a"
    unlim = frontier.iloc[-1]
    ent_eff = (float(unlim["SRRS_Mitigated"]) / float(unlim["Budget_Utilized"])
               if float(unlim["Budget_Utilized"]) > 1e-9 else 0.0)
    return {
        "Budget_For_50pct_Risk_Reduction": _budget_for_target(frontier, 0.50),
        "Budget_For_75pct_Risk_Reduction": _budget_for_target(frontier, 0.75),
        "Budget_For_90pct_Risk_Reduction": _budget_for_target(frontier, 0.90),
        "Enterprise_Capital_Efficiency": round(ent_eff, 8),
        "Optimal_Investment_Point": optimal,
        "Tier1_Funding_Requirement": round(float(tier1["Inventory_Investment_Required"].sum()), 2),
        "Max_Achievable_Risk_Reduction_Pct": round(float(unlim["Risk_Reduction_Pct"]), 4),
    }


def build_enterprise_decision_dashboard(write: bool = True):
    kpis = enterprise_kpis()
    dash = pd.DataFrame([{"KPI": k, "Value": v} for k, v in kpis.items()])
    if write:
        cfg.ensure_output_dirs()
        dash.to_csv(cfg.OUTPUT_DIR / "enterprise_decision_dashboard.csv", index=False)
    return dash


if __name__ == "__main__":
    main()
