# FINAL SYSTEM AUDIT (STEP20→28) — Executive Report

**Independent adversarial audit · MAS railway inventory-planning pipeline · 2026-06-08**
*Read-only; no analytics/outputs modified. Verdicts post academic-paper-reviewer self-critique. Scores are ordinal auditor judgment, not a calibrated rubric.*

---

## 1. Executive audit verdict
The STEP20→28 MAS pipeline is **mathematically correct, statistically reproducible, internally consistent, and broadly inventory-theory-aligned** on demand classification and forecast-method selection. It was built **entirely from internal data**, is **strictly additive** (every prior output byte-for-byte unchanged across 28 steps), and contains **no synthetic demand, lead times, criticality, stock, or savings**.

It carries **legitimate, literature-backed methodological limitations** — safety stock uses a normal approximation the literature flags for intermittent demand (86% of items); forecast accuracy uses sMAPE rather than the recommended MASE — and **one gating operational risk**: the ROP/SRRS shortage signal (465/626 "Critical Shortage") rests on an **unconfirmed assumption** about depot-027534's role and is **not netted against open POs**.

## 2. Production deployment verdict
**Conditionally deployable as a supervised, advisory decision-support tool for the MAS division. Not ready for automated/unsupervised procurement, and not ready for enterprise rollout.**

## 3. GO / NO-GO
- ✅ **CONDITIONAL GO** — supervised **advisory** pilot at MAS (ranking + visibility; **human sign-off on every order; no auto-procurement**), **after** Gate-1 actions (confirm depot role, net open POs).
- ⛔ **NO-GO** — automated/unsupervised procurement (until Gate-2: intermittent-aware SS, MASE, tests).
- ⛔ **NO-GO** — enterprise/zone rollout (until Gate-3: per-division data, engineer VED).

## 4. Top 10 risks
1. **F03** ROP over-procurement signal; depot-027534 role unconfirmed; open POs not netted *(RED)*.
2. **F01** Safety stock normal-approx on intermittent/lumpy majority — possible systematic bias *(AMBER; magnitude unquantified)*.
3. **F04** Forecastability/accuracy uses sMAPE (unsuitable for intermittent; MASE preferred).
4. **F06** Criticality is a binary stores-proxy validated on only n=32 PLs — not RAMS/VED.
5. **F05** Enterprise rollout blocked — only 1 of 6 divisions has source data.
6. **F07** Lead time blends vendor (PO) and internal (Reqn) semantics.
7. **F02** SRRS is gap/volume-dominated (Spearman 0.884); "service-risk" label overstates criticality's role.
8. **F09** No automated tests; one-off-driver orchestration → regression risk at scale.
9. **F10** Fragile regex parsing + silent failures + latent empty-median crash.
10. **F08/F11/F12** Config drift; derived Closing_Stock; 35%-PL (4%-vol) coverage tail.

## 5. Top 10 strengths
1. Formulas (SS, ROP, SRRS) **dimensionally correct**, recompute to ±0.005.
2. **Strict backward compatibility** — 0 prior outputs changed across all 28 steps (SHA-256).
3. Classification cutoffs + method assignment **match Syntetos–Boylan 2005**.
4. **No fabrication** — no synthetic demand/LT/criticality/stock/savings; honest coverage flagging.
5. Pipeline **funnel consistent & dependency-integral** (1083→626), fully reproducible.
6. **Complete internal data foundation** — demand, forecast, LT, stock, criticality all recovered from existing records.
7. **SRRS objective reused verbatim**; rankings **stable to ±20%** weight/SF perturbation.
8. **Value-exposure lens kept independent** of the cost-free SRRS (correct design; complementary, not duplicative).
9. **Lead-time chronology clean** — 0 negative intervals, winsorized.
10. **Modular, traceable, additive** engineering; every output traces to source.

## 6. Final readiness (0–100, ordinal auditor judgment — see `production_readiness_assessment.csv`)
Data Foundation 78 · Forecasting 65 · Lead Time 70 · Criticality 58 · Safety Stock 55 · ROP 62 · SRRS 60 · Value Exposure 72 · Operationalization 55 · Governance 50 · Software Engineering 55 → **≈ 62/100 overall** (band: **Medium** — pilot-ready, not production-hardened). *Scores are comparative judgments, not measured; treat as Low/Medium/High bands.*

## 7. Final hardened architecture
`RAW (DMTR + SUMMARY mandatory; NS_DM_CONS optional; engineer-VED future) → PROCESSING (reconstruct → classify → lead-time → PL master) → PLANNING (forecast +MASE → intermittent-aware SS → ROP + Net_Gap) → PRIORITIZATION (SRRS + ₹-exposure) → PROCUREMENT (portfolio + dashboard)` — full table in `final_architecture.csv`.

## 8. Mandatory actions before deployment
**Gate 1 (before procurement action):** confirm depot-027534 role; net open POs; advisory-only with human sign-off.
**Gate 2 (before automation):** intermittent-aware safety stock; MASE metric; automated tests + config centralisation.
**Gate 3 (before rollout):** per-division DMTR+SUMMARY; engineer-led VED criticality (expand n=32 validation).

## 9. Answers to the 14 questions
1. **Mathematically correct?** Yes — formulas recompute to ±0.005, no negatives, units consistent.
2. **Forecasting sound?** Method selection literature-aligned & reproducible; **but the accuracy metric (sMAPE) is unsuitable for intermittent — use MASE.**
3. **Lead-time defensible?** Yes for PO-sourced (chronology-clean, winsorized); **PO/Reqn semantics are mixed** (AMBER).
4. **Criticality valid?** A reasonable proxy (recall 0.95) but **a stores tag, not RAMS/VED, validated on n=32** — AMBER.
5. **Safety stock correct?** Arithmetically yes; **methodologically a normal-approx inappropriate for the intermittent majority** — AMBER (RED for automation).
6. **ROP correct?** Mechanics yes; **issuing-depot over-procurement distortion + no PO netting** — RED.
7. **SRRS prioritising risk or volume?** **Predominantly gap/volume (Spearman 0.884)**, criticality a ~22% modulator — AMBER (relabel).
8. **Weakest assumptions?** Depot-027534 role; normal-demand SS; "Safety Item"=criticality; 54-mo DMTR represents future; flat forecast.
9. **Must fix before production?** Gate-1+2+3 actions (§8).
10. **Top 10 risks?** §4.
11. **Top 10 strengths?** §5.
12. **Final readiness score?** ≈ **62/100 (Medium)** — ordinal.
13. **Final hardened architecture?** §7 / `final_architecture.csv`.
14. **Approve production deployment?** **Conditional GO for a supervised advisory MAS pilot; NO-GO for automated procurement or enterprise rollout** until the gated actions are complete. Approval is **earned for a pilot, withheld for full production.**

---
*Deliverables: 4 reports + 15 CSVs. Read-only; backward compatibility SHA-256-verified (0 prior outputs changed). Findings classified on merit (no credit for prior disclosure). Audit self-limitations disclosed (SC1–SC5).*
