# STEP 27 — Operational Validation, PO-Netting Readiness & Rollout: Implementation Report

**Type:** Validation / operationalization / rollout planning. **No analytics, forecasting, lead-time, safety-stock, ROP, or SRRS logic modified. No existing output altered.**
**Date:** 2026-06-08 · **Scope:** MAS (+ rollout assessment for SA/TPJ/MDU/PGT/TVC).

---

## 1. Objective
Not a new model — **validate** the STEP 26 priorities, assess **PO-netting** readiness, segment a **procurement portfolio**, design a **management dashboard**, and assess **multi-division rollout**.

## 2. Method (read-only)
`_step27_audit.py` synthesizes existing outputs (STEP 21A–26) + NS_DM_CONS; writes 4 catalogue CSVs; SHA-256 guard (0 existing files changed).

## 3. Outputs (new, `outputs/MAS/history/`)
| File | Purpose |
|------|---------|
| `srrs_validation.csv` | Top-50 SRRS items cross-checked vs demand/forecast/LT/SS/stock/procurement + operational-importance verdict |
| `po_netting_feasibility.csv` | Net_Gap reconstruction method, coverage, reliability, gaps (no Net_Gap computed) |
| `procurement_portfolio.csv` | 5 mutually-exclusive tiers with counts, volume, ROP, gap, ₹, SRRS contribution |
| `division_rollout_readiness.csv` | per-division source availability, STEP21A feasibility, missing data, effort, coverage |

## 4. Part A — SRRS validation result
Top-50 SRRS items: **43 High + 7 Medium operational importance, 0 Low**. The top items (56501006, 56509959, 56501018, 561196180021, 509000396559) are consistently **Critical + high-forecast + high-gap** across every planning layer. Rankings are **stable and operationally sensible**; the only distortion is the documented issuing-depot inflation (relative ranking unaffected). Only 2 of the top-50 appear in NS_DM_CONS — expected, since SRRS is driven by routine high-volume cables, not the special-item indents NS tracks.

## 5. Part B — PO-netting readiness
`Net_Gap = ROP − Current_Stock − Open_PO_Qty` is **mechanically feasible** (all three components exist; `Open_PO_Qty = Item Qty − Qty Recd` from NS_DM_CONS). **But coverage is low:** NS_DM_CONS covers 29/626 SRRS PLs (4.6%); only **1** open-PO item overlaps the SRRS set. → **Feasible but low-impact today**; a fuller open-PO/indent feed (covering the cable universe) is the enabler. Net_Gap **not** computed (feasibility only).

## 6. Part C — Procurement portfolio (mutually exclusive)

| Tier | PLs | Forecast vol | Gap (units) | Gap value (₹) | SRRS % |
|------|----:|------------:|------------:|--------------:|-------:|
| 1 — Dual-priority | 6 | 366,789 | 236,837 | 2,116,822,425 | **57.6%** |
| 2 — High-Risk & High-Value | 80 | 226,809 | 173,745 | 751,479,733 | 30.0% |
| 3 — High-Risk only | 70 | 95,758 | 82,596 | 35,701,105 | 12.0% |
| 4 — High-Value only | 70 | 2,048 | 1,797 | 385,427,619 | 0.1% |
| 5 — Routine | 400 | 154,846 | 7,693 | 77,936,577 | 0.3% |

**Tier 1+2 (86 PLs) = 87.6% of service risk.** Tier 4 (₹385M, 0.1% SRRS) = expensive low-service-risk items → capital-protection lens, not service-driven.

## 7. Part E — Multi-division rollout
| Division | DMTR | Stock Summary | STEP21A | Missing |
|----------|:----:|:-------------:|---------|---------|
| MAS | Y | Y | Done (live) | — |
| SA / TPJ / MDU / PGT / TVC | N | N | **Blocked** | DMTR registers, SUMMARY OF STOCK HELD, NS_DM_CONS |

All five divisions hold only `stock_history.xlsx`; the demand/forecast pipeline cannot run without their DMTR registers. **Rollout is blocked on data acquisition, not method** — the pipeline is proven and reusable (~1–2 wk/division once data supplied; ~90–96% coverage expected).

## 8. Files
| Path | Action |
|------|--------|
| `railway/outputs/MAS/history/{srrs_validation,po_netting_feasibility,procurement_portfolio,division_rollout_readiness}.csv` | new |
| `_step27_audit.py` | one-off audit driver, retained |
| all existing outputs (525 files) | **untouched (SHA-256 verified)** |

See `STEP27_VALIDATION_REPORT.md` and `STEP27_OPERATIONALIZATION_REPORT.md`.
