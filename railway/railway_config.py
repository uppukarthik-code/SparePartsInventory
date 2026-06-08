"""
railway_config.py
=================
Single source of truth for the Railway Signalling Spare Parts Analytics platform.

All locked business rules, thresholds, mappings, file paths and the *actual* workbook
coordinates discovered during Phase-1 discovery live here. Every other railway module
imports from this file so that scaling from 59 strategic items -> 907 depot items ->
full Southern Railway S&T inventory requires no code redesign, only configuration.

This module contains NO business logic and has NO third-party dependencies
(standard library only) so importing it can never affect the Walmart workflow.
"""

from pathlib import Path

# ======================================================================
# 1. PATHS  (everything is resolved relative to this file -> portable)
# ======================================================================
PACKAGE_DIR = Path(__file__).resolve().parent          # .../SparePartsInventory/railway
REPO_ROOT = PACKAGE_DIR.parent                          # .../SparePartsInventory
RAW_DATA_DIR = REPO_ROOT / "raw_data"

OUTPUT_DIR = PACKAGE_DIR / "outputs"
POWERBI_DIR = OUTPUT_DIR / "powerbi"
ANYLOGISTIX_DIR = OUTPUT_DIR / "anylogistix"
SAMPLE_OUTPUT_DIR = PACKAGE_DIR / "examples" / "sample_outputs"

# Core strategic output files
DEMAND_HISTORY_CSV = OUTPUT_DIR / "railway_demand_history.csv"
SKU_MASTER_CSV = OUTPUT_DIR / "railway_sku_master.csv"
FORECAST_CSV = OUTPUT_DIR / "railway_forecast.csv"
INVENTORY_POLICY_CSV = OUTPUT_DIR / "railway_inventory_policy.csv"


def ensure_output_dirs():
    """Create the output folder tree if it does not yet exist (idempotent)."""
    for d in (OUTPUT_DIR, POWERBI_DIR, ANYLOGISTIX_DIR, SAMPLE_OUTPUT_DIR):
        d.mkdir(parents=True, exist_ok=True)


# ======================================================================
# 2. WORKBOOKS  (two separate business domains -- never merged)
# ======================================================================
# Strategic / planning domain
STRATEGIC_WORKBOOK = RAW_DATA_DIR / "railways.xlsx"
# Operational / visibility domain
OPERATIONAL_WORKBOOK = RAW_DATA_DIR / "railway_stock_summary.xlsx"

# ----- railways.xlsx sheet names (verbatim, incl. leading spaces) -----
STRATEGIC_STOCK_SHEET = "  Stock as on 31.03.2026"      # primary modelling baseline
EARAAC_SHEET = "  % EARAAC as on 31.03.2026"            # Safety/Vital flag source
EAR_CONSUMPTION_SHEET = "EAR Consumptions"              # division-wise consumption

# ----- '  Stock as on 31.03.2026' -> 2-row banner header, data starts row 4 -----
STRATEGIC_HEADER_ROWS = (2, 3)
STRATEGIC_DATA_START_ROW = 4                            # 1-indexed
# 0-indexed column positions (discovered in Phase 1)
STRATEGIC_COLS = {
    "PL_Code":        1,
    "Description":    2,
    "FY2020_21":      3,
    "FY2022_23":      4,
    "FY2023_24":      5,
    "FY2024_25":      6,
    "FY2025_26":      7,
    "AAC":            8,
    "Current_Stock": 15,   # 'TOTAL' across the six depots
    "EAR_Qty":       16,   # 'EAR QTY. 2025-26'
    "Pending_Supply":17,   # 'P.O. qty pending supply'
    "Unit_Cost":     18,   # 'Rate in Rs.'
}
# Depot-wise stock columns (for AnyLogistix node stock)
STRATEGIC_DEPOT_COLS = {
    "GSD/PER":  9, "GSD/ED": 10, "LSD/MDU": 11,
    "DSD/QLN": 12, "GSD/GOC": 13, "SSD/PTJ": 14,
}
# STEP 19 -- verified strategic store-depot -> Business_Unit mapping.
# Each of the six Southern Railway divisions owns exactly one strategic store
# depot column in 'Stock as on ...'. Mapping verified in STEP19 against:
#   * structural 6-depot <-> 6-division (EAR Consumptions) elimination, and
#   * railway nomenclature (PER=Perambur/Chennai, ED=Erode/Salem, MDU=Madurai,
#     QLN=Quilon/Thiruvananthapuram, GOC=Golden Rock-Ponmalai/Tiruchirappalli,
#     PTJ=Podanur Junction/Palakkad).
# NOTE: SSD/PTJ resolves to PGT (Podanur is in the Palakkad division), NOT TPJ
# (Tiruchirappalli's store is GSD/GOC). See STEP19_VALIDATION_REPORT.md.
STRATEGIC_DEPOT_TO_BU = {
    "GSD/PER": "MAS", "GSD/ED": "SA", "LSD/MDU": "MDU",
    "DSD/QLN": "TVC", "GSD/GOC": "TPJ", "SSD/PTJ": "PGT",
}

