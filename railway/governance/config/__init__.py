"""railway.governance.config — centralized planning configuration (Phase B).

Resolves the ACTIVE division (MAS) into module-level constants that are
byte-identical to the prior hardcoded literals, so the STEP20-28 modules import
their constants from one place instead of re-declaring them. Division-agnostic by
construction (see ``divisions.py``); MAS behaviour unchanged.
"""
from railway.governance.config import divisions
from railway.governance.config.divisions import get, raw_dir, summary_workbook, DIVISIONS, ACTIVE_DIVISION

_ACTIVE = get(ACTIVE_DIVISION)

# --- MAS-resolved constants (exact prior values) ------------------------------
DIVISION = _ACTIVE["division"]
DEPOT = _ACTIVE["depot"]
DAYS_PER_MONTH = _ACTIVE["DAYS_PER_MONTH"]
SERVICE_LEVEL = _ACTIVE["SERVICE_LEVEL"]
TYPE_WEIGHT = _ACTIVE["TYPE_WEIGHT"]
ROP_CRITICAL_FACTOR = _ACTIVE["ROP_CRITICAL_FACTOR"]
ROP_EXCESS_FACTOR = _ACTIVE["ROP_EXCESS_FACTOR"]
HORIZON = _ACTIVE["HORIZON"]
DMTR_DIR = raw_dir(ACTIVE_DIVISION)
SUMMARY_WORKBOOK = summary_workbook(ACTIVE_DIVISION)

# --- division output routing (was the hardcoded "MAS" path/label everywhere) --
DIVISION_OUTPUT_DIR = divisions.cfg.OUTPUT_DIR / DIVISION
HISTORY_DIR = DIVISION_OUTPUT_DIR / "history"

__all__ = [
    "DIVISION", "DEPOT", "DAYS_PER_MONTH", "SERVICE_LEVEL", "TYPE_WEIGHT",
    "ROP_CRITICAL_FACTOR", "ROP_EXCESS_FACTOR", "HORIZON", "DMTR_DIR",
    "SUMMARY_WORKBOOK", "DIVISION_OUTPUT_DIR", "HISTORY_DIR",
    "get", "raw_dir", "summary_workbook", "DIVISIONS",
    "ACTIVE_DIVISION", "divisions",
]
