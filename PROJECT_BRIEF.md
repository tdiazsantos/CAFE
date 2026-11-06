# CAFE development — project brief

Owner: Tanio Díaz-Santos. Started 2026-11-04.

## Goal
1. Bring my three CAFE versions (GOALS upstream, my fork, my local folder) into one checked, synchronised state, with **minimal** code changes and nothing reaching GOALS that I haven't approved line by line.
2. Freeze the old setup as legacy and continue in a clean workspace.
3. Develop CAFE further, starting with the speed of cube fitting.

## Repositories and folders
- **GOALS upstream:** https://github.com/GOALS-survey/CAFE. `master` @ `39e298b` (2026-06-08) at the start; `7299306` since 2026-11-06 (PR #99); `3147e2a` since 2026-11-06 (PR #100). Remote name `upstream`.
- **My fork:** https://github.com/tdiazsantos/CAFE. `master` @ `377cfef` (2025-02-10) at the start; `7299306` since 2026-11-06, then `3147e2a` (after PR #100), equal to GOALS `master`. Remote name `origin`.
- **Project folder (since the freeze, 2026-11-06):** `/Users/tanio/Sync/pywork/CAFE`, a fresh clone of my fork, with remotes `origin` and `upstream` (push to `upstream` disabled). Branch `dev` (from `master` @ `7299306`, also on my fork) holds the project and environment files.
- **Pre-sync folder (my old working copy):** `/Users/tanio/Sync/pywork/CAFE_presync_2026-11`, read only (CLAUDE.md §5). It was `/Users/tanio/Sync/pywork/CAFE` until the freeze.
  - At the start: branch `make_contparcube` @ `f50bd6e` (2024-04-05), with uncommitted edits. Both remotes are already configured.
  - Since 2026-11-04 my work in progress is committed on branch `local-wip-2026-11` (`135aa70`).