# ----- '  % EARAAC as on 31.03.2026' -> single header row (row 2), data row 3 -----
EARAAC_DATA_START_ROW = 3
EARAAC_COLS = {"PL_Code": 1, "Description": 2, "Safety_Vital": 3}

# ----- 'EAR Consumptions' -> header row 2, data row 3.
# Each division has a (requirement, consumption) pair; we model the CONSUMPTION column.
EAR_CONSUMPTION_DATA_START_ROW = 3
EAR_CONSUMPTION_COLS = {"PL_Code": 1, "Description": 2}
# division -> 0-indexed consumption column
EAR_DIVISION_CONSUMPTION_COLS = {
    "MAS": 4, "TPJ": 6, "SA": 8, "MDU": 10, "PGT": 12, "TVC": 14,
}

# Canonical ordered list of consumption fiscal years (NOTE: 2021-22 is unavailable)
CONSUMPTION_YEARS = ["FY2020_21", "FY2022_23", "FY2023_24", "FY2024_25", "FY2025_26"]

# Backtest split (hold-out validation)
BACKTEST_TRAIN_YEARS = ["FY2020_21", "FY2022_23", "FY2023_24", "FY2024_25"]
BACKTEST_TEST_YEAR = "FY2025_26"
FORECAST_TARGET_YEAR = "FY2026_27"                      # label for Forecast_2026_27


# ======================================================================
# 3. ABC CLASSIFICATION  (Southern Railway Stores policy)
#    Annual Issue Value = AAC x Unit_Cost  (rupees)
# ======================================================================
LAKH = 100_000
ABC_THRESHOLDS = {        # lower-exclusive bounds in rupees
    "A":  69 * LAKH,      # > 69 lakh
    "B1": 35 * LAKH,      # 35 - 69 lakh
    "B2": 13 * LAKH,      # 13 - 35 lakh
    # C  : < 13 lakh (implicit)
}
ABC_ORDER = ["A", "B1", "B2", "C"]


def classify_abc(annual_issue_value):
    """Map an Annual Issue Value (Rs.) to its Southern Railway ABC band."""
    if annual_issue_value is None:
        return "C"
    v = float(annual_issue_value)
    if v > ABC_THRESHOLDS["A"]:
        return "A"
    if v > ABC_THRESHOLDS["B1"]:
        return "B1"
    if v > ABC_THRESHOLDS["B2"]:
        return "B2"
    return "C"


# ======================================================================
# 4. CRITICALITY  (from Safety/Vital sheet)
# ======================================================================
CRITICALITY_MAP = {"S": "S1", "V": "S2", "N": "S3"}     # else -> S4
DEFAULT_CRITICALITY = "S4"
CRITICALITY_ORDER = ["S1", "S2", "S3", "S4"]
# Human-readable criticality labels for Power BI legacy-visual compatibility.
# Display-only mapping (no analytical effect): the S1-S4 code remains the
# canonical classification; Criticality_Name is a presentation alias.
CRITICALITY_NAME_MAP = {
    "S1": "Safety Critical",
    "S2": "Operational Critical",
    "S3": "Service Critical",
    "S4": "Non Critical",
}
# Safety_Flag = Yes when the raw flag is one of these
SAFETY_FLAG_POSITIVE = {"S", "V"}


def map_criticality(safety_vital_flag):
    """Map a raw Safety/Vital flag (S/V/N/blank) to S1..S4."""
    if safety_vital_flag is None:
        return DEFAULT_CRITICALITY
    return CRITICALITY_MAP.get(str(safety_vital_flag).strip().upper(), DEFAULT_CRITICALITY)


# ======================================================================
# 5. INVENTORY COVERAGE KPI
#    Coverage = (Current_Stock + Pending_Supply) / EAR_Qty
# ======================================================================
# (upper-exclusive band edges, label)
COVERAGE_BANDS = [
    (0.5, "Critical Shortage"),
    (1.0, "Understocked"),
    (2.0, "Healthy"),
    (5.0, "Overstocked"),
    (float("inf"), "Excess Capital"),
]


def classify_coverage(ratio):
    """Map a coverage ratio to its band label."""
    if ratio is None:
        return "Unknown"
    for edge, label in COVERAGE_BANDS:
        if ratio < edge:
            return label
    return COVERAGE_BANDS[-1][1]


# ======================================================================
# 6. LEAD TIME LOGIC  (locked two-tier specification)
# ======================================================================
LEAD_TIME_MIN_MONTHS = 1
LEAD_TIME_MAX_MONTHS = 12
# Tier-2 fallback by criticality (used when Pending_Supply <= 0)
LEAD_TIME_FALLBACK_MONTHS = {"S1": 6, "S2": 4, "S3": 3, "S4": 2}
LEAD_TIME_DEFAULT_FALLBACK = 3


