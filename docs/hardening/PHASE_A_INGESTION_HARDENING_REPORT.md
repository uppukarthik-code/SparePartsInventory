# Phase A — Ingestion Extraction Hardening Report

**Date:** 2026-06-08 · **Status:** ✅ COMPLETE, behavior-preserving · Evidence: `ingestion_migration_report.csv`, regression suite, reader/normalizer equivalence proofs.

---

## 1. What was built
A new consolidated I/O layer `railway/ingestion/`:

| Submodule | Responsibility | Source consolidated |
|---|---|---|
| `excel_reader.py` | raw-OOXML readers `read_sheet_rows` (list) + `iter_sheet_rows` (generator) | `demand_reconstruction._sheet_rows` + `data_preparation._xlsx_rows_via_xml` |
| `csv_reader.py` | `read_pl_csv` (PL_Code-as-str, `keep_default_na=False`) | triplicated `_rd` in safety_stock/rop/lead_time |
| `pl_normalization.py` | `norm_pl_key` (key) + `normalize_pl` (audit tuple) | `data_preparation._norm_pl` + `pl_master.normalize_pl` |
| `data_validation.py` | input-side guard primitives (additive) | new home (schema_validation left as output authority) |
| `shared_io.py` | re-exports + `DMTR_DIR`, `SUMMARY_WORKBOOK` single source | the leaked `dr.DMTR_DIR` + the triplicated SUMMARY literal |

## 2. The leak is gone
Previously `railway_safety_stock`, `railway_rop`, `railway_srrs_mas`, `railway_lead_time_derivation` imported **`railway_demand_reconstruction`** solely to reach its *private* `_sheet_rows` (and `DMTR_DIR`) — a prioritization-layer module depending on a demand-layer private function for I/O.

```
grep "import railway_demand_reconstruction" railway/*.py  ->  0 results
grep "dr._sheet_rows | dr.DMTR_DIR"        railway/*.py  ->  0 results
```
All four now depend on `railway.ingestion`. The two original private readers remain as **thin delegations** (names/return contracts kept) so internal callers are untouched.

## 3. Behavior preservation — proof (not assertion)
The modules now *delegate*, so identical readers ⇒ identical downstream outputs. Proven directly against the original reader source:

| Check | Result |
|---|---|
| `read_sheet_rows` vs old `_sheet_rows` on **every** real input (54 DMTR + SUMMARY) | **55/55 byte-identical** |
| `iter_sheet_rows` vs old `_xlsx_rows_via_xml` on operational workbook | **identical** |
| `norm_pl_key` vs old `_norm_pl` (20 cases incl. NaN/int/float/composite/`NA`) | **0 mismatches** |
| `normalize_pl` vs old (leading-zero / NonNumeric / Len tagging) | **0 mismatches** |
| MAS extension chain regenerated through new layer → SHA-256 regression | **535/536 byte-identical** |
| Formula-invariant tests (SS/ROP/SRRS) | **3/3 green** |
| **Full suite** | **540 passed** |

## 4. The one non-byte-identical file (honest disclosure)
`MAS/history/pl_match_candidates.csv` did **not** match the prior hash. Root-caused as **pre-existing cross-process non-determinism, NOT a Phase-A regression**:
- `pl_master.build_match_candidates` sorts only on `["Match_Type","Match_Score"]`; tied rows fall back to `set()` iteration order, which Python varies per-process via `PYTHONHASHSEED`.
- Proof: two fresh processes at default seed → different hashes; at `PYTHONHASHSEED=0` → identical hashes; **row-SET identical across seeds** (only tied-row order differs).
- My refactor only delegated the *proven-identical* `normalize_pl`; it cannot have changed the content.
- **Resolution:** regenerated deterministically under `PYTHONHASHSEED=0`, re-pinned **only that one** manifest entry. `pl_master` logic was **not** modified (a tied-row reorder would be a byte change requiring sign-off).
- **Tracked follow-up (sign-off-gated):** add a stable data tiebreaker to the candidates sort to make the file reproducible without seed pinning. Recorded in `technical_debt_remediation.csv` scope as a determinism fix.

## 5. Answers to Phase-A questions
- **Which readers were consolidated?** The two raw-OOXML readers (`_sheet_rows`→`read_sheet_rows`, `_xlsx_rows_via_xml`→`iter_sheet_rows`) and the triplicated CSV `_rd`→`read_pl_csv`.
- **Which modules changed imports?** `demand_reconstruction`, `data_preparation`, `safety_stock`, `rop`, `srrs_mas`, `lead_time_derivation`, `pl_master` (7 modules).
- **What duplication was eliminated?** 2 duplicate XLSX readers → 1 module; 3 identical CSV readers → 1 function; 2 normalizers centralized to 1 module; `DMTR_DIR` single-sourced; the cross-layer leak removed.

## 6. Verdict
Leak eliminated, duplication consolidated, **zero analytical/output change** (proven byte-level + content-level). The platform is simpler and the ingestion surface is now a single, testable layer. Proceed to Phase B.
