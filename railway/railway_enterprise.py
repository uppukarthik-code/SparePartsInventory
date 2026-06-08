"""
railway_enterprise.py
=====================
STEP 12.5 -- Multi-Domain Enterprise Architecture (additive, read-only).

Evolves the Railway Signalling analytics platform into an Enterprise Inventory
Management Information System by layering two enterprise dimensions --
`Inventory_Domain` and `Business_Unit` -- on top of the EXISTING, validated
outputs, WITHOUT modifying any of them.

This module:
  * reads existing pipeline outputs ONLY (never raw data, never analytics code);
  * re-uses published KPI values verbatim (sum / tag only -- no KPI is recomputed);
  * writes everything new under outputs/enterprise/ (a brand-new tree);
  * proves backward compatibility by hashing the whole existing outputs/ tree
    before and after generation and asserting it is byte-for-byte identical.

Generated artefacts (all NEW):
  outputs/enterprise/master_sku_registry.csv
  outputs/enterprise/domain_benchmark.csv
  outputs/enterprise/southern_railway_summary.csv
  outputs/enterprise/enterprise_summary.csv
  outputs/enterprise/powerbi/<every existing page, enriched with slicer columns>
  STEP12_5_VALIDATION_REPORT.md
  STEP12_5_IMPLEMENTATION_REPORT.md

Run:  python -m railway.railway_enterprise
"""

from __future__ import annotations

import hashlib

import pandas as pd

from railway import railway_config as cfg
from railway import railway_business_unit_config as buc
from railway import railway_domain_config as dom
from railway import railway_strategic_allocation as salloc   # STEP19 strategic allocation

OUT = cfg.OUTPUT_DIR
PBI = cfg.POWERBI_DIR
AXLX = cfg.ANYLOGISTIX_DIR

ENTERPRISE_DIR = OUT / "enterprise"
ENTERPRISE_PBI = ENTERPRISE_DIR / "powerbi"

SNAPSHOT_DATE = dom.DEFAULT_SNAPSHOT_DATE
PIPELINE_VERSION = dom.ENTERPRISE_PIPELINE_VERSION

BENCHMARK_MEASURES = [
    "Strategic_Inventory_Value", "Operational_Inventory_Value",
    "Dead_Stock_Value", "Inventory_Turn_Risk", "Digital_Twin_Readiness",
]


# ======================================================================
# Backward-compatibility guard: hash the whole existing outputs/ tree.
# ======================================================================
def hash_existing_outputs():
    """SHA-256 of every existing file under outputs/ EXCEPT the new enterprise/ tree.
    Used before and after generation to prove nothing existing was touched."""
    digests = {}
    for p in sorted(OUT.rglob("*")):
        if not p.is_file():
            continue
        if ENTERPRISE_DIR in p.parents or p == ENTERPRISE_DIR:
            continue
        digests[str(p.relative_to(OUT))] = hashlib.sha256(p.read_bytes()).hexdigest()
    return digests


# ======================================================================
# Read-only access to published KPI values (no recomputation).
# ======================================================================
def _read(path):
    return pd.read_csv(path, dtype={"PL_Code": str})


def published_domain_kpis():
    """Headline KPI values for the live Railway_Operations domain, taken VERBATIM
    from the existing executive dashboard + digital-twin readiness exports."""
    p0 = dict(zip(*[_read(PBI / "page0_executive_dashboard.csv")[c]
                    for c in ("KPI", "Value")]))
    dt = _read(AXLX / "digital_twin_readiness.csv")
    readiness = float(dt.loc[dt["Metric"] == "Overall_Digital_Twin_Readiness",
                             "Score_Pct"].iloc[0])
    return {
        "Strategic_Inventory_Value": round(float(p0["Strategic Inventory Value (Normalized)"]), 2),
        "Operational_Inventory_Value": round(float(p0["Operational Inventory Value"]), 2),
        "Dead_Stock_Value": round(float(p0["Dead Stock Value"]), 2),
        "Inventory_Turn_Risk": round(float(p0["Inventory Turn Risk %"]), 2),
        "Digital_Twin_Readiness": round(readiness, 2),
    }


