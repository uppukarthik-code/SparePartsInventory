# STEP37 — VALIDATION REPORT

**Date:** 2026-06-09
**Env:** conda `spareparts`, `PYTHONHASHSEED=0`

---

## 1. Test Suite — Baseline Preserved

| Run | Result |
|---|---|
| **Baseline (pre-change)** | 647 passed, 1 skipped, 0 failed |
| **After STEP37** | **661 passed, 1 skipped, 0 failed** |

Delta = **+14 new STEP37 tests** (TDD). All 647 original tests remain green; the 2 affected invariant tests were updated (intent-preserving, §4 of the implementation report) — none deleted, none failing.

```
$ PYTHONHASHSEED=0 python -m pytest railway/tests -q
661 passed, 1 skipped, 9340 warnings in 28.49s
```

### TDD evidence (RED → GREEN)
- New suite first run: **12 failed, 2 passed** — failures for the expected reason (missing `use_division`, unregistered divisions, un-retired constant, etc.).
- After implementation: **14 passed**.

---

## 2. Golden Baseline (STEP36) Integrity — Unchanged

The 537 pinned output CSVs were left untouched; the governed integrity gate passes:

```
$ python -c "from railway.tests.regression import manifest_tools as m; m.check()"
manifest integrity OK
```

- `test_golden_outputs.py`: all 537 hashes **MATCH**.
- `test_no_unexpected_new_outputs`: no committed outputs altered.
- STEP35 `test_enterprise_allocation.py`: **green** (enterprise allocation, frontier, roadmap, board KPIs intact).

---

## 3. Legacy Retirement — Verified

| Item | Evidence |
|---|---|
| `railway_stock_summary.xlsx` | File deleted (`git rm`); `OPERATIONAL_WORKBOOK` removed; `test_operational_workbook_constant_retired` green; full suite green with the file absent from disk. |
| `stock_history.xlsx` | `_load_stock_history_snapshot()` removed; `test_stock_history_snapshot_removed` + `test_no_stock_history_reference_in_demand_reconstruction` green. |
| `_build_stock_summary.py` | Deleted (obsolete builder). |

---

## 4. SUMMARY OF STOCK HELD as Operational Source — Verified

- `load_operational_stock()` now concatenates per-division SUMMARY files.
- Native column mapping confirmed by `test_operational_reads_native_summary_columns`: `Unit_Cost = col11`, `Inventory_Value = col12` (the +1 shift from the retired remapped workbook is corrected).
- Frame includes both TPJ (`TPJ` depot token) and MAS (`027534`) rows.

Validation run (scratch dir; committed outputs untouched):
```
all-division operational rows : 5696
TPJ operational rows          : 1355
TPJ inventory value (Rs)      : 209,048,735.20
TPJ zero-stock rows           : 787
```

---

## 5. Runtime Division Switching — Verified

`gcfg.use_division("TPJ")` re-points `gcfg` constants **and** the STEP20-28 modules' frozen captures, restoring on exit (`test_use_division_switches_summary_and_restores`, `test_use_division_switches_dmtr_dir_and_history`):

```
inside use_division("TPJ"):  gcfg.DIVISION == "TPJ"
                             gcfg.SUMMARY_WORKBOOK -> .../TPJ/SUMMARY...
                             safety_stock.SUMMARY == rop.SUMMARY == srrs.SUMMARY == gcfg.SUMMARY_WORKBOOK
                             gcfg.DMTR_DIR.name == "TPJ"; demand_reconstruction.DMTR_DIR re-pointed
after exit:                  restored to MAS
```

---

## 6. Stale MAS Filename — Fixed

```
gcfg.summary_workbook('MAS') -> SUMMARY OF STOCK HELD (as on 09-06-2026) _09-06-2026.xlsx
```
The deleted `08-06-2026` pin no longer strands the pipeline; the glob resolver selects the live `09-06` snapshot. MAS sanity run: `railway_inventory_policy.csv` = **59 rows** (unchanged).

---

## 7. Success Criterion — Met

> *"TPJ executes end-to-end and produces its own `railway_inventory_policy.csv` using native TPJ DMTR and SUMMARY OF STOCK HELD inputs."*

```
[TPJ full pipeline]  railway_inventory_policy.csv rows : 59  (50 procurement-required)
                     railway_operational_inventory.csv : 1355 rows (native TPJ SUMMARY)
[STEP21A native DMTR] 54 files -> 16,390 transactions -> 841 PLs -> 31,289 monthly rows
```
`test_tpj_produces_own_inventory_policy` and `test_tpj_demand_extraction_from_native_dmtr` both green.
