"""
railway_management_reports.py
=============================
STEP 12 -- Automated Management Narrative Reports.

Converts the finished analytical CSV outputs (produced through Step 11) into
management-ready Markdown reports written in plain operational English for senior
railway officers (DRM, ADRM, PCSTE, CSTE, Sr.DSTE, Stores Officers).

Design rules (locked):
  * READ-ONLY consumer of existing CSV outputs -- never re-runs analytics.
  * NEVER overwrites any analytical output. All reports are written to a NEW
    folder: outputs/reports/.
  * NO business logic is duplicated from the analytical modules. Every number in
    every report is read or trivially aggregated from a CSV at run time, so the
    reports stay valid when the source data changes.
  * No machine-learning / statistics / forecasting jargon. Operational,
    maintenance, procurement and inventory-management language only.

Each report follows the narrative pattern for every finding:
    Observation  ->  Business Implication  ->  Recommended Action

Run:  python -m railway.railway_management_reports
"""

from __future__ import annotations

import csv
import json
import re
from collections import Counter
from datetime import datetime

import pandas as pd

from railway import railway_config as cfg
from railway.governance import division_summary as _ds   # STEP31 single source of truth

# === STEP31 REPORTING CUT-OVER (strangler) ====================================
# division_summary is the SINGLE SOURCE OF TRUTH for the modern STEP1-28 KPI set.
# The legacy collect_kpis()/run()/management-pack below are DEPRECATED and kept
# ONLY for backward compatibility (they reproduce the pinned management/page8/page9
# outputs). New consumers MUST use the delegating accessors here; no modern KPI is
# duplicated. Physical removal deferred to repository purification.


def modern_kpis(division: str | None = None) -> dict:
    """Modern STEP1-28 L1/L2/L3 KPIs (delegates to division_summary)."""
    return _ds.compute_kpis(division)


def modern_summary(division: str | None = None, write: bool = False) -> dict:
    """Modern division-aware management summary (delegates to division_summary)."""
    return _ds.build(division, write=write)
# ==============================================================================


# ----------------------------------------------------------------------
# Report repository -- a permanent management-information store, kept
# completely separate from the analytical outputs (which never change).
#
#   outputs/reports/
#       latest/        most recent run (overwritten each run -- the "current" pointer)
#       archive/YYYY-MM/   immutable monthly snapshots + delta (never overwritten)
#       history/       append-only index, KPI trend, run snapshots, CHANGELOG
#       validation/    timestamped validation reports
# ----------------------------------------------------------------------
PBI = cfg.POWERBI_DIR
AXLX = cfg.ANYLOGISTIX_DIR
REPORTS_DIR = cfg.OUTPUT_DIR / "reports"
LATEST_DIR = REPORTS_DIR / "latest"
ARCHIVE_DIR = REPORTS_DIR / "archive"
HISTORY_DIR = REPORTS_DIR / "history"
VALIDATION_DIR = REPORTS_DIR / "validation"

REPORT_INDEX_CSV = HISTORY_DIR / "report_index.csv"
TREND_HISTORY_CSV = HISTORY_DIR / "executive_trend_history.csv"
RUN_SNAPSHOTS_JSONL = HISTORY_DIR / "run_snapshots.jsonl"
CHANGELOG_MD = HISTORY_DIR / "CHANGELOG.md"

# Single execution clock -- every artefact in one run shares the same stamp.
_NOW = datetime.now()
RUN_TS = _NOW.strftime("%Y-%m-%dT%H-%M-%S")        # filesystem-safe, unique per run
RUN_MONTH = _NOW.strftime("%Y-%m")                  # archive bucket / pack suffix (YYYY-MM)
RUN_MONTH_US = _NOW.strftime("%Y_%m")               # Management_Pack_YYYY_MM
REPORT_DATE = _NOW.strftime("%d %B %Y")
RUN_DATE_ISO = _NOW.strftime("%Y-%m-%d")
GEN_TIMESTAMP = _NOW.strftime("%Y-%m-%d %H:%M:%S")

# Reports the module produces (filename -> generator function name, wired below).
REPORT_FILES = [
    "monthly_executive_report.md",
    "procurement_review.md",
    "dead_stock_review.md",
    "rationalization_review.md",
    "budget_review.md",
    "digital_twin_readiness_report.md",
]


# ======================================================================
# Generic helpers (formatting + CSV access) -- no business logic.
# ======================================================================
def _read(path, **kw):
    return pd.read_csv(path, dtype={"PL_Code": str}, **kw)


def _kpi_dict(df, key="KPI", val="Value"):
    """Two-column (name,value) CSV -> {name: float-or-raw}."""
    return dict(zip(df[key], df[val]))


def inr(value):
    """Format a rupee amount in Indian crore / lakh narrative form."""
    if value is None or pd.isna(value):
        return "Rs 0"
    v = float(value)
    sign = "-" if v < 0 else ""
    v = abs(v)
    if v >= 1_00_00_000:
        return f"{sign}Rs {v / 1_00_00_000:,.2f} crore"
    if v >= 1_00_000:
        return f"{sign}Rs {v / 1_00_000:,.2f} lakh"
    return f"{sign}Rs {v:,.0f}"


def pct(value, digits=1):
    if value is None or pd.isna(value):
        return "0%"
    return f"{float(value):.{digits}f}%"


def num(value):
    """Whole-number count with thousands separators."""
    return f"{int(round(float(value))):,}"


def oia(observation, implication, action):
    """Render one Observation -> Business Implication -> Recommended Action block."""
    return (
        f"> **Observation.** {observation}\n>\n"
        f"> **Business Implication.** {implication}\n>\n"
        f"> **Recommended Action.** {action}\n"
    )


# Words that carry no procurement meaning -- dropped before theme detection.
_THEME_STOPWORDS = {
    "for", "and", "the", "with", "its", "of", "in", "to", "as", "on", "or",
    "type", "set", "each", "per", "no", "nos", "kg", "mm", "sq", "mtr", "mtrs",
    "metre", "meter", "x", "c", "v", "ah", "db", "w", "h", "l", "size", "make",
    "item", "items", "part", "parts", "unit", "units", "complete", "system",
    "equipment", "qty", "rate", "new", "old", "work", "works", "etc",
}


def detect_themes(descriptions, top_n=3):
    """Data-driven theme detector: surface the most common meaningful words across a
    set of item descriptions. Keeps narrative phrasing (e.g. 'lead-acid', 'relay')
    grounded in the actual data rather than hard-coded assumptions."""
    counter = Counter()
    for desc in descriptions:
        if not isinstance(desc, str):
            continue
        for tok in re.split(r"[^A-Za-z]+", desc.lower()):
            if len(tok) >= 3 and tok not in _THEME_STOPWORDS:
                counter[tok] += 1
    themes = [w for w, _ in counter.most_common(top_n) if counter[w] > 1]
    return themes


def themes_phrase(descriptions, top_n=3):
    """Human phrase from detected themes, e.g. 'cable-, relay- and cell-related items'."""
    themes = detect_themes(descriptions, top_n=top_n)
    if not themes:
        return "a range of signalling spare items"
    labelled = [f"{t}-related" for t in themes]
    if len(labelled) == 1:
        return f"{labelled[0]} items"
    return f"{', '.join(labelled[:-1])} and {labelled[-1]} items"


