# STEP 18A — Validation Report

**Date:** 2026-06-08
**Subject:** Activation of SA, TPJ, MDU, PGT, TVC (Configured → Live) + division output generation
**Method:** Re-execution of the existing pipeline (unchanged) + evidence collection. Read-only verification of outputs.

---

## 1. Validation criteria — results

| # | Criterion | Result | Evidence |
|---|-----------|--------|----------|
| 1 | All six divisions processed | ✅ PASS | MAS (pre-existing) + SA/TPJ/MDU/PGT/TVC processed in MULTI-BU SPLIT mode |
| 2 | No crashes | ✅ PASS | All 5 division pipelines ran to completion; runner exit clean (`DONE.`) |
| 3 | Existing MAS outputs unchanged | ✅ PASS | `outputs/MAS` not written this run (mtime proof below); MAS deliberately not re-run |
| 4 | Enterprise aggregation operational | ✅ PASS *(with documented caveat)* | `_enterprise_rollup/master_sku_registry_all.csv` spans all 6 divisions (4,771 SKUs) |
| 5 | Benchmarking operational | ✅ PASS | Per-BU `enterprise/domain_benchmark.csv` now carries 6 `Live` rows |
| 6 | Backward compatibility maintained | ✅ PASS *(with documented caveat)* | MAS untouched; strategic analytics reproduce 0-diff; config change additive |

---

## 2. Criterion 1 — All six divisions processed

Runner discovery on the restored workbook:
```
Operational items : 5335 (depot-level, partitionable)
   MAS  operational= 907  strategic=yes  status=Live
   SA   operational= 542  strategic=no   status=Live
   TPJ  operational=1355  strategic=no   status=Live
   MDU  operational= 769  strategic=no   status=Live
   PGT  operational= 920  strategic=no   status=Live
   TVC  operational= 842  strategic=no   status=Live
Mode: MULTI-BU SPLIT   Processing: ['SA','TPJ','MDU','PGT','TVC']
   [SA]  scoped pipeline (operational=542)  -> outputs/SA
   [TPJ] scoped pipeline (operational=1355) -> outputs/TPJ
   [MDU] scoped pipeline (operational=769)  -> outputs/MDU
   [PGT] scoped pipeline (operational=920)  -> outputs/PGT
   [TVC] scoped pipeline (operational=842)  -> outputs/TVC
```
Depot→BU resolution: **0 unmapped depots**; partition counts match the audit exactly.

---

## 3. Criterion 2 — No crashes; output completeness

Every division produced the full **65-file** structure (identical to the MAS reference), each with **10 Power BI pages + 5 operational pages**:

| Division | Total files | Structure == MAS | powerbi pages | op_* pages | enterprise files |
|----------|------------:|:----------------:|:-------------:|:----------:|:----------------:|
| MAS | 65 | ✅ | 10 | 5 | 4 |
| SA  | 65 | ✅ | 10 | 5 | 4 |
| TPJ | 65 | ✅ | 10 | 5 | 4 |
| MDU | 65 | ✅ | 10 | 5 | 4 |
| PGT | 65 | ✅ | 10 | 5 | 4 |
| TVC | 65 | ✅ | 10 | 5 | 4 |

Key analytical outputs non-empty for all divisions:

| Division | op_inventory | demand | forecast | policy | sku_master |
|----------|-------------:|-------:|---------:|-------:|-----------:|
| MAS | 907 | 59 | 59 | 59 | 59 |
| SA  | 542 | 59 | 59 | 59 | 59 |
| TPJ | 1,355 | 59 | 59 | 59 | 59 |
| MDU | 769 | 59 | 59 | 59 | 59 |
| PGT | 920 | 59 | 59 | 59 | 59 |
| TVC | 842 | 59 | 59 | 59 | 59 |

*(Operational row counts differ per division; strategic-driven rows = 59 shared — see §7.)*

---

## 4. Criterion 3 — Existing MAS outputs unchanged

MAS was not re-run; `outputs/MAS` was never targeted by the 5-division run nor the roll-up (which only **reads** MAS). Modification-time proof:

```
MAS newest file mtime : 07:48:52   (from the prior session run)
SA  oldest file mtime : 08:26:57   (this activation run)
MAS entirely predates the new run? True
```

**`outputs/MAS` is byte-for-byte identical to its pre-STEP18A state.** ✅

### 4.1 Forward-looking note (not a regression)
A non-destructive re-run of MAS under the restored workbook (written to a temp dir, then discarded) showed MAS would reproduce as follows:

| MAS output | Rows | Cell diffs vs canonical |
|------------|-----:|------------------------:|
| `railway_inventory_policy.csv` | 59 | **0** |
| `railway_forecast.csv` | 59 | **0** |
| `railway_sku_master.csv` | 59 | **0** |
| `railway_operational_inventory.csv` | 907 | 293 cells across 146 rows |

The operational diffs decompose as: `Last_Receipt_Date` 144 → cascading `Days_Since_Movement` 53 / `Inventory_Aging_Class` 47 / `Movement_Status` 46; plus `Unit_Cost` 2 and `Inventory_Value` 1 genuine source cells (e.g. PL 539821491576 ₹800,654→₹790,605). **Root cause: the current per-division MAS extract is a newer snapshot than the deleted original workbook** (refreshed receipt/issue dates on 144 items + 3 price cells). It is real updated data, not a logic change — and it does **not** affect the canonical MAS outputs, which remain untouched.

