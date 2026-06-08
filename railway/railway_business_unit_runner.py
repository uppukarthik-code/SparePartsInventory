"""
railway_business_unit_runner.py
===============================
STEP 18 -- Multi-Business-Unit execution runner (NO analytical changes).

Drives the EXISTING analytics pipeline once per Business Unit, writing each BU's
outputs to `outputs/<BU>/`, then produces an enterprise roll-up. Scoping and path
isolation are achieved entirely from this orchestration layer:

  * paths        -> railway_context.use_context(BU)   (redirects cfg + frozen captures)
  * data scope   -> the raw loaders are monkey-patched to serve cached frames; in
                    multi-BU mode the OPERATIONAL frame is filtered by depot -> BU.
                    railways.xlsx / stock_summary.xlsx are parsed ONCE and reused.

Semantics (honest to the data, per STEP18 assessment):
  * Operational universe (depot-granular) is PARTITIONED by Business Unit.
  * Strategic universe (zone-consolidated) is SHARED across Business Units.
  * Single-BU run  = full dataset (no partition) -> byte-for-byte == current outputs.
  * Multi-BU run   = operational partitioned per BU; strategic shared.

Run:
    python -m railway.railway_business_unit_runner                 # MAS only (backward-compat)
    python -m railway.railway_business_unit_runner MAS TPJ         # multi-BU split
"""

from __future__ import annotations

import contextlib
import io
import sys
from contextlib import contextmanager

import pandas as pd

from railway import railway_config as cfg
from railway import railway_context as rc
from railway import railway_business_unit_config as buc
from railway import railway_domain_config as dom
from railway import railway_data_preparation as dp
from railway import railway_data_quality as dq

# Pipeline module sequence (each exposes run()); executed in dependency order.
from railway import (
    railway_classification, railway_forecasting, railway_inventory_optimization,
    railway_inventory_rationalization, railway_operational_analysis,
    railway_executive_summary, railway_powerbi_export, railway_enterprise,
    railway_anylogistix_export, railway_explainability, railway_audit_trail,
)

# Dependency-ordered pipeline. anylogistix_export precedes enterprise because
# enterprise.published_domain_kpis() reads anylogistix/digital_twin_readiness.csv.
PIPELINE = [
    ("data_preparation", dp),
    ("classification", railway_classification),
    ("forecasting", railway_forecasting),
    ("inventory_optimization", railway_inventory_optimization),
    ("data_quality", dq),
    ("operational_analysis", railway_operational_analysis),
    ("inventory_rationalization", railway_inventory_rationalization),
    ("executive_summary", railway_executive_summary),
    ("powerbi_export", railway_powerbi_export),
    ("anylogistix_export", railway_anylogistix_export),
    ("enterprise", railway_enterprise),
    ("explainability", railway_explainability),
]
# Note: railway_management_reports and railway_lineage (stateful report archives /
# lineage) are auxiliary report layers, outside the deterministic analytics + KPI +
# Power BI byte-identical scope of this runner; they have their own entry points.


# ----------------------------------------------------------------------
# Discovery
# ----------------------------------------------------------------------
def discover_domains():
    return [(d, dom.DOMAINS[d].get("Status", "")) for d in dom.DOMAIN_ORDER]


def discover_business_units(op_full: pd.DataFrame):
    """Return [(bu, operational_row_count, has_strategic)] for every BU that has data."""
    bu_of = op_full["Depot"].map(buc.resolve_business_unit)
    counts = bu_of.value_counts().to_dict()
    rows = []
    for bu in buc.BUSINESS_UNIT_ORDER:
        n = int(counts.get(bu, 0))
        has_strategic = (bu == buc.DEFAULT_BUSINESS_UNIT)
        if n > 0 or has_strategic:
            rows.append((bu, n, has_strategic))
    return rows


