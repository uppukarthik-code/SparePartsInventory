# STEP 19 — Strategic Inventory Allocation Framework

**Implementation Report**
**Date:** 2026-06-08
**Scope:** Convert strategic inventory from a **zone-level shared** model to a **Business-Unit allocated** model using the per-store-depot stock columns in `railways.xlsx`. **Strategic allocation layer only** — operational analytics, forecasting, ROP/optimization, SRRS and procurement formulas are untouched.

---

## 1. Objective & approach

Previously all 59 strategic items were attributed to the zone (defaulting to MAS), so every Business Unit inherited the full zone strategic stock/value — inflating enterprise aggregation by **6×** and preventing division-level strategic visibility.

STEP 19 allocates each strategic PL's stock across the six Southern Railway divisions by its **store-depot column**, then propagates that allocation into the enterprise layer (de-inflation), conserving the zone total exactly.

---

## 2. Verified depot-code → Business-Unit mapping

The strategic stock sheets carry **6 store-depot columns**; `EAR Consumptions` carries the **6 SR divisions**. One depot per division:

| Stock depot column | Store / location | Division | Business Unit | Verification basis |
|--------------------|------------------|----------|---------------|--------------------|
| `GSD/PER` | Perambur, Chennai | Chennai | **MAS** | given + nomenclature |
| `GSD/ED`  | Erode | Salem | **SA** | given + nomenclature |
| `LSD/MDU` | Madurai | Madurai | **MDU** | given + nomenclature |
| `DSD/QLN` | Quilon / Kollam | Thiruvananthapuram | **TVC** | given + nomenclature |
| `GSD/GOC` | Golden Rock (Ponmalai), Tiruchirappalli | Tiruchirappalli | **TPJ** | given + nomenclature |
| `SSD/PTJ` | **Podanur Junction** | **Palakkad** | **PGT** | **STEP19 verified** (structure + nomenclature) |

### 2.1 PTJ decision rationale — `SSD/PTJ → PGT` (not TPJ)
- **Structural elimination (decisive):** 6 depots ↔ 6 divisions, 1:1. Five pin unambiguously (incl. GOC→TPJ — Golden Rock *is* Tiruchirappalli/Ponmalai). The only unpinned division is PGT; the only unpinned depot is PTJ ⇒ `PTJ↔PGT`.
- **Nomenclature:** station code **PTJ = Podanur Junction**, in the **Palakkad (PGT)** division. Ponmalai/Golden Rock = **GOC = Tiruchirappalli**. PTJ and Ponmalai are different places in different divisions — disproving the old `"PTJ = Ponmalai (Tiruchirappalli)"` config comment.
- **Empirical (disclosed, non-decisive):** the `SSD/PTJ` column holds only ~12 units, so per-PL correlation gave no signal (r≈−0.03); used as neither proof nor disproof.
- **Documentary limit:** a full-text sweep of all 9 sheets found no expanded location names — the workbook uses codes only.

### 2.2 PGT decision rationale — resolved by the PTJ finding
With `SSD/PTJ → PGT`, **PGT's strategic stock IS the `SSD/PTJ` column** (≈12 units). The audit's "PGT column does not exist" was an artefact of the prior `PTJ→TPJ` assumption. **No consumption-derived invention was needed** (Option B rejected); PGT is allocated directly from the stock sheet (Option: direct depot column). The 12-unit figure is a genuine finding — PGT is strategically under-stocked on this snapshot (its consumption is 42,027, available in `EAR Consumptions` as a cross-check only).

---

## 3. Modules impacted

| Module | Change | Protected-logic impact |
|--------|--------|------------------------|
| `railway_config.py` | **Added** `STRATEGIC_DEPOT_TO_BU` (verified map) | none (additive constant) |
| `railway_business_unit_config.py` | **Corrected** `("PTJ","TPJ")` → `("PTJ","PGT")` | none — never fires on operational depots (they carry literal `TPJ`/`PGT`); zero existing outputs changed |
| **NEW** `railway_strategic_allocation.py` | Allocation engine + `strategic_inventory_allocation.csv` | none (read-only on strategic sheet) |
| `railway_enterprise.py` | Strategic SKU tagging → allocated BU; benchmark strategic value → per-BU allocated share; self-validation updated | enterprise layer only (intended de-inflation) |
| Forecasting / optimization / SRRS / procurement / operational / Power BI page schemas | **No change** | verified byte-identical |