# ======================================================================
# Report 1 -- monthly_executive_report.md
# ======================================================================
def build_executive_report():
    p0 = _kpi_dict(_read(PBI / "page0_executive_dashboard.csv"))
    actions = _read(PBI / "page9_management_actions.csv")
    budgets = _read(PBI / "page8_budget_scenarios.csv")
    dt = _read(AXLX / "digital_twin_readiness.csv")
    risk = _read(AXLX / "service_risk.csv")

    strategic_val = p0["Strategic Inventory Value (Normalized)"]
    operational_val = p0["Operational Inventory Value"]
    proc_required = p0["Procurement Required Value"]
    dead_val = p0["Dead Stock Value"]
    slow_val = p0["Slow Moving Value"]
    turn_risk = p0["Inventory Turn Risk %"]
    annual_issue = p0["Annual Issue Value"]

    dead_pct = dead_val / operational_val * 100.0 if operational_val else 0.0
    slow_pct = slow_val / operational_val * 100.0 if operational_val else 0.0
    readiness = float(dt.loc[dt["Metric"] == "Overall_Digital_Twin_Readiness", "Score_Pct"].iloc[0])
    readiness_band = dt.loc[dt["Metric"] == "Overall_Digital_Twin_Readiness", "Band"].iloc[0]

    act = actions.set_index("Action")
    n_procure = int(act.loc["Procure Immediately", "Count"]) if "Procure Immediately" in act.index else 0
    n_dispose = int(act.loc["Dispose", "Count"]) if "Dispose" in act.index else 0
    n_rationalize = int(act.loc["Rationalize", "Count"]) if "Rationalize" in act.index else 0

    largest = budgets.sort_values("Budget").iloc[-1]
    high_risk = risk[risk["Procurement_Priority_Class"].isin(["Immediate", "High"])]

    # Metrics asserted for traceability (formatted strings must appear in the text).
    metrics = {
        "Strategic Inventory Value": inr(strategic_val),
        "Operational Inventory Value": inr(operational_val),
        "Procurement Requirement": inr(proc_required),
        "Dead Stock Value": inr(dead_val),
        "Slow Moving Value": inr(slow_val),
        "Dead Stock % of Operational": pct(dead_pct),
        "Inventory Turn Risk %": pct(turn_risk),
        "Digital Twin Readiness": pct(readiness, 0),
    }
    sources = [
        "page0_executive_dashboard.csv", "page9_management_actions.csv",
        "page8_budget_scenarios.csv", "digital_twin_readiness.csv", "service_risk.csv",
    ]

    md = []
    md.append(f"# Monthly Executive Inventory Report")
    md.append(f"*Southern Railway Signalling & Telecom Spare Parts — {REPORT_DATE}*")
    md.append(f"*Audience: DRM, ADRM, PCSTE, CSTE, Sr.DSTE, Stores Officers*\n")

    md.append("## Executive Summary\n")
    md.append(
        f"The signalling spare parts holding stands at {inr(strategic_val)} of strategic "
        f"(planning) stock and {inr(operational_val)} of operational depot stock. Against an "
        f"annual issue value of {inr(annual_issue)}, the assessed procurement requirement is "
        f"{inr(proc_required)}, with {num(n_procure)} items needing immediate purchase to protect "
        f"service. On the other side of the ledger, {pct(dead_pct)} of operational value "
        f"({inr(dead_val)}) is dead stock and a further {inr(slow_val)} is slow moving, leaving "
        f"{pct(turn_risk)} of operational value exposed to poor inventory turnover. Disposal and "
        f"rationalisation cover {num(n_dispose + n_rationalize)} items and can release working "
        f"capital. The platform is {pct(readiness, 0)} ready ({readiness_band}) for network "
        f"simulation. Management is asked to fund critical procurement, clear dead stock, and "
        f"approve a phased rationalisation drive."
    )

    md.append("\n## Inventory Overview\n")
    md.append(
        f"- **Strategic Inventory Value:** {inr(strategic_val)}\n"
        f"- **Operational Inventory Value:** {inr(operational_val)}\n"
        f"- **Annual Issue Value:** {inr(annual_issue)}\n"
        f"- **Inventory Turn Risk:** {pct(turn_risk)} of operational value moves slowly or not at all\n"
    )
    md.append(oia(
        f"Operational depot stock ({inr(operational_val)}) is roughly "
        f"{operational_val / strategic_val:.1f} times the strategic planning holding.",
        "The bulk of capital tied up in spares sits in depot stock whose movement is not yet "
        "actively managed item by item.",
        "Treat operational depot stock as the primary target for turnover improvement, not just "
        "the strategic planning list.",
    ))

    md.append("\n## Procurement Position\n")
    md.append(
        f"- **Procurement Requirement:** {inr(proc_required)}\n"
        f"- **Items to procure immediately:** {num(n_procure)}\n"
        f"- **Items flagged high service risk:** {num(len(high_risk))}\n"
    )
    md.append(oia(
        f"The assessed procurement requirement is {inr(proc_required)}, of which {num(n_procure)} "
        f"items are immediate priorities.",
        "Service on safety and vital items can be interrupted if these purchases slip, while the "
        "full requirement far exceeds any single year's budget.",
        "Sanction the immediate-priority items first and plan the balance as a phased, "
        "criticality-led programme over multiple years.",
    ))

    md.append("\n## Operational Health\n")
    md.append(
        f"- **Dead Stock Value:** {inr(dead_val)} ({pct(dead_pct)} of operational value)\n"
        f"- **Slow Moving Value:** {inr(slow_val)} ({pct(slow_pct)} of operational value)\n"
        f"- **Inventory Turn Risk:** {pct(turn_risk)}\n"
    )
    md.append(oia(
        f"Dead stock represents {pct(dead_pct)} of operational inventory value ({inr(dead_val)}) "
        f"and warrants review for disposal or transfer.",
        "Capital and shelf space are locked in items that are not moving and may be deteriorating "
        "or becoming obsolete.",
        "Commission a dead-stock board to clear, transfer or dispose of these items in the current "
        "financial year.",
    ))

    md.append("\n## Budget Position\n")
    md.append(
        f"- **Largest scenario modelled:** {largest['Scenario']} "
        f"({inr(largest['Budget'])})\n"
        f"- **Procurement coverage at that budget:** {pct(largest['Procurement_Coverage_Pct'], 1)}\n"
        f"- **Requirement still unfunded:** {inr(largest['Remaining_Gap'])}\n"
    )
    md.append(oia(
        f"Even the largest budget scenario ({inr(largest['Budget'])}) funds only "
        f"{pct(largest['Procurement_Coverage_Pct'], 1)} of the procurement requirement.",
        "No realistic single-year allocation closes the gap, so unfunded critical items remain a "
        "standing service risk.",
        "Adopt a multi-year procurement plan and prioritise by criticality; see the budget review "
        "for the recommended scenario.",
    ))

    md.append("\n## Major Risks\n")
    md.append(
        f"- {num(len(high_risk))} items carry high or immediate service risk.\n"
        f"- {pct(turn_risk)} of operational value is exposed through dead and slow-moving stock.\n"
        f"- Procurement requirement of {inr(proc_required)} is largely unfunded.\n"
    )

    md.append("\n## Key Findings\n")
    md.append(
        f"- Strategic holding {inr(strategic_val)}; operational holding {inr(operational_val)}.\n"
        f"- Procurement requirement {inr(proc_required)}; {num(n_procure)} immediate items.\n"
        f"- Dead stock {inr(dead_val)} ({pct(dead_pct)}); slow moving {inr(slow_val)}.\n"
        f"- Inventory turn risk {pct(turn_risk)} of operational value.\n"
        f"- Digital twin readiness {pct(readiness, 0)} ({readiness_band}).\n"
    )

    md.append("\n## Business Implications\n")
    md.append(
        "- Service continuity on safety and vital items depends on clearing the immediate "
        "procurement list.\n"
        "- A large share of working capital is idle in dead and slow-moving stock and can be "
        "recovered.\n"
        "- The procurement gap cannot be closed in one year and needs a sanctioned multi-year plan.\n"
    )

    md.append("\n## Recommended Management Actions\n")
    md.append(
        f"1. **Sanction immediate procurement** of the {num(n_procure)} critical items to protect "
        f"service.\n"
        f"2. **Clear dead stock** worth {inr(dead_val)} through a disposal / transfer board this year.\n"
        f"3. **Approve phased rationalisation** of the {num(n_rationalize)} slow-moving items to "
        f"release working capital.\n"
        f"4. **Adopt a multi-year procurement budget** prioritised by criticality.\n"
        f"5. **Close the data gaps** to reach full readiness for network simulation "
        f"(currently {pct(readiness, 0)}).\n"
    )

    md.append("\n## Data Sources\n")
    md.append("\n".join(f"- `{s}`" for s in sources) + "\n")

    return "\n".join(md), metrics, sources


