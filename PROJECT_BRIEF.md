# CAFE development — project brief

Owner: Tanio Díaz-Santos. Started 2026-11-04.

## Goal
1. Bring my three CAFE versions (GOALS upstream, my fork, my local folder) into one checked, synchronised state, with **minimal** code changes and nothing reaching GOALS that I haven't approved line by line.
2. Freeze the old setup as legacy and continue in a clean workspace.
3. Develop CAFE further: spectrum fits first, then fits with photometry, then the speed of cube fitting, then clean-up and packaging (M4–M7).

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

### M3 — My local changes *(approved 2026-11-14; plan in `reports/M3_plan_2026-11-14.md`. **M3 complete 2026-11-15.**)*
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
- **Group 3 (`norm_factor` and #11, D3a–e) started 2026-11-15:** D3 shown to me (options, current behaviour, recommendation). `dev` pushed with my OK (`f45a02b`→`1523059`). Decided 2026-11-15 (see "Decisions"); two commits, `fit_spec` then `fit_cube`, each shown and approved before the next.
  - Done as **one commit, `476c6ef`** (with the co-author trailer): `fit_spec` and `fit_cube` both fit through `cafe_grinder`, so the simplest form (CLAUDE.md §8) is one change there, which covers both, `init_parcube` and the neighbour initialisation. `cafe_grinder` divides the spectrum and photometry by the spectrum's median |flux|, scales the line/PAH peaks (value, min, max) and `cont_profs['flux0']` to match, and scales the peaks (with stderr) and `flux0` back after the fit, with a 7-line helper `scale_peaks`. Everything outside the fit stays physical.
  - Test `tests/M3/test_normalisation.py` (synthetic, no fit): failing case first, 17 of 33 checks fail on `6e81bfe`; after the change, 33/33 pass. Tests 2de and `test_spec_unc_floor.py` adapted to the normalised fit (their stubs now give `cont_profs` and a `Parameters` object, and expect the data divided by n). The M3 suite and the smoke test (18/18) pass.
  - Inputs (`scale_inputs.py`): for the tutorial spectrum at k = 10⁻⁴, 10⁴ and 1.0000001, what the fit sees equals k = 1 to 2×10⁻¹⁶ (spectrum, errors, `flux0`) and 10⁻¹³ (initial values); the bounds are identical.
  - 1D fits at k = 10⁻⁴, 1, 10⁴: χ²/N 21,723, 21,880, 21,687 (before: 77,611, 21,659, 23,950); line/PAH peaks at 0: 6, 7, 6 (before: 57, 8, 8). The products agree exactly with profiles rebuilt from the physical spectrum (contcube vs compdict fCON, ratio 1.0).
  - Cube (`cube_scale.py`, the 3×3 M1 grid cube) at k = 10⁻⁴, 1, 10⁴: all 9 spaxels fit in each. The first spaxel's MIN/MAX are identical across k (parcube fully physical); the other spaxels' bounds differ by ~10⁻³, because they are set around their neighbours' results, which differ.
  - The fits at different k are not identical, although their inputs agree to rounding: the fit amplifies rounding-level differences (see "Biases", 2026-11-15). A repeat at k = 1 is bit-identical; k = 1.0000001 gives STB_FLX 3.7×, COO_TMP +13%, peaks 5.4% (median), χ²/N −1.4%. So the fit is independent of the source's flux level in its inputs, not in its fitted values.
  - Approved 2026-11-15 with a wording change: the comment says the fit does not depend on the source's flux level (it said "flux units"), and the helper's docstring says the peaks are in Jy. Amended as `476c6ef` (it was `91475a3`, not pushed); the amended hunk is shown to me before the push.
- **Group 4 (`cafe_helper` physics choices D4, D5) started 2026-11-15:** shown to me with the options, the current behaviour and a recommendation (see "Awaiting my OK"). `dev` pushed with my OK (`1523059`→`7880a8d`, 5 commits, all mine, each with the co-author trailer). Decided 2026-11-15: D4 (a) and D5 (a), dev kept; my local versions are not brought in. **Group 4 done, with no code change.**
- **Group 5 (CRETA `stitch_to_shortest`, D6) started 2026-11-15:** shown to me with the options, the current behaviour and a recommendation (see "Awaiting my OK"). Changed the same day to one general option for the reference band (see "Decisions").
  - Done as commit `be4201c` (with the co-author trailer), +18/−21 in `creta.py`, `cube_preproc.py` and the two generic parameter files. `stitch_band` in the parameter file names the reference band as in `cubes` (default: the last). `stitchSpectrum` multiplies band idx by `prod(ratios[idx:]) / prod(ratios[ref:])`. Single and grid extraction both pass the reference. The grid now stitches its last band like the others; it used to append it unstitched, which assumed the last band was the reference. `stitch_to_shortest` is not ported.
  - Test `tests/M3/test_stitch_band.py` (synthetic bands with known factors; all overlapping, one gap, two gaps, no valid data in one overlap; every reference band): failing case first, 25 of 26 checks fail on `087c0a1`; after the change, 26/26 pass. That includes, with the last band as reference and no gaps, output bit-identical to `087c0a1`.
  - Real extractions (`stitch_run.py`, `stitch_compare.py`; the 12 NGC7469 MIRI cubes, a 0.5″ aperture and a 3×3 grid of 0.5″ spaxels), before and after the change: 17/17 checks pass.
    - Default, all 12 bands: single and grid outputs bit-identical to before, `_cube.fits` products too.
    - `stitch_band = ch1-short`: each stitched spectrum (and its errors) is the default one times one constant (1.44 for the single aperture, 0.58–1.73 for the grid spaxels; spread ≤ 9×10⁻¹⁶), and ch1-short keeps its own flux.
    - ch2-medium left out (a gap): the default changes only the bands before the gap, by one common factor (0.748, the chain from ch2-long to ch4-long). The bands from ch2-long on are bit-identical.
    - A name not in `cubes` stops the extraction with `ValueError: 'ch2-mediun' is not in list`.
  - The grid extraction runs only in `cafe-legacy`: in `cafe-dev` it fails before reaching the stitching (G4). The single extraction ran in `cafe-dev`. Smoke test: 0 failed.
  - Approved 2026-11-15. Next: fix G4 on `dev`; G5 and G6 stay logged for later (my decision, 2026-11-15).
- **G4 fixed on `dev`** (my request, 2026-11-15): commit `5c7085a`; tests and the two further grid failures it uncovered (G7, G8) under "GOALS bugs found after M2". Approved 2026-11-15. Not pushed.
- **`dev` pushed** 2026-11-15 with my OK (`7880a8d`→`beb8cf6`, the 5 commits shown to me).
- **The M3 list is done, apart from the `DESIGN.md` update** (checked 2026-11-15 against `reports/M3_plan_2026-11-14.md`): groups 1–5 done (1e skipped as planned), D1–D8 decided, and the spectral error floor added.
- **The grid extraction runs in `cafe-dev`** (my request, 2026-11-15): G7, G8 and the PSF-path half of G4 fixed on `dev`, 3 commits `56b4c75`, `d41e6b1`, `1e66caf` (with the co-author trailer); details and tests under "GOALS bugs found after M2". Approved 2026-11-15. Not pushed.
- **`DESIGN.md` updated for all M3 changes** (2026-11-15, the last M3 step): the opt-file option, `read_spec`/`read_phot`, the normalisation, error floor and photometric weights in `cafe_grinder`, the products, a new section on CRETA's extraction and stitching (with the photutils dependence), and a list of the M3 commits. Updated again 2026-11-15 with G6, G9 and G5 and the cube flow's "M4 target" (my request). Waiting for my review. Not pushed.
- **Before M3 is marked complete: G5 and G6** (my request, 2026-11-15).
  - G6 fixed on `dev`, commit `82539c1`, approved 2026-11-15. G9 fixed, commit `744dc2a` (a typo fix: `r` was meant to be `r_ap`). G5 option (a), commit `8177bb6` (my decision). Details under "GOALS bugs found after M2". G9 and G5 wait for my approval. Not pushed.
  - The "CRETA aperture-correction path" item (G10, G11 and G11's two related problems) stays open, to be fixed and tested end to end together once CRETA's PSF cubes are found (my decision, 2026-11-15).
  - `dev` pushed 2026-11-15 with my OK (`beb8cf6`→`1926c7b`, 12 commits).
  - G12 fixed on `dev`, commit `1fc4f5a` (my request, 2026-11-15); details under "GOALS bugs found after M2". `DESIGN.md`'s M3 list gets it. Approved 2026-11-15.
  - Naming rule (CLAUDE.md §9, my decision 2026-11-15) applied: `r_in` and `width` in `singleExtraction` renamed `bkg_ann_r_in` and `bkg_ann_width`, commit `2297264` (8 lines; no change in behaviour), approved 2026-11-15. The generic names that M3's commits introduced were listed with proposed names ("Awaiting my OK"); decided 2026-11-15 (see "Decisions") and applied, one commit per file area:
    - CRETA, commit `5b0b051`: `ref_band` and `stitchSpectrum`'s `ref` → `stitch_ref_idx`; `ratio` → `band_to_ref_multiplier`; `xx, yy` → `x_center_pix, y_center_pix`. Tests: the five real extractions (`single_all`, `single_all_ch1s`, `single_gap`, `grid_all`, `grid_all_ch1s`) give the same files as on `45a06f8` (FITS data and metadata, `.csv`, parameter-file copy), and `test_stitch_band.py` passes 26/26.
    - `5b0b051` (CRETA) approved 2026-11-15, with `1fc4f5a` (G12).
    - First CAFE commits (`dd2c22e`, `b4d547a`, both bit-identical on the seeded real fit) replaced the same day under the naming rule's addition (my decision): `par` stays `par`; `scale_peaks` takes `spec_norm_factor` and divides by it; `wave` and `R_0` stay, with the original comment. History rewritten from `5b0b051` (local commits only).
    - `a763bd4` (`scale_peaks` dividing by `spec_norm_factor`) replaced the same day (my decision): `scale_peaks(params, scaling_factor)` multiplies the peaks (value, bounds, stderr) by `scaling_factor`; the calls are `scale_peaks(params, 1 / spec_norm_factor)` going in and `scale_peaks(result.params, spec_norm_factor)` coming back; `par` stays. History rewritten again from `5b0b051` (local commits only). Its seeded run had moved the fit's end point; that run used the fake-photometry setup, so it showed only that the fit moved, not which end point is better (CLAUDE.md §10).
    - CAFE fit driver, commit `2ae9cb4` (`cafe.py`): `factor` → `scaling_factor` (`scale_peaks`); `norm` → `spec_norm_factor`, `k, v` → `comp_name, comp_flux0`, `floor` → `spec_unc_floor`, `spec_fit` → `spec_with_unc_floor`, `s` → `spec_phot_sort_idx`, `dl` → `spec_phot_delta_wave` (`cafe_grinder`); `par`, `wave` and `R_0` stay. The arithmetic is as before the renames.
    - CAFE output, commit `7f2988c` (`cafe_io.py`, was `b113094`, approved 2026-11-15): `p` → `par` in the `fitParsErr` comprehension.
    - Static check (`static_names.py`; stdlib `ast`, `symtable`, `tokenize`, as no linter is installed) of `scale_peaks`, `cafe_grinder`, `save_asdf`, `stitchSpectrum`, `singleExtraction` and `gridExtraction`: no undefined names, no leftover old names, no shadowing by an M3 name, and every M3 name bound once. In `cafe_grinder`, `spec` and `phot` are rebound on purpose to their normalised copies (the caller's dicts are not changed, except that `phot['weight']` is written into the caller's photometry dict before the rebinding; nothing in the products uses it), and `params` as before M3. The other hits are older code: G13 (below); `gridExtraction` reads `PSF_all` before it is set (G10, in the aperture-correction item); keyword arguments overwritten from the parameter file (API clean-up); local `time`, `user`, `preprocess` and a local import of `drude_int_fluxes` shadowing module names; generator-expression variables reusing loop-variable names.
    - Functional check against `45a06f8` (setup: `NGC7469_SingleExt_r1.5as_MIRI.dat`, z = 0.0163; shipped `inpars_jwst_miri_AGN.ini` and `photometry_opt.cafe`; the 5 fake points of `inputs/phot5_obs.txt`: IRAC1 3.55 µm 0.08 ± 0.008 Jy, PACS70 30 ± 3 Jy and PACS160 15 ± 1.5 Jy (synthetic M3 test points), FAKE1 2.5 µm 0.08 ± 0.01 Jy and FAKE2 32 µm 3.0 ± 0.2 Jy (from my notebook's `NGC7469_phot.dat`); 92 parameters free at the end; `PYTHONHASHSEED=0`): all 7 products bit-identical (`rename_compare.py`, 7/7). The synthetic M3 suite passes, 0 FAIL lines. Smoke test: 0 failed.
    - `2ae9cb4` approved 2026-11-15.
    - Tests (real single extractions, `cafe-dev`; `g12_meta.py`): with background subtraction on (`single_all_bkgsub.txt`: `r_ann_in = 0.8`, `ann_width = 0.3`), the output after the rename is bit-identical to the code before it (`7396590`, worktree `cmp/rename_before`), data, `_cube.fits` and metadata string; `single_all_bkgmeta` and `single_all` likewise against the G12 runs. Smoke test: 0 failed.
- **M3 complete** (my decision, 2026-11-15). Everything in `reports/M3_plan_2026-11-14.md` is done or decided, `DESIGN.md` covers the M3 changes, and every M3 commit is approved. `dev` pushed to my fork with my OK (`1926c7b`→`6b9136c`, 10 commits). Carried over, not part of M3:
  - the "CRETA aperture-correction path" item (G10, G11 and its two related problems), to be fixed and tested end to end once CRETA's PSF cubes are found;
  - G13 (`save_asdf`'s undefined `self`);
  - the clean-up list, now M7 (dead and commented-out code, generic names, keywords the parameter file overrides, the line table's row order);
  - M4 to M7 (split 2026-11-15) each start only after my approval (CLAUDE.md §1).
- Start only after my approval (CLAUDE.md §1).
- Covers the bugs that exist only in my local changes.
- Bring my local changes from `local-wip-2026-11` (`135aa70`, in the pre-sync folder) into `dev`, one at a time, each tested.
- The changes and the findings on each are in the M1 report. The 8 items merged in GOALS PR #99 are already in.
- Claude co-authorship applies from here, only on commits that stay on my fork. `.claude/settings.local.json`: commit attribution on and PR attribution off since 2026-11-14 (CLAUDE.md §2).

Milestone split decided 2026-11-15 (my decision): M4 to M7 below. **Each milestone starts only after my approval** (CLAUDE.md §1). The CRETA aperture-correction path stays a separate item until the PSF cubes are found.

### M4 — Fitting a JWST spectrum alone *(approved 2026-11-16)*
- Check that fitting a JWST spectrum alone works well, including the non-unique convergence.
- **Important finding (logged 2026-11-15): the fit does not converge to a unique minimum.** In the tutorial fit (`476c6ef`), inputs that differ only by rounding (2×10⁻¹⁶) move STB_FLX by 3.7×, COO_TMP by 13% and the line/PAH peaks by ~5% (median), while a repeat is bit-identical (see "Biases", 2026-11-15).
  - Fit settings (`FTOL`, `MAX_LOOPS`, `FIT_CHK`, `max_nfev`, method) stay my decision (CLAUDE.md §4).
- **Stage 1 plan** (approved 2026-11-16; see "Decisions"). `dev` @ `fa348d8` in `cafe-dev`, no code change. Tests in `tests/M4/` (work folder); they only record what lmfit returns. `PYTHONHASHSEED=0`. Every setup uses the shipped `default_opt.cafe` (FTOL 10⁻⁵, `SPEC_UNC_FLOOR` 0.01, `FIT_CHK` True, `MAX_LOOPS` 5, `FitPhot` False) and no photometry.
  - R1 (AGN): the NGC7469 tutorial spectrum `NGC7469_SingleExt_r1.5as_MIRI.dat`, z = 0.0163, `inpars_jwst_miri_AGN.ini`; 129 parameters free at the start.
  - R2 (starburst): NGC3256 nuc1, my extraction `my_notebooks/extractions/NGC3256_nuc1_SingleExt_r0.15as_cube.fits` (pre-sync folder; MIRI, 0.15″ cone), z = 0.009354, `inpars_jwst_miri_SB.ini`; 88 free at the start.
  - S1 (known truth): R1's plain-fit model on R1's wavelengths, plus one realisation of Gaussian noise at the floored errors √(σ_quoted² + (0.01 F)²). Fitted with the quoted errors and R1's inpars and options, from the inpars' starting values.
  - Each setup is fitted 10 times, with `read_spec(flux_scale = 1 + j·10⁻⁷)`, j = 0…9: inputs that differ only by rounding; j = 0 is the plain fit.
  - Measured: how each fit stops; χ² with the floored and the quoted errors; the spread of every parameter, of the component fluxes over the observed range, of the PAH and line fluxes and of the model, against the fit's stderr; for S1, also against the truth. "The same fit" means Δχ² < 1 in the floored χ².
  - Report: one short summary table per setup (stop reasons, χ² spread, spread of the key parameters and of the in-range component fluxes against their stderr, classification), with the details in a report file in the work folder. Then stop.
  - Stage 2 (the cause, with diagnostic fit settings) and a NIRSpec + MIRI spectrum are decided after stage 1.
- **Stage 1 done 2026-11-16.** Report: `reports/M4_stage1_2026-11-16.md` (work folder). All 31 fits (10 per setup, plus a repeat of R1 j = 0, bit-identical) wrote every product, and every last `minimize` stopped on `ftol`.
  - The end points are not the same fit. In R1 and R2 only the best fit is within Δχ² < 1 of the best; the others end up to Δχ² = 1,300 (R1) and 3,100 (R2) above it. S1: up to 25.
  - R1: no refits, all parameters free to the end, and the fits that run longer reach a lower χ² (rank correlation −0.98).
  - R2: STB_FLX goes to 0 in every fit; lmfit then returns no error bars and the refit loop ends in different models (57–66 free); 3 fits end without error bars.
  - The fit's stderr understates the spread (R1 up to 2.3×, R2 up to 59×).
  - S1's truth is out of the fit's reach: `init_feats` dropped three of the truth's lines on S1's data (+811 in χ²), so S1 cannot show whether the optimiser reaches the minimum.
  - Waiting for my review. Stage 2 not started.
- **M4 order from here** (decided 2026-11-17; stop after each step):
  1. The zero-flux freeze (see "Decisions", 2026-11-17), and a check whether opacity features need the same. Diff hunk by hunk with reason paragraphs and tests; wait for my approval.
     - *(Done 2026-11-17, approved 2026-11-17: commit `d6bd782`, `check_fit_pars` fixes every other parameter of a component whose `_FLX` is at 0, by name prefix.)*
     - Synthetic test (`test_zero_flux_freeze.py`; all 7 shipped inpars, every component, with and without error bars): 98/126 cases before (`STB_100`, `STB_010`, `PAH_MIX`, `PAH_COV` left free), 126/126 after.
     - R2 rerun (10 fits): refits 30 → 10; fits ending without error bars 3 → 0; none uses all 5 loops. The χ² spread is unchanged (Δχ² up to 3,110): the freeze does not touch the convergence problem. R1 and S1 can't change: no `_FLX` reached its lower bound there.
     - Opacity features (`o_`) need nothing new: when their peak reaches 0, `check_fit_pars` already fixes their Wave and Gamma (the branch shared with lines and PAHs). Two related questions were decided 2026-11-17 (see "Decisions").
     - *(Follow-up done 2026-11-17, approved 2026-11-17: commit `672749d`. One rule after the other checks replaces `d6bd782`'s block: every free parameter that no longer affects the model is fixed (all other parameters of a component whose `_FLX` is 0; the MIX and COV of a component whose `_TAU` is 0, also when the TAU is set by an expression), except one that another component's expression uses.)*
     - Synthetic test, extended (`test_zero_flux_freeze.py`; cases FLX, TAU reaching 0, TAU fixed at 0, a synthetic tie `HOT_COV = COO_COV`, and none at 0; 7 inpars, with and without error bars): 294/490 cases before (on `d6bd782`: `WRM_TAU` fixed when `WRM_FLX` is 0; MIX and COV left free when a TAU is 0; the tie not respected), 490/490 after. Import smoke test: 0 failed.
     - R1, R2 and S1 can't change, so no rerun: in their logs the only TAU at 0 is `HOT_TAU` (R1 j = 1, 2, 9 and every R2 fit), and `HOT_MIX` and `HOT_COV` are fixed in all 7 inpars; `WRM_FLX` never reached 0; and the components fixed at 0 in their inpars have all their other parameters fixed there too.
  2. From the stage 1 fits (no new runs): which `_FLX` ended at their 0 or 2 bounds, and how far each component's reference wavelength is from the observed range, so that I can decide whether the `flux0` fix comes before the stage 2 diagnostics.
     - *(Done 2026-11-17, waiting for my decision on the order: `step2_flx_bounds.py`, from the saved stage 1 fits on `fa348d8`, no new fits.)*
     - No `_FLX` ended at 2 in any of the 30 fits. The highest values: `HOT_FLX` 0.84 (R2), `WRM_FLX` 0.90 (R1), `STB_FLX` 0.68 (R1).
     - At 0: `STB_FLX` in all 10 R2 fits (fixed there by `check_fit_pars`). `DSK_FLX` in R1 ends at 1.1–4.6 × 10⁻⁵, just above the 10⁻⁵ tolerance, and is fixed as unconstrained in all 10 fits. The rest are fixed in the inpars (CIR, CLD, STR at 0, DSK at 0 in SB, PAH at 1).
     - Reference wavelengths against the observed range (rest frame; R1 and S1 4.88–28.14 µm, R2 4.85–27.64 µm): COO 24, WRM 14, DSK 10 and PAH 6.22 µm inside. Outside, with `flux0` = the edge channel: HOT 3.5 µm (1.39× below the first channel), STB 2 µm (2.4×), STR 1.6 µm (3.0×); CLD 70 µm (2.5× above the last channel), CIR 450 µm (16×).
     - The model uses `_FLX` only through `_FLX × flux0`, so `flux0` sets the scale of `_FLX` and where its upper limit 2 lies, not the lower bound 0. In stage 1 the limit 2 never bound, and STB's zero in R2 does not depend on `flux0`.
  3. Stage 2 (convergence diagnostics on R1 and R2) and the S1 rebuild.
     - *(Done 2026-11-17, waiting for my review. Report: `reports/M4_stage2_2026-11-17.md` (work folder). `dev` @ `3fd0498`; diagnostic option copies in `tests/M4/inputs/`, no default changed; 10 fits per set, as in stage 1.)*
     - Sets: R1 restart (each `minimize` restarted from its end point until a restart lowers χ² by < 1), R1 FTOL 10⁻⁸ (SciPy's default `ftol`), R2 the same with `FIT_CHK` off, S1b plain and restart. `x_scale='jac'` (with restarts) on R2 and R1, as both were inconclusive: R2's end points stayed in separate groups, R1's chains were still falling when they stopped.
     - R1: the default fit stops on `ftol` partway along a long, shallow valley (HOT_FLX up, STB_FLX down, COO_TMP and COO_TAU down, STB_TAU up). Restarts take every fit 534–1,837 below stage 1 (COO_TMP 23.4 K in all 10) and were still falling ~2 per restart when they stopped; FTOL 10⁻⁸ stops on `xtol` 82–262 above them.
     - R2: two separate minima, with the cool and warm dust temperatures swapped (30.5/59.4 K and 59.4/29.5 K, Δχ² ≈ 3,000); restarts and FTOL 10⁻⁸ leave each fit where it is. `x_scale='jac'` reaches the better one in all 10 fits; 8 of them end lower than any fit without it (best 288,938, 123 below the best without it).
     - G14 (see "GOALS bugs found after M2"): the dust emissivity jumps in temperature, and fits stop on the jumps: R2's HOT_TMP at 649.49 K in 21 of 40 fits; every R1 fit below χ² ≈ 117,000 (all with `x_scale='jac'`, down to 105,009 with COO_TMP at 6.35 K) has a dust temperature on a jump.
     - S1b (S1 rebuilt so the truth has only lines the fit keeps; χ²(truth)/N 0.986): the shipped settings reach the minimum to within the noise (χ²(fit) − χ²(truth) = −139 to −135, expected ≈ −128 ± 16); every key parameter within 1 stderr of the truth; component fluxes within 1% except fHOT 0.96–0.97 and fSTB 1.06; line and PAH peaks median 0.999.
     - HOT_FLX against STB_FLX at equal χ²: R1, 3 fits within Δχ² < 1: rank correlation −1.0, fHOT + fSTB 6–10× steadier than either, but HOT_FLX spans only 0.788–0.790. Across all R1 fits (−0.99) the trade-off runs along the valley, with χ² changing. R2: STB_FLX at 0 in 29 of 40 fits. S1b: −0.83 (6 fits), with the sum as variable as the parts (~1%).
  4. The G14 fix (decided 2026-11-18; see "Decisions"), and a proposal of non-overlapping dust T ranges for each shipped inpars file. No inpars file changes until I choose them.
     - *(Done 2026-11-18, approved 2026-11-18: commit `93a90dc`, `grain_totemissivity` takes the two grid temperatures that bracket T (`np.searchsorted`; the end pair outside the grid). No PR to GOALS.)*
     - Failing case `emissivity_jumps.py` on `5ddb29d` (real E_COO, E_WRM, E_HOT on R1's wavelengths): 28 jumps, median a factor 17 at 6.35 K, 46% at 12.5 K, 5% at 26.6 K. After: 10⁻⁸–10⁻⁷ across each former jump (the slope over 2×10⁻⁹ in T); j at every grid temperature and at 1, 2.5, 1800 and 3000 K bit-identical to before.
     - Synthetic test `test_G14_emissivity.py` (known answer: the grid values, the log–log line between the bracketing grid temperatures, the end-pair line outside the grid; two sets of grain fractions): 526/586 cases before (the 28 points just above each former jump and 2 inside the extrapolated bands fail, by up to 54%), 586/586 after. Import smoke test: 0 failed.
     - T ranges proposed (see "Awaiting my OK").
     - *(Done 2026-11-18, approved 2026-11-18: commit `4ab23ea`, COO 3–50 K, WRM 50–200 K, HOT 200–1027.2 K in the six shipped inpars files other than IIZw096; COO starts at 40 K in the two AGN files. Checked: all parse with these bounds and every start lies inside its range.)*
  5. Stage 3: rerun R1, R2 and S1 regenerated (S1c), with the fixed model and the new ranges, before the `flux0` fix (plan approved 2026-11-18; see "Decisions").
     - *(Done 2026-11-18, waiting for my review. Report: `reports/M4_stage3_2026-11-18.md` (work folder). `dev` @ `ffb257a`, shipped `default_opt.cafe`; 90 fits: R1, R2 and S1c × plain, restart (stop when 5 successive restarts together lower χ² by < 1), `x_scale='jac'` + restart, 10 each.)*
     - S1c: truth = R1's stage 3 plain fit (j = 0) with [Al VI] 9.12, [Ar V] 13.10 and broad Na VIII 5.18 µm at 0 (`init_feats` drops them on S1c's data); after that, every true line (74 peaks > 0) is in the fit's set.
     - G14 and the ranges: no end temperature on a former jump (90 fits). R2 no longer swaps (all at COO 30.5, WRM 59.4 K); its plain fits now agree (9 of 10 within Δχ² < 1 of each other; spread 3,103 in stage 1).
     - R1 has two end states. A (restart, all 10): HOT 665 K, STB_FLX ≈ 0.001. B (`x_scale` + restart, 9 of 10), 773 lower: **HOT_TMP at its 200 K lower bound**, HOT_FLX 0.11, STB_FLX 0.58, COO 16 K, WRM 71 K; B gains 5,215 in channel 4C (24.4–28.8 µm observed) and loses ~4,400 elsewhere. The plain fits stop on `ftol` between them, 1,246–2,549 above B, as in stage 1: R1's plain-fit problem is not G14.
     - `x_scale='jac'` + restart: best on R1, worse than plain on R2 (8 of 10 end 26–353 above the best, plain 19.5–21.3), as good as restart alone on S1c.
     - S1c: plain fits 9 of 10 at −143 to −127 below χ²(truth) (expected ≈ −127 ± 16), one at −85; restart and `x_scale` sets −147 to −136. The converged fits agree with each other but sit 2–3 stderr from the truth in COO_TMP, COO_TAU and WRM (one noise realisation). HOT_FLX and STB_FLX anticorrelated within equal-χ² groups (ρ −0.96 to −1.0): fHOT 0.75–0.96, fSTB 0.70–1.23 of the truth.
     - Cost (information): 3 h 05 min at 4 at a time, 12.0 h of fit time.

### M5 — Fits with real photometry
- Fits of a JWST spectrum together with real photometry. The fake-photometry setup is for functional checks only (CLAUDE.md §10).
- Refit, with the G14 fix (`93a90dc`), my pre-sync fits that have a temperature on a G14 jump: 51 of 121 distinct fits, CLD_TMP at 6.351 K in 42 of the 91 with CLD free, mostly the CYGNUS fits (logged 2026-11-18; see "Biases", G14).

### M6 — Cube-fit performance and parallelisation
- Includes the fitting order (#6): the image for the fitting sequence is, for now, the `nansum` over all channels (M2, temporary); a proper SNR image is still to come (see also "Biases", 2026-11-04). Includes `NPROC` (#15).
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
- The non-unique convergence (M4) sets the spread: any speed-up that changes the floating-point order (caching, parallel spaxels, a cheaper `get_model_fluxes`) will move results by this much. The baseline comparison and its tolerances must allow for this spread.

### M7 — Clean-up and packaging
- Packaging: pyproject-only, correct dependencies.
- Logging instead of `print`.
- Generic variable names elsewhere in CAFE and CRETA (naming rule, CLAUDE.md §9, 2026-11-15): rename them to names that identify what they hold. Includes the older names on lines M3 rewrote: `tab` in `read_phot`, `cmap` in `gridExtraction`, `aper` in `doPSFGridPhotometry`, `stitchSpectrum`'s `idx`, `ratio_list` and `spectrum`, and the parameters `r_in`, `width` of `getSubCubes` and `doBackgroundSubtraction`.
- Removing dead and commented-out code. Includes `sliceGridExtractionPhotometry` in `CRETA/cube_handler.py` (not called; it still passes the cube's 3-D WCS to `aperture_photometry`, G4).
- The other items logged for the clean-up in this brief (e.g. keywords the parameter file overrides, the README's keyword tables, the line table's row order, G13).

### CRETA aperture-correction path (separate item, not a milestone)
- G10, G11 and G11's two related problems (see "GOALS bugs found after M2"): fixed and tested end to end together once CRETA's PSF cubes are found, not with stand-in PSFs.

### Later (do not start)
- Tests and CI.
- A ratio constraint on the dust temperatures, like Onion's (`HOT_WRM`, `WRM_COO`), to keep the components in order (logged 2026-11-18; for now the order comes from non-overlapping T ranges in the inpars files).
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
- **G4: CRETA's grid extraction fails with the current photutils** (logged 2026-11-15). `doGridPhotometry` (`cube_handler.py:202–203`) passes the cube's 3-D WCS to `aperture_photometry`. photutils 3.1.1 (`cafe-dev`) uses it to compute the apertures' sky positions, which raises `TypeError: WCS projection has 3 dimensions…`. photutils 1.10.0 (`cafe-legacy`) runs. The single extraction passes `w.celestial` there (`cube_preproc.py:346`) and runs in both. This breaks the normal workflow on the current stack. It also corrects the M1 note on R2 ("photutils ignores `wcs` for pixel apertures"), which no longer holds.
  - **Fixed on `dev`**, commit `5c7085a` (2026-11-15, with the co-author trailer): both calls in `doGridPhotometry` pass `self.wcs.celestial`. The sums don't use the WCS (pixel apertures); CRETA reads only the sums and the pixel centres.
  - Failing case first: in `cafe-dev`, the grid extraction on `beb8cf6` stops at `cube_handler.py:202` with that `TypeError`.
  - After the fix, the photometry passes in `cafe-dev` and the run stops at G7, then at G8. With test-side stand-ins for both (`g4_run_dev.py`; nothing in the repo changed), the `cafe-dev` grid run completes. `g4_compare.py`: 14/14 checks pass.
    - `cafe-legacy`: the outputs after the fix are bit-identical to those before it (`grid_all`, `grid_all_ch1s`, `_cube.fits` too).
    - `cafe-dev`: with `stitch_band = ch1-short` each spaxel's stitched spectrum and errors are the default ones times one constant (0.58–1.74, spread ≤ 9×10⁻¹⁶), and ch1-short keeps its own flux.
    - Information: `cafe-dev` and `cafe-legacy` outputs differ, because photutils changed (see "Biases", 2026-11-15).
  - Smoke test: 0 failed.
  - Approved 2026-11-15.
  - The same 3-D WCS went to `aperture_photometry` in `doPSFGridPhotometry` (`cube_handler.py:222`, the grid's aperture-correction path, where G6 also applies). **Fixed on `dev`**, commit `56b4c75` (2026-11-15): it passes `self.wcs.celestial`. Its real path stays untested until G6 is fixed. Test `tests/M3/test_psf_grid_photometry.py` (synthetic, known truth: a uniform cube with a 3-D RA/DEC/WAVE WCS and squares on pixel boundaries, called on a stand-in object): failing case first, in `cafe-dev` the code at `d58797b` raises the `TypeError`; after the fix the sums are the true ones (18, 32, 18) in both envs, and in `cafe-legacy` bit-identical to the code before.
  - `sliceGridExtractionPhotometry` (`:355–356`, not called) also passes the 3-D WCS: left for the dead-code clean-up (my decision, 2026-11-15).
- **G5: CRETA with `parameter_file=False` cannot run** (logged 2026-11-15). `sel_cubes` and `files_sort` are set only when a parameter file is read (`creta.py:101–131`, `:777–792`, lines at `087c0a1`), so `singleExtraction` stops with a `NameError` at `params.append(str(sel_cubes))`, and `gridExtraction` when it loads the cubes. Not fixed.
  - Uses (checked 2026-11-15): none. CRETA itself never calls the extractions. All 29 live calls in my notebooks and scripts in the pre-sync folder (21 single, 8 grid) pass `parameter_file=True` explicitly, as do the shipped `CRETA/notebooks/IIZw096_MIRI_spec_CRETA.ipynb` and the 3 commented-out calls in `script/`. The only `parameter_file=False` are the two examples in `CRETA/README.md` ("parametrized via command line"), which could not run anyway: they leave out the required `data_path` and `parfile_path`.
  - Making the path work would be a feature: there is no keyword for `cubes` (or `stitch_band`), the file listing and sorting sit inside the parameter-file block of both functions, and the grid has no keyword branch at all.
  - Options shown to me 2026-11-15; decided the same day: (a).
  - **Fixed on `dev`**, commit `8177bb6` (2026-11-15, with the co-author trailer): `parameter_file=False` raises a `ValueError` in both extractions (`else: raise …` on the parameter-file block); the single extraction's keyword branch is removed, and so are the grid's now always-true condition on copying the parameter file (its block dedented, old commented-out lines included) and the two README examples. The keyword stays, so every existing call works. The comment on `@parameter_file` says it must be True.
  - Test `tests/M3/test_parameter_file.py`: failing case first, on `744dc2a` both extractions stop with `UnboundLocalError` (`sel_cubes`, `files_sort`); now both raise the `ValueError`. The real single and grid extractions (`single_all`, `grid_all`, `cafe-dev`) are bit-identical to before (`_cube.fits` too), and the parameter-file copy is written and identical. Smoke test: 0 failed.
  - Left as they are, for the API clean-up: several keywords of both functions are always overridden by the parameter file (e.g. `point_source`, `lambda_ap`, `centering`, `background` in the single; `centering`, `lambda_cent`, `nx_steps`, `ny_steps`, `step_size`, `user_center` in the grid), and the README's tables of keyword defaults.
- **G6: the grid extraction puts the PSF files into the data file list** (logged 2026-11-15). With `aperture_correction` or `convolve`, `gridExtraction` appends the matching PSF files to `files_sort` instead of `PSF_files_sort` (`creta.py:800–802` at `087c0a1`). Found by reading.
  - Confirmed 2026-11-15 with a real NGC7469 grid extraction with `aperture_correction=True` in `cafe-dev` (`g6_run.py`). CRETA's PSF cubes (the 218-plane cubes that `CRETA/PSF_centroids` and `CRETA/PSF_infaps` were made from) are not on this machine: not in the repo, its history, the pre-sync folder or the data folders. The webbPSF models in `/Volumes/Gluon/lowz/jwst/PSFs/MIRI/` (735×735 px, detector coordinates) and the simulated point-source cubes there (850 planes) don't match those tables. The simulated cubes stand in as PSF files (symlinks in `tests/M3/inputs/psf_sim/`): their names match `cubes`, which is all G6 needs.
  - Failing case: on `25af335`, the grid looks for the PSF cube among the data: `FileNotFoundError: …/NGC7469/Level3_ch1-short_s3d.fits` at `creta.py:851`.
  - **Fixed on `dev`**, commit `82539c1` (2026-11-15, with the co-author trailer): the PSF files go to `PSF_files_sort`, and the PSFs are loaded from that list (sorted like the data), as in the single extraction, instead of from every file in the PSF folder in directory order.
  - Tests: the grid with aperture correction now loads the 12 NGC7469 cubes as data ("Last cube is: ch4_LONG") and stops at the PSF loading on G9. `g6_lists.py` (a test-side value for the undefined name, to reach the PSF call): the data list holds the 12 NGC7469 cubes only, and the PSF list the same 12 bands in the same order. The default grid (no aperture correction) is bit-identical to `1e66caf`, `_cube.fits` too. Smoke test: 0 failed.
- **G9: the grid's PSF loading passes an undefined name `r`** (logged 2026-11-15; `creta.py:927` at `82539c1`, `user.getSubCubes(PSFs_path, PSF_files_sort, r, …)`). With `aperture_correction` (or `convolve`), `gridExtraction` stops there with `NameError: name 'r' is not defined`. It is a typo: `r` was meant to be `r_ap`, the radius the grid gives its data cubes, so the PSF is measured in the same aperture as the data, as an aperture correction requires (recorded 2026-11-15 as a typo fix, not a physics decision; my decision).
  - **Fixed on `dev`**, commit `744dc2a` (with the co-author trailer).
  - Rerun (`g6_run.py`, stand-in PSF files): the PSF cubes load and the grid photometry runs for all 12 bands; the run then stops at G11 (`creta.py:988` at `744dc2a`). Nothing is written into the repo. The default grid is bit-identical to `1e66caf`, `_cube.fits` too. The path stays untested end to end until CRETA's PSF cubes are found.
- **CRETA aperture-correction path** (G10, G11 and G11's two related problems; grouped 2026-11-15, my decision). To be fixed and tested end to end together once CRETA's PSF cubes are found, not with stand-in PSFs. So far the path has been run only as far as G11 (G6 and G9 were tested with stand-in PSF files, for the file handling only). Lines at `8177bb6` unless noted. Not fixed.
  - G10 (found by reading, logged 2026-11-15): with `convolve`, `gridExtraction` calls `fixConvolved` with `PSF_all` (`creta.py:918–920` at `82539c1`) before the PSF cubes are loaded (`:924–927`). The README says `convolve` is not supported.
  - G11 (logged 2026-11-15): the aperture-correction code reads `self.creta_path`, which is never set; `__init__` sets `self.creta_dir`. `creta_path` came in with my commit `0327e64` ("directory-changes", 2023). With aperture correction, both extractions stop with `AttributeError: 'creta' object has no attribute 'creta_path'`: the grid at `creta.py:972` (run, after G9), the single at `:251` (by reading, the same expression).
  - Related to G11: the single extraction looks for the PSF centroids in `centroids/`, while the repo folder is `PSF_centroids/`.
  - Related to G11: the writers for missing PSF tables (`userAPI.py:130`, `:152`, `:187`) write to paths relative to the current directory.
- **G14: the dust emissivity jumps in temperature** (logged 2026-11-17; found in M4 stage 2). `grain_totemissivity` (`dustgrainfunc.py`, non-FASTTEMP branch) interpolates log j linearly in log T between the two grid temperatures nearest to T (`np.argsort(tdiff)[:2]`), not the two that bracket T. The grid (`cafe_helper.py`: `geomspace(33, 1780, 30) − 30`) is not uniform in log T, so in part of each interval the code extrapolates from the pair on one side, and j jumps where the pair changes, at T = √(T₍ᵢ₋₁₎T₍ᵢ₊₁₎): 28 temperatures. Median jump over R1's observed range: a factor 17 at 6.35 K, 46% at 12.5 K, 13% at 19.1 K, 5% at 26.6 K, 1% at 56 K, 0.2% at 649.5 K. Fits stop on the jumps (M4 stage 2: R2's HOT_TMP at 649.49 K; R1's lowest χ² with COO_TMP at 6.35 K). Same code and grid in GOALS `master` (`ca10c84`). Failing case: `tests/M4/emissivity_jumps.py` (work folder). *(Fixed on `dev` 2026-11-18, commit `93a90dc`, approved 2026-11-18; test `tests/M4/test_G14_emissivity.py`. No PR to GOALS.)*
- **G13: `save_asdf` uses an undefined `self`** (logged 2026-11-15; found by the static name check). `cafe_io.save_asdf(cafe, …)` writes to `self.cafe_dir + "output/last_unnamed_cafefit.asdf"` when `file_name` is None (`cafe_io.py:1138`, GOALS code, 2023), so that call raises a `NameError`; it would also write into the repo's `CAFE/output/`. `save_products` always passes `file_name`, so the normal workflow is not affected. Not fixed.
- **G12: the single extraction's metadata records the background annulus from the keywords** (logged 2026-11-15; found by reading). `meta_dict` (`creta.py:351–353` at `8177bb6`) takes `bkg_r_in` and `bkg_an_w` from the keywords `r_ann_in` and `ann_width` (default `None`), not from the parameter file's values (`r_in`, `width`). Metadata only.
  - Failing case (real single extraction, `single_all_bkgmeta.txt` = `single_all.txt` with `r_ann_in = 0.8`, `ann_width = 0.3`, background subtraction off; on `eb89a4f`): the metadata string in the `.fits` table header records `'bkg_r_in': None, 'bkg_an_w': None`.
  - **Fixed on `dev`**, commit `1fc4f5a` (2026-11-15, with the co-author trailer): `"bkg_r_in":r_in, "bkg_an_w":width`, the values read from the parameter file (arcsec) and used for the background subtraction.
  - Rerun (`g12_meta.py`): 0.8 and 0.3 for `single_all_bkgmeta`, 0.0 and 0.0 for `single_all`; data and `_cube.fits` bit-identical to `after_single_all` in both. Smoke test: 0 failed. The grid's metadata writes fixed values (no background subtraction in the grid), which is right.
  - The keywords `r_ann_in` and `ann_width` now have no effect at all: for the API clean-up, with the other keywords the parameter file overrides (see G5).
- **G7: the grid extraction calls `plt.cm.get_cmap`** (logged 2026-11-15; `creta.py:1055`), which matplotlib 3.9 removed (`cafe-dev` has 3.11.2; `cafe-legacy`'s 3.8.2 still has it). In `cafe-dev` the grid run stops there with an `AttributeError`, after the photometry. It only picks the colours of the grid plot; `plt.get_cmap('hsv', n)` works in both. This breaks the normal workflow on the current stack.
  - **Fixed on `dev`**, commit `d41e6b1` (2026-11-15): `plt.get_cmap('hsv', …)`, the same colours in matplotlib 3.8.2 and 3.11.2, with no deprecation warning in either. Failing case first: the `cafe-dev` grid run on `56b4c75` stops at `creta.py:1055` with the `AttributeError`.
- **G8: the grid extraction reads the photometry columns `xcenter`/`ycenter`** (logged 2026-11-15; `creta.py:1092–1093`), which photutils 3.0 renamed `x_center`/`y_center`. photutils 3 still maps the old names on the table, with a deprecation warning, but not on a table row, which is what CRETA indexes. So in `cafe-dev` the grid run stops with `KeyError: 'xcenter'`. The values become the sub-cubes' `.xys`. This breaks the normal workflow on the current stack.
  - **Fixed on `dev`**, commit `1e66caf` (2026-11-15): `xx, yy = all_aps[i][j].positions[grid_point_idx]`, the same values from the aperture itself, with any photutils version (checked: the aperture positions equal the table's centre columns in 1.10.0 and 3.1.1). The grid stores them in `.xys`, which nothing downstream in the grid reads. Failing case first: the `cafe-dev` grid run on `d41e6b1` stops at `creta.py:1092` with `KeyError: 'xcenter'`.
  - Tests for G7, G8 and the PSF path (real NGC7469 grid, `grid_dev_compare.py`): 18/18 checks pass.
    - `cafe-dev`, with no test-side stand-ins: the grid extraction runs. Its outputs are bit-identical to the run with the stand-ins (`g4_run_dev.py`), `_cube.fits` too, and the D6 grid checks pass (with `stitch_band = ch1-short` each spaxel is the default × one constant, 0.58–1.74, spread ≤ 9×10⁻¹⁶; ch1-short keeps its own flux).
    - `cafe-legacy`: the outputs are bit-identical to those at `5c7085a` and at `be4201c`, `_cube.fits` too.
    - Smoke test: 0 failed.
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
cd /Users/tanio/pywork/cafe_work/tests/M3 && env PYTHONDONTWRITEBYTECODE=1 MPLBACKEND=Agg PYTHONPATH=/Users/tanio/Sync/pywork/CAFE ~/miniforge3/envs/cafe-dev/bin/python test_normalisation.py /Users/tanio/Sync/pywork/CAFE
cd /Users/tanio/pywork/cafe_work/tests/M3/out/scale/inputs_check && env PYTHONDONTWRITEBYTECODE=1 MPLBACKEND=Agg PYTHONPATH=/Users/tanio/Sync/pywork/CAFE ~/miniforge3/envs/cafe-dev/bin/python ../../../scale_inputs.py /Users/tanio/Sync/pywork/CAFE
cd /Users/tanio/pywork/cafe_work/tests/M3/out/scale/norm_k_1e-4 && env PYTHONDONTWRITEBYTECODE=1 MPLBACKEND=Agg PYTHONPATH=/Users/tanio/Sync/pywork/CAFE ~/miniforge3/envs/cafe-dev/bin/python ../../../scale_dep.py /Users/tanio/Sync/pywork/CAFE 1e-4   # likewise norm_k_1, norm_k_1e4, norm_k_1_repeat (k = 1) and norm_k_1p1e-7 (k = 1.0000001)
cd /Users/tanio/pywork/cafe_work/tests/M3/out/cube_scale/k_1e-4 && env PYTHONDONTWRITEBYTECODE=1 MPLBACKEND=Agg PYTHONPATH=/Users/tanio/Sync/pywork/CAFE ~/miniforge3/envs/cafe-dev/bin/python ../../../cube_scale.py /Users/tanio/Sync/pywork/CAFE 1e-4   # likewise k_1 and k_1e4
cd /Users/tanio/pywork/cafe_work/tests/M3 && env PYTHONDONTWRITEBYTECODE=1 ~/miniforge3/envs/cafe-dev/bin/python scale_compare.py norm_k_1 norm_k_1e-4 norm_k_1e4 norm_k_1_repeat norm_k_1p1e-7
cd /Users/tanio/pywork/cafe_work/tests/M3 && env PYTHONDONTWRITEBYTECODE=1 ~/miniforge3/envs/cafe-dev/bin/python cube_compare.py k_1 k_1e-4 k_1e4
cd /Users/tanio/pywork/cafe_work/tests/M3/out/d4 && env PYTHONDONTWRITEBYTECODE=1 MPLBACKEND=Agg PYTHONPATH=/Users/tanio/Sync/pywork/CAFE ~/miniforge3/envs/cafe-dev/bin/python ../../d4_pah_window.py /Users/tanio/Sync/pywork/CAFE
cd /Users/tanio/pywork/cafe_work/tests/M3/out/d5 && env PYTHONDONTWRITEBYTECODE=1 MPLBACKEND=Agg PYTHONPATH=/Users/tanio/Sync/pywork/CAFE ~/miniforge3/envs/cafe-dev/bin/python ../../d5_phot_grid.py /Users/tanio/Sync/pywork/CAFE
cd /Users/tanio/pywork/cafe_work/tests/M3/out/d6 && env PYTHONDONTWRITEBYTECODE=1 MPLBACKEND=Agg PYTHONPATH=/Users/tanio/Sync/pywork/CAFE ~/miniforge3/envs/cafe-dev/bin/python ../../d6_stitch.py /Users/tanio/Sync/pywork/CAFE
cd /Users/tanio/pywork/cafe_work/tests/M3 && env PYTHONDONTWRITEBYTECODE=1 MPLBACKEND=Agg PYTHONPATH=/Users/tanio/Sync/pywork/CAFE ~/miniforge3/envs/cafe-dev/bin/python test_stitch_band.py /Users/tanio/Sync/pywork/CAFE
cd /Users/tanio/pywork/cafe_work/tests/M3 && env PYTHONDONTWRITEBYTECODE=1 MPLBACKEND=Agg PYTHONPATH=/Users/tanio/Sync/pywork/CAFE ~/miniforge3/envs/cafe-dev/bin/python stitch_run.py /Users/tanio/Sync/pywork/CAFE single single_all.txt after_single_all   # likewise single_gap, single_all_ch1s, single_gap_ch1s, single_all_typo; before_* on 087c0a1
cd /Users/tanio/pywork/cafe_work/tests/M3 && env PYTHONDONTWRITEBYTECODE=1 MPLBACKEND=Agg PYTHONPATH=/Users/tanio/Sync/pywork/CAFE ~/miniforge3/envs/cafe-legacy/bin/python stitch_run.py /Users/tanio/Sync/pywork/CAFE grid grid_all.txt after_grid_all   # likewise grid_all_ch1s; cafe-legacy because of G4
cd /Users/tanio/pywork/cafe_work/tests/M3 && env PYTHONDONTWRITEBYTECODE=1 ~/miniforge3/envs/cafe-dev/bin/python stitch_compare.py
cd /Users/tanio/pywork/cafe_work/tests/M3 && env PYTHONDONTWRITEBYTECODE=1 MPLBACKEND=Agg PYTHONPATH=/Users/tanio/Sync/pywork/CAFE ~/miniforge3/envs/cafe-dev/bin/python stitch_run.py /Users/tanio/Sync/pywork/CAFE grid grid_all.txt g4_before_dev   # G4 failing case, on beb8cf6 (log: logs/g4_before_dev_grid_all.txt)
cd /Users/tanio/pywork/cafe_work/tests/M3 && env PYTHONDONTWRITEBYTECODE=1 MPLBACKEND=Agg PYTHONPATH=/Users/tanio/Sync/pywork/CAFE ~/miniforge3/envs/cafe-dev/bin/python g4_run_dev.py /Users/tanio/Sync/pywork/CAFE grid grid_all.txt g4_after_dev_grid_all   # likewise grid_all_ch1s; test-side stand-ins for G7 and G8
cd /Users/tanio/pywork/cafe_work/tests/M3 && env PYTHONDONTWRITEBYTECODE=1 MPLBACKEND=Agg PYTHONPATH=/Users/tanio/Sync/pywork/CAFE ~/miniforge3/envs/cafe-legacy/bin/python stitch_run.py /Users/tanio/Sync/pywork/CAFE grid grid_all.txt g4_after_legacy_grid_all   # likewise grid_all_ch1s, and single single_all.txt g4_legacy_single_all
cd /Users/tanio/pywork/cafe_work/tests/M3 && env PYTHONDONTWRITEBYTECODE=1 ~/miniforge3/envs/cafe-dev/bin/python g4_compare.py
cd /Users/tanio/pywork/cafe_work/tests/M3 && env PYTHONDONTWRITEBYTECODE=1 MPLBACKEND=Agg PYTHONPATH=/Users/tanio/Sync/pywork/CAFE ~/miniforge3/envs/cafe-dev/bin/python test_psf_grid_photometry.py /Users/tanio/Sync/pywork/CAFE d58797b   # likewise in cafe-legacy
cd /Users/tanio/pywork/cafe_work/tests/M3 && env PYTHONDONTWRITEBYTECODE=1 MPLBACKEND=Agg PYTHONPATH=/Users/tanio/Sync/pywork/CAFE ~/miniforge3/envs/cafe-dev/bin/python stitch_run.py /Users/tanio/Sync/pywork/CAFE grid grid_all.txt g8_after_dev_grid_all   # likewise grid_all_ch1s, and both in cafe-legacy (g8_after_legacy_*); no stand-ins
cd /Users/tanio/pywork/cafe_work/tests/M3 && env PYTHONDONTWRITEBYTECODE=1 ~/miniforge3/envs/cafe-dev/bin/python grid_dev_compare.py
cd /Users/tanio/pywork/cafe_work/tests/M3 && env PYTHONDONTWRITEBYTECODE=1 MPLBACKEND=Agg PYTHONPATH=/Users/tanio/Sync/pywork/CAFE ~/miniforge3/envs/cafe-dev/bin/python g6_run.py /Users/tanio/Sync/pywork/CAFE grid_all.txt g6_after_dev   # G6; aperture correction with inputs/psf_sim/ (g6_before_dev on 25af335)
cd /Users/tanio/pywork/cafe_work/tests/M3 && env PYTHONDONTWRITEBYTECODE=1 MPLBACKEND=Agg PYTHONPATH=/Users/tanio/Sync/pywork/CAFE ~/miniforge3/envs/cafe-dev/bin/python g6_lists.py /Users/tanio/Sync/pywork/CAFE
cd /Users/tanio/pywork/cafe_work/tests/M3 && env PYTHONDONTWRITEBYTECODE=1 MPLBACKEND=Agg PYTHONPATH=/Users/tanio/Sync/pywork/CAFE ~/miniforge3/envs/cafe-dev/bin/python g6_run.py /Users/tanio/Sync/pywork/CAFE grid_all.txt g9_after_dev   # G9; and stitch_run.py grid grid_all.txt g9_after_dev_grid_all
cd /Users/tanio/pywork/cafe_work/tests/M3 && env PYTHONDONTWRITEBYTECODE=1 MPLBACKEND=Agg PYTHONPATH=/Users/tanio/Sync/pywork/CAFE ~/miniforge3/envs/cafe-dev/bin/python stitch_run.py /Users/tanio/Sync/pywork/CAFE single single_all_bkgmeta.txt g12_after_bkgmeta   # G12; likewise single_all.txt g12_after_single_all (g12_before_bkgmeta on eb89a4f)
cd /Users/tanio/pywork/cafe_work/tests/M3 && env PYTHONDONTWRITEBYTECODE=1 ~/miniforge3/envs/cafe-dev/bin/python g12_meta.py g12_after_bkgmeta single_all_bkgmeta.txt after_single_all
cd /Users/tanio/pywork/cafe_work/tests/M3 && env PYTHONDONTWRITEBYTECODE=1 MPLBACKEND=Agg PYTHONPATH=/Users/tanio/Sync/pywork/CAFE ~/miniforge3/envs/cafe-dev/bin/python stitch_run.py /Users/tanio/Sync/pywork/CAFE single single_all_bkgsub.txt rn_after_bkgsub   # rename; rn_before_bkgsub with PYTHONPATH and checkout /Users/tanio/pywork/cafe_work/cmp/rename_before (7396590); likewise rn_after_bkgmeta, rn_after_single_all
cd /Users/tanio/pywork/cafe_work/tests/M3 && env PYTHONDONTWRITEBYTECODE=1 ~/miniforge3/envs/cafe-dev/bin/python g12_meta.py rn_after_bkgsub single_all_bkgsub.txt rn_before_bkgsub
cd /Users/tanio/pywork/cafe_work/tests/M3/out/rename/after_phot5_seed0 && env PYTHONHASHSEED=0 PYTHONDONTWRITEBYTECODE=1 MPLBACKEND=Agg PYTHONPATH=/Users/tanio/Sync/pywork/CAFE ~/miniforge3/envs/cafe-dev/bin/python ../../../realfit_phot5.py /Users/tanio/Sync/pywork/CAFE   # names; before_phot5_seed0 with a git archive export of 45a06f8 as checkout; before_phot5, after_phot5 without the seed
cd /Users/tanio/pywork/cafe_work/tests/M3 && env PYTHONDONTWRITEBYTECODE=1 ~/miniforge3/envs/cafe-dev/bin/python rename_compare.py before_phot5_seed0 after_phot5_seed0   # likewise final_phot5_seed0 (2ae9cb4)
cd /Users/tanio/pywork/cafe_work/tests/M3 && env PYTHONDONTWRITEBYTECODE=1 MPLBACKEND=Agg PYTHONPATH=/Users/tanio/Sync/pywork/CAFE ~/miniforge3/envs/cafe-dev/bin/python static_names.py /Users/tanio/Sync/pywork/CAFE
cd /Users/tanio/pywork/cafe_work/tests/M3 && env PYTHONDONTWRITEBYTECODE=1 MPLBACKEND=Agg PYTHONPATH=/Users/tanio/Sync/pywork/CAFE ~/miniforge3/envs/cafe-dev/bin/python stitch_run.py /Users/tanio/Sync/pywork/CAFE single single_all.txt rnm_after_single_all   # names; likewise single_all_ch1s, single_gap, grid_all, grid_all_ch1s; rnm_before_* on 45a06f8
cd /Users/tanio/pywork/cafe_work/tests/M3 && env PYTHONDONTWRITEBYTECODE=1 MPLBACKEND=Agg PYTHONPATH=/Users/tanio/Sync/pywork/CAFE ~/miniforge3/envs/cafe-dev/bin/python test_parameter_file.py /Users/tanio/Sync/pywork/CAFE 744dc2a   # G5; and stitch_run.py single single_all.txt g5_after_single_all, grid grid_all.txt g5_after_grid_all
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

**M4 stage 1** (work folder `tests/M4/`; setups in `m4_setups.py`; each fit single-threaded, `PYTHONHASHSEED=0`, `cafe-dev`, `dev` on `PYTHONPATH`; outputs in `out/<setup>/j<j>/`, logs in `logs/`)
```
cd /Users/tanio/pywork/cafe_work/tests/M4 && ./run_one.sh R1 0   # one fit: <setup> <j> [<run folder>]
cd /Users/tanio/pywork/cafe_work/tests/M4 && env PYTHONDONTWRITEBYTECODE=1 ~/miniforge3/envs/cafe-dev/bin/python s1_make.py   # S1, after R1 j0
cd /Users/tanio/pywork/cafe_work/tests/M4 && xargs -P 2 -L 1 ./run_one.sh < queue_stage1.txt   # the other 30 fits, with the repeat "R1 0 j0_repeat"
cd /Users/tanio/pywork/cafe_work/scratch/m4_plan && env PYTHONHASHSEED=0 PYTHONDONTWRITEBYTECODE=1 MPLBACKEND=Agg PYTHONPATH=/Users/tanio/Sync/pywork/CAFE ~/miniforge3/envs/cafe-dev/bin/python ../../tests/M4/s1_line_check.py /Users/tanio/Sync/pywork/CAFE
cd /Users/tanio/pywork/cafe_work/tests/M4 && ./m4_report.sh   # summary tables, figures and the report (with findings_stage1.md)
cd /Users/tanio/pywork/cafe_work/tests/M4 && env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/Users/tanio/Sync/pywork/CAFE ~/miniforge3/envs/cafe-dev/bin/python test_zero_flux_freeze.py /Users/tanio/Sync/pywork/CAFE   # step 1 synthetic test (logs/freeze_rules_{before,after}_raw.txt)
cd /Users/tanio/pywork/cafe_work/tests/M4 && xargs -P 4 -L 1 ./run_one.sh < queue_freeze_R2.txt   # step 1: R2 with the freeze (out/R2/freeze_j<j>)
cd /Users/tanio/pywork/cafe_work/tests/M4 && env PYTHONDONTWRITEBYTECODE=1 ~/miniforge3/envs/cafe-dev/bin/python freeze_compare.py   # R2 before / after the freeze
cd /Users/tanio/pywork/cafe_work/tests/M4 && env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/Users/tanio/Sync/pywork/CAFE ~/miniforge3/envs/cafe-dev/bin/python step2_flx_bounds.py /Users/tanio/Sync/pywork/CAFE > logs/step2_flx_bounds.txt   # step 2: _FLX bounds, reference wavelengths
cd /Users/tanio/pywork/cafe_work/scratch/m4_stage2 && env PYTHONHASHSEED=0 PYTHONDONTWRITEBYTECODE=1 MPLBACKEND=Agg PYTHONPATH=/Users/tanio/Sync/pywork/CAFE ~/miniforge3/envs/cafe-dev/bin/python ../../tests/M4/s1b_make.py /Users/tanio/Sync/pywork/CAFE S1b ../../tests/M4/out/R1/j0   # stage 2: S1b and its truth
cd /Users/tanio/pywork/cafe_work/tests/M4 && xargs -P 3 -L 1 ./run_stage2.sh < queue_stage2_R.txt   # stage 2: R1 restart/tight, R2 nochk_restart/nochk_tight (also queue_stage2_S1b.txt, queue_stage2_R2_xjac.txt, queue_stage2_R1_xjac.txt)
cd /Users/tanio/pywork/cafe_work/scratch/m4_stage2 && env PYTHONDONTWRITEBYTECODE=1 MPLBACKEND=Agg PYTHONPATH=/Users/tanio/Sync/pywork/CAFE ~/miniforge3/envs/cafe-dev/bin/python ../../tests/M4/emissivity_jumps.py /Users/tanio/Sync/pywork/CAFE ../../tests/M4/logs/emissivity_values_after_G14.npz ../../tests/M4/logs/emissivity_values_before_G14.npz   # G14's jumps; j at the grid temperatures against the pre-fix values
cd /Users/tanio/pywork/cafe_work/tests/M4 && env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/Users/tanio/Sync/pywork/CAFE ~/miniforge3/envs/cafe-dev/bin/python test_G14_emissivity.py /Users/tanio/Sync/pywork/CAFE   # G14 synthetic test
cd /Users/tanio/pywork/cafe_work/tests/M4 && ~/miniforge3/envs/cafe-dev/bin/python stage2_summary.py > logs/stage2_summary.txt && ./m4_report_stage2.sh   # stage 2 summary and report
cd /Users/tanio/pywork/cafe_work/tests/M4 && ./stage3_launch.sh > logs/stage3_launch.txt 2>&1   # stage 3: R1 plain j0, then S1c (s1b_make.py <checkout> S1c ../../tests/M4/out/R1/s3_plain_j0, log logs/s1c_make.txt), then all 90 fits, 4 at a time (queue_worker.sh, run_stage3.sh <setup> <j> <variant>)
cd /Users/tanio/pywork/cafe_work/tests/M4 && env PYTHONDONTWRITEBYTECODE=1 ~/miniforge3/envs/cafe-dev/bin/python stage3_summary.py > logs/stage3_summary.txt && ./m4_report_stage3.sh   # stage 3 summary and report
```

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
- 2026-11-15: **D3 decided (group 3).** Physics/numerics decisions:
  - D3e (c): automatic per-spectrum normalisation by the spectrum's own median |flux| (each spaxel's own in cubes) before the fit, scaled back after. It replaces my `norm_factor`, which is not ported. `read_spec(flux_scale=…)` stays as it is.
  - D3a (c): no change in `check_fit_pars`; its absolute 10⁻⁵ peak tolerance then acts relative to the spectrum's median |flux|.
  - D3b–d, as proposed: the spectrum's and the photometry's flux and errors are divided; only the line/PAH `_Peak` (`g_*`, `d*_*`) value, stderr, min and max are scaled (not `o_*_Peak`, not `_FLX`); the parcube is fully in physical units; `cont_profs['flux0']` is scaled back for the products.
  - Two commits, in the simplest form (CLAUDE.md §8): `fit_spec`, then `fit_cube`. Each is shown hunk by hunk with its reason paragraph and approved before the next.
  - Push `dev` to my fork now, showing first what it publishes (done: `f45a02b`→`1523059`, the range shown to me the turn before).
- 2026-11-15: **The normalisation commit approved, with a wording change** (now `476c6ef`; the amended hunk is shown to me before the push).
  - **Standing convention: CAFE's units are fixed**, fluxes in Jy and wavelengths in µm. Never describe anything as depending on "flux units". When a result changes with the flux scale, describe it as depending on the source's flux level (brightness). Recorded in CLAUDE.md §4, here and in `DESIGN.md` (this entry ahead of the end-of-M3 update). The existing mentions in the commit's comment and in this brief are corrected.
  - The non-unique convergence is logged as an important finding for M4 (see M4). Fit settings stay my decision.
  - Then push `dev` to my fork, showing first what it publishes, and go on to group 4: show me D4 and D5 with the options, the current behaviour and your recommendation, and stop.
- 2026-11-15: **`dev` pushed** (`1523059`→`7880a8d`, the 5 commits shown to me). **D4 and D5 decided (group 4):**
  - D4 (a): the reference-PAH continuum window stays at ±10,000 km/s, as in GOALS. My local ±γ_PAH is not brought in.
  - D5 (a): the photometry-only model grid stays at 250 points per decade, as in GOALS. My local R × λ_min is not brought in.
  - Then group 5: show me D6 with the options, the current behaviour and your recommendation, and stop.
- 2026-11-15: **D6 changed: one general option for the reference band, instead of porting `stitch_to_shortest`.**
  - The user chooses the band the spectrum is stitched to. The current default (the last band) and `stitch_to_shortest` (the first band) become special cases, so only one option exists.
  - Compute the cumulative factors as before, chaining through gaps with the unknown ratio set to 1.0 (D6 a), then divide by the reference band's factor, so every band lands on the reference band's level.
  - Default: the last band, as now. This changes the default only for spectra with gaps.
  - The grid extraction gets the option too if it uses the same stitching code.
  - First show me how the user specifies the band (names, where it is set), then the diff hunk by hunk with its reason paragraph and the test, and wait for my approval.
- 2026-11-15: **Commit `be4201c` (the reference band for stitching) approved.** Push `dev`, showing me first what it publishes. Then fix G4 on `dev`: pass `w.celestial` in `doGridPhotometry`, as the single extraction does; show the failing case first, then the diff hunk by hunk with its reason paragraph, and rerun the real NGC7469 grid test in `cafe-dev`. G5 and G6 stay logged for later.
- 2026-11-15: **`dev` pushed** (`7880a8d`→`beb8cf6`, the 5 approved commits). **Commit `5c7085a` (G4) approved.** The photutils-version finding is logged as it is (see "Biases"). After confirming that the M3 list is done apart from the `DESIGN.md` update, fix the new grid problems: G7, G8, and `w.celestial` in `doPSFGridPhotometry` (its path stays untested until G6); leave `sliceGridExtractionPhotometry` for the dead-code clean-up. Show the failing cases, then the diff hunk by hunk with reason paragraphs, and rerun the real NGC7469 grid extraction in `cafe-dev` without the test-side stand-ins. Update `DESIGN.md` last, then stop.
- 2026-11-15: **Before marking M3 complete, fix G5 and G6.** G6: confirm it with a real NGC7469 grid extraction with aperture correction, then fix it; show the failing case, the diff hunk by hunk with reason paragraphs, and the rerun. G5: tell me whether the `parameter_file=False` path is used anywhere (CRETA, my notebooks and scripts in the pre-sync folder), then propose the simplest fix, or removing that path if nothing uses it, and wait for my decision.
- 2026-11-15: **Approved: `56b4c75`, `d41e6b1`, `1e66caf` (the grid fixes) and `82539c1` (G6).** **G9: use `r_ap` for the PSF photometry**, the same aperture as the data, which is what an aperture correction requires; show me the diff hunk by hunk with its reason paragraph. The path stays untested end to end until CRETA's PSF cubes are found. **G10 stays logged.** **G5: option (a)**; show me its diff too. In `DESIGN.md`, change the cube flow's "the M2 target" to "the M4 target", and add the G6, G9 and G5 commits to the M3 list. Then wait for my approval before pushing.
- 2026-11-15: **`dev` pushed** (`beb8cf6`→`1926c7b`, the 12 commits shown to me). **G9 is recorded as a typo fix** (`r` was meant to be `r_ap`), not a physics decision. **Fix G12 now**: the metadata must record `bkg_r_in` and `bkg_an_w` from the parameter file; show the failing case, the diff hunk by hunk with its reason paragraph, and the rerun. **G10, G11 and G11's two related problems are one item, "CRETA aperture-correction path"**, to be fixed and tested end to end together once CRETA's PSF cubes are found; not with stand-in PSFs. After I approve G12, mark M3 complete in the brief and stop.
- 2026-11-15: **Naming rule (standing; CLAUDE.md §9):** variable names must identify what they hold; no generic names such as `r_in`, `width`, `s`, `dl`, `norm` or `factor`. It applies to all code written or changed from now on, and to the code added in M3. Apply it now: rename `r_in` and `width` in `singleExtraction` (e.g. `bkg_ann_r_in`, `bkg_ann_width`), and list the generic names introduced in M3's commits with proposed names. Generic names elsewhere in CAFE and CRETA go on the clean-up list, not changed now. Show me the renames hunk by hunk with their reason paragraphs, and wait for my approval before marking M3 complete or pushing.
- 2026-11-15: **Commit `2297264` approved.** Apply the proposed M3 names, with two changes: `norm` → `spec_norm_factor` (it is the factor the spectrum is normalised by), and `spec_fit` → `spec_with_unc_floor` (it holds the whole spectrum, not only its uncertainties). Include `ratio`, `xx` and `yy` as proposed; the other older names go on the clean-up list. One commit per file area, each shown hunk by hunk with tests (outputs bit-identical). Remove the scratch worktree `cmp/rename_before`. Then wait for my approval.
- 2026-11-15: **Approved: `1fc4f5a` (G12) and `5b0b051`.** **Addition to the naming rule (CLAUDE.md §9):** the more fundamental a variable is, the less explicit its name needs to be. Core names such as `wave`, `flux`, `z` or `params` stay as they are, and natural derived names stay too, e.g. `par` for one item of `params`. Explicit names are for secondary variables: helpers, indices and intermediate results. The same quantity keeps the same name across functions. Don't propose renaming core or natural names. Apply it now, amending `dd2c22e` and `b4d547a`: `par` stays `par` (not `fit_param`, not `par_name`); `scale_peaks` takes `spec_norm_factor` under that name and divides by it, the normalisation calls `scale_peaks(params, spec_norm_factor)` and the scaling back `scale_peaks(result.params, 1 / spec_norm_factor)`; in the photometry weights, keep `wave` and `R_0` as they were, with the original comment. Show me the amended hunks, then wait for my approval.
- 2026-11-15: **`scale_peaks` multiplies**, and its argument is called `scaling_factor`: `scale_peaks(params, scaling_factor)` multiplies the line and PAH peaks (value, bounds, stderr) by `scaling_factor`; the calls are `scale_peaks(params, 1 / spec_norm_factor)` going in and `scale_peaks(result.params, spec_norm_factor)` coming back. Keep `par`. Amend `a763bd4` accordingly. **`b113094` approved.** Then check the renamed code statically for undefined names, leftover old names, and accidental reassignment or shadowing; fit results don't need to be bit-identical. **M4 order:** first check that fitting a JWST spectrum alone works well, including the non-unique convergence; then fits with real photometry; then cube-fit performance. **Standing rules for tests (CLAUDE.md §10):** every test report starts with its setup (spectrum file and z, inpars and opt files, the photometry with values and origin, the number of free parameters); the fake-photometry setup is only for functional checks that compare code versions on identical input, never for judging parameter values or fit stability.
- 2026-11-15: **Commit `2ae9cb4` approved. M3 complete.** Push `dev` to my fork, showing me first what it publishes.
- 2026-11-15: **`dev` pushed** (`1926c7b`→`6b9136c`, the 10 commits shown to me). Attribution: commit attribution was turned on (PR attribution off) when I approved M3; CLAUDE.md §2 describes that state, and nothing for GOALS carries a Claude line.
- 2026-11-15: **Milestone split; don't start M4 yet.** M4: fitting a JWST spectrum alone, including the non-unique convergence. M5: fits with real photometry. M6: cube-fit performance and parallelisation, including the fitting order (#6). M7: clean-up and packaging. The CRETA aperture-correction path stays a separate item until the PSF cubes are found. Each milestone starts only after my approval. Earlier entries that give cube-fit performance as M4 mean M6.
- 2026-11-15: **`dev` pushed** (`6b9136c`→`fa348d8`, the 3 commits shown to me: the attribution text in CLAUDE.md §2, the record of the previous push, the milestone split).
- 2026-11-16: **M4 approved**, with the plan's recommended choices: NGC3256 nuc1 from my existing extraction as the second real spectrum; rounding-level perturbations only; S1 noise at the floored errors; Δχ² < 1 in the floored χ² as "the same fit"; NIRSpec + MIRI decided after stage 1. Except: 10 fits per setup, not 20. The report starts with one short summary table per setup; the full details go in a report file in the work folder.
- 2026-11-17: **Brief update with the M4 stage 1 results committed** (`5777ff7`).
- 2026-11-17: **Zero-flux freeze.** When a continuum component's `_FLX` reaches 0, its other parameters are fixed (TMP, TAU, MIX, COV, and the starburst's age parameters), as `check_fit_pars` already does for line and PAH peaks.
- 2026-11-17: **The `flux0` mismatch is to be fixed** (see "Biases", 2026-11-16), including the 0–2 `_FLX` limit when a component's reference wavelength is outside the data. The design is still open.
- 2026-11-17: **Commit `d6bd782` approved.**
- 2026-11-17: **One principle for the freeze: fix a parameter only when it no longer affects the model.** So (a) when a component's TAU reaches 0, its MIX and COV are fixed too; (b) the freeze leaves free any parameter that another component's expression uses (e.g. `WRM_TAU` through `PAH_TAU`).
- 2026-11-17: **Commit `672749d` approved.** Go on to M4 step 2.
- 2026-11-17: **M4 order: stage 2 first; the `flux0` fix stays in M4, after stage 2.** Stage 2 as planned (diagnostic runs; no default changes): R1 with a tighter FTOL and restarts from each end point (`x_scale='jac'` only if that is inconclusive); R2 the same with `FIT_CHK` off; S1 rebuilt so that its truth uses only the lines the fit keeps. Also report, from the stage 1 and stage 2 fits, whether `HOT_FLX` and `STB_FLX` are anticorrelated across fits at equal χ², and S1's fitted values against its truth.
- 2026-11-18: **Order of the dust temperatures:** set by sensible, non-overlapping T ranges in the inpars files, with no code change. A ratio constraint like Onion's is logged for future development (see "Later"). The T ranges for each shipped inpars file are proposed to me, starting from my pre-sync values where they exist; no inpars file changes until I choose them.
- 2026-11-18: **M4 next: the G14 fix.** Choose the two grid temperatures that bracket T; keep the log–log interpolation, the values at the grid points and the behaviour outside the grid unchanged. Failing case (`emissivity_jumps.py`), then the diff hunk by hunk with its reason paragraph, then the test. No PR to GOALS.
- 2026-11-18: **Commit `93a90dc` (G14 fix) approved.**
- 2026-11-18: **Dust T ranges applied to the shipped inpars files, except `inpars_jwst_miri_IIZw096.ini`** (unchanged for now): COO 3–50 K, WRM 50–200 K, HOT 200–1027.2 K. COO's start becomes 40 K where 75 K lies outside its range. Diff shown to me file by file. Then a rerun plan: R1, R2 and S1b regenerated with the fixed model and the new ranges.
- 2026-11-18: **Commit `4ab23ea` (dust T ranges) approved.**
- 2026-11-18: **M4 stage 3 reruns as proposed, before the `flux0` fix.** R1, R2 and S1c; sets plain, restart and `x_scale='jac'` + restart; 10 fits each. Restart rule: stop when 5 successive restarts together lower χ² by less than 1. S1c: the lines that `init_feats` drops on S1c's own data are set to 0 in its truth, with a check that the fit's line set keeps every true line. Then report and stop.
- 2026-11-06: **Exception to the testing rule, for the six M2 fixes only.** They are evident fixes: check them by reading and the import smoke test only, with no data tests.
  - Before this, a few data tests had started. They stay in the work folder:
    - `tests/m2/test_numpy_attrs.py`, a static scan for NumPy attributes that the installed NumPy lacks: 4 hits before #1 (the `np.NaN` lines), 0 after;
    - `tests/m2/run_creta_grid.py`, run once on the unfixed branch, where it failed at `creta.py:867` as expected;
    - logs in `tests/m2/logs`, and the empty output folder `tests/m2/out/t1_grid_before`.

### Awaiting my OK
- M3 decisions, from `reports/M3_plan_2026-11-14.md` (2026-11-14). For each, when we reach its group: show me the options, the current GOALS behaviour and your recommendation.
  - D3a–e: flux normalisation and #11: a relative lower-bound test in `check_fit_pars`; what `scale_flux_params` scales (line and PAH `_Peak` value, stderr and bounds; not `o_*_Peak` or `_FLX`); a parcube fully in physical units; products from continuum profiles rebuilt from the unscaled spectrum; whether `norm_factor` is still needed after #11.
    - 2026-11-15, shown to me with options and a recommendation. *(Decided 2026-11-15: D3e (c), D3a (c), D3b–d as proposed; see "Decisions".)* Measured on `dev` (`1f16eb7`, work folder, no code change): the tutorial fit (fixture setup, now with the 1% floor) on the same spectrum read with `read_spec(flux_scale=k)`. The χ² surface is the same for every k.
    - k = 10⁻⁴ (peaks ~10⁻⁶–10⁻⁵ Jy, as in a faint spaxel): spectral χ²/N 77,611; 57 of 84 line/PAH peaks at 0 (56 fixed at the lower bound by #11); 54 parameters free at the end. The optimiser itself drove bright features to ~0 before #11 fixed them ([O IV] 25.9 µm: 0.20 Jy at k = 1, 6×10⁻⁷ Jy here, divided by k). So fixing #11 alone would not rescue this fit.
    - k = 1: χ²/N 21,659; 8 peaks at 0 (7 fixed by #11); 102 free. k = 10⁴: χ²/N 23,950; 8 peaks at 0 (3 fixed by #11); 101 free. Yet against k = 1, STB_FLX is 0.53×, VGRAD 5.9 instead of 15.4 km/s, HOT_FLX 1.13×, and the peaks differ by 11% (median of 74). The optimiser does not give the same fit at every flux level: SciPy `least_squares` (TRF) with `x_scale = 1`, and a finite-difference step that is absolute (1.5×10⁻⁸) for parameters below 1. *(Corrected 2026-11-15: a fit whose inputs differ from k = 1 only by rounding (k = 1.0000001, normalised) differs by as much (STB_FLX 3.7×), so this k = 10⁴ difference is not evidence of a dependence on the source's flux level. The k = 10⁻⁴ failure is: 57 peaks at 0 and χ²/N 3.6× higher, gone with the normalisation.)*
    - The plan's D3a (a relative lower-bound test) is withdrawn: the peaks' lower bounds are 0, a relative tolerance around 0 is 0, and `least_squares` never lands exactly on a bound, so the test would never fire.
    - Recommended: automatic normalisation of each spectrum (each spaxel) by its own median |flux| before the fit, scaled back after; no new argument. The #11 tolerance then acts relative to the spectrum's median |flux|, with no change in `check_fit_pars`. Scope: spectrum and photometry divided; only the line/PAH `_Peak` value, stderr, min and max scaled; parcube fully physical; `cont_profs['flux0']` scaled back for the products.
  - D4: the reference-PAH continuum window (±γ_PAH or ±10,000 km/s).
    - 2026-11-15, shown to me with options and a recommendation. *(Decided 2026-11-15: (a), dev kept; see "Decisions".)* `init_feats` takes the first PAH of the order 6.22, 11.33, 7.6, 3.3, 17.0 µm inside the spectrum as the reference (6.2123 µm for any spectrum that covers 6.2 µm), guesses its peak as F(λ₀) minus the mean of F at λ₀(1 ± d), and scales every PAH's template peak to it. Only the starting values change: the bounds stay [0, ∞) in all 7 shipped inpars (`EPSPeak_PAH = −1`). dev: d = 10,000 km/s / c = 0.0334. Local: d = γ of the reference PAH. Measured with `d4_pah_window.py` (work folder, no fit); guess / truth:
    - One Drude PAH on a linear continuum: dev 0.95, 0.93, 0.70, 0.97, 0.51 (6.2, 11.3, 7.6, 3.3, 17.0 µm); local 0.80 for all (a Drude is at 20% of its peak at ±1 FWHM).
    - The whole PAH template on a linear continuum, through `init_feats` with the fixture's line tables: dev 1.39, 0.98, 0.55, 0.17, 0.90; local 0.95, 0.83, 0.75, 0.79, 0.80. At 6.2 µm, dev's window lands on the broad 6.27 µm component; at 17.0 µm, on the 16.45 µm band.
    - NGC7469 tutorial spectrum, against its fit (`476c6ef`, fitted peak 0.145 Jy; 0.143 Jy in the rounding-perturbed fit): dev 1.04 × fitted, local 0.81 ×; over the 23 PAHs fitted above 0, median guess / fitted 0.94 (dev) and 0.73 (local).
    - Options: (a) keep dev; (b) the local ±γ; (c) ±γ divided by 0.8, which removes the 20% for an isolated Drude: 1.19, 1.04, 0.93, 0.99, 1.00 on the template, 1.01 × fitted on NGC7469. (b) and (c) also need the comment ("10000 km/s") changed.
    - Recommended: (a). In the usual case (6.2 µm reference) dev's guess on real data is as good as (c) and better than (b). The poor dev cases (7.6 and 17.0 µm references) arise only for spectra that miss 6.2 and 11.3 µm. A different start ends at a different point (non-unique convergence, see "Biases"), so any change shifts every fit without a gain I can show.
  - D5: the photometry-only model grid density.
    - 2026-11-15, shown to me with options and a recommendation. *(Decided 2026-11-15: (a), dev kept; see "Decisions".)* With `resolutions = 'PHOTOMETRY', R` the model is computed on a grid from the bluest to the reddest band and interpolated at the band centres (no filter integration). dev: 250 points per decade (spacing 0.92%; "R~100" in the comment). Local: R × λ_min[µm] per decade; it also fails (IndexError) when no R is given, which `read_inst` allows (default 50). No shipped inpars uses this mode. My HERUS fits (2024) used 250 per decade.
    - Measured with `d5_phot_grid.py` (work folder, no fit): the same parameters on each grid (30 PAHs, strong; `init_feats` keeps no lines from the photometry), against a 5,000-per-decade grid. Bands J–SPIRE 500 (1.25–500 µm) and SDSS u + the same (0.355–500 µm).
    - dev: within 0.30% at every band, at R = 50 and 100, for both band sets.
    - Local: 62 and 17.5 points per decade at R = 50 for the two band sets (3.7% and 13% spacing): up to 3.0% (2 of 16 bands > 1%) and 25% (19 of 21 bands > 1%). At R = 100: 0.66% and 1.9% (4 of 21 > 1%).
    - Options: (a) keep 250 per decade; (b) the local formula; (c) 2 points per resolution element at R, 2 ln(10) R per decade (231 at R = 50): within 0.62% at R = 50 and 0.13% at R = 100.
    - Recommended: (a). It is within 0.3% everywhere tested, well below photometric errors. (b) ties the density to the bluest band's wavelength, with no physical reason, and fails without R. (c) ties it to R, which here sets only the widths of lines, and the model had none; R above 100 is not tested.
  - D6: `stitch_to_shortest` at no-overlap gaps.
    - 2026-11-15, shown to me with options and a recommendation. *(Changed 2026-11-15: one general option for the reference band, with D6 (a) at gaps; see "Decisions".)* CRETA's single extraction scales each band by the median ratio in its overlap with the next band. A ratio of exactly 1.0 (no overlap, or a NaN median in the overlap) ends a chain. Default (dev = GOALS): each band is chained forward to the first 1.0, so each group of overlapping bands ends at its own last band's level. My local `stitch_to_shortest` (single extraction only, not the grid) chains from the first band through every band, multiplying through the 1.0s.
    - Measured with `d6_stitch.py` (work folder; dev's code and the local `cube_preproc.py` from `135aa70`, run as they are): synthetic bands of a known spectrum, with known band factors 1.00, 1.05, 0.97, 1.10; stitched / truth per band.
    - Contiguous overlaps: default 1.10 for all (the last band), `stitch_to_shortest` 1.00 for all (the first band). Both right, each to its own reference.
    - One gap after two bands: default 1.05, 1.05 | 1.10, 1.10; `stitch_to_shortest` 1.00, 1.00 | 0.924, 0.924. The second group gets the first group's chain factor (1.00/1.05) on top of its own first band's 0.97. Stopping at gaps would give 1.00, 1.00 | 0.97, 0.97.
    - When gaps arise: G395H (to ~5.27 µm) and MIRI ch1S (from ~4.9 µm) overlap, so a full NIRSpec + MIRI set has none (the M1 report's "NIRSpec→MIRI" example holds only when a band is missing). Gaps come from a missing band, or from an overlap with no valid data in one band.
    - Options: (a) port as it is; (b) port, stopping at gaps: each group starts from its own first band, the mirror of the default; (c) don't bring the option in.
    - Recommended: (b). No information crosses a gap, so no factor should. (b) is one line in `stitchSpectrum` (the last 1.0 at or before the band, as the default looks for the first at or after it). The console print of the growing ratio list is left out; the cumulative factors can be printed by calling `stitchSpectrum` itself.

- Which real cube is the M6 benchmark (cube-fit performance; M4 before the split of 2026-11-15).
- 2026-11-17: **Candidate for the `flux0` fix:** the median over N channels around λ₀ (one-sided at the data edges). N is my decision.
- 2026-11-17: **G14: fix the emissivity interpolation to the bracketing pair of grid temperatures?** (from M4 stage 2) A model change; it would shift every fit with a dust temperature between grid points. Stage 2's sets would be rerun after it. *(Decided 2026-11-18: fix it next; see "Decisions".)*
- 2026-11-17: **Constrain the order of the cool and warm dust temperatures** (e.g. WRM_TMP > COO_TMP)? (from M4 stage 2) Without it, R2 ends in either of two minima with the temperatures swapped. A physics choice. *(Decided 2026-11-18: non-overlapping T ranges in the inpars files, no code change; see "Decisions".)*
- 2026-11-17: **Fit settings after G14** (CLAUDE.md §4): `x_scale='jac'`, FTOL, restarts or another convergence test. In stage 2, `x_scale='jac'` found R2's better minimum in all 10 fits; in R1 its lower χ² came only with temperatures on G14's jumps. Stage 3 (2026-11-18, G14 fixed, new ranges): no setting is best on all three. `x_scale='jac'` + restart reaches R1's lowest end state in 9 of 10 fits but ends worse than plain on R2 in 8 of 10; restart alone takes R1 to its higher end state (A) and S1c to the noise level; the shipped plain fit stops 1,246–2,549 above R1's best and 4–63 above S1c's.
- 2026-11-18: **Dust T ranges for the shipped inpars files** (non-overlapping, my decision of 2026-11-18). Proposed, from my pre-sync `inpars_jwst_miri_SB.ini` (the only pre-sync JWST file with ranges; also used for my IIZw096, NGC3256 nuc1 and VV114 fits): COO 0–50 K, WRM 50–200 K, HOT 200–1027.2 K in all 7 files (now 0–∞, 0–∞, 100–1027.2). The two AGN files start COO at 75 K, outside that range: proposed start 40 K, as in the other files (R1's fits end at 23–29 K). CIR and CLD unchanged (fixed, flux 0). M4's fits lie inside these ranges (R1: COO 23–29, WRM 76–78, HOT 530–650 K; R2: 30.5, 59.4, 649 K), and R2's swapped state (COO 59.4 K) is excluded. My pre-sync IIZw096 fit with them ended at both lower bounds (WRM 50.0, HOT 200.0 K). Alternative from my pre-sync files: CLD 5–25, COO 25–100, WRM 100–300, HOT 300–1027.2 K (CYGNUS, MIRI + photometry), which would exclude R1's and R2's WRM (59–78 K). *(Decided 2026-11-18: COO 3–50, WRM 50–200, HOT 200–1027.2 K, all files but IIZw096; see "Decisions".)*
- 2026-11-18: **Rerun plan, M4 stage 3** (proposed). `dev` with G14 fixed and the new T ranges; shipped `default_opt.cafe`; no photometry; 10 fits per set with the stage 1 rounding-level inputs; new run names, stage 1 and 2 outputs kept. Setups: R1 and R2 as before (their inpars now with the new ranges), and S1c, built as S1b was but from the new R1 plain fit (j = 0), so S1b's files stay. Sets per setup: plain (shipped settings), restart, and `x_scale='jac'` + restart. To decide: the restart stop rule (recommended: stop when 5 successive restarts together lower χ² by < 1, as stage 2's single-restart rule stopped R1's chains while they still fell ~2 per restart). Measured as in stage 2, plus: end temperatures at a range edge, and none on a former G14 jump. *(Decided 2026-11-18: as proposed, with the 5-restart rule, before the `flux0` fix; see "Decisions".)*
- 2026-11-18: **R1's lowest χ² puts HOT at its 200 K lower bound** (from M4 stage 3). End state B (HOT_TMP 200 K fixed "at lower bound", HOT_FLX 0.11, STB_FLX 0.58, COO 16 K, WRM 71 K) lies 773 below A (HOT 665 K, STB_FLX ≈ 0.001, COO 23.7 K, WRM 77.1 K). B's net gain comes from channel 4C (24.4–28.8 µm observed: −5,215, against +4,400 elsewhere), which holds 39% of R1's χ² at B. So the fit wants a third dust component cooler than 200 K, and the short-wavelength continuum then goes to the stars instead of the hot dust. A physics choice for me: accept B as R1's fit, change HOT's range for this source, or look at channel 4C first.
- 2026-11-18: **S1c: separate a bias from the noise?** (from M4 stage 3) On its one noise realisation, the converged S1c fits agree with each other but sit 2–3 stderr from the truth in COO_TMP (+4%), COO_TAU (+10–16%) and WRM (−1 to −7%); S1b showed the same pattern. Telling a bias from noise needs several noise realisations of the same truth (e.g. 10 seeds, restart set). Not run.
- 2026-11-17: **A component's TAU at 0: fix its MIX and COV too?** (from M4 step 1) The model skips a component's extinction when its TAU is 0 (`if p["STB_TAU"] > 0: … else: ext = 1`), so MIX and COV then have no effect, as the other parameters do when `_FLX` is 0. `check_fit_pars` fixes the TAU at 0 but leaves MIX and COV free: a free parameter with no effect, so no error bars and a refit. Free in the shipped inpars: `STB_COV` (SB, nirspec-miri SB, IIZw096). Recommended: yes, the same rule as for `_FLX`. *(Decided 2026-11-17: yes, under one principle; see "Decisions".)*
- 2026-11-17: **Keep a parameter free when another component's expression uses it?** (from M4 step 1) All 7 shipped inpars tie `PAH_TAU` to `WRM_TAU`. When `WRM_FLX` reaches 0, `check_fit_pars` fixes `WRM_TAU` (before and after `d6bd782`), although it still sets the PAH extinction. Recommended: the zero-flux (and zero-TAU) freeze leaves free any parameter that a parameter of another component uses in its expression. *(Decided 2026-11-17: yes, under one principle; see "Decisions".)*
- 2026-11-15: **Generic names introduced in M3's commits, with proposed names** (naming rule, CLAUDE.md §9).
  - `cafe.py`, `scale_peaks`: `factor` → `peak_multiplier`; `par` → `fit_param`.
  - `cafe.py`, `cafe_grinder`, normalisation: `norm` → `spec_median_abs_flux`; the dict comprehensions' `k, v` (over `cont_profs['flux0']`) → `comp_name, comp_flux0`.
  - `cafe.py`, `cafe_grinder`, error floor: `floor` → `spec_unc_floor` (the option's name); `spec_fit` → `spec_floored_unc`.
  - `cafe.py`, `cafe_grinder`, photometric weights: `R_0` → `spec_resolving_power`; `wave` → `spec_phot_wave`; `s` → `spec_phot_sort_idx`; `dl` → `spec_phot_delta_wave`.
  - `cafe_io.py`, `.asdf` output: `p` in `{p: fitPars[p].stderr for p in fitPars}` → `par_name`.
  - `creta.py`: `ref_band` (it holds an index) → `stitch_ref_idx`. `cube_preproc.py`, `stitchSpectrum`: the argument `ref` → `stitch_ref_idx`.
  - Kept, as they identify what they hold: `flux_scale`, `ignore_DQ`, `flux_lam`, `fFTS_0` (the module's naming), `bkg_ann_r_in`, `bkg_ann_width`.
  - Older generic names on lines M3 rewrote (not introduced by M3): `ratio` in `stitchSpectrum` → `band_to_ref_multiplier`; `xx, yy` in the grid (G8) → `x_center_pix, y_center_pix`; `tab` in `read_phot` (5 lines) → `phot_table`; `flux` in `cafeplot`; `cmap` in the grid; `aper` in `doPSFGridPhotometry`; `idx`, `ratio_list`, `spectrum` (`stitchSpectrum`'s other arguments). Proposed: rename `ratio` and `xx, yy` with the M3 names (their lines were written in M3), and put the rest on the clean-up list.
  - Not listed: loop indices (`i`, `j`) of loops M3 did not write.
  - *(Decided 2026-11-15: as proposed, except `norm` → `spec_norm_factor` and `spec_fit` → `spec_with_unc_floor`; `ratio`, `xx` and `yy` renamed too; the other older names go on the clean-up list. Amended the same day under the rule's addition: `par`, `wave` and `R_0` stay; `scale_peaks` takes `spec_norm_factor` and divides by it. See "Decisions".)*
- 2026-11-15: **G5 (`parameter_file=False`): fix or remove** (my request: tell me whether the path is used, then propose the simplest fix or its removal). Nothing uses it (see G5).
  - (a) Remove the path, keep the keyword: `parameter_file=False` raises a `ValueError` saying the extraction reads its parameters from the parameter file; the single extraction's keyword branch (19 lines) and the README's two "parametrized via command line" paragraphs go. Every existing call (all pass `True`) keeps working.
  - (b) Make it work: add `cubes` and `stitch_band` keywords, move the file listing and sorting out of the parameter-file block, and give the grid a keyword branch. Its keyword defaults (e.g. the aperture radius) would be physics defaults to decide.
  - (c) Remove the keyword too: breaks every existing call, since all 29 of mine and the shipped notebook pass `parameter_file=True`.
  - Recommended: (a). *(Decided 2026-11-15: (a); see "Decisions".)*
- 2026-11-15: **G9: the aperture of the grid's PSF photometry.** *(Settled 2026-11-15: a typo fix, `r` was meant to be `r_ap`; not a physics decision. See G9.)* Recommended: `r_ap`, the radius the grid gives its data cubes, as the single extraction gives the PSF cubes its data radii. The path can't be tested end to end here without CRETA's PSF cubes.
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
- 2026-11-14: `make_profcube` calls `get_model_fluxes` once per profile per spaxel. With the 10 contcube profiles of M3 1d (3 before), building the contcube takes about 3.3× as long. It doesn't matter for 1D spectra, but it adds up for cubes. Information for M4 (now M6, cube-fit performance).
- 2026-11-14: `cafeplot`'s residual panel uses the combined spectral + photometric arrays. So it joins the photometric residuals to the spectral ones with a line, and its ±4σ y-range includes them. Display only; seen in the M3 group 2 real fit. Not acted on.
- 2026-11-14: The contcube `WAVE` table is float32 (since M1 item H7). In the tutorial spectrum, the sub-band overlaps hold wavelengths only 2×10⁻⁷ µm apart, which float32 cannot separate. So 179 adjacent `WAVE` entries are equal; the fit's float64 grid is strictly increasing. This was already in the fixture contcube, before group 2. Not acted on.
- 2026-11-15: Spectral error floor: the parameters' uncertainties come from the fit, so they reflect the floored χ² (lmfit rescales the covariance by χ²/dof, `scale_covar=True`). That covers the parcube `STDERR` and the relative-error tests in `check_fit_pars` (`REL_ERR_*`); only its 0.5σ peak test uses the quoted spectral errors. Not acted on.
- 2026-11-15: The line table's empty rows (lines not fitted) come out in a different order from run to run; the rows themselves are the same. Seen in the synthetic fits. Not acted on. *(Cause found 2026-11-15: `line_table` builds its list of lines with `list(set(...))` (`cafe_io.py:897`), so their order follows Python's per-process string hashing; the fitted rows are then in wavelength order, the empty ones are not. With `PYTHONHASHSEED` fixed, two runs give identical tables. Reproducibility only; for the clean-up.)* *(2026-11-16, M4: the order also differed between fits with `PYTHONHASHSEED=0` when different lines ended at zero.)*
- 2026-11-15: **The fit amplifies rounding-level differences in its inputs.** The tutorial fit (normalised, `476c6ef`) is bit-identical when repeated, but with inputs that differ only by rounding (2×10⁻¹⁶; flux_scale 1.0000001) it ends elsewhere: STB_FLX 3.7×, HOT_FLX 0.79×, COO_TMP +13%, STB_TAU −35%, line/PAH peaks 5.4% (median of 77; 24 differ by >10%), χ²/N 21,583 vs 21,880. So it does not converge to a unique minimum (FTOL = 10⁻⁵, degenerate components such as STB/HOT/COO, ~100 free parameters). Consequences: any change in floating-point order (code, library versions, machine) can move results by this much; regression-test tolerances must allow for it (my decision); and differences of this size between fits, such as those among the synthetic floor variants 0.75–3% in the optical depths, may be within this spread. Logged as an important finding for M4 (see M4); fit settings are my decision. Not acted on.
- 2026-11-15: Two residual dependences on the source's flux level after the normalisation, both outside the fit: `init_feats` drops a line whose initial peak guess is below 10⁻¹⁰ Jy (an absolute threshold; only matters for sources that faint), and a spectrum whose median |flux| is 0 would divide by 0 (an all-zero spectrum). Neither seen in real data. Not acted on.
- 2026-11-15: **CRETA's extracted fluxes and errors depend on the photutils version.** Same code (`5c7085a`) and NGC7469 cubes, `cafe-dev` (photutils 3.1.1) against `cafe-legacy` (1.10.0), from `g4_compare.py`:
  - Rectangular apertures (the grid's spaxels): photutils 1.10 has no exact overlap for rectangles. With `method='exact'` it samples 32×32 subpixels, so areas come in steps of 1/1024 px² (a 2.46 px square at (20.37, 19.61) gets 6.0947 px² instead of 6.0516). 3.1.1 computes the exact area. Grid fluxes, dev/legacy: 0.972–1.032 (median 1.000). The circular aperture of the single extraction agrees to 10⁻¹⁵.
  - Errors: 1.10 sums σ²·w over the aperture, 3.1.1 sums σ²·w² (w = the fraction of the pixel inside the aperture), so 3.1.1 gives smaller errors wherever partial pixels count. Errors, dev/legacy: grid 0.68–0.95 (median 0.85); single 0.89–0.99 (median 0.98). Which is right depends on how correlated the cube's pixels are (the cubes are resampled): a physics choice, mine to make.
  - Not acted on.
- 2026-11-14: `CAFE_prof_generator` assumes the photometry is sorted by wavelength. It extends the model grid from `phot_dict['wave'][0]` and `[-1]`, and `read_phot` doesn't sort. With an unsorted photometry file, the grid may stop short of the bluest or reddest band. Not acted on. *(Logged as GOALS bug G1 the same day, with a failing case; see "GOALS bugs found after M2".)*
- 2026-11-16: **`flux0` outside the spectrum's range: the docs and the code disagree.** `CAFE_prof_generator` sets each component's `flux0` with `np.interp` (`cafe_helper.py:1010`), which returns the end values outside the spectrum's range. So for a MIRI spectrum HOT, STR and STB (reference wavelengths 3.5, 1.6 and 2 µm) take the flux of the bluest channel (0.158 Jy for all three in the tutorial spectrum), and CIR and CLD (450 and 70 µm) that of the reddest. DESIGN.md ("Parameter naming") says `_FLX` is a ratio to the observed flux at the component's reference wavelength. The model is unaffected (only `_FLX` × `flux0` enters it), but those `_FLX` values rest on a single channel. Seen in M4. Not acted on.
- 2026-11-16: **`init_feats`' line selection depends on the noise.** It leaves out lines whose guessed peak is negative. On M4's S1 (R1's fit plus 1% noise) it left out three lines the truth has ([Al VI] 9.12 µm, [Ar V] 13.10 µm, the broad Na VIII 5.18 µm component; peaks 1.4–6.7 mJy) and kept two the truth lacks. Not acted on.
- 2026-11-17: **The 0.5σ test in `check_fit_pars` also reaches opacity-feature peaks**, which are optical depths: it compares them with the (normalised) flux error at the feature's wavelength and sets those below half of it to 0. The units don't match, so the threshold has no meaning there; it only removes very small optical depths. No shipped setup fits opacity features (0 in R1 and R2). Not acted on.
- 2026-11-17: **The onion path in `check_fit_pars` looks up `HOT_WRM` and `WRM_COO` in the inpars**, where no shipped file has them, so with `Onion = True` it would stop with a KeyError (older code; `Onion = False` in all three opt files). Not acted on.
- 2026-11-17: **`PAH_FLX` only switches the PAH continuum component on or off.** The model uses `fPAH = jPAH`; the scaling by `PAH_FLX` is commented out (`cafe_lib.py`, PAH component). A free `PAH_FLX` would have no effect above 0. It is fixed at 1 in all 7 shipped inpars. Not acted on.
- 2026-11-17: **The expression exception keeps `WRM_TAU` free also when the PAH component is dropped** (`WRM_FLX` and `PAH_FLX` both 0), where it then has no effect. Not possible with the shipped inpars (`PAH_FLX` fixed at 1). Not acted on.
- 2026-11-17: **A `_FLX` or `_TAU` fixed at 0 in the inpars, with that component's other parameters (or MIX and COV) left free:** `check_fit_pars` fixes them only after the first fit, so that fit returns no error bars and one refit follows. No shipped inpars does this. Not acted on.
- 2026-11-17: **`flux0` is `np.interp` of one or two channels**, so their noise sets the scale of every `_FLX`. A channel ≤ 0 in a faint spaxel would stop that component from being positive: `_FLX` ≥ 0 times `flux0` ≤ 0 gives a component ≤ 0, which the model clips to 0. Not acted on (the `flux0` fix comes after M4 stage 2).
- 2026-11-17: **The cool and warm dust components can swap temperatures**: both TMP bounds are [0, ∞) in the shipped inpars, with no order between them. In R2 (M4 stage 2), 7 of 10 stage 1 fits end with COO at 59.4 K and WRM at 29.5 K, about 3,000 higher in χ² than the other state, because `PAH_TAU = WRM_TAU` makes the two labellings differ. Not acted on (see "Awaiting my OK").
- 2026-11-17: **The restart test in M4 stage 2 (stop when a restart lowers χ² by < 1) ended R1's chains while they were still falling ~2 per restart.** A diagnostic setting only; R1's minimum along the valley is not reached.
- 2026-11-17: **Line components at their lower bound stay there.** In R2, the end points within the better minimum differ by which narrow or broad component of H I Humphreys 9–6 (5.91 µm) and 7–6 (12.37 µm) sits at 0; restarts don't bring it back. TRF's step shrinks for parameters near a bound, which may hold them there (not tested). Not acted on.
- 2026-11-17: **In R2, two first `minimize` calls end on the evaluation limit** (47,200, j = 2 and 4, at χ² 4.1–4.7×10⁵, also in stage 1). The refit loop (or a restart) rescues them. Not acted on.
- 2026-11-18: **G14 affected my pre-sync fits.** In the 269 `fitpars.ini` files of my pre-sync folder (121 distinct fits), 51 fits have a free temperature on a G14 jump. CLD_TMP sits on the 6.351 K jump in 42 of the 91 fits where it was free, mostly in the CYGNUS (Spitzer U/LIRG) sample; the others are COO at 19.12 K, WRM at 83.38, 119.4 and 141.5 K, and HOT at several jumps (119–865 K). Those results would change with the fix. Not acted on.
