# Regression Governance

This document defines ownership, re-baselining rules, and change-control process for the Railway Platform regression suite.

---

## Baseline Philosophy

The golden manifest (`railway/tests/regression/golden_output_manifest.csv`) pins the **byte-exact SHA-256** of every committed output file. This makes regression detection deterministic: any unintended content change in an output CSV is caught before merge.

Key principles:

- **LF normalization via `.gitattributes`:** All output CSVs (`railway/outputs/**/*.csv`) and the manifest itself are normalized to LF (`text eol=lf`). CI runs on `ubuntu-latest` (LF). pandas on Windows writes CRLF; `.gitattributes` corrects this on `git add`. A fresh clone on any OS reproduces the committed LF bytes and therefore reproduces the SHA-256 hashes.
- **Strategic counts are invariants:** The strategic universe (59 PLs, 4 tiers, 5 divisions) is stable business data. Tests that assert these counts are regression guards — they must not drift silently and require explicit approval to change.
- **Operational counts are volatile:** Row counts for operational outputs (pages 4 and 5) track data volume and change when new BUs are onboarded. These are validated structurally (schema, reproducibility, business-rule invariants) rather than by pinned magic numbers.

---

## Manifest Ownership and Re-Baselining Rules

The manifest is owned by `railway/tests/regression/manifest_tools.py`. All manifest operations must go through its API:

| Operation | Invocation |
|-----------|-----------|
| **Check** (CI gate) | `python -c "import sys; sys.path.insert(0,'railway/tests/regression'); import manifest_tools as m; m.check()"` |
| **Rebuild** (after intentional output change) | `python -c "import sys; sys.path.insert(0,'railway/tests/regression'); import manifest_tools as m; m.rebuild()"` |
| **Forensics** (diagnose a failing hash) | `python -c "import sys; sys.path.insert(0,'railway/tests/regression'); import manifest_tools as m; m.forensics('out.csv')"` |

**Re-baselining rules:**

1. `m.rebuild()` **aborts** if it detects `CONTENT_DIFFERENCE` or `MISSING_FILE`. Resolve the underlying issue first.
2. Re-baseline **only** after an intentional, reviewed output change — never to mask a failing refactor.
3. Always run `m.rebuild()` on Linux, or on Windows with the `.gitattributes` LF rules in place, so the stored hashes match what CI will see.
4. After rebuilding, run the full suite (`pytest railway/tests`) before committing.
5. The rebuilt manifest must be committed in the same PR as the output change, with a documented reason.

---

## Fixture Ownership

| Fixture type | Policy |
|---|---|
| **Strategic-universe counts** (59 PLs, 4 tiers, 5 divisions) | Must not drift silently. Any change requires human approval and a documented reason. These are stable invariants. |
| **Operational counts** (page 4 / page 5 row counts) | Track data volume. Update when onboarding changes. Record the update in `docs/audits/stale_fixture_inventory.csv`. Do not use magic numbers — prefer reproducibility invariants. |
| **Business-rule tests** | Encode a specific STEP-verified behaviour (e.g. STEP19 depot routing). When the underlying rule changes, update the fixture and document the STEP reference. |
| **Schema tests** | PL_Code uniqueness applies to master and policy outputs; operational outputs are exempt (multi-row per PL is expected). Fixture scope must match the actual invariant. |

**General guidance:** prefer invariants (reproducibility, schema correctness, business-rule verification) over magic numbers. Magic-number fixtures become stale silently; invariant fixtures stay correct as data evolves.

---

## Approval Requirements

The following changes require **explicit human approval** and a documented reason before they are committed:

- Any change that alters a SHA-256 hash in the golden manifest (i.e. any output content change)
- Any change to a strategic-universe count (59 PLs, tier counts, division counts)
- Any formula change
- Any KPI definition change

The following are **routine** but must be documented (update `docs/audits/stale_fixture_inventory.csv`):

- EOL-only normalization (CRLF→LF): expected when renormalizing on Windows; no content change
- Operational count fixture updates due to BU onboarding

---

## Change-Control Process

Follow these steps for any change that touches outputs, fixtures, or the manifest:

1. **`m.check()`** — confirm the manifest matches current committed outputs. If it fails on a file you did not intend to change, investigate before proceeding.
2. **Document intent** — if outputs will intentionally change, write a brief reason (PR description, commit message, or `stale_fixture_inventory.csv` entry).
3. **`m.rebuild()`** — rebuild the manifest after the intended output change. This will abort on unexpected diffs; resolve those first.
4. **Update affected fixtures** — update any test fixtures that encode counts or values that changed. Record the change in `docs/audits/stale_fixture_inventory.csv`.
5. **`pytest railway/tests`** — run the full suite. All tests must pass before committing.
6. **PR with diff + reason** — open a PR that includes the output diff, the rebuilt manifest, updated fixtures, and a documented reason for the change.

---

## EOL Policy

- All output CSVs (`railway/outputs/**/*.csv`) and the golden manifest are committed as **LF**.
- `.gitattributes` enforces `text eol=lf` for these files. git normalizes them on `add` and `checkout` regardless of the OS that wrote them.
- Never commit CRLF outputs. If `git diff` shows only `^M` differences, run `git add --renormalize` on the affected files and verify the diff is EOL-only before committing.
- CI (`ubuntu-latest`) produces LF natively; the `.gitattributes` rule ensures Windows developer machines produce the same bytes.