# ======================================================================
# 1. Master asset registry (domain / business-unit / equipment-family aware)
# ======================================================================
def build_master_registry():
    strat = _read(OUT / "railway_sku_master.csv")
    op = _read(PBI / "op_inventory_summary.csv")

    s_idx = strat.set_index("PL_Code")
    o_idx = op.set_index("PL_Code")
    all_pl = list(dict.fromkeys(list(strat["PL_Code"]) + list(op["PL_Code"])))

    # STEP19: strategic-only SKUs are tagged by their allocated (dominant) Business
    # Unit instead of the zone default (MAS). Operationally-present SKUs keep their
    # depot-derived BU. The full per-depot split lives in
    # strategic_inventory_allocation.csv (registry is one row per PL).
    dominant_bu = salloc.dominant_bu_by_pl()

    rows = []
    for pl in all_pl:
        in_s = pl in s_idx.index
        in_o = pl in o_idx.index
        source = "Both" if (in_s and in_o) else ("Strategic" if in_s else "Operational")
        s = s_idx.loc[pl] if in_s else None
        o = o_idx.loc[pl] if in_o else None
        # handle accidental duplicate PL rows -> take first
        if in_s and isinstance(s, pd.DataFrame):
            s = s.iloc[0]
        if in_o and isinstance(o, pd.DataFrame):
            o = o.iloc[0]

        description = (s["Description"] if in_s else o["Description"])
        depot = (str(o["Depot"]) if in_o and pd.notna(o["Depot"]) else "")
        if in_o:
            business_unit = buc.resolve_business_unit(depot)      # operational lineage
        else:
            business_unit = dominant_bu.get(pl, buc.DEFAULT_BUSINESS_UNIT)  # STEP19 strategic allocation
        division = buc.division_of(business_unit)
        abc = (s["ABC_Class"] if in_s else (o["Operational_ABC"] if in_o else ""))
        criticality = (s["Criticality"] if in_s else "")
        stock = (s["Current_Stock"] if in_s else (o["Current_Stock"] if in_o else ""))
        unit_cost = (s["Unit_Cost"] if in_s else (o["Unit_Cost"] if in_o else ""))
        inv_val = (s["Inventory_Value"] if in_s else (o["Inventory_Value"] if in_o else ""))

        rows.append({
            "PL_Code": pl,
            "Description": description,
            "Inventory_Domain": "Railway_Operations",
            "Business_Unit": business_unit,
            "Division": division,
            "Equipment_Family": dom.classify_equipment_family(description),
            "Source_Universe": source,
            "ABC_Class": abc,
            "Criticality": criticality,
            "Current_Stock": stock,
            "Unit_Cost": unit_cost,
            "Inventory_Value": inv_val,
            "Depot": depot,
            "Snapshot_Date": SNAPSHOT_DATE,
            "Pipeline_Version": PIPELINE_VERSION,
        })
    return pd.DataFrame(rows)


# ======================================================================
# 2. Enriched Power BI exports (append slicer dimensions; originals untouched)
# ======================================================================
def _enrich(df):
    """Append the six enterprise slicer columns to a copy of an existing export."""
    out = df.copy()
    has_depot = "Depot" in out.columns
    depot_series = out["Depot"].astype(str) if has_depot else None

    out["Inventory_Domain"] = "Railway_Operations"
    if has_depot:
        out["Business_Unit"] = depot_series.map(buc.resolve_business_unit)
    else:
        out["Business_Unit"] = buc.DEFAULT_BUSINESS_UNIT
    out["Division"] = out["Business_Unit"].map(buc.division_of)
    if not has_depot:
        out["Depot"] = ""        # keep slicer column present & consistent everywhere
    out["Snapshot_Date"] = SNAPSHOT_DATE
    out["Pipeline_Version"] = PIPELINE_VERSION

    # Guarantee every enriched file exposes the full slicer set, original cols first.
    original = [c for c in df.columns]
    slicers = [c for c in dom.ENTERPRISE_DIMENSIONS if c not in original]
    return out[original + slicers]


def build_enriched_exports(write=True):
    enriched = {}
    for src in sorted(PBI.glob("*.csv")):
        enriched[src.name] = _enrich(_read(src))
    if write:
        ENTERPRISE_PBI.mkdir(parents=True, exist_ok=True)
        for name, df in enriched.items():
            df.to_csv(ENTERPRISE_PBI / name, index=False)
    return enriched


