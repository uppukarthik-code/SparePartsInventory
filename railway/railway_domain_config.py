"""
railway_domain_config.py
========================
STEP 12.5 -- Enterprise Inventory_Domain dimension (configuration only).

Turns the single-purpose Railway Signalling analytics platform into a multi-domain
Enterprise Inventory MIS by introducing the top-level `Inventory_Domain` dimension.
New domains (Workshops, Production Units, Stores Depots, Training Centres, Project
Offices ...) are onboarded purely by adding an entry to `DOMAINS` -- no analytics,
reporting, KPI or dashboard code changes.

Standard library only; contains NO analytical/KPI business logic.
"""

from __future__ import annotations

from railway import railway_business_unit_config as bu

# ----------------------------------------------------------------------
# Enterprise governance constants
# ----------------------------------------------------------------------
# Source snapshot of the live Railway_Operations data ("Stock as on 31.03.2026").
DEFAULT_SNAPSHOT_DATE = "2026-03-31"
# Enterprise architecture version (Step 12.5). Bump when the enterprise layer changes.
ENTERPRISE_PIPELINE_VERSION = "12.5.0"

# The six enterprise metadata dimensions appended to every enriched export.
ENTERPRISE_DIMENSIONS = [
    "Inventory_Domain", "Business_Unit", "Division", "Depot",
    "Snapshot_Date", "Pipeline_Version",
]

# ----------------------------------------------------------------------
# Domain master.
#   Status: "Live"      -> full analytics + reporting package active
#           "Framework" -> dimension + metadata scaffolded, analytics not built yet
# ----------------------------------------------------------------------
DOMAINS = {
    "Railway_Operations": {
        "Domain_Name": "Railway Operations",
        "Business_Units": bu.business_units_for_domain("Railway_Operations"),
        "Default_Business_Unit": "MAS",
        "Default_Metadata": {
            "Inventory_Domain": "Railway_Operations",
            "Zone": "Southern Railway",
            "Snapshot_Date": DEFAULT_SNAPSHOT_DATE,
            "Pipeline_Version": ENTERPRISE_PIPELINE_VERSION,
        },
        "Reporting_Package": [
            "Procurement Review", "Dead Stock Review", "Rationalization Review",
            "Budget Review", "Management Pack",
        ],
        "Status": "Live",
    },
    "Training_Centre": {
        "Domain_Name": "Training Centre Assets",
        "Business_Units": bu.business_units_for_domain("Training_Centre"),
        "Default_Business_Unit": "STTC_PTJ",
        "Default_Metadata": {
            "Inventory_Domain": "Training_Centre",
            "Zone": "Southern Railway",
            "Snapshot_Date": DEFAULT_SNAPSHOT_DATE,
            "Pipeline_Version": ENTERPRISE_PIPELINE_VERSION,
        },
        # Framework only -- analytics intentionally NOT implemented in this step.
        "Reporting_Package": [],
        "Future_KPIs": [
            "Asset Availability", "Training Readiness", "AMC Coverage",
            "Warranty Status", "Asset Age Profile", "Replacement Planning",
        ],
        "Status": "Framework",
    },
}

# Domains planned for future onboarding -- configurable, no code changes required.
FUTURE_DOMAINS = [
    "Workshops", "Production Units", "Stores Depots",
    "Training Centres", "Project Offices",
]

DOMAIN_ORDER = ["Railway_Operations", "Training_Centre"]


# ----------------------------------------------------------------------
# Equipment-family classification (asset-registry metadata only).
# Ordered keyword rules, first match wins. Purely descriptive tagging; it does
# NOT feed any KPI, forecast, ABC, criticality or optimisation calculation.
# ----------------------------------------------------------------------
EQUIPMENT_FAMILY_RULES = [
    (("kavach", "tcas"), "Kavach"),
    (("axle counter", "axle-counter", "ssdac", "msdac"), "Axle Counter"),
    (("point machine",), "Point Machine"),
    (("relay",), "Relay"),
    (("led",), "LED Signal"),
    (("cable",), "Signal Cable"),
    (("ips", "integrated power"), "IPS"),
    (("battery charger", "charger", "stabilizer", "stabiliser"), "Power Supply"),
    (("lead acid", "cell", "battery"), "Battery / Cell"),
    (("telephone", "phone", "dtmp", "emt", "exchange"), "Telephone"),
    (("signal",), "Signal Equipment"),
    (("smart board", "interactive panel", "interactive board"), "Smart Board"),
    (("simulator",), "Training Simulator"),
    (("laptop",), "Laptop"),
    (("printer", "scanner"), "Printer"),
    (("router", "switch", "network", "modem", "ethernet"), "Network Equipment"),
    (("computer", "desktop", "workstation"), "Computer"),
    (("terminal block", "socket", "connector", "adopter", "adapter"), "Termination / Wiring"),
]
DEFAULT_EQUIPMENT_FAMILY = "Other / Unclassified"


def classify_equipment_family(description):
    """Tag an item description with an equipment family (registry metadata only)."""
    if not description or not isinstance(description, str):
        return DEFAULT_EQUIPMENT_FAMILY
    d = description.lower()
    for keywords, family in EQUIPMENT_FAMILY_RULES:
        if any(k in d for k in keywords):
            return family
    return DEFAULT_EQUIPMENT_FAMILY


def domain_metadata(inventory_domain):
    """Default metadata block for a domain (used to stamp exports)."""
    return dict(DOMAINS.get(inventory_domain, {}).get("Default_Metadata", {}))


def domain_name(inventory_domain):
    return DOMAINS.get(inventory_domain, {}).get("Domain_Name", inventory_domain)