- **Tag `legacy-2026-11`** → `7299306`: the stable synced version (my fork's `master` = GOALS `master` after PR #99). It's on my fork.
- **Work folder:** `/Users/tanio/pywork/cafe_work`. Conda envs live in `~/miniforge3/envs`.
- **Data folders (read only):** `/Volumes/Gluon/lowz/goals/jwst/miri/mrs/data` and `/Volumes/Gluon/lowz/goals/jwst/nirspec/ifu/data`, one subfolder per galaxy (IIZw096, NGC3256, NGC7469, VV114). They hold pipeline `s3d` cubes, e.g. NGC7469 MIRI/MRS: the 12 sub-band GOALS HLSP v2.0 cubes. `cubemod` needs a CRETA cube made from them. The NGC7469 tutorial 1D spectrum is not in them (checked by name and content 2026-11-04), so it comes from the tutorial link (see "Commands").

## State at start (first comparison, 2026-11-04: verify, don't trust)
- Fork `master` is **0 commits ahead of and 6 behind** GOALS `master`. Every fork branch is already merged into GOALS. `f50bd6e` is contained in both remotes.
- The GOALS-only commits:
  - `e890795` `simps`→`simpson` (cafe_lib.py, dustgrainfunc.py), merged via PR #91 (`0567234`).
  - `09f5df6` `'gamma'`→`'width'` in the gauss/drude lists in cafe.py.
  - `d60a4be` `trapz`→`trapezoid` **plus a large reformat** of cafe_io.py, cafe_lib.py, component_model.py and sourceSED.py, merged via PR #95 (`c57673d`).
  - `39e298b` install docs.
- My local work that exists nowhere else is **uncommitted edits in 25 tracked files** (verified in M0; `git status` has the full list). They include:
  - code: `CAFE/cafe.py`, `cafe_helper.py`, `cafe_io.py`, `cafe_lib.py`, `dustgrainfunc.py`, `sourceSED.py`, `CRETA/creta.py`, `CRETA/cube_preproc.py`;
  - options and inputs: `opt_parfiles/default_opt.cafe`, `inp_parfiles/inpars_jwst_miri_SB.ini`;
  - tables: `tables/lines.atomic_SB.txt` and further line tables;
  - CRETA param files;
  - 7 compiled `CRETA/__pycache__/*.pyc` files, which changed only because the code was run.
- What the local edits contain:
  - flux normalisation in `cubemod.fit_cube`: new `norm_factor` argument and `scale_flux_params()`;
  - photometry weights (`calc_phot_weights`);
  - `phot_dict` passed to `get_model_fluxes` where component fluxes are computed;
  - removal of the deprecated `specmod.save_result`;
  - CRETA changes.
- Untracked files in the local folder fall into three groups:
  - object-specific inputs: W2246, CYGNUS, VV114, SPITZER, NGC7469 tests;
  - generic tables that may be worth upstreaming: `tables/resolving_power/R_JWST_MIRI_LRS.txt`, `R_SPITZER_IRS_{SL1,SL2,LL1,LL2}.txt`, and the `SPITZER_lines.*` tables;
  - clutter: editor backups (`*~`), Syncthing `.sync-conflict-*` files, `__pycache__`.

### Candidate issues to verify in M1 (from a first read, not a review)
1. Removed library functions:
   - fork `master` calls `scipy.integrate.simps` (removed in SciPy 1.14); local already uses `simpson`;
   - both fork and local call `np.trapz` (absent in recent NumPy 2.x);
   - so both fail on current library versions. GOALS master has fixed both.
2. Debugging leftovers (`ipdb`). Check all three versions:
   - local: module-level `import ipdb` in `cafe.py:28` and `cafe_lib.py:19`. That's an ImportError for anyone without ipdb, and it must not go upstream.
   - local: a live `ipdb.set_trace()` at `cafe_helper.py:304`, inside a bare `except:`, with its import commented out. Reaching it raises `NameError`.
   - GOALS master and fork: a live `ipdb.set_trace()` at `dustgrainfunc.py:247`, with its import commented out. Reaching that branch raises `NameError`.
3. The local `scale_flux_params` docstring says it scales `_FLX` and `_Peak` values, bounds and errors. The code scales only `_Peak` value and stderr. The inpars files describe `_FLX` as a flux *ratio* at the reference wavelength, so leaving `_FLX` unscaled may be correct. Check that, and check the `_Peak` bounds.
4. `cubemod.fit_cube(pattern=None)` passes `None` to `get_fit_sequence`, which handles only `'snr'` and `'spiral'`. Confirmed in isolation: it returns `None` for `None`, so the default call would fail when the result is unpacked. Check what callers actually pass.
5. `cafe_grinder`: the bare `except:` refers to `result`.
   - If `minimize` raises on the first iteration, `result` is undefined and an unrelated error is raised.
   - On refit iterations the previous `result` is silently reused.
6. `NPROC` is read from the options file but never used.
7. The cube "SNR image" that drives the fitting order is `nansum(flux[10:20])`, a flux sum over 10 channels, not an SNR.
8. GOALS `specmod.fit_spec` computes component fluxes without `phot_dict`. The local edits pass it. Check whether this matters when photometry is fitted.
9. specutils 2.x renamed `Spectrum1D` to `Spectrum` (the alias still exists). Check for deprecation warnings.
10. Packaging: `asdf` is imported but missing from `setup.py`, and `ipykernel` is listed as a runtime dependency. These are later-milestone items, not M1.

## Milestones

### M0 — Setup (no code changes)
1. Do this before anything else:
   - Create `.claude/settings.local.json` containing `{"attribution": {"commit": "", "pr": ""}}`, so no Claude attribution is added to commits or PRs (CLAUDE.md §2).
   - Add `.claude/`, `CLAUDE.md`, `PROJECT_BRIEF.md`, `DESIGN.md` and the environment files to `.git/info/exclude` in the pre-sync repo.
2. Check that `~/.claude/CLAUDE.md` is loaded (see CLAUDE.md §0).
3. GitHub, read-only checks: `gh auth status`, and `git ls-remote` on both remotes. Confirm my push rights on the fork and on GOALS **without pushing anything**.
4. Create the work folder and both conda envs with their environment files (CLAUDE.md §6). Python for `cafe-legacy`: propose a version (my local folder was last run with 3.11).
5. Smoke test: import CAFE and CRETA from GOALS master in `cafe-dev`, and from the fork and local versions in `cafe-legacy`. Download the NGC7469 tutorial spectrum (link in `notebooks/CAFE_tutorial_NGC7469_1D.ipynb`) directly into the work folder, not through astropy's download cache in `~/.astropy`.
6. Fill in "Commands" below.

**Exit:** wait for my go-ahead.

### M1 — Code comparison (no code changes)
M1 changes nothing in any code: no fixes, no porting, no edits, no tests, no fit runs (see "Decisions").

1. **Snapshot** *(done 2026-11-04)*. In the pre-sync repo, branch `local-wip-2026-11` (commit `135aa70`, parent `f50bd6e`) holds my 25 modified tracked files exactly as they were, including the 7 tracked `.pyc` files. No untracked files; not pushed.
2. **Comparison setup** *(done 2026-11-04)*. In the work folder: a clone of the fork at `cmp/fork-master` (fork master), with remotes `upstream` and `presync` (push disabled for both), and worktrees `cmp/goals-master` (GOALS master) and `cmp/local-wip` (`local-wip-2026-11`). Nothing was written into the pre-sync repo. The `presync` remote was called `legacy` and pointed to `/Users/tanio/Sync/pywork/CAFE` until the freeze (2026-11-06).
3. **Compare the `.py` files** of GOALS master, my fork and my local version: the diffs, read line by line. This includes the check that the `d60a4be` reformat changes no behaviour, by comparing ASTs after normalising the `trapz`/`simps` renames *(done 2026-11-04: identical)*.
4. **Report the differences, then STOP.** For each difference: what changed, and the findings on it (severity, file:line, evidence).

**Exit:** wait for my decision on what happens next. *(Decided 2026-11-05; the next steps are under "Decisions".)*

### Freeze (end of M1) *(complete 2026-11-06)*
Decided 2026-11-06 and corrected the same day. A new session follows step 4.

**Legacy** means the stable synced version, not my work in progress.

1. **Tag** *(done 2026-11-06)*.
   - Annotated tag `legacy-2026-11` on `7299306`: my fork's `master`, equal to GOALS `master` after PR #99. Tagger: me.
   - Pushed to my fork with my OK (tag object `81315ba`). Not on GOALS.
   - An earlier `legacy-2026-11` on `135aa70` (tag object `f75b678`) was deleted locally and on my fork, with my OK.
     - While it existed, `135aa70` was public on my fork.
     - GitHub may keep that commit reachable by its hash until it garbage-collects it.
   - No tag on `377cfef`: that state is already in the history.
2. **Work in progress** stays on branch `local-wip-2026-11` (`135aa70`) in the old folder. It's the source for M3. Pushed to my fork as a backup with my OK (2026-11-06). Not on GOALS.
3. **Rename and clone.** I do this myself, after closing the session in the old folder:
   ```
   mv /Users/tanio/Sync/pywork/CAFE /Users/tanio/Sync/pywork/CAFE_presync_2026-11
   git clone https://github.com/tdiazsantos/CAFE.git /Users/tanio/Sync/pywork/CAFE
   ```
4. **New session in `/Users/tanio/Sync/pywork/CAFE`.** I start it there. It reads this brief from `/Users/tanio/Sync/pywork/CAFE_presync_2026-11/PROJECT_BRIEF.md` until the copy below exists. *(Done 2026-11-06: `master` = `upstream/master` = `7299306`, tag `legacy-2026-11` (object `81315ba`) → `7299306`; `dev` pushed to my fork with my OK.)*
   1. Check that `~/.claude/CLAUDE.md` is loaded (CLAUDE.md §0).
   2. Add the GOALS remote and check the starting point: `git remote add upstream https://github.com/GOALS-survey/CAFE.git`, `git fetch upstream`.
      - `master` and `upstream/master` should both be at `7299306` (or later, if GOALS has moved).
      - The clone should have the tag `legacy-2026-11` → `7299306`.
   3. Create `dev` from `master`: `git switch -c dev master`.
   4. Copy from `/Users/tanio/Sync/pywork/CAFE_presync_2026-11`: `CLAUDE.md`, `PROJECT_BRIEF.md`, `DESIGN.md`, `environment-dev.yml`, `environment-legacy.yml` and `.claude/settings.local.json`. The settings file keeps Claude attribution off (see "Decisions").
   5. Add `.claude/` to `.git/info/exclude`. `.claude/` is not committed.
   6. Update this brief for the new layout:
      - the old working copy is now `/Users/tanio/Sync/pywork/CAFE_presync_2026-11`, read only (CLAUDE.md §5);
      - in the work-folder clone, point the `legacy` remote there, and rename it `presync`, since "legacy" now means the synced version:
        - `git -C /Users/tanio/pywork/cafe_work/cmp/fork-master remote set-url legacy /Users/tanio/Sync/pywork/CAFE_presync_2026-11`
        - `git -C /Users/tanio/pywork/cafe_work/cmp/fork-master remote rename legacy presync`
      - the "Commands" that use the old local path now use `CAFE_presync_2026-11`.
   7. Commit `CLAUDE.md`, `PROJECT_BRIEF.md`, `DESIGN.md` and both environment files on `dev`. Stage them by explicit path; my identity; no trailer.
   8. Ask before pushing `dev` to my fork.
   - `dev` contains the project files. Branches meant for GOALS therefore still start from `upstream/master`, never from `dev` (CLAUDE.md §2).

### M2 — Bugs in the synced version (GOALS) *(scope done 2026-11-06: PR #100 merged, fork `master` synced; physics decisions #6, #7, #11, #13 deferred)*
- Start only after my approval (CLAUDE.md §1).
- **First step once I approve M2:** list which bugs from the M1 report (`reports/M1_py_differences_2026-11-05.md` in the work folder) and from "Candidate issues to verify in M1" are in the synced version (`legacy-2026-11` = GOALS `master`), and which exist only in my local changes. *(Done 2026-11-06: `reports/M2_bug_list_2026-11-06.md` in the work folder, items #1–#18 = a1–a18. Scope decided the same day; see "Decisions".)*
- **Scope (2026-11-06):** fix #1, #2, #3, #4, #5 and #9 on one branch from `upstream/master`, one commit per fix. Tests stay in the work folder; the PR contains only the fixes. *(Fixes done 2026-11-06 on branch `m2-fixes-2026-11`, worktree `cmp/m2-fixes` in the work folder: 6 commits `151ea38`..`40cac7c` on `7299306`, 4 files, +17/−17. Checked by reading and the import smoke test. Full diff in `reports/M2_m2-fixes-2026-11.diff`. All 10 hunks approved line by line. Pushed to my fork with my OK. PR opened with my OK: https://github.com/GOALS-survey/CAFE/pull/100. I merged it on 2026-11-06 (merge commit `3147e2a`), and my fork's `master` was synced to it with my OK.)*
- Fix only bugs in the synced version. Each fix is minimal and tested: failing case, then fix, then test; synthetic data with known truth for physics and numerics (CLAUDE.md §3, personal rules).
- Then a PR to GOALS after my line-by-line review (CLAUDE.md §2). The PR description is a brief human summary of 2 or 3 sentences.
- No Claude co-authorship anywhere in M2: commits, PR title and PR description (CLAUDE.md §2).
- After I merge, sync my fork's `master` with GOALS again, and ask before pushing.

### M3 — My local changes
- Start only after my approval (CLAUDE.md §1).
- Covers the bugs that exist only in my local changes.
- Bring my local changes from `local-wip-2026-11` (`135aa70`, in the pre-sync folder) into `dev`, one at a time, each tested.
- The changes and the findings on each are in the M1 report. The 8 items merged in GOALS PR #99 are already in.
- Claude co-authorship may start here, only on commits that stay on my fork. Attribution in `.claude/settings.local.json` stays off until I approve M3 (CLAUDE.md §2).

### M4 — Cube-fit performance
- **Baseline:** time `cubemod.fit_cube` on a real cube (I choose which) and on a synthetic cube with known truth. Profile where the time goes:
  - per-spaxel parameter and profile regeneration;
  - table reading;
  - the number of lmfit function evaluations × the cost of `get_model_fluxes`;
  - refit loops;
  - I/O.
- **Then propose options with trade-offs. Plan first, no code.** Starting points from DESIGN.md:
  - cache the work that doesn't depend on the spaxel (tables, grain emissivities and opacities, `waveMod`) and recompute only the flux-dependent parts (`flux0`);
  - use `NPROC` to parallelise spaxels while keeping the neighbour-initialisation order from `get_fit_sequence`;
  - make `get_model_fluxes` cheaper.
- **Acceptance:** results identical to the baseline within approved tolerances, plus a measured speed-up. A speed-up that changes results is a physics decision for me (CLAUDE.md §4).

### Later (do not start)
- Tests and CI.
- Packaging: pyproject-only, correct dependencies.
- Logging instead of `print`.
- Removing dead and commented-out code.
- Spitzer IRS and MIRI LRS support.
- Docs.

## Commands
All verified 2026-11-04 (M0). `conda`, `mamba` and `gh` are in `~/miniforge3/bin`, which is not on the default PATH. The `env VAR=… cmd` form works in both tcsh and zsh.

**GitHub, read-only checks**
```
~/miniforge3/bin/gh auth status
git -C /Users/tanio/Sync/pywork/CAFE ls-remote origin
git -C /Users/tanio/Sync/pywork/CAFE ls-remote upstream
~/miniforge3/bin/gh api repos/tdiazsantos/CAFE --jq .permissions
~/miniforge3/bin/gh api repos/GOALS-survey/CAFE --jq .permissions
```

**Environments** (run from the work folder; the environment files are on branch `dev`)
```
cd /Users/tanio/pywork/cafe_work
~/miniforge3/bin/mamba env create -f /Users/tanio/Sync/pywork/CAFE/environment-dev.yml -y
~/miniforge3/bin/mamba env create -f /Users/tanio/Sync/pywork/CAFE/environment-legacy.yml -y
```
scikit-learn (2026-11-04). It is now in both env files, so a fresh `env create` includes it. In the existing envs:
```
~/miniforge3/bin/mamba install -y -n cafe-dev --override-channels -c conda-forge scikit-learn
```
`cafe-legacy` already had scikit-learn 1.9.1, as a dependency of conda-forge's photutils 1.10.0 build. The env file now pins it. A dry-run `env create` from each file resolves to exactly the installed versions of every package listed below.

Resolved versions:
- `cafe-dev`: python 3.12.16, numpy 2.5.4, scipy 1.18.1, astropy 8.0.2, specutils 2.4.0, photutils 3.1.1, lmfit 1.3.4, matplotlib 3.11.2, pandas 3.1.1, asdf 6.0.0, scikit-learn 1.9.1.
- `cafe-legacy`: python 3.11.18, numpy 1.26.2, scipy 1.11.4, astropy 6.0.0, specutils 1.12.0 (pip), photutils 1.10.0, lmfit 1.2.2, matplotlib 3.8.2, pandas 2.1.3, asdf 3.0.1, gwcs 0.20.0, asdf-astropy 0.5.0, ndcube 2.2.0, scikit-learn 1.9.1, ipdb 0.13.13.

Check that scikit-learn works in an env (the call CRETA makes; known truth: slope 3, intercept 2). Replace `<env>` by `cafe-dev` or `cafe-legacy`:
```
~/miniforge3/envs/<env>/bin/python -c "import numpy as np; from sklearn.linear_model import LinearRegression as L; x=np.arange(10.)[:,None]; m=L().fit(x,3*x[:,0]+2); print(m.coef_[0], m.intercept_)"
```
Result 2026-11-04: slope 3 and intercept 2 to within 1e-14 in both envs (rounding error only). `pip check`: clean in `cafe-dev`; in `cafe-legacy` only the `imagecodecs` note (see "Biases").

**M0 smoke-test snapshots** (read-only export from the pre-sync repo; M1.2 replaces them with worktrees)
```
mkdir -p /Users/tanio/pywork/cafe_work/smoke/goals-master-39e298b /Users/tanio/pywork/cafe_work/smoke/fork-master-377cfef
git -C /Users/tanio/Sync/pywork/CAFE_presync_2026-11 archive 39e298b | tar -x -C /Users/tanio/pywork/cafe_work/smoke/goals-master-39e298b
git -C /Users/tanio/Sync/pywork/CAFE_presync_2026-11 archive 377cfef | tar -x -C /Users/tanio/pywork/cafe_work/smoke/fork-master-377cfef
```

**Smoke test: import every CAFE and CRETA module** (`scripts/smoke_import.py` in the work folder; exit status = number of failed imports)
```
cd /Users/tanio/pywork/cafe_work
env PYTHONDONTWRITEBYTECODE=1 MPLBACKEND=Agg PYTHONPATH=/Users/tanio/pywork/cafe_work/smoke/goals-master-39e298b ~/miniforge3/envs/cafe-dev/bin/python scripts/smoke_import.py /Users/tanio/pywork/cafe_work/smoke/goals-master-39e298b
env PYTHONDONTWRITEBYTECODE=1 MPLBACKEND=Agg PYTHONPATH=/Users/tanio/pywork/cafe_work/smoke/fork-master-377cfef ~/miniforge3/envs/cafe-legacy/bin/python scripts/smoke_import.py /Users/tanio/pywork/cafe_work/smoke/fork-master-377cfef
env PYTHONDONTWRITEBYTECODE=1 MPLBACKEND=Agg PYTHONPATH=/Users/tanio/Sync/pywork/CAFE_presync_2026-11 ~/miniforge3/envs/cafe-legacy/bin/python scripts/smoke_import.py /Users/tanio/Sync/pywork/CAFE_presync_2026-11
```
Result 2026-11-04, re-run after adding scikit-learn: 18/18 modules import in each of the three (the CAFE and CRETA packages plus 9 and 7 modules; first reported as 19 by miscount, corrected 2026-11-05), and the script also imports and prints `sklearn` 1.9.1. The only warnings are the `'\,'` escapes (see "Biases"). Output is in `logs/smoke_{goals-master,fork-master,local}.txt` in the work folder. `PYTHONDONTWRITEBYTECODE=1` keeps `__pycache__` out of the checkouts; the repo's `git status` was identical before and after. Re-run 2026-11-06 on the pre-sync path: 18/18, output identical to `logs/smoke_local.txt` apart from the path, pre-sync `git status` unchanged.

**Smoke test on the sync branch** (step 2, only to catch typos from the rewrite; worktree `cmp/sync-local` in the work folder)
```
cd /Users/tanio/pywork/cafe_work
env PYTHONDONTWRITEBYTECODE=1 MPLBACKEND=Agg PYTHONPATH=/Users/tanio/pywork/cafe_work/cmp/sync-local ~/miniforge3/envs/cafe-dev/bin/python scripts/smoke_import.py /Users/tanio/pywork/cafe_work/cmp/sync-local
```
Result 2026-11-05: 18/18 import, 0 failed. The output is identical to the GOALS master run apart from the path (`logs/smoke_sync-local.txt`).

**Smoke test on the M2 fix branch** (worktree `cmp/m2-fixes` in the work folder; removed 2026-11-06 after the merge)
```
cd /Users/tanio/pywork/cafe_work
env PYTHONDONTWRITEBYTECODE=1 MPLBACKEND=Agg PYTHONPATH=/Users/tanio/pywork/cafe_work/cmp/m2-fixes ~/miniforge3/envs/cafe-dev/bin/python scripts/smoke_import.py /Users/tanio/pywork/cafe_work/cmp/m2-fixes
```
Result 2026-11-06: 18/18 import, 0 failed. The output is identical to `logs/smoke_sync-local.txt` apart from the path (`logs/smoke_m2-fixes.txt`).

**NGC7469 tutorial spectrum** (link from `notebooks/CAFE_tutorial_NGC7469_1D.ipynb`; tutorial uses z = 0.0163)
```
mkdir -p /Users/tanio/pywork/cafe_work/data/NGC7469
curl -fsSL -o /Users/tanio/pywork/cafe_work/data/NGC7469/NGC7469_SingleExt_r1.5as_MIRI.dat 'https://caltech.box.com/shared/static/u12th7dvkvu2iiv73r77c45lnn58sgvh.dat'
shasum -a 256 /Users/tanio/pywork/cafe_work/data/NGC7469/NGC7469_SingleExt_r1.5as_MIRI.dat
```
324,989 bytes, 9,695 rows × 3 columns (wavelength 4.957–28.603 µm observed, flux, uncertainty), sha256 `e317901ca755f853008a2abc05bdd5ce4a2d88cd4f4135da04e464783436dc16`.

## Decisions & biases
All entries are dated. Record a decision only after I approve it. Log biases as soon as you notice them. List defaults that still need my OK under "Awaiting my OK".

### Decisions (approved)
- 2026-11-04: The milestones are M0 setup, M1 check + sync + freeze, M2 cube-fit performance, and the rest later. *(Superseded 2026-11-06; see below.)*
- 2026-11-04: M1 code changes are minimal. Nothing goes to GOALS without my line-by-line approval and an explicit OK. Changes go upstream only as a PR from my fork.
- 2026-11-04: Until M1 is complete, everything pushed to my fork or to GOALS is authored by me alone, with no Claude attribution. Co-authorship starts with M2 in the new folder. *(Superseded 2026-11-06; see "Claude co-authorship" below.)*
- 2026-11-04: There are two envs: `cafe-dev` (Python 3.12, current stack) and `cafe-legacy` (numpy<2, scipy<1.14).
- 2026-11-04: `cafe-legacy` uses Python 3.11 and the package versions of the old `/usr/local/anaconda3/envs/cafe_env` (the local version's last env). specutils 1.12.0 comes from pip, because conda-forge doesn't have it.
- 2026-11-04: scikit-learn goes into an env only if a version needs it at import time. None does (CRETA imports it inside functions), so neither env has it. (Superseded the same day; see below.)
- 2026-11-04: `ipdb` is installed in `cafe-legacy` only, so the local version imports unchanged. It is not in `cafe-dev` and not a code dependency.
- 2026-11-04: scikit-learn is installed in both envs, because the M1 CRETA extraction calls it at run time. In `cafe-legacy`, use the version from the old `cafe_env` if it had one; otherwise use one compatible with its pins. This is an env change only, not a code dependency. It replaces the sklearn entry above.
- 2026-11-04: The M1.1 snapshot includes the 7 tracked `CRETA/__pycache__/*.pyc` files, so the legacy snapshot is exact.
- 2026-11-04: Tools may write to the system temp folder and to their own caches (CLAUDE.md §5).
- 2026-11-04: M1 scope is the `.py` files only: compare, review and port only those. My local changes to tables, inpars/opt files and CRETA param files stay personal and are not upstream candidates unless I say otherwise. Regression runs use GOALS master's tables and input files for every version: `cafe_dir`, the inpars file and the opt file all come from the GOALS master checkout, whatever code is on `PYTHONPATH`. So the differences reflect code only. If a local `.py` edit needs my modified tables or input files to work, flag it instead of switching. (The regression part of this entry no longer applies; see the next entry.)
- 2026-11-04: M1 is a code comparison only: diffs and line-by-line reading of the `.py` files, plus the AST check that the GOALS reformat changes no behaviour (it compares code without running it). No tests and no fit runs: step 6 (regression runs) and the re-run in step 8 are dropped. Every bug fix needs a test (personal rule), so M1 makes no bug fixes; bugs are reported as findings for a later milestone. The only edits allowed in M1 are ports of my approved local `.py` changes, without the debugging leftovers. (Superseded the same day; see the next entry.)
- 2026-11-04: M1 changes nothing in any code: no fixes, no porting, no edits, no tests, no fit runs. M1 now means: show me the differences in the `.py` files between GOALS master, my fork and my local version, with findings on each difference, then stop. I decide what happens next. This replaces M1 steps 3 and 5–11 and the earlier M1 entries above; the snapshot (step 1), the comparison setup (step 2) and the AST check of the GOALS reformat (step 4) are done.
- 2026-11-05: After the M1 differences report (`reports/M1_py_differences_2026-11-05.md` in the work folder), in this order:
  1. **Now:** fast-forward my fork's `master` to GOALS `master`. Show me what will be pushed and ask before pushing. Then stop. *(Done 2026-11-05: fork `master` `377cfef`→`39e298b`, fast-forward, pushed with my OK.)*
  2. **Next, after my OK:**
     - Make a separate branch from GOALS `master` (e.g. `sync-local-2026-11`), not from my fork's `master`.
     - Put on it my local small real fixes plus three no-effect changes, and nothing else:
       - fixes: `waveOpt` sorting, `float32` contcube wavelengths, the hidden-file filter in `read_inst`, and the two `sourceSED` fixes;
       - no-effect changes: `phot_dict` passed to `get_model_fluxes`, `w.celestial` in CRETA, and the `save_result` removal.
     - Write edits to reformatted files in GOALS's layout. Remove the debugging leftovers rather than commenting them out.
     - Show me the full diff for line-by-line review.
     - With my OK, push the branch to my fork.
     - With my OK, open the PR from that branch to GOALS. I approve and merge it myself on GitHub; never merge on GOALS.
     - After I merge, bring my fork's `master` up to GOALS again (ask before pushing).
  3. **Later:** the not-ready items (`norm_factor`, `calc_phot_weights`), the GOALS bugs, and tests of my code.
- 2026-11-06: I approved all 11 hunks of `sync-local-2026-11` line by line: 8 commits `fd50066`..`c086c34` on top of GOALS `master` `39e298b`, in 5 files (`cafe.py`, `cafe_helper.py`, `cafe_io.py`, `sourceSED.py`, `CRETA/cube_preproc.py`). Any later change to the branch must be shown to me again.
- 2026-11-06: `sync-local-2026-11` pushed to my fork with my OK (tip `c086c34`). Before the PR is opened, show me its exact title and description for review.
- 2026-11-06: PR opened with my OK and my own title and text: https://github.com/GOALS-survey/CAFE/pull/99, "Small (inconsequential) fixes", `tdiazsantos:sync-local-2026-11` @ `c086c34` → GOALS `master` (`39e298b`). 8 commits, 5 files, +11/−57. GitHub reports it mergeable and shows no CI checks. Its text is in `reports/PR_sync-local-2026-11_body.md` in the work folder. Later the same day, with my OK, I changed one phrase in the description: "is handled in the helper" → "is written elsewhere". I merge it myself on GitHub; never merge, approve or close anything on GOALS. Next: after my merge, bring my fork's `master` up to GOALS again, and ask before pushing.
- 2026-11-06: I merged PR #99 on GitHub (09:52 UTC, merge commit `7299306`, parents `39e298b` + `c086c34`) and deleted the fork branch `sync-local-2026-11`. GOALS `master` is now `7299306`, and its file tree is identical to the approved `c086c34`. Next: fast-forward my fork's `master` to `7299306`, asking before pushing.
- 2026-11-06: Step 2 is complete:
  - My fork's `master` went `39e298b`→`7299306` (fast-forward, pushed with my OK), so fork `master` = GOALS `master` = `7299306`.
  - With my OK, the work-folder clone was cleaned up: the worktree `cmp/sync-local`, the local branch `sync-local-2026-11` (deleted with `git branch -d` after setting its upstream to `origin/master`, which contains it; no force) and the stale `origin/sync-local-2026-11` ref.
  - The comparison worktrees `cmp/fork-master` (local `master` @ `377cfef`), `cmp/goals-master` (`39e298b`) and `cmp/local-wip` (`135aa70`) stay as they were. They show the pre-sync state.
  - Next: the freeze. I start it.
- 2026-11-06: The live `ipdb.set_trace()` at `dustgrainfunc.py:247` (GOALS master) stays out of this PR. It goes on the later bug list.
- 2026-11-05: The authorship rule (CLAUDE.md §2) applies to commits made in this project. Commits by GOALS contributors that arrive unchanged (e.g. through a fast-forward) are not covered by it.
- 2026-11-05: **Exception to the testing rule, for step 2 only.** Port the listed fixes to `sync-local-2026-11` without tests now; the tests come after the sync, as decided above. Before showing the diff, re-run the existing M0 import smoke test on the branch, only to catch typos from the rewrite.
- 2026-11-05: Keep the old run outputs in the work folder (`runs/m1_1d`, `runs/m1_1d_gi`, `runs/creta_grid`, `data/NGC7469/creta_grid3x3`, `scratch/`).
- 2026-11-04: The work folder is `/Users/tanio/pywork/cafe_work`.
- 2026-11-04: The freeze happens at the end of M1. Tag `legacy-2026-11`, old folder → `CAFE_legacy`, new clone at `/Users/tanio/Sync/pywork/CAFE`, branch `dev`. *(Details superseded 2026-11-06; see below.)*
- 2026-11-06: **Freeze plan** (steps in "Milestones → Freeze"): *(The tag target and folder name were corrected the same day; see "Freeze corrections" below.)*
  - One tag, `legacy-2026-11`, on `135aa70` (the local snapshot). The earlier plan for a tag on `377cfef` is dropped; that state is already in the history.
  - I rename the folder to `CAFE_legacy` and clone my fork to `/Users/tanio/Sync/pywork/CAFE`.
  - In a new session there: add `upstream`, create `dev` from `master`, and copy the project files, both environment files and `.claude/settings.local.json` from `CAFE_legacy`.
  - The project and environment files are committed on `dev`; `.claude/` is not. Ask before pushing `dev` to my fork.
- 2026-11-06: Tag `legacy-2026-11` (on `135aa70`) pushed to my fork with my OK. Only `135aa70` was newly published; I am its author, and there are no trailers. *(That tag was deleted the same day; see below.)*
- 2026-11-06: **Milestones after the freeze:** *(Superseded the same day; see below.)*
  - M2 brings my remaining local changes from `legacy-2026-11` into `dev` one at a time, each with tests.
  - M3 is cube-fit performance (previously M2).
  - Later items unchanged.
- 2026-11-06: **Freeze corrections** (replace the tag and folder parts above):
  - **Tag.** "Legacy" means the stable synced version, not my work in progress.
    - `legacy-2026-11` on `135aa70` was deleted locally and on my fork, with my OK.
    - `legacy-2026-11` was recreated on `7299306` (my fork's `master` = GOALS `master`) and pushed to my fork, with my OK. Tag object `81315ba`, tagger me, no trailers; the push published no new commits.
  - **Work in progress** stays on branch `local-wip-2026-11` (`135aa70`) in the old folder. It's the source for M3.
  - **Folder.** The old folder is renamed `CAFE_presync_2026-11`, not `CAFE_legacy`. The folder line in CLAUDE.md §5 was updated with my permission.
- 2026-11-06: **Milestones after the freeze** (replace the entry above):
  - M2: bugs in the synced version (GOALS) only. Each fix minimal and tested, then a PR to GOALS after my line-by-line review. After I merge, sync my fork's `master` with GOALS again.
  - M3: the bugs that exist only in my local changes, and bringing my local changes from `local-wip-2026-11` into `dev` one at a time, each tested.
  - M4: cube-fit performance.
  - When I approve M2, start by listing which bugs from the M1 report and the candidate list are in the synced version, and which exist only in my local changes.
- 2026-11-06: **Claude attribution stays off** until I decide whether commits going to GOALS may show Claude as co-author. This overrides "co-authorship starts with M2" (the 2026-11-04 entry above and CLAUDE.md §2) until then. *(Decided 2026-11-06; see "Claude co-authorship" below.)*
- 2026-11-06: Branch `local-wip-2026-11` (`135aa70`) pushed to my fork as a backup, with my OK. Only `135aa70` was newly published; I am its author, and there are no trailers.
- 2026-11-06: **CLAUDE.md edits**, with my permission:
  - §2: the co-authorship sentence now says attribution stays off after the freeze until I decide about GOALS commits.
  - §2 and §5: "legacy folder" / "legacy working copy" → "pre-sync folder".
  - §5: the old folder line now reads `CAFE_presync_2026-11`.
  - The `cafe-legacy` env and `environment-legacy.yml` keep their names; they refer to the old library versions.
- 2026-11-06: **Freeze complete.**
  - The new clone has branch `dev` with 3 commits on `7299306`: the project files, the environment files, and this brief updated for the new layout (tip `5812048`). Pushed to my fork with my OK. Only those 3 commits were newly published; I am their author, and there are no trailers.
  - With my OK, push to `upstream` is disabled in the project clone, as in the work-folder clone: `git remote set-url --push upstream DISABLED-no-push-to-GOALS`. PRs from my fork are the only route to GOALS. Fetch from `upstream` still works.
  - Next: M2, which waits for my approval.
- 2026-11-06: **Claude co-authorship** (replaces "Claude attribution stays off" and the co-authorship part of the 2026-11-04 entry above):
  - No Claude co-authorship on anything that goes to GOALS, ever: commits, PR titles and PR descriptions. This includes M2.
  - Claude co-authorship may start in M3, and only on commits that stay on my fork.
  - If a change made with co-authorship later goes to GOALS, the commits for the GOALS PR are made fresh from `upstream/master` without any Claude trailer, and every commit is checked before pushing.
  - Attribution stays off in `.claude/settings.local.json` until I approve M3.
  - CLAUDE.md §2 updated to match, with my permission: the settings sentence and the pre-push check, plus a new "Claude co-authorship after M1" rule.
- 2026-11-06: **M2 approved.**
  - First step only: list the bugs from the M1 report and the candidate list, sorted into (a) bugs in the synced version (GOALS) and (b) bugs only in my local changes. For each (a) bug: file:line, what goes wrong, and when it happens in normal use. Then stop for my review. No fixes yet.
  - Any later PR to GOALS: the description is a brief human summary of 2 or 3 sentences, and there is no Claude co-authorship anywhere.
- 2026-11-06: **M2 scope** (numbers as in `reports/M2_bug_list_2026-11-06.md`):
  - Fix now, each minimal and tested, one commit each:
    - #1 `np.NaN` in CRETA;
    - #2 `fit_cube`'s default `pattern`, set to `'snr'`, the default `get_fit_sequence` already uses;
    - #4 `read_spec`'s `wave_min` / `wave_max`;
    - #9 CRETA's trailing-slash handling.
  - Also fix:
    - #3 a spaxel hitting `max_nfev` must not stop the cube: warn clearly, keep lmfit's result for that spaxel, and continue;
    - #5 `plot_cafefit` reads `'gamma'`, the key `save_asdf` writes.
  - Physics decisions for later, not in this PR: #6, #7, #11, #13.
  - Later: #8, #10, #12, #14, #16, #17, #18. #15 (`NPROC`) goes to M4.
  - Work on a branch from `upstream/master`, then show me the full diff for line-by-line review. Tests stay in the work folder; the PR contains only the fixes. Don't push.
- 2026-11-06: **M2 diff review.**
  - I approved hunks 1–4 and 6–10 (#1, #2, #4, #5, #9) line by line.
  - For #3 (hunk 5), I asked for a smaller change: delete only the `raise` line and keep `acceptFit = False`. The existing refit loop then retries and, after `MAX_LOOPS`, prints its own "fitting was unsuccessful" message and continues.
  - The branch was rebuilt to keep one commit per fix: `8776826` is the new #3, and #4, #5 and #9 were re-applied unchanged (same patch IDs) as `e78de07`, `268e816` and `c76dcb2`. The old tip was `ae27e19`.
  - Then, for #3: replace the `raise` line with a print of the same message, starting with "WARNING: ", and keep `acceptFit = False` so the retry loop runs as before. The branch was rebuilt again: `a0c8cf5` is the new #3, and #4, #5 and #9 are `c6d6245`, `7221d60` and `40cac7c` (same patch IDs). The previous tip was `c76dcb2`.
  - I approved the new hunk 5. **All 10 hunks of `m2-fixes-2026-11` are now approved line by line:** 6 commits `151ea38`..`40cac7c` on GOALS `master` `7299306`, in 4 files (`cafe.py`, `creta.py`, `cube_handler.py`, `userAPI.py`). Any later change to the branch must be shown to me again.
- 2026-11-06: `m2-fixes-2026-11` pushed to my fork with my OK (tip `40cac7c`). Only its 6 approved commits were newly published; I am their author, and there are no trailers. PR text, mine:
  - Title: "Additional small fixes to CAFE and CRETA".
  - Description: in `reports/PR_m2-fixes-2026-11_body.md` in the work folder.
  - Before opening the PR to GOALS, ask "Open PR m2-fixes-2026-11 → GOALS-survey/CAFE?" and wait for a clear yes. I merge it myself on GitHub.
- 2026-11-06: **PR opened** with my OK: https://github.com/GOALS-survey/CAFE/pull/100, "Additional small fixes to CAFE and CRETA", `tdiazsantos:m2-fixes-2026-11` @ `40cac7c` → GOALS `master` (`7299306`).
  - 6 commits, 4 files, +17/−17. Its description is identical to my text. There is no Claude attribution anywhere.
  - GitHub reports it mergeable and shows no CI checks.
  - I merge it myself on GitHub; never merge, approve or close anything on GOALS.
  - Next: after my merge, bring my fork's `master` up to GOALS again, asking before pushing.
- 2026-11-06: `dev` pushed to my fork with my OK (`52ba88a`→`819b503`, 8 commits, `PROJECT_BRIEF.md` only, no trailers).
- 2026-11-06: **Branch names** describe their content, not our milestones (e.g. `GOALS-fixes-2026-11`, not `m2-fixes-2026-11`). This applies from now on. `m2-fixes-2026-11` keeps its name, because renaming it would close PR #100.
- 2026-11-06: **PR #100 merged.**
  - I merged it on GitHub at 13:52 UTC: merge commit `3147e2a`, parents `7299306` + `40cac7c`.
  - GOALS `master` is now `3147e2a`, and its file tree is identical to the approved `40cac7c`.
  - The merge commit's message says "from tdiazsantos/GOALS-fixes-2026-11". The PR's head branch was `m2-fixes-2026-11`, and it is no longer on my fork.
  - The local `master` in the project clone was fast-forwarded to `3147e2a`; that is local only.
  - Next:
    - fast-forward my fork's `master` `7299306`→`3147e2a`, asking before pushing; only the merge commit is new to the fork;
    - after that, M2's scope is done, and M3 waits for my approval.
  - Still in place:
    - the local branch `m2-fixes-2026-11`, which tracks the deleted `origin/m2-fixes-2026-11`;
    - its worktree `cmp/m2-fixes` in the work folder.
    Removing them needs my OK.
  - *(All done the same day; see the next entry.)*
- 2026-11-06: **M2 sync and clean-up**, each step with my OK:
  - My fork's `master` went `7299306`→`3147e2a` (fast-forward), so fork `master` = GOALS `master` = `3147e2a`. Only the merge commit was new to the fork.
  - `dev` went `819b503`→`f398f51`: `dd55cc1` (branch naming) and `f398f51` (merge record).
  - The worktree `cmp/m2-fixes` was removed (it was clean). The local branch `m2-fixes-2026-11` was deleted with `git branch -d` (no force); it is contained in `master`.
  - The stale remote-tracking ref `origin/m2-fixes-2026-11` was removed with `git branch -d -r`. No other stale refs are left.
  - M2's scope is done. M3 waits for my approval.
- 2026-11-06: **Exception to the testing rule, for the six M2 fixes only.** They are evident fixes: check them by reading and the import smoke test only, with no data tests.
  - Before this, a few data tests had started. They stay in the work folder:
    - `tests/m2/test_numpy_attrs.py`, a static scan for NumPy attributes that the installed NumPy lacks: 4 hits before #1 (the `np.NaN` lines), 0 after;
    - `tests/m2/run_creta_grid.py`, run once on the unfixed branch, where it failed at `creta.py:867` as expected;
    - logs in `tests/m2/logs`, and the empty output folder `tests/m2/out/t1_grid_before`.

### Awaiting my OK
- How attribution is turned on once I approve M3. `.claude/settings.local.json` applies to every commit and PR made from this folder, so a commit trailer would also land on commits for GOALS branches, and PR attribution on PRs to GOALS.
- Which real cube is the M4 benchmark (cube-fit performance).

### Biases and small issues flagged
- 2026-11-04: The repo lives inside a Syncthing folder, which already has `.sync-conflict` files. A sync in the middle of a git operation could corrupt `.git`. Not acted on.
- 2026-11-04: The cube fitting order uses a flux sum as its "SNR" (candidate issue 7), which favours bright spaxels over high-SNR ones. Not acted on.
- 2026-11-04: `read_spec` writes `./dummy.fits` into the current directory.
- 2026-11-04: GOALS `master` is not branch-protected (GitHub API: `protected: false`), and I have push rights there. A stray `git push upstream` would land directly. Not acted on. *(2026-11-06: push to `upstream` is now disabled in the project clone and the work-folder clone. The read-only pre-sync repo still has a live `upstream` push URL, and a push that names the GOALS URL directly would still go through.)*
- 2026-11-04: GOALS has open PRs that may overlap the M1 sync PR: #98 (hexagon aperture for extraction, 2026-10-24), #93 (draft, YAML conversion), #56 (PAH EQW), #47 (tutorial notebook). Not acted on.
- 2026-11-04: `cafe-legacy` runs Python 3.11.18, not the old 3.11.5 (patch release only). The old env was x86_64; this Mac is arm64. Not acted on.
- 2026-11-04: In `cafe-legacy`, `pip check` reports that `imagecodecs` 2026.3.6 requires numpy>=2. It arrives via photutils 1.10.0 → scikit-image → tifffile, and it imports fine with numpy 1.26.2. A metadata mismatch only. Not acted on.
- 2026-11-04: Invalid escape sequence `'\,'` in strings: GOALS `cafe_lib.py:1499–1514` (SyntaxWarning on 3.12), fork `cafe_lib.py:1137–1140`. A future Python will make this an error. For a later milestone.
- 2026-11-04: scikit-learn is used in `CRETA/cube_handler.py:323,612` (all three versions) but is missing from `setup.py`. For the packaging milestone.
- 2026-11-04: Correction to an M0 statement. `cafe-legacy` has had scikit-learn 1.9.1 since it was created, because conda-forge's photutils 1.10.0 build requires `scikit-learn>=1.0`. So the first sklearn decision's "neither env has it" was wrong for `cafe-legacy`. The old `cafe_env` (pip-installed photutils) had no scikit-learn.
- 2026-11-06: After a `git stash` / `git stash pop` in the worktree `cmp/m2-fixes`, its index was empty: every file was listed as deleted and untracked. No data was lost. The working tree matched the stash byte for byte, and the commits were intact. `git read-tree HEAD` rebuilt the index. The cause is unknown; the worktree's git data lives in the Syncthing-synced `.git` (see the first entry). `git stash` is no longer used here.
- 2026-11-06: `CRETA/cube_handler.py:129` (`self.delta_factor_list * len(self.rs)`) throws its result away, the same pattern as #9. It has no effect, because `delta_factor_list` is never read. For the dead-code clean-up under "Later".
- 2026-11-06: The CRETA `.py` files have CRLF line endings, while the CAFE files have LF. The M2 edits keep each file's endings.
