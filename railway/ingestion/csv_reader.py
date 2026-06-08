"""Canonical CSV readers for the railway platform (Phase A consolidation).

``read_pl_csv`` is the single source for the byte-identical CSV-reading pattern
that was triplicated as a private ``_rd`` in ``railway_safety_stock``,
``railway_rop`` and ``railway_lead_time_derivation``:

    pd.read_csv(path, dtype={"PL_Code": str}, keep_default_na=False)

``keep_default_na=False`` is essential: the PL code "NA" is a real (uncoded) DMTR
item and must NOT be coerced to NaN. ``dtype={"PL_Code": str}`` preserves leading
zeros / exact code strings.

NOTE: ``railway_pl_master._rd`` reads ALL columns as ``dtype=str`` (a different
contract) and is intentionally NOT consolidated here.
"""
import pandas as pd


def read_pl_csv(path):
    """Read a planning CSV preserving PL_Code as string and literal 'NA'."""
    return pd.read_csv(path, dtype={"PL_Code": str}, keep_default_na=False)
