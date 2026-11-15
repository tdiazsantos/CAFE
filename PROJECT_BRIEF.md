# CAFE development — project brief

Owner: Tanio Díaz-Santos. Started 2026-11-04.

## Goal
1. Bring my three CAFE versions (GOALS upstream, my fork, my local folder) into one checked, synchronised state, with **minimal** code changes and nothing reaching GOALS that I haven't approved line by line.
2. Freeze the old setup as legacy and continue in a clean workspace.
3. Develop CAFE further, starting with the speed of cube fitting.

## Repositories and folders
- **GOALS upstream:** https://github.com/GOALS-survey/CAFE. `master` @ `39e298b` (2026-06-08) at the start; `7299306` since 2026-11-06 (PR #99); `3147e2a` since 2026-11-06 (PR #100); `788be50` since 2026-11-06 (PR #101); `ca10c84` since 2026-11-06 (PR #102). Remote name `upstream`.
- **My fork:** https://github.com/tdiazsantos/CAFE. `master` @ `377cfef` (2025-02-10) at the start; `7299306` since 2026-11-06, then `3147e2a` (after PR #100), then `788be50` (after PR #101), then `ca10c84` (after PR #102), equal to GOALS `master`. Remote name `origin`.
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

### M2 — Bugs in the synced version (GOALS) *(first round done 2026-11-06: PR #100 merged, fork `master` synced; physics decisions #6, #7, #11, #13 deferred. Second round done 2026-11-06: PR #101 merged. Last round: PR #102 merged 2026-11-06. **M2 done.**)*
- Start only after my approval (CLAUDE.md §1).
- **First step once I approve M2:** list which bugs from the M1 report (`reports/M1_py_differences_2026-11-05.md` in the work folder) and from "Candidate issues to verify in M1" are in the synced version (`legacy-2026-11` = GOALS `master`), and which exist only in my local changes. *(Done 2026-11-06: `reports/M2_bug_list_2026-11-06.md` in the work folder, items #1–#18 = a1–a18. Scope decided the same day; see "Decisions".)*
- **Scope (2026-11-06):** fix #1, #2, #3, #4, #5 and #9 on one branch from `upstream/master`, one commit per fix. Tests stay in the work folder; the PR contains only the fixes. *(Fixes done 2026-11-06 on branch `m2-fixes-2026-11`, worktree `cmp/m2-fixes` in the work folder: 6 commits `151ea38`..`40cac7c` on `7299306`, 4 files, +17/−17. Checked by reading and the import smoke test. Full diff in `reports/M2_m2-fixes-2026-11.diff`. All 10 hunks approved line by line. Pushed to my fork with my OK. PR opened with my OK: https://github.com/GOALS-survey/CAFE/pull/100. I merged it on 2026-11-06 (merge commit `3147e2a`), and my fork's `master` was synced to it with my OK.)*
- **Second GOALS round (2026-11-06):** fix #8, #12, #14 and #17 on branch `GOALS-small-fixes-2026-11` from `upstream/master` (`3147e2a`), one commit per fix. Checked by reading, a static check and the import smoke test, with no data runs. Then the full diff for my line-by-line review. Not pushed. *(Fixes done 2026-11-06 in worktree `cmp/GOALS-small-fixes`: 4 commits `a2d2ba1`..`f76a4c0` on `3147e2a`, 4 files, +16/−24, 6 hunks. Static checks and the smoke test pass. Diff in `reports/GOALS-small-fixes-2026-11.diff`. All 6 hunks approved line by line. Pushed to my fork with my OK. PR opened with my OK: https://github.com/GOALS-survey/CAFE/pull/101. I merged it on 2026-11-06 (merge commit `788be50`). The worktree, local branch and stale ref are removed.)*
- **Last GOALS round (2026-11-06):** fix #13, #6 (temporary) and #7 on branch `GOALS-physics-fixes-2026-11` from `upstream/master` (`788be50`), one commit per fix. Checked by reading, a static check and the import smoke test, with no data runs. Then the full diff for my line-by-line review. Not pushed. #11 waits for M3, together with `norm_factor`. *(Fixes done 2026-11-06 in worktree `cmp/GOALS-physics-fixes`: 3 commits `02fae32`..`f3d81f2` on `788be50`, 3 files, +10/−4, 3 hunks. At my request, the #7 formula keeps its multi-line layout and the outdated "Should add integrated gauss" comment is dropped (amended from `70002f2`, `32ba98f`, `11b8c65`). Checks and the smoke test pass. Diff in `reports/GOALS-physics-fixes-2026-11.diff`. All 3 hunks approved line by line. Pushed to my fork with my OK. PR opened with my OK: https://github.com/GOALS-survey/CAFE/pull/102. I merged it on 2026-11-06 (merge commit `ca10c84`).)*
- Fix only bugs in the synced version. Each fix is minimal and tested: failing case, then fix, then test; synthetic data with known truth for physics and numerics (CLAUDE.md §3, personal rules).
- Then a PR to GOALS after my line-by-line review (CLAUDE.md §2). The PR description is a brief human summary of 2 or 3 sentences.
- No Claude co-authorship anywhere in M2: commits, PR title and PR description (CLAUDE.md §2).
- After I merge, sync my fork's `master` with GOALS again, and ask before pushing.

### M3 — My local changes *(approved 2026-11-14; plan in `reports/M3_plan_2026-11-14.md`)*
- **Group 1 (I/O and products) done 2026-11-14** on `dev`, 4 commits `6d62e73`..`2263c17` (with the co-author trailer):
  - 1a `read_spec(flux_scale=…)`;
  - 1b `read_spec(ignore_DQ=…)`, fixed to `np.zeros_like(masks)`;
  - 1c `fitParsErr` in the `.asdf`;
  - 1d extinguished and intrinsic contcube profiles, with distinct keys and `'fCON'`.
  - 1e (`read_cretacube` `nz`, no effect) skipped as planned.
  - Tests in `tests/M3/` (work folder) all pass; failing cases first, including the local version for 1b and 1d.
  - Shown to me hunk by hunk under the review rule (CLAUDE.md §2). Approved 2026-11-14 and pushed with my OK (`8e0291b`→`f45a02b`).
- **Group 2 (photometry) done 2026-11-14** on `dev`, after my decision on D2 (option C). 4 commits `2063569`..`d7f07bb` (with the co-author trailer):
  - 2a: the contcube is built on the fit's model grid with photometry (`make_profcube` passes the fit's `phot_dict`);
  - 2b: `fFTS0` in `CompFluxes_0`;
  - 2c: the `cafeplot` y-range includes the photometry;
  - 2d + 2e (one commit, so that no step leaves the weights computed but unused): the weights R₀·Δλ/λ (option C), computed once per fit in `cafe_grinder` in five lines with `np.gradient`, applied in `chisquare`.
  - Tests in `tests/M3/` (work folder) all pass. The failing cases were run first, including the local un-sort on NumPy 1.26.
  - Commits 1–3 approved 2026-11-14. Commit 4 redone the same day under CLAUDE.md §8: it was `57a8bf7`, with the 47-line `calc_phot_weights`. The weights are the same bit for bit in 2,001 cases, on NumPy 2.5.4 and 1.26.2.
  - Simplification check of groups 1–2 (2026-11-14): nothing else in the ported lines has a simpler form worth a change. Left as they are: `ignore_DQ == True` (1b; the file's own idiom, as `trim == True`) and the named `fFTS_0` (2b; like its neighbours `fDST_0`, `fSRC_0`).
  - Real fits with photometry (2026-11-14): the tutorial spectrum with `inpars_jwst_miri_AGN.ini` and 5 points (the 3 test points plus the 2 FAKE points of my notebook; `inputs/phot5_obs.txt`).
    - With the shipped `photometry_opt.cafe` (`DoFilter = True`): broken by GOALS bug G3. The fit drove the model to about 0 (spectral χ²/N = 1.6×10⁷; model photometry 0).
    - Also run with `DoFilter = False` (`inputs/opt_fitphot.cafe`), so that group 2 is tested end to end. Spectral χ²/N = 20,690, as in the fixture fit without photometry (≈ 21,000). Weights 870–2,300.
    - In that fit, the photometry adds 8.4×10⁵ to χ², against 2.0×10⁸ from the spectrum (0.4%), so the spectrum still decides the fit. The model is 18× and 109× below PACS70 and PACS160 (cold and cirrus dust are fixed to 0 in this inpars file), and 2.5–2.9× above the two near-IR points. This is the error-floor question under "Awaiting my OK".
  - New commit 4 approved 2026-11-14. Not pushed. The G3 and G1 fixes are on `dev` (see "GOALS bugs found after M2"). Group 3 waits for my go-ahead.
- **Spectral error floor** (my decision 2026-11-15, see "Decisions") on `dev`, commit `1f6bca0` (with the co-author trailer):
  - `cafe_grinder` hands `chisquare` the spectral uncertainties sqrt(unc² + (f·F)²), with F the observed flux and f = `SPEC_UNC_FLOOR` from `[FIT OPTIONS]`: 0.01 in the three shipped opt files, and 0.01 for opt files without the option. `check_fit_pars` and the products keep the quoted uncertainties.
  - Test `tests/M3/test_spec_unc_floor.py` (synthetic, no fit): failing case first, 6 of 23 checks fail on `31d84a7` (the fit got the quoted errors whatever the floor, and the opt files had no such option); after the change, 23/23 pass.
  - The M3 suite (1a–1d, 2a–2c, 2de, G1, G3) passes, and the smoke test imports 18/18.
  - Synthetic known-truth fit with `photometry_opt.cafe` (floor 0.01 from the opt file): the parameters, parcube, contcube, `.asdf`, `_fitpars.ini`, figure and PAH table are identical to the work-folder variant at 1% run on the code before the change. The line table has the same rows; two empty rows (lines not fitted) come out in a different order, as they already did between the earlier runs.
  - Recovery at 1% (true mismatch 1.5%): COO_TMP +0.9%, WRM_TMP +1.4%, COO_TAU −8.5%, WRM_TAU +3.4%, STB_TAU −4.2%; far-IR bands (70–250 µm) / truth 0.982–0.995. Photometry's share of χ² 10.5%; spectral χ²/N 1.53 with the floored errors.
  - Approved 2026-11-15, with the fallback kept (opt files without the option get 0.01).
- **Group 3 (`norm_factor` and #11, D3a–e) started 2026-11-15:** D3 shown to me (options, current behaviour, recommendation); waiting for my decision before porting anything.
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
- Idea, logged 2026-11-15 (not tested, by my decision): one free spectrum-to-photometry scale factor, with a prior of the instrument's calibration uncertainty (MRS 5.6%). It would remove the calibration offset that a spectral error floor leaves in everything the spectrum pins down. It goes together with a floor: on its own, in the synthetic test, it stayed at its prior (s = 1.007 ± 0.044, truth 1.05).

### GOALS bugs found after M2 (logged 2026-11-14)
Each was found in GOALS `master` (`ca10c84`) as well as in `dev`. Line numbers are for `dev` before the fixes. Since 2026-11-14, fixes go only into `dev`, with my approval (CLAUDE.md §2).
- **G1: the photometry file's line order changes the model grid.** `read_phot` (`cafe.py:644`) keeps the file order, and `CAFE_prof_generator` (`cafe_helper.py:805`, `:813`) extends the model grid from `phot_dict['wave'][0]` for the bluest band and `[-1]` for the reddest.
  - Failing case: `tests/M3/test_G1_unsorted_phot.py` (work folder), with the same 3 points in ascending and in descending order (stubbed fit).
    - Ascending: the grid runs from 1.5 to 231 µm.
    - Descending: the grid stops at 30 µm, and the 70 and 160 µm points both get the model's value at 30 µm (3.35 Jy, `np.interp`'s end value), without a warning.
  - When: any photometry file that is not in ascending wavelength order.
- **G2: the `'Feat'` branch of `make_profcube` cannot run** (`cafe_helper.py:1171–1181`).
  - It uses an undefined `param`, adds a string to a list (`prof_pars+'_Wave'`), and creates a `ValueError` without raising it.
  - No caller asks for a `'Feat'` profile: `save_products` asks only for `'Comp'` and `'Comp_0'`, and so do my pre-sync scripts. So it doesn't break the normal workflow.
  - Stays for the dead-code clean-up (my decision, 2026-11-14).
- **G3: `synphot` with `DoFilter = True` converts the model to f_λ in place, once per filter** (`cafe_lib.py:295`, `flux *= 2.998e14 / wave**2`, inside the loop over filters).
  - Each filter after the first gets the conversion again. The caller's model array (`fluxMod`) is also changed.
  - Failing case: `tests/M3/test_G3_synphot_dofilter.py`, synthetic flat f_ν = 1 Jy model and three box filters. Result: 1.0116, 6.7×10¹⁰ and 1.9×10²⁰, instead of the formula's 1.0116, 1.0324 and 1.0566. Each filter on its own is right. The input array ends between 3.7×10²⁸ and 2.7×10⁴³.
  - My local version (`135aa70`) has the same line.
  - When: every fit with the shipped `photometry_opt.cafe` (`DoFilter = True`) and two or more photometric points with non-zero widths.
  - Effect in a real fit (M3 group 2 real fit, 2026-11-14): the fit drove the whole model to about 0 (spectral χ²/N = 1.6×10⁷). This breaks the normal workflow.
- **GOALS round for G3 and G1 (2026-11-14).** Branch `GOALS-photometry-fixes-2026-11` from `upstream/master` (`ca10c84`), in the worktree `cmp/GOALS-photometry-fixes` (work folder). 2 commits, mine, no co-author trailer; 2 files, +3/−2, 2 hunks:
  - `f44f96e` G3: `synphot` puts the f_λ conversion into its own array (`flux_lam`). Rebinding `flux` instead would leave the input unchanged but still compound inside the loop (checked).
  - `c0bd2c6` G1: `read_phot` sorts the table by wavelength.
  - Failing cases first, on the branch: test G3 failed 3/3 before and passes 3/3 after, in `cafe-dev` and `cafe-legacy`; test G1 failed 2 of 3 checks before and passes 3/3 after. Smoke test: 18/18, the same output as the last GOALS round apart from the path.
  - Real fit on the branch with `photometry_opt.cafe` (`DoFilter = True`) and the 5 points: it converges. Spectral χ²/N = 20,700, as without photometry; model photometry 0.28, 0.26, 3.65, 1.80 and 0.17 Jy. GOALS has no photometry weights (D2), so the photometry adds 1,130 to a χ² of 2.0×10⁸.
  - Diff in `reports/GOALS-photometry-fixes-2026-11.diff`; draft PR title and description in `reports/PR_GOALS-photometry-fixes-2026-11_body.md` (work folder).
  - Both hunks approved 2026-11-14. Not sent to GOALS (no more GOALS PRs; CLAUDE.md §2). Cherry-picked onto `dev` as `88d648b` (G3) and `39c930a` (G1), with the same changed lines.
  - The local branch is deleted; it was never pushed. Its worktree folder `cmp/GOALS-photometry-fixes` is detached at `c0bd2c6` and kept until I OK its removal. The draft PR text in `reports/` is obsolete.
  - On `dev` (`39c930a`): all M3 tests plus G1 and G3 pass (69 checks, with 2de and G3 also in `cafe-legacy`). Smoke test: 18/18, unchanged.
  - Real fit on `dev` with `photometry_opt.cafe` and the 5 points: it converges in 4,296 steps. Spectral χ²/N = 21,060; model photometry 0.27, 0.24, 3.41, 1.32 and 0.11 Jy.
  - With the D2 weights, the photometry adds 1.08×10⁶ to a χ² of 2.04×10⁸ (0.5%). Compared with the same fit without weights (on the GOALS branch), the photometry's unweighted χ² falls from 1,130 to 948, and the spectral χ² rises by 1.7%. The far-IR points are still 22× and 131× above the model: the error-floor question, and cold and cirrus dust are fixed to 0 in this inpars file.

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

**Static checks and smoke test on the second GOALS round** (worktree `cmp/GOALS-small-fixes` in the work folder; removed 2026-11-06 after the merge)
```
cd /Users/tanio/pywork/cafe_work
env PYTHONDONTWRITEBYTECODE=1 ~/miniforge3/envs/cafe-dev/bin/python tests/GOALS-small-fixes/static_checks.py cmp/GOALS-small-fixes
env PYTHONDONTWRITEBYTECODE=1 MPLBACKEND=Agg PYTHONPATH=/Users/tanio/pywork/cafe_work/cmp/GOALS-small-fixes ~/miniforge3/envs/cafe-dev/bin/python scripts/smoke_import.py /Users/tanio/pywork/cafe_work/cmp/GOALS-small-fixes
```
`static_checks.py` scans all of CAFE and CRETA for the pattern behind each fix, and checks that `cafe_lib.py` parses to the same AST as on `upstream/master`. Result 2026-11-06, before the fixes: 1 try/except in `cafe_grinder`, 5 remove-while-iterating loops (all in `creta.py`), 1 live `ipdb`, 4 SyntaxWarnings; nothing else. After the fixes: 0 of each, and the AST is identical. Smoke test: 18/18 import, 0 failed. The output is identical to `logs/smoke_m2-fixes.txt` apart from the path, except that the four `'\,'` SyntaxWarnings are gone (`logs/smoke_GOALS-small-fixes.txt`).

**NGC7469 tutorial spectrum** (link from `notebooks/CAFE_tutorial_NGC7469_1D.ipynb`; tutorial uses z = 0.0163)
```
mkdir -p /Users/tanio/pywork/cafe_work/data/NGC7469
curl -fsSL -o /Users/tanio/pywork/cafe_work/data/NGC7469/NGC7469_SingleExt_r1.5as_MIRI.dat 'https://caltech.box.com/shared/static/u12th7dvkvu2iiv73r77c45lnn58sgvh.dat'
shasum -a 256 /Users/tanio/pywork/cafe_work/data/NGC7469/NGC7469_SingleExt_r1.5as_MIRI.dat
```
324,989 bytes, 9,695 rows × 3 columns (wavelength 4.957–28.603 µm observed, flux, uncertainty), sha256 `e317901ca755f853008a2abc05bdd5ce4a2d88cd4f4135da04e464783436dc16`.

**Checks and smoke test on the last GOALS round** (worktree `cmp/GOALS-physics-fixes` in the work folder; removed 2026-11-06 after the merge)
```
cd /Users/tanio/pywork/cafe_work
env PYTHONDONTWRITEBYTECODE=1 MPLBACKEND=Agg PYTHONPATH=/Users/tanio/pywork/cafe_work/cmp/GOALS-physics-fixes ~/miniforge3/envs/cafe-dev/bin/python tests/GOALS-physics-fixes/static_checks.py cmp/GOALS-physics-fixes
env PYTHONDONTWRITEBYTECODE=1 MPLBACKEND=Agg PYTHONPATH=/Users/tanio/pywork/cafe_work/cmp/GOALS-physics-fixes ~/miniforge3/envs/cafe-dev/bin/python scripts/smoke_import.py /Users/tanio/pywork/cafe_work/cmp/GOALS-physics-fixes
```
`static_checks.py` checks three things, with no data read:
- the `x/(1.*y)` pattern of #13 anywhere in CAFE or CRETA;
- that the fitting-sequence image of #6 is a `nansum` over all channels;
- that the #7 line strength, evaluated on three synthetic lines, equals the `line_table` formula and the integral over frequency of CAFE's own `gauss_prof` (known truth).

Result 2026-11-06:
- Before the fixes, all four checks fail: the old strength was off by a factor of about 10¹⁸.
- After the fixes, all pass. The new strength over the `line_table` formula is exactly 2√(2 ln 2)/2.35482 = 1 + 1.9e-8, because `save_asdf` and `gauss_prof` use the rounded 2.35482. The new strength over the `gauss_prof` integral is 0.9999 (narrow-line approximation and `gauss_prof`'s sampled profile).
- Smoke test: 18/18 import, 0 failed. The output is identical to `logs/smoke_GOALS-small-fixes.txt` apart from the path (`logs/smoke_GOALS-physics-fixes.txt`).

**M3 shared fixture and tests** (work folder; code on `PYTHONPATH`, `cafe-dev`)
```
cd /Users/tanio/pywork/cafe_work/tests/M3/fixture
env PYTHONDONTWRITEBYTECODE=1 MPLBACKEND=Agg PYTHONPATH=/Users/tanio/Sync/pywork/CAFE ~/miniforge3/envs/cafe-dev/bin/python ../make_fixture.py /Users/tanio/Sync/pywork/CAFE
cd /Users/tanio/pywork/cafe_work/tests/M3/out/1a && env PYTHONDONTWRITEBYTECODE=1 MPLBACKEND=Agg PYTHONPATH=/Users/tanio/Sync/pywork/CAFE ~/miniforge3/envs/cafe-dev/bin/python ../../test_1a_flux_scale.py /Users/tanio/Sync/pywork/CAFE
cd /Users/tanio/pywork/cafe_work/tests/M3/out/1b && env PYTHONDONTWRITEBYTECODE=1 MPLBACKEND=Agg PYTHONPATH=/Users/tanio/Sync/pywork/CAFE ~/miniforge3/envs/cafe-dev/bin/python ../../test_1b_ignore_DQ.py /Users/tanio/Sync/pywork/CAFE
cd /Users/tanio/pywork/cafe_work/tests/M3 && env PYTHONDONTWRITEBYTECODE=1 MPLBACKEND=Agg PYTHONPATH=/Users/tanio/Sync/pywork/CAFE ~/miniforge3/envs/cafe-dev/bin/python test_1c_fitParsErr.py /Users/tanio/Sync/pywork/CAFE out/1c
cd /Users/tanio/pywork/cafe_work/tests/M3 && env PYTHONDONTWRITEBYTECODE=1 MPLBACKEND=Agg PYTHONPATH=/Users/tanio/Sync/pywork/CAFE ~/miniforge3/envs/cafe-dev/bin/python test_1d_contcube.py /Users/tanio/Sync/pywork/CAFE out/1d /Users/tanio/pywork/cafe_work/cmp/local-wip
cd /Users/tanio/pywork/cafe_work/tests/M3 && env PYTHONDONTWRITEBYTECODE=1 MPLBACKEND=Agg PYTHONPATH=/Users/tanio/Sync/pywork/CAFE ~/miniforge3/envs/cafe-dev/bin/python test_2a_profcube_phot.py /Users/tanio/Sync/pywork/CAFE out/2a
cd /Users/tanio/pywork/cafe_work/tests/M3 && env PYTHONDONTWRITEBYTECODE=1 MPLBACKEND=Agg PYTHONPATH=/Users/tanio/Sync/pywork/CAFE ~/miniforge3/envs/cafe-dev/bin/python test_2b_fFTS0.py /Users/tanio/Sync/pywork/CAFE out/2b
cd /Users/tanio/pywork/cafe_work/tests/M3 && env PYTHONDONTWRITEBYTECODE=1 MPLBACKEND=Agg PYTHONPATH=/Users/tanio/Sync/pywork/CAFE ~/miniforge3/envs/cafe-dev/bin/python test_2c_plot_ylim.py /Users/tanio/Sync/pywork/CAFE out/2c
cd /Users/tanio/pywork/cafe_work/tests/M3 && env PYTHONDONTWRITEBYTECODE=1 MPLBACKEND=Agg PYTHONPATH=/Users/tanio/Sync/pywork/CAFE ~/miniforge3/envs/cafe-dev/bin/python test_2de_phot_weights.py /Users/tanio/Sync/pywork/CAFE
cd /Users/tanio/pywork/cafe_work/tests/M3 && env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/Users/tanio/pywork/cafe_work/cmp/local-wip ~/miniforge3/envs/cafe-legacy/bin/python test_2d_local_unsort.py
cd /Users/tanio/pywork/cafe_work/tests/M3 && env PYTHONDONTWRITEBYTECODE=1 MPLBACKEND=Agg PYTHONPATH=/Users/tanio/Sync/pywork/CAFE ~/miniforge3/envs/cafe-dev/bin/python test_G1_unsorted_phot.py /Users/tanio/Sync/pywork/CAFE out/G1
cd /Users/tanio/pywork/cafe_work/tests/M3 && env PYTHONDONTWRITEBYTECODE=1 MPLBACKEND=Agg PYTHONPATH=/Users/tanio/Sync/pywork/CAFE ~/miniforge3/envs/cafe-dev/bin/python test_G3_synphot_dofilter.py /Users/tanio/Sync/pywork/CAFE
cd /Users/tanio/pywork/cafe_work/tests/M3/out/realfit_phot5 && env PYTHONDONTWRITEBYTECODE=1 MPLBACKEND=Agg PYTHONPATH=/Users/tanio/Sync/pywork/CAFE ~/miniforge3/envs/cafe-dev/bin/python ../../realfit_phot5.py /Users/tanio/Sync/pywork/CAFE
cd /Users/tanio/pywork/cafe_work/tests/M3/out/realfit_phot5_nofilter && env PYTHONDONTWRITEBYTECODE=1 MPLBACKEND=Agg PYTHONPATH=/Users/tanio/Sync/pywork/CAFE ~/miniforge3/envs/cafe-dev/bin/python ../../realfit_phot5.py /Users/tanio/Sync/pywork/CAFE /Users/tanio/pywork/cafe_work/tests/M3/inputs/opt_fitphot.cafe
cd /Users/tanio/pywork/cafe_work/tests/M3 && env PYTHONDONTWRITEBYTECODE=1 MPLBACKEND=Agg PYTHONPATH=/Users/tanio/pywork/cafe_work/cmp/GOALS-photometry-fixes ~/miniforge3/envs/cafe-dev/bin/python test_G3_synphot_dofilter.py /Users/tanio/pywork/cafe_work/cmp/GOALS-photometry-fixes
cd /Users/tanio/pywork/cafe_work/tests/M3 && env PYTHONDONTWRITEBYTECODE=1 MPLBACKEND=Agg PYTHONPATH=/Users/tanio/pywork/cafe_work/cmp/GOALS-photometry-fixes ~/miniforge3/envs/cafe-dev/bin/python test_G1_unsorted_phot.py /Users/tanio/pywork/cafe_work/cmp/GOALS-photometry-fixes out/G1_goals_after
cd /Users/tanio/pywork/cafe_work/tests/M3/out/realfit_phot5_goalsfix && env PYTHONDONTWRITEBYTECODE=1 MPLBACKEND=Agg PYTHONPATH=/Users/tanio/pywork/cafe_work/cmp/GOALS-photometry-fixes ~/miniforge3/envs/cafe-dev/bin/python ../../realfit_phot5.py /Users/tanio/pywork/cafe_work/cmp/GOALS-photometry-fixes
cd /Users/tanio/pywork/cafe_work/tests/M3/out/realfit_phot5_dev_fixed && env PYTHONDONTWRITEBYTECODE=1 MPLBACKEND=Agg PYTHONPATH=/Users/tanio/Sync/pywork/CAFE ~/miniforge3/envs/cafe-dev/bin/python ../../realfit_phot5.py /Users/tanio/Sync/pywork/CAFE
cd /Users/tanio/pywork/cafe_work/tests/M3/out/weighting/W2246_C && env PYTHONDONTWRITEBYTECODE=1 MPLBACKEND=Agg PYTHONPATH=/Users/tanio/Sync/pywork/CAFE ~/miniforge3/envs/cafe-dev/bin/python ../../../weighting_W2246.py /Users/tanio/Sync/pywork/CAFE C
cd /Users/tanio/pywork/cafe_work/tests/M3/out/weighting/W2246_B && env PYTHONDONTWRITEBYTECODE=1 MPLBACKEND=Agg PYTHONPATH=/Users/tanio/Sync/pywork/CAFE ~/miniforge3/envs/cafe-dev/bin/python ../../../weighting_W2246.py /Users/tanio/Sync/pywork/CAFE B
cd /Users/tanio/pywork/cafe_work/tests/M3 && env PYTHONDONTWRITEBYTECODE=1 ~/miniforge3/envs/cafe-dev/bin/python floor_rule.py out/weighting/W2246_C/summary.npz
cd /Users/tanio/pywork/cafe_work/tests/M3/out/weighting/W2246_Cfloor && env PYTHONDONTWRITEBYTECODE=1 MPLBACKEND=Agg PYTHONPATH=/Users/tanio/Sync/pywork/CAFE ~/miniforge3/envs/cafe-dev/bin/python ../../../weighting_W2246.py /Users/tanio/Sync/pywork/CAFE Cfloor 0.056
cd /Users/tanio/pywork/cafe_work/tests/M3 && env PYTHONDONTWRITEBYTECODE=1 MPLBACKEND=Agg PYTHONPATH=/Users/tanio/Sync/pywork/CAFE ~/miniforge3/envs/cafe-dev/bin/python synth_make.py /Users/tanio/Sync/pywork/CAFE
cd /Users/tanio/pywork/cafe_work/tests/M3/out/synth/C && env PYTHONDONTWRITEBYTECODE=1 MPLBACKEND=Agg PYTHONPATH=/Users/tanio/Sync/pywork/CAFE ~/miniforge3/envs/cafe-dev/bin/python ../../../synth_fit.py /Users/tanio/Sync/pywork/CAFE C
cd /Users/tanio/pywork/cafe_work/tests/M3/out/synth/Cfloor && env PYTHONDONTWRITEBYTECODE=1 MPLBACKEND=Agg PYTHONPATH=/Users/tanio/Sync/pywork/CAFE ~/miniforge3/envs/cafe-dev/bin/python ../../../synth_fit.py /Users/tanio/Sync/pywork/CAFE Cfloor
cd /Users/tanio/pywork/cafe_work/tests/M3/out/synth/Cscale && env PYTHONDONTWRITEBYTECODE=1 MPLBACKEND=Agg PYTHONPATH=/Users/tanio/Sync/pywork/CAFE ~/miniforge3/envs/cafe-dev/bin/python ../../../synth_fit.py /Users/tanio/Sync/pywork/CAFE Cscale
cd /Users/tanio/pywork/cafe_work/tests/M3/out/synth/Cfloor_0.0075 && env PYTHONDONTWRITEBYTECODE=1 MPLBACKEND=Agg PYTHONPATH=/Users/tanio/Sync/pywork/CAFE ~/miniforge3/envs/cafe-dev/bin/python ../../../synth_fit.py /Users/tanio/Sync/pywork/CAFE Cfloor 0.0075
cd /Users/tanio/pywork/cafe_work/tests/M3/out/synth/Cfloor_0.03 && env PYTHONDONTWRITEBYTECODE=1 MPLBACKEND=Agg PYTHONPATH=/Users/tanio/Sync/pywork/CAFE ~/miniforge3/envs/cafe-dev/bin/python ../../../synth_fit.py /Users/tanio/Sync/pywork/CAFE Cfloor 0.03
cd /Users/tanio/pywork/cafe_work/tests/M3/out/synth/Cfloor_0.01 && env PYTHONDONTWRITEBYTECODE=1 MPLBACKEND=Agg PYTHONPATH=/Users/tanio/Sync/pywork/CAFE ~/miniforge3/envs/cafe-dev/bin/python ../../../synth_fit.py /Users/tanio/Sync/pywork/CAFE Cfloor 0.01   # run on 31d84a7, before the floor option
cd /Users/tanio/pywork/cafe_work/tests/M3/out/synth/dev_floor_0.01 && env PYTHONDONTWRITEBYTECODE=1 MPLBACKEND=Agg PYTHONPATH=/Users/tanio/Sync/pywork/CAFE ~/miniforge3/envs/cafe-dev/bin/python ../../../synth_fit.py /Users/tanio/Sync/pywork/CAFE C   # 1f6bca0: the floor from photometry_opt.cafe
cd /Users/tanio/pywork/cafe_work/tests/M3 && env PYTHONDONTWRITEBYTECODE=1 ~/miniforge3/envs/cafe-dev/bin/python synth_compare.py C Cfloor_0.0075 dev_floor_0.01 Cfloor Cfloor_0.03 Cscale
cd /Users/tanio/pywork/cafe_work/tests/M3 && env PYTHONDONTWRITEBYTECODE=1 MPLBACKEND=Agg PYTHONPATH=/Users/tanio/Sync/pywork/CAFE ~/miniforge3/envs/cafe-dev/bin/python test_spec_unc_floor.py /Users/tanio/Sync/pywork/CAFE
cd /Users/tanio/pywork/cafe_work/tests/M3/out/scale/k_1e-4 && env PYTHONDONTWRITEBYTECODE=1 MPLBACKEND=Agg PYTHONPATH=/Users/tanio/Sync/pywork/CAFE ~/miniforge3/envs/cafe-dev/bin/python ../../../scale_dep.py /Users/tanio/Sync/pywork/CAFE 1e-4   # likewise k_1 with 1, k_1e4 with 1e4
cd /Users/tanio/pywork/cafe_work/tests/M3 && env PYTHONDONTWRITEBYTECODE=1 ~/miniforge3/envs/cafe-dev/bin/python scale_compare.py k_1 k_1e-4 k_1e4
```
- **Weighting test (2026-11-15):** `weighting_W2246.py` replaces only the χ² that `cafe_grinder` hands to lmfit (variants C, B, Cfloor). The W2246 tables reach `dev`'s code through `tests/M3/cafe_dir_W2246/` (symlinks to `dev`'s tables plus the five W2246 tables from the pre-sync folder), passed as `cafe_dir`.
- **Fixture:** made 2026-11-14 with code `21e0cbf`, which equals GOALS `master` `ca10c84`. It is the NGC7469 tutorial spectrum fitted with `inpars_jwst_miri_AGN.ini` and `default_opt.cafe` (z = 0.0163), in 42.5 s.
- **How the product tests use it:** they run the real `fit_spec` with only `cafe_grinder` replaced by the fixture's parameters (`tests/M3/common.py`), so all products are written by the code under test.
- **Test 1b:** uses a copy of the M1 CRETA cube with DQ = 1 on 10 channels of the centre spaxel. The original cube has no flagged channels.
- **Result 2026-11-14:** all four tests pass. Smoke test: 18/18 (`logs/smoke_dev_M3g1.txt`).
- **Group 2 tests:**
  - `stub_fit_spec(..., phot=True)` adds 3 synthetic photometric points outside the spectrum (`inputs/phot3_obs.txt`) and uses `inputs/opt_fitphot.cafe` (`default_opt.cafe` with `FitPhot = True`).
  - Test 2de uses synthetic data only (no fit; lmfit's `Minimizer` and `get_model_fluxes` are replaced by stubs) and checks the weights that `cafe_grinder` sets. It also passes in `cafe-legacy` (NumPy 1.26).
  - The "before" runs use the detached worktree `cmp/dev-before` in the work folder.
  - Result 2026-11-14 on `d7f07bb`, after the redo of commit 4: all 8 M3 tests pass (54 checks), and test 2de also in `cafe-legacy`. Smoke test: 18/18, the same output as group 1 (`logs/smoke_dev_M3g2b.txt`).

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
- 2026-11-06: **M2 continues with a second GOALS round** (numbers as in `reports/M2_bug_list_2026-11-06.md`):
  - Branch from `upstream/master` (`3147e2a`), named after its content: `GOALS-small-fixes-2026-11`. One commit per fix, each minimal:
    - #8: remove the try/except around `fitter.minimize` in `cafe_grinder`, so lmfit's own error is raised;
    - #12: replace the remove-while-looping hidden-file loops in `creta.py` with list comprehensions, as in PR #99;
    - #14: replace `ipdb.set_trace()` in `dustgrainfunc.py` with a clear error saying custom SED arrays are disabled and a source name must be used;
    - #17: make the `'\,'` strings in `cafe_lib.py` raw strings, without changing the labels.
  - These are evident fixes: check them by reading, a static check and the import smoke test, with no data runs.
  - Then show me the full diff for line-by-line review. Don't push.
- 2026-11-06: **Second GOALS round reviewed.**
  - I approved all 6 hunks of `GOALS-small-fixes-2026-11` line by line: 4 commits `a2d2ba1`..`f76a4c0` on GOALS `master` `3147e2a`, in 4 files (`cafe.py`, `cafe_lib.py`, `dustgrainfunc.py`, `creta.py`). Any later change to the branch must be shown to me again.
  - PR text, mine:
    - Title: "More small fixes to CAFE and CRETA".
    - Description: in `reports/PR_GOALS-small-fixes-2026-11_body.md` in the work folder.
  - Next: ask before pushing the branch to my fork, then ask "Open PR GOALS-small-fixes-2026-11 → GOALS-survey/CAFE?".
- 2026-11-06: `GOALS-small-fixes-2026-11` pushed to my fork with my OK (tip `f76a4c0`). Only its 4 approved commits were newly published; I am their author, and there are no trailers. Next: ask "Open PR GOALS-small-fixes-2026-11 → GOALS-survey/CAFE?".
- 2026-11-06: **PR opened** with my OK: https://github.com/GOALS-survey/CAFE/pull/101, "More small fixes to CAFE and CRETA", `tdiazsantos:GOALS-small-fixes-2026-11` @ `f76a4c0` → GOALS `master` (`3147e2a`).
  - 4 commits, 4 files, +16/−24. Its description is identical to my text. There is no Claude attribution anywhere.
  - GitHub reports it mergeable and shows no CI checks.
  - I merge it myself on GitHub; never merge, approve or close anything on GOALS.
  - Next: after my merge, bring my fork's `master` up to GOALS again, asking before pushing.
- 2026-11-06: **PR #101 merged.**
  - I merged it on GitHub at 16:57 UTC: merge commit `788be50`, parents `3147e2a` + `f76a4c0`. I deleted the branch on GitHub.
  - GOALS `master` is now `788be50`, and its file tree is identical to the approved `f76a4c0`.
  - With my OK:
    - the worktree `cmp/GOALS-small-fixes` was removed (it was clean);
    - the local branch `GOALS-small-fixes-2026-11` was deleted with `git branch -d` (no force); it is contained in `master`;
    - the stale ref `origin/GOALS-small-fixes-2026-11` was removed. No other stale refs are left.
  - The local `master` was fast-forwarded to `788be50`.
  - Next: fast-forward my fork's `master` `3147e2a`→`788be50` and push `dev`, showing me first what each push publishes. With that, M2's second round is done, and M3 waits for my approval.
  - *(Done the same day, with my OK: my fork's `master` `3147e2a`→`788be50` (fast-forward; equal to GOALS `master`), and `dev` `f398f51`→`72c3481` (7 commits, `PROJECT_BRIEF.md` only, no trailers). M2's second round is done; M3 waits for my approval.)*
- 2026-11-06: **Last GOALS round of M2: physics decisions #13, #6 and #7** (numbers as in `reports/M2_bug_list_2026-11-06.md`). Branch from `upstream/master`, named after its content: `GOALS-physics-fixes-2026-11`. One commit each, minimal:
  - #13: in `cafe_helper.py`, the PAH peak lower bound becomes `drude[2][i]/(1.+inpars['EPSPEAK_PAH'])`, as in the Gauss branch.
  - #6 (temporary): in `fit_cube`, the image for the fitting sequence is the `nansum` over all wavelength channels instead of channels 10–19. A proper SNR image is still to come.
  - #7: in `save_asdf`, the line `'strength'` is computed like the PAH strength, as an integrated flux in W m⁻²: √(2π) × (c/λ0) × (gamma/2.35482) × peak × 1e-26. This is algebraically the formula `line_table` already uses for line fluxes (`cafe_io.py:926–931`).
  - #11 (`check_fit_pars`' absolute tolerance) waits for M3, together with `norm_factor`.
  - Check by reading, a static check and the import smoke test, with no data runs. Then show me the full diff for line-by-line review. Don't push.
- 2026-11-06: **Last GOALS round reviewed.**
  - At my request, the #7 expression is on one line.
  - I approved all 3 hunks of `GOALS-physics-fixes-2026-11` line by line: 3 commits `02fae32`..`32ba98f` on GOALS `master` `788be50`, in 3 files (`cafe_helper.py`, `cafe.py`, `cafe_io.py`). Any later change to the branch must be shown to me again.
  - Next: my PR title and description, then ask before pushing the branch to my fork, then ask "Open PR GOALS-physics-fixes-2026-11 → GOALS-survey/CAFE?".
  - Then I asked to drop the outdated `#  Should add integrated gauss` comment from hunk 3 and keep the closing brace. The #7 commit is now `11b8c65`, and hunk 3 needs my review again.
  - Then I asked to restore the multi-line layout of the strength formula, still without the comment. The #7 commit is now `f3d81f2`; its formula lines are identical to `70002f2`. Hunk 3 needs my review again.
  - I approved the new hunk 3. **All 3 hunks of `GOALS-physics-fixes-2026-11` are approved line by line:** 3 commits `02fae32`..`f3d81f2` on GOALS `master` `788be50`. Any later change to the branch must be shown to me again.
  - PR text, mine:
    - Title: "Last small fixes to CAFE".
    - Description: in `reports/PR_GOALS-physics-fixes-2026-11_body.md` in the work folder.
  - Next: ask before pushing the branch to my fork, then ask "Open PR GOALS-physics-fixes-2026-11 → GOALS-survey/CAFE?".
- 2026-11-06: `GOALS-physics-fixes-2026-11` pushed to my fork with my OK (tip `f3d81f2`). Only its 3 approved commits were newly published; I am their author, and there are no trailers. Next: ask "Open PR GOALS-physics-fixes-2026-11 → GOALS-survey/CAFE?".
- 2026-11-06: **PR opened** with my OK: https://github.com/GOALS-survey/CAFE/pull/102, "Last small fixes to CAFE", `tdiazsantos:GOALS-physics-fixes-2026-11` @ `f3d81f2` → GOALS `master` (`788be50`).
  - 3 commits, 3 files, +10/−4. Its description is identical to my text. There is no Claude attribution anywhere.
  - GitHub reports it mergeable and shows no CI checks.
  - I merge it myself on GitHub; never merge, approve or close anything on GOALS.
  - Next: after my merge, bring my fork's `master` up to GOALS again, asking before pushing, then clean up the worktree, the local branch and the stale ref with my OK.
- 2026-11-06: **PR #102 merged.**
  - I merged it on GitHub at 17:41 UTC: merge commit `ca10c84`, parents `788be50` + `f3d81f2`. I deleted the branch on GitHub.
  - GOALS `master` is now `ca10c84`, and its file tree is identical to the approved `f3d81f2`.
  - The merge commit's message says "from tdiazsantos/GOALS-last-small-fixes-2026-11". The PR's head branch was `GOALS-physics-fixes-2026-11`.
  - The local `master` was fast-forwarded to `ca10c84`.
  - Next, each with my OK:
    - fast-forward my fork's `master` `788be50`→`ca10c84` and push `dev`, showing me first what each push publishes;
    - remove the worktree `cmp/GOALS-physics-fixes`, the local branch `GOALS-physics-fixes-2026-11` and the stale ref `origin/GOALS-physics-fixes-2026-11`.
  - With that, M2 (all three GOALS rounds) is done, and M3 waits for my approval.
  - *(Done the same day, with my OK:*
    - *my fork's `master` `788be50`→`ca10c84` (fast-forward; equal to GOALS `master`);*
    - *`dev` `72c3481`→`1252ecb` (12 commits, `PROJECT_BRIEF.md` only, no trailers);*
    - *the clean worktree `cmp/GOALS-physics-fixes` removed, the local branch deleted with `git branch -d`, and the stale ref removed. No other stale refs are left.*
    - ***M2 is done.** #11 waits for M3, and M3 waits for my approval.)*
- 2026-11-14: **M3 approved.**
  - First step: merge `master` (= GOALS `master` `ca10c84`) into `dev`, with no rebase and no force push, so M3 starts from the fixed version. Done: merge commit `c2915e9` (parents `35f0cd8` + `ca10c84`). The code on `dev` now equals GOALS `master`; only the project files differ.
  - **Co-authorship:** commit attribution on, PR attribution off, in `.claude/settings.local.json` (`commit` on, `pr` empty). It applies to commits that stay on my fork. Anything for GOALS follows the GOALS rule: no Claude trailer and no attribution, with fresh commits from `upstream/master`. Attribution was turned on after the commit that records this.
  - Then a plan only: my local changes from `local-wip-2026-11`, the local-only bugs and #11 (together with `norm_factor`), grouped, in the order I'd bring them into `dev`, each with what it does and a simple test. Done: `reports/M3_plan_2026-11-14.md`. Its open decisions are under "Awaiting my OK". Waiting for my review.
- 2026-11-14: `dev` pushed to my fork with my OK (`1252ecb`→`8e0291b`: `35f0cd8`, the merge `c2915e9`, `8e0291b`; no trailers).
- 2026-11-14: **M3 decisions:**
  - **D1:** yes, one NGC7469 tutorial 1D fit as a shared fixture for the product tests.
  - **D7:** rename the contcube extension `'fCon'` → `'fCON'` only if nothing in CAFE, CRETA or my scripts reads `'fCon'`.
    - Result: only the line that writes it mentions `'fCon'`.
    - My pre-sync notebooks read `contcube['fCON']` and the other upper-case names.
    - astropy stores EXTNAME in upper case (`FCON` in both cases) and looks it up case-insensitively, so the rename changes nothing on disk.
    - So: rename.
  - **D8:** my input files (inpars, opt, line tables, CRETA parameter files) stay out of the shipped defaults.
  - **D2–D6:** when we reach each group, show me the options, the current GOALS behaviour and your recommendation.
  - Work one group at a time. Group 1 first, then stop for my review.
- 2026-11-14: **Standing rule: review of every code change** (CLAUDE.md §2). For every code change, on any branch, show me:
  - the full diff, hunk by hunk;
  - for each change, a short paragraph on the reason for it (what the problem was) and how it is addressed.

  Nothing is pushed and no next group starts until I approve it. GOALS changes also follow the GOALS rule. Applied first to M3 group 1 (`6d62e73`..`2263c17`).
- 2026-11-14: **M3 group 1 approved.** `dev` pushed to my fork with my OK (`8e0291b`→`f45a02b`, 7 commits, all mine, each with the Claude co-author trailer allowed on fork-only M3 commits). Then group 2 starts with D2 only, and stops for my decision before anything is ported.
- 2026-11-14: **D2: option C.**
  - The photometric weights keep only the interval term R₀·Δλ/λ, without the factor (median SNR_spec / median SNR_phot)². So each photometric point keeps its own uncertainty.
  - Before: GOALS weighted photometry by plain 1/σ²; my local formula had the SNR factor.
  - Then port group 2, each change shown hunk by hunk with its reason (standing rule).
- 2026-11-14: **M3 group 2: commits 1–3 approved** (`2063569`, `44f0d34`, `ee33a5d`).
  - Commit 4 is redone, not added as a new commit, with the five `np.gradient` lines in `cafe_grinder` in place of `calc_phot_weights`.
  - Also asked for: a check of groups 1–2 for other simplifications; one real fit with photometry; G1 logged as a GOALS bug.
  - For the real fit I chose the 3 test points plus the 2 FAKE points of my notebook (5 points), and the shipped `photometry_opt.cafe`.
- 2026-11-14: **Standing rule: the simplest form when bringing in my local changes** (CLAUDE.md §8).
  - Faithfulness to my old code is not a goal. Write each change in the simplest form that gives the same result (personal rule on simplicity).
  - If my old code can be replaced by something shorter, or by an existing NumPy, astropy or lmfit function, do that, and say so in the change's paragraph.
  - Applied first to group 2 commit 4: `calc_phot_weights` (47 lines) became five lines with `np.gradient` in `cafe_grinder`.
- 2026-11-14: **New commit 4 (`d7f07bb`) and CLAUDE.md §8 approved.**
- 2026-11-14: **A short GOALS round for G3 and G1, before group 3.** On a branch from `upstream/master`, named after its content (`GOALS-photometry-fixes-2026-11`). One commit each, minimal, each with its failing case shown first. These commits go to GOALS, so no Claude co-author trailer.
  - G3: in `synphot`, do the unit conversion on a copy, so the model isn't modified in place.
  - G1: `read_phot` sorts the photometry by wavelength.
  - Then, on that branch, rerun the photometry fit with `photometry_opt.cafe` (`DoFilter = True`) to confirm it works. Show me the diff hunk by hunk with the reason paragraphs.
  - G2 stays for the dead-code clean-up.
- 2026-11-14: **Both hunks of the G3/G1 round approved, then a change of plan: no more pushes or PRs to GOALS** (CLAUDE.md §2).
  - From now on, fixes to GOALS bugs go only into `dev` on my fork. My fork's `master` stays equal to GOALS `master`.
  - Applied at once: cherry-pick `f44f96e` and `c0bd2c6` onto `dev`, delete the local branch `GOALS-photometry-fixes-2026-11` (never pushed), and rerun the photometry fit with `photometry_opt.cafe` on `dev`. Then wait before group 3.
- 2026-11-15: **D2 option C stays as the photometry weighting.** The spectral error budget is a separate physics decision, to be settled with a synthetic known-truth test: one CAFE model with known parameters, a spectrum at realistic SNR, photometry, a ~5% calibration offset and a ~1–2% model mismatch. Variants: (1) option C alone; (2) option C plus a per-channel 1–2% model-error floor; (3) option C plus one free spectrum-to-photometry scale with a 5.6% prior. Run from the work folder, no code change on `dev`, then stop for my decision.
- 2026-11-15: **One last synthetic check of the floor, and the scale factor deferred.** Same setup, from the work folder, no code change on `dev`: true mismatch 1.5%, fitted with floors of 0.75% and 3%, to see whether the recovery of the dust shape and the far-IR bands still holds. The free scale factor for the calibration offset is logged as an idea for later (under "Later"), not tested. Then stop for my decision on the floor.
- 2026-11-15: **Spectral error floor: 1% of the observed flux** (physics decision). Added in quadrature to the quoted spectral uncertainties and used only in the fit's χ²; the saved products and `check_fit_pars` keep the quoted errors. One option in the opt file's `[FIT OPTIONS]`, default 0.01, so it can be changed or set to 0. Implemented on `dev` as its own change, in the simplest form, then shown to me hunk by hunk with its reason paragraph for my approval.
- 2026-11-15: **Commit `1f6bca0` (spectral error floor) approved; keep the fallback** of 0.01 for opt files without the option. Push `dev` to my fork, showing me first what it publishes. **Update `DESIGN.md` once, at the end of M3, covering all M3 changes.** Then start group 3: show me D3, the normalisation scope and #11, with the options, the current behaviour and your recommendation, and stop for my decision.
- 2026-11-06: **Exception to the testing rule, for the six M2 fixes only.** They are evident fixes: check them by reading and the import smoke test only, with no data tests.
  - Before this, a few data tests had started. They stay in the work folder:
    - `tests/m2/test_numpy_attrs.py`, a static scan for NumPy attributes that the installed NumPy lacks: 4 hits before #1 (the `np.NaN` lines), 0 after;
    - `tests/m2/run_creta_grid.py`, run once on the unfixed branch, where it failed at `creta.py:867` as expected;
    - logs in `tests/m2/logs`, and the empty output folder `tests/m2/out/t1_grid_before`.

### Awaiting my OK
- M3 decisions, from `reports/M3_plan_2026-11-14.md` (2026-11-14). For each, when we reach its group: show me the options, the current GOALS behaviour and your recommendation.
  - D3a–e: flux normalisation and #11: a relative lower-bound test in `check_fit_pars`; what `scale_flux_params` scales (line and PAH `_Peak` value, stderr and bounds; not `o_*_Peak` or `_FLX`); a parcube fully in physical units; products from continuum profiles rebuilt from the unscaled spectrum; whether `norm_factor` is still needed after #11.
    - 2026-11-15, shown to me with options and a recommendation; my decision pending. Measured on `dev` (`1f16eb7`, work folder, no code change): the tutorial fit (fixture setup, now with the 1% floor) on the same spectrum read with `read_spec(flux_scale=k)`. The χ² surface is the same for every k.
    - k = 10⁻⁴ (peaks ~10⁻⁶–10⁻⁵ Jy, as in a faint spaxel): spectral χ²/N 77,611; 57 of 84 line/PAH peaks at 0 (56 fixed at the lower bound by #11); 54 parameters free at the end. The optimiser itself drove bright features to ~0 before #11 fixed them ([O IV] 25.9 µm: 0.20 Jy at k = 1, 6×10⁻⁷ Jy here, in the original units). So fixing #11 alone would not rescue this fit.
    - k = 1: χ²/N 21,659; 8 peaks at 0 (7 fixed by #11); 102 free. k = 10⁴: χ²/N 23,950; 8 peaks at 0 (3 fixed by #11); 101 free. Yet against k = 1, STB_FLX is 0.53×, VGRAD 5.9 instead of 15.4 km/s, HOT_FLX 1.13×, and the peaks differ by 11% (median of 74). The optimiser is not unit-invariant: SciPy `least_squares` (TRF) with `x_scale = 1`, and a finite-difference step that is absolute (1.5×10⁻⁸) for parameters below 1.
    - The plan's D3a (a relative lower-bound test) is withdrawn: the peaks' lower bounds are 0, a relative tolerance around 0 is 0, and `least_squares` never lands exactly on a bound, so the test would never fire.
    - Recommended: automatic normalisation of each spectrum (each spaxel) by its own median |flux| before the fit, scaled back after; no new argument. The #11 tolerance then acts in units of the data scale, with no change in `check_fit_pars`. Scope: spectrum and photometry divided; only the line/PAH `_Peak` value, stderr, min and max scaled; parcube fully physical; `cont_profs['flux0']` scaled back for the products.
  - D4: the reference-PAH continuum window (±γ_PAH or ±10,000 km/s).
  - D5: the photometry-only model grid density.
  - D6: `stitch_to_shortest` at no-overlap gaps.

- Which real cube is the M4 benchmark (cube-fit performance).
- A separate physics decision, for later (noted 2026-11-14 with D2): add a systematic error floor to the spectral uncertainties? In the tutorial fit (the M3 fixture), the median quoted error is 0.028% of the flux, while the model misses the data by 1.2% (median), so χ²/N ≈ 21,000. With errors like these, the spectrum outweighs everything else in the fit, photometry included. *(Decided 2026-11-15: a 1% floor; see "Decisions".)*
- 2026-11-15: **Photometry weighting scheme: tested on real data (my request); my decision pending.** *(Decided 2026-11-15: option C stays; see "Decisions".)* No code change on `dev`; variants run from the work folder.
  - Case: W2246 (unresolved), as in my notebook `myCAFE_1D+photo_CYGNUS.ipynb`: MRS spectrum `W2246_SingleExt_r0.5as.fits` (z = 4.6, 11,197 channels, 0.88–5.1 µm rest, median SNR 57), 13 photometric points (1.5–882 µm observed, median SNR 12), `inpars_jwst_miri+phot_W2246.ini` with its five W2246 tables, `photometry_opt.cafe`.
  - NGC7469 left out: no matching-aperture photometry. The GOALS table on Gluon and my notebook's `NGC7469.txt` are galaxy-integrated; the notebook scales the 1.2″ spectrum by 1.7 to meet them.
  - (a) option C (`dev`): spectral χ²/N 23.6; photometry 13% of the minimised χ².
  - (b) formula B: 24.2; photometry 76% (SNR factor (57.2/12.3)² = 21.5).
  - (c) option C + 5.6% floor in quadrature (in the χ² only): 24.4 with the quoted errors, 3.4 with the floored ones; photometry 51%.
  - The fit is nearly the same in all three: each point's residual changes by at most 0.1σ (IRAC 3.6 µm +5.8σ, 4.5 µm −3.7σ, WISE 22 µm +2.7σ, 882 µm −2.1σ, the other nine within 0.9σ), and only 14 parameters vary. So W2246 cannot tell the schemes apart.
  - Floor rule: "χ²/N = 1 from the residuals of a fit without a floor" gives 27% on W2246. It is driven by the low-SNR blue end (0.9–1.5 µm rest: χ²/N 4–9, errors too small by 2–3×) and the 3.3 µm feature (15–23% misfit), not by a fractional systematic. Not usable as a general rule.
  - Proposed rule instead: the instrument's documented calibration uncertainty, added in quadrature, as the photometric errors include calibration (MRS: 5.6 ± 0.7%, Argyriou et al. 2023, A&A 675, A111; Law et al. 2025, AJ 169, 67, refine the calibration without one headline number).
  - Open with it: a calibration error is mostly a common scale, which a per-channel floor only approximates; and whether `check_fit_pars` (which zeroes features below 0.5σ) should see the floored errors.
  - Seen in passing: inside the spectrum, WISE 22 µm is 1.4× the model fitted to the spectrum, while WISE 12 µm agrees to 0.4%.
- 2026-11-15: **Spectral error budget: synthetic known-truth test done; my decision pending.** *(Decided 2026-11-15: a 1% floor; see "Decisions".)*
  - Truth: the M3 fixture model (NGC7469 tutorial fit) on the tutorial spectrum's 9,695 channels with its quoted errors (SNR ~3,500). Spectrum = 1.05 × truth × (1 + 1.5% rms sinusoidal ripple in log λ, 15 cycles) + noise. 8 photometric points (2.2, 3.6, 4.5, 24 [inside the spectrum], 70, 100, 160, 250 µm), 5% or 7% errors. One noise realisation (seed 20261115). Fits with `inpars_jwst_miri_AGN.ini` and `photometry_opt.cafe`.
  - Variant (2) uses a 1.5% floor, equal to the injected mismatch: the best case, since in real data the level is not known.
  - Photometry's share of χ²: (1) 0.26%, (2) 18%, (3) 0.16%. Spectral χ²/N with the quoted errors: 2,363, 2,518, 2,358; (2) is 0.70 with its floored errors.
  - Shape parameters (truth → error): WRM_TMP −9.2%, +1.3%, −10.3%; COO_TMP −2.3%, +0.9%, −1.2%; COO_TAU +17%, −9%, +18%; WRM_TAU −24%, −4%, −43%; STB_TAU −76%, +4%, −60%.
  - Model at the far-IR bands (70–250 µm) / truth: (1) 1.13–1.17, (2) 0.98–0.99, (3) 1.11–1.14. Near-IR bands (2.2, 3.5 µm): (1) 0.86, 0.82; (2) 1.01, 1.03; (3) 0.94, 0.86.
  - Absolute fluxes / truth, cool dust (28% of the truth's flux), warm dust (24%), starburst (41%): (1) 0.98, 1.10, 0.84; (2) 1.05, 1.03, 0.87; (3) 0.98, 1.08, 0.93. Feature peaks (median of 79): 1.01, 1.05, 1.00.
  - (3): the scale stays at its prior, s = 1.007 ± 0.044 (truth 1.05). Without a floor, the mismatch dominates the spectral χ², and the photometry has too little leverage to set s.
  - (2) recovers the shape and the far-IR, but everything tied to the spectrum keeps the 5% calibration offset (features +4.8%, dust fluxes +3–5%, the 4.4 and 24 µm bands +5–7%). Floor plus scale together (not run) is the obvious candidate to remove it.
  - In all three, the hot dust (3.4% of the truth's flux) is poorly recovered (fHOT 1.3–2.6×; HOT_TMP at its upper bound in (2)), and the AGN disc (0.002%) is unconstrained. This is a degeneracy, not an error-budget effect.
- 2026-11-15: **Floor sensitivity (my request): true mismatch 1.5%, fitted with floors of 0.75%, 1.5% and 3%; my decision on the floor pending.** *(Decided 2026-11-15: a 1% floor; see "Decisions".)* Same data and code as above; only the floor changes (`synth_fit.py <checkout> Cfloor <floor>`; logs `synth_Cfloor_0.0075.txt`, `synth_Cfloor_0.03.txt`).
  - Photometry's share of χ²: 6.7%, 18%, 44%. Spectral χ²/N with the floored errors: 2.69, 0.70, 0.18 (quoted errors: 2,483, 2,518, 2,555). Option C alone: 0.26%.
  - The recovery holds across the factor of 4. COO_TMP +0.7%, +0.9%, +0.8%; WRM_TMP +1.1%, +1.3%, −0.0%; COO_TAU −8.6%, −9.1%, −9.3%. Far-IR bands (70–250 µm) / truth: 0.984–0.997, 0.978–0.994, 0.976–0.993 (option C alone: 1.13–1.18). 2.2 µm: 1.01 in all three.
  - It weakens at 3%, twice the mismatch: WRM_TAU +4%, −4%, −17%; STB_TAU −6%, +4%, +14%. The spectrum's hold on the silicate absorption loosens.
  - The 3.5 and 4.4 µm bands (just blueward of the spectrum) follow their noisy photometric points more as the floor grows: model/truth 1.02, 1.03, 1.04 and 1.05, 1.07, 1.08, where the data are 1.04 and 1.09 × truth. This is photometric noise being fitted, not a bias.
  - Unchanged by the floor: the 5% calibration offset in what the spectrum pins down (24 µm band 1.049, cool dust 1.05, feature-peak median 1.04, 1.05, 1.03), and the hot-dust / AGN-disc degeneracy (fHOT 2.0–2.6×, HOT_TMP 1,022–1,027 K vs 695 K).
  - Not tested: floors between 0 and 0.75%, where the photometry's leverage falls from 6.7% to 0.26%; other noise realisations (differences of ~1% between the runs may be noise).
  - Cost (information only): 30,004 fit steps at 0.75%, 8,227 at 1.5%, 7,405 at 3%.

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
- 2026-11-14: Photometric weights (D2, now in `cafe_grinder`), end points: the first and last points of the combined spectral + photometric wavelength list get the full gap to their one neighbour as Δλ, while interior points get half the distance between their two neighbours. So an end photometric point (e.g. the longest far-IR band) gets about twice its share. Not acted on.
- 2026-11-14: Photometric weights (D2), R₀: it is estimated from the mean sampling over the whole spectrum, assuming 2 channels per resolution element. In the tutorial spectrum R₀ = 2,513, while the sampling at 24 µm gives 2,000. Not acted on.
- 2026-11-14: `make_profcube` calls `get_model_fluxes` once per profile per spaxel. With the 10 contcube profiles of M3 1d (3 before), building the contcube takes about 3.3× as long. It doesn't matter for 1D spectra, but it adds up for cubes. Information for M4.
- 2026-11-14: `cafeplot`'s residual panel uses the combined spectral + photometric arrays. So it joins the photometric residuals to the spectral ones with a line, and its ±4σ y-range includes them. Display only; seen in the M3 group 2 real fit. Not acted on.
- 2026-11-14: The contcube `WAVE` table is float32 (since M1 item H7). In the tutorial spectrum, the sub-band overlaps hold wavelengths only 2×10⁻⁷ µm apart, which float32 cannot separate. So 179 adjacent `WAVE` entries are equal; the fit's float64 grid is strictly increasing. This was already in the fixture contcube, before group 2. Not acted on.
- 2026-11-15: Spectral error floor: the parameters' uncertainties come from the fit, so they reflect the floored χ² (lmfit rescales the covariance by χ²/dof, `scale_covar=True`). That covers the parcube `STDERR` and the relative-error tests in `check_fit_pars` (`REL_ERR_*`); only its 0.5σ peak test uses the quoted spectral errors. Not acted on.
- 2026-11-15: The line table's empty rows (lines not fitted) come out in a different order from run to run; the rows themselves are the same. Seen in the synthetic fits. Not acted on.
- 2026-11-15: The fit's result depends on where the optimiser stops. The tutorial spectrum in units 10⁴ times larger converged (FTOL = 10⁻⁵) to STB_FLX 0.53× and VGRAD 5.9 instead of 15.4 km/s, with χ²/N 10% higher. So for degenerate parameters such as STB_FLX and HOT_FLX, the spread from the optimiser's path alone is up to ~2×. A convergence and degeneracy question for later (fit settings are my decision). Not acted on.
- 2026-11-14: `CAFE_prof_generator` assumes the photometry is sorted by wavelength. It extends the model grid from `phot_dict['wave'][0]` and `[-1]`, and `read_phot` doesn't sort. With an unsorted photometry file, the grid may stop short of the bluest or reddest band. Not acted on. *(Logged as GOALS bug G1 the same day, with a failing case; see "GOALS bugs found after M2".)*
