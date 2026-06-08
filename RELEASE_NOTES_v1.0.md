# Railway Inventory Planning Platform — v1.0 Release Notes

**Status:** PREPARATION ONLY (not committed/tagged/published). Division: **MAS** (Southern Railway). Branch: `repository-purification`.

---

## Platform evolution (STEP1–33)
| Arc | Steps | Outcome |
|---|---|---|
| **Railway Core Transformation** | STEP1–19 | Multi-division platform (MAS/SA/TPJ/MDU/PGT/TVC); strategic + operational pipelines, forecasting engine, optimizer, enterprise rollup |
| **MAS Planning Platform** | STEP20–28 | Demand reconstruction (54 mo), SBC classification, forecasting (SBA/TSB/Croston), lead-time derivation, criticality, **safety stock / ROP / SRRS**, procurement portfolio |
| **Independent Audit** | — | Formula recomputation ±0.005; literature-validated; CONDITIONAL GO |
| **Hardening Program A/B** | — | `ingestion/` extracted (leak removed), `governance/config` centralized, **reproducible-from-code regression baseline** |
| **Notebook & Reporting Rebuild** | STEP30 | 3 executed railway notebooks; `division_summary` STEP1-28 KPI engine |
| **Reporting Cut-Over** | STEP31 | Single KPI source of truth; division-aware; enterprise rollup foundation |
| **Repository Purification** | STEP32–33 | Railway-only tree; 94% size reduction; pinned deps; CI; docs hierarchy |

## Capabilities (v1.0)
- **Forecasting:** Syntetos–Boylan routing → SBA/TSB/Croston/SES-Holt; 88.7% coverage.
- **Lead time:** derived from DMTR procurement chronology; 97.8% coverage.
- **Planning:** safety stock (z·σ·√(LT/30.44)), ROP (DDLT+SS), SRRS prioritization.
- **Risk:** 465 critical shortages surfaced; top-10 = 84.5% of service risk; 5-tier procurement portfolio.
- **Capital:** current stock Rs 0.91B vs reorder-gap Rs 3.37B quantified.
- **Reporting:** L1/L2/L3 KPI framework; 3 audience-tuned notebooks; division-aware management summary with provenance metadata.
- **Engineering:** 541 green tests; reproducible baseline; layered ingestion/governance; pinned deps; CI.

## Limitations
- Single live division (**MAS**); others config-ready, data-blocked.
- SS uses normal approximation for intermittent demand (documented; AMBER in audit).
- `pl_match_candidates.csv` requires `PYTHONHASHSEED=0` (tied-row determinism).
- Legacy reporting compute frozen (deprecated) for output backward-compat; physical removal deferred.

## TPJ readiness
**No architectural change needed** — config + data only. **NO-GO today, solely data-blocked** (TPJ DMTR + SUMMARY absent). On data arrival: add `DIVISIONS["TPJ"]`, run STEP20–28, `division_summary --division TPJ`.

## Future roadmap
1. Remote migration to `uppukarthik-code` (PRIVATE) + STEP34/35/36 commit→push→tag.
2. Permanent purge of the quarantine after review.
3. TPJ onboarding (data acquisition).
4. Enterprise rollup build-out; layered-package completion; legacy-compute removal.

## Release governance
**PRIVATE repository** — contains real Southern Railway operational + commercial data (DMTR, stock-held, procurement, valuations). Public release requires data-governance clearance.
