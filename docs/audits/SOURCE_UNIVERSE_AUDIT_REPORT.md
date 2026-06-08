# SOURCE_UNIVERSE Audit Report (Phase 2)

**Generated:** 2026-06-08
**Status:** 🔍 **ANALYSIS ONLY — NO CODE CHANGED.** Awaiting approval before any implementation.
**Trigger:** Power BI shows `Source_Universe` = `Strategic` only on the procurement page.

---

## 1. Where `Source_Universe` Is Created (full trace)

`grep -rn 'Source_Universe' railway --include=*.py` →

| # | Location | Assignment | Drives |
|---|---|---|---|
| 1 | `railway_inventory_rationalization.py:109` | `np.where(df["Value_op"].notna(), "Operational", "Strategic")` — **data-driven** | page5, page9 (both universes present) |
| 2 | `railway_powerbi_export.py:118` | `p1["Source_Universe"] = "Strategic"` — **hard-coded** | **page1_procurement** |
| 3 | `railway_powerbi_export.py:132` | `p3["Source_Universe"] = "Strategic"` — **hard-coded** | page3_criticality |
| 4 | `railway_powerbi_export.py:168` | `"Source_Universe": "Strategic"` — **hard-coded** | page7 ABC×Criticality matrix |
| 5 | `railway_powerbi_export.py:140` | `p4["Source_Universe"] = "Operational"` — **hard-coded** | page4_operational_health |
| 6 | `railway_enterprise.py:137` | `"Both" / "Strategic" / "Operational"` — **data-driven** | master_sku_registry |

**The reported symptom is location #2.** `page1_procurement` carries a literal `"Strategic"` tag.

## 2. Exact Code Assigning It (the procurement page)

`railway_powerbi_export.py`, Page 1 builder:

```python
p1 = policy[[                       # <-- policy = railway_inventory_policy.csv
    "PL_Code", "Description", "Criticality", "ABC_Class", "Forecast_2026_27",
    "Current_Stock", "ROP", "Inventory_Gap", "Normalized_Investment_Required",
    "Normalized_Procurement_Priority_Score", "Normalized_Procurement_Priority_Class"]].copy()
p1 = p1.rename(columns={"Normalized_Procurement_Priority_Class": "Procurement_Priority_Class"})
p1["Source_Universe"] = "Strategic"     # line 118  <-- HARD-CODED
```

## 3. Are Operational Records *Incorrectly* Excluded? → **No.**

The procurement page is sourced **entirely** from `railway_inventory_policy.csv`, which is
produced by `railway_inventory_optimization.py::_load_inputs()`:

```python
hist   = demand_history.csv      # consumption series  (STRATEGIC universe, 59 items)
master = railway_sku_master.csv  # ABC / Criticality / Unit_Cost
fc     = railway_forecast.csv    # Forecast_2026_27
df = hist.merge(master ...).merge(fc ...)     # strategic-only frame
```

A procurement recommendation requires **forecast, demand-history σ, lead-time, ROP and
Inventory_Gap**. These exist **only for the 59 strategic items.** The 907-item
**operational** universe (`railway_operational_inventory.csv`) is a *stock-visibility* layer —
it carries `Movement_Status`, `Inventory_Aging_Class`, `Operational_ABC`, `Inventory_Value`,
but **no demand, no forecast, no ROP, no Inventory_Gap.**

Consequences:
- It is **structurally impossible** to compute a buy recommendation for operational-only SKUs
  with the current inputs — there is no demand signal to size a reorder against.
- The policy frame is therefore Strategic by construction; line 118 **labels what is already
  true** — it does not filter anything out.
- The ~7 SKUs that exist in **both** universes are already present on page1 via their strategic
  record, so **zero procurement-eligible items are dropped.**
- The operational universe's procurement-relevant signal points the **other way** — dead/slow
  stock to **dispose / rationalize** — and that *is* surfaced (page4, page5, page9), where
  `Source_Universe` correctly shows both `Strategic` and `Operational`.

**Verdict:** The `"Strategic"`-only tag on page1 is **accurate and non-defective.** The absence
of operational rows is a **data-availability fact**, not an exclusion bug.

## 4. Should Procurement Recommendations Contain Operational / Strategic / Both?

**Recommendation: STRATEGIC ONLY (keep current behaviour).**

| Option | Feasible today? | Assessment |
|---|---|---|
| **Strategic only** (current) | ✅ Yes | **Correct.** Procurement = forecast-driven replenishment-to-ROP; only strategic items have the required demand/forecast/lead-time inputs. |
| Operational only | ❌ No | Operational SKUs have no demand/ROP signal — no defensible "buy" quantity can be computed. |
| Both | ⚠️ Not without new data | Would require acquiring **forecast + consumption history + lead-time for the 907 depot items** (a data-acquisition project). Merely re-tagging the universe would surface operational rows with blank ROP/Gap/Score — misleading, not informative. It would also change page1 row count 59 → ~966 and break the "page1 = items to buy" contract and downstream validations (V2/V5, page8 budget knapsack). |

## 5. Exact Code Diff *Required* (only if "Both" is later approved — **DO NOT IMPLEMENT NOW**)

Re-tagging alone is **not** a real fix; it would need the universe sourced from data **and**
upstream demand inputs for operational items. The minimal *labeling* diff (insufficient on its
own, shown for completeness) would be:

```diff
# railway_powerbi_export.py  (Page 1) — NOT RECOMMENDED without operational demand data
- p1 = policy[[ ... strategic columns ... ]].copy()
- p1 = p1.rename(columns={"Normalized_Procurement_Priority_Class": "Procurement_Priority_Class"})
- p1["Source_Universe"] = "Strategic"
+ # Source the universe tag from the rationalization register instead of hard-coding,
+ # and (REQUIRED) join operational demand/ROP once it exists upstream.
+ universe = rationalization[["PL_Code", "Source_Universe"]]
+ p1 = policy[[ ... strategic columns ... ]].copy()
+ p1 = p1.rename(columns={"Normalized_Procurement_Priority_Class": "Procurement_Priority_Class"})
+ p1 = p1.merge(universe, on="PL_Code", how="left")
+ p1["Source_Universe"] = p1["Source_Universe"].fillna("Strategic")
```

> ⚠️ This diff **only relabels**. Without operational `Forecast / ROP / Inventory_Gap /
> Investment` it produces rows with empty procurement fields. **Prerequisite for a genuine
> "Both" procurement view:** extend the optimizer's `_load_inputs()` to ingest operational
> demand history and run the ROP model over the 907-item universe. That is a roadmap item, not
> a compatibility fix.

## 6. Findings Summary

1. ✅ `Source_Universe` on page1 is produced by a **hard-coded literal** (`railway_powerbi_export.py:118`).
2. ✅ It is **correct** — the upstream policy frame is strategic-only by data availability.
3. ✅ **No operational records are incorrectly excluded** (operational SKUs have no demand/ROP signal; the ~7 overlapping items are already included via the strategic side).
4. ✅ **Recommended scope: Strategic only.** "Both" requires new upstream demand data, not a tag change.
5. 🚫 **No code change made.** Diff above is illustrative and gated on business approval + data acquisition.