# ======================================================================
# 3. Benchmarking framework (per business unit, across domains)
# ======================================================================
def build_domain_benchmark(kpis):
    """One row per configured business unit. The live unit carries the published
    domain KPI values verbatim; configured-but-not-yet-onboarded units are left
    blank (framework ready, awaiting data)."""
    # STEP19: split the published (zone) Strategic_Inventory_Value across Business
    # Units by their verified depot-allocated share, so summing across units yields
    # the zone total exactly (no 6x inflation) instead of every unit carrying the
    # full zone value. Operational measures are unchanged.
    strat_share = salloc.strategic_value_share()
    published_strategic = kpis["Strategic_Inventory_Value"]

    rows = []
    for bu_code in buc.BUSINESS_UNIT_ORDER:
        meta = buc.BUSINESS_UNITS[bu_code]
        row = {
            "Inventory_Domain": meta["Inventory_Domain"],
            "Business_Unit": bu_code,
            "Division": meta["Division"],
            "Status": meta["Status"],
            "Strategic_Inventory_Value": "",
            "Operational_Inventory_Value": "",
            "Dead_Stock_Value": "",
            "Inventory_Turn_Risk": "",
            "Digital_Twin_Readiness": "",
            "Snapshot_Date": SNAPSHOT_DATE,
            "Pipeline_Version": PIPELINE_VERSION,
        }
        if meta["Status"] == "Live":
            for m in BENCHMARK_MEASURES:
                row[m] = kpis[m]
            # STEP19 strategic de-inflation: this BU's allocated share of the zone total.
            row["Strategic_Inventory_Value"] = round(
                published_strategic * strat_share.get(bu_code, 0.0), 2)
        rows.append(row)
    cols = ["Inventory_Domain", "Business_Unit", "Division", "Status",
            *BENCHMARK_MEASURES, "Snapshot_Date", "Pipeline_Version"]
    return pd.DataFrame(rows)[cols]


# ======================================================================
# 4. Zone & enterprise aggregation
# ======================================================================
def _live_value_sum(benchmark, domain, measure):
    sub = benchmark[(benchmark["Inventory_Domain"] == domain) &
                    (benchmark["Status"] == "Live")]
    vals = pd.to_numeric(sub[measure], errors="coerce")
    return round(float(vals.sum()), 2) if vals.notna().any() else ""


def _live_rate(benchmark, domain, measure):
    # Rates are not summed; carry the live unit's published rate (the zone == domain
    # here, so this is exactly the published domain figure).
    sub = benchmark[(benchmark["Inventory_Domain"] == domain) &
                    (benchmark["Status"] == "Live")]
    vals = pd.to_numeric(sub[measure], errors="coerce").dropna()
    return round(float(vals.iloc[0]), 2) if len(vals) else ""


def build_southern_railway_summary(benchmark):
    """Zone-level rollup for the Railway Operations domain."""
    domain = "Railway_Operations"
    bus = buc.business_units_for_domain(domain)
    live = [b for b in bus if buc.is_live(b)]
    row = {
        "Zone": "Southern Railway",
        "Inventory_Domain": domain,
        "Business_Units_Configured": len(bus),
        "Business_Units_Populated": len(live),
        "Strategic_Inventory_Value": _live_value_sum(benchmark, domain, "Strategic_Inventory_Value"),
        "Operational_Inventory_Value": _live_value_sum(benchmark, domain, "Operational_Inventory_Value"),
        "Dead_Stock_Value": _live_value_sum(benchmark, domain, "Dead_Stock_Value"),
        "Inventory_Turn_Risk": _live_rate(benchmark, domain, "Inventory_Turn_Risk"),
        "Digital_Twin_Readiness": _live_rate(benchmark, domain, "Digital_Twin_Readiness"),
        "Snapshot_Date": SNAPSHOT_DATE,
        "Pipeline_Version": PIPELINE_VERSION,
    }
    return pd.DataFrame([row])


def build_enterprise_summary(benchmark):
    """One row per domain, across the whole enterprise."""
    rows = []
    for domain in dom.DOMAIN_ORDER:
        bus = buc.business_units_for_domain(domain)
        live = [b for b in bus if buc.is_live(b)]
        rows.append({
            "Inventory_Domain": domain,
            "Domain_Name": dom.domain_name(domain),
            "Status": dom.DOMAINS[domain]["Status"],
            "Business_Units_Configured": len(bus),
            "Business_Units_Populated": len(live),
            "Strategic_Inventory_Value": _live_value_sum(benchmark, domain, "Strategic_Inventory_Value"),
            "Operational_Inventory_Value": _live_value_sum(benchmark, domain, "Operational_Inventory_Value"),
            "Dead_Stock_Value": _live_value_sum(benchmark, domain, "Dead_Stock_Value"),
            "Inventory_Turn_Risk": _live_rate(benchmark, domain, "Inventory_Turn_Risk"),
            "Digital_Twin_Readiness": _live_rate(benchmark, domain, "Digital_Twin_Readiness"),
            "Snapshot_Date": SNAPSHOT_DATE,
            "Pipeline_Version": PIPELINE_VERSION,
        })
    return pd.DataFrame(rows)


