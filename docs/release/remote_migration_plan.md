# Remote Migration Plan (STEP33 safety requirement #3)

**Date:** 2026-06-08 · **STATUS: PLAN ONLY — remotes NOT modified, nothing pushed. Await explicit approval.**

---

## 1. Ownership mismatch detected
| | Value |
|---|---|
| **Current origin** | `https://github.com/vivasvana1/SparePartsInventory.git` |
| **Intended owner** | `https://github.com/uppukarthik-code/` |
| **Match?** | ❌ **NO** — origin points to `vivasvana1`, not `uppukarthik-code` |

Per safety requirement #3, this **stops any push/remote modification**. STEP33 is preparation-only and performs no push regardless; the migration below executes only at the future push stage (STEP35), after explicit approval.

## 2. Target remote
A repository must exist under the intended owner, e.g.:
```
https://github.com/uppukarthik-code/railway-inventory-planning-platform.git
```
(exact name TBD by owner — suggest `railway-inventory-planning-platform` for the v1.0 identity.)

## 3. Migration commands (DO NOT RUN until approved — STEP35)
```bash
# 0. Confirm you own/can-push to the target repo (create empty repo on GitHub first, PRIVATE).
# 1. Inspect current remotes
git remote -v

# 2a. Option A — repoint origin (single canonical remote)
git remote set-url origin https://github.com/uppukarthik-code/railway-inventory-planning-platform.git

# 2b. Option B — keep old as 'upstream', add new origin (safer, dual-remote)
git remote rename origin upstream
git remote add origin https://github.com/uppukarthik-code/railway-inventory-planning-platform.git

# 3. Push the purified branch (NOT main) first, PRIVATE repo
git push -u origin repository-purification

# 4. Open PR repository-purification -> main ON THE NEW REMOTE; review; merge there.
# 5. Tag v1.0 ONLY after merge + green CI (STEP36).
```

## 4. Branch strategy
- All STEP33 work stays on `repository-purification` (no commits to `main`/`master`).
- Migration pushes `repository-purification` to the **new** origin first; `main` is updated only via reviewed PR on the new remote.
- The old `vivasvana1` remote is retained as `upstream` (Option B) for traceability, or dropped (Option A) once migration is confirmed.

## 5. Risks
| Risk | Mitigation |
|---|---|
| Pushing private railway/procurement data to wrong/public repo | Target must be **PRIVATE**; verify owner before push (Phase J) |
| Overwriting an existing repo | Create a fresh empty target repo; push branch (not force) |
| Losing provenance to original repo | Keep old remote as `upstream` (Option B) |
| Large untracked data accidentally pushed | Purify + `.gitignore` first (STEP33), so 2.4 GB Walmart data never enters history |
| Credentials/visibility | Confirm GitHub auth for `uppukarthik-code`; keep repo private until Phase J clears public release |

## 6. Recommendation
**Do not migrate remotes or push during STEP33.** Resolve ownership and create the PRIVATE target repo under `uppukarthik-code` out-of-band; execute §3 (Option B) only at STEP35 after explicit approval. Until then `origin` is left **unchanged**.
