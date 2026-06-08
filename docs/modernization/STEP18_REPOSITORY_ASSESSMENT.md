# STEP 18 — Repository Assessment (Multi-Business-Unit Readiness)

**Generated:** 2026-06-08
**Mode:** 🔍 **PRE-IMPLEMENTATION GATE — READ-ONLY. No code written.**
**Question:** Can the existing pipeline be executed repeatedly for multiple Business Units
(e.g. **MAS** = Chennai/Perambur, **TPJ** = Tiruchirappalli/Golden Rock) simply by changing
execution context?

---

## 0. Executive Verdict

| # | Question | Answer |
|---|---|---|
| **A** | MAS & TPJ processed independently without modifying **analytical** code? | **NO today — but achievable WITHOUT analytical changes.** Blocked by the I/O context layer + absence of input scoping, not by the analytics. |
| **B** | Modules assuming a single output directory? | **All writer modules (15)** — every one references `cfg.OUTPUT_DIR`/`POWERBI_DIR` globals; several freeze them at import. |
| **C** | Modules assuming a single demand-history file? | All readers of `cfg.DEMAND_HISTORY_CSV` (data_preparation, forecasting, classification, inventory_optimization, data_quality). |
| **D** | Modules assuming a single SKU master? | All readers of `cfg.SKU_MASTER_CSV` (classification, inventory_optimization, rationalization, executive_summary, powerbi_export, enterprise). |
| **E** | Is a context-based runner sufficient? | **Necessary but NOT sufficient alone.** Must be paired with (1) config path parameterization and (2) an ingestion-scoping step. A naïve env-var runner will not work because paths are import-time constants. |
| **F** | Is analytical module refactoring required? | **NO.** The analytical modules are BU-agnostic, PL_Code-keyed pure functions with no embedded division logic. |

**Bottom line:** the work is an **I/O-context + data-scoping** refactor, not an analytics rewrite.

---

## 1. Input-Reading Modules (audit)

| Module | Reads | Source binding |
|---|---|---|
| `railway_data_preparation` | `STRATEGIC_WORKBOOK` (railways.xlsx), `OPERATIONAL_WORKBOOK` (stock_summary.xlsx) | `cfg.*_WORKBOOK` globals (single files) |
| `railway_classification` | `DEMAND_HISTORY_CSV` + safety/vital | `cfg.DEMAND_HISTORY_CSV` |
| `railway_forecasting` | `DEMAND_HISTORY_CSV` | `cfg.DEMAND_HISTORY_CSV` |
| `railway_inventory_optimization` | `DEMAND_HISTORY_CSV`, `SKU_MASTER_CSV`, `FORECAST_CSV` | `cfg.*_CSV` globals |
| `railway_data_quality` | strategic workbook (via dp), `INVENTORY_POLICY_CSV` | `cfg.*` |
| `railway_inventory_rationalization` | `SKU_MASTER_CSV`, `INVENTORY_POLICY_CSV`, `data_quality.csv`, `operational_inventory.csv` | `cfg.*` / `cfg.OUTPUT_DIR` |
| `railway_operational_analysis` | `OPERATIONAL_WORKBOOK` (via dp) | `cfg.OPERATIONAL_WORKBOOK` |
| `railway_executive_summary` | `SKU_MASTER_CSV`, `FORECAST_CSV`, `INVENTORY_POLICY_CSV`, `data_quality.csv`, plan | `cfg.*` |
| `railway_powerbi_export` | policy, master, forecast, operational, rationalization, dq, `op_inventory_summary` | `cfg.OUTPUT_DIR` / `cfg.POWERBI_DIR` |
| `railway_enterprise` | `SKU_MASTER_CSV`, `op_inventory_summary`, all PBI pages, KPI summary | `cfg.OUTPUT_DIR`/`POWERBI_DIR` |
| `railway_anylogistix_export` | division consumption + several `OUTPUT_DIR` csvs | `cfg.*` |
| `schema_validation`, `*_validation`, `railway_explainability`, `railway_audit_trail` | produced csvs | `cfg.OUTPUT_DIR`/`POWERBI_DIR` |

Every input path resolves to a **single global constant** in `railway_config.py`. No reader accepts
an input path / BU as a parameter.

## 2. Output-Writing Modules (audit)

| Module | Writes to |
|---|---|
| data_preparation | `cfg.DEMAND_HISTORY_CSV` |
| classification | `cfg.SKU_MASTER_CSV` |
| forecasting | `cfg.FORECAST_CSV` |
| inventory_optimization | `cfg.INVENTORY_POLICY_CSV`, `cfg.OUTPUT_DIR/{matrix,procurement_plan}` |
| data_quality | `cfg.INVENTORY_POLICY_CSV`, `cfg.OUTPUT_DIR/data_quality`, `cfg.POWERBI_DIR/page6` |
| inventory_rationalization | `cfg.OUTPUT_DIR/{rationalization,summary}` |
| operational_analysis | `cfg.OUTPUT_DIR/*`, `cfg.POWERBI_DIR/op_*` |
| executive_summary | `cfg.OUTPUT_DIR/*`, `cfg.POWERBI_DIR/page0` |
| powerbi_export | `cfg.POWERBI_DIR/page0..9` |
| enterprise | `OUTPUT_DIR/enterprise/*`, `…/enterprise/powerbi/*`, **repo-root** `STEP12_5_*.md` |
| anylogistix_export | `cfg.ANYLOGISTIX_DIR/*`, **repo-root** `ANYLOGISTIX_READINESS_REPORT.md` |
| dashboard_validation | `cfg.OUTPUT_DIR/step11_*`, **repo-root** `STEP11_VALIDATION_REPORT.md` |
| management_reports / lineage | `cfg.OUTPUT_DIR/reports/*`, `cfg.OUTPUT_DIR/data_lineage_report.csv` |
| explainability / audit_trail | `cfg.OUTPUT_DIR/funding_explainability.csv`, **repo-root** `STEP17_AUDIT_TRAIL.json` |