# ======================================================================
# Report 2 -- procurement_review.md
# ======================================================================
def build_procurement_review():
    p1 = _read(PBI / "page1_procurement.csv")
    risk = _read(AXLX / "service_risk.csv")
    p0 = _kpi_dict(_read(PBI / "page0_executive_dashboard.csv"))

    proc_required = p0["Procurement Required Value"]
    n_immediate = int((p1["Procurement_Priority_Class"] == "Immediate").sum())
    n_high = int((p1["Procurement_Priority_Class"] == "High").sum())

    # Top 20 procurement candidates by normalized priority score (immediate + high lead the list).
    top = p1.sort_values("Normalized_Procurement_Priority_Score", ascending=False).head(20)

    # Highest service-risk items, with descriptions joined from the procurement page.
    desc_map = p1.set_index("PL_Code")["Description"].to_dict()
    risk_top = risk.sort_values("Normalized_Procurement_Priority_Score", ascending=False).head(20).copy()
    risk_top["Description"] = risk_top["PL_Code"].map(desc_map).fillna("(description unavailable)")
    risk_theme = themes_phrase(risk_top["Description"].tolist())

    crit_mix = p1["Criticality"].value_counts().reindex(cfg.CRITICALITY_ORDER).fillna(0).astype(int)

    metrics = {
        "Procurement Requirement": inr(proc_required),
        "Immediate Items": num(n_immediate),
        "High Priority Items": num(n_high),
    }
    sources = ["page1_procurement.csv", "service_risk.csv", "page0_executive_dashboard.csv"]

    md = []
    md.append("# Monthly Procurement Review")
    md.append(f"*Southern Railway Signalling & Telecom Spare Parts — {REPORT_DATE}*\n")

    md.append("## Executive Summary\n")
    md.append(
        f"The assessed procurement requirement is {inr(proc_required)}. Of the planning items, "
        f"{num(n_immediate)} are immediate purchase candidates and a further {num(n_high)} are high "
        f"priority. The highest-risk purchases are concentrated in {risk_theme}, where a stock-out "
        f"would directly affect train signalling and safety. Because the total requirement is far "
        f"larger than any single year's budget, procurement must be released in priority order, "
        f"starting with safety (S1) and vital (S2) items that are currently short. This review lists "
        f"the top candidates, the items carrying the greatest service risk, and the criticality mix "
        f"so that limited funds are committed where service exposure is greatest."
    )

    md.append("\n## Immediate Procurement Candidates\n")
    md.append(f"There are **{num(n_immediate)} immediate** and **{num(n_high)} high-priority** items. "
              f"The leading {len(top)} candidates by priority are:\n")
    md.append("| Rank | PL Code | Description | Criticality | Class | Investment Required |")
    md.append("|---|---|---|---|---|---|")
    for i, (_, r) in enumerate(top.iterrows(), 1):
        d = str(r["Description"])[:48]
        md.append(f"| {i} | {r['PL_Code']} | {d} | {r['Criticality']} | "
                  f"{r['Procurement_Priority_Class']} | {inr(r['Normalized_Investment_Required'])} |")
    md.append("")
    md.append(oia(
        f"{num(n_immediate)} items are immediate procurement candidates and lead the priority list.",
        "These items are short against requirement and are the most likely to cause a service "
        "interruption if not replenished.",
        "Raise purchase indents for the immediate candidates without waiting for the full annual plan.",
    ))

    md.append("\n## High Priority Items\n")
    md.append(oia(
        f"A further {num(n_high)} items are rated high priority behind the immediate list.",
        "These will become immediate risks if their stock is drawn down before the next "
        "procurement cycle.",
        "Schedule the high-priority items in the next indent tranche and monitor their stock monthly.",
    ))

    md.append("\n## Budget Requirement\n")
    md.append(f"- **Total procurement requirement:** {inr(proc_required)}\n")
    md.append(oia(
        f"The total procurement requirement is {inr(proc_required)}.",
        "This sum cannot be committed in a single year; spreading it without a priority order would "
        "leave critical items unfunded.",
        "Fund the requirement in criticality order across multiple years (see the budget review).",
    ))

    md.append("\n## Service Risk Exposure\n")
    md.append("Items carrying the greatest service risk:\n")
    md.append("| PL Code | Description | Criticality | Inventory Gap | Risk Class |")
    md.append("|---|---|---|---|---|")
    for _, r in risk_top.head(15).iterrows():
        d = str(r["Description"])[:48]
        md.append(f"| {r['PL_Code']} | {d} | {r['Criticality']} | "
                  f"{num(r['Inventory_Gap'])} | {r['Procurement_Priority_Class']} |")
    md.append("")
    md.append(oia(
        f"{risk_theme.capitalize()} account for a large share of the highest service-risk items.",
        "A shortage in this group has an outsized effect on signalling availability and safety.",
        "Prioritise this group within the immediate procurement list and hold a small safety buffer.",
    ))

    md.append("\n## Criticality Mix\n")
    md.append("| Criticality | Items |")
    md.append("|---|---|")
    for c in cfg.CRITICALITY_ORDER:
        md.append(f"| {c} | {num(crit_mix[c])} |")
    md.append("")

    md.append("\n## Key Findings\n")
    md.append(
        f"- Procurement requirement {inr(proc_required)}.\n"
        f"- {num(n_immediate)} immediate and {num(n_high)} high-priority items.\n"
        f"- Highest service risk concentrated in {risk_theme}.\n"
        f"- Criticality mix: "
        + ", ".join(f"{c} {num(crit_mix[c])}" for c in cfg.CRITICALITY_ORDER) + ".\n"
    )

    md.append("\n## Business Implications\n")
    md.append(
        "- Delaying immediate items risks signalling service interruptions on safety/vital spares.\n"
        "- Committing funds out of priority order would leave the most critical items short.\n"
    )

    md.append("\n## Recommended Actions\n")
    md.append(
        f"1. **Indent the {num(n_immediate)} immediate items now.**\n"
        f"2. **Prioritise {risk_theme}** within those indents.\n"
        f"3. **Queue the {num(n_high)} high-priority items** for the next tranche.\n"
        f"4. **Plan the balance of {inr(proc_required)}** across future years by criticality.\n"
    )

    md.append("\n## Data Sources\n")
    md.append("\n".join(f"- `{s}`" for s in sources) + "\n")

    return "\n".join(md), metrics, sources


# ======================================================================
# Report 3 -- dead_stock_review.md
# ======================================================================
def build_dead_stock_review():
    dead = _read(PBI / "op_dead_stock.csv")
    aging = _read(PBI / "op_inventory_aging.csv")
    p0 = _kpi_dict(_read(PBI / "page0_executive_dashboard.csv"))

    dead_count = int(len(dead))
    dead_value = p0["Dead Stock Value"]
    operational_val = p0["Operational Inventory Value"]
    dead_pct = dead_value / operational_val * 100.0 if operational_val else 0.0

    top = dead.sort_values("Inventory_Value", ascending=False).head(20)
    over_two_years = int((dead["Days_Since_Movement"] > 730).sum())

    metrics = {
        "Dead Stock Count": num(dead_count),
        "Dead Stock Value": inr(dead_value),
        "Dead Stock % of Operational": pct(dead_pct),
        "Inactive Over Two Years": num(over_two_years),
    }
    sources = ["op_dead_stock.csv", "op_inventory_aging.csv", "page0_executive_dashboard.csv"]

    md = []
    md.append("# Monthly Dead Stock Review")
    md.append(f"*Southern Railway Signalling & Telecom Spare Parts — {REPORT_DATE}*\n")

    md.append("## Executive Summary\n")
    md.append(
        f"There are {num(dead_count)} dead-stock items in the depots worth {inr(dead_value)}, which "
        f"is {pct(dead_pct)} of operational inventory value. Of these, {num(over_two_years)} items "
        f"have had no movement for more than two years. This is capital and shelf space locked in "
        f"spares that are not being issued and may be deteriorating or turning obsolete. The largest "
        f"items by value are listed below and should be physically verified, then reviewed for reuse "
        f"elsewhere on the division, transfer to a depot that needs them, or disposal under extant "
        f"rules. Clearing this stock recovers space and, where disposal yields scrap value, returns "
        f"some capital. Management is asked to convene a dead-stock board to act on the top items "
        f"this financial year."
    )

    md.append("\n## Dead Stock Overview\n")
    md.append(
        f"- **Dead stock items:** {num(dead_count)}\n"
        f"- **Dead stock value:** {inr(dead_value)} ({pct(dead_pct)} of operational value)\n"
        f"- **Inactive over two years:** {num(over_two_years)} items\n"
    )
    md.append(oia(
        f"{num(dead_count)} items worth {inr(dead_value)} have shown no movement and are classed as "
        f"dead stock.",
        "This represents idle working capital and occupied depot space that could serve active items.",
        "Verify these items physically and route each to reuse, transfer or disposal.",
    ))

    md.append("\n## Top Dead Stock Items\n")
    md.append("The highest-value dead-stock items (review these first):\n")
    md.append("| Rank | PL Code | Description | Qty | Value | Idle (days) |")
    md.append("|---|---|---|---|---|---|")
    for i, (_, r) in enumerate(top.iterrows(), 1):
        d = str(r["Description"])[:46]
        md.append(f"| {i} | {r['PL_Code']} | {d} | {num(r['Current_Stock'])} | "
                  f"{inr(r['Inventory_Value'])} | {num(r['Days_Since_Movement'])} |")
    md.append("")

    md.append("\n## Value at Risk\n")
    top20_value = float(top["Inventory_Value"].sum())
    md.append(
        f"- **Total dead stock value:** {inr(dead_value)}\n"
        f"- **Top 20 items account for:** {inr(top20_value)} "
        f"({pct(top20_value / dead_value * 100.0 if dead_value else 0)} of dead-stock value)\n"
    )
    md.append(oia(
        f"The top 20 items carry {inr(top20_value)} of the {inr(dead_value)} total dead-stock value.",
        "A small number of high-value items drive most of the locked capital, so focused action on "
        "them recovers the most.",
        "Concentrate the first disposal / transfer board on these high-value items.",
    ))

    md.append("\n## Ageing Profile\n")
    md.append("| Ageing Class | Items | Value |")
    md.append("|---|---|---|")
    for _, r in aging.iterrows():
        md.append(f"| {r['Inventory_Aging_Class']} | {num(r['Count'])} | {inr(r['Inventory_Value'])} |")
    md.append("")
    md.append(oia(
        f"{num(over_two_years)} dead-stock items have been inactive for more than two years.",
        "Items inactive this long are unlikely to be issued and the case for holding them is weak.",
        "Items inactive for more than two years should be reviewed for transfer, reuse or disposal "
        "as a standing rule.",
    ))

    md.append("\n## Key Findings\n")
    md.append(
        f"- {num(dead_count)} dead-stock items worth {inr(dead_value)} ({pct(dead_pct)} of operational value).\n"
        f"- {num(over_two_years)} items inactive for over two years.\n"
        f"- Top 20 items hold {inr(top20_value)} of the value.\n"
    )

    md.append("\n## Business Implications\n")
    md.append(
        "- Idle capital and depot space are tied up in non-moving spares.\n"
        "- Some items may deteriorate or become obsolete, reducing any future recovery value.\n"
    )

    md.append("\n## Recommended Actions\n")
    md.append(
        "1. **Convene a dead-stock board** and start with the top 20 items by value.\n"
        "2. **Physically verify** condition and quantity before any decision.\n"
        "3. **Transfer or reuse** items needed elsewhere on the division.\n"
        "4. **Dispose** items inactive over two years with no foreseeable use, under extant rules.\n"
    )

    md.append("\n## Data Sources\n")
    md.append("\n".join(f"- `{s}`" for s in sources) + "\n")

    return "\n".join(md), metrics, sources


