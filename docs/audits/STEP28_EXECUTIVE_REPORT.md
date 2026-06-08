# STEP 28 — Executive Report: MAS Inventory-Planning System

**For:** Southern Railway S&T Stores management · **Date:** 2026-06-08
**Subject:** Deployment verdict, outcomes, and roadmap for the MAS division planning system and zone rollout.
*(All figures evidence-based and traceable to the STEP 21A–27 outputs; no fabricated savings.)*

---

## 1. What was built
A complete, **internally-sourced** division-level inventory-planning system for the **MAS (Chennai S&T, depot 027534)** division:

**Demand history → Forecast → Lead time → Current stock → Criticality → Safety stock → ROP → Reorder gap → SRRS prioritization → Capital-exposure lens.**

Built entirely from existing railway records (DMTR transaction registers, SUMMARY OF STOCK HELD, procurement reports) — **no external systems required**.

## 2. From STEP 20 to STEP 27 (the journey)

| | STEP 20 (start) | STEP 27 (now) |
|---|---|---|
| Planning level | Zone only (shared) | **Division-specific (MAS)** |
| Demand data | 5 annual points (zone) | **54 monthly points, 1,083 PLs** |
| Forecast / SS / ROP / SRRS | none at division | **626 PLs, 96% of forecast volume** |
| Readiness | ~48% | **deployable** |
| Maturity (avg, 0–5) | **0.5** | **3.5** (+3.0) |

## 3. Blockers discovered and resolved (all internally)

| Blocker | Resolution | Result |
|---------|-----------|--------|
| No multi-year per-division demand | Reconstructed 54 months from DMTR (STEP 21A) | demand 100% |
| Lead time 0% (no stored field) | Derived from PO/Reqn → Receipt dates (STEP 23.6B) | 96% of volume |
| Demand vs stock universe mismatch (027534 vs 027029) | Found the depot-027534 stock snapshot | stock 99.6% |
| Criticality 3% | Reconstructed binary Safety/Vital/NA (STEP 23.8) | 99.6% |

## 4. Key outcomes
- **626 PLs planned**, covering **96% of MAS forecast volume**.
- **Risk is extremely concentrated:** the **Top-10 PLs carry 84.5% of service risk**; Top-50 carry 97.8%. Management can address the overwhelming majority of risk by acting on tens of items.
- **6 dual-priority items + 86 Tier-1/2 items = 87.6% of service risk** — a focused, actionable worklist.
- **Two independent lenses:** service-risk (high-volume cables) and capital-exposure (₹3.37B reorder-gap value, led by expensive fire-alarm/EI systems).

## 5. Remaining limitations
1. Lead-time tail — 35% of PLs (only 4% of volume) lack a derived lead time.
2. Criticality is **binary** (Safety/Vital/NA); precise S1–S4 granularity pending an extended master.
3. **Issuing-depot context** — depot 027534 holds ~0 of fast-movers, so absolute shortage counts are inflated (relative ranking is valid; open POs should be netted).
4. **5 divisions data-blocked** — only `stock_history.xlsx` is available for SA/TPJ/MDU/PGT/TVC.

## 6. Maturity assessment (0–5)
| Dimension | Before | After |
|-----------|:-----:|:----:|
| Demand Planning | 1 | 4 |
| Forecasting | 1 | 4 |
| Lead Time | 0 | 3 |
| Inventory Visibility | 1 | 4 |
| Criticality | 1 | 3 |
| Safety Stock | 0 | 4 |
| ROP | 0 | 4 |
| Prioritization (SRRS) | 1 | 4 |
| Dashboard Readiness | 0 | 3 |
| Enterprise Rollout | 0 | 2 |
| **Average** | **0.5** | **3.5** |

## 7. Management action plan (act now)
| Tier | PLs | Action | Owner (illustrative) | Review |
|------|----:|--------|----------------------|--------|
| 1 Dual-priority | 6 | **Procure immediately**, net open POs | Sr.DMM / COS | Weekly |
| 2 High-Risk & High-Value | 80 | Procure next cycle | Depot Material Supt | Fortnightly |
| 3 High-Risk only | 70 | Service quick-wins (cheap critical cables) | Section Stores | Monthly |
| 4 High-Value only | 70 | Capital review (avoid over-buy) | Stores + Finance | Quarterly |
| 5 Routine | 400 | Min/max policy | Depot routine | Quarterly |

*(Owners illustrative — confirm against the actual divisional org.)*

## 8. Verdicts

- **Executive deployment verdict:** ✅ **The MAS planning system is operationally deployable.** It is complete, validated (STEP 27, Top-50 all operationally important), reproducible, and additive (every legacy output preserved). Recommend production use for MAS planning + procurement prioritization now.
- **Enterprise rollout verdict:** **Method-ready, data-blocked.** The pipeline is proven and reusable (~1–2 weeks/division); the only prerequisite is acquiring per-division **DMTR + SUMMARY OF STOCK HELD**.

## 9. Recommended Southern Railway roadmap (12 months)
| Horizon | Action |
|---------|--------|
| 0–1 mo | Deploy MAS to production; procure Tier 1–2 (net open POs); stand up the 7-view dashboard. |
| 1–3 mo | Acquire DMTR + SUMMARY for **TPJ** (largest), run STEP 21A→26; commission a full open-PO feed. |
| 3–6 mo | Onboard **TVC** + one more; extend the S1–S4 criticality master. |
| 6–12 mo | All 6 divisions live; **enterprise SRRS roll-up** (zone prioritization); integrate Net_Gap; quarterly cadence. |

## 10. Questions answered
1. **Achieved?** A full internal MAS planning stack, 96% volume, maturity 0.5→3.5.
2. **Problems solved?** Demand, lead time, stock-universe, criticality — all resolved internally.
3. **Unresolved?** LT tail (4% vol), S1–S4 granularity, 5 divisions' data, full PO netting.
4. **Immediate action?** Procure Tier 1–2; deploy dashboard.
5. **Items needing procurement?** The 6 dual-priority + 86 Tier-1/2 (87.6% of risk).
6. **Next divisions?** TPJ → TVC (data-availability first).
7. **Data still required?** Per-division DMTR + SUMMARY; full open-PO feed; S1–S4 criticality.
8. **12-month roadmap?** §9.
9. **Maturity improvement?** **0.5 → 3.5 (+3.0)**.
10. **Deployable?** ✅ **Yes — MAS is deployable now.**
