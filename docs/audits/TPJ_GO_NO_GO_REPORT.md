# TPJ GO / NO-GO REPORT
### STEP37 — Legacy Dependency & True Data Contract Audit (READ-ONLY)

**Date:** 2026-06-09
**Scope:** Determine whether the platform can operate **without** `railway_stock_summary.xlsx` and `stock_history.xlsx`, and what TPJ onboarding actually requires.
**Status:** AUDIT ONLY — no code, config, notebooks, or tests were modified.

---

## 0. Headline Verdict

| Question | Verdict |
|---|---|
| Can TPJ be onboarded **without code changes**? | **NO** — config alone is insufficient (3 hard blockers below). |
| Can `railway_stock_summary.xlsx` be retired? | **YES — but requires one code change** (`load_operational_stock`). |
| Can `stock_history.xlsx` be retired? | **YES — cleanly, no code change required.** |
| Overall TPJ onboarding | **CONDITIONAL GO** — small, well-scoped change (~1-2 weeks, pipeline is reusable). |

The good news: the deep planning engine (STEP21A–26) is **already division-parameterized** through `railway.governance.config` (`gcfg`). It reads `DMTR_*.xlsx` and `SUMMARY OF STOCK HELD*.xlsx` from `raw_data/Railway_Operations/<DIV>/` at their **native** column positions. No schema mapping or transformation layer is needed — TPJ's source files are **byte-schema-identical** to MAS's.

The blockers are all in the **configuration registry, the division-activation mechanism, and the one legacy operational loader** — not in the analytics.

---

## 1. The Two Data Architectures (why this is subtle)

The platform runs **two parallel ingestion contracts**:

**A. Strategic core + Enterprise allocation (STEP1–19, STEP18 runner, STEP35)**
- Strategic source: `raw_data/railways.xlsx` ✅ (valid, the only strategic workbook).
- Operational source: `raw_data/railway_stock_summary.xlsx` ❌ (STALE / forbidden).
- STEP35 enterprise allocation pools `outputs/<DIV>/railway_inventory_policy.csv`, which is **strategic-driven (59 items)** and **currently byte-identical across all 6 divisions** (MD5 `ffa1f1f45d`). → Enterprise allocation is presently pooling **six clones of MAS**.

**B. Per-division deep planning (STEP20–28)**
- Sources: `raw_data/Railway_Operations/<DIV>/DMTR_*.xlsx` (demand) + `SUMMARY OF STOCK HELD*.xlsx` (current stock, criticality, unit cost).
- Reads via `gcfg.DMTR_DIR` / `gcfg.SUMMARY_WORKBOOK`, **division-aware by construction**.
- Currently produces output for **MAS only** (`outputs/MAS/history/`); no other division has a `history/` dir.

`stock_history.xlsx` was only ever the **build input** to architecture A's operational workbook (via the one-off `_build_stock_summary.py`). Architecture B never needed it.

---

## 2. Can the platform run WITHOUT `railway_stock_summary.xlsx`? — YES, with one fix

**Who consumes it (package only):**
- `railway_config.OPERATIONAL_WORKBOOK` (constant)
- `railway_data_preparation.load_operational_stock()` — **MANDATORY** for the operational pipeline
- `railway_operational_analysis` (STEP6 — dead-stock / slow-moving / zero-stock / valuation) — **MANDATORY**, and it is in the STEP18 runner `PIPELINE`
- `railway_business_unit_runner.load_reference_once / scoped_loaders` — **MANDATORY** for the multi-BU depot partition
- `railway_inventory_rationalization` — indirect (reads STEP6 *outputs*, not the workbook)
- `railway_lineage`, `railway/__init__.py` — documentation strings only

**Does the strategic core / STEP35 need it?** **No.** `build_demand_history`, classification, forecasting, `inventory_optimization` → `railway_inventory_policy.csv` → `enterprise_allocation` all run from `railways.xlsx` only. The single `load_operational_stock()` call inside `data_preparation.run()` (L262) is a cosmetic row-count print.

