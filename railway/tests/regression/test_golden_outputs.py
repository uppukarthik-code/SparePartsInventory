"""Golden-file regression guard for the railway platform (STEP1-28 outputs).

PURPOSE
-------
This is the behavior-preservation harness REQUIRED before any modernization
refactor (layered package, shared ingestion, config centralization). It pins the
SHA-256 of every produced output CSV at the pre-refactor baseline. A refactor is
behavior-preserving IFF every byte of every output is unchanged after re-running
the pipeline.

USAGE
-----
1. Baseline (already done):    python _build_golden_manifest.py   (or the inline pin)
2. Refactor a module (behavior-preserving).
3. Re-run the producing driver(s) to regenerate outputs.
4. pytest railway/tests/regression/test_golden_outputs.py
   - PASS  => outputs byte-identical => behavior preserved.
   - FAIL  => a hash diverged => investigate before merging. ANY diff must be
             explained (and, for a pure refactor, reverted) per the
             non-negotiable "no behavior change" rule.

To intentionally re-baseline after an APPROVED, EXPLAINED output change, delete
golden_output_manifest.csv and re-run the pin step. Do NOT re-baseline to make a
failing refactor "pass".
"""
import csv
import hashlib
from pathlib import Path

import pytest

from railway import railway_config as cfg

MANIFEST = Path(__file__).parent / "golden_output_manifest.csv"
ROOT = cfg.OUTPUT_DIR


def _load_manifest():
    if not MANIFEST.exists():
        pytest.skip("golden_output_manifest.csv missing - run the pin step first")
    with open(MANIFEST, newline="") as f:
        return list(csv.DictReader(f))


def _sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


@pytest.mark.parametrize("row", _load_manifest(), ids=lambda r: r["relpath"])
def test_output_unchanged(row):
    """Each pinned output CSV must be byte-identical to its baseline hash."""
    p = ROOT / row["relpath"]
    assert p.exists(), f"output missing (regression): {row['relpath']}"
    actual = _sha256(p)
    assert actual == row["sha256"], (
        f"OUTPUT CHANGED: {row['relpath']}\n"
        f"  expected {row['sha256'][:16]}... ({row['bytes']} bytes)\n"
        f"  actual   {actual[:16]}...\n"
        f"  -> a refactor altered behavior; explain or revert."
    )


def test_no_unexpected_new_outputs():
    """Warn if new outputs appeared that are not in the baseline (additive ok,
    but surfaced so the refactor PR can confirm they are intended)."""
    pinned = {r["relpath"] for r in _load_manifest()}
    actual = {
        str(p.relative_to(ROOT)).replace("\\", "/")
        for p in ROOT.rglob("*.csv")
        if p.is_file()
    }
    new = sorted(actual - pinned)
    # Not a failure: additive outputs are allowed. Reported for review.
    if new:
        print(f"\n[info] {len(new)} new output CSV(s) not in baseline:")
        for n in new[:20]:
            print(f"   + {n}")