# ======================================================================
# 7. SERVICE-LEVEL TARGETS  (by ABC x Criticality -> z-value via scipy in optimizer)
# ======================================================================
# Authoritative target service level by (ABC_Class, Criticality). Any combination
# not listed falls back to DEFAULT_TARGET_SL.
# Step 17 hardening: centralized here (previously hard-coded in
# railway_inventory_optimization.py); a divergent, UNUSED `SERVICE_LEVEL_TARGETS`
# (ABC-only) was removed. Values are byte-for-byte UNCHANGED from the frozen optimizer.
SERVICE_LEVEL_TABLE = {
    ("A", "S1"): 0.99,
    ("A", "S2"): 0.98,
    ("B1", "S1"): 0.97,
    ("B2", "S2"): 0.95,
}
DEFAULT_TARGET_SL = 0.90


# ======================================================================
# 8. OPTIMIZATION WEIGHTS
# ======================================================================
# Criticality-weighted stockout penalty (replaces retail stockout logic)
CRITICALITY_STOCKOUT_WEIGHT = {"S1": 10, "S2": 5, "S3": 2, "S4": 1}
HOLDING_COST_RATE = 0.25          # annual holding cost as fraction of unit cost
ORDERING_COST_PER_ORDER = 500.0   # Rs. per replenishment order (assumption, tunable)

# ----------------------------------------------------------------------
# Step 15 -- SRRS calibration (post-audit STEP14)
# ----------------------------------------------------------------------
# Calibrated objective:  SRRS = Criticality_Weight * Service_Factor * Positive_Gap
# Demand_Factor and Lead_Time_Factor were REMOVED from the objective (they double-
# counted demand x lead time already embedded in Inventory_Gap via EDLT + safety
# stock). They remain as diagnostic columns only.
#
# Service_Factor recalibration: bounded linear discrimination
#   Service_Factor = 1 + SERVICE_FACTOR_SLOPE * max(0, Target_Service_Level - baseline)
# replaces the steep 1/(1-SL) which saturated at the 0.90 floor and re-counted the
# z(SL) already present in safety stock.
SERVICE_FACTOR_BASELINE_SL = 0.90     # service level mapped to Service_Factor = 1.0
SERVICE_FACTOR_SLOPE = 20.0           # 0.90->1.0, 0.95->2.0, 0.97->2.4, 0.98->2.6, 0.99->2.8

# Safety Reserve -- guarantees a budget share for high-consequence insurance spares
# (S1/S2) BEFORE the remaining budget is optimised across all items. Additive,
# config-gated: when disabled the allocator reduces to the legacy single knapsack.
SAFETY_RESERVE_ENABLED = True
SAFETY_RESERVE_BUDGET_PCT = 0.20      # fraction of EACH budget reserved for insurance spares first
SAFETY_RESERVE_CRITICALITIES = ("S1", "S2")   # criticality tiers that qualify as insurance spares


# ======================================================================
# 9. DEMAND CLASSIFICATION  (ADI / CV^2 framework -- Syntetos-Boylan)
# ======================================================================
ADI_CUTOFF = 1.32
CV2_CUTOFF = 0.49
# (demand_class names produced by railway_classification)
DEMAND_CLASSES = ["Smooth", "Intermittent", "Erratic", "Lumpy", "Dead"]


# ======================================================================
# 10. ANYLOGISTIX DIVISIONS  (Southern Railway)
# ======================================================================
ANYLOGISTIX_DIVISIONS = ["MAS", "TPJ", "SA", "MDU", "PGT", "TVC"]


# ======================================================================
# 11. FORECASTING -- primary blend weights (locked)
# ======================================================================
FORECAST_BLEND_WEIGHTS = {"AAC": 0.40, "EAR": 0.30, "MA": 0.20, "CAGR": 0.10}


# ======================================================================
# 12. PROCUREMENT BUDGET SCENARIOS  (Indian numbering)
# ======================================================================
PROCUREMENT_BUDGET = 1_00_00_000.0          # Rs 1 crore (default single scenario)
BUDGET_SCENARIOS = [                        # (label, rupees)
    ("Rs 50 Lakh", 50_00_000.0),
    ("Rs 1 Crore", 1_00_00_000.0),
    ("Rs 2 Crore", 2_00_00_000.0),
    ("Rs 5 Crore", 5_00_00_000.0),
]


# ======================================================================
# 13. DATA-QUALITY NORMALIZATION (unit-of-measure mismatch)
# ======================================================================
UNIT_COST_MISMATCH_THRESHOLD = 100_000      # Rs; above this + metre unit => suspect
UNIT_MISMATCH_DIVISOR = 1000.0              # per-km -> per-metre correction factor
METRE_UNIT_TOKENS = ("MTR", "METRE", "METER", "KM")


# ======================================================================
# 14. DEMAND ALLOCATION (AnyLogistix)
# ======================================================================
DEMAND_ALLOCATION_DEFAULT = "Equal_Split"   # used when division % unavailable


# ======================================================================
# 15. CONTROLLED VOCABULARIES (for schema validation)
# ======================================================================
VALID_ABC_CLASSES = {"A", "B1", "B2", "C"}
VALID_CRITICALITY = {"S1", "S2", "S3", "S4"}
VALID_DEMAND_CLASSES = {"Smooth", "Intermittent", "Erratic", "Lumpy", "Dead"}
VALID_FORECAST_CONFIDENCE = {"High", "Medium", "Low", "Very Low"}
VALID_INVENTORY_STATUS = {"Procurement Required", "Sufficient"}
