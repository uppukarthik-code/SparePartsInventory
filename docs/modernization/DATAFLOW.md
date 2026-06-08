# Data Flow

End-to-end flow from raw railway records to prioritized replenishment, with the
owning module and produced artifact at each stage.

## Sources (`raw_data/`)
| Source | Depot | Feeds |
|---|---|---|
| `DMTR_*.xlsx` (54 files, issue + procurement) | 027534 (MAS) | demand reconstruction, lead-time derivation |
| `SUMMARY OF STOCK HELD (... 08-06-2026).xlsx` | 027534 | current stock, criticality (PL-Code/Type/Usage) |
| `stock_history.xlsx` (per division) | 027029 etc. | strategic stock snapshot (core) |
| `railways.xlsx`, `railway_stock_summary.xlsx` | — | core strategic/operational loaders |

## Stages
```
[1] DMTR issues ──► railway_demand_reconstruction
        Issues_Qty = ToUser + ForEndUse + ToContractor; gap-fill first-seen→2026-06;
        reconstruct Closing_Stock running balance
        → monthly_demand_history.csv
[2] history ──► railway_demand_classification   (SBC: ADI 1.32 / CV² 0.49)
        → demand_classification.csv
[3] class ──► railway_forecast_generation        (Croston/SBA/TSB/Holt via forecasting engine)
        → forecast_results.csv
[4] DMTR procurement ──► railway_lead_time_derivation
        PO→Receipt (p1) / Reqn→Receipt (p2); P5/P95 winsorize; median; reject negatives
        → lead_time_master.csv
[5] PL reconciliation ──► railway_pl_master       → enterprise_pl_master.csv
[6] [2]+[3]+[4]+criticality ──► railway_safety_stock
        SS = z·σ·√(LT/30.4375)                    → safety_stock_results.csv
[7] [6]+forecast ──► railway_rop
        ROP = DDLT + SS; gap = ROP − stock         → rop_results.csv
[8] [7]+criticality+value ──► railway_srrs_mas
        SRRS = weight × service_factor × positive_gap; separate value lens
        → srss_results.csv
[9] all ──► reports (STEP27/28)
```

## Stage ownership & reproducibility notes
- **Criticality** is currently derived inline inside steps [6]/[8] from the SUMMARY
  `PL-Code/Type/Usage` Type token (Safety/Vital/NA → Critical/Non-Critical). It has
  no dedicated module yet (extraction is planned — `technical_debt_remediation.csv` TD18).
- **Current stock** comes **only** from the depot-027534 SUMMARY snapshot — no
  synthetic/back-calculated stock, no 027029 substitution.
- The flow is **deterministic and byte-reproducible**; all 536 outputs are
  SHA-256-pinned (`tests/regression/golden_output_manifest.csv`).
- Shared XLSX reading is currently provided by `demand_reconstruction._sheet_rows`
  (the leak); after the `ingestion/` extraction it will come from `ingestion/xlsx_reader.py`.