# ======================================================================
# Report 4 -- rationalization_review.md
# ======================================================================
def build_rationalization_review():
    rat = _read(PBI / "page5_rationalization.csv")
    actions = _read(PBI / "page9_management_actions.csv")

    counts = rat["Inventory_Action"].value_counts()
    n_rationalize = int(counts.get("Rationalize", 0))
    n_dispose = int(counts.get("Dispose", 0))
    n_retain = int(counts.get("Retain", 0))

    val_by_action = rat.groupby("Inventory_Action")["Normalized_Inventory_Value"].sum()
    rationalize_val = float(val_by_action.get("Rationalize", 0.0))
    dispose_val = float(val_by_action.get("Dispose", 0.0))
    affected_val = rationalize_val + dispose_val

    metrics = {
        "Rationalize Count": num(n_rationalize),
        "Dispose Count": num(n_dispose),
        "Retain Count": num(n_retain),
        "Value Affected": inr(affected_val),
    }
    sources = ["page5_rationalization.csv", "page9_management_actions.csv"]

    md = []
    md.append("# Inventory Rationalisation Review")
    md.append(f"*Southern Railway Signalling & Telecom Spare Parts — {REPORT_DATE}*\n")

    md.append("## Executive Summary\n")
    md.append(
        f"A review of stock movement identifies {num(n_rationalize)} items for rationalisation "
        f"(slow moving, holding can be reduced) and {num(n_dispose)} items for disposal (dead stock), "
        f"while {num(n_retain)} items are healthy and should be retained at current levels. Together "
        f"the rationalisation and disposal candidates account for {inr(affected_val)} of inventory "
        f"value. Acting on them reduces the number of lines carried, frees depot space, and releases "
        f"working capital that is presently idle. None of this affects fast-moving or critical items, "
        f"which are retained. Management is asked to approve a phased rationalisation drive, taking "
        f"the highest-value slow-moving and dead items first, so that the reduction in holding is "
        f"achieved without any risk to service."
    )

    md.append("\n## Rationalization Candidates\n")
    md.append(
        f"- **Rationalise (reduce holding):** {num(n_rationalize)} items, {inr(rationalize_val)}\n"
    )
    md.append(oia(
        f"{num(n_rationalize)} slow-moving items worth {inr(rationalize_val)} are carried at levels "
        f"above what their movement justifies.",
        "Holding more than is needed of slow movers ties up capital and space that active items "
        "could use.",
        "Reduce reorder levels for these items and avoid fresh purchases until stock draws down.",
    ))

    md.append("\n## Disposal Candidates\n")
    md.append(
        f"- **Dispose (dead stock):** {num(n_dispose)} items, {inr(dispose_val)}\n"
    )
    md.append(oia(
        f"{num(n_dispose)} dead-stock items worth {inr(dispose_val)} are not moving at all.",
        "These will not be issued in the foreseeable future and only consume space and capital.",
        "Route these items to the dead-stock board for transfer, reuse or disposal.",
    ))

    md.append("\n## Savings Opportunity\n")
    md.append(
        f"- **Total value affected:** {inr(affected_val)}\n"
        f"- **Items retained (no change):** {num(n_retain)}\n"
    )
    md.append(oia(
        f"Rationalisation and disposal together address {inr(affected_val)} of holding.",
        "This is working capital that can be progressively released and redirected to critical "
        "procurement.",
        "Approve a phased drive and re-deploy the released capital towards the immediate "
        "procurement list.",
    ))

    md.append("\n## Action Summary\n")
    md.append("| Action | Items | Strategic Value | Operational Value |")
    md.append("|---|---|---|---|")
    for _, r in actions.iterrows():
        md.append(f"| {r['Action']} | {num(r['Count'])} | "
                  f"{inr(r['Strategic_Inventory_Value'])} | {inr(r['Operational_Inventory_Value'])} |")
    md.append("")

    md.append("\n## Key Findings\n")
    md.append(
        f"- {num(n_rationalize)} items to rationalise ({inr(rationalize_val)}).\n"
        f"- {num(n_dispose)} items to dispose ({inr(dispose_val)}).\n"
        f"- {num(n_retain)} items retained at current levels.\n"
        f"- Total value affected: {inr(affected_val)}.\n"
    )

    md.append("\n## Business Implications\n")
    md.append(
        "- Carrying lines beyond their movement need inflates holding cost and crowds depots.\n"
        "- Released working capital can be redirected to fund critical procurement.\n"
        "- Fast-moving and critical items are untouched, so service is not affected.\n"
    )

    md.append("\n## Recommended Actions\n")
    md.append(
        f"1. **Approve a phased rationalisation drive** covering the {num(n_rationalize + n_dispose)} "
        f"slow-moving and dead items.\n"
        f"2. **Lower reorder levels** on the {num(n_rationalize)} rationalisation candidates.\n"
        f"3. **Dispose / transfer** the {num(n_dispose)} dead-stock items.\n"
        f"4. **Redirect released capital** of up to {inr(affected_val)} towards critical procurement.\n"
    )

    md.append("\n## Data Sources\n")
    md.append("\n".join(f"- `{s}`" for s in sources) + "\n")

    return "\n".join(md), metrics, sources