**The retirement blocker — a one-column shift:**
`load_operational_stock()` reads `Unit_Cost = col12`, `Inventory_Value = col13`. But the **native** `SUMMARY OF STOCK HELD` layout is `Average Rate = col11`, `Value = col12` (confirmed: `srrs` reads `col11`, `rop` reads `col8`). The `railway_stock_summary.xlsx` workbook only matched the loader because `_build_stock_summary.py` **remapped `11→12, 12→13`** when concatenating the per-division extracts.

> **Therefore:** retiring `railway_stock_summary.xlsx` requires modifying `load_operational_stock()` to (a) glob+concat `raw_data/Railway_Operations/<DIV>/SUMMARY OF STOCK HELD*.xlsx`, and (b) read native indices (`col11`/`col12`). Bonus: because the per-division SUMMARY files are already folder-scoped by division, the runner's depot-string→BU partition logic becomes a trivial folder selection.

**Verdict:** ✅ **`railway_stock_summary.xlsx` can be retired.** Cost = 1 focused loader change + delete `_build_stock_summary.py`.

---

## 3. Can the platform run WITHOUT `stock_history.xlsx`? — YES, cleanly

**Only one package reference:** `railway_demand_reconstruction._load_stock_history_snapshot()` — and it is **fully optional**:

```python
p = DMTR_DIR / "stock_history.xlsx"
if not p.exists():
    return {}          # graceful: empty reconciliation anchor
```

It is a STEP21A **closing-stock reconciliation anchor only** (the reconstructed `Closing_Stock` is already labelled AMBER / "do not use for planning"). All other references are non-package audit scripts (`_step21a_run.py`, `_step27_audit.py`, `_final_audit.py`, `_build_stock_summary.py`) or documentation.

**Verdict:** ✅ **`stock_history.xlsx` can be retired with no code change.** The files are already deleted and the pipeline degrades gracefully. Recommended (hygiene, not required): delete the dead method + update the docstring.

---

## 4. Can TPJ be onboarded WITHOUT code changes? — NO (3 blockers)

1. **Division registry is MAS-only.** `governance/config/divisions.py` `DIVISIONS = {"MAS": {...}}` and `ACTIVE_DIVISION = "MAS"`. TPJ has no entry. *(A registry edit is "configuration" in spirit, but it is still editing a `.py` file.)*
2. **No runtime division-switch.** `gcfg` resolves `DMTR_DIR`, `SUMMARY_WORKBOOK`, `HISTORY_DIR` **once at import** from `ACTIVE_DIVISION`. The STEP21A–26 modules freeze these as module constants at import. There is **no `use_division()` context** (unlike `railway_context.use_context` which only covers the STEP1-19 *output* paths, not `gcfg`). Running a second division in one process is impossible without an activation/reload mechanism. **This is code.**
3. **MAS's own config is already stale.** Registered `summary_filename = "SUMMARY OF STOCK HELD (as on 08-06-2026) _08-06-2026.xlsx"` — but that file is **deleted**; raw_data now holds the `09-06-2026` snapshot. A fresh MAS planning run would `FileNotFound`. The filename is hardcoded, not globbed.

Plus the operational-source migration from §2 (needed because `railway_stock_summary.xlsx` is forbidden).

**Verdict:** ❌ **Not config-only.** It is **configuration + a thin enabling change** — explicitly *not* a schema-mapping layer (schemas are identical) and *not* a transformation layer.

---

## 5. Exact Modules That Must Be Modified

| # | File | Change | Why |
|---|---|---|---|
| 1 | `railway/governance/config/divisions.py` | Add `TPJ` (and other live divisions) to `DIVISIONS`; change `summary_filename` to a **glob** (`SUMMARY OF STOCK HELD*_*.xlsx`); fix MAS to the 09-06 snapshot | Register TPJ; stop date-hardcoding; unbreak MAS |
| 2 | `railway/governance/config/__init__.py` | Add a `use_division(div)` context / reload switch (mirror `railway_context`) | Enable per-division runs; STEP21A–26 modules then need **no change** |
| 3 | `railway/railway_data_preparation.py` | `load_operational_stock()`: glob+concat per-division `SUMMARY*.xlsx`, fix indices `col12→col11`, `col13→col12` | Retire `railway_stock_summary.xlsx` |
| 4 | `railway/railway_config.py` | Retire/repoint `OPERATIONAL_WORKBOOK` | Remove the stale workbook constant |
| 5 *(hygiene)* | `railway/railway_demand_reconstruction.py` | Remove `_load_stock_history_snapshot()` + docstring ref | Retire `stock_history.xlsx` |
| 6 *(cleanup)* | `_build_stock_summary.py`, `railway/railway_lineage.py`, `railway/__init__.py` | Delete builder; update lineage/doc strings | Remove dead references |