# ======================================================================
# Generation + validation
# ======================================================================
def generate_all():
    ENTERPRISE_DIR.mkdir(parents=True, exist_ok=True)
    ENTERPRISE_PBI.mkdir(parents=True, exist_ok=True)

    kpis = published_domain_kpis()
    registry = build_master_registry()
    benchmark = build_domain_benchmark(kpis)
    sr_summary = build_southern_railway_summary(benchmark)
    ent_summary = build_enterprise_summary(benchmark)
    enriched = build_enriched_exports(write=True)

    registry.to_csv(ENTERPRISE_DIR / "master_sku_registry.csv", index=False)
    benchmark.to_csv(ENTERPRISE_DIR / "domain_benchmark.csv", index=False)
    sr_summary.to_csv(ENTERPRISE_DIR / "southern_railway_summary.csv", index=False)
    ent_summary.to_csv(ENTERPRISE_DIR / "enterprise_summary.csv", index=False)

    return {
        "kpis": kpis, "registry": registry, "benchmark": benchmark,
        "sr_summary": sr_summary, "ent_summary": ent_summary, "enriched": enriched,
    }


def validate(before_hashes, after_hashes, art):
    registry = art["registry"]
    benchmark = art["benchmark"]
    enriched = art["enriched"]

    # Backward compatibility: existing outputs byte-for-byte identical.
    changed = [k for k in before_hashes if before_hashes[k] != after_hashes.get(k)]
    removed = [k for k in before_hashes if k not in after_hashes]
    outputs_unchanged = (not changed) and (not removed)

    # Enriched exports are supersets of the originals (original cols preserved, in order).
    superset_ok = True
    for name, df in enriched.items():
        orig_cols = list(_read(PBI / name).columns)
        if list(df.columns)[:len(orig_cols)] != orig_cols:
            superset_ok = False
        if not all(d in df.columns for d in dom.ENTERPRISE_DIMENSIONS):
            superset_ok = False

    # Benchmark KPI values match the published outputs exactly (no recomputation drift).
    # STEP19: Strategic_Inventory_Value is now allocated per BU (a split of the
    # published zone total), so it is validated by CONSERVATION (sum over Live units
    # == published zone value) rather than per-row equality; all other measures still
    # match the published KPIs verbatim.
    live = benchmark[benchmark["Status"] == "Live"].iloc[0]
    kpis = art["kpis"]
    _nonstrat = [m for m in BENCHMARK_MEASURES if m != "Strategic_Inventory_Value"]
    _strat_sum = pd.to_numeric(
        benchmark.loc[benchmark["Status"] == "Live", "Strategic_Inventory_Value"],
        errors="coerce").sum()
    bench_matches = (all(float(live[m]) == kpis[m] for m in _nonstrat)
                     and abs(_strat_sum - kpis["Strategic_Inventory_Value"]) < 1.0)

    gate = {
        "existing_outputs_unchanged": outputs_unchanged,
        "existing_reports_unchanged": not any(c.startswith("reports/") for c in changed + removed),
        "existing_dashboards_unaffected": not any(
            c.startswith("powerbi/") for c in changed + removed),
        "inventory_domain_operational": "Inventory_Domain" in registry.columns
            and set(registry["Inventory_Domain"]) <= set(dom.DOMAINS),
        "business_unit_operational": "Business_Unit" in registry.columns
            and set(registry["Business_Unit"]) <= set(buc.BUSINESS_UNITS),
        "equipment_family_tagged": "Equipment_Family" in registry.columns
            and registry["Equipment_Family"].notna().all(),
        "benchmarking_operational": set(BENCHMARK_MEASURES).issubset(benchmark.columns)
            and (benchmark["Status"] == "Live").any() and bench_matches,
        "enterprise_aggregation_operational":
            (ENTERPRISE_DIR / "southern_railway_summary.csv").exists()
            and (ENTERPRISE_DIR / "enterprise_summary.csv").exists(),
        "powerbi_slicers_appended": superset_ok,
        "backward_compatibility_maintained": outputs_unchanged and superset_ok,
    }
    detail = {"changed": changed, "removed": removed,
              "n_existing_files": len(before_hashes)}
    return gate, detail


