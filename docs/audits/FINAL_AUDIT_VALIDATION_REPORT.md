# FINAL SYSTEM AUDIT — Validation Report

**Date:** 2026-06-08 · Independent re-verification + literature validation + self-critique. Read-only.

---

## 1. Numeric re-verification (recomputed from source CSVs)

| Check | Result | Verdict |
|-------|--------|---------|
| Pipeline funnel | demand 1083 → forecast 961 → lead-time 702 → SS 626 → ROP 626 → SRRS 626; all PL-unique; SS⊂forecast, ROP=SS set, SRRS=ROP set | ✅ consistent |
| Forecast profile | 100% flat (annual = 12×monthly), Seasonality_Modeled=No | ✅ as designed (caveat C) |
| Safety stock | recompute `z·σ·√(LT/30.4375)` vs stored: **max abs err 0.005**; z = norm.ppf(SL) ✓; no negative SS | ✅ arithmetic correct |
| ROP | recompute `Forecast_Annual·LT_days/365.25 + SS` vs stored: **max abs err 0.005**; no negative ROP; SS reused verbatim from STEP24 (diff 0) | ✅ arithmetic correct |
| SRRS objective | effective weights back-out = {1,5,10}=NA/Vital/Safety ✓; = weight×SF×Positive_Gap | ✅ reused verbatim |
| Backward compatibility | every STEP20–28 step + this audit: SHA-256, **0 prior outputs changed** | ✅ strictly additive |

## 2. SRRS sensitivity & dominance (Part H — recomputed)
- **Spearman(SRRS, Positive_Gap) = 0.884** → SRRS rank is ~78% explained by the gap (volume×under-stock); criticality/service-factor reorder ~22%.
- Top-10 SRRS vs Top-10-by-gap-alone overlap = **8/10**; Top-20 = 14/20.
- **±20% perturbation:** weight-ratio −20% → Top-10 stability **1.00**, Top-20 0.95; service-factor −20% → Top-10/20 **1.00**, Spearman 0.9995.
- **Conclusion:** SRRS is **gap-dominated with a secondary criticality tilt**; rankings are robust to weight/SF error. (Calibrated down from a draft "volume-dominated" overstatement — the math is correct; this is an interpretation/labeling finding, AMBER.)

## 3. Literature validation (focused, citation-backed)

| Theory | Implementation | Literature | Verdict |
|--------|----------------|-----------|---------|
| SBC cutoffs ADI 1.32 / CV² 0.49 | `_sbc_class` exact | Syntetos–Boylan 2005 | ✅ **match** |
| Method assignment | Erratic→Croston, Intermittent→SBA (Smooth→SES, Lumpy→TSB) | SB2005: Croston for erratic, SBA otherwise; TSB (2011) for lumpy/obsolescence | ✅ **aligned** (TSB-for-lumpy = valid post-2005 extension) |
| Safety stock for intermittent | `z·σ·√LT` normal-approx, σ=monthly std incl zeros | Syntetos/Babai: normal-approx **limited** for intermittent; bootstrap/Croston-variance preferred | ⚠ **deviation (AMBER)** — magnitude not quantified here |
| Forecast accuracy metric | sMAPE/MAPE (non-zero) | Hyndman: sMAPE **minimized by zero-forecast** for intermittent; **MASE** recommended | ⚠ **deviation (AMBER)** — MASE not recomputed here |
| Criticality | binary stores "Safety Item" proxy | VED = consequence-based, engineer-assessed (V/E/D) | ⚠ **proxy, not RAMS/VED (AMBER)**; binary collapses tiers |

Sources: Syntetos, Boylan & Croston (2005) *On the categorization of demand patterns*; Croston (1972); Teunter, Syntetos & Babai (2011) TSB; Syntetos & Babai et al. (parametric vs bootstrapping for intermittent SS); Hyndman (*Another look at forecast-accuracy metrics for intermittent demand*); VED spare-parts criticality practice.

## 4. Per-part findings (detail in the 13 audit CSVs)
- **B Data foundation:** demand conserved, 0 nulls; **Closing_Stock derived/weakly reconciled** (AMBER); near-disjoint universes resolved for stock via SUMMARY 027534.
- **C Forecast:** SBC-aligned & reproducible; **flat profile** + **sMAPE metric** AMBER.
- **D Lead time:** 0 negative intervals, winsorized; **PO/Reqn semantics mixed** + 35% tail AMBER.
- **E Criticality (red-team):** "Safety Item" is a stores tag, validated **indicative-only (n=32, precision 0.74)**; binary; not RAMS — AMBER.
- **F Safety stock:** arithmetic correct; **normal-approx inappropriate for intermittent majority** — AMBER (RED for automation).
- **G ROP:** correct mechanics; **issuing-depot over-procurement signal, depot role UNCONFIRMED** — RED; no PO netting.
- **H SRRS:** correct & rank-stable; **gap-dominated** — AMBER.
- **I Value:** unit-rate 100%, internally consistent, **complementary** to SRRS (Spearman 0.746, top-20 overlap 6) — GREEN with outlier caveat.
- **J Operational:** pilot-ready, dashboard designed-not-built, rollout data-blocked.
- **K Consistency:** ✅ all consistent.
- **L Software:** modular/reproducible/backward-compatible; **no tests, hardcoded config, fragile parsing** — AMBER.

## 5. Self-critique outcome (academic-paper-reviewer pass)
The draft audit **over-rated** F01/F02/F04 as RED on literature/interpretation grounds without empirical recomputation; these were downgraded to **AMBER** with explicit "magnitude unquantified" caveats. The **depot-role assumption** behind F03 was surfaced (cause unconfirmed). The **n=32 criticality** double-standard was corrected (indicative-only throughout). Readiness scores re-labeled **ordinal judgment, not a rubric**. Net: **1 RED, 12 AMBER, 5 GREEN, 5 disclosed audit-limitations** — a calibrated, evidence-bounded position.

## 6. Verdict
The pipeline is **mathematically correct, statistically reproducible, and broadly inventory-theory-aligned on classification/forecasting**, with **legitimate, literature-backed methodological limitations** (SS for intermittent, accuracy metric) and **one gating operational risk** (ROP over-procurement signal with unconfirmed depot role). Detailed Go/No-Go and actions in the Hardening and Executive reports.
