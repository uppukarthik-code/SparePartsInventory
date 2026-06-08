"""Input-side validation helpers for the railway ingestion layer (Phase A).

Additive, behavior-preserving. These are reusable guard primitives for code that
reads raw/intermediate data, giving the ingestion layer a single validation home.

This does NOT replace ``railway.schema_validation``, which remains the authority
for OUTPUT contract validation (column/numeric/null/dup/range checks over the
produced CSVs) and is left untouched. Validation was already centralised there
(it was not duplicated); this module covers the ingestion/input side so future
parsers share one set of guards instead of bare ``except -> 0.0`` patterns.

No existing module is rewired to use these yet (that would be a behavior change
to harden silent-failure paths, scheduled as a later phase); they are provided
now as the consolidation point.
"""
from __future__ import annotations

from pathlib import Path


class IngestionError(ValueError):
    """Raised when an ingestion input violates an explicit expectation."""


def require_file(path) -> Path:
    """Assert a required input file exists; return it as a Path."""
    p = Path(path)
    if not p.exists():
        raise IngestionError(f"required input file missing: {p}")
    return p


def require_columns(present, required, *, where: str = "") -> None:
    """Assert all required column indices/names are present."""
    missing = [c for c in required if c not in present]
    if missing:
        raise IngestionError(f"missing columns {missing} in {where or 'input'}")


def coerce_float(raw, default: float = 0.0) -> float:
    """Parse a float, returning ``default`` for blank/None (explicit, not bare-except)."""
    if raw is None:
        return default
    s = str(raw).strip()
    if s == "":
        return default
    try:
        return float(s)
    except ValueError:
        return default


def non_negative(value: float, *, name: str = "value") -> float:
    """Assert a value is non-negative (e.g. quantities, lead times)."""
    if value < 0:
        raise IngestionError(f"{name} must be non-negative, got {value}")
    return value