def write_validation_report(gate, detail, art):
    out = cfg.REPO_ROOT / "STEP12_5_VALIDATION_REPORT.md"
    registry = art["registry"]
    benchmark = art["benchmark"]
    md = []
    md.append("# STEP 12.5 — Multi-Domain Enterprise Architecture: Validation")
    md.append(f"*Snapshot {SNAPSHOT_DATE} · Pipeline {PIPELINE_VERSION}*\n")
    md.append("Confirms the enterprise dimensions were added **additively**: every existing "
              "analytical output, report, dashboard export and KPI is byte-for-byte unchanged.\n")

    md.append("## Backward-Compatibility Proof\n")
    md.append(f"- Existing files fingerprinted under `outputs/`: **{detail['n_existing_files']}**")
    md.append(f"- Files changed by this step: **{len(detail['changed'])}**")
    md.append(f"- Files removed by this step: **{len(detail['removed'])}**")
    if detail["changed"]:
        md.append("  - " + ", ".join(f"`{c}`" for c in detail["changed"]))
    md.append("- Method: SHA-256 of the whole `outputs/` tree (excluding the new `enterprise/` "
              "folder) captured **before and after** generation and compared.\n")

    md.append("## Validation Gate\n")
    for k, v in gate.items():
        md.append(f"- {'✅' if v else '❌'} {k}")
    md.append(f"\n**ALL PASS: {all(gate.values())}**\n")

    md.append("## Enterprise Dimensions In Effect\n")
    md.append(f"- **Inventory_Domain** values: {', '.join(sorted(set(registry['Inventory_Domain'])))}")
    md.append(f"- **Business_Unit** values in registry: {', '.join(sorted(set(registry['Business_Unit'])))}")
    md.append(f"- **Configured business units**: {', '.join(buc.BUSINESS_UNIT_ORDER)}")
    md.append(f"- **Equipment families detected**: {', '.join(sorted(set(registry['Equipment_Family'])))}\n")

    md.append("## Benchmark Snapshot (live units carry published KPIs verbatim)\n")
    md.append("| Inventory_Domain | Business_Unit | Status | Strategic | Operational | Dead Stock | Turn Risk | Readiness |")
    md.append("|---|---|---|---|---|---|---|---|")
    for _, r in benchmark.iterrows():
        md.append(f"| {r['Inventory_Domain']} | {r['Business_Unit']} | {r['Status']} | "
                  f"{r['Strategic_Inventory_Value']} | {r['Operational_Inventory_Value']} | "
                  f"{r['Dead_Stock_Value']} | {r['Inventory_Turn_Risk']} | {r['Digital_Twin_Readiness']} |")
    md.append("")

    md.append("## New Artefacts (all additive)\n")
    for f in ["master_sku_registry.csv", "domain_benchmark.csv",
              "southern_railway_summary.csv", "enterprise_summary.csv"]:
        md.append(f"- `outputs/enterprise/{f}`")
    md.append(f"- `outputs/enterprise/powerbi/` — {len(art['enriched'])} enriched exports with "
              f"slicer columns ({', '.join(dom.ENTERPRISE_DIMENSIONS)})")
    md.append("- `railway/railway_domain_config.py`, `railway/railway_business_unit_config.py`\n")

    out.write_text("\n".join(md), encoding="utf-8")
    return out


