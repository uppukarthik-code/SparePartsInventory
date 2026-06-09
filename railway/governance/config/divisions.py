"""Division planning configuration (Phase B centralization; STEP37 multi-division).

Single source for the planning constants of the STEP20-28 extension. The MAS
values are byte-identical to the prior module-local literals, so MAS behaviour is
unchanged. STEP37 promotes this registry from MAS-only to all six live Southern
Railway divisions and resolves the SUMMARY OF STOCK HELD workbook by GLOB (rather
than a hardcoded, date-stamped filename) so a new daily snapshot never strands the
pipeline on a deleted file.

NOTE on depot: the depot code (e.g. 027534) is NOT a code filter anywhere; the
SUMMARY OF STOCK HELD workbook is inherently single-depot, so depot scoping is
carried by WHICH file is read (the division folder). Codes are provenance only.
"""
import glob

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

# --- division registry (STEP37: all six live divisions) -----------------------
# Each entry needs only its raw_subdir; the SUMMARY workbook is glob-resolved.
# `summary_filename` is an OPTIONAL pin (provenance / override) used only when the
# named file still exists; otherwise the glob resolver picks the live snapshot.
DIVISIONS = {
    "MAS": {"division": "MAS", "depot": "027534",
            "raw_subdir": ("Railway_Operations", "MAS"), **DEFAULTS},
    "SA":  {"division": "SA",  "depot": "067532",
            "raw_subdir": ("Railway_Operations", "SA"), **DEFAULTS},
    "TPJ": {"division": "TPJ", "depot": "077355",
            "raw_subdir": ("Railway_Operations", "TPJ"), **DEFAULTS},
    "MDU": {"division": "MDU", "depot": "087221",
            "raw_subdir": ("Railway_Operations", "MDU"), **DEFAULTS},
    "PGT": {"division": "PGT", "depot": "037254",
            "raw_subdir": ("Railway_Operations", "PGT"), **DEFAULTS},
    "TVC": {"division": "TVC", "depot": "057253",
            "raw_subdir": ("Railway_Operations", "TVC"), **DEFAULTS},
}

# Deterministic iteration order (matches enterprise display order).
DIVISION_ORDER = ["MAS", "SA", "TPJ", "MDU", "PGT", "TVC"]

ACTIVE_DIVISION = "MAS"


def get(division: str = ACTIVE_DIVISION) -> dict:
    """Return the resolved config dict for a division (KeyError if unknown)."""
    return DIVISIONS[division]


def live_divisions() -> list[str]:
    """Registered (live) divisions in canonical order."""
    return [d for d in DIVISION_ORDER if d in DIVISIONS]


def raw_dir(division: str = ACTIVE_DIVISION):
    return cfg.RAW_DATA_DIR.joinpath(*get(division)["raw_subdir"])


def summary_workbook(division: str = ACTIVE_DIVISION):
    """Resolve the division's current SUMMARY OF STOCK HELD workbook.

    Resolution order:
      1. an explicit ``summary_filename`` pin, IF that file still exists;
      2. otherwise glob ``SUMMARY OF STOCK HELD*.xlsx`` in the division folder,
         preferring the canonical ``(as on DD-MM-YYYY)`` variant, deterministically.
    Falling back to glob is what fixes a stale, deleted date-stamped filename.
    """
    d = get(division)
    base = raw_dir(division)
    pinned = d.get("summary_filename")
    if pinned and (base / pinned).exists():
        return base / pinned
    cands = sorted(glob.glob(str(base / "SUMMARY OF STOCK HELD*.xlsx")))
    if not cands:
        # preserve a deterministic path even when no file is present yet
        return base / (pinned or "SUMMARY OF STOCK HELD.xlsx")
    preferred = [c for c in cands if "(as on" in c]
    from pathlib import Path
    return Path((preferred or cands)[-1])