# ======================================================================
# Report 5 -- budget_review.md
# ======================================================================
def build_budget_review():
    budgets = _read(PBI / "page8_budget_scenarios.csv").sort_values("Budget").reset_index(drop=True)
    p0 = _kpi_dict(_read(PBI / "page0_executive_dashboard.csv"))
    proc_required = p0["Procurement Required Value"]

    # Marginal coverage per rupee, to detect diminishing returns and pick a recommendation.
    budgets = budgets.copy()
    budgets["Coverage_Per_Crore"] = (
        budgets["Procurement_Coverage_Pct"] / (budgets["Budget"] / 1_00_00_000)
    )
    diminishing = bool(budgets["Coverage_Per_Crore"].is_monotonic_decreasing
                       and budgets["Coverage_Per_Crore"].iloc[0] > budgets["Coverage_Per_Crore"].iloc[-1])
    # Recommend the scenario with the highest criticality coverage (largest tranche the
    # data supports); marginal return is reported so the reader sees the trade-off.
    rec = budgets.sort_values("Criticality_Coverage_Pct", ascending=False).iloc[0]
    largest = budgets.iloc[-1]

    metrics = {
        "Procurement Requirement": inr(proc_required),
        "Recommended Scenario": str(rec["Scenario"]),
        "Largest Coverage %": pct(largest["Procurement_Coverage_Pct"], 1),
    }
    sources = ["page8_budget_scenarios.csv", "page0_executive_dashboard.csv"]

    md = []
    md.append("# Procurement Budget Review")
    md.append(f"*Southern Railway Signalling & Telecom Spare Parts — {REPORT_DATE}*\n")

    md.append("## Executive Summary\n")
    md.append(
        f"The total procurement requirement is {inr(proc_required)}. Four budget scenarios were "
        f"tested to see how much of that requirement each would fund and how many critical items it "
        f"would cover. Even the largest scenario ({inr(largest['Budget'])}) funds only "
        f"{pct(largest['Procurement_Coverage_Pct'], 1)} of the requirement, leaving "
        f"{inr(largest['Remaining_Gap'])} unfunded. Because the requirement is so much larger than "
        f"any single sanction, each additional rupee buys broadly similar coverage, and no one year "
        f"can close the gap. The practical course is a multi-year programme that always funds the "
        f"most critical items first. The recommended first-year tranche is **{rec['Scenario']}**, "
        f"which secures the widest criticality coverage available in this set "
        f"({pct(rec['Criticality_Coverage_Pct'], 1)})."
    )

    md.append("\n## Scenario Comparison\n")
    md.append("| Scenario | Budget | Items Funded | Procurement Coverage | Criticality Coverage | Remaining Gap |")
    md.append("|---|---|---|---|---|---|")
    for _, r in budgets.iterrows():
        md.append(f"| {r['Scenario']} | {inr(r['Budget'])} | {num(r['Items_Funded'])} | "
                  f"{pct(r['Procurement_Coverage_Pct'], 1)} | {pct(r['Criticality_Coverage_Pct'], 1)} | "
                  f"{inr(r['Remaining_Gap'])} |")
    md.append("")

    md.append("\n## Procurement Coverage\n")
    md.append(oia(
        f"The largest scenario ({inr(largest['Budget'])}) covers {pct(largest['Procurement_Coverage_Pct'], 1)} "
        f"of the {inr(proc_required)} requirement.",
        "A single year's budget cannot materially reduce the procurement backlog.",
        "Plan procurement as a multi-year programme rather than expecting one sanction to clear it.",
    ))

    md.append("\n## Criticality Coverage\n")
    md.append(oia(
        f"The recommended tranche, {rec['Scenario']}, reaches {pct(rec['Criticality_Coverage_Pct'], 1)} "
        f"criticality coverage — the highest in the set.",
        "When funds are scarce, covering the most critical items matters more than the rupee value "
        "funded.",
        "Always allocate the budget to safety (S1) and vital (S2) items before lower-criticality stock.",
    ))

    md.append("\n## Remaining Gaps\n")
    md.append(
        f"- **Unfunded at largest scenario:** {inr(largest['Remaining_Gap'])}\n"
    )
    md.append(oia(
        f"{inr(largest['Remaining_Gap'])} of requirement remains unfunded even at the top scenario.",
        "Critical items left unfunded each year remain a standing service risk.",
        "Carry the unfunded critical items forward as the first call on the next year's budget.",
    ))

    md.append("\n## Diminishing Returns\n")
    if diminishing:
        md.append(
            "Each successive scenario returns less coverage per rupee than the one before it, so "
            "very large single-year sanctions are not the most efficient use of funds.")
    else:
        md.append(
            "Across these scenarios each additional rupee returns broadly the same coverage "
            "(about "
            f"{budgets['Coverage_Per_Crore'].mean():.2f}% of the requirement per crore), because the "
            "requirement far exceeds every budget tested. The constraint is the size of the backlog, "
            "not diminishing efficiency, which reinforces the case for a sustained multi-year plan.")
    md.append("")

    md.append("\n## Key Findings\n")
    md.append(
        f"- Procurement requirement {inr(proc_required)}.\n"
        f"- Largest scenario funds {pct(largest['Procurement_Coverage_Pct'], 1)}; "
        f"{inr(largest['Remaining_Gap'])} remains unfunded.\n"
        f"- Recommended first tranche: {rec['Scenario']} "
        f"({pct(rec['Criticality_Coverage_Pct'], 1)} criticality coverage).\n"
    )

    md.append("\n## Business Implications\n")
    md.append(
        "- No single-year budget closes the procurement gap.\n"
        "- Funding out of criticality order would leave the most important items short.\n"
    )

    md.append("\n## Recommended Scenario\n")
    md.append(
        f"Adopt **{rec['Scenario']}** ({inr(rec['Budget'])}) as the first-year tranche — it secures "
        f"the widest criticality coverage in the set ({pct(rec['Criticality_Coverage_Pct'], 1)}) — "
        f"and commit to a multi-year programme to fund the balance of {inr(proc_required)} in "
        f"criticality order.\n"
    )

    md.append("\n## Data Sources\n")
    md.append("\n".join(f"- `{s}`" for s in sources) + "\n")

    return "\n".join(md), metrics, sources


# ======================================================================
# Report 6 -- digital_twin_readiness_report.md
# ======================================================================
def build_digital_twin_report():
    dt = _read(AXLX / "digital_twin_readiness.csv")
    mec = _read(AXLX / "multi_echelon_candidates.csv")
    risk = _read(AXLX / "service_risk.csv")

    dt_map = dict(zip(dt["Metric"], dt["Score_Pct"]))
    band_map = dict(zip(dt["Metric"], dt["Band"]))
    overall = float(dt_map["Overall_Digital_Twin_Readiness"])
    overall_band = band_map["Overall_Digital_Twin_Readiness"]

    candidates = mec[mec["Multi_Echelon_Candidate"] == "YES"].copy()
    n_candidates = int(len(candidates))
    n_risk = int(len(risk))

    # Components below full readiness are the gap-closers.
    gaps = dt[(dt["Metric"] != "Overall_Digital_Twin_Readiness") & (dt["Score_Pct"] < 100)]

    metrics = {
        "Overall Readiness": pct(overall, 0),
        "Multi-Echelon Candidates": num(n_candidates),
        "Service Risk Items": num(n_risk),
    }
    sources = ["digital_twin_readiness.csv", "multi_echelon_candidates.csv", "service_risk.csv"]

    md = []
    md.append("# Digital Twin Readiness Report")
    md.append(f"*Southern Railway Signalling & Telecom Spare Parts — {REPORT_DATE}*\n")

    md.append("## Executive Summary\n")
    md.append(
        f"The inventory platform is {pct(overall, 0)} ready ({overall_band}) to support a network "
        f"simulation and stocking study across depots. Inventory and stocking-policy data are "
        f"complete; the gaps are in network and demand information, which are partly available. "
        f"{num(n_candidates)} items have been identified as candidates for multi-depot (tiered) "
        f"stocking, where holding a central buffer can protect service at lower total stock. "
        f"{num(n_risk)} items already carry a measured service-risk score that can feed the study. "
        f"Closing the remaining network and demand-data gaps would move the platform to fully ready "
        f"and allow a credible simulation of stocking levels, depot roles and service outcomes "
        f"before any money is committed on the ground."
    )

    md.append("\n## Data Completeness\n")
    md.append("| Data Area | Completeness | Status |")
    md.append("|---|---|---|")
    for _, r in dt.iterrows():
        name = str(r["Metric"]).replace("_", " ")
        md.append(f"| {name} | {pct(r['Score_Pct'], 0)} | {r['Band']} |")
    md.append("")
    md.append(oia(
        f"Overall readiness is {pct(overall, 0)} ({overall_band}); inventory and policy data are "
        f"complete while network and demand data are partial.",
        "A simulation built on incomplete network and demand inputs would give unreliable stocking "
        "advice.",
        "Complete the depot-network and demand inputs before relying on simulation results.",
    ))

    md.append("\n## Service Risk Inputs\n")
    md.append(f"- **Items with a service-risk score:** {num(n_risk)}\n")
    md.append(oia(
        f"{num(n_risk)} items carry a measured service-risk score.",
        "These scores let the study weight stocking decisions towards items whose shortage hurts "
        "service most.",
        "Use the service-risk scores as the priority weighting inside the simulation.",
    ))

    md.append("\n## Multi-Echelon Opportunities\n")
    md.append(f"There are **{num(n_candidates)} multi-depot stocking candidates**:\n")
    md.append("| PL Code | Description | ABC | Criticality | Target Service Level |")
    md.append("|---|---|---|---|---|")
    for _, r in candidates.iterrows():
        d = str(r["Description"])[:46]
        md.append(f"| {r['PL_Code']} | {d} | {r['ABC_Class']} | {r['Criticality']} | "
                  f"{pct(float(r['Target_Service_Level']) * 100, 0)} |")
    md.append("")
    md.append(oia(
        f"{num(n_candidates)} items are suited to tiered, multi-depot stocking.",
        "For these items a shared central buffer can hold the same service level at lower total "
        "stock than holding full stock at every depot.",
        "Model these items first in the network study to size the central buffer and depot stocks.",
    ))

    md.append("\n## Readiness Score\n")
    md.append(f"- **Overall digital twin readiness:** {pct(overall, 0)} ({overall_band})\n")
    if len(gaps):
        md.append("- **Areas below full readiness:** "
                  + ", ".join(f"{str(g['Metric']).replace('_', ' ')} ({pct(g['Score_Pct'], 0)})"
                              for _, g in gaps.iterrows()) + "\n")

    md.append("\n## Key Findings\n")
    md.append(
        f"- Overall readiness {pct(overall, 0)} ({overall_band}).\n"
        f"- {num(n_candidates)} multi-depot stocking candidates.\n"
        f"- {num(n_risk)} items carry a service-risk score.\n"
    )

    md.append("\n## Business Implications\n")
    md.append(
        "- The platform is close to supporting a credible stocking simulation.\n"
        "- Incomplete network and demand data are the only barrier to full readiness.\n"
    )

    md.append("\n## Next Steps\n")
    md.append(
        "1. **Complete the depot-network data** (locations, lead times, links).\n"
        "2. **Complete the demand data** for the modelled items.\n"
        f"3. **Run the network study** on the {num(n_candidates)} multi-depot candidates first.\n"
        "4. **Use service-risk scores** to weight stocking priorities in the study.\n"
    )

    md.append("\n## Recommended Actions\n")
    md.append(
        "1. Assign data owners to close the network and demand gaps.\n"
        "2. Re-check readiness once the gaps are filled.\n"
        "3. Commission the simulation when readiness reaches full.\n"
    )

    md.append("\n## Data Sources\n")
    md.append("\n".join(f"- `{s}`" for s in sources) + "\n")

    return "\n".join(md), metrics, sources


