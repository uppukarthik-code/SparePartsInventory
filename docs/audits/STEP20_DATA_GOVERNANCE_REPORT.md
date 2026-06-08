# STEP 20 — Data Governance Report

**Type:** Read-only audit. No code/data/config changes.
**Date:** 2026-06-08
**Focus:** Strategic stock vs consumption vs EAR by Business Unit; anomalies; strategic exposure; the PGT = 12 investigation.

---

## PART 2 — Strategic Stock vs Consumption vs EAR

### 2.1 Master table (allocated strategic stock; EAR & consumption are 2020-21, the only per-division year)

| BU | Strategic Stock | EAR Requirement | Consumption | Coverage (Stock ÷ Cons) | Operational Value (₹) | Dead Stock (₹) |
|----|----------------:|----------------:|------------:|------------------------:|----------------------:|---------------:|
| MAS | 220,422 | 217,200 | 77,323 | **2.851×** | 512,406,406 | 76,283,548 |
| TPJ | 38,284 | 79,290 | 27,034 | **1.416×** | 209,040,051 | 3,195,260 |
| TVC | 30,744 | 83,395 | 32,119 | **0.957×** | 194,686,398 | 16,750,692 |
| MDU | 15,446 | 79,761 | 28,538 | **0.541×** | 100,246,296 | 3,862,176 |
| SA | 8,984 | 96,125 | 64,775 | **0.139×** | 81,817,770 | 3,250,955 |
| PGT | 12 | 114,742 | 42,027 | **0.0003×** | 119,999,655 | 6,325,697 |

### 2.2 Rankings

**Strategic coverage (stock ÷ annual consumption) — high → low**
1. 🟢 MAS 2.85× · 2. 🟢 TPJ 1.42× · 3. 🟡 TVC 0.96× · 4. 🟠 MDU 0.54× · 5. 🔴 SA 0.14× · 6. ⚫ **PGT 0.0003×**

- **Overstocked (>1.5×):** MAS (2.85×) — holds ~70% of zone strategic units; TPJ (1.42×).
- **Adequate (~1×):** TVC (0.96×).
- **Understocked (<0.6×):** MDU (0.54×), SA (0.14×).
- **Critically understocked (≈0):** **PGT (0.0003×)** — see §2.4.

**EAR requirement — high → low:** PGT 114,742 > MAS 217,200… *(note: MAS 217,200 is highest; PGT 114,742 is 2nd).* Corrected order: MAS 217,200 · PGT 114,742 · SA 96,125 · TVC 83,395 · MDU 79,761 · TPJ 79,290.

### 2.3 Potential data anomalies & strategic exposure

| Finding | Type | Detail | Exposure |
|---------|------|--------|----------|
| **PGT 12 units vs 114,742 EAR / 42,027 consumption** | Completeness / governance | See §2.4 | 🔴 Highest — strategic vital-item visibility for Palakkad is effectively absent |
| **MAS 220,422 ≈ MAS EAR 217,200, but MAS consumption only 77,323** | Allocation interpretation | MAS/Perambur (`GSD/PER`) holds 70% of zone strategic units; requirement (217k) is 2.8× its own consumption (77k) | 🟠 `GSD/PER` may function as the **zone central reserve**, not purely Chennai-division stock — attributing 100% to MAS may overstate MAS and understate peers |
| **SA coverage 0.14×** (8,984 vs 64,775 consumption) | Strategic exposure | Salem holds <2 months of strategic cover | 🟠 Genuine understock risk |
| **Composite PL `50232356/50232319`** | Source data-entry error | Depot-sum 808 vs workbook TOTAL 114 (carried from STEP19) | 🟡 Upstream workbook correction needed |
| **Single-year per-division demand** | Coverage | `EAR Consumptions` covers only 2020-21 | 🟠 Blocks per-division forecasting (see Readiness report) |

### 2.4 Special focus — is PGT strategic stock = 12 genuine?

**Evidence gathered (read-only):**
- Only **2 PLs** carry any `SSD/PTJ` stock — both relays: PL 56451027 "Relay AC Immune Plug-in QBC" (10) and PL 56450217 "Relay AC Immune Plug-in QSPA1" (2) = **12 units total**.
- PGT has the **2nd-highest EAR requirement** (114,742) and **2nd-highest consumption** (42,027) of the six divisions.
- PGT simultaneously holds **₹119,999,655 of operational stock across 920 items** (STEP18A).
- Strategic coverage = **0.029%** of annual consumption — three orders of magnitude below every peer.

**Verdict — primarily (C) stock held/recorded elsewhere + (D) governance/visibility gap; (A) genuine at the cell level; (B) is NOT the cause.**

| Option | Assessment |
|--------|-----------|
| **A. Genuine** | ✅ True *as recorded* — the `SSD/PTJ` column legitimately contains 12 units across 2 relay PLs; the number is internally consistent, not a transcription slip. |
| **B. Data-quality (wrong number)** | ❌ Rejected — the cells are coherent; this is not a typo or unit error. |
| **C. Stock held/recorded elsewhere** | ✅ **Most likely** — a division consuming 42,027/yr with ₹120M operational stock must hold vital spares somewhere. The Podanur (`SSD/PTJ`) signal store is evidently **not** where Palakkad's strategic vital items are recorded; they are most plausibly carried in PGT's operational depot or another Palakkad store outside this zone return. |
| **D. Governance problem** | ✅ **Concurrent** — the zone vital-items return under-reports Palakkad. The strategic stock-position process does not capture Palakkad's true vital-item holding, creating a reporting/governance gap. |

**Recommendation:** treat PGT's strategic stock as **unverified/incomplete**, not zero. Do **not** drive PGT procurement or SRRS from the `SSD/PTJ` figure until the division's stores department confirms where Palakkad's strategic vital items are held and reconciles them into the zone return. Flag as a **governance action**, not a code fix.

---

## 2.5 Governance findings summary

1. **PGT strategic visibility gap (Critical):** reconcile Palakkad vital-item holdings; the 12-unit figure is real but materially incomplete.
2. **Perambur central-reserve ambiguity (High):** confirm whether `GSD/PER` is Chennai-division stock or the zone central reserve; if central, the STEP19 allocation should carry a "central reserve" flag rather than 100% MAS attribution (a future configuration question, not a defect).
3. **Single-year per-division demand (High):** the per-division demand foundation is one year — the chief blocker to business-unit planning.
4. **Source workbook anomaly (Medium):** correct PL `50232356/50232319` TOTAL (114) vs depot-sum (808) upstream.
5. **Audit-trail recommendation:** institute a per-snapshot reconciliation of `Σ depot columns == TOTAL` and `division EAR vs consumption` as a standing data-governance gate before each planning cycle.

*No data was modified in producing this report.*
