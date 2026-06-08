# STEP 28 — Business Case Report

**Date:** 2026-06-08 · **Scope:** MAS (deployed) + Southern Railway rollout.
**Discipline:** evidence-only. **No fabricated savings, no invented financial figures.** Monetary figures shown are *exposure/visibility* metrics from source data, not claimed savings.

---

## 1. The problem (STEP 20 baseline)
Southern Railway S&T inventory planning was **zone-level only**: a single shared 59-item strategic model, 5 annual demand points, no division-specific forecasting/safety-stock/ROP/SRRS, and an enterprise aggregation that inflated strategic totals. Division managers had **no item-level, division-specific planning signal**. Readiness ≈ 48%.

## 2. What was delivered (evidence)
A complete MAS division planning system, internally sourced:

| Capability | Evidence (traceable) |
|------------|----------------------|
| Monthly demand history | 54 months, 1,083 PLs (STEP 21A) |
| Forecasts | 961 PLs, method-assigned (STEP 22–23) |
| Lead times | 702 PLs / 96% volume, derived from PO/Reqn→Receipt (STEP 23.6B) |
| Current stock | 99.6% (depot-027534 SUMMARY) |
| Criticality | 99.6% binary (STEP 23.8) |
| Safety stock / ROP / SRRS | 626 PLs / 96% volume (STEP 24–26) |
| Prioritization & portfolio | 5-tier worklist, validated (STEP 26–27) |

## 3. Benefits realization (qualitative — no synthetic savings)

| Benefit | Type | Evidence |
|---------|------|----------|
| **Planning visibility** | Quantified | division planning coverage **0% → 96%** of MAS forecast volume |
| **Procurement prioritization** | Quantified | 6 dual-priority + 86 Tier-1/2 PLs = **87.6% of service risk** in a focused worklist |
| **Risk reduction** | Quantified | **Top-10 PLs = 84.5%** of service risk now explicit and actionable |
| **Shortage reduction** | Qualitative-High | **465 critical shortages** now visible & ranked (previously invisible at division level) |
| **Inventory optimization** | Qualitative-High | 626 PLs with SS+ROP; **60 excess items** + Tier-4 (₹385M) flagged for capital review |
| **Management reporting** | Qualitative | 7-view dashboard designed on existing CSVs (no analytics rebuild) |
| **Capital-exposure transparency** | Evidence | reorder-gap exposure **₹3.37B**, depot stock **₹290M** made visible *(exposure, not a savings claim)* |

**No rupee savings are claimed.** The value is **decision quality and visibility**: management can now target the ~10–86 items that carry the great majority of service risk and capital exposure, instead of a flat 626/1,083-item catalogue.

## 4. Risk-concentration evidence (why focus pays off)

| Metric | Total | Top-10 | Top-20 | Top-50 |
|--------|------:|-------:|-------:|-------:|
| Service risk (SRRS) | 8,217,897 | **84.5%** | 94.6% | 97.8% |
| Reorder gap (units) | 502,668 | 71.7% | 86.8% | 95.6% |
| Reorder-gap value (₹) | 3,367,367,459 | **74.1%** | 79.6% | 88.4% |

**Interpretation:** MAS inventory risk and capital exposure are **highly concentrated** — a small managed worklist (tens of PLs out of 626) governs the majority of both. This is the core of the business case: **focused action on a tiny fraction of items addresses most of the risk.**

## 5. Cost-to-extend (effort, not money)
- MAS: complete (sunk).
- Each further division: **~1–2 weeks** of analyst effort *once* its **DMTR + SUMMARY OF STOCK HELD** are supplied — the pipeline is fully reusable. No new model development.
- Enablers: per-division data acquisition; (optional) full open-PO feed for Net_Gap; extended S1–S4 criticality master.

## 6. Enterprise rollout business case

| Division | Sequence | Expected coverage | Effort | Value rationale |
|----------|:--------:|------------------:|--------|-----------------|
| TPJ | 1 | ~90–96% | Low | largest operational universe (1,355) |
| TVC | 2 | ~90–96% | Low | highest dead-stock value (rationalization upside) |
| SA / MDU / PGT | 3–5 | ~90–96% | Low | complete the zone |

All blocked only on data acquisition (DMTR + SUMMARY), not on capability.

## 7. Verdicts
- **Business-case verdict:** ✅ **Justified.** The system converts a zero-visibility, zone-only baseline into a validated, division-specific, risk-prioritized planning capability covering 96% of MAS forecast volume — built entirely from existing data at low marginal cost. Value is in decision quality and risk concentration (Top-10 = 84.5% of risk), evidenced, not financially fabricated.
- **Enterprise rollout verdict:** ✅ **Recommended**, sequenced TPJ → TVC → SA/MDU/PGT, contingent on per-division DMTR + SUMMARY acquisition.
- **Final maturity:** **0.5 → 3.5 (avg, 0–5 scale)** — every capability dimension improved; MAS planning is **operationally deployable now**.

## 8. Recommended next step
Approve **production deployment of MAS planning**, action the **Tier-1/2 procurement worklist** (netting open POs), commission the **dashboard** and the **per-division data acquisition** (start TPJ) — the single highest-leverage move to extend a proven, internally-built capability across Southern Railway.

*Reporting and planning only. No forecasting, safety-stock, ROP, SRRS, or enterprise output was modified; no savings were fabricated.*
