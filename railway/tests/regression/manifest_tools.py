"""STEP36 governed manifest tooling: forensics, rebuild, and CI integrity check
for railway/tests/regression/golden_output_manifest.csv.

This NEVER modifies output CSVs. It only inspects them and (rebuild) re-pins the
manifest hashes to the current committed bytes. A rebuild is permitted ONLY when
every pinned file is byte-identical modulo line-endings (IDENTICAL_EOL_ONLY) or
already matching — a genuine CONTENT_DIFFERENCE aborts the rebuild.
"""
from __future__ import annotations
import csv
import hashlib
from pathlib import Path

from railway import railway_config as cfg

MANIFEST = Path(__file__).parent / "golden_output_manifest.csv"
ROOT = cfg.OUTPUT_DIR


def _sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _read_manifest():
    with open(MANIFEST, newline="") as f:
        return list(csv.DictReader(f))


def classify(relpath: str, manifest_sha: str):
    p = ROOT / relpath
    if not p.exists():
        return {"actual_sha": "", "crlf_sha": "", "lf_sha": "", "classification": "MISSING_FILE"}
    raw = p.read_bytes()
    actual = _sha(raw)
    lf = raw.replace(b"\r\n", b"\n")
    crlf = lf.replace(b"\n", b"\r\n")
    lf_sha, crlf_sha = _sha(lf), _sha(crlf)
    if actual == manifest_sha:
        cls = "MATCH"
    elif manifest_sha in (lf_sha, crlf_sha):
        cls = "IDENTICAL_EOL_ONLY"
    else:
        cls = "CONTENT_DIFFERENCE"
    return {"actual_sha": actual, "crlf_sha": crlf_sha, "lf_sha": lf_sha, "classification": cls}


def forensics(write_to: str | None = None):
    rows = []
    pinned = set()
    for r in _read_manifest():
        rel = r["relpath"]; pinned.add(rel)
        c = classify(rel, r["sha256"])
        rows.append({"relpath": rel, "manifest_sha": r["sha256"], **c})
    for p in ROOT.rglob("*.csv"):
        rel = str(p.relative_to(ROOT)).replace("\\", "/")
        if rel not in pinned:
            rows.append({"relpath": rel, "manifest_sha": "", "actual_sha": _sha(p.read_bytes()),
                         "crlf_sha": "", "lf_sha": "", "classification": "EXTRA_FILE"})
    if write_to:
        with open(write_to, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["relpath", "manifest_sha", "actual_sha",
                                              "crlf_sha", "lf_sha", "classification"])
            w.writeheader(); w.writerows(rows)
    return rows


def rebuild(dry_run: bool = False):
    """Re-pin the manifest to current committed bytes for the SAME relpaths.
    Aborts if any pinned file is CONTENT_DIFFERENCE or MISSING_FILE."""
    rows = _read_manifest()
    report = []
    blockers = []
    for r in rows:
        rel = r["relpath"]
        c = classify(rel, r["sha256"])
        if c["classification"] in ("CONTENT_DIFFERENCE", "MISSING_FILE"):
            blockers.append((rel, c["classification"]))
        report.append({"relpath": rel, "old_sha": r["sha256"], "new_sha": c["actual_sha"],
                       "old_class": c["classification"]})
    if blockers:
        raise SystemExit(f"REBUILD ABORTED — genuine differences: {blockers[:10]}")
    if not dry_run:
        with open(MANIFEST, "w", newline="") as f:
            w = csv.writer(f); w.writerow(["relpath", "bytes", "sha256"])
            for r in rows:
                p = ROOT / r["relpath"]
                w.writerow([r["relpath"], len(p.read_bytes()), _sha(p.read_bytes())])
    return report


def check():
    """CI integrity gate: nonzero exit if any pinned file is CONTENT_DIFFERENCE/MISSING."""
    bad = [r for r in forensics() if r["classification"] in ("CONTENT_DIFFERENCE", "MISSING_FILE")]
    if bad:
        raise SystemExit(f"MANIFEST INTEGRITY FAIL: {len(bad)} files: {[b['relpath'] for b in bad[:10]]}")
    print("manifest integrity OK")
