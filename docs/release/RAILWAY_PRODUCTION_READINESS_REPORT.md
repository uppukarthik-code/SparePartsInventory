# Railway Inventory Analytics Platform — Production Readiness Report

**Phase:** Step 9 — Platform Hardening & Validation
**Date:** 2026-06-07
**Scope:** QA only — no new business functionality, no existing outputs modified.

---

## Hardening delivered in this phase

| Part | Artifact | Result |
|---|---|---|
| 1 Test framework | `railway/tests/` — 8 pytest files | **53 tests, all passing (2.8 s)** |
| 2 Schema validation | `railway/schema_validation.py` (fail-fast) | **ALL CHECKS PASSED** |
| 3 Data lineage | `railway/railway_lineage.py` → `data_lineage_report.csv` | **44 outputs tracked** (Strategic 19 · Operational 13 · Derived 12) |
| 4 Regression baseline | `railway/railway_regression.py` → `railway_regression_baseline.json` | baseline saved; **compare = no drift** |
| 5 Performance | `railway/performance_test.py` | 1k/5k/10k SKUs; **O(n) linear (1.02×)** |
| 6 Config centralization | constants → `railway_config.py` | blend weights, budgets, DQ thresholds, demand defaults, vocabularies centralized; pipeline re-run **behaviour-identical** |
| 7 Scorecard | this report | Overall **78/100** |

### Performance (synthetic SKUs, core per-SKU transforms)
| SKUs | Seconds | Peak MB | ms/SKU |
|---:|---:|---:|---:|
| 1,000 | 0.72 | 0.42 | 0.72 |
| 5,000 | 3.71 | 2.08 | 0.74 |
| 10,000 | 7.30 | 4.16 | 0.73 |

Per-SKU cost is **flat (1.02× drift 10k vs 1k)** → genuinely linear. Memory negligible. Dominant cost is per-row Python iteration (`iterrows` + statsmodels Holt); vectorising would cut wall-clock ~5–10× but is **not** required at current/near-term scale.

---

## Architecture Scorecard

| Dimension | Score /100 | Justification (evidence-based) |
|---|---:|---|
| **Code Quality** | 82 | 9 modules, ~2,000 LOC, single-responsibility, documented, reuse-provenance commented. Constants now centralized (Part 6). Minor: a few module-local helpers remain. |
| **Test Coverage** | 76 | 53 unit+integration tests across all 8 modules' pure logic + output schemas. Covers ABC/criticality/coverage, blend/CAGR/intermittent, lead-time tiers, aging (incl. the NaN bug), rationalization matrix, Power BI & AnyLogistix schemas. Gap: no line-coverage metric, limited end-to-end/property tests. |
| **Data Quality** | 80 | Fail-fast schema validation passes; dedicated DQ normalization layer (unit-mismatch) with full audit trail; lineage report; regression guard. Residual *documented* items: locked SS dimensional note, `inf` forecast-to-stock sentinel, single DQ rule. |
| **Scalability** | 76 | Measured linear O(n) to 10k; streaming strategic loader. Known hotspot: `iterrows` in 3 modules + per-SKU Holt → super-linear only beyond ~100k. No redesign needed for depot/division scale. |
| **Maintainability** | 85 | Strong domain separation (strategic vs operational, originals vs normalized), config single-source-of-truth, idempotent `run()` per module with built-in gates, regression baseline to catch drift. |
| **Deployment Readiness** | 70 | Depot-level functional end-to-end; division-partial (demand allocation = Equal_Split); zonal not-yet. Digital-twin readiness 75% (Near Ready) — blocked only by external data (geo-coords, division demand). |

### Overall Score: **78 / 100**  →  Production-ready for **depot decision-support with controls**.

---

## FINAL QUESTION
**"Can this platform be safely used by a Southern Railway S&T depot for decision support?"**

## ✅ YES — WITH CONTROLS

**Why YES:** The platform runs end-to-end on real Southern Railway data, every stage has a passing validation gate, 53 automated tests pass, schema validation and a regression baseline guard against drift, and full source lineage is preserved (strategic and operational pipelines never silently merged). The outputs answer the real management questions (what to buy/retain/review/rationalize/dispose, how much capital, what ₹1 cr buys) and feed Power BI and AnyLogistix as visualization-only layers.

**Mandatory controls before acting on outputs:**
1. **Treat Safety_Stock / ROP / investment magnitudes as relative rankings, not absolute quantities.** The locked `SS = Z × annual_σ × √months` formula is dimensionally conservative and overstates buffers; use it to *prioritise*, and convert to absolute order quantities with a period-consistent recalculation before raising indents.
2. **Stores must confirm the 2 unit-mismatch normalizations** (per-km cable rates) before any value/disposal decision; the audit trail (`railway_data_quality.csv`) makes this a one-look review.
3. **ABC, demand class and forecasts are directional** — derived from only 5 annual observations (2021-22 missing). Use for planning emphasis, not contractual commitments; refresh when monthly issue data becomes available.
4. **Procurement, rationalization and disposal lists require human sign-off.** The platform recommends; the depot officer decides. The 190 disposal candidates and 327 rationalization items are *review lists*, not auto-actions.
5. **Network/AnyLogistix modeling is gated** on supplying real geo-coordinates and division-level demand (currently Placeholder / Equal_Split — never fabricated).

**Why not unconditional YES:** the residual items above are data-supply and formula-convention matters, not defects in the pipeline. **Why not NO:** every gate passes, the logic is tested and traceable, and the known limitations are explicitly flagged in the outputs themselves rather than hidden.

---

### Bottom line
A correct, tested, auditable depot-level decision-support platform. Safe to use for **prioritisation and review** today; safe for **absolute procurement quantities and network optimization** once the five controls/data-gaps are closed — all of which are known, localised, and fixable without redesign.