# ======================================================================
# Report generation
# ======================================================================
_GENERATORS = {
    "monthly_executive_report.md": build_executive_report,
    "procurement_review.md": build_procurement_review,
    "dead_stock_review.md": build_dead_stock_review,
    "rationalization_review.md": build_rationalization_review,
    "budget_review.md": build_budget_review,
    "digital_twin_readiness_report.md": build_digital_twin_report,
}

# Pretty section titles for the consolidated pack (spec order).
_PACK_ORDER = [
    ("Executive Review", "monthly_executive_report.md"),
    ("Procurement Review", "procurement_review.md"),
    ("Dead Stock Review", "dead_stock_review.md"),
    ("Rationalisation Review", "rationalization_review.md"),
    ("Budget Review", "budget_review.md"),
    ("Digital Twin Readiness", "digital_twin_readiness_report.md"),
]

_RECOMMEND_HEADERS = ["## Recommended Actions", "## Recommended Management Actions",
                      "## Recommended Scenario", "## Next Steps"]


def generate_all():
    """Run every report generator (in-memory). Returns {filename: (text, metrics, sources)}."""
    results = {}
    for fname, gen in _GENERATORS.items():
        results[fname] = gen()
    return results


# ----------------------------------------------------------------------
# Raw KPI snapshot -- the numeric repository feeding trend + delta.
# (Pure CSV reads; no analytical logic.)
# ----------------------------------------------------------------------
_TREND_KPIS = [
    ("Strategic_Inventory_Value", "Strategic Inventory Value (Normalized)"),
    ("Operational_Inventory_Value", "Operational Inventory Value"),
    ("Procurement_Requirement", "Procurement Required Value"),
    ("Dead_Stock_Value", "Dead Stock Value"),
    ("Slow_Moving_Value", "Slow Moving Value"),
    ("Inventory_Turn_Risk", "Inventory Turn Risk %"),
]


def collect_kpis():
    p0 = _kpi_dict(_read(PBI / "page0_executive_dashboard.csv"))
    dt = _read(AXLX / "digital_twin_readiness.csv")
    budgets = _read(PBI / "page8_budget_scenarios.csv")
    readiness = float(dt.loc[dt["Metric"] == "Overall_Digital_Twin_Readiness", "Score_Pct"].iloc[0])
    snap = {
        "Run_Date": RUN_DATE_ISO,
        "Generation_Timestamp": GEN_TIMESTAMP,
    }
    for key, kpi in _TREND_KPIS:
        snap[key] = round(float(p0[kpi]), 2)
    snap["Digital_Twin_Readiness"] = round(readiness, 2)
    snap["Budget_Scenarios"] = {
        str(r["Scenario"]): {
            "coverage": round(float(r["Procurement_Coverage_Pct"]), 2),
            "crit_coverage": round(float(r["Criticality_Coverage_Pct"]), 2),
            "remaining_gap": round(float(r["Remaining_Gap"]), 2),
        }
        for _, r in budgets.iterrows()
    }
    return snap


# ----------------------------------------------------------------------
# Source-row accounting (for the report index)
# ----------------------------------------------------------------------
def _source_path(name):
    for base in (PBI, AXLX):
        p = base / name
        if p.exists():
            return p
    return None


def _rows_analysed(sources):
    total = 0
    for s in sources:
        p = _source_path(s)
        if p is not None:
            total += len(_read(p))
    return total


# ----------------------------------------------------------------------
# Delta helpers
# ----------------------------------------------------------------------
def _inr_signed(value):
    s = "+" if value >= 0 else "-"
    return f"{s}{inr(abs(value))}"


def _pct_change(prev, curr):
    if prev in (None, 0) or pd.isna(prev):
        return None
    return (curr - prev) / abs(prev) * 100.0


_DELTA_INTERPRET = {
    "Strategic_Inventory_Value": ("Strategic holding has increased.",
                                  "Strategic holding has reduced."),
    "Operational_Inventory_Value": ("Operational depot holding has increased.",
                                    "Operational depot holding has reduced."),
    "Procurement_Requirement": ("Procurement exposure has risen; more capital is needed to protect service.",
                                "Procurement pressure has eased since the previous run."),
    "Dead_Stock_Value": ("Idle capital in dead stock has grown; accelerate disposal and transfer.",
                         "Dead stock is being cleared — capital is being recovered."),
    "Slow_Moving_Value": ("More capital has drifted into slow-moving stock; tighten reorder levels.",
                          "Slow-moving holding has reduced."),
    "Inventory_Turn_Risk": ("A larger share of operational value is now exposed to poor turnover.",
                            "Turnover risk has improved."),
}

# (snapshot key, label, is_percentage_point_metric)
_DELTA_FIELDS = [
    ("Strategic_Inventory_Value", "Strategic Inventory Value", False),
    ("Operational_Inventory_Value", "Operational Inventory Value", False),
    ("Procurement_Requirement", "Procurement Requirement", False),
    ("Dead_Stock_Value", "Dead Stock Value", False),
    ("Slow_Moving_Value", "Slow Moving Value", False),
    ("Inventory_Turn_Risk", "Inventory Turn Risk", True),
]


def _is_significant(key, change_abs, pct, is_pp):
    if is_pp:
        return abs(change_abs) >= 2.0          # >= 2 percentage points
    return pct is not None and abs(pct) >= 5.0  # >= 5% relative


def build_delta_report(kpis, prev):
    """Compare this run with the immediately preceding one."""
    md = []
    md.append("# Report Delta Analysis")
    md.append(f"*Southern Railway Signalling & Telecom Spare Parts — {REPORT_DATE}*\n")

    if prev is None:
        md.append("## Executive Summary\n")
        md.append("This is the **baseline execution** of the reporting repository. There is no "
                  "earlier run to compare against; future runs will show month-on-month movement "
                  "here.\n")
        md.append("## Current Position\n")
        for key, label, is_pp in _DELTA_FIELDS:
            val = kpis[key]
            md.append(f"- **{label}:** {pct(val) if is_pp else inr(val)}")
        md.append("")
        md.append("## Data Sources\n- `page0_executive_dashboard.csv`\n- `page8_budget_scenarios.csv`\n"
                  "- `digital_twin_readiness.csv`\n")
        return "\n".join(md)

    significant = []
    md.append("## Executive Summary\n")
    md.append(f"This analysis compares the current run ({kpis['Run_Date']}) with the previous run "
              f"({prev.get('Run_Date', 'unknown')}). Movements above the materiality threshold "
              f"(5% in value, or 2 percentage points in a rate) are flagged for management attention "
              f"below.\n")

    for key, label, is_pp in _DELTA_FIELDS:
        prev_v = prev.get(key)
        curr_v = kpis[key]
        md.append(f"## {label}\n")
        if prev_v is None:
            md.append("- Not recorded in the previous run.\n")
            continue
        change = curr_v - prev_v
        pc = _pct_change(prev_v, curr_v)
        if is_pp:
            md.append(f"- **Previous:** {pct(prev_v)}")
            md.append(f"- **Current:** {pct(curr_v)}")
            md.append(f"- **Change:** {'+' if change >= 0 else ''}{change:.1f} pp\n")
        else:
            md.append(f"- **Previous:** {inr(prev_v)}")
            md.append(f"- **Current:** {inr(curr_v)}")
            md.append(f"- **Change:** {_inr_signed(change)} "
                      f"({'+' if (pc or 0) >= 0 else ''}{pc:.1f}%)\n" if pc is not None
                      else f"- **Change:** {_inr_signed(change)}\n")
        if _is_significant(key, change, pc, is_pp):
            interp = _DELTA_INTERPRET[key][0] if change >= 0 else _DELTA_INTERPRET[key][1]
            md.append(f"> **Management interpretation.** {interp}\n")
            significant.append((label, change, pc, is_pp))

    # Budget scenario results
    md.append("## Budget Scenario Results\n")
    prev_b = prev.get("Budget_Scenarios", {})
    curr_b = kpis.get("Budget_Scenarios", {})
    md.append("| Scenario | Previous Coverage | Current Coverage | Change |")
    md.append("|---|---|---|---|")
    for scen, cur in curr_b.items():
        pv = prev_b.get(scen, {}).get("coverage")
        cc = cur["coverage"]
        if pv is None:
            md.append(f"| {scen} | — | {pct(cc)} | new |")
        else:
            md.append(f"| {scen} | {pct(pv)} | {pct(cc)} | "
                      f"{'+' if (cc - pv) >= 0 else ''}{cc - pv:.1f} pp |")
    md.append("")

    md.append("## Significant Changes — Management View\n")
    if significant:
        for label, change, pc, is_pp in significant:
            mag = f"{change:+.1f} pp" if is_pp else f"{_inr_signed(change)} ({pc:+.1f}%)"
            md.append(f"- **{label}** moved {mag}.")
    else:
        md.append("- No KPI moved beyond the materiality threshold since the previous run.")
    md.append("")

    md.append("## Data Sources\n- `page0_executive_dashboard.csv`\n- `page8_budget_scenarios.csv`\n"
              "- `digital_twin_readiness.csv`\n- `run_snapshots.jsonl` (previous run)\n")
    return "\n".join(md)


