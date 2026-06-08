"""Shared I/O surface for the railway ingestion layer (Phase A).

Single, non-leaky home for:
  * the canonical readers (re-exported for one-import convenience), and
  * the shared raw-data PATH constants that were previously defined inside
    ``railway_demand_reconstruction`` (DMTR_DIR) and triplicated as a literal in
    the planning modules (the dated SUMMARY OF STOCK HELD workbook).

This removes the architectural leak whereby planning modules imported
``railway_demand_reconstruction`` solely to reach its private ``_sheet_rows`` and
``DMTR_DIR``. Every layer now depends on ``railway.ingestion`` for I/O.

NOTE (Phase B): the path/filename constants below are I/O *locations* held here
as the single source for Phase A. Phase B (configuration centralization) will
promote the division-specific pieces (depot, division folder, dated filename)
into ``railway/governance/config`` and have this module reference them. Values
are byte-identical to the originals so no output changes.
"""
from railway.ingestion.excel_reader import read_sheet_rows, iter_sheet_rows
from railway.ingestion.csv_reader import read_pl_csv
from railway.governance import config as gcfg   # single source for raw-data paths (Phase B)

# --- shared raw-data locations (now sourced from centralized config) ---------
# DMTR monthly Material Transaction Register workbooks (active division).
DMTR_DIR = gcfg.DMTR_DIR

# Current-stock snapshot (depot 027534) used by safety_stock / rop / srrs.
SUMMARY_WORKBOOK = gcfg.SUMMARY_WORKBOOK

__all__ = [
    "read_sheet_rows", "iter_sheet_rows", "read_pl_csv",
    "DMTR_DIR", "SUMMARY_WORKBOOK",
]
