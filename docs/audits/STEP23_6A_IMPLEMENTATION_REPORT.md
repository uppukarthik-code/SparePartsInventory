# STEP 23.6A — Implementation Report

**Type:** Investigative discovery (feasibility). **Additive; no synthetic lead times; nothing written into planning/forecasting/inventory outputs; no analytical logic modified.**
**Date:** 2026-06-08 · **Scope:** MAS.

---

## 1. Objective
Determine whether usable procurement **lead-time** information can be reconstructed from existing DMTR data — STEP 23.5 reported native lead-time coverage = 0%, but supplier/procurement coverage ≈ 79%.

## 2. Method (read-only mining)
A discovery driver (`_step23_6a_audit.py`) re-scans all 54 DMTR workbooks using the existing raw-OOXML reader (`railway_demand_reconstruction._sheet_rows`) and:
1. catalogues every procurement signal in receipt transactions (type, vendor, PO/Contract no+date, Reqn no+date, DBR no+date, Challan, receipt date/qty);
2. tests candidate **order-date → receipt-date** linkages, measuring PL coverage, chronological reliability (non-negative intervals) and interval distributions;
3. writes two catalogue CSVs. **No lead time is written to any planning output.**

## 3. Procurement-related fields found in DMTR
- **col2** transaction/receipt date (100%); **col3** transaction type; **col6** PL; **col8** detail — vendor name, `PO / Contract No. <id> dt. <date>`, `Reqn No. <id> dt. <date>`, `vide Challan No. <id> dt. <date>`; **col9** quantity; **col11** remarks — `DBR No. <id> … dt. <date>`.

## 4. Key result
Receipts carry a **second (order) date** that precedes the receipt date:
- **PO / Contract Date** (vendor, 42.4% of receipts) → **PO→Receipt** vendor procurement lead time.
- **Requisition Date** (internal, 34.8%) → **Reqn→Receipt** internal fulfilment lead time.
- **DBR date** (≈ receipt posting) and **Challan date** (dispatch/transit) are **not** full lead times.

| Path | PL coverage | Reliability | Median LT | Feasible |
|------|------------:|------------:|----------:|----------|
| PO→Receipt | 47.8% | 100% | 119 d | ✅ |
| Reqn→Receipt | 22.5% | 100% | 49 d | ✅ |
| **Combined** | **64.8% (702 PLs)** | 100% | — | ✅ |

Zero negative intervals on 2,821 paired observations → high chronological integrity.

## 5. Outputs (new, `outputs/MAS/history/`)

| File | Rows | Purpose |
|------|-----:|---------|
| `procurement_signal_inventory.csv` | 10 | per-signal coverage %, distinct count, suitability |
| `lead_time_feasibility.csv` | 6 | per-path coverage %, reliability %, Feasible flag, comments |

Plus reports: `STEP23_6A_LEAD_TIME_DISCOVERY_REPORT.md`, `STEP23_6A_VALIDATION_REPORT.md`, this file.

## 6. Decisions applied (agreed)
- **Feasible rule:** PL coverage ≥ 20% AND reliability ≥ 95% AND plausible distribution → PO Yes, Reqn Yes, Combined Yes; DBR/Challan/Demand No.
- **Next phase:** STEP 23.6B internal derivation for the 702 covered PLs (not deferred to external systems).

## 7. Outcome
Lead time is **reconstructable from internal DMTR data for ~65% of the demand universe** with 100% chronological reliability. STEP 24 can proceed for the covered subset on internal data; external systems remain needed only for the residual ~35% and for the separate criticality/current-stock gaps (STEP 23.5). Full evidence in the Discovery report.

## 8. Files
| Path | Action |
|------|--------|
| `railway/outputs/MAS/history/procurement_signal_inventory.csv` | new |
| `railway/outputs/MAS/history/lead_time_feasibility.csv` | new |
| `_step23_6a_audit.py` | one-off discovery driver, retained |
| all existing outputs (506 files) | **untouched (SHA-256 verified)** |
