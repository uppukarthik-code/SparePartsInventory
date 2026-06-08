# Phase C — TPJ Onboarding Readiness Report

**Date:** 2026-06-08 · **Assessment only — no code changed, no TPJ data processed.** Evidence: `tpj_onboarding_readiness.csv`, post-Phase-B state.

---

## 1. Question
Can TPJ (Tiruchirappalli Division) be onboarded to the STEP20–28 planning pipeline through **configuration only**?

## 2. Readiness by dimension (`tpj_onboarding_readiness.csv`)
| Classification | Count | Dimensions |
|---|---:|---|
| **READY** | 6 | division registry, planning constants, horizon, output routing, ingestion readers, core BU registry (TPJ already in `business_unit_config`) |
| **MINOR_CHANGES_REQUIRED** | 4 | division *selection* mechanism, STEP20–28 division-agnostic *execution*, DMTR/SUMMARY schema match, criticality Type tokens |
| **MAJOR_REFACTOR_REQUIRED** | 2 | **TPJ DMTR demand data**, **TPJ SUMMARY stock snapshot** — both *data acquisition*, not code |

## 3. What blocks TPJ
1. **DATA (the binding blocker).** TPJ DMTR registers and a TPJ SUMMARY OF STOCK HELD snapshot are **not present** in `raw_data/` (only `stock_history` exists for some divisions). No synthetic substitution is permitted. This is a procurement/data-acquisition task, **not** a code change. Until this is resolved, TPJ planning cannot run regardless of code readiness.
2. **Division selection.** The extension currently resolves a single `ACTIVE_DIVISION` (MAS) at import time. Running TPJ needs either flipping `ACTIVE_DIVISION` (a one-line config edit, fine for TPJ-only) or threading a `division=` parameter through `run()/build()` for concurrent multi-division — a small, mechanical refactor.
3. **Schema validation.** The MAS DMTR column indices and the SUMMARY `PL-Code/Type/Usage` token format are assumed; they must be verified against TPJ's actual files before trusting the parse.

## 4. Can STEP20–28 become division-agnostic?
**Largely already achieved in Phase B.** Every division-specific value (depot, raw subdir, SUMMARY filename, horizon, service levels, weights, thresholds, output dir, division label) now lives in the `DIVISIONS` registry and is read via `gcfg`. The remaining step to *full* agnosticism is parameterizing the division *selection* (currently a single resolved `ACTIVE_DIVISION`). So: **yes** — the analytics are no longer MAS-coupled; what remains is a selection mechanism + per-division data.

## 5. Which MAS assumptions remain?
- DMTR/SUMMARY **file schema** (column indices, Type tokens) — assumed identical across divisions.
- The single active-division resolution (one division per process).
- The srrs `0.85` fallback default (division-agnostic anyway).
- depot `027534` appears only in a function name/comment (cosmetic — not a filter).

## 6. Verdict & Go/No-Go
- **Code/config readiness:** **MINOR_CHANGES_REQUIRED** — the configuration surface is ready (Phase B); only a division-selection mechanism + schema verification remain.
- **Data readiness:** **MAJOR (blocked)** — TPJ DMTR + SUMMARY absent.
- **Overall TPJ onboarding: NO-GO today**, solely due to **missing TPJ data**. Once the data is acquired and schema-verified, onboarding is **config + a small selection parametrization** — *not* a rewrite. This is a decisive improvement over the pre-program state (fully MAS-hardcoded).

**Recommended onboarding path:** (1) acquire TPJ DMTR + SUMMARY; (2) add `DIVISIONS["TPJ"]`; (3) add `division=` selection (or flip `ACTIVE_DIVISION`); (4) verify schema on TPJ files; (5) run + pin a TPJ golden baseline.