**Regeneration driver:** `_step19_regenerate.py` (one-off) regenerates **only** the allocation + enterprise layers per BU — it never re-runs operational/forecast/SRRS/procurement, so those outputs stay byte-identical (proven in the validation report).

---

## 4. Allocation logic

`railway_strategic_allocation.allocate()`:
1. Reads the `Stock as on 31.03.2026` sheet (read-only) — the six `stock_<depot>` columns + `Unit_Cost`.
2. For each PL × depot with non-zero stock, emits one row tagged with the depot's Business Unit.
3. **Allocation basis = depot columns** (per-location source of truth). Where a PL's `TOTAL` column disagrees with its depot sum, the depot columns win and the discrepancy is reported (see §6 anomaly).

**Output `strategic_inventory_allocation.csv`** — `PL_Code, Description, Business_Unit, Strategic_Stock, Allocation_Source, Source_Depot_Column` — written per BU (`outputs/<BU>/`) and consolidated (`outputs/_enterprise_rollup/`). **78 rows, 313,892 units, conserved.**

### 4.1 Per-BU strategic allocation result

| BU | Depot | Strategic Stock | Strategic Value raw (₹) | Value share | Benchmark (de-inflated, ₹) |
|----|-------|----------------:|------------------------:|------------:|---------------------------:|
| MAS | GSD/PER | 220,422 | 644,079,280 | 0.9675 | 82,879,378.63 |
| TPJ | GSD/GOC | 38,284 | 7,667,532 | 0.0115 | 986,649.15 |
| TVC | DSD/QLN | 30,744 | 6,665,838 | 0.0100 | 857,752.29 |
| MDU | LSD/MDU | 15,446 | 6,168,158 | 0.0093 | 793,711.41 |
| SA | GSD/ED | 8,984 | 1,091,561 | 0.0016 | 140,460.87 |
| PGT | SSD/PTJ | 12 | 44,166 | 0.0001 | 5,683.17 |
| **Zone** | — | **313,892** | **665,716,535** | **1.0000** | **85,663,635.52** |

---

## 5. Enterprise de-inflation

The benchmark previously stamped the **full** published zone strategic value (₹85.66M, normalized) onto **every** Live unit → summing 6 units gave ₹513.98M (6× phantom). STEP 19 replaces it with each BU's **allocated share** of that same published total, so the sum equals ₹85.66M exactly (**no KPI redefinition** — only a conserved split). The master registry now tags strategic-only SKUs by their **dominant** depot BU instead of all-MAS.

---

## 6. Data-quality finding (carried, not silently fixed)

PL `50232356/ 50232319` (composite "Magneto telephone") has depot-sum **808** but a `TOTAL` column of **114** (Δ694) — a source data-entry error. Per the approved decision, allocation uses the **depot columns** (808 distributed: MAS 241, TVC 173, TPJ 161, MDU 148, SA 85). Flagged in the validation report.

---

## 7. Deliverables
- `railway/railway_strategic_allocation.py` (new module)
- `outputs/<BU>/strategic_inventory_allocation.csv` (×6) + `outputs/_enterprise_rollup/strategic_inventory_allocation.csv`
- Regenerated `outputs/<BU>/enterprise/*` (de-inflated)
- `STEP19_VALIDATION_REPORT.md`, `STEP19_IMPACT_ANALYSIS.md`

**Recommended next step:** per-division strategic *forecasting / ROP / SRRS* on the allocated stock (explicitly out of STEP 19 scope — STEP 19 allocates the stock dimension only; forecast/ROP/SRRS/procurement formulas remain zone-level and unchanged).
