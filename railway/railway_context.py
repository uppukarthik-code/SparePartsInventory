"""
railway_context.py
==================
STEP 18 -- Execution-context path parameterization (NO analytical changes).

Every analytical module reads/writes the single global `cfg.OUTPUT_DIR` tree, and
several modules freeze `OUT = cfg.OUTPUT_DIR` / `PBI = cfg.POWERBI_DIR` at import. This
module provides a context manager that, for the duration of a `with` block, redirects
ALL of those bindings to a Business-Unit-scoped root (`outputs/<BU>/`) and restores them
on exit. The analytical code is never modified -- it simply runs against the redirected
paths.

Usage:
    from railway import railway_context as rc
    with rc.use_context("MAS"):
        opt.run(); powerbi.run(); enterprise.run()   # all write to outputs/MAS/

Backward compatibility: the default canonical root is unchanged, so importing this
module has no effect until `use_context` is entered.
"""

from __future__ import annotations

import importlib
from contextlib import contextmanager
from pathlib import Path

from railway import railway_config as cfg

# Canonical (original) output root captured once at import.
CANONICAL_OUTPUT_DIR = cfg.OUTPUT_DIR                  # .../railway/outputs
CANONICAL_ROOT = cfg.OUTPUT_DIR.parent                # .../railway

# cfg path attributes that must be re-pointed per BU (name -> derivation from base_out).
_CFG_PATH_KINDS = {
    "OUTPUT_DIR": "out",
    "POWERBI_DIR": "pbi",
    "ANYLOGISTIX_DIR": "axlx",
    "DEMAND_HISTORY_CSV": "demand",
    "SKU_MASTER_CSV": "master",
    "FORECAST_CSV": "forecast",
    "INVENTORY_POLICY_CSV": "policy",
}

# Module-level frozen captures: (module dotted-path, attribute, derivation-kind).
# These modules cached a cfg path at import, so patching cfg alone would not reach them.
_MODULE_CAPTURES = [
    ("railway.railway_powerbi_export", "OUT", "out"),
    ("railway.railway_powerbi_export", "PBI", "pbi"),
    ("railway.railway_enterprise", "OUT", "out"),
    ("railway.railway_enterprise", "PBI", "pbi"),
    ("railway.railway_enterprise", "AXLX", "axlx"),
    ("railway.railway_enterprise", "ENTERPRISE_DIR", "ent"),
    ("railway.railway_enterprise", "ENTERPRISE_PBI", "entpbi"),
    ("railway.railway_anylogistix_export", "ALX", "axlx"),
    ("railway.railway_anylogistix_export", "OUT", "out"),
    ("railway.railway_anylogistix_export", "PBI", "pbi"),
    ("railway.railway_management_reports", "PBI", "pbi"),
    ("railway.railway_management_reports", "AXLX", "axlx"),
    ("railway.railway_management_reports", "REPORTS_DIR", "reports"),
    ("railway.railway_dashboard_validation", "OUT", "out"),
    ("railway.railway_dashboard_validation", "PBI", "pbi"),
    ("railway.railway_srrs_validation", "OUT", "out"),
    ("railway.railway_srrs_validation", "PBI", "pbi"),
    ("railway.railway_audit_trail", "OUT", "out"),
    ("railway.railway_audit_trail", "PBI", "pbi"),
    ("railway.railway_audit_trail", "TRAIL_PATH", "trail"),
]


def _derive(base_out: Path, kind: str) -> Path:
    return {
        "out": base_out,
        "pbi": base_out / "powerbi",
        "axlx": base_out / "anylogistix",
        "ent": base_out / "enterprise",
        "entpbi": base_out / "enterprise" / "powerbi",
        "reports": base_out / "reports",
        "trail": base_out / "STEP17_AUDIT_TRAIL.json",
        "demand": base_out / "railway_demand_history.csv",
        "master": base_out / "railway_sku_master.csv",
        "forecast": base_out / "railway_forecast.csv",
        "policy": base_out / "railway_inventory_policy.csv",
    }[kind]


def bu_output_dir(business_unit: str, root: Path | None = None) -> Path:
    """Scoped output root for a Business Unit: <root>/<BU> (default outputs/<BU>)."""
    return (root or CANONICAL_OUTPUT_DIR) / business_unit


@contextmanager
def use_context(business_unit: str, root: Path | None = None):
    """Redirect all cfg + module path bindings to outputs/<BU>/ for the block,
    then restore every original binding (even on exception)."""
    base_out = bu_output_dir(business_unit, root)
    for d in (base_out, base_out / "powerbi", base_out / "anylogistix"):
        d.mkdir(parents=True, exist_ok=True)

    saved_cfg = {}
    saved_mod = []

    try:
        # 1. cfg path constants
        for name, kind in _CFG_PATH_KINDS.items():
            saved_cfg[name] = getattr(cfg, name)
            setattr(cfg, name, _derive(base_out, kind))
        # 2. frozen module-level captures
        for mod_path, attr, kind in _MODULE_CAPTURES:
            try:
                mod = importlib.import_module(mod_path)
            except Exception:
                continue
            if hasattr(mod, attr):
                saved_mod.append((mod, attr, getattr(mod, attr)))
                setattr(mod, attr, _derive(base_out, kind))
        yield base_out
    finally:
        for name, val in saved_cfg.items():
            setattr(cfg, name, val)
        for mod, attr, val in saved_mod:
            setattr(mod, attr, val)