# ----------------------------------------------------------------------
# Reference cache + loader scoping  (load workbooks ONCE)
# ----------------------------------------------------------------------
def load_reference_once() -> dict:
    """Parse railways.xlsx + stock_summary.xlsx exactly once; return cached frames."""
    return {
        "strategic": dp.load_strategic_stock(),
        "safety": dp.load_safety_vital(),
        "division": dp.load_division_consumption(),
        "operational": dp.load_operational_stock(),
        "units": dq.load_units(),
    }


@contextmanager
def scoped_loaders(business_unit: str, cache: dict, split: bool):
    """Monkey-patch the raw loaders to serve cached frames (copies). In split mode the
    operational frame is filtered to the BU's depots. The analytical modules are
    unchanged -- they simply receive the scoped data. Originals restored on exit."""
    originals = {
        (dp, "load_strategic_stock"): dp.load_strategic_stock,
        (dp, "load_safety_vital"): dp.load_safety_vital,
        (dp, "load_division_consumption"): dp.load_division_consumption,
        (dp, "load_operational_stock"): dp.load_operational_stock,
        (dq, "load_units"): dq.load_units,
    }

    def _op():
        df = cache["operational"].copy()
        if split:
            keep = df["Depot"].map(buc.resolve_business_unit) == business_unit
            df = df[keep].reset_index(drop=True)
        return df

    try:
        dp.load_strategic_stock = lambda: cache["strategic"].copy()
        dp.load_safety_vital = lambda: cache["safety"].copy()
        dp.load_division_consumption = lambda: cache["division"].copy()
        dp.load_operational_stock = _op
        dq.load_units = lambda: cache["units"].copy()
        yield
    finally:
        for (mod, attr), fn in originals.items():
            setattr(mod, attr, fn)


# ----------------------------------------------------------------------
# Per-BU pipeline execution
# ----------------------------------------------------------------------
def run_pipeline(quiet: bool = True):
    """Execute the existing analytics pipeline (unchanged) in the active context."""
    sink = io.StringIO() if quiet else sys.stdout
    for name, mod in PIPELINE:
        with contextlib.redirect_stdout(sink):
            mod.run()


def _write_skeleton(business_unit: str, base, op_count: int, reason: str):
    """Data-less Business Unit -> write a non-crashing skeleton status marker.
    The analytics modules are not designed for empty universes (and must not be
    modified), so a configured-but-unonboarded BU yields a status file, not a run."""
    import json
    base.mkdir(parents=True, exist_ok=True)
    meta = buc.BUSINESS_UNITS.get(business_unit, {})
    (base / "BU_STATUS.json").write_text(json.dumps({
        "business_unit": business_unit,
        "name": meta.get("Name", business_unit),
        "status": meta.get("Status", "Configured"),
        "operational_rows": int(op_count),
        "processed": False,
        "reason": reason,
    }, indent=2), encoding="utf-8")


def run_business_unit(business_unit: str, cache: dict, split: bool,
                      root=None, quiet: bool = True, audit: bool = True) -> str:
    base = rc.bu_output_dir(business_unit, root)
    with rc.use_context(business_unit, root):
        with scoped_loaders(business_unit, cache, split):
            run_pipeline(quiet=quiet)
        if audit:
            with contextlib.redirect_stdout(io.StringIO()):
                railway_audit_trail.run()      # per-BU STEP17_AUDIT_TRAIL.json
    return str(base)


# ----------------------------------------------------------------------
# Enterprise roll-up across Business Units
# ----------------------------------------------------------------------
def enterprise_rollup(business_units, root=None, quiet: bool = True) -> dict:
    """Concatenate per-BU enterprise registries / summaries into a cross-BU view at
    outputs/_enterprise_rollup/. Additive; reads each BU's enterprise outputs."""
    root = root or rc.CANONICAL_OUTPUT_DIR
    out = root / "_enterprise_rollup"
    out.mkdir(parents=True, exist_ok=True)

    registries, summaries = [], []
    for bu in business_units:
        reg = root / bu / "enterprise" / "master_sku_registry.csv"
        summ = root / bu / "enterprise" / "southern_railway_summary.csv"
        if reg.exists():
            d = pd.read_csv(reg, dtype={"PL_Code": str}); d["BU_Scope"] = bu
            registries.append(d)
        if summ.exists():
            d = pd.read_csv(summ); d["BU_Scope"] = bu
            summaries.append(d)

    info = {"business_units": list(business_units), "files": []}
    if registries:
        reg_all = pd.concat(registries, ignore_index=True)
        reg_all.to_csv(out / "master_sku_registry_all.csv", index=False)
        info["files"].append("master_sku_registry_all.csv")
        info["total_rows"] = int(len(reg_all))
    if summaries:
        summ_all = pd.concat(summaries, ignore_index=True)
        summ_all.to_csv(out / "southern_railway_summary_all.csv", index=False)
        info["files"].append("southern_railway_summary_all.csv")
    return info