**Every writer targets the one fixed `cfg.OUTPUT_DIR` tree** (plus a few repo-root reports). Running
the pipeline twice for two BUs would **overwrite the same files** — MAS and TPJ outputs cannot coexist.

## 3. Hard-Coded Paths

All paths are **centralized** in `railway_config.py` (good) but defined as **static, import-time
constants** (the problem):

```python
PACKAGE_DIR  = Path(__file__).resolve().parent
REPO_ROOT    = PACKAGE_DIR.parent
RAW_DATA_DIR = REPO_ROOT / "raw_data"
OUTPUT_DIR   = PACKAGE_DIR / "outputs"          # <- single, fixed
POWERBI_DIR  = OUTPUT_DIR / "powerbi"
ANYLOGISTIX_DIR = OUTPUT_DIR / "anylogistix"
DEMAND_HISTORY_CSV = OUTPUT_DIR / "railway_demand_history.csv"
SKU_MASTER_CSV     = OUTPUT_DIR / "railway_sku_master.csv"
FORECAST_CSV       = OUTPUT_DIR / "railway_forecast.csv"
INVENTORY_POLICY_CSV = OUTPUT_DIR / "railway_inventory_policy.csv"
STRATEGIC_WORKBOOK   = RAW_DATA_DIR / "railways.xlsx"
OPERATIONAL_WORKBOOK = RAW_DATA_DIR / "railway_stock_summary.xlsx"
```

No paths are hard-coded **outside** config except derived report writes (`OUT.parent.parent /
"STEP*.md"`) and `ENTERPRISE_DIR = OUTPUT_DIR / "enterprise"`. Centralization is strong; **mutability
is the gap.**

## 4. Global Configuration Dependencies (critical subtlety)

Every module does `from railway import railway_config as cfg`. Crucially, **several modules capture
the path into their own module-level constant at import time**, e.g.:

```python
# railway_powerbi_export.py, railway_enterprise.py, railway_dashboard_validation.py,
# railway_audit_trail.py:
OUT = cfg.OUTPUT_DIR
PBI = cfg.POWERBI_DIR
```

Consequence: **monkey-patching `cfg.OUTPUT_DIR` at runtime would NOT redirect these modules** — they
already froze the value at first import. A pure "set an env var / mutate cfg" runner therefore cannot
work without either (a) refactoring these to resolve the path lazily, or (b) re-importing modules per
BU (fragile). This is the single most important technical blocker for context-only switching.

## 5. Data-Separability Analysis (the deeper blocker)

Business-Unit resolution **already exists** as configuration (`railway_business_unit_config.py`):
`DEPOT_TOKEN_TO_BUSINESS_UNIT` maps depot tokens → BU (`PER→MAS`, `GOC/PTJ→TPJ`, `ED→SA`, …), with
`resolve_business_unit()` and `division_of()`. BU is currently a **derived slicer dimension** applied
by the enterprise layer *after* analytics — not an ingestion partition.

| Universe | BU granularity in source | Today's pipeline |
|---|---|---|
| **Operational** (`stock_summary.xlsx`, 907 rows) | **Per-depot** (`Depot` column → resolvable to BU) | Reads **all** rows; tags BU only in enterprise enrichment. **Filterable by BU.** |
| **Strategic** (`railways.xlsx`, 59 rows) | **Zone-consolidated** — the 'Stock as on 31.03.2026' sheet carries one zone-level row per PL (AAC, EAR_Qty, Pending_Supply, Current_Stock, Unit_Cost). These feed demand_history → forecast → policy → **SRRS**. | Runs on the **zone aggregate**; no division split. |
| Strategic — *available* division detail | `load_division_consumption()` reads `EAR_DIVISION_CONSUMPTION_COLS` (MAS/TPJ/SA/MDU/PGT/TVC); `STRATEGIC_DEPOT_COLS` gives 6 depot stock columns | Loaded only for **AnyLogistix** demand allocation — **not** wired into the core demand_history. |

**Implication:** the operational universe is data-ready for per-BU runs (just needs a filter). The
**strategic/SRRS** universe is currently **zone-level**; division-wise consumption + depot stock
**exist** in the source, so a per-division strategic model is *data-feasible*, but it requires
**constructing a division-scoped `demand_history`/`sku_master`** from those columns — a data-modelling
decision, still **not** an analytical-code change.

