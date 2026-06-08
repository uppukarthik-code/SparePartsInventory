"""Canonical PL-code normalization (Phase A consolidation).

Centralises the platform's two DISTINCT normalization concerns into one module.
They are NOT duplicates and are intentionally kept as separate functions with
their exact original behaviour:

* ``norm_pl_key`` — formerly ``railway_data_preparation._norm_pl``. Produces a
  clean string join-key (or None) from float/int/composite raw values. Used to
  align PL codes across loaders.

* ``normalize_pl`` — formerly ``railway_pl_master.normalize_pl``. An AUDITING
  normaliser returning ``(normalized, issue_type, changed)`` with leading-zero
  stripping and issue tagging (Whitespace / Composite / NonNumeric).

Behaviour is preserved byte-for-byte; the originals now delegate here.
"""
import re

import pandas as pd


def norm_pl_key(v):
    """Normalise a P.L. code to a clean string key (handles float/int/composite).

    Exact replacement for ``railway_data_preparation._norm_pl``.
    """
    if v is None:
        return None
    if isinstance(v, float) and pd.isna(v):
        return None
    if isinstance(v, (int, float)):
        return str(int(v))
    s = re.sub(r"\s+", "", str(v))          # drop internal spaces ('a/ b' -> 'a/b')
    return s or None


def normalize_pl(pl: str):
    """Return (normalized, issue_type, changed). Digits-only, leading zeros stripped.

    Exact replacement for ``railway_pl_master.normalize_pl``.
    """
    raw = str(pl)
    issue = []
    if raw != raw.strip() or " " in raw:
        issue.append("Whitespace")
    if "/" in raw:
        issue.append("Composite")
    digits = "".join(c for c in raw if c.isdigit())
    if not digits:
        norm = re.sub(r"\s+", "", raw.upper())
        issue.append("NonNumeric")
    else:
        if digits[0] == "0":
            issue.append("LeadingZero")
        norm = digits.lstrip("0") or "0"
        issue.append(f"Len{len(digits)}")
    return norm, "+".join(issue) if issue else "Standard", (norm != raw)
