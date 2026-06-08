# FINAL SYSTEM AUDIT — Hardening Report

**Date:** 2026-06-08 · RAG findings, mandatory actions, hardened architecture. (Post self-critique recalibration.)

---

## 1. Findings register (RAG) — 1 RED · 12 AMBER · 5 GREEN · 5 audit-limitations
Full detail + evidence/impact/likelihood/recommendation in `hardening_findings.csv`.

### 🔴 RED (address before any procurement *action*)
- **F03 — ROP over-procurement signal / unconfirmed depot role.** 465/626 PLs flag Critical Shortage at depot 027534; the cause (issuing-depot artifact vs genuine under-stock) is an **audit assumption, not confirmed from data**. Acting literally risks over-procurement. **Action:** confirm depot operating model + net open POs; keep advisory-only until then.

### 🟠 AMBER (address before automation / enterprise scale)
F01 SS normal-approx on intermittent demand (magnitude unquantified) · F02 SRRS gap-dominated (labeling) · F04 sMAPE metric (MASE preferred; not recomputed) · F05 enterprise rollout data-blocked (5/6 divisions) · F06 criticality stores-proxy, n=32 indicative · F07 PO/Reqn lead-time semantics mixed · F08 config drift / dead config · F09 no test suite / driver-script orchestration · F10 fragile parsing + silent failures + empty-median edge · F11 Closing_Stock derived/weakly reconciled · F12 35% PL coverage tail · F13 SRRS can't prioritise excess.

### 🟢 GREEN (validated — maintain)
F14 formulas dimensionally correct (recompute ±0.005) · F15 strict backward compatibility (0 prior outputs changed) · F16 SBC cutoffs + method assignment match Syntetos–Boylan 2005 · F17 no synthetic demand/LT/criticality/stock/savings + honest coverage flagging · F18 funnel consistent, dependency-integral, reproducible.

### ⚪ Audit limitations (SC1–SC5)
SS error not empirically measured · MASE not recomputed · depot role assumed · scores ordinal not rubric · criticality n=32 small.

## 2. Mandatory actions before deployment

**Gate 1 — before any procurement action (pilot):**
1. **Confirm depot-027534 operating model** (issuing vs consignee) with stores; reinterpret the 465 shortages accordingly. (F03)
2. **Net open POs** into the reorder gap (acquire fuller open-PO feed; NS_DM_CONS covers only 29/626). (F03)
3. **Advisory-only governance** — human sign-off on every procurement decision; system outputs are decision-support, not auto-orders.

**Gate 2 — before automated/unsupervised procurement:**
4. **Intermittent-aware safety stock** (bootstrap / Croston-variance / distributional) for the intermittent/lumpy majority; empirically compare to current normal-approx. (F01)
5. **MASE** as primary accuracy metric; recompute the Forecastability "accuracy" term. (F04)
6. **Automated test suite + config centralisation + pipeline runner**; remove fragile-parse/silent-failure modes. (F08–F10)

**Gate 3 — before enterprise rollout:**
7. **Per-division DMTR + SUMMARY** acquisition (TPJ→TVC→…). (F05)
8. **Engineer-led VED/criticality** for top items; expand validation beyond n=32. (F06)

## 3. Final hardened architecture (see `final_architecture.csv`)
```
RAW (mandatory: DMTR monthly txns, SUMMARY OF STOCK HELD; optional: NS_DM_CONS;
     future-mandatory: engineer VED master)
  → PROCESSING (demand reconstruction → SBC classification → lead-time derivation → PL master)
  → PLANNING (forecast [+MASE] → safety stock [intermittent-aware for full prod] → ROP + Net_Gap [net open POs])
  → PRIORITIZATION (SRRS risk-weighted gap + independent ₹-exposure lens)
  → PROCUREMENT (tiered portfolio + dashboard [build])
  + ENHANCEMENT: S1–S4 criticality, seasonality, bootstrap SS, enterprise rollout, test suite
```
**Mandatory inputs:** DMTR, SUMMARY. **Optional:** NS_DM_CONS. **Future-mandatory:** engineer-assessed criticality, full open-PO feed.

## 4. Hardening posture
The system is **structurally sound and additive** (every legacy output preserved, formulas correct, literature-aligned classification). The residual risk is concentrated in (a) **one operational gate** (F03 depot/over-procurement) that blocks procurement *action* until resolved, and (b) **method-maturity AMBERs** (SS for intermittent, MASE, tests) that block *automation/scale* but not a supervised advisory pilot.