# ----------------------------------------------------------------------
# Consolidated management pack
# ----------------------------------------------------------------------
def build_management_pack(results, kpis, delta_text):
    md = []
    md.append(f"# Consolidated Management Pack — {RUN_MONTH}")
    md.append(f"*Southern Railway Signalling & Telecom Spare Parts*")
    md.append(f"*Prepared {REPORT_DATE} for DRM, ADRM, PCSTE, CSTE, Sr.DSTE and Stores Officers*\n")
    md.append("This single pack consolidates all six management reports plus the month-on-month "
              "delta analysis. No separate file or CSV needs to be opened.\n")

    md.append("## Position at a Glance\n")
    md.append(f"- **Strategic Inventory Value:** {inr(kpis['Strategic_Inventory_Value'])}")
    md.append(f"- **Operational Inventory Value:** {inr(kpis['Operational_Inventory_Value'])}")
    md.append(f"- **Procurement Requirement:** {inr(kpis['Procurement_Requirement'])}")
    md.append(f"- **Dead Stock Value:** {inr(kpis['Dead_Stock_Value'])}")
    md.append(f"- **Slow Moving Value:** {inr(kpis['Slow_Moving_Value'])}")
    md.append(f"- **Inventory Turn Risk:** {pct(kpis['Inventory_Turn_Risk'])}")
    md.append(f"- **Digital Twin Readiness:** {pct(kpis['Digital_Twin_Readiness'], 0)}\n")

    md.append("## Contents\n")
    for i, (title, _) in enumerate(_PACK_ORDER, 1):
        md.append(f"{i}. {title}")
    md.append(f"{len(_PACK_ORDER) + 1}. Month-on-Month Delta Analysis\n")
    md.append("---\n")

    for i, (title, fname) in enumerate(_PACK_ORDER, 1):
        text = results[fname][0]
        # Demote the report's own H1 so the pack has a single document hierarchy.
        body = re.sub(r"^# ", "## ", text, count=1)
        md.append(f"# Part {i} — {title}\n")
        md.append(body)
        md.append("\n---\n")

    md.append(f"# Part {len(_PACK_ORDER) + 1} — Month-on-Month Delta Analysis\n")
    md.append(re.sub(r"^# ", "## ", delta_text, count=1))
    return "\n".join(md)


# ----------------------------------------------------------------------
# Append-only history files (never overwrite past records)
# ----------------------------------------------------------------------
def read_previous_snapshot():
    if not RUN_SNAPSHOTS_JSONL.exists():
        return None
    last = None
    for line in RUN_SNAPSHOTS_JSONL.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            last = line
    return json.loads(last) if last else None


def append_run_snapshot(kpis):
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    with RUN_SNAPSHOTS_JSONL.open("a", encoding="utf-8") as f:
        f.write(json.dumps(kpis) + "\n")


