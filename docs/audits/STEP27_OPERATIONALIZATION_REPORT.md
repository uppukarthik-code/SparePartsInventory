# STEP 27 — Operationalization Report (MAS)

**Date:** 2026-06-08 · **Type:** Validation verdicts, dashboard design, procurement portfolio, rollout strategy, 12-month roadmap. Design & planning only — no code, no model changes.

---

## 1. Operational validation verdict
**The SRRS priorities are operationally valid and stable.** Top-50 SRRS items are 43 High + 7 Medium operational importance (0 Low); the leaders are Critical, high-forecast, high-gap signalling cables/OFC that recur across every planning layer. **Six items dominate** (Tier 1, 57.6% of service risk): `56501006`, `56509959`, `56501018`, `561196180021`, `567912550075`, `569003030023`. Sole caveat: issuing-depot inflation (relative ranking unaffected).

## 2. PO-netting readiness verdict
**Feasible but low-impact today.** `Net_Gap = ROP − Current_Stock − Open_PO_Qty` is mechanically reconstructable (`Open_PO_Qty = Item Qty − Qty Recd` from NS_DM_CONS), but NS_DM_CONS covers only 29/626 SRRS PLs (1 open-PO overlap) — it tracks special/new-item indents, not the high-volume cables driving SRRS. **Recommendation: do not block procurement on netting; pursue a complete open-PO/indent feed for the cable universe as the enabler.**

## 3. Procurement portfolio design (act on Tiers 1–2 first)

| Tier | PLs | SRRS % | Gap value (₹) | Action |
|------|----:|-------:|--------------:|--------|
| **1 Dual-priority** | 6 | 57.6% | 2.12B | **Procure immediately** — top service risk *and* capital |
| **2 High-Risk & High-Value** | 80 | 30.0% | 751M | Procure next — material on both axes |
| 3 High-Risk only | 70 | 12.0% | 35.7M | Service-priority (cheap critical cables — quick wins) |
| 4 High-Value only | 70 | 0.1% | 385M | **Capital-protect** (expensive low-risk electronics; review, don't bulk-buy) |
| 5 Routine | 400 | 0.3% | 78M | Min/max policy |

**86 PLs (Tiers 1–2) = 87.6% of service risk** — management focus belongs here.

## 4. Management dashboard design (design only — no coding)

**Refresh:** monthly (aligned to the DMTR monthly cadence); stock/PO views weekly if a live feed is added. **Sources:** all `outputs/MAS/history/*.csv` (STEP 21A–27).

| # | View | KPIs | Charts | Tables | Source |
|---|------|------|--------|--------|--------|
| 1 | **Executive Summary** | PLs planned (626), forecast-vol coverage 96%, total reorder gap (502,668 u), capital exposure ₹3.37B, Critical-Shortage count (465) | gauge (coverage), donut (status), KPI tiles | top-line numbers | srss_summary, rop_summary |
| 2 | **Top Risk Items** | Top-10 SRRS share 84.5% | horizontal bar (SRRS by PL) | Top-20 SRRS w/ gap & criticality | srrs_results |
| 3 | **Top Value Exposure** | Top-10 value share 74.1% | Pareto (cum ₹) | Top-20 by Reorder_Gap_Value | srrs_results |
| 4 | **Critical Shortages** | 465 critical-shortage PLs, gap units | stacked bar (status × criticality) | Critical Shortage list, sortable | rop_results |
| 5 | **Excess Inventory** | 60 excess PLs, excess ₹ | bar (top excess) | Excess list (stock > 2×ROP) | rop_results |
| 6 | **Procurement Portfolio** | tier counts, SRRS%, ₹ per tier | quadrant scatter (SRRS × ₹), tier bars | tier worklist (Tier 1→5) | procurement_portfolio, srss_results |
| 7 | **Division Planning KPIs** | divisions live (1/6), coverage, readiness | rollout status board | division readiness | division_rollout_readiness |

**Quadrant scatter** (View 6) is the centrepiece: X = SRRS (service risk), Y = Reorder_Gap_Value (₹), four quadrants → procure-first / service / capital / routine.

## 5. Multi-division rollout strategy
- **MAS:** live (STEP 21A–26 complete, 96% volume).
- **SA / TPJ / MDU / PGT / TVC:** **method-ready, data-blocked.** Each needs (a) **DMTR monthly registers**, (b) **SUMMARY OF STOCK HELD** (its own depot), (c) **NS_DM_CONS** (optional, for procurement/lead-time corroboration). Today they hold only `stock_history.xlsx`.
- Once data is supplied, the pipeline is **fully reusable** (~1–2 weeks/division; ~90–96% coverage if DMTR depth matches MAS).
- **Sequencing recommendation (data-availability first, then business value):** prioritise whichever division supplies DMTR first; absent that, **TPJ** (largest operational universe, 1,355 items) and **TVC** (highest dead-stock ₹) offer the greatest early value.

## 6. Recommended 12-month roadmap

| Horizon | Action |
|---------|--------|
| **0–1 mo** | Act on **Tier 1 (6) + Tier 2 (80)** procurement (net open POs where NS_DM_CONS allows); stand up the management dashboard (View 1–6) on the existing CSVs. |
| **1–3 mo** | Acquire **DMTR + SUMMARY** for the **first rollout division** (TPJ or TVC); run STEP 21A→26; commission a **complete open-PO feed** to make Net_Gap reliable. |
| **3–6 mo** | Onboard **2 more divisions**; add View 7 division KPIs live; extend the **S1–S4 criticality master** (beyond binary) for finer SRRS weighting. |
| **6–12 mo** | **All 6 divisions live**; build the **enterprise SRRS roll-up** (zone-level prioritisation, reusing STEP 26 per division); quarterly planning cadence; integrate Net_Gap into procurement once the PO feed covers the cable universe. |

## 7. Closeout — questions answered
1. **Do SRRS rankings make operational sense?** ✅ Yes — Top-50 all High/Medium importance; leaders consistent across all layers.
2. **Which items consistently dominate risk?** The 6 Tier-1 PLs (PVC cables, OFC, fire-alarm) — 57.6% of SRRS.
3. **Can Open-PO netting be implemented?** Mechanically yes; **low impact now** (29/626 coverage) — needs a fuller PO feed.
4. **What portfolio should management focus on?** **Tiers 1–2 (86 PLs = 87.6% of service risk)**; treat Tier 4 as capital-protection.
5. **What should the dashboard look like?** 7 views (§4), monthly refresh, centred on the SRRS × ₹ quadrant.
6. **Which division next?** Whichever supplies DMTR first; by value, **TPJ** then **TVC**.
7. **Effort to extend STEP 21A→26?** ~1–2 weeks/division once DMTR + SUMMARY are provided (pipeline reusable).
8. **Roadmap after MAS?** §6 — act on MAS priorities + dashboard now; data-acquire and onboard divisions over 3–12 months; enterprise roll-up by month 12.

*Validation, operationalization and rollout planning only. No forecasting, lead-time, safety-stock, ROP, SRRS, or enterprise output was modified.*
