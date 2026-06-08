# Power BI Compatibility Restoration Report (Phase 1)

**Generated:** 2026-06-08
**Mandate:** Fix **compatibility only**. No analytical logic, calculation, threshold, ranking,
classification, optimization logic, KPI, or output value was modified. All changes are
*additive columns* or *aliases of existing values*.

**Modules changed**
- `railway/railway_config.py` — added display-only `CRITICALITY_NAME_MAP`.
- `railway/railway_powerbi_export.py` — page1, page3, page4, page5, page9 column additions.
- `railway/railway_dashboard_validation.py` — V4 alias exemption + new V6 integrity checks.

**Regeneration sequence executed**
1. `python -m railway.railway_powerbi_export` → rebuilt `outputs/powerbi/page*.csv`
2. `python -m railway.railway_enterprise` → re-enriched `outputs/enterprise/powerbi/*.csv` (existing-outputs hash: **0 files changed by enterprise run**)
3. `python -m railway.railway_dashboard_validation` → V1–V6 **ALL PASS**

---

## 1. Changes by Page

### page1_procurement.csv
- `Description` — already carried from policy/SKU master (verified present; 0 nulls).
- **Added `Criticality_Name`** mapped from `Criticality` via config:
  `S1→Safety Critical, S2→Operational Critical, S3→Service Critical, S4→Non Critical`.

```diff
  p1 = p1.rename(columns={"Normalized_Procurement_Priority_Class": "Procurement_Priority_Class"})
+ p1["Criticality_Name"] = p1["Criticality"].map(cfg.CRITICALITY_NAME_MAP)
  p1["Source_Universe"] = "Strategic"
```

### page3_criticality.csv
- **Added `Description`** carried from `railway_sku_master.csv` (strategic 59-item master).
- **Added `Criticality_Name`** (same mapping as page1).

```diff
- p3 = master[["PL_Code", "Criticality", "ABC_Class"]] \
+ p3 = master[["PL_Code", "Description", "Criticality", "ABC_Class"]] \
        .merge(dq, ...).merge(forecast...).merge(policy...)
+ p3["Criticality_Name"] = p3["Criticality"].map(cfg.CRITICALITY_NAME_MAP)
  p3["Source_Universe"] = "Strategic"
- pages["page3_criticality"] = p3[["PL_Code","Criticality","ABC_Class",
-     "Normalized_Inventory_Value","Forecast_2026_27","Inventory_Status","Source_Universe"]]
+ pages["page3_criticality"] = p3[["PL_Code","Description","Criticality","Criticality_Name",
+     "ABC_Class","Normalized_Inventory_Value","Forecast_2026_27","Inventory_Status","Source_Universe"]]
```

### page4_operational_health.csv
- **Added `Description`** from the operational master (`railway_operational_inventory.csv`).
- Full detail in **`STEP12_5A_IMPLEMENTATION_REPORT.md`**.

### page5_rationalization.csv
- **Added `Description`** carried from `railway_inventory_rationalization.csv`.
- **Added compatibility alias `Inventory_Value = Normalized_Inventory_Value`** (identical value,
  no calculation change). Legacy visuals that bind to `Inventory_Value` are restored.

```diff
- p5 = rationalization[["PL_Code","Inventory_Action","Inventory_Value","Movement_Status","Source_Universe"]].copy()
+ p5 = rationalization[["PL_Code","Description","Inventory_Action","Inventory_Value","Movement_Status","Source_Universe"]].copy()
  p5 = p5.rename(columns={"Inventory_Value": "Normalized_Inventory_Value"})
+ p5["Inventory_Value"] = p5["Normalized_Inventory_Value"]   # alias; same value
```

### page9_management_actions.csv
- **Added `Description`**.

> ⚠️ **Interpretation flagged for review.** `page9` is an **action-level aggregate** (5 rows:
> Procure Immediately / Retain / Dispose / Rationalize / …) with **no per-SKU rows**, so a SKU-level
> `Description` cannot be literally carried without changing the grouping (which is forbidden).
> To restore legacy visuals that bind to a `Description` field, `Description` is supplied as a
> **compatibility alias of the existing `Action` label** (display-only, no analytics change).
> If a different meaning was intended (e.g., a hard-coded action narrative), advise and it will be adjusted.

