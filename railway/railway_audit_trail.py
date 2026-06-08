"""
railway_audit_trail.py
======================
STEP 17 -- Execution audit trail (additive, read-only).

Captures reproducibility / auditability metadata for a pipeline run and writes
STEP17_AUDIT_TRAIL.json at the repo root:

  * timestamp (UTC ISO-8601)
  * platform version + enterprise pipeline version
  * run ID (uuid4)
  * input row counts  (raw -> strategic/operational artefacts)
  * output row counts (policy, plan, every Power BI page, matrix, rationalization)
  * SHA-256 of each output (tamper-evidence / drift detection)

Reads existing outputs only; modifies nothing. Run:
    python -m railway.railway_audit_trail
"""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone

import pandas as pd

from railway import railway_config as cfg
from railway import __version__ as PLATFORM_VERSION
from railway import railway_domain_config as dom

OUT = cfg.OUTPUT_DIR
PBI = cfg.POWERBI_DIR
TRAIL_PATH = cfg.REPO_ROOT / "STEP17_AUDIT_TRAIL.json"

INPUT_FILES = [
    "railway_demand_history.csv", "railway_sku_master.csv",
    "railway_forecast.csv", "railway_operational_inventory.csv",
]
OUTPUT_FILES = [
    "railway_inventory_policy.csv", "railway_procurement_plan.csv",
    "railway_abc_criticality_matrix.csv", "railway_inventory_rationalization.csv",
    "railway_rationalization_summary.csv", "railway_data_quality.csv",
    "executive_kpi_summary.csv",
]
PAGE_FILES = [f"page{i}_{n}" for i, n in enumerate([
    "executive_dashboard", "procurement", "forecasting", "criticality",
    "operational_health", "rationalization", "data_quality",
    "abc_criticality_matrix", "budget_scenarios", "management_actions"])]


def _rows(path):
    return int(len(pd.read_csv(path))) if path.exists() else None


def _sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


def build_trail(run_id: str | None = None, timestamp: str | None = None) -> dict:
    """Assemble the audit-trail dict. run_id/timestamp may be injected for
    deterministic/reproducible runs; otherwise generated fresh."""
    ts = timestamp or datetime.now(timezone.utc).isoformat()
    rid = run_id or str(uuid.uuid4())

    inputs = {f: _rows(OUT / f) for f in INPUT_FILES}
    outputs = {f: {"rows": _rows(OUT / f), "sha256": _sha256(OUT / f)} for f in OUTPUT_FILES}
    pages = {f: {"rows": _rows(PBI / f"{f}.csv"), "sha256": _sha256(PBI / f"{f}.csv")}
             for f in PAGE_FILES}

    return {
        "run_id": rid,
        "timestamp_utc": ts,
        "platform_version": PLATFORM_VERSION,
        "pipeline_version": dom.ENTERPRISE_PIPELINE_VERSION,
        "config": {
            "procurement_budget": cfg.PROCUREMENT_BUDGET,
            "service_factor_slope": cfg.SERVICE_FACTOR_SLOPE,
            "service_factor_baseline_sl": cfg.SERVICE_FACTOR_BASELINE_SL,
            "safety_reserve_enabled": cfg.SAFETY_RESERVE_ENABLED,
            "safety_reserve_budget_pct": cfg.SAFETY_RESERVE_BUDGET_PCT,
            "safety_reserve_criticalities": list(cfg.SAFETY_RESERVE_CRITICALITIES),
            "criticality_weights": cfg.CRITICALITY_STOCKOUT_WEIGHT,
        },
        "input_row_counts": inputs,
        "output_artifacts": outputs,
        "powerbi_pages": pages,
    }


def run(run_id: str | None = None, timestamp: str | None = None) -> dict:
    trail = build_trail(run_id=run_id, timestamp=timestamp)
    TRAIL_PATH.write_text(json.dumps(trail, indent=2), encoding="utf-8")
    print("=" * 78)
    print("STEP 17 -- EXECUTION AUDIT TRAIL")
    print("=" * 78)
    print(f"   run_id           : {trail['run_id']}")
    print(f"   timestamp_utc    : {trail['timestamp_utc']}")
    print(f"   platform_version : {trail['platform_version']}  pipeline {trail['pipeline_version']}")
    print(f"   inputs           : {trail['input_row_counts']}")
    print(f"   output artefacts : {len(trail['output_artifacts'])}; powerbi pages: {len(trail['powerbi_pages'])}")
    print(f"   Wrote: {TRAIL_PATH}")
    return trail


if __name__ == "__main__":
    run()