# ----------------------------------------------------------------------
# Orchestration entry point
# ----------------------------------------------------------------------
def run(business_units=None, root=None, quiet: bool = True):
    business_units = business_units or [buc.DEFAULT_BUSINESS_UNIT]
    # Consolidated (backward-compatible) iff the single default BU is requested:
    # full dataset, no scoping -> byte-for-byte identical to the canonical outputs.
    consolidated = (len(business_units) == 1 and business_units[0] == buc.DEFAULT_BUSINESS_UNIT)

    print("=" * 80)
    print("STEP 18 -- MULTI-BUSINESS-UNIT RUNNER")
    print("=" * 80)
    print("Domains discovered :", {d: s for d, s in discover_domains()})

    print("\nLoading reference workbooks once (railways.xlsx + stock_summary.xlsx) ...")
    cache = load_reference_once()
    bu_of = cache["operational"]["Depot"].map(buc.resolve_business_unit)
    op_counts = bu_of.value_counts().to_dict()
    print(f"Strategic items     : {len(cache['strategic'])} (zone-level, shared)")
    print(f"Operational items   : {len(cache['operational'])} (depot-level, partitionable)")
    print("Business Units found:")
    for bu, n, hs in discover_business_units(cache["operational"]):
        print(f"   {bu:9s} operational={n:4d}  strategic={'yes' if hs else 'no'}  "
              f"status={buc.BUSINESS_UNITS.get(bu, {}).get('Status', '?')}")

    print(f"\nMode: {'SINGLE-BU (consolidated / backward-compatible)' if consolidated else 'MULTI-BU SPLIT'}")
    print(f"Processing: {business_units}\n")

    results, processed = {}, []
    for bu in business_units:
        base = rc.bu_output_dir(bu, root)
        op_n = int(op_counts.get(bu, 0))
        if consolidated:
            # full dataset (no scope) -> byte-identical
            results[bu] = run_business_unit(bu, cache, split=False, root=root, quiet=quiet)
            processed.append(bu)
            print(f"   [{bu}] full pipeline -> {results[bu]}")
        elif op_n > 0:
            # operational data present -> full scoped pipeline
            results[bu] = run_business_unit(bu, cache, split=True, root=root, quiet=quiet)
            processed.append(bu)
            print(f"   [{bu}] scoped pipeline (operational={op_n}) -> {results[bu]}")
        else:
            # configured-but-unonboarded BU -> skeleton, no crash
            _write_skeleton(bu, base, op_n, "no operational data in source (Status=Configured)")
            results[bu] = str(base) + "  [skeleton: no data]"
            print(f"   [{bu}] SKELETON (operational=0, awaiting onboarding) -> {base}")

    rollup = None
    if not consolidated and processed:
        rollup = enterprise_rollup(processed, root=root, quiet=quiet)
        print(f"\nEnterprise roll-up  : {rollup.get('files')} "
              f"({rollup.get('total_rows', 0)} registry rows) -> _enterprise_rollup/")

    print("\nDONE.")
    print("=" * 80)
    return {"business_units": business_units, "consolidated": consolidated,
            "processed": processed, "outputs": results, "rollup": rollup}


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    run(business_units=args or None, quiet="--verbose" not in sys.argv)
