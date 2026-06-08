"""
railway_business_unit_config.py
===============================
STEP 12.5 -- Enterprise Business-Unit dimension (configuration only).

Defines the `Business_Unit` enterprise dimension and the rules that map a raw
depot string to a business unit. Adding a new business unit (a new division, a
new training centre, a workshop, a production unit ...) is a pure configuration
change here -- no analytics, reporting or KPI code is touched.

Standard library only; no business logic -- this module never changes any KPI.
"""

from __future__ import annotations

import re

# ----------------------------------------------------------------------
# Business-unit master.  Extend by adding entries -- no code changes needed.
#   Status: "Live"       -> data is onboarded and flowing through analytics
#           "Configured" -> dimension ready, awaiting data onboarding
# ----------------------------------------------------------------------
BUSINESS_UNITS = {
    "MAS": {
        "Business_Unit": "MAS", "Name": "Chennai Division (Signal & Telecom)",
        "Division": "Chennai", "Inventory_Domain": "Railway_Operations",
        "Zone": "Southern Railway", "Status": "Live",
    },
    "SA": {
        "Business_Unit": "SA", "Name": "Salem Division (Signal & Telecom)",
        "Division": "Salem", "Inventory_Domain": "Railway_Operations",
        "Zone": "Southern Railway", "Status": "Live",
    },
    "TPJ": {
        "Business_Unit": "TPJ", "Name": "Tiruchirappalli Division (Signal & Telecom)",
        "Division": "Tiruchirappalli", "Inventory_Domain": "Railway_Operations",
        "Zone": "Southern Railway", "Status": "Live",
    },
    "MDU": {
        "Business_Unit": "MDU", "Name": "Madurai Division (Signal & Telecom)",
        "Division": "Madurai", "Inventory_Domain": "Railway_Operations",
        "Zone": "Southern Railway", "Status": "Live",
    },
    "PGT": {
        "Business_Unit": "PGT", "Name": "Palakkad Division (Signal & Telecom)",
        "Division": "Palakkad", "Inventory_Domain": "Railway_Operations",
        "Zone": "Southern Railway", "Status": "Live",
    },
    "TVC": {
        "Business_Unit": "TVC", "Name": "Thiruvananthapuram Division (Signal & Telecom)",
        "Division": "Thiruvananthapuram", "Inventory_Domain": "Railway_Operations",
        "Zone": "Southern Railway", "Status": "Live",
    },
    "STTC_PTJ": {
        "Business_Unit": "STTC_PTJ", "Name": "S&T Training Centre, Ponmalai (Tiruchirappalli)",
        "Division": "Tiruchirappalli", "Inventory_Domain": "Training_Centre",
        "Zone": "Southern Railway", "Status": "Configured",
    },
}

# Display / iteration order.
BUSINESS_UNIT_ORDER = ["MAS", "SA", "TPJ", "MDU", "PGT", "TVC", "STTC_PTJ"]

# ----------------------------------------------------------------------
# Depot-token -> Business_Unit resolution (configurable, priority-ordered).
# Matched as a whole token inside the raw depot string (e.g. the operational
# depot "SSET/SRM/PER027029-S AND T-SR" resolves via the "PER" token -> MAS).
# ----------------------------------------------------------------------
DEPOT_TOKEN_TO_BUSINESS_UNIT = [
    ("STTC", "STTC_PTJ"),   # training-centre stores
    ("PER", "MAS"),         # Perambur (Chennai)
    ("ED", "SA"),           # Erode (Salem division)
    ("GOC", "TPJ"),         # Golden Rock / Ponmalai (Tiruchirappalli)
    ("PTJ", "PGT"),         # Podanur Junction (Palakkad division) -- STEP19 verified
                            #   (was TPJ; corrected -- PTJ=Podanur is in Palakkad, not Trichy.
                            #    Never fires on operational depots, which carry literal TPJ/PGT.)
    ("QLN", "TVC"),         # Kollam / Quilon (Thiruvananthapuram)
    ("MDU", "MDU"),         # Madurai
    ("PGT", "PGT"),         # Palakkad
    # direct division codes (used when a depot already carries the BU code)
    ("MAS", "MAS"), ("SA", "SA"), ("TPJ", "TPJ"), ("TVC", "TVC"),
]

# Default business unit for the live Railway_Operations domain when a depot is
# absent (e.g. zone-consolidated strategic planning rows).
DEFAULT_BUSINESS_UNIT = "MAS"


def resolve_business_unit(depot, default=DEFAULT_BUSINESS_UNIT):
    """Map a raw depot string to a Business_Unit code (configuration-driven)."""
    if not depot or not isinstance(depot, str):
        return default
    up = depot.upper()
    for token, bu in DEPOT_TOKEN_TO_BUSINESS_UNIT:
        # whole-token match: token not flanked by other letters
        if re.search(r"(?<![A-Z])" + re.escape(token) + r"(?![A-Z])", up):
            return bu
    return default


def division_of(business_unit):
    """Division name for a business unit (blank if unknown)."""
    return BUSINESS_UNITS.get(business_unit, {}).get("Division", "")


def domain_of(business_unit):
    """Inventory_Domain for a business unit (blank if unknown)."""
    return BUSINESS_UNITS.get(business_unit, {}).get("Inventory_Domain", "")


def business_units_for_domain(inventory_domain):
    """All configured business units belonging to a domain, in display order."""
    return [bu for bu in BUSINESS_UNIT_ORDER
            if BUSINESS_UNITS.get(bu, {}).get("Inventory_Domain") == inventory_domain]


def is_live(business_unit):
    return BUSINESS_UNITS.get(business_unit, {}).get("Status") == "Live"