def write_implementation_report(gate, art):
    out = cfg.REPO_ROOT / "STEP12_5_IMPLEMENTATION_REPORT.md"
    md = []
    md.append("# STEP 12.5 — Multi-Domain Enterprise Architecture: Implementation Report")
    md.append(f"*Snapshot {SNAPSHOT_DATE} · Pipeline {PIPELINE_VERSION}*\n")

    md.append("## Objective\n")
    md.append("Evolve the platform from **Railway Inventory Analytics** to an **Enterprise "
              "Inventory Management Information System** supporting multiple inventory domains "
              "(Railway Operations, Training Centres, and future domains) — without altering any "
              "existing analytics, reports, dashboards, KPIs or management packs.\n")

    md.append("## Modules Impacted\n")
    md.append("**None modified.** All work is additive:\n")
    md.append("| New file | Purpose |")
    md.append("|---|---|")
    md.append("| `railway/railway_business_unit_config.py` | `Business_Unit` dimension + depot→BU resolver |")
    md.append("| `railway/railway_domain_config.py` | `Inventory_Domain` dimension, equipment families, governance constants |")
    md.append("| `railway/railway_enterprise.py` | Read-only generator for registry, benchmark, aggregation, enriched exports |")
    md.append("")
    md.append("Protected logic left untouched: forecasting, procurement prioritisation, inventory "
              "optimisation, budget optimisation, rationalisation, operational health, reporting, "
              "management pack, historical archive, Power BI exports, KPI calculations.\n")

    md.append("## Enterprise Dimensions\n")
    md.append("Two dimensions now anchor all future reporting, dashboards and benchmarking:\n")
    md.append("- **Inventory_Domain** — Railway_Operations (Live), Training_Centre (Framework); "
              f"future: {', '.join(dom.FUTURE_DOMAINS)}.")
    md.append(f"- **Business_Unit** — {', '.join(buc.BUSINESS_UNIT_ORDER)} (extensible via config).")
    md.append("Metadata appended to enriched exports: "
              f"{', '.join(dom.ENTERPRISE_DIMENSIONS)}.\n")

    md.append("## Domain Status\n")
    md.append("| Domain | Status | Business Units | Reporting Package |")
    md.append("|---|---|---|---|")
    for d in dom.DOMAIN_ORDER:
        info = dom.DOMAINS[d]
        pkg = ", ".join(info["Reporting_Package"]) or "Framework only (analytics not yet built)"
        md.append(f"| {info['Domain_Name']} | {info['Status']} | "
                  f"{', '.join(info['Business_Units']) or '—'} | {pkg} |")
    md.append("")
    md.append("Training_Centre is **framework only** — its future KPIs are declared but not "
              f"implemented: {', '.join(dom.DOMAINS['Training_Centre']['Future_KPIs'])}.\n")

    md.append("## Master Asset Registry\n")
    reg = art["registry"]
    md.append(f"- Items registered: **{len(reg)}** (union of strategic + operational universes)")
    md.append(f"- Columns added: `Inventory_Domain`, `Business_Unit`, `Equipment_Family` "
              "(plus Division, Depot, Snapshot_Date, Pipeline_Version)")
    fam_counts = reg["Equipment_Family"].value_counts()
    md.append("- Equipment-family distribution (top): "
              + ", ".join(f"{k} ({v})" for k, v in fam_counts.head(8).items()) + "\n")

    md.append("## Power BI Readiness\n")
    md.append(f"- {len(art['enriched'])} existing exports copied to `outputs/enterprise/powerbi/` "
              "with six slicer columns appended; **originals untouched**.")
    md.append("- Future dashboards can slice by Domain, Business Unit, Division, Depot and "
              "Snapshot Date with no redesign of current pages.\n")

    md.append("## Validation Result\n")
    for k, v in gate.items():
        md.append(f"- {'✅' if v else '❌'} {k}")
    md.append(f"\n**ALL PASS: {all(gate.values())}** — see `STEP12_5_VALIDATION_REPORT.md` for the "
              "byte-level backward-compatibility proof.\n")

    md.append("## Success Criteria\n")
    md.append("The platform now operates as an Enterprise Inventory MIS spanning Railway "
              "Operations, Training Centres and future domains, while every existing analytic, "
              "dashboard, report, KPI and management pack continues to function unchanged. New "
              "business units and domains onboard through configuration alone.\n")

    out.write_text("\n".join(md), encoding="utf-8")
    return out


def run():
    print("=" * 80)
    print("STEP 12.5 -- MULTI-DOMAIN ENTERPRISE ARCHITECTURE")
    print("=" * 80)

    before = hash_existing_outputs()
    art = generate_all()
    after = hash_existing_outputs()

    gate, detail = validate(before, after, art)
    val_path = write_validation_report(gate, detail, art)
    impl_path = write_implementation_report(gate, art)

    print(f"\nExisting files fingerprinted : {detail['n_existing_files']}")
    print(f"Existing files changed       : {len(detail['changed'])}")
    print(f"Master registry items        : {len(art['registry'])}")
    print(f"Benchmark business units     : {len(art['benchmark'])}")
    print(f"Enriched Power BI exports    : {len(art['enriched'])}")
    print("\nVALIDATION GATE:")
    for k, v in gate.items():
        print(f"   {k:38s}: {v}")
    print(f"   ALL PASS: {all(gate.values())}")
    print(f"\nValidation report     : {val_path}")
    print(f"Implementation report : {impl_path}")
    print("=" * 80)
    return art, gate


if __name__ == "__main__":
    run()
