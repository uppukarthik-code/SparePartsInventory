# STEP 29 — Executive Reporting Report

**Date:** 2026-06-08 · **Audit & planning only.** Evidence: `executive_kpi_framework.csv` (live values), `tpj_reporting_readiness.csv`, STEP20–28 outputs.

---

## 1. The 3-level KPI framework (computed live from current outputs)
`executive_kpi_framework.csv` — 23 KPIs across three levels, with **real current numbers** (read-only from STEP20–28 CSVs).

### Level 1 — Executive
| KPI | Value | Source |
|---|---|---|
| Forecast Coverage % | **88.7%** (961/1083) | forecast_results |
| Lead-Time Coverage % | **97.8%** (612/626) | lead_time_master |
| Current Stock Value | **Rs 913,635,687** | srss (stock×rate) |
| Reorder Gap Value | **Rs 3,367,367,459** | srss |
| Total SRRS | **8,217,896.6** | srss |
| Top-10 Risk Concentration | **84.5%** | srss |
| Tier 1 (Dual-Priority) | **6 PLs · 57.6% of SRRS · Rs 2.12B gap** | procurement_portfolio |
| Tier 2 (HighRisk-HighValue) | 80 PLs · 30.0% SRRS | procurement_portfolio |

### Level 2 — Operational
| KPI | Value |
|---|---|
| **Critical Shortages** | **465** (of 626 planned) |
| Shortages / Healthy / Excess | 45 / 43 / 60 |
| Open Procurement Exposure | Rs 3,367,367,459 |
| Service Levels | Critical(0.95): 360 · Non-Critical(0.85): 266 |

### Level 3 — Technical
| KPI | Value |
|---|---|
| Forecast Method Mix | SBA 654 · TSB 276 · Croston 26 · SES/Holt 5 |
| Demand Class Mix | Intermittent 654 · Lumpy 276 · Dead 122 · Erratic 26 · Smooth 5 |
| Criticality | Critical 360 · Non-Critical 266 |
| LT Source | PO_Date 518 · Requisition 184 |
| Test Coverage | 541 tests green (reproducible baseline) |
| Platform Readiness | scorecard mean 43.9 → 76.7 target; A/B done |

## 2. What the numbers say (executive narrative)
- **Risk is hyper-concentrated:** 6 PLs (Tier 1) drive 57.6% of all service risk; the top 10 drive 84.5%. Executive attention should focus there.
- **Large open exposure:** Rs 3.37B of reorder-gap against Rs 914M current stock — the division is materially under-stocked on planned items.
- **Operational urgency:** 465 of 626 planned PLs are in **Critical Shortage** — the single most important figure absent from today's reporting.
- **Sound analytics base:** 88.7% forecast / 97.8% LT coverage; method mix dominated by intermittent-demand methods (SBA/TSB), consistent with railway spares.

## 3. TPJ reporting readiness (`tpj_reporting_readiness.csv`)
When TPJ data arrives, executive reporting needs: per-division KPI rendering, a MAS-vs-TPJ comparison view, enterprise roll-up KPIs, a per-division scorecard, and a live TPJ-readiness gauge. All are **blocked only by TPJ data** (the framework + config are ready). Reporting is **structurally ready, data-blocked** — the same posture as the platform itself.

## 4. Verdict
**Executive reporting is currently inadequate but cheaply fixable.** The KPIs that matter (capital exposure, risk concentration, critical shortages) are computable *today* from existing outputs — proven above — they are simply not wired into the notebook or the summary. Standing up the L1/L2/L3 framework is reporting work, not analytics work. For TPJ: **ready by design, blocked by data.**