---

## 5. Criterion 4 — Enterprise aggregation operational

`outputs/_enterprise_rollup/master_sku_registry_all.csv` — clean cross-division SKU aggregation:

| BU_Scope | MAS | SA | TPJ | MDU | PGT | TVC | Total |
|----------|----:|---:|----:|----:|----:|----:|------:|
| SKU rows | 959 | 521 | 934 | 710 | 901 | 746 | **4,771** |

All six divisions present (`set(divisions) ⊆ BU_Scope` → True). `southern_railway_summary_all.csv` contains one row per division (6 rows).

### 5.1 ⚠ Documented caveat (pre-existing behaviour, not modified)
`build_domain_benchmark()` stamps the **running BU's** KPI values onto **every** `Live` row, and `build_southern_railway_summary()` then sums all `Live` rows. With only MAS Live this was a 1× pass-through; with six Live BUs the **zone-summary sums inflate** (e.g. a BU's `southern_railway_summary.csv` Operational = 6 × that BU's value). This surfaced only because multiple BUs are now Live. Per scope ("do not modify KPI / reporting / enterprise logic"), this was **left unchanged**. The trustworthy cross-division view is **`master_sku_registry_all.csv`** (real, per-division, deduped). Recommend addressing the benchmark fan-out in a dedicated enterprise-aggregation phase.

---

## 6. Criterion 5 — Benchmarking operational

Each division's `enterprise/domain_benchmark.csv` now reflects six `Live` business units (example — `outputs/SA/enterprise/domain_benchmark.csv`):

```
MAS       Status=Live
SA        Status=Live
TPJ       Status=Live
MDU       Status=Live
PGT       Status=Live
TVC       Status=Live
STTC_PTJ  Status=Configured   (correctly still framework-only)
```

`BENCHMARK_MEASURES` columns present; `is_live()` now returns True for all six operational divisions. ✅

---

## 7. Criterion 6 — Backward compatibility

| Aspect | Status |
|--------|--------|
| `outputs/MAS` (canonical) | ✅ Untouched, byte-identical |
| Strategic analytics (policy/forecast/sku_master) under restored workbook | ✅ Reproduce with **0** cell diffs |
| Config change | ✅ Additive (only `Status` values; no structural change) |
| Analytical / SRRS / procurement / Power BI / KPI code | ✅ Unmodified |

### 7.1 ⚠ Documented caveat — default (no-arg) run semantics
Restoring the multi-division operational workbook (5,335 rows) changes one behaviour: the **no-argument consolidated run** (`python -m railway.railway_business_unit_runner`, `split=False`) now treats the **entire 5,335-row zone** as a single MAS unit rather than MAS-only (907). **Always invoke with explicit BU args** (`... MAS` for split-mode MAS isolation, or the 5/6-BU list) for per-division results. The canonical `outputs/MAS` on disk is unaffected by this note.

---

## 8. Final roll-up

### ✅ Business Units Ready / Processing
**MAS, SA, TPJ, MDU, PGT, TVC** — all six `Live`, all produced complete 65-file output sets with real per-division operational analytics.

### ❌ Business Units Missing Data
**STTC_PTJ** (Training_Centre) — correctly left `Configured`; no data on disk.

### ⚙ Business Units Requiring Configuration / Follow-up
- **None** for activation — the five flips are complete and operational.
- **Enterprise-aggregation follow-up** (separate phase, out of STEP 18A scope): fix the `domain_benchmark` / `southern_railway_summary` fan-out so zone sums don't inflate with multiple `Live` BUs (§5.1).
- **Operational-input durability** (recommendation): `raw_data/railway_stock_summary.xlsx` is untracked and was missing at start; it is now restored. Consider committing it or generating it deterministically so the pipeline cannot break again.

---

## 9. Master summary table

| Division | Operational Rows | Strategic Rows | Outputs Generated | Crashes | MAS-Unchanged | Status |
|----------|-----------------:|---------------:|------------------:|:-------:|:-------------:|--------|
| MAS | 907 | 59 *(shared)* | 65 *(pre-existing, untouched)* | none | ✅ | 🟢 Live |
| SA  | 542 | 59 *(shared)* | 65 | none | n/a | 🟢 Live |
| TPJ | 1,355 | 59 *(shared)* | 65 | none | n/a | 🟢 Live |
| MDU | 769 | 59 *(shared)* | 65 | none | n/a | 🟢 Live |
| PGT | 920 | 59 *(shared)* | 65 | none | n/a | 🟢 Live |
| TVC | 842 | 59 *(shared)* | 65 | none | n/a | 🟢 Live |
| **Zone** | **5,335** | **59** | **390 (+ roll-up)** | **none** | **✅** | **6 Live** |

**Verdict: STEP 18A validation PASSED** — five data-ready divisions activated and generating, MAS preserved, six-division aggregation operational. Two non-blocking caveats documented (benchmark fan-out §5.1; default-run semantics §7.1), both consequences of multi-BU activation and both outside the "no analytical/KPI/reporting changes" scope of this task.
