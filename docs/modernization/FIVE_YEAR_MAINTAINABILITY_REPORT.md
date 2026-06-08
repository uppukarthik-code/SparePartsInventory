# Five-Year Maintainability Report

**Date:** 2026-06-08 · Scenario: a railway engineer inherits this repository in **2031**. Read-only. Evidence: `five_year_maintainability_audit.csv`, `repository_scorecard.csv`.

---

## 1. The 2031 onboarding test (could a new engineer maintain it?)
A new maintainer opening this repo cold would face:
- **84 `.md` reports + 17 cryptic `_step*` driver scripts** at the root — no obvious entry point, no README explaining the STEP21A→28 pipeline.
- **A flat 35-module package** mixing 26 legacy (zone/Walmart-era) and 9 new modules with no layering or naming convention to tell them apart.
- **No tests on the live pipeline** — changing `railway_safety_stock` / `rop` / `srrs` risks silent breakage with nothing to catch it.
- **No architecture/onboarding docs** — the *design rationale lives in 84 narrative reports*, not in code, docstrings, or a diagram.
- **Hardcoded constants and a hardcoded division (`027534`)** — extending to another division means hunting magic numbers across modules.
- **Manual orchestration** — the engineer must reverse-engineer the correct run order from driver scripts.

**Verdict: onboarding is HARD; hands-off maintenance by a new engineer is currently NOT viable.**

## 2. Maintainability scorecard (Part O — `repository_scorecard.csv`, ordinal 0–100)
| Dimension | Score | Dimension | Score |
|-----------|------:|-----------|------:|
| Architecture | 45 | Reusability | 50 |
| Maintainability | 45 | Documentation | 50 |
| **Testing** | **25** | Scalability | 45 |
| Configuration | 40 | Performance | 60 |
| Reliability | 55 | Production Readiness | 40 |
| | | **Overall (mean)** | **≈ 46/100** |
*(Scores are comparative auditor judgment, not a calibrated rubric — treat as bands: Testing = critical-low; Architecture/Config/Prod-readiness = low; Reliability/Performance = medium.)*

## 3. Top maintainability risks
1. **Zero tests on the new pipeline** — highest risk; any change can silently corrupt SS/ROP/SRRS.
2. **Knowledge concentration** — built step-wise by one author; design captured in reports, not in tests/docs/code structure.
3. **Leaky/flat architecture** — no layer boundaries; a small change ripples unpredictably.
4. **Hardcoded division + constants** — rollout/maintenance requires editing source.
5. **Manual orchestration + repo clutter** — no reproducible "run the pipeline" command.

## 4. What's genuinely good (preserve)
- **Determinism & backward compatibility** — byte-identical re-runs; 0 prior outputs ever changed across 28 steps.
- **Traceability** — every output traces to a source; provenance is thorough (if in the wrong medium).
- **Correct formula reuse** — no Walmart contamination; analytics reuse existing engine functions.

## 5. Five-year maintainability verdict
**Conditional.** The repository is **not maintainable hands-off by a new engineer today**, but the gap is **structural hygiene, not correctness** and is fully closable via the modernization roadmap (Phases 1–3 are decisive: cleanup → layered package + shared `ingestion` → test suite + README/architecture docs). After those, a railway engineer could confidently own it for 5 years.

## 6. Go / No-Go (long-term maintainability)
- ⛔ **NO-GO as-is** for unsupported 5-year maintenance.
- ✅ **GO after Phases 1–3** of the modernization roadmap (est. ~6–10 weeks): archive clutter + dead data, extract `ingestion/` shared-I/O layer (resolves the leaky dependency + 3 duplicate readers), centralize config, and add a risk-prioritized **test suite (SS/ROP/SRRS/lead-time/demand first) + README/architecture docs**.

**One-line recommendation:** keep the (audited, correct) analytics exactly as-is; invest the next 6–10 weeks in *structure, tests, and docs* — not formulas — to make it a 5-year-maintainable asset.