```diff
  p9 = pd.DataFrame({
      "Action": actions,
+     "Description": actions,   # alias of Action label (aggregate has no SKU Description)
      "Count": [...], "Strategic_Inventory_Value": [...],
      "Operational_Inventory_Value": [...], "Priority": [...],
  })
```

---

## 2. Validation Results

### 2a. Invariance proof (regenerated vs. pre-change snapshot)

| Page | Rows before → after | Shared columns byte-identical | Σ Inventory / Normalized value | Verdict |
|---|---|---|---|---|
| page1_procurement | 59 → 59 | ✅ True (ranks + values) | unchanged | ✅ |
| page3_criticality | 59 → 59 | ✅ True | unchanged | ✅ |
| page4_operational_health | 907 → 907 | ✅ True | 512,406,406.47 = 512,406,406.47 | ✅ |
| page5_rationalization | 959 → 959 | ✅ True | 595,295,746.05 = 595,295,746.05 | ✅ |
| page9_management_actions | 5 → 5 | ✅ True (counts/values/priority) | unchanged | ✅ |
| page0_executive_dashboard | — | ✅ fully identical | KPIs unchanged | ✅ |
| page7_abc_criticality_matrix | — | ✅ fully identical | unchanged | ✅ |
| page8_budget_scenarios | — | ✅ fully identical | unchanged | ✅ |

### 2b. Lineage validation suite (`STEP11_VALIDATION_REPORT.md` — regenerated)

| # | Check | Result |
|---|---|---|
| V1 | Executive strategic value == Σ Normalized_Inventory_Value (85,663,636) | ✅ PASS |
| V2 | Procurement page total == Σ Normalized_Investment_Required (473,115,370) | ✅ PASS |
| V3 | Criticality matrix == Σ Normalized_Inventory_Value | ✅ PASS |
| V4 | No raw value/score columns on strategic pages (page5 alias exempted) | ✅ PASS |
| V5 | Top-20 rank comparison generated | ✅ PASS |
| **V6a** | **page5 `Inventory_Value` == `Normalized_Inventory_Value` (alias integrity)** | ✅ PASS |
| **V6b** | **`Description` populated on page1/page3/page4/page5 (0 nulls)** | ✅ PASS |
| **V6c** | **`Criticality_Name` populated on page1/page3 (0 nulls)** | ✅ PASS |

### 2c. Mandated checklist

| Requirement | Status |
|---|---|
| Row counts unchanged | ✅ (59 / 59 / 907 / 959 / 5) |
| KPI values unchanged | ✅ (page0/page7/page8 byte-identical) |
| Rankings unchanged | ✅ (page1 shared cols byte-identical) |
| Inventory values unchanged | ✅ (page4 & page5 sums identical) |
| Description populated | ✅ (0 nulls on page1/3/4/5) |
| Criticality_Name populated | ✅ (0 nulls; S1–S4 mapped per spec) |
| Legacy Power BI visuals restored | ✅ (Description, Criticality_Name, Inventory_Value alias all present) |

---

## 3. Criticality_Name Mapping (config — display only)

```python
CRITICALITY_NAME_MAP = {
    "S1": "Safety Critical",
    "S2": "Operational Critical",
    "S3": "Service Critical",
    "S4": "Non Critical",
}
```

The canonical `S1–S4` code remains the analytical classification; `Criticality_Name` is a
presentation alias only.

---

## 4. Files Regenerated

- `railway/outputs/powerbi/page{1,3,4,5,9}.csv` (+ unchanged page0/2/6/7/8)
- `railway/outputs/enterprise/powerbi/*.csv` (new columns inherited, slicers appended)
- `STEP11_VALIDATION_REPORT.md`, `step11_top20_rank_comparison.csv`
- `STEP12_5A_IMPLEMENTATION_REPORT.md` (page4 detail)

## 5. Known Cosmetic Note (out of scope, unchanged)

`railway_dashboard_validation.py` prints a `Σ` glyph that raises `UnicodeEncodeError` on a
default Windows **cp1252 console** (run with `PYTHONIOENCODING=utf-8` for clean console output).
This is a pre-existing console-print issue with **no effect on data, validation logic, or the
written report**, and was left untouched to honour the "compatibility only" scope.

---

## ✅ Phase 1 Complete

All five pages carry the required compatibility columns; every analytical value, ranking, KPI,
and row count is provably unchanged. The one interpretation decision (page9 `Description` =
`Action` alias) is flagged above for confirmation.
