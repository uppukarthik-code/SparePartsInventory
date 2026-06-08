"""
railway_dashboard_validation.py
==============================
Step-11 dashboard data-lineage validation suite (V1-V5). Confirms the Power BI
pages now consume NORMALIZED values and never mix inventory universes.

Generates STEP11_VALIDATION_REPORT.md.
"""

from __future__ import annotations

import pandas as pd

from railway import railway_config as cfg

OUT = cfg.OUTPUT_DIR
PBI = cfg.POWERBI_DIR
TOL = 0.001                                  # 0.1%
FORBIDDEN = ["Inventory_Value", "Inventory_Investment_Required", "Procurement_Priority_Score"]
# Pages allowed to carry an "Inventory_Value" column:
#   page4_operational_health   - operational universe value (no normalized counterpart)
#   page5_rationalization      - compatibility ALIAS defined to EQUAL
#                                Normalized_Inventory_Value (verified by V6); legacy
#                                Power BI visuals bind to this column name.
OPERATIONAL_EXEMPT = {"page4_operational_health", "page5_rationalization"}


def _within(a, b, tol=TOL):
    if b == 0:
        return abs(a) < 1e-6
    return abs(a - b) / abs(b) <= tol


def run():
    policy = pd.read_csv(OUT / "railway_inventory_policy.csv", dtype={"PL_Code": str})
    dq = pd.read_csv(OUT / "railway_data_quality.csv", dtype={"PL_Code": str})
    p0 = pd.read_csv(PBI / "page0_executive_dashboard.csv").set_index("KPI")["Value"].to_dict()
    p1 = pd.read_csv(PBI / "page1_procurement.csv", dtype={"PL_Code": str})
    p7 = pd.read_csv(PBI / "page7_abc_criticality_matrix.csv")

    results = []

    # ---- V1: Executive strategic inventory value == SUM(Normalized_Inventory_Value) ----
    norm_inv = float(dq["Normalized_Inventory_Value"].sum())
    exec_val = float(p0["Strategic Inventory Value (Normalized)"])
    results.append(("V1 Executive strategic value == SUM(Normalized_Inventory_Value)",
                    _within(exec_val, norm_inv), f"page0={exec_val:,.0f} vs Σnorm={norm_inv:,.0f}"))

    # ---- V2: Procurement total == SUM(Normalized_Investment_Required) ----
    p1_sum = float(p1["Normalized_Investment_Required"].sum())
    pol_sum = float(policy["Normalized_Investment_Required"].sum())
    p0_proc = float(p0["Procurement Required Value"])
    results.append(("V2 Procurement page total == SUM(Normalized_Investment_Required)",
                    _within(p1_sum, pol_sum), f"page1={p1_sum:,.0f} vs policy={pol_sum:,.0f}"))
    results.append(("V2b Executive 'Procurement Required' == page1 total",
                    _within(p0_proc, p1_sum), f"page0={p0_proc:,.0f} vs page1={p1_sum:,.0f}"))

    # ---- V3: Criticality matrix reconciles to SUM(Normalized_Inventory_Value) ----
    p7_sum = float(p7["Normalized_Inventory_Value"].sum())
    results.append(("V3 Criticality matrix == SUM(Normalized_Inventory_Value)",
                    _within(p7_sum, norm_inv), f"page7={p7_sum:,.0f} vs Σnorm={norm_inv:,.0f}"))

    # ---- V4: no strategic Power BI page contains original value/score columns ----
    v4_violations = []
    for path in sorted(PBI.glob("page*.csv")):
        name = path.stem
        if name in OPERATIONAL_EXEMPT:
            continue
        cols = pd.read_csv(path, nrows=0).columns
        hits = [c for c in FORBIDDEN if c in cols]
        if hits:
            v4_violations.append(f"{name}: {hits}")
    results.append(("V4 no original value/score columns on strategic pages",
                    len(v4_violations) == 0, v4_violations or "clean"))

    # ---- V5: Top-20 procurement before vs after normalization ----
    pol = policy.copy()
    pol["Rank_Before"] = pol["Procurement_Priority_Score"].rank(ascending=False, method="first").astype(int)
    pol["Rank_After"] = pol["Normalized_Procurement_Priority_Score"].rank(ascending=False, method="first").astype(int)
    pol["Delta_Rank"] = pol["Rank_Before"] - pol["Rank_After"]
    top = pol.sort_values("Rank_Before").head(20)[
        ["PL_Code", "Description", "Rank_Before", "Rank_After", "Delta_Rank",
         "Procurement_Priority_Score", "Normalized_Procurement_Priority_Score"]].rename(
        columns={"Procurement_Priority_Score": "Original_Value",
                 "Normalized_Procurement_Priority_Score": "Normalized_Value"})
    top["Flag_>10"] = top["Delta_Rank"].abs() > 10
    big_moves = int(top["Flag_>10"].sum())
    top.to_csv(OUT / "step11_top20_rank_comparison.csv", index=False)
    results.append(("V5 Top-20 rank comparison generated",
                    True, f"{big_moves} item(s) moved >10 positions (see step11_top20_rank_comparison.csv)"))

    # ---- V6: Power BI compatibility columns (Description / Criticality_Name / alias) ----
    p3 = pd.read_csv(PBI / "page3_criticality.csv", dtype={"PL_Code": str})
    p4 = pd.read_csv(PBI / "page4_operational_health.csv", dtype={"PL_Code": str})
    p5 = pd.read_csv(PBI / "page5_rationalization.csv", dtype={"PL_Code": str})

    # V6a: page5 Inventory_Value alias is byte-equal to Normalized_Inventory_Value
    alias_ok = ("Inventory_Value" in p5.columns
                and "Normalized_Inventory_Value" in p5.columns
                and p5["Inventory_Value"].equals(p5["Normalized_Inventory_Value"]))
    results.append(("V6a page5 Inventory_Value == Normalized_Inventory_Value (alias)",
                    alias_ok, "identical" if alias_ok else "alias mismatch"))

    # V6b: Description populated on every compatibility-restored page
    desc_pages = {"page1": p1, "page3": p3, "page4": p4, "page5": p5}
    desc_missing = {n: int(d["Description"].isna().sum()) if "Description" in d.columns else "ABSENT"
                    for n, d in desc_pages.items()}
    desc_ok = all(v == 0 for v in desc_missing.values())
    results.append(("V6b Description populated on page1/page3/page4/page5",
                    desc_ok, desc_missing))

    # V6c: Criticality_Name populated on page1 & page3
    crit_pages = {"page1": p1, "page3": p3}
    crit_missing = {n: int(d["Criticality_Name"].isna().sum()) if "Criticality_Name" in d.columns else "ABSENT"
                    for n, d in crit_pages.items()}
    crit_ok = all(v == 0 for v in crit_missing.values())
    results.append(("V6c Criticality_Name populated on page1/page3",
                    crit_ok, crit_missing))

    all_pass = all(ok for _, ok, _ in results)

    # ---- report ----
    lines = ["# STEP 11 — Validation Report\n",
             f"**Generated:** 2026-06-07 · Tolerance: 0.1%\n",
             f"## Overall: {'✅ ALL VALIDATIONS PASS' if all_pass else '❌ FAILURES PRESENT'}\n",
             "| # | Validation | Result | Detail |", "|---|---|---|---|"]
    for name, ok, detail in results:
        lines.append(f"| | {name} | {'✅ PASS' if ok else '❌ FAIL'} | {detail} |")
    lines.append("\n## V5 — Top 20 Procurement Items: Before vs After Normalization\n")
    lines.append("| Rank Before | Rank After | Δ Rank | PL_Code | Original Value | Normalized Value | >10 |")
    lines.append("|---:|---:|---:|---|---:|---:|:--:|")
    for _, r in top.iterrows():
        lines.append(f"| {r['Rank_Before']} | {r['Rank_After']} | {r['Delta_Rank']:+d} | {r['PL_Code']} | "
                     f"{r['Original_Value']:,.0f} | {r['Normalized_Value']:,.0f} | "
                     f"{'⚠️' if r['Flag_>10'] else ''} |")
    (OUT.parent.parent / "STEP11_VALIDATION_REPORT.md").write_text("\n".join(lines), encoding="utf-8")

    print("=" * 78)
    print("STEP 11 — DASHBOARD VALIDATION SUITE")
    print("=" * 78)
    for name, ok, detail in results:
        print(f"   {'PASS' if ok else 'FAIL'}  {name}")
        print(f"         {detail}")
    print(f"\n   ALL PASS: {all_pass}")
    print(f"   Wrote: STEP11_VALIDATION_REPORT.md, step11_top20_rank_comparison.csv")
    return results, all_pass


if __name__ == "__main__":
    run()
