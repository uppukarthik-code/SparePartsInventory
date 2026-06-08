"""railway.ingestion — consolidated I/O layer (Phase A).

Single source for raw-OOXML reading, canonical CSV reading, PL-code
normalization, input validation, and shared raw-data paths. Replaces three
duplicated readers and removes the cross-layer leak whereby planning modules
imported ``railway_demand_reconstruction`` for its private ``_sheet_rows``.
"""
from railway.ingestion.excel_reader import read_sheet_rows, iter_sheet_rows
from railway.ingestion.csv_reader import read_pl_csv
from railway.ingestion.pl_normalization import norm_pl_key, normalize_pl
from railway.ingestion.shared_io import DMTR_DIR, SUMMARY_WORKBOOK

__all__ = [
    "read_sheet_rows", "iter_sheet_rows", "read_pl_csv",
    "norm_pl_key", "normalize_pl", "DMTR_DIR", "SUMMARY_WORKBOOK",
]