**Modules that need NO change** (already division-correct): `railway_demand_reconstruction` (DMTR glob), `railway_demand_classification`, `railway_forecast_generation`, `railway_lead_time_derivation`, `railway_pl_master`, `railway_safety_stock`, `railway_rop`, `railway_srrs_mas`, `division_summary`. They already consume `gcfg.DMTR_DIR` / `gcfg.SUMMARY_WORKBOOK` / `gcfg.HISTORY_DIR`.

---

## 6. Minimum Safe Implementation

**Phase 1 — Data-contract repair (division-agnostic; also fixes MAS):**
- Register all live divisions in `divisions.py`; glob the summary filename; fix MAS to 09-06.
- Add `gcfg.use_division()` (or reload switch).
- *Risk: low. Benefits MAS immediately (unbreaks the stale filename).*

**Phase 2 — Operational-source migration:**
- Repoint `load_operational_stock()` to per-division `SUMMARY OF STOCK HELD*.xlsx` (glob + concat) with corrected `col11`/`col12` indices.
- Delete `railway_stock_summary.xlsx`, `_build_stock_summary.py`, and `stock_history` references.
- *Risk: medium — validate STEP6 operational outputs and STEP18 partition row counts against a known-good baseline.*

**Phase 3 — Run TPJ:**
- Execute STEP21A→26 for `TPJ` → `outputs/TPJ/history/*`.
- Validate: TPJ DMTR depth ≈ MAS (TPJ has 54 DMTR files, 1356-row SUMMARY, ~1355 operational rows — the **largest** division).
- *Risk: low — pipeline reusable; data quality is the only variable.*

**Phase 4 — Enterprise integration (OPTIONAL, the real value-unlock):**
- Connect STEP20–28 division plans into the policy that STEP35 consumes, so `enterprise_allocation` stops pooling six identical strategic clones (MD5 `ffa1f1f45d`) and produces **genuine division differentiation** (divergent SRRS, capital exposure, allocation splits, procurement roadmap, board KPIs).
- *Risk: higher — touches the STEP35 input contract; do as a separate, reviewed step.*

> **Minimum SAFE onboarding = Phases 1 + 2 + 3.** Phase 4 is where TPJ stops being a clone and starts driving real enterprise optimization — recommend planning it as a distinct follow-on (STEP38).

---

## 7. Evidence Summary

- **Schemas (TPJ vs MAS):** identical across DMTR (12 cols), NS_DM_CONS (22 cols), SUMMARY OF STOCK HELD (13 cols). Only depot-code *values* differ (`077355`/`TPJ`/`GOC` vs `027534`/`PER`).
- **`railway_stock_summary.xlsx`:** consumed by `load_operational_stock` (mandatory, STEP6/STEP18) — NOT by strategic core or STEP35. Native SUMMARY differs by a +1 cost/value column shift.
- **`stock_history.xlsx`:** one optional, absence-tolerant package read; otherwise audit/build scripts only.
- **`NS_DM_CONS_REPORT`:** consumed only by audit scripts (`_step27_audit`, `_final_audit`); never by the package pipeline — OPTIONAL.
- **Enterprise clones:** all 6 `railway_inventory_policy.csv` byte-identical (MD5 `ffa1f1f45d`, 59 rows, 50 procurement-required).
- **Division parameterization:** STEP21A–26 read via `gcfg.DMTR_DIR`/`gcfg.SUMMARY_WORKBOOK`; the only missing piece is a registry entry + an activation switch.
- **Corroboration:** `_step28_audit.py` independently rated TPJ onboarding "Low effort (~1-2 wk), pipeline reusable, largest division (1355 ops) → high value."

---

*End of report. No files other than the three STEP37 deliverables (`legacy_dependency_audit.csv`, `step_data_contract_audit.csv`, `TPJ_GO_NO_GO_REPORT.md`) were created; no code, config, notebooks, or tests were modified.*