---

## 6. Explicit Answers

### A. Can MAS and TPJ be processed independently without modifying analytical code?
**Not today**, but **yes after I/O + ingestion changes that leave analytics untouched.** Two blockers,
neither analytical:
1. **I/O context** — fixed global output/input paths (frozen at import in several modules) → two BU
   runs collide on one output tree and share one input set.
2. **Input scoping** — no step produces a BU-scoped `demand_history`/`sku_master`/operational slice;
   strategic inputs are zone-consolidated.
The analytics (classification, forecasting, optimization/SRRS, data_quality, rationalization,
operational_analysis, executive_summary, powerbi_export) are PL_Code-keyed and BU-agnostic — they run
unchanged on whatever scoped inputs they receive.

### B. Which modules assume a single output directory?
**All 15 writer modules** (§2). Each references `cfg.OUTPUT_DIR` / `cfg.POWERBI_DIR` /
`cfg.ANYLOGISTIX_DIR` / `cfg.*_CSV`; `powerbi_export`, `enterprise`, `dashboard_validation`,
`audit_trail` additionally **freeze** `OUT/PBI` at import. Repo-root report writers
(`enterprise`, `anylogistix_export`, `dashboard_validation`, `audit_trail`) also assume a single
destination.

### C. Which modules assume a single demand-history file?
Every consumer of `cfg.DEMAND_HISTORY_CSV`: **`railway_data_preparation`** (writer),
**`railway_classification`**, **`railway_forecasting`**, **`railway_inventory_optimization`**
(`_load_inputs`), and **`railway_data_quality`** (via `dp.build_demand_history`).

### D. Which modules assume a single SKU master?
Every consumer of `cfg.SKU_MASTER_CSV`: **`railway_classification`** (writer),
**`railway_inventory_optimization`**, **`railway_inventory_rationalization`**,
**`railway_executive_summary`**, **`railway_powerbi_export`**, **`railway_enterprise`**
(`build_master_registry`).

### E. Is a context-based runner sufficient?
**Necessary but not sufficient by itself.** A runner that loops BUs and injects context is the right
orchestration shape, but on its own it **fails** because (i) several modules cache `cfg.OUTPUT_DIR`
at import (mutating cfg won't redirect them) and (ii) no BU-scoped inputs exist. It becomes sufficient
**only when paired with**:
1. **Config path parameterization** — resolve `OUTPUT_DIR`/`POWERBI_DIR`/`*_CSV`/workbooks from a
   runtime **context** (BU code → `outputs/<BU>/…`), and make the module-level `OUT/PBI` captures
   lazy (accessor/`get_paths(ctx)`), so a runner can set context per BU.
2. **Ingestion scoping** — a pre-step that materialises per-BU inputs: filter operational rows by
   `resolve_business_unit(Depot)`; for strategic, decide zone-level vs division-level
   `demand_history` (the division consumption columns make the latter feasible).
No analytical module is touched by either.

### F. Is analytical module refactoring required?
**No.** Classification, forecasting, inventory_optimization (SRRS + Safety Reserve + knapsack),
data_quality normalization, rationalization, operational_analysis, executive_summary and
powerbi_export contain **no hard-coded BU/division logic** and operate purely on PL_Code-keyed input
frames. They produce identical, correct results for any BU-scoped input. The required changes are
confined to **configuration (path context)** and a **new ingestion-scoping + runner layer** — both
additive.

---

## 7. Recommended Implementation Shape (for the gated work — not yet built)

1. **Context object / path factory** in `railway_config` — `get_context(bu)` returning a paths bundle
   (`outputs/<bu>/…`, `outputs/<bu>/powerbi/…`); replace frozen `OUT = cfg.OUTPUT_DIR` module captures
   with a lazy accessor so a runner can switch context per BU. (Default context = current single-tree
   → preserves all existing Step-1…17 outputs byte-identically.)
2. **Ingestion scoping module** — build per-BU `demand_history`/`sku_master`/operational slice using
   the existing `railway_business_unit_config` resolver (operational: filter by depot→BU; strategic:
   zone-level pass-through initially, division-level optional later via `EAR_DIVISION_CONSUMPTION_COLS`).
3. **Context runner** — iterate `BUSINESS_UNIT_ORDER` (or a CLI BU list), set context, invoke the
   existing module `run()` sequence unchanged, emit per-BU audit trails.
4. **Backward-compatibility guard** — default/"ALL" context must reproduce today's outputs exactly
   (golden-manifest check, as in Step 17).

---

## 8. Gate Decision

The assessment is complete. **Implementation may proceed**, scoped to:
- ✅ Configuration path-context parameterization (incl. de-freezing module-level `OUT/PBI` captures)
- ✅ A new ingestion-scoping layer (BU filter, reusing existing BU config)
- ✅ A context-based multi-BU runner
- 🚫 **No analytical-module refactoring** (explicitly out of scope and unnecessary)
- 🚫 No change to SRRS / Service_Factor / criticality weights / knapsack / Safety Reserve / KPIs /
  Power BI schemas (frozen since Step 17) for the default single-BU context.
