# STEP 23.6B — Internal Lead-Time Derivation & Planning-Universe Reconciliation: Implementation Report

**Type:** Additive data foundation. **No synthetic/default/industry lead times. No forecasting, SRRS, procurement, optimization, KPI or reporting logic modified.**
**Date:** 2026-06-08 · **Scope:** MAS.

---

## 1. Objectives
A. Derive a **real** per-PL planning lead time from internal DMTR procurement dates.
B. Quantify and reconcile the four planning universes (the STEP 23.5 mismatch).

## 2. Module added (additive)
`railway/railway_lead_time_derivation.py` (reuses the DMTR raw-XML reader). Writes two new files to `outputs/MAS/history/`; modifies nothing existing.

## 3. Lead-time derivation method (as approved)
- Sources, strict per-PL hierarchy: **Priority 1 `PO Date → Receipt`** (vendor procurement LT); **Priority 2 `Requisition Date → Receipt`** (internal fulfilment LT). A PL uses PO if it has any PO observation, else Reqn.
- Real DMTR dates only; **negative intervals rejected** (0 admitted).
- **Global per-source P5/P95 winsorization** before per-PL aggregation: PO bounds = (33, 668) days; Reqn bounds = (0, 618) days.
- **Median_LT = the planning lead time** (`Lead_Time_Days`).
- Confidence: High ≥20 obs · Medium 5–19 · Low <5.

### `lead_time_master.csv` (702 PLs)
Columns: PL_Code, Lead_Time_Days, Lead_Time_Source, Observations, Median_LT, P90_LT, Std_LT, Confidence.

| Aspect | Result |
|--------|--------|
| PLs with derived LT | **702** (64.8% of the 1,083 demand universe) |
| Source split | PO_Date 518 (median 131 d) · Requisition_Date 184 (median 81 d) |
| Confidence | High 20 · Medium 107 · Low 575 |
| LT distribution (days) | min 0 · p25 66 · **median 128** · p75 249 · p90 437 · max 668 · mean 184 |

## 4. Universe reconciliation
### `pl_universe_reconciliation.csv` (1,990 union PLs)
Columns: PL_Code, In_DMTR, In_Operational, In_Strategic, In_Criticality, Universe_Status.

| Universe | Size | ∩ DMTR |
|----------|-----:|-------:|
| DMTR demand | 1,083 | — |
| Operational stock | 907 | 20 |
| Strategic | 41 | 27 |
| Criticality | 59 | 32 |

| Universe_Status | PLs |
|-----------------|----:|
| Demand_Only | 1,031 |
| Inventory_Only | 880 |
| Partial_Match | 67 |
| Criticality_Only | 12 |
| **Fully_Reconciled** | **0** |

**Finding:** the four universes are **almost completely disjoint** — *zero* PLs appear in all four. The demand register (depot **027534**) and the operational stock snapshot (depot **027029**) share only **20** PLs. This is the structural root behind the sparse planning fields and is now the binding constraint for ROP/SRRS.

## 5. Coverage analysis

| Coverage | Value |
|----------|------:|
| PL coverage (LT) | 64.8% (702/1,083) |
| **Forecast-volume coverage** | **96.0%** (846,251 / 881,752) |
| Forecastability coverage | 65.1% (626/961) |
| ABC coverage (of covered) | 3.8% |
| Strategic-item coverage | 26/41 |

The covered 702 PLs carry **96% of forecast volume** — the high-volume items reliably have lead times; only the low-volume long tail (4% of volume) lacks them.

## 6. Headline outcome
**STEP 24 Safety Stock can be executed now for a meaningful subset** — 702 PLs covering 96% of MAS forecast volume — using derived LT + demand σ (already in place) + a default/criticality-tiered service level, **with no external system**. The remaining constraints (current-stock reconciliation, criticality linkage) gate STEP 25/26, not STEP 24.

## 7. Files
| Path | Action |
|------|--------|
| `railway/railway_lead_time_derivation.py` | new module |
| `railway/outputs/MAS/history/lead_time_master.csv` | new |
| `railway/outputs/MAS/history/pl_universe_reconciliation.csv` | new |
| `_step23_6b_run.py` | one-off validation driver, retained |
| all existing outputs (508 files) | **untouched (SHA-256 verified)** |

See `STEP23_6B_VALIDATION_REPORT.md` and `STEP23_6B_READINESS_REPORT.md`.
