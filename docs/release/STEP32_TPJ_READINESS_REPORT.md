# STEP 32 — TPJ Readiness Report (Purification View)

**Date:** 2026-06-08 · Audit only. Evidence: `tpj_onboarding_readiness.csv`, governance/config registry, STEP31 reporting cut-over.

---

## 1. Question
Can TPJ (Tiruchirappalli) be onboarded **without architectural changes**?

## 2. Readiness by dimension
| Dimension | Status | Evidence |
|---|---|---|
| Code | ✅ READY | `gcfg` division registry + `division_summary --division` CLI |
| Reporting | ✅ READY | `division_summary` division-aware (STEP31); roll-up scaffold |
| Notebook | ✅ READY | railway notebooks parametrize via `division_summary` |
| Documentation | ✅ READY | `DIVISION_ONBOARDING_GUIDE.md` |
| **Data** | ⛔ **BLOCKED** | TPJ DMTR + SUMMARY absent from `raw_data/` |
| Architecture change needed | **NO** | config + data only |

## 3. Relationship to purification
Purification **does not block** TPJ and TPJ **does not block** purification — they are independent. Removing Walmart assets has **zero** effect on TPJ onboarding (no shared dependency). After purification, the cleaner repo makes TPJ onboarding *easier* (clear structure, division registry, onboarding guide).

## 4. Onboarding path (unchanged from STEP31)
1. Acquire TPJ DMTR + SUMMARY data. 2. Add `DIVISIONS["TPJ"]` registry entry. 3. Run the STEP20–28 chain + `division_summary --division TPJ`. 4. Pin a TPJ golden baseline. 5. Notebooks/reporting render TPJ automatically; MAS-vs-TPJ comparison + enterprise roll-up activate.

## 5. Verdict
**TPJ onboarding requires NO architectural change** — it is config + data. **Status: NO-GO today, solely data-blocked**, exactly as established in STEP31/Hardening Phase C. Purification is orthogonal and safe to do first.
