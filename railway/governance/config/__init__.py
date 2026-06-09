"""railway.governance.config — centralized planning configuration (Phase B).

Resolves the ACTIVE division into module-level constants that are byte-identical
to the prior hardcoded MAS literals, so the STEP20-28 modules import their
constants from one place. STEP37 adds ``use_division(div)`` — a runtime switch
that re-points BOTH these module-level constants AND the frozen captures the
STEP20-28 modules took at import (``SUMMARY``, ``DMTR_DIR``, ``H``/``HISTORY_DIR``,
...), then restores everything on exit. This mirrors ``railway_context`` (which
covers the STEP1-19 output paths) for the planning layer.
"""
import importlib
from contextlib import contextmanager

from railway.governance.config import divisions
from railway.governance.config.divisions import (
    get, raw_dir, summary_workbook, live_divisions, DIVISIONS, ACTIVE_DIVISION,
)


def _resolve(division: str) -> dict:
    """Resolve a division into the full set of planning constants."""
    a = get(division)
    out = {
        "DIVISION": a["division"],
        "DEPOT": a["depot"],
        "DAYS_PER_MONTH": a["DAYS_PER_MONTH"],
        "SERVICE_LEVEL": a["SERVICE_LEVEL"],
        "TYPE_WEIGHT": a["TYPE_WEIGHT"],
        "ROP_CRITICAL_FACTOR": a["ROP_CRITICAL_FACTOR"],
        "ROP_EXCESS_FACTOR": a["ROP_EXCESS_FACTOR"],
        "HORIZON": a["HORIZON"],
        "DMTR_DIR": raw_dir(division),
        "SUMMARY_WORKBOOK": summary_workbook(division),
    }
    out["DIVISION_OUTPUT_DIR"] = divisions.cfg.OUTPUT_DIR / a["division"]
    out["HISTORY_DIR"] = out["DIVISION_OUTPUT_DIR"] / "history"
    return out


# Names that live as module-level constants in THIS module.
_OWN = ["DIVISION", "DEPOT", "DAYS_PER_MONTH", "SERVICE_LEVEL", "TYPE_WEIGHT",
        "ROP_CRITICAL_FACTOR", "ROP_EXCESS_FACTOR", "HORIZON", "DMTR_DIR",
        "SUMMARY_WORKBOOK", "DIVISION_OUTPUT_DIR", "HISTORY_DIR"]

# --- initialise the active-division constants (exact prior MAS values) --------
globals().update(_resolve(ACTIVE_DIVISION))

# Frozen captures the STEP20-28 modules / shared_io took at import:
#   (module dotted-path, module attribute, gcfg constant name)
_DIVISION_CAPTURES = [
    ("railway.ingestion.shared_io", "DMTR_DIR", "DMTR_DIR"),
    ("railway.ingestion.shared_io", "SUMMARY_WORKBOOK", "SUMMARY_WORKBOOK"),
    ("railway.railway_demand_reconstruction", "BUSINESS_UNIT", "DIVISION"),
    ("railway.railway_demand_reconstruction", "DMTR_DIR", "DMTR_DIR"),
    ("railway.railway_demand_reconstruction", "HISTORY_DIR", "HISTORY_DIR"),
    ("railway.railway_demand_classification", "BUSINESS_UNIT", "DIVISION"),
    ("railway.railway_demand_classification", "HISTORY_DIR", "HISTORY_DIR"),
    ("railway.railway_forecast_generation", "BUSINESS_UNIT", "DIVISION"),
    ("railway.railway_forecast_generation", "HISTORY_DIR", "HISTORY_DIR"),
    ("railway.railway_forecast_generation", "HORIZON", "HORIZON"),
    ("railway.railway_lead_time_derivation", "H", "HISTORY_DIR"),
    ("railway.railway_lead_time_derivation", "MAS", "DIVISION_OUTPUT_DIR"),
    ("railway.railway_pl_master", "H", "HISTORY_DIR"),
    ("railway.railway_pl_master", "MAS", "DIVISION_OUTPUT_DIR"),
    ("railway.railway_safety_stock", "H", "HISTORY_DIR"),
    ("railway.railway_safety_stock", "SUMMARY", "SUMMARY_WORKBOOK"),
    ("railway.railway_safety_stock", "DAYS_PER_MONTH", "DAYS_PER_MONTH"),
    ("railway.railway_safety_stock", "SERVICE_LEVEL", "SERVICE_LEVEL"),
    ("railway.railway_rop", "H", "HISTORY_DIR"),
    ("railway.railway_rop", "SUMMARY", "SUMMARY_WORKBOOK"),
    ("railway.railway_rop", "DAYS_PER_MONTH", "DAYS_PER_MONTH"),
    ("railway.railway_srrs_mas", "H", "HISTORY_DIR"),
    ("railway.railway_srrs_mas", "SUMMARY", "SUMMARY_WORKBOOK"),
    ("railway.railway_srrs_mas", "TYPE_WEIGHT", "TYPE_WEIGHT"),
    ("railway.railway_srrs_mas", "SERVICE_LEVEL", "SERVICE_LEVEL"),
]


@contextmanager
def use_division(division: str):
    """Redirect the planning layer to ``division`` for the duration of the block,
    then restore every binding (even on exception). Affects this module's
    constants AND the STEP20-28 modules' frozen captures."""
    resolved = _resolve(division)
    saved_own = {n: globals()[n] for n in _OWN}
    saved_mod = []
    try:
        globals().update(resolved)
        for mod_path, attr, gname in _DIVISION_CAPTURES:
            try:
                mod = importlib.import_module(mod_path)
            except Exception:
                continue
            if hasattr(mod, attr):
                saved_mod.append((mod, attr, getattr(mod, attr)))
                setattr(mod, attr, resolved[gname])
        yield division
    finally:
        for n, v in saved_own.items():
            globals()[n] = v
        for mod, attr, val in saved_mod:
            setattr(mod, attr, val)


__all__ = [
    "DIVISION", "DEPOT", "DAYS_PER_MONTH", "SERVICE_LEVEL", "TYPE_WEIGHT",
    "ROP_CRITICAL_FACTOR", "ROP_EXCESS_FACTOR", "HORIZON", "DMTR_DIR",
    "SUMMARY_WORKBOOK", "DIVISION_OUTPUT_DIR", "HISTORY_DIR",
    "get", "raw_dir", "summary_workbook", "live_divisions", "DIVISIONS",
    "ACTIVE_DIVISION", "divisions", "use_division",
]