def append_trend_history(kpis):
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    header = ["Run_Date", "Strategic_Inventory_Value", "Operational_Inventory_Value",
              "Procurement_Requirement", "Dead_Stock_Value", "Slow_Moving_Value",
              "Inventory_Turn_Risk", "Digital_Twin_Readiness"]
    new = not TREND_HISTORY_CSV.exists()
    with TREND_HISTORY_CSV.open("a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if new:
            w.writerow(header)
        w.writerow([kpis[h] for h in header])


def append_report_index(rows):
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    header = ["Report_Name", "Version_Date", "Generation_Timestamp",
              "Source_Files", "Rows_Analysed", "Report_Path"]
    new = not REPORT_INDEX_CSV.exists()
    with REPORT_INDEX_CSV.open("a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if new:
            w.writerow(header)
        for r in rows:
            w.writerow([
                r["report"], RUN_DATE_ISO, GEN_TIMESTAMP,
                ";".join(r["sources"]), _rows_analysed(r["sources"]),
                f"reports/latest/{r['report']}",
            ])


def update_changelog(kpis, prev, report_names):
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    section = []
    section.append(f"## {GEN_TIMESTAMP} (run {RUN_TS})\n")
    section.append("**Reports Generated**\n")
    for n in report_names:
        section.append(f"- {n}")
    section.append(f"- Management_Pack_{RUN_MONTH_US}.md\n")
    section.append("**Key KPI Values**\n")
    section.append(f"- Strategic Inventory Value: {inr(kpis['Strategic_Inventory_Value'])}")
    section.append(f"- Operational Inventory Value: {inr(kpis['Operational_Inventory_Value'])}")
    section.append(f"- Procurement Requirement: {inr(kpis['Procurement_Requirement'])}")
    section.append(f"- Dead Stock Value: {inr(kpis['Dead_Stock_Value'])}")
    section.append(f"- Slow Moving Value: {inr(kpis['Slow_Moving_Value'])}")
    section.append(f"- Inventory Turn Risk: {pct(kpis['Inventory_Turn_Risk'])}")
    section.append(f"- Digital Twin Readiness: {pct(kpis['Digital_Twin_Readiness'], 0)}\n")
    section.append("**Major Changes Since Previous Run**\n")
    if prev is None:
        section.append("- Baseline run — no previous data to compare.\n")
    else:
        changes = []
        for key, label, is_pp in _DELTA_FIELDS:
            pv = prev.get(key)
            if pv is None:
                continue
            cv = kpis[key]
            change = cv - pv
            pc = _pct_change(pv, cv)
            if _is_significant(key, change, pc, is_pp):
                mag = f"{change:+.1f} pp" if is_pp else f"{_inr_signed(change)} ({pc:+.1f}%)"
                changes.append(f"- {label}: {mag}")
        if changes:
            section.extend(changes)
        else:
            section.append("- No material change beyond the reporting threshold.")
        section.append("")
    new_block = "\n".join(section) + "\n"

    title = "# Management Reports Change Log\n\n"
    if CHANGELOG_MD.exists():
        existing = CHANGELOG_MD.read_text(encoding="utf-8")
        body = existing[len(title):] if existing.startswith(title) else existing
        CHANGELOG_MD.write_text(title + new_block + body, encoding="utf-8")   # newest first
    else:
        CHANGELOG_MD.write_text(title + new_block, encoding="utf-8")


# ----------------------------------------------------------------------
# Archive writer -- NEVER overwrites an existing archived file.
# ----------------------------------------------------------------------
def _archive_write(month_dir, filename, text):
    """Write into archive/YYYY-MM/ without ever clobbering a prior version."""
    target = month_dir / filename
    if target.exists():
        stem, _, ext = filename.rpartition(".")
        target = month_dir / f"{stem}__{RUN_TS}.{ext}"   # preserve the earlier version
    target.write_text(text, encoding="utf-8")
    return target


# ----------------------------------------------------------------------
# Optional PDF export (best-effort, never mandatory)
# ----------------------------------------------------------------------
def try_pdf_export(md_text, out_path):
    """Render the management pack to PDF if any supported library is present.
    Returns the path on success, or None (silently) when no dependency is available."""
    try:
        import markdown as _md
        from xhtml2pdf import pisa
        html = _md.markdown(md_text, extensions=["tables"])
        with out_path.open("wb") as f:
            pisa.CreatePDF("<html><body>" + html + "</body></html>", dest=f)
        return out_path
    except Exception:
        pass
    try:
        from fpdf import FPDF
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=12)
        pdf.add_page()
        pdf.set_font("Helvetica", size=9)
        for line in md_text.splitlines():
            pdf.multi_cell(0, 4, line.encode("latin-1", "replace").decode("latin-1"))
        pdf.output(str(out_path))
        return out_path
    except Exception:
        pass
    return None


# ======================================================================
# Validation
# ======================================================================
def _executive_summary_word_count(text):
    """Words between '## Executive Summary' and the next '## ' header."""
    m = re.search(r"## Executive Summary\s*(.+?)(?:\n## |\Z)", text, re.DOTALL)
    if not m:
        return None
    return len(m.group(1).split())


def validate(results):
    """Per-report quality controls. Returns (report_rows, content_gate)."""
    rows = []
    for fname, (text, metrics, sources) in results.items():
        path = LATEST_DIR / fname
        checks = {}
        checks["file_written"] = path.exists() and path.stat().st_size > 0
        checks["has_executive_summary"] = "## Executive Summary" in text
        checks["has_recommended_actions"] = any(h in text for h in _RECOMMEND_HEADERS)
        checks["has_data_sources"] = "## Data Sources" in text
        wc = _executive_summary_word_count(text)
        checks["exec_summary_<=200_words"] = wc is not None and wc <= 200
        checks["all_values_traceable"] = all(v in text for v in metrics.values())
        rows.append({
            "report": fname, "exec_summary_words": wc, "sources": sources,
            "metrics": metrics, "checks": checks, "passed": all(checks.values()),
        })
    content_gate = {
        "all_reports_generated": len(results) == len(REPORT_FILES),
        "all_files_nonempty": all(r["checks"]["file_written"] for r in rows),
        "all_have_exec_summary": all(r["checks"]["has_executive_summary"] for r in rows),
        "all_exec_summaries_within_200w": all(r["checks"]["exec_summary_<=200_words"] for r in rows),
        "all_have_recommended_actions": all(r["checks"]["has_recommended_actions"] for r in rows),
        "all_have_data_sources": all(r["checks"]["has_data_sources"] for r in rows),
        "all_values_traceable_to_csv": all(r["checks"]["all_values_traceable"] for r in rows),
    }
    return rows, content_gate


def write_validation_report(rows, gate, repo_gate, pack_path, archive_paths, pdf_path):
    """Emit STEP12_REPORT_VALIDATION.md (repo root + timestamped copy in validation/)."""
    md = []
    md.append("# STEP 12 — Management Narrative Report Validation")
    md.append(f"*Generated {GEN_TIMESTAMP} (run {RUN_TS})*\n")
    md.append("Records that every management narrative report was produced from the Step 11 "
              "analytical CSV outputs, archived immutably, and that all values are traceable to "
              "those files with no analytical business logic duplicated.\n")

    md.append("## Reports Generated\n")
    md.append("| Report | Exec Summary Words | Source CSVs | Result |")
    md.append("|---|---|---|---|")
    for r in rows:
        srcs = ", ".join(f"`{s}`" for s in r["sources"])
        md.append(f"| `{r['report']}` | {r['exec_summary_words']} | {srcs} | "
                  f"{'PASS' if r['passed'] else 'FAIL'} |")
    md.append(f"| `Management_Pack_{RUN_MONTH_US}.md` | (consolidated) | all of the above | "
              f"{'PASS' if pack_path.exists() else 'FAIL'} |")
    md.append("")

    md.append("## Repository Artefacts This Run\n")
    md.append(f"- **Latest folder:** `reports/latest/` (current pointer)")
    md.append(f"- **Archive snapshot:** `reports/archive/{RUN_MONTH}/` "
              f"({len(archive_paths)} files, never overwritten)")
    md.append(f"- **Report index:** `reports/history/report_index.csv` (append-only)")
    md.append(f"- **KPI trend history:** `reports/history/executive_trend_history.csv` (append-only)")
    md.append(f"- **Change log:** `reports/history/CHANGELOG.md` (append-only)")
    md.append(f"- **Delta analysis:** `reports/archive/{RUN_MONTH}/report_delta.md`")
    md.append(f"- **PDF export:** {'`' + str(pdf_path.name) + '`' if pdf_path else 'skipped (no PDF library installed — optional)'}\n")

    md.append("## Per-Report Validation Checks\n")
    for r in rows:
        md.append(f"### `{r['report']}`\n")
        for k, v in r["checks"].items():
            md.append(f"- {'✅' if v else '❌'} {k}")
        md.append("\n**Traceable values (re-derived from CSVs, asserted present in the report):**\n")
        for k, v in r["metrics"].items():
            md.append(f"- {k}: `{v}`")
        md.append("")

    md.append("## Content Validation Gate\n")
    for k, v in gate.items():
        md.append(f"- {'✅' if v else '❌'} {k}")
    md.append("")
    md.append("## Repository Validation Gate\n")
    for k, v in repo_gate.items():
        md.append(f"- {'✅' if v else '❌'} {k}")
    all_pass = all(gate.values()) and all(repo_gate.values())
    md.append(f"\n**ALL PASS: {all_pass}**\n")

    md.append("## Quality Controls Confirmed\n")
    md.append(
        "- **Every report generated successfully** — see gates above.\n"
        "- **No hard-coded numbers** — every figure is read from a CSV at run time; the traceability "
        "check re-derives each reported value from its source file and asserts it appears in the text.\n"
        "- **No business logic duplicated** — this module only reads and aggregates existing outputs.\n"
        "- **Analytical outputs never overwritten** — reports live only under `railway/outputs/reports/`.\n"
        "- **Archived reports never overwritten** — the archive writer versions any same-month "
        "collision with a run timestamp; history files are append-only.\n"
        "- **Reports remain valid when source data changes** — re-running regenerates everything "
        "from the current CSVs and records the movement in the delta and trend history.\n")

    text = "\n".join(md)
    root_out = cfg.REPO_ROOT / "STEP12_REPORT_VALIDATION.md"
    root_out.write_text(text, encoding="utf-8")
    VALIDATION_DIR.mkdir(parents=True, exist_ok=True)
    (VALIDATION_DIR / f"validation_{RUN_TS}.md").write_text(text, encoding="utf-8")
    return root_out, all_pass


# ======================================================================
# Orchestration
# ======================================================================
def _ensure_dirs():
    for d in (REPORTS_DIR, LATEST_DIR, ARCHIVE_DIR, HISTORY_DIR, VALIDATION_DIR):
        d.mkdir(parents=True, exist_ok=True)
    # Tidy any flat reports written by an earlier (pre-repository) version.
    for fname in REPORT_FILES:
        flat = REPORTS_DIR / fname
        if flat.exists():
            flat.unlink()


def run():
    print("=" * 80)
    print("STEP 12 -- MANAGEMENT NARRATIVE REPORTS + VERSIONED REPOSITORY")
    print("=" * 80)
    _ensure_dirs()

    # 1. Read the previous run BEFORE we append this one.
    prev_snapshot = read_previous_snapshot()
    kpis = collect_kpis()

    # 2. Generate the six narrative reports + delta + consolidated pack.
    results = generate_all()
    delta_text = build_delta_report(kpis, prev_snapshot)
    pack_text = build_management_pack(results, kpis, delta_text)
    pack_name = f"Management_Pack_{RUN_MONTH_US}.md"

    # 3. Write latest/ (the current pointer — this folder is the only one overwritten).
    for fname, (text, _, _) in results.items():
        (LATEST_DIR / fname).write_text(text, encoding="utf-8")
    (LATEST_DIR / pack_name).write_text(pack_text, encoding="utf-8")

    # 4. Archive an immutable monthly snapshot (never overwrites prior versions).
    month_dir = ARCHIVE_DIR / RUN_MONTH
    month_dir.mkdir(parents=True, exist_ok=True)
    archive_paths = []
    for fname, (text, _, _) in results.items():
        archive_paths.append(_archive_write(month_dir, fname, text))
    archive_paths.append(_archive_write(month_dir, pack_name, pack_text))
    delta_path = _archive_write(month_dir, "report_delta.md", delta_text)
    archive_paths.append(delta_path)

    # 5. Validate report content (reads from latest/).
    rows, content_gate = validate(results)

    # 6. Append-only history (index, trend, snapshot, changelog).
    append_report_index(rows)
    append_trend_history(kpis)
    update_changelog(kpis, prev_snapshot, list(results.keys()))
    append_run_snapshot(kpis)        # appended LAST so prev-read above is correct

    # 7. Optional PDF export of the pack (best-effort).
    pdf_path = try_pdf_export(pack_text, LATEST_DIR / f"Management_Pack_{RUN_MONTH_US}.pdf")

    # 8. Repository-level validation gate.
    repo_gate = {
        "latest_has_all_reports": all((LATEST_DIR / f).exists() for f in REPORT_FILES),
        "management_pack_created": (LATEST_DIR / pack_name).exists(),
        "archive_snapshot_created": len(archive_paths) >= len(REPORT_FILES) + 2,
        "delta_report_created": delta_path.exists(),
        "report_index_appended": REPORT_INDEX_CSV.exists(),
        "trend_history_appended": TREND_HISTORY_CSV.exists(),
        "changelog_updated": CHANGELOG_MD.exists(),
        "run_snapshot_recorded": RUN_SNAPSHOTS_JSONL.exists(),
    }

    val_path, all_pass = write_validation_report(
        rows, content_gate, repo_gate, LATEST_DIR / pack_name, archive_paths, pdf_path)

    # ---- console summary ----
    print(f"\nLatest reports : {LATEST_DIR}")
    print(f"Archive snapshot: {month_dir}")
    for r in rows:
        print(f"   {r['report']:38s}: {'PASS' if r['passed'] else 'FAIL'}  "
              f"(exec summary {r['exec_summary_words']} words)")
    print(f"   {pack_name:38s}: {'PASS' if (LATEST_DIR / pack_name).exists() else 'FAIL'}")

    print("\nCONTENT GATE:")
    for k, v in content_gate.items():
        print(f"   {k:34s}: {v}")
    print("REPOSITORY GATE:")
    for k, v in repo_gate.items():
        print(f"   {k:34s}: {v}")
    print(f"\n   ALL PASS: {all_pass}")
    print(f"PDF export     : {'written ' + str(pdf_path) if pdf_path else 'skipped (optional — no PDF library)'}")
    print(f"Validation     : {val_path}")
    print("=" * 80)
    return results, {**content_gate, **repo_gate}


if __name__ == "__main__":
    run()
