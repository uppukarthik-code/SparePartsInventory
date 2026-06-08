"""Division planning configuration (Phase B centralization).

Single source for the previously-hardcoded planning constants of the STEP20-28
MAS extension. Values are byte-identical to the prior module-local literals, so
no output changes. The structure is division-keyed so additional divisions can be
onboarded by adding a registry entry plus their data (see the TPJ readiness
assessment) — but MAS behaviour is unchanged.

NOTE on depot: depot ``027534`` is NOT a code filter anywhere; the SUMMARY OF
STOCK HELD workbook is inherently single-depot, so depot scoping is carried by
``summary_filename`` (which file is read), recorded here for provenance only.

These constants intentionally mirror the modules' OWN values, which differ in
shape from the (separately-keyed, S1-S4) ``railway_config.SERVICE_LEVEL_TABLE`` /
``CRITICALITY_STOCKOUT_WEIGHT``; reconciling those two representations is a
documented follow-up, not part of this behaviour-preserving phase.
"""
from railway import railway_config as cfg

# --- planning defaults (shared across divisions; overridable per division) ----
DEFAULTS = {
    "DAYS_PER_MONTH": 30.4375,
    "SERVICE_LEVEL": {"Critical": 0.95, "Non-Critical": 0.85},
    "TYPE_WEIGHT": {"Safety Item": 10, "Vital Item": 5, "NA": 1},   # S1 / S2 / S4
    "ROP_CRITICAL_FACTOR": 0.5,    # cur < 0.5*ROP  -> Critical Shortage
    "ROP_EXCESS_FACTOR": 2.0,      # cur <= 2*ROP   -> Healthy, else Excess
    "HORIZON": ["Jul_2026", "Aug_2026", "Sep_2026", "Oct_2026", "Nov_2026", "Dec_2026",
                "Jan_2027", "Feb_2027", "Mar_2027", "Apr_2027", "May_2027", "Jun_2027"],
}

# --- division registry --------------------------------------------------------
DIVISIONS = {
    "MAS": {
        "division": "MAS",
        "depot": "027534",                       # provenance only (not a code filter)
        "raw_subdir": ("Railway_Operations", "MAS"),
        "summary_filename": "SUMMARY OF STOCK HELD (as on 08-06-2026) _08-06-2026.xlsx",
        **DEFAULTS,
    },
}

ACTIVE_DIVISION = "MAS"


def get(division: str = ACTIVE_DIVISION) -> dict:
    """Return the resolved config dict for a division (KeyError if unknown)."""
    return DIVISIONS[division]


def raw_dir(division: str = ACTIVE_DIVISION):
    d = get(division)
    return cfg.RAW_DATA_DIR.joinpath(*d["raw_subdir"])


def summary_workbook(division: str = ACTIVE_DIVISION):
    return raw_dir(division) / get(division)["summary_filename"]
