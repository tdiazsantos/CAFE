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

### M4 — Fitting a JWST spectrum alone *(approved 2026-11-16; **closed 2026-11-19**)*
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
     - *(Done 2026-11-18, reviewed 2026-11-18. Report: `reports/M4_stage3_2026-11-18.md` (work folder). `dev` @ `ffb257a`, shipped `default_opt.cafe`; 90 fits: R1, R2 and S1c × plain, restart (stop when 5 successive restarts together lower χ² by < 1), `x_scale='jac'` + restart, 10 each.)*
     - S1c: truth = R1's stage 3 plain fit (j = 0) with [Al VI] 9.12, [Ar V] 13.10 and broad Na VIII 5.18 µm at 0 (`init_feats` drops them on S1c's data); after that, every true line (74 peaks > 0) is in the fit's set.
     - G14 and the ranges: no end temperature on a former jump (90 fits). R2 no longer swaps (all at COO 30.5, WRM 59.4 K); its plain fits now agree (9 of 10 within Δχ² < 1 of each other; spread 3,103 in stage 1).
     - R1 has two end states. A (restart, all 10): HOT 665 K, STB_FLX ≈ 0.001. B (`x_scale` + restart, 9 of 10), 773 lower: **HOT_TMP at its 200 K lower bound**, HOT_FLX 0.11, STB_FLX 0.58, COO 16 K, WRM 71 K; B gains 5,215 in channel 4C (24.4–28.8 µm observed) and loses ~4,400 elsewhere. The plain fits stop on `ftol` between them, 1,246–2,549 above B, as in stage 1: R1's plain-fit problem is not G14.
     - `x_scale='jac'` + restart: best on R1, worse than plain on R2 (8 of 10 end 26–353 above the best, plain 19.5–21.3), as good as restart alone on S1c.
     - S1c: plain fits 9 of 10 at −143 to −127 below χ²(truth) (expected ≈ −127 ± 16), one at −85; restart and `x_scale` sets −147 to −136. The converged fits agree with each other but sit 2–3 stderr from the truth in COO_TMP, COO_TAU and WRM (one noise realisation). HOT_FLX and STB_FLX anticorrelated within equal-χ² groups (ρ −0.96 to −1.0): fHOT 0.75–0.96, fSTB 0.70–1.23 of the truth.
     - Cost (information): 3 h 05 min at 4 at a time, 12.0 h of fit time.
  6. The `flux0` fix (decided 2026-11-18): each component's `flux0` is the median flux of the 20 channels around its reference wavelength, one-sided at the data edges. Diff hunk by hunk with its reason paragraph and its test; then stop. No more diagnostics in M4.
     - *(Done 2026-11-18, approved 2026-11-18: commit `c071ab1`, `make_cont_profs` (`cafe_helper.py`) takes each `flux0` as the median of the 20 channels around λ₀ (10 below, 10 at or above; the first or last 20 near or beyond an edge); DESIGN.md updated. No PR to GOALS.)*
     - Test `tests/M4/test_flux0.py` (work folder; `make_cont_profs` on synthetic spectra F ∝ λ², shipped AGN inpars and options): on `880551b` it fails 3 of 4 checks, on `c071ab1` it passes 4/4. flux0 equals the median of the expected 20 channels (inside, below, above, and 1–2 channels from an edge); noise-free within 10⁻⁴ of F(λ₀); at 10% noise its scatter falls from 0.062–0.078 (one channel) to 0.025–0.028; zeros at λ₀ or at the first channel no longer set `flux0` to 0. Import smoke test: 0 failed.
     - On R1 and R2 (information, no fit): new / old `flux0` is 0.99–1.02 for every component except CLD and CIR, which use the last channels (1.077 in R1, 0.963 in R2; both fixed at 0 in the shipped inpars).
  7. The baseline, the last M4 step (decided 2026-11-18): plain fits only with the shipped settings, R1 and R2, 10 each with `read_spec(flux_scale = 1 + j × 10⁻⁷)`, j = 0…9, as the reference for M6. Report the χ² spread and the key parameters; then bring DESIGN.md up to date with all M4 changes, show what a push of `dev` to my fork would publish, and stop.
     - *(Done 2026-11-18, reviewed 2026-11-19. Report: `reports/M4_baseline_2026-11-18.md` (work folder). `dev` @ `5ef8463` (code as `c071ab1`), shipped `default_opt.cafe`, no photometry; 20 fits, 3 at a time.)*
     - R1: Δχ² to the best (117,152.80) 0, 237, 290, 396, 408, 422, 423, 434, 772, 961; 1 of 10 the same fit; all stop on `ftol`, no refit. The fits lie along stage 1's valley (lower χ², higher HOT_FLX 0.50 → 0.88, lower STB_FLX 0.23 → 0.003 and COO_TMP 27.7 → 24.5 K); the best is 246 above stage 3's state A. Spread / median stderr: COO_TMP 2.0, STB_FLX 1.7, HOT_TMP 1.2; fHOT 34%, fSTB 38%, fCON 0.19%; model 0.18 of the floored error per channel (median).
     - R2: 8 of 10 within Δχ² 26 of the best (288,938.07; 3 within 2.1), every key dust parameter within 0.2%, model 0.006 of the floored error per channel (median); 146–174 below stage 3's plain fits. **2 of 10 (j = 1, 8) end 450,295 higher, with WRM_TMP at its 50 K lower bound and COO_TMP 48.3 K** (WRM_TAU 26.9, HOT 217 K); see "Biases", 2026-11-18.
     - Times (information; the machine also ran 8 Cloudy jobs, so not a timing baseline): R1 5.5–18.2 min, R2 6.6–9.2 min per fit.

### M5 — Fits with real photometry *(approved 2026-11-19)*
- Fits of a JWST spectrum together with real photometry. The fake-photometry setup is for functional checks only (CLAUDE.md §10).
- **Open: photometry conventions** (logged 2026-11-23).
  - Among them, WISE W4 for red sources (α ≥ 1): the catalogued flux is about 8–10% too high, and Brown et al. 2014 put the effective wavelength at 22.8 µm. Both describe the same discrepancy, so apply one, not both (WISE Explanatory Supplement, sec. IV.4.h).
  - See W2246 below and "Biases".
  - **Photometry enters a fit only once its origin is known: the bands, the instrument and the aperture** (my decision, 2026-11-23).
    - W2246.txt names its points only `filter`. That its 12.0 and 22.0 µm points are WISE W3 and W4 is an inference.
- Refit, with the G14 fix (`93a90dc`), my pre-sync fits that have a temperature on a G14 jump: 51 of 121 distinct fits, CLD_TMP at 6.351 K in 42 of the 91 with CLD free, mostly the CYGNUS fits (logged 2026-11-18; see "Biases", G14).
- **The HOT–STB degeneracy** (decided 2026-11-19): goes here, with near-IR photometry, and to a NIRSpec + MIRI spectrum of NGC7469 (see "Later"). *(NIRSpec + MIRI part closed 2026-11-22: NIRSpec removes M4's MIRI-only valley; see the end of the NIRSpec + MIRI steps below.)*
- **Step 1 (approved 2026-11-19): NGC7469 NIRSpec + MIRI with CRETA's single extraction** (see "Decisions"). *(Done 2026-11-19, waiting for my review; no fits. Work folder: `tests/M5/`, `extractions/NGC7469_NIRSpec+MIRI/`.)*
  - **Data** (read only):
    - NIRSpec, `nirspec/ifu/data/NGC7469/`: G140H/F100LP, G235H/F170LP and G395H/F290LP (`jw01328-o018_t010_nirspec_<grating>_s3d`).
      - Pipeline 1.8.3.dev70, CRDS `jwst_1027.pmap`, written 2022-12-30, observed 2022-07-19; 0.1″ pixels.
      - Two versions: `20221229/` and `20230110/…_wcsfix`. They differ only in CRPIX1 (28 → 23, 0.5″); the data and the ASDF WCS are identical. The two zips hold the `wcsfix` cubes.
    - MIRI, `miri/mrs/data/NGC7469/`: the 12 GOALS HLSP v2.0 cubes (ch1–4, short/medium/long).
      - Pipeline 1.7.2, CRDS `jwst_0963.pmap`, written 2022-09-22, observed 2022-07-04.
      - Byte-identical to `new_wavelength_solution_and_wcs_20230331.zip`. `NGC7469_old/` holds older versions.
  - **CRETA can do it as asked:**
    - `cubes` may mix gratings and MIRI bands, and stitching works on any pair of adjacent bands that overlap (G395H and ch1-short overlap at 4.90–5.28 µm).
    - It centres once, at `lambda_cent`, and uses that sky position in every cube.
    - `point_source = False` gives the same radius at every wavelength; `aperture_correction = False`; `stitch_band = ch1-short`.
    - It needs every cube in one folder, matched by name, so the work folder has symlinks (`data/NGC7469/cubes_nirspec_wcsfix+miri/`).
  - **My choices** *(approved 2026-11-19)*:
    - the `wcsfix` NIRSpec cubes;
    - all three gratings;
    - centring at 5.4 µm, which falls in ch1-short (MIRI's WCS), from the start 23h03m15.614s +08d52m26.09s of `CRETA/param_files/NGC7469_MIRI_single_params.txt`.
  - **Centring.** CRETA put the nucleus at 23h03m15.6110s +08d52m26.079s.
    - From the same start, CRETA's centring in each instrument puts NIRSpec's nucleus 0.19–0.20″ from MIRI's with the `wcsfix` cubes (0.16″ E, 0.11″ N), and 0.60″ with the December 2022 ones.
    - Within MIRI it is at most 0.09″ (ch4).
    - Moving the 1.5″ aperture by those 0.19″ changes its flux by at most 0.4% in every cube tested (1.25–12 µm).
  - **Result:** 20,714 channels, 0.966–28.603 µm (observed).
    - NaN in about 305 channels per grating (detector gaps and flagged pixels, which CRETA's aperture sum turns into NaN) and in 3 MIRI channels.
    - CRETA's warning that the three NIRSpec bands "contain all NaNs" is false: it looks only at each band's first plane (see "Biases").
  - **Stitching ratios** (next band / this band over their overlap):
    - within NIRSpec: G235H/G140H 0.984, G395H/G235H 0.974;
    - **the NIRSpec–MIRI join: ch1-short/G395H 1.180**;
    - within MIRI: 0.954–1.036.
    - Factors to the ch1-short level: NIRSpec × 1.130, 1.148, 1.180; MIRI × 1.04–1.20 (ch4-long × 1.154).
  - **Against R1** (median per band, outside the overlaps):
    - Stitched new / R1 is 1.1544–1.1556 in every MIRI band and in R1's G395H channels. R1 is the same extraction stitched to ch4-long, the CRETA default, and the new one reproduces it to 0.1% apart from the reference band.
    - Unstitched new / R1 runs from 1.155 (ch1-short) to 0.97–1.01 (ch3–ch4).
  - **Against reg1** (shape only; both divided by their median over 2.83–28.1 µm rest): new / reg1 is 1.3–1.7 at 2.8–5.6 µm and falls to 0.26 at 24–28 µm. Below 1 where reg1's PAHs are stronger (7.4–8.6, 11.4–13.3 µm), and about 1.5 in reg1's silicate absorption.
    - reg1 is a much redder, PAH-stronger region than the 1.5″ nucleus, so it is not a stand-in for it.
- **Step 2 (approved 2026-11-19): 10 plain fits of the NIRSpec + MIRI spectrum** (see "Decisions"). *(Done 2026-11-19, waiting for my review. Work folder: `tests/M5/` (`resolution_check.py`, `m5_fit.py`, `run_fit.sh`, `m5_summary.py`), fits in `out/j<j>/`, logs in `logs/`.)*
  - **Setup:**
    - `NGC7469_NIRSpec+MIRI_SingleExt_r1.5as_cube.fits` (step 1), z = 0.0163, `read_spec(ignore_DQ=True, flux_scale = 1 + j × 10⁻⁷)`, j = 0…9; 17,730 channels fitted.
    - Inpars: `tests/M5/params/inpars_jwst_nirspec-miri_AGN_M5.ini`, a copy of the shipped `inpars_jwst_nirspec-miri_AGN.ini` with two lines changed: `Source_HOT = 'AGN'`, `STR_FLX = 0.2, True, 0., 2.` (STR_TAU stays fixed at 0).
    - Shipped `default_opt.cafe`; no photometry; 222 free parameters at the start, 179 at the end (178 in one fit); `dev` @ `47f1fc9`.
  - **Pre-check:** the resolving-power tables cover every band; HOT and STB are free; STR is fixed at 0 in every shipped inpars. Read as shipped, CAFE drops ch1-short, ch1-long and all but 23 ch1-medium channels (15,279 channels reach the fit). See "Biases", (a)–(c).
  - **χ² (floored):** best 201,523.95 (χ²/N 11.37).
    - Δχ² to the best: 0, 0.5, 0.6, 1.4, 1.7, 2.4 (six fits) and 31.5, 31.9, 32.1, 34.0 (j = 5, 4, 3, 8). 3 of 10 are the same fit (Δχ² < 1). All stop on `ftol`; one refit (j = 0).
    - The two groups differ only in line and PAH peaks, by 0.1–1% (most in H I Pfund and Paschen lines, [Ne II], H₂ S(2)). In the four higher fits CAFE fixes the narrow [Si VIII] 5.29 µm component after the fit as unconstrained.
  - **HOT, STB, STR:** the same in all 10 fits to 4–5 digits.
    - HOT_FLX 0.1600–0.1601; **HOT_TMP at its upper bound, 1027.2** (fixed after the fit in 7); HOT_TAU 7.307–7.309.
    - STB_FLX 0.3182; STB_TAU 1.617; STB_010 at its upper bound, 1 (fixed after the fit in all 10).
    - **STR_FLX at 0** (fixed after the fit in all 10). DSK_FLX 0.2317, DSK_TAU 0.091.
    - Correlation within each fit (lmfit, first minimize call): HOT_FLX–STB_FLX +0.83, HOT_FLX–STR_FLX −0.60, STB_FLX–STR_FLX −0.79, HOT_FLX–HOT_TMP −0.33. Across the fits the values differ only at the rounding level, so a correlation across them means nothing.
  - **Fractions of the continuum over 5–6 µm rest** (∫F_ν dν), the same in all 10 fits: HOT 0.327, STB 0.080, STR 0, DSK 0.461, WRM 0.132.
    - R1 state A: HOT 0.515, STB 0.301, WRM 0.184, DSK 0. State B: HOT 0.197, STB 0.692, WRM 0.111, DSK 0.
    - With the 1–5 µm data the fit is in neither of R1's states: the AGN disc, at 0 in R1, takes 46%, HOT is at its upper temperature bound, and STB is small.
  - **χ² per band** (best fit): ch4-long 27% (χ²/N 79), G140H 20%, G235H 15%, ch3-short 12% (χ²/N 39); every other band ≤ 5%.
  - Cost (information only): 6.3–16.7 min per fit, 38 min for the 10 at 3 at a time; peak memory 0.8 GB.
- **Fixes (a) and (b), and the HOT_TMP check (approved 2026-11-20)** (see "Decisions"). *(Done 2026-11-20, waiting for my review. Work folder: `tests/M5/` (`dq_check.py`, `extract.py` with an output-folder argument, `dq_compare.py`, `resolving_power_test.py`, `hot_tmp_check.py`, `line_pedestal_check.py`); the redone extraction in `extractions/NGC7469_NIRSpec+MIRI_dqfix/`; logs in `logs/`.)*
  - **(a), commit `a1ff60a`:** `getApertureDQList` takes the maximum DQ over the pixels the aperture overlaps (`mask.cutout(DQ)[mask.data > 0]`).
    - Not `ApertureMask.get_values` as proposed: that weights each pixel by its overlap, so a half-covered pixel with DQ 513 gives about 250. The pixels are the same.
    - Synthetic DQ planes (21 × 21, r = 3 px): flagged pixels only in the square's corners give DQ 513 before the fix (the failing case) and 0 after. A flagged pixel inside the circle, or partly covered, gives 513 and a NaN flux; one outside gives 0.
    - NGC7469 extraction redone: every plane but DQ is bit-identical. Channels with DQ ≠ 0 go from 3,925 to 914, exactly the NaN-flux channels (ch1: 2,908 → 0; G140H, G235H, G395H: 336, 333, 334 → 305, 303, 303). The channels reaching the fit with the DQ used are bit-identical to step 2's with `ignore_DQ=True` (17,730).
  - **(b), commit `9e8ccd5`:** `CAFE_param_generator` takes the band names (`mask_spec`'s, passed at its five call sites in `cafe.py`). `init_feats` gives each line the table of the band of its nearest channel. Which lines are candidates does not change.
    - The table is found by the band's key (`ch1_SHORT` → `CH1S`, `G140H` → `G140H`) inside the inpars' table names, as `read_inst` matches file names, not by a fixed map: the shipped inpars write the names four ways (`g140h`, `MIRI_CH1S`, `JWST_MIRI_CH1S`, `miri_ch1s`). The band names reach the fit as plain strings (the proposal's `('G140H')` was wrong).
    - `UNKNOWN` bands, and bands with no table of their own in the inpars, keep today's rule (see "Awaiting my OK"). *(Changed 2026-11-20: such a band now stops the fit with an error, commit `fb585da`; see below.)*
    - Synthetic test (z = 0.05; G395H, ch1-short, -medium, -long; 33 lines): before the fix 13 lines were off their band's R by +9 to +29% (tables in the inpars' order) and 9 lines by −5 to −7% (order reversed). After it, every line is within 3×10⁻¹⁶ of its band's R in both orders; `UNKNOWN` bands give the old widths bit for bit; the same lines are kept.
    - NIRSpec + MIRI starting parameters: the widths of 9 of the 12 lines listed under (b) change, each to its band's R. [Fe II] 5.67 and H I 8.67 µm are in neither starting object (peak guess ≤ 0).
    - [S VII] 5.23 µm was not in the old starting object and enters the new one: with the right width its peak guess is > 0. So the proposal's "which lines are fitted stays as now" holds for the candidates, not for the guesser's choice.
    - Every other peak guess moves by ≤ 6×10⁻¹⁴ (`gauss_prof`'s tails; see "Biases").
    - R1: starting parameters identical.
    - R2 (CRETA cube, MIRI band names): [Ni II] 6.64 µm R 3734 → 3184 (ch1-long data, ch1-medium's table before) and [Ne III] 15.56 µm R 2607 → 2090 (ch3-long data, ch3-medium's table before). M4's R2 fits had these two narrow widths 15% and 20% too narrow.
    - Smoke tests: `specmod.plot_spec_ini` (NIRSpec + MIRI) and `cubemod.plot_cube_ini` (pre-sync `NGC7469_GridExt_3x3_s1.0as_cube.fits`, spaxel (1, 1)) run.
    - End to end: one plain fit (j = 0, step 2's setup, `tests/M5/out/fixb_j0/`) on the working tree before the commit. It runs (15.9 min, stops on `ftol`, 223 → 179 free parameters, [S VII] 5.23 µm the extra one). χ² 201,244.39, 279.6 below step 2's best; HOT, STB, STR and DSK as in step 2 to 4 digits (HOT_TMP at 1027.2).
  - **HOT_TMP (read-only):**
    - **Origin of 1027.2:** in every inpars since GOALS' first commit (`4e667dd`, Thomas Lai, 2023-01-04), with the comment `_HOT_TMP = 571.6 -> <HOT_TMP> = 1250K`, and in every pre-sync inpars. The fits saved in that commit's notebooks already stop at it.
      - No code uses it. It is not a grid temperature (996.9 and 1148.3 K on either side; 905.5 and 1127.9 in the original `geomspace(3, 1750, 30)`). Its derivation is not recorded. M4 changed only the lower bound (100 → 200 K).
    - **Meaning:** HOT_TMP is `T_bb`, the radiation field's intensity written as a blackbody temperature, σT_bb⁴/π, with the spectral shape of `Source_HOT`'s SED (`grainEQTemp`, `grain_emissivity`, `grain_totemissivity`). It is not a grain temperature.
      - Each grain size and species reaches its own T_eq by balancing what it absorbs from that field against its emission (Eq. 12 of Marshall et al. 2007, as the code says). Large grey grains sit near T_bb (10 µm grains: 0.96 T_bb for silicates, 1.02 T_bb for carbon); small grains are much hotter.
      - At T_bb = 1027.2 K (AGN SED) the surviving carbon grains have a mass-weighted mean T_eq of 1216 K; 10 µm silicates are at 984 K. The plot legend's "Hot (1027 K)" is T_bb.
    - **What the grid allows at the top:** the emissivity grid has 30 T_bb points from 3 to 1750 K (… 865.0, 996.9, 1148.3, 1322.0, 1521.3, 1750.0), interpolated in log j. `grainSizeDF` removes every grain with T_eq > 1400 K, so small grains go first as T_bb rises.
      - AGN SED: silicate mass kept 59% at 571.6 K, 9% at 750 K, ≈ 0 from 865 K. Carbon mass kept 72% at 571.6 K, 44% at 1027.2 K, 32% at 1148.3 K, 10% at 1322 K, none at 1521.3 K. The ISRF is similar.
      - HOT's shape as the fit sees it (AGN): its ν F_ν peak stays at 2.2–2.3 µm from 800 to 1148 K. F_ν(2 µm)/F_ν(5 µm) is 1.42 at 800 K, 1.66 at 1027.2 K and 1.71 at 1148.3 K. Above that it falls again (1.46 at 1200 K, 1.04 at 1322 K), as only the large grains are left. From 1521.3 K on, HOT is a flat F_ν (see "Biases"). ISRF: 1.77 at 1027.2 K, 1.84 at 1148.3 K.
      - So the bound sits near the hottest-looking HOT the model can make: raising it gains at most 3–4% in F_ν(2)/F_ν(5), up to 1148 K. No T_bb gives grains above 1400 K, because carbon is cut at the silicates' 1400 K and its own 1750 K (`sSubCar`) is unused (see "Biases"). *(Carbon is cut at 1750 K since `076adbd`; see below.)*
- **Review of (a) and (b); carbon at 1750 K; HOT_TMP up to 1750 K in a work-folder copy (approved 2026-11-20)** (see "Decisions"). *(Done 2026-11-20, waiting for my review. Work folder: `tests/M5/` (`resolving_power_test.py` section 4, `band_table_test.py`, `carbon_sublimation_test.py`, `hot1750_summary.py`; `m5_fit.py` and `run_fit.sh` take a run set); fits in `out/hot1750_j<j>/`; logs in `logs/`.)*
  - **`bandname` keyword, commit `5f3a533`:** `bandname=None` is the last keyword of `CAFE_param_generator` and of `init_feats`. `None` keeps today's rule (the first table whose range holds the line). The five call sites in `cafe.py` pass it by keyword.
    - Fix (b)'s test passes unchanged. Without `bandname`, the old arguments give the old NIRSpec + MIRI starting object bit for bit (511 parameters).
  - **NIRSpec tables in `SB_and_AGN`, commit `173f758`:** `g140h` and `g235h` before `g395h`.
    - On NGC7469 NIRSpec + MIRI, 35 lines enter the starting object (22 on G140H data, 13 on G235H) and none leaves. Three lines on G235H data that had G395H's table get their own, R +75% ([Si VII] 2.48, Br β 2.63, [Mg VIII] 3.03 µm). Every narrow width is at its band's R.
    - `_reg` is not changed: it cannot be loaded (see "Biases" and "Awaiting my OK").
  - **Error for a band with no table, commit `fb585da`:** `init_feats` raises a `ValueError` that names the band.
    - Synthetic spectrum (G395H, ch1 short, medium, long; no ch1-medium table): the error names `ch1_MEDIUM`. With all four tables there is no error. With `UNKNOWN` bands or no `bandname`, there is no error and the widths are as before, bit for bit.
    - Shipped inpars on NGC7469's 15 bands: `miri_AGN` and `miri_SB` stop with an error naming G140H (before, they ran without the lines below 4.9 µm); the others run. R1, R2 and the NGC7469 fit setup start as before, bit for bit.
  - **Carbon at 1750 K, commit `076adbd`:** `grainSizeDF` removes carbon grains with T_eq > `sSubCar` = 1750 K; silicates still go at `tSubSil` = 1400 K. Test for the AGN, ISRF, SB2Myr, SB10Myr and SB100Myr SEDs:
    - Silicate size distributions and emissivities identical, bit for bit; `grain_opacity` (T_bb = 0, as the fit calls it) identical.
    - The carbon size distribution equals the uncut one where T_eq ≤ 1750 K (≤ 1400 K before) and is 0 elsewhere. The carbon emissivity changes from T_bb = 420 K (SB2Myr), 486.3 K (AGN, SB10Myr) or 750 K (ISRF, SB100Myr) up. So WRM (≤ 200 K) and COO are unchanged in every shipped inpars but `IIZw096` (open bounds).
    - Carbon mass kept (AGN), before → after: 996.9 K 0.44 → 0.63; 1148.3 K 0.32 → 0.56; 1322 K 0.10 → 0.47; 1521.3 K 0 → 0.36; 1750 K 0 → 0.
    - HOT's shape (AGN), after: the ν F_ν peak is at 1.8–1.9 µm from 1000 K on (2.25 µm before). F_ν(2 µm)/F_ν(5 µm) is 2.55 at 1027.2 K (1.66 before), 2.83 at 1148.3 K, 3.26 at 1322 K, 3.31 at 1521.3 K and 2.15 at 1600 K; at 1750 K there is no emission. ISRF: 2.70 at 1027.2 K (1.77 before), 3.30 at 1521.3 K.
  - **10 plain fits with HOT_TMP up to 1750 K** (`hot1750`):
    - **Setup:** step 2's spectrum from fix (a)'s extraction, read with the DQ (`ignore_DQ=False`: step 2's 17,730 channels and errors), z = 0.0163, `flux_scale = 1 + j × 10⁻⁷`, j = 0…9.
      - Inpars: `tests/M5/params/inpars_jwst_nirspec-miri_AGN_M5_hot1750.ini`, step 2's copy with `HOT_TMP = 500.0, True, 200., 1750.`. Shipped `default_opt.cafe`; no photometry.
      - 223 free parameters at the start, 180 at the end (181 in 3). `dev` @ `bfce1a0` (j = 0–2) and `5073617` (j = 3–9): earlier versions of `076adbd` with the same tree (only the commit message differs).
      - Against step 2, three things change: fix (b), carbon to 1750 K, and HOT_TMP's bound. `fixb_j0` has fix (b) alone.
    - **χ² (floored):** best 200,549.87 (χ²/N 11.31), 974.1 below step 2's best and 694.5 below `fixb_j0`.
      - Δχ² to the best: 0, 1.0, 2.4, 3.0, 3.4, 4.4, 16.7 (7 fits) and 3,925.8, 3,926.2, 3,927.1 (j = 7, 8, 9). Spread 3,927.1 (step 2: 34.0). 1 of 10 is the same fit (step 2: 3). All stop on `ftol` after one minimize call.
    - **Two end states.** The 7 low fits have STR at 0, as in step 2. In j = 7–9: STR_FLX 0.443 (free to the end), DSK_FLX 0.189 and DSK_TAU 0.39 (0.232 and 0.091 in the low fits), HOT_FLX 0.144 (0.158). No step 2 fit ended there.
    - **HOT_TMP is 1519.8–1521.3 K in all 10 fits**, 0.04–1.5 K below the 1521.31 K grid point, and none is above it.
      - That grid point is where HOT's F_ν(2)/F_ν(5) peaks (3.31). Below it the shape hardly changes (3.26 at 1322 K); above it the shape flattens fast toward the empty 1750 K point.
      - So the fit takes the bluest HOT the grid offers, as step 2 took its bound. HOT_TMP's stderr there (± 310 K) means little.
      - HOT_FLX 0.158 and HOT_TAU 8.24 (step 2: 0.160, and 7.31 with HOT_TMP at its 1027.2 bound).
    - **Fractions of the 5–6 µm continuum** (∫F_ν dν):
      - Low fits: HOT 0.324, DSK 0.463, STB 0.081, WRM 0.133, STR 0. Step 2 and `fixb_j0`: 0.327, 0.461, 0.080, 0.132, 0.
      - j = 7–9: HOT 0.299, DSK 0.455, STR 0.033.
      - So HOT is bluer and more extincted, and its share and the disc's move by ≤ 0.003.
    - **χ² per band** (best fits, against `fixb_j0`): G235H −234, ch1-medium −233, G395H −94, ch4-long −57, ch2-medium −50, G140H −42, ch1-long +53. Against step 2, ch1-short also drops by 299, from fix (b) ([S VII] 5.23 µm).
    - Cost (information only): 10.0–48.5 min per fit, 3 at a time.
- **Second review round: shipped optical depths and HOT_TMP's bound (approved 2026-11-20)** (see "Decisions"). *(Done 2026-11-20. Reviewed the same day: the 0.1 starts and HOT_TMP's bound are kept; DSK_TAU's fix is under review (see the next bullet). Work folder: `tests/M5/` (`inpars_tau_test.py`, `tau01_summary.py`, `tau01_check.py`; `m5_fit.py` run set `tau01`); fits in `out/tau01_j<j>/`; logs in `logs/`.)*
  - `5073617`'s message now says 61% at 1027.2 K: it is `076adbd`, same tree; the brief commit after it was recommitted (`29893bb`).
  - `_reg`'s `read_inst` fix is on hold: the file fails before `read_inst` (see "Biases" and "Awaiting my OK").
  - **Shipped inpars, commit `9ffc4b7`:** in all seven, every free COO_TAU, WRM_TAU, HOT_TAU and STB_TAU starts at 0.1. DSK_TAU is `0.0, False` in `miri_AGN`, `nirspec-miri_AGN` and `_reg` (bounds kept). HOT_TMP's upper bound is 1750 K.
    - Test (`inpars_tau_test.py`: each file as `read_inifile` reads it, against `29893bb`): only those entries change, and only in those fields. Every file's continuum parameter object builds, with its values within bounds. `_reg` keeps its CRLF line ends.
  - **10 plain fits with the new inpars** (`tau01`):
    - **Setup:** as `hot1750` (spectrum, channels, errors, z, flux_scale, options; no photometry), with `tests/M5/params/inpars_jwst_nirspec-miri_AGN_M5_tau01.ini`: the shipped `nirspec-miri_AGN` after `9ffc4b7` with step 2's two changes (`Source_HOT = 'AGN'`, STR_FLX free from 0.2).
      - Against `hot1750`'s copy: COO_TAU 2.0 → 0.1, HOT_TAU 0.5 → 0.1 and STB_TAU 0.5 → 0.1 at the start (WRM_TAU 0.1 in both); DSK_TAU fixed at 0 (free from 0.1).
      - 222 free parameters at the start, 177–178 at the end. `dev` @ `9ffc4b7`.
    - **χ² (floored):** best 254,887.81 (χ²/N 14.38), 54,337.9 above `hot1750`'s best (+27%).
      - Δχ² to the best: 0, 1.1, 6.0, 11.3, 16.9, 18.1, 18.1, 18.2, 18.8, 19.5. Spread 19.5 (`hot1750`: 3,927.1). 1 of 10 is the same fit. All stop on `ftol`.
    - **One end state in all 10 fits: the disc drops out** (DSK_FLX at 0, fixed after the fit).
      - HOT_TMP 710.7–714.7 K (± 23 K), between the 649.8 and 750 K grid points; HOT_FLX 0.39.
      - WRM_TMP 138 K; COO_TMP at its 50 K bound (fixed after the fit). STR_FLX 0.387 (free to the end); STB_FLX 0.56.
    - **Optical depths** (best fits, `tau01` / `hot1750`): COO_TAU 2.37 / 9.18; WRM_TAU (= PAH_TAU) 0.44 / 0.32; HOT_TAU 2.09 / 8.24; STB_TAU 1.36 / 1.63; DSK_TAU 0 (fixed) / 0.091. The 10 `tau01` fits agree to 1%.
    - **Fractions of the 5–6 µm continuum:** HOT 0.222, DSK 0, STR 0.028, STB 0.112, WRM 0.634, COO 0.004. `hot1750`'s low fits: 0.324, 0.463, 0, 0.081, 0.133, 0.
    - **χ² per band** (best fits, against `hot1750`): ch4-long +22,077, G395H +7,082, ch4-short +6,914, ch1-medium +5,225, G235H +3,230, ch3-short +2,827, ch3-medium +2,349, ch4-medium +2,084; G140H −456 and ch2-medium −862.
    - **Which change does it: not separated.** `hot1750`'s best with only DSK_TAU set to 0 gives χ² 3,921,068 (`tau01_check.py`, no refit; it rebuilds both best fits' χ² exactly). So that point does not tell whether the 0.1 starts or DSK_TAU = 0 lead to the new state. Fits with each change alone would.
    - Cost (information only): 9.9–20.5 min per fit, 3 at a time.
- **DSK_TAU free again: the candidate `0.1, True, 0., 0.5` (approved 2026-11-20; run set `dskfree`)** (see "Decisions"). *(Done 2026-11-20. Reviewed 2026-11-22: DSK_TAU's shipped default becomes this candidate, see the next bullet. Work folder: `tests/M5/` (`dskfree_summary.py`; `m5_fit.py` run set `dskfree`); fits in `out/dskfree_j<j>/`; log `logs/dskfree_summary.txt`.)*
  - **Setup:** as `tau01`, with `tests/M5/params/inpars_jwst_nirspec-miri_AGN_M5_dskfree.ini`: the `tau01` copy with `DSK_TAU = 0.1, True, 0., 0.5`. Only j = 0, 1 and 2 (my change, 2026-11-20).
    - Against `tau01`: only DSK_TAU. Against `hot1750`: the 0.1 starts of COO_TAU, HOT_TAU and STB_TAU, and DSK_TAU's upper bound (0.5 here, 2 there).
    - 223 free parameters at the start, 181 at the end. `dev` @ `3be2054` (code as at `9ffc4b7`).
  - **χ² (floored):** best 204,473.92 (χ²/N 11.53). Δχ² to the best: 0, 5.9, 6.2 (spread 6.2; 1 of 3 is the same fit). All stop on `ftol`.
    - 3,924 above `hot1750`'s best and 50,414 below `tau01`'s. Over the same j, `hot1750`'s spread is 2.3 and `tau01`'s 13.5.
  - **End state: all three end in the state of `hot1750`'s j = 7–9** (STR on). Their free parameters agree with `hot1750`'s j = 7 to 0.05% (median), and the best is 1.8 below it in χ². At the same j (0, 1, 2), `hot1750`'s fits ended in its lower state (STR at 0).
  - **Optical depths** (best fits, `dskfree` / `hot1750` / `tau01`): COO_TAU 8.93 / 9.18 / 2.37; WRM_TAU (= PAH_TAU) 0.25 / 0.32 / 0.44; HOT_TAU 8.30 / 8.24 / 2.09; STB_TAU 1.59 / 1.63 / 1.36; DSK_TAU 0.391 / 0.091 / 0 (fixed). DSK_TAU is not at its bound (0.5) in any of the three.
  - **HOT_TMP** 1518.9–1521.3 K, at the 1521.31 K grid point (± 411 K), as in `hot1750`. **COO_TMP** 36.4 K, not at a bound (`hot1750` 35.1 K; `tau01` at its 50 K bound). **DSK_FLX** 0.189 (`hot1750` 0.232; `tau01` 0).
  - **Fractions of the 5–6 µm continuum** (`dskfree` / `hot1750` best / `tau01` best): HOT 0.299 / 0.324 / 0.223; DSK 0.456 / 0.463 / 0; WRM 0.136 / 0.133 / 0.633; STR 0.033 / 0 / 0.028; STB 0.077 / 0.081 / 0.112.
  - **χ² per band** (best fits, `dskfree` − `hot1750`): ch4-long +918, G235H +869, G140H +678, ch2-medium +678, ch2-long +530, ch1-medium +362, G395H +315; ch4-medium −319.
  - **So DSK_TAU = 0 is what made the disc drop out in `tau01`.** With DSK_TAU free, the 0.1 starts reach `hot1750`'s STR-on state. The fits don't separate whether the 0.1 starts or DSK_TAU's 0.5 bound send them there rather than to the lower state. DSK_TAU ends at 0.39, inside both bounds. Three fits can't tell how often each state occurs.
  - Cost (information only): 57.7–60.8 min per fit, 3 at a time, on a machine loaded by other jobs (load average 21–29). That is 19,499–21,510 evaluations, against 16,360–17,255 for `hot1750`'s j = 0–2 (10.0–10.8 min). Peak memory 0.28–0.30 GB.
- **DSK_TAU's shipped default, commit `72e9edd` (decided 2026-11-22):** `DSK_TAU = 0.1, True, 0., 0.5` wherever DSK is free: `miri_AGN`, `nirspec-miri_AGN` and `SB_and_AGN`. `_reg` stays on the M7 list.
  - Test (`inpars_dsktau_test.py`: each file as `read_inifile` reads it, against `669ebe2`): only DSK_TAU changes, and only in those three files. Every file's continuum parameter object builds, with its values within bounds.
  - The shipped `nirspec-miri_AGN` now differs from the `dskfree` copy only by step 2's two changes (`Source_HOT`, STR_FLX).
- **NIRSpec + MIRI step closed (2026-11-22, my decision): NIRSpec removes M4's MIRI-only valley.** What is left is logged in "Biases" (2026-11-22): the two end states, and the dust optical depths bent toward a power law.
- **W2246, MIRI only: CRETA's single extraction (2026-11-23, my request; see "Decisions").** *(Stopped 2026-11-23: with both cube sets, CRETA's centring fails and one stitching ratio is negative. Step 3, the comparison with M3's spectrum and the photometry, not run. Work folder: `tests/M5/` (`extract_W2246.py`, `params/W2246_MIRI_r0.5as_params.txt`, `W2246/centring_diag.py`, `W2246/stitch_diag.py`, `W2246/mast_inventory.py`); cubes linked in `data/W2246/`; extractions in `extractions/W2246_MIRI/` (stage3) and `extractions/W2246_MIRI_c1003/`; logs in `tests/M5/logs/`.)*
  - **Data** (read only):
    - `miri/mrs/stage3/`: 12 `Level3_*_s3d.fits`, program 1712, observation 002 (4 dithers), observed 2023-07-17. Pipeline 1.13.4, CRDS `jwst_1214.pmap`, written 2024-03-29. Master background subtracted (`S_MSBSUB = COMPLETE`).
    - `miri/mrs/mast/202611/` (MAST): 36 s3d cubes, all pipeline 3.0.0, CRDS `jwst_1584.pmap`, written 2026-10-18, `skyalign`, `S_BKDSUB = SKIPPED`.
      - `sci/`: two products of the same 4 exposures of observation 002. `jw01712-c1003_t001_*` pairs them with the background observation and is master background subtracted (`S_MSBSUB = COMPLETE`). `jw01712-o002_t001_*` has no background subtraction.
      - `bkg/`: `jw01712-o001_t003_*`, the dedicated background field (`W2246-0526-MIRI-MRS-BKG`, observation 001, 2 exposures).
      - These cubes have a `WCS-TABLE` extension; CRETA reads them.
  - **Setup:** a cone of 0.5″ at 5.4 µm (radius ∝ λ), as M3's `W2246_SingleExt_r0.5as.fits` records it (that extraction was not centred). CRETA's centring at 5.4 µm from M3's position 22h46m07.5646s −05d26m34.802s. No aperture correction, no background subtraction, `stitch_band = ch1-short`. `dev` @ `e9ad4a7`.
  - **The centring fails in both sets.** In ch1-short at 5.4 µm, CRETA's 11×11-pixel box around W2246 sums to less than 0, although W2246 is there (peak 20–22 MJy/sr, 1–2 pixels from the start).
    - ch1-short: box median −6.6 MJy/sr per plane in stage3 and −6.0 in `c1003`; 109 and 105 of 121 pixels negative.
    - ch1-long: −3.7 and −4.9 MJy/sr; 102 and 107 negative. ch1-medium is positive (+4.6, +4.2).
    - So both extractions stayed at M3's position, while CRETA's metadata says `Centering: True`.
  - **W2246's centroid offset from M3's position, per cube** (CRETA's centring at mid-band; ch1-short at 5.4 µm):
    - stage3: ch1-short and ch1-long fail; ch1-medium 0.197″ (S); ch2–ch4 0.011–0.045″.
    - `c1003`: ch1-short and ch1-long fail; ch1-medium 0.205″; ch2–ch4 0.124–0.163″, all to the west (E −0.12 to −0.16″, N −0.05 to +0.01″).
    - So the `c1003` cubes put W2246 about 0.14″ W of where the stage3 cubes put it. Probably a WCS change between the two pipeline versions (inference).
  - **Stitching ratios** (CRETA's, band n+1 / band n over their overlap, ch1-short → ch4-long):
    - stage3: 0.818, **−1.685**, 0.889, 0.937, 0.910, 1.163, 0.963, 1.008, 0.960, 1.167, 1.227.
    - `c1003`: 0.813, **−5.317**, 1.114, 1.037, 0.945, 1.214, 0.998, 1.033, 1.002, 1.183, 1.208.
    - The negative one is ch1-medium → ch1-long (6.53–6.63 µm). In `c1003` the two bands' mean fluxes there are +0.013 and −0.057 mJy. Every band from ch1-long on is scaled through it, so the stitched spectrum changes sign from ch1-long on. ch1-short itself is negative: median −0.042 mJy in both sets.
  - **`c1003`'s ch4-long goes negative beyond 27 µm.** Its median flux is +15.3 mJy at 24.5–25 µm, −6.6 at 27–27.5, −94 at 27.5–28 and −350 mJy at 28–28.5 µm. Stage3 holds 14–21 mJy to 28 µm and is −75 mJy at 28–28.5 µm. The master background probably over-subtracts there (inference).
  - **The stage3 extraction does not reproduce M3's `W2246_SingleExt_r0.5as.fits`.** This is a diagnosis, not step 3 (inline check, log `logs/stitch_diag_W2246.txt`).
    - Same position, radius and wavelengths, yet the unstitched fluxes differ by up to 200σ: ch1-short −0.042 vs +0.021 mJy, ch1-long −0.061 vs +0.119 mJy, ch1-medium ×1.40, ch2-short ×1.31, ch4-medium ×1.20, the other bands ×0.96–1.02.
    - My notebook reads its cubes from `/ssd/up/hotdogs/jwst/W2246/miri/mrs/analysis/20250206_master_bg/` (another machine), with the stage3 path commented out.
    - Not settled whether the cubes or CRETA's code since then make the difference.
  - **Photometry for step 3:** `W2246.txt` has two points in 4.9–28.7 µm, 12.0 µm (2.5 ± 0.2 mJy) and 22.0 µm (15.9 ± 1.6 mJy). They are named only `filter`, with width 0 (presumably WISE W3 and W4). There are no WISE response curves yet, so they will be compared with the spectrum interpolated there.
  - **NIRSpec mega cubes** (`nirspec/ifu/processed/`; read only, not for fitting; my request, 2026-11-23; folder `tests/M5/W2246_megacubes/`):
    - All four are 190×134×9119 cubes (1.660–5.271 µm observed, 0.05″ pixels), "assembled and sigma clipped by Vayner et al. 2023b algorithm", pipeline 1.13.4, `jwst_1223.pmap`.
      - HDUs: PRIMARY, SCI, a second SCI and an unnamed third. No NaN; zeros mark missing data.
      - There is no spatial shift between the versions.
    - **`fix_wcs`:** in MJy/sr, with the corrected WCS in its first SCI. It is the one for W2246's total SED when we get to NIRSpec (my decision).
      - **Its second SCI is probably the variance** (≥ 0, zero where there is no data; empty-sky scatter 0.86–1.53 × its square root; not settled). CRETA would need a σ in an `ERR` extension. That HDU's WCS has the new CRPIX but the old CRVAL (1.6″ off).
      - The third HDU is all zeros (float64).
    - **`wcs_fix_old`:** a byte-for-byte copy of `fix_wcs`.
    - **`nuclear2`:** `fix_wcs` converted to F_λ per spaxel, 10⁻¹⁵ erg s⁻¹ cm⁻² µm⁻¹ (constant to 4×10⁻¹⁶), **but its BUNIT still says MJy/sr.**
      - It keeps the old pipeline WCS, which puts the nucleus 0.25″ elsewhere on the sky.
      - Corner pixel (1,1) holds a nucleus-like spectrum (zero in `fix_wcs`), close to a 0.15″-radius nuclear sum (ratio 0.98).
    - **`psf_sub_fix_wcs`:** in the same units as `nuclear2`, **with the same wrong BUNIT**.
      - It is smoothed spatially by a Gaussian of σ = 2 px (0.1″), minus a compact nuclear model. Within 0.15″ of the nucleus, 4–9% of the flux stays below 3.5 µm and 34–46% above 4.5 µm.
      - Nothing is subtracted at 1.660–1.775 and 5.200–5.271 µm. Its variance was not updated for the smoothing (inference).
  - **The pipeline's `c1003` x1d spectra treat W2246 as extended** (read only, 2026-11-23; `W2246/x1d_check.py`, `W2246/x1d_background_check.py`). The x1d route is closed (my decision, 2026-11-23).
    - **Extraction:** `SRCTYPE = EXTENDED` in all 12 bands, taken from APT (`SRCTYAPT = EXTENDED`; the dither pattern is the extended-source one).
      - The area is the whole field, centred on the cube's middle pixel, not on W2246, and does not change with wavelength. It is about 96% of each cube's valid pixels: ~1,105 pixels of 0.13″ in ch1 (as wide as a 2.4″-radius circle), ~960 of 0.17″ in ch2 (3.0″), ~1,155 of 0.20″ in ch3 (3.8″), ~580 of 0.35″ in ch4 (4.8″).
      - No annulus; the reference file is `jwst_miri_extract1d_0004.asdf`.
    - **No background subtracted and no aperture correction:** `FLUX` equals the plain sum of the whole cube to 4 digits.
      - The step loaded the aperture-correction files `jwst_miri_apcorr_0007` (ch1; not logged for ch1-short), `0005` (ch2), `0006` (ch3) and `0004` (ch4). The pipeline applies them only to point sources.
      - The `BACKGROUND` column is not the background field: it is −2.9 MJy/sr in ch1-short, where the field is +5.9. It looks like the cube's leftover level after the master background (inference). It is recorded, not subtracted.
    - **Flux:**
      - ch1-short is negative in 96% of channels (−1.5 to −1.0 mJy), smooth (channel scatter 1.2 × the errors).
      - ch1-long is negative in 95% (about −2.6 mJy to 7.5 µm, −0.2 at 7.5–7.65 µm), smooth (1.2 ×).
      - ch4-long beyond 27 µm falls steeply: −51 mJy at 27–27.5 µm, −365 at 27.5–28, −1,484 at 28–28.5 and −410 at 28.5–28.7 µm; the scatter is 12.6 × the errors over the band.
      - The cause is the negative leftover background summed over the whole field (about −1.3 mJy in ch1-short, −55 mJy in ch4-long).
    - **Against CRETA's `c1003` extraction** (at M3's position, 0.138″ from the 8.0 µm one; unstitched; bands where both medians are positive): x1d/CRETA 3.97 (ch2-short), 2.07, 1.54, 1.35, 1.42, 1.33, 1.15 and 1.67 (ch4-medium).
      - Not a calibration test: the whole field against a 0.5″ cone. In ch2-short the leftover background over the field (+1.6 mJy) is most of the x1d's 1.98 mJy, while W2246 gives 0.44 mJy in the cone.
  - **CRETA's per-plane annulus for point sources, commit `9017022`** (2026-11-23, my request; waiting for my review; see "Awaiting my OK").
    - **The change:** with `point_source = True` and background subtraction on, each plane's annulus starts at `r_ann_in` scaled with wavelength like the cone, and ends at the largest circle around the source inside the cube's field (`getFieldRadii`).
      - A plane whose annulus has fewer than 50 valid pixels, or no room, gets a NaN background and flux.
      - Extended sources keep the fixed annulus.
    - **Synthetic test** (`tests/M5/annulus/test_point_source_annulus.py`):
      - Setup: four MIRI-like bands of 41×41 pixels with small rectangular fields; a 1 mJy Gaussian point source (FWHM from Law et al. 2023); a flat background of +3, −3 or 0 MJy/sr × λ/5.4 µm, with and without noise of 1 MJy/sr per pixel; a 0.3″ cone at 5.4 µm with `r_ann_in = 0.6″`.
      - Result: 17/17 checks pass.
        - Background recovered to 4×10⁻¹⁶ MJy/sr, and the flux with the background on equals the flux with it off, to 3.6×10⁻⁸.
        - The NaN planes are exactly those with fewer than 50 annulus pixels, counted from the geometry: 147 of 281 in ch1-long and all 316 in ch2-short, which has no room.
        - With noise: the background error has mean +0.02 ± 0.04 and rms 1.02 × 1.25σ/√N; the flux error has mean +0.17 ± 0.08 µJy.
      - Before the change, CRETA stops on the same cubes with photutils' `'r_out' must be greater than 'r_in'`.
    - **Regression:** the real NGC7469 single extractions of M3 (`single_all.txt`, no background; `single_all_bkgsub.txt`, extended source with background) are identical before (`96dced6`) and after (`.fits`, `_cube.fits` and the `.csv` table).
    - **W2246, read only** (`W2246/annulus_fit_fwhm.py`; cone 0.28″ at 5.4 µm, multiple 2, centred at 8.0 µm):
      - The annulus fits in all 12 bands, in every plane with data: at least 98 valid pixels (ch4-long), 172–690 in the others.
      - ch4-long's last 12 planes (28.633–28.699 µm) have no data at all.
      - The largest multiple with at least 50 pixels everywhere is 2.2, set by ch4-long.
    - *(Approved 2026-11-23; see "Decisions".)*
  - **CRETA scales point-source cones with the PSF's FWHM, commit `2818075`** (2026-11-23, my request; waiting for my review; see "Awaiting my OK").
    - **The change:** r(λ) = r_ap × FWHM(λ) / FWHM(λ_ap) for the cone, and so for the annulus's inner radius, with the FWHM law chosen from each cube's `INSTRUME`.
      - MIRI MRS follows Law et al. 2023, with FWHM(λ_ap) from MIRI; a `lambda_ap` below 4.9 µm stops with a `ValueError`.
      - NIRSpec keeps FWHM ∝ λ, as before. Extended sources are unchanged.
    - **Synthetic test** (`tests/M5/fwhm/test_fwhm_cone.py`):
      - Setup: the 12 MRS bands and a NIRSpec G395H-like band, each sampled at FWHM/20 per pixel, 121×121 pixels, 0.05 µm per plane. A 1 mJy Gaussian, integrated over each pixel, with the FWHM of Law et al. (MIRI) or ∝ λ (NIRSpec). r_ap = 0.2842″ at 5.4 µm. No background, no noise.
      - At 0.05″ per pixel, the aperture's pixelisation reached 0.6% at 4.9 µm and 1.7% in the NIRSpec band, hence the finer sampling. The tolerance, 0.003, is unchanged.
      - **After the change** (all pass):
        - MIRI R_ap = r_ap × FWHM(λ)/FWHM(5.4) to 2×10⁻¹⁶″, so 1.000 FWHM in every band.
        - The flux in the cone is 0.9370–0.9372 in every MIRI band (a Gaussian's 0.9375 within pixelisation).
        - NIRSpec: R_ap = r_ap × λ/5.4, as before; flux in the cone 0.9367–0.9373.
        - With r_ann_in = 0.5684″, the annulus's inner radius is 2 FWHM(λ) in ch4-long.
        - `lambda_ap = 4.0 µm` with MIRI cubes stops with the `ValueError`.
      - **Before** (`bebd239`'s CRETA): the MIRI cone runs from 0.99 FWHM (ch1-short) to 1.42 FWHM (ch4-long), and the flux in it from 0.9232 to 0.9966. NIRSpec is the same as after.
    - **Regression:** NGC7469's M3 single extraction without background, with an extended-source background, the 3×3 grid, and M5's NIRSpec + MIRI extraction are byte-identical before (`bebd239`) and after (all `.fits` files; `.csv` tables identical). All use cylinders.
    - **W2246, read only** (`W2246/annulus_fit_fwhm.py`; r_ap = 0.2842″ and r_ann_in = 0.5684″ at 5.4 µm, centred at 8.0 µm):
      - The cone is 1.00 FWHM and the annulus starts at 2 FWHM in every band: 0.27–0.30″ and 0.54–0.59″ in ch1-short, up to 0.91–1.05″ and 1.82–2.11″ in ch4-long.
      - The annulus fits all 12 bands in every plane with data, with at least 213 valid pixels (ch4-long; 252–687 in the others).
      - Every band would also allow a multiple of 3 (the largest tested).
    - *(Approved 2026-11-23 with its three choices; the synthetic cubes under `tests/M5/fwhm/` deleted, my request.)*
  - **W2246 extracted with the one-FWHM cone and a local background** (2026-11-23, my request; see "Decisions"). Work folder: `tests/M5/` (`extract_W2246.py`, `params/W2246_MIRI_r0.2842as_bkg_params.txt`, `W2246/bkg_extraction_check.py`, `W2246/step3_compare.py`); extraction in `extractions/W2246_MIRI_c1003_bkg/`.
    - **Setup:**
      - the 12 MAST `c1003` cubes (pipeline 3.0.0, master background subtracted), `dev` @ `a9cef3e`;
      - CRETA's centring at 8.0 µm (ch2-short) from M3's position. It worked: 341.53148°, −5.44300°, 0.138″ W of M3's position;
      - `point_source = True`, r_ap = 0.2842″ at 5.4 µm (one FWHM at every wavelength);
      - background on, r_ann_in = 0.5684″ (two FWHM), out to the field's edge;
      - no aperture correction; `stitch_band = ch2-short`.
    - **Background removed** (median per band, MJy/sr):

      | ch1-short | ch1-medium | ch1-long | ch2-short | ch2-medium | ch2-long |
      |---|---|---|---|---|---|
      | −2.77 | −0.77 | −6.35 | +2.12 | +2.06 | +1.94 |

      | ch3-short | ch3-medium | ch3-long | ch4-short | ch4-medium | ch4-long |
      |---|---|---|---|---|---|
      | +1.32 | +2.46 | +2.30 | +0.39 | +6.17 | −48.4 |

    - **NaN planes:** only ch4-long's 12 empty planes (28.633–28.699 µm). Every other plane has at least 50 annulus pixels.
    - **CRETA's overlap ratios** (next / this, over the overlap), with their S/N from the scatter of the overlap's channels (the S/N from CRETA's `Err` is 2–6× higher):

      | Overlap | Ratio | S/N |
      |---|---|---|
      | ch1-short → ch1-medium | 1.654 | 7.3 |
      | ch1-medium → ch1-long | 1.050 | 23 |
      | ch1-long → ch2-short | 0.918 | 58 |
      | ch2-short → ch2-medium | 0.991 | 116 |
      | ch2-medium → ch2-long | 0.973 | 131 |
      | ch2-long → ch3-short | 0.959 | 209 |
      | ch3-short → ch3-medium | 0.969 | 214 |
      | ch3-medium → ch3-long | 1.001 | 263 |
      | ch3-long → ch4-short | 0.961 | 298 |
      | ch4-short → ch4-medium | 1.019 | 191 |
      | ch4-medium → ch4-long | 0.990 | 53 |

      - All positive, all with S/N ≥ 3, so the stitched spectrum is used.
    - **Stitched bands:** no band's median is negative. The share of negative channels is 24% in ch1-short (median +0.018 mJy), 4% in ch1-medium and 3% in ch4-long; 0 elsewhere.
    - **ch4-long beyond 27 µm is now positive:** median 16.3, 22.4, 14.7 and 23.8 mJy (unstitched) at 27–27.5, 27.5–28, 28–28.5 and 28.5–28.7 µm. The annulus removes −67, −277, −825 and −316 MJy/sr of leftover background there.
    - **Step 3, shape against M3's `W2246_SingleExt_r0.5as.fits`:** both stitched spectra are divided by their median in ch2-short; per band, the median of new / M3:

      | Band | New / M3 |
      |---|---|
      | ch1-short | 0.53 (too noisy) |
      | ch1-medium | 0.79 |
      | ch1-long | 0.81 |
      | ch2-short | 0.97 |
      | ch2-medium | 1.03 |
      | ch2-long | 1.00 |
      | ch3-short | 1.06 |
      | ch3-medium | 1.10 |
      | ch3-long | 1.12 |
      | ch4-short | 1.17 |
      | ch4-medium | 1.23 |
      | ch4-long | 1.16 |

      - So the new spectrum rises by up to 23% relative to M3's from ch3 on, and falls by about 20% in ch1.
      - M3's spectrum differs in its cone (0.5″ at 5.4 µm, growing with λ: 1.8–2.5 FWHM), the background (none subtracted), the cubes (another reduction) and its stitching. Not separated.
      - *(Not pursued, my decision 2026-11-23: this extraction supersedes M3's spectrum.)*
    - **Step 3, photometry** (W2246.txt, width 0; the stitched spectrum interpolated in log λ, as CAFE does for width 0):
      - 12.0 µm (ch3-short): measured 2.50 ± 0.20 mJy, spectrum 2.03 mJy, ratio 0.81 ± 0.07.
      - 22.0 µm (ch4-medium): measured 15.9 ± 1.6 mJy, spectrum 11.05 mJy, ratio 0.70 ± 0.07.
      - Expected without aperture correction: 0.94 for a Gaussian PSF (6.25% outside a one-FWHM cone), 0.83 for an Airy pattern (17%).
      - The annulus at 2 FWHM also removes the wings' light there. The absolute level is set by ch2-short's cone, the stitching reference.
      - The points are approximate: single wavelengths, without WISE's response curves.
      - **W4's red-source issue** (logged 2026-11-23, checked against the WISE All-Sky Explanatory Supplement, sec. IV.4.h, last updated 2017; see "Biases"):
        - For steeply rising spectra (F_ν ∝ ν^−α with α ≥ 1), the catalogued W4 flux is about 8–10% too high. W2246's spectrum has α = 2.1 over 20–24 µm.
        - With W4 decreased by 8% or 10%, the 22 µm ratio becomes 0.76 ± 0.08 or 0.77 ± 0.08. The spectrum at 22.8 µm, Brown et al. 2014's effective wavelength, gives 0.76 ± 0.08 against W4 as catalogued.
        - So both points are about 0.8 (0.81 ± 0.07 and 0.76–0.77 ± 0.08), consistent with one aperture-correction factor.
        - To be handled with M5's photometry conventions (see the open item at the top of M5).
        - *(2026-11-23: this item and the "one aperture-correction factor" rest on the inference that W2246.txt's 12.0 and 22.0 µm points are WISE W3 and W4. The file's bands and origin are unknown. W2246 is fitted on its spectrum alone, with no W4 correction; see "Decisions".)*
    - **ch1-short is unreliable for W2246 and is left out of its fits** (my decision, 2026-11-23). It is barely detected (median 0.011 mJy unstitched, 0.018 mJy stitched), 24% of its channels are negative, and its overlap ratio of 1.65 (the lowest S/N, 7.3) sets its stitching.
    - No fit of W2246 until its PSF arrives (my decision, 2026-11-23).
    - Cost (information only): the extraction took 26 s.
  - **CRETA's fixed-width background ring for point sources, commit `2383c67`** (2026-11-23, my request; waiting for my review; see "Awaiting my OK").
    - **The change:** for a point source, the ring is `ann_width` wide at every wavelength.
      - Its inner edge is `r_ann_in` at `lambda_ap`, scaled like the cone.
      - Where the ring would leave the largest circle around the source inside the field, it moves inward just enough to fit, but never inside the cone. A plane with no room outside the cone gets a NaN background and flux.
      - CRETA prints, per band, how many planes are pulled in and how many have no room.
      - `ann_width` must be > 0 (a `ValueError` otherwise), and `MIN_ANNULUS_PIXELS` is 20. Extended sources are unchanged.
    - **Synthetic test** (`tests/M5/annulus/test_point_source_annulus.py`, rewritten):
      - Setup: four MIRI-like bands of 41×41 pixels with rectangular fields (ch1 at 0.13″ per pixel, a ch4-short-like band at 0.5″); a 1 mJy Gaussian with Law et al.'s FWHM; a flat background of +3, −3 or 0 MJy/sr × λ/5.4 µm, with and without noise of 1 MJy/sr per pixel; a cone of 0.3″, `r_ann_in` 0.6″ and `ann_width` 0.2″ at 5.4 µm.
      - The four bands cover the four cases: the ring nominal (ch1-short), pulled in (96 planes of ch1-medium), pulled in or without room (159 and 122 planes of ch1-long), and under 20 pixels (all of ch4-short).
      - **Result: all checks pass.**
        - The ring's edges in every plane match the rule computed from the rectangles to 10⁻¹⁰ px.
        - `ann_width = 0` stops with the `ValueError`.
        - The NaN planes are exactly the no-room and under-20 ones, and CRETA's counts per band are as expected.
        - The background is recovered to 10⁻¹⁵ MJy/sr, and flux(B0) = flux(0) to 10⁻¹⁵. Where the ring is nominal, the flux with background on equals that with it off to 1.3×10⁻⁷.
        - With noise, where the ring is nominal: the background error has mean +0.06 ± 0.05 and rms 0.92 × 1.25σ/√N; the flux error has mean +0.09 ± 0.10 µJy.
      - **Information:** where the ring is pulled in to just outside the cone (ch1-long), the Gaussian's wings in it lower the flux by 0.7–1.5%, and with noise the background comes out 1.5σ high, because the median of steep wings plus noise is not the median of the wings plus that of the noise. A ring pulled in near the cone costs accuracy.
      - **Before** (`1c93f9a`'s CRETA): 17 checks fail. The ring ignores `ann_width` and reaches the field's edge, the minimum is 50, and `ann_width = 0` raises no error.
    - **Regression:** NGC7469's M3 single extraction (no background; extended-source background), 3×3 grid and M5 NIRSpec + MIRI extraction are byte-identical before (`1c93f9a`) and after.
    - **W2246, read only** (`W2246/ring_fit.py`; cone 0.4263″ = 1.5 FWHM, `r_ann_in` 0.8526″ = 3 FWHM, `ann_width` 1.0″, centred at 8.0 µm):

      | Band | Cone | Ring inner → outer | Pulled in | Fewest pixels |
      |---|---|---|---|---|
      | ch1-short | 0.402–0.443″ | 0.803–0.886 → 1.803–1.886″ | no | 490 |
      | ch1-medium | 0.439–0.487″ | 0.878–0.959 → 1.878–1.959″ | 197 planes (6.47–6.63 µm) | 513 |
      | ch1-long | 0.482–0.538″ | 0.965–0.974 → 1.965–1.974″ | 1,285 planes (6.62–7.65 µm) | 537 |
      | ch2-short | 0.531–0.593″ | 1.062–1.186 → 2.062–2.186″ | no | 339 |
      | ch2-medium | 0.588–0.660″ | 1.176–1.321 → 2.176–2.321″ | no | 363 |
      | ch2-long | 0.655–0.738″ | 1.309–1.413 → 2.309–2.413″ | 490 planes (11.06–11.70 µm) | 388 |
      | ch3-short | 0.731–0.826″ | 1.462–1.652 → 2.462–2.652″ | no | 306 |
      | ch3-medium | 0.819–0.930″ | 1.598 → 2.598″ | all 892 planes | 320 |
      | ch3-long | 0.922–1.049″ | 1.724 → 2.724″ | all 1,028 planes | 337 |
      | ch4-short | 1.035–1.196″ | 2.071–2.392 → 3.071–3.392″ | no | 130 |
      | ch4-medium | 1.183–1.371″ | 2.367–2.646 → 3.367–3.646″ | 162 planes (23.51–24.48 µm) | 144 |
      | ch4-long | 1.367–1.580″ | 2.596 → 3.596″ | all 717 planes | 151 |

      - The cone is 1.50 FWHM in every band.
      - Where the ring is pulled in, its inner edge stays at least 2.47 FWHM out (ch3-long and ch4-long at their red ends).
      - No plane lacks room. The only NaN planes are ch4-long's 12 empty ones (28.633–28.699 µm).
    - *(Approved 2026-11-23; see "Decisions".)*
  - **W2246 re-extracted with the 1.5-FWHM cone and the 1″ ring** (2026-11-23, my request, step 1; see "Decisions"). *(Stopped before using the stitched spectrum: the ch1-short → ch1-medium ratio has S/N 1.8. Step 2, the fit setup, not done.)* Extraction in `extractions/W2246_MIRI_c1003_ring/`; parameters `tests/M5/params/W2246_MIRI_r0.4263as_ring_params.txt`.
    - **Setup:**
      - the 12 `c1003` cubes, `dev` @ `3b64c30`; CRETA's centring at 8.0 µm (341.53148°, −5.44300°, as before);
      - r_ap = 0.4263″ and r_ann_in = 0.8526″ at 5.4 µm, `ann_width` = 1.0″, background on;
      - no aperture correction; `stitch_band = ch2-short`.
      - The ring is pulled in where `W2246/ring_fit.py` said: 197 planes of ch1-medium, 1,285 of ch1-long, 490 of ch2-long, 162 of ch4-medium, and all of ch3-medium, ch3-long and ch4-long. No plane lacks room.
    - **Background removed** (median per band, MJy/sr):

      | ch1-short | ch1-medium | ch1-long | ch2-short | ch2-medium | ch2-long |
      |---|---|---|---|---|---|
      | −2.74 | −0.76 | −6.40 | +2.00 | +1.98 | +1.86 |

      | ch3-short | ch3-medium | ch3-long | ch4-short | ch4-medium | ch4-long |
      |---|---|---|---|---|---|
      | +1.16 | +2.37 | +2.32 | +0.08 | +3.30 | −52.7 |

    - **NaN planes:** only ch4-long's 12 empty planes.
    - **Overlap ratios** (next / this; S/N from the overlap's channel scatter, with CRETA's `Err` in brackets):

      | Overlap | Ratio | S/N |
      |---|---|---|
      | **ch1-short → ch1-medium** | **6.31** | **1.8 (4.6)** |
      | ch1-medium → ch1-long | 1.054 | 16 |
      | ch1-long → ch2-short | 0.924 | 46 |
      | ch2-short → ch2-medium | 0.948 | 94 |
      | ch2-medium → ch2-long | 0.949 | 107 |
      | ch2-long → ch3-short | 0.997 | 185 |
      | ch3-short → ch3-medium | 0.967 | 204 |
      | ch3-medium → ch3-long | 0.999 | 236 |
      | ch3-long → ch4-short | 1.043 | 242 |
      | ch4-short → ch4-medium | 1.018 | 146 |
      | ch4-medium → ch4-long | 1.026 | 36 |

      - ch1-short's overlap median is 0.0062 mJy (0.0157 with the one-FWHM cone).
      - That ratio enters only ch1-short's own stitching factor (6.15). Every other band's factor (0.92–1.15) matches the product of the other ratios and does not use it (`stitch_factors_W2246_c1003_ring.txt`). ch1-short is already left out of W2246's fits.
    - **Stitched bands:** no band's median is negative. Negative channels: 35% in ch1-short, 5% in ch1-medium, 4% in ch4-long, 0 elsewhere.
    - ch4-long beyond 27 µm is positive (21–50 mJy unstitched per 0.5 µm).
    - *(2026-11-23: going on with the stitched spectrum without ch1-short, my decision; see "Decisions".)*
  - **W2246's spectrum-only fit: the setup, no fit** (2026-11-23, my request, step 2; `tests/M5/W2246/fit_setup.py`, log `logs/fit_setup_W2246.txt`; my choices are under "Awaiting my OK").
    - **Spectrum:** `data/W2246/spectra/W2246_MIRI_r0.4263as_ring_noch1s_cube.fits`.
      - It is the ring extraction's `_cube.fits` with ch1-short's 1,050 channels removed from every extension (`W2246/drop_band.py`). The stitched fluxes of the other bands are identical; only NAXIS1 changes.
      - CAFE reads it as `fit_spec` does (`read_spec` with its default trim, which keeps the shorter band in each overlap; DQ used; then `mask_spec`): 9,907 channels, 9,895 after masking.
      - Rest range 1.0106–5.1111 µm at z = 4.601: ch1-medium 1.011–1.184 … ch4-long 4.371–5.111 µm (observed 5.660–28.627 µm).
    - **z (for me to choose):**
      - 4.601 from [CII] (Díaz-Santos et al. 2016); 4.593 from UV and optical lines (quoted by Fan et al. 2018).
      - M3 used 4.6. My pre-sync notebook's active line is 4.507, with 4.601 commented out.
      - The parameter count and the range do not depend on it: 17 free at 4.593, 4.6 and 4.601; the range shifts by < 0.01 µm.
    - **Inpars:** my `inpars_jwst_miri+phot_W2246.ini` (pre-sync, read only).
      - Its five tables: `lines.atomic_W2246.txt`, `lines.molecular_W2246.txt`, `lines.H_recombination_W2246.txt`, `pah_template_W2246.txt` and `opacity/gauss_opacity_W2246.ecsv`.
      - They reach `dev` through `tests/M5/W2246/cafe_dir_W2246/` (`W2246/make_cafe_dir.py`: links to every current `dev` table plus the five).
      - **In the rest range, every line and opacity feature in them has MASK = 1, so CAFE fits none.** That is the 1 atomic line ([O I] 1.317 µm), all 72 H₂ lines, all 68 H recombination lines (Paβ, Paα, Brα among them), and the 5 ice and CO features. The only feature left is the 3.3 µm PAH (`d0_PAH33_32890`).
    - **Against the shipped `inpars_jwst_miri_AGN.ini`:**
      - Sources: COO and WRM are heated by the AGN SED (shipped: ISRF); HOT by the AGN in both.
      - T ranges:

        | Parameter | W2246 | Shipped |
        |---|---|---|
        | CIR_TMP | 3.74, free in [0, 5] | fixed |
        | CLD | on: FLX 0.1 free in [0, 20], TMP 10 free in [5, 25] | off |
        | COO_TMP | [25, 100] | [3, 50] |
        | WRM_TMP | 150 in [100, 300] | 135 in [50, 200] |
        | HOT_TMP | 500 in [300, 1027.2] | 500 in [200, 1750] |

      - Optical depths:

        | Parameter | W2246 | Shipped |
        |---|---|---|
        | COO_TAU | 1, fixed | 0.1, free |
        | WRM_TAU | 4 | 0.1 |
        | HOT_TAU | 1 | 0.1 |
        | STB_TAU | 1 | 0.1 |
        | DSK_TAU | 0.1, free in [0, 2] | 0.1, free in [0, 0.5] |

      - FLX starts: WRM 0.1 (0.3), HOT 0.5 (0.3), STB 0.01 (0.2), DSK 0.001 (0.15).
      - Lines: `FitWave0_LIN_B`, `FitGamma_LIN_B` and `FitVgrad` are False (shipped True), `EPSVgrad` is 200 (100). With no lines fitted, these have no effect.
    - **Free:** 17 of 46 parameters.
      - The continuum's 16: CIR_TMP, CLD_FLX, CLD_TMP, COO_FLX, COO_TMP, WRM_FLX, WRM_TMP, WRM_TAU, HOT_FLX, HOT_TMP, HOT_TAU, STB_FLX, STB_TAU, STB_010, DSK_FLX and DSK_TAU.
      - Plus the 3.3 µm PAH's peak.
      - Fixed: CIR_FLX = 0 (CIR off), STR off, COO_TAU = 1, PAH_FLX = 1, and PAH_TAU = WRM_TAU (an expression).
    - **What the range can and cannot constrain** (CAFE's model at the start, and each far-IR component at its upper bounds with no extinction):
      - At the start, HOT is 96% of the model in the range (86% at the blue end, 81% at the red end); DSK 1.4% (9% at the blue end); STB 1.2% (4.5%); WRM 18% at the red end.
      - **CIR:** at most 3×10⁻³⁶ of the data, and its FLX is fixed at 0, so its free TMP has no effect.
      - **CLD:** at most 5×10⁻⁸ of the data. Not constrained.
      - **COO:** at most 1.05× the data, only at 5.05 µm and at FLX 2, 100 K; negligible at its 40 K start. Only weakly constrained, at the red end.
      - **WRM** (AGN-heated, up to 300 K): up to 197× the data at 1.03 µm at FLX 2, 300 K, so it overlaps HOT.
      - **Optical depths:** WRM_TAU also sets PAH_TAU. HOT_TAU, STB_TAU and DSK_TAU act only through the extinction curve below 5.1 µm, against the temperatures and the stellar mix.
      - **The FLX scale** of CIR, CLD, COO, WRM, DSK and PAH: their reference wavelengths (450, 70, 24, 14, 10 and 6.22 µm) lie beyond the data. CAFE's `flux0` then takes the last 20 channels (9.447 mJy at about 5.1 µm), so their [0, 2] bounds are relative to that. HOT's `flux0` at 3.5 µm is 1.760 mJy, STB's at 2 µm 0.330 mJy.
    - **Opt file:** `dev`'s `default_opt.cafe`, as in the M5 NGC7469 fits and my notebook. `FitPhot` False, ftol 1e-5, `SPEC_UNC_FLOOR` 0.01, `FIT_CHK` True, `MAX_LOOPS` 5, `ExtOrAbs` 'EXT', `Draine_Or_OHMc` 'OHMc'; reference wavelengths as above.
    - **Channel-to-channel scatter against CRETA's quoted errors** (rest-frame spectrum as read; scatter = 1.4826 MAD of successive differences / √2):

      | Band | Median S/N | Scatter / quoted error | With the 1% floor |
      |---|---|---|---|
      | ch1-medium | 7 | 1.96 | 1.95 |
      | ch1-long | 13 | 1.89 | 1.87 |
      | ch2-short | 39 | 1.92 | 1.77 |
      | ch2-medium | 79 | 2.31 | 1.78 |
      | ch2-long | 107 | 2.16 | 1.47 |
      | ch3-short | 287 | 3.09 | 0.98 |
      | ch3-medium | 320 | 3.58 | 1.05 |
      | ch3-long | 291 | 3.18 | 1.03 |
      | ch4-short | 206 | 3.48 | 1.51 |
      | ch4-medium | 122 | 6.03 | 3.80 |
      | ch4-long | 35 | 3.59 | 3.37 |

      - So the quoted errors are 2–6× too small. With the 1% floor (σ_fit = √(σ² + (0.01 F)²)), ch3 matches the scatter, but ch1–ch2 stay 1.5–2× low and ch4-medium and ch4-long 3.4–3.8× low.
      - If adjacent channels are correlated, the successive-difference scatter underestimates the noise, so these ratios are lower limits.
  - **W2246's first spectrum-only fits** (2026-11-23, run set `w2246`, j = 0, 1, 2; W2246's own setup, see "Decisions"; `m5_fit.py`, `w2246_summary.py`, log `logs/w2246_summary.txt`).
    - **Setup:**
      - the ring extraction without ch1-short (`data/W2246/spectra/W2246_MIRI_r0.4263as_ring_noch1s_cube.fits`), z = 4.601, DQ used, flux_scale = 1 + j × 1e-7; 9,895 channels;
      - inpars `params/inpars_jwst_miri_W2246_M5_spec.ini`, the copy of my file with 10 changes (diff in `logs/inpars_W2246_M5_spec_diff.txt`), through `W2246/cafe_dir_W2246/`;
      - the shipped `default_opt.cafe`, with CRETA's errors and its 1% floor; no photometry; `dev` @ `1bd172a`.
      - 12 free parameters: WRM_FLX, WRM_TMP, WRM_TAU, HOT_FLX, HOT_TMP, HOT_TAU, STB_FLX, STB_TAU, STB_010, DSK_FLX and DSK_TAU, plus the 3.3 µm PAH's peak; PAH_TAU = WRM_TAU.
    - **χ² (floored):**

      | j | χ² | χ²/N | Δχ² to the best | Stop |
      |---|---|---|---|---|
      | 2 | 109,441.68 | 11.060 | 0 | ftol + xtol |
      | 1 | 109,453.44 | 11.062 | 11.8 | ftol + xtol |
      | 0 | 109,734.02 | 11.090 | 292.3 | xtol |

      - Only 1 of 3 is within Δχ² < 1 of the best; the spread is 292.
      - One minimize call each, 925–1,069 evaluations, 25 s per fit.
    - **Continuum** (j = 2 / j = 1 / j = 0; value ± lmfit's error):

      | Parameter | j = 2 | j = 1 | j = 0 |
      |---|---|---|---|
      | HOT_TMP | 1303 ± 185 K | 1291 ± 161 K | 1063 ± 79 K |
      | HOT_FLX | 0.723 ± 0.035 | 0.725 ± 0.031 | 0.763 ± 0.018 |
      | HOT_TAU | 2.82 ± 0.12 | 2.81 ± 0.10 | 2.67 ± 0.05 |
      | WRM_TMP | 264 ± 174 K | 248 ± 169 K | 225 ± 170 K |
      | WRM_FLX | 0.61 ± 0.55 | 0.67 ± 0.62 | 0.78 ± 0.90 |
      | WRM_TAU (= PAH_TAU) | 7.4 ± 3.3 | 7.1 ± 3.4 | 7.1 ± 4.2 |
      | DSK_FLX | 0.0062 ± 0.0055 | 0.0059 ± 0.0039 | 0.0023 ± 0.0007 |
      | DSK_TAU | 0.19 ± 0.34 | 0.18 ± 0.62 (fixed after the fit) | 0.0017 (fixed after the fit) |

      - **STB_FLX ends at 0** (its lower bound) in all three, and is fixed after the fit. STB_TAU and STB_010 are then undetermined (errors 10⁴–10⁵).
    - **Share of the continuum** (best fit, j = 2; ∫F_ν dν):

      | Window (µm rest) | HOT | WRM | DSK | STB |
      |---|---|---|---|---|
      | 1.0–1.5 | 0.56 | 0 | 0.44 | 0 |
      | 1.5–2.0 | 0.89 | 0.001 | 0.11 | 0 |
      | 2.0–2.5 | 0.94 | 0.011 | 0.047 | 0 |
      | 2.5–3.0 | 0.92 | 0.054 | 0.031 | 0 |
      | 3.0–3.5 | 0.81 | 0.16 | 0.024 | 0 |
      | 3.5–4.0 | 0.65 | 0.34 | 0.019 | 0 |
      | 4.0–4.5 | 0.47 | 0.52 | 0.016 | 0 |
      | 4.5–5.12 | 0.32 | 0.67 | 0.012 | 0 |
      | whole range | 0.66 | 0.31 | 0.035 | 0 |

      - j = 0 and j = 1 give HOT 0.56–0.66 and DSK 0.34–0.44 at 1.0–1.5 µm.
    - **3.3 µm PAH:** its peak ends at 0 in all three fits and is fixed after the fit, so the PAH table is empty.
    - **χ²/N per band** (j = 2; j = 0 and 1 within 0.5, except ch3-short 4.31–4.84):

      | Band | χ²/N |
      |---|---|
      | ch1-medium | 15.7 |
      | ch1-long | 9.3 |
      | ch2-short | 11.4 |
      | ch2-medium | 10.6 |
      | ch2-long | 8.2 |
      | ch3-short | 4.8 |
      | ch3-medium | 3.5 |
      | ch3-long | 2.3 |
      | ch4-short | 25.7 |
      | ch4-medium | 16.7 |
      | ch4-long | 24.0 |
      | all | 11.06 |

  - **The three lines unmasked, before any fit** (2026-11-23, my request; `W2246/line_width_check.py`, log `logs/line_width_check_W2246.txt`). *(Stopped before fitting: the width bounds would stop a broad line.)*
    - **Setup:**
      - `params/inpars_jwst_miri_W2246_M5_spec_lines.ini` = the first copy with `hrecomb_input = 'lines.H_recombination_W2246_M5_3lines.txt'` and `FitGamma_LIN_N = True` (diff in `logs/inpars_W2246_M5_spec_lines_diff.txt`).
      - That table is a work-folder copy of my H table (`W2246/tables/`) with Paschen(5-3), Paschen(4-3) and Brackett(5-4) at MASK = 0; their DOUBLE is already 0. It is linked into `W2246/cafe_dir_W2246/` by `make_cafe_dir.py`.
    - **Width bounds** (FWHM), as `make_feat_pars` sets them for a single (narrow) component:
      - lower bound = the instrumental width / 1.05;
      - upper bound = max(1.05 × the instrumental width, `EPSGamma_LIN_N`). My file has `EPSGamma_LIN_N` = 400 km/s.

      | Line | Observed | Band | Width start | Bounds |
      |---|---|---|---|---|
      | Paβ | 7.181 µm | ch1-long | 89 km/s | 85–400 km/s |
      | Paα | 10.505 µm | ch2-long | 100 km/s | 95–400 km/s |
      | Brα | 22.697 µm | ch4-medium | 174 km/s | 165–400 km/s |

      - The centres are fixed at z = 4.601 (`FitWave0_LIN_N` False; `EPSWave0_LIN_N` 100 km/s if freed).
    - **Paα is dropped by `fit_spec`'s default** (`force_all_lines = False`): its starting amplitude at the instrumental width comes out ≤ 0. Only with `force_all` is it kept (16 → 18 free parameters).
    - **How broad they are, roughly:** a Gaussian plus a straight line fitted to the first run's residual (outside CAFE).
      - Paβ: FWHM 1,250 ± 210 km/s, centred at +13 km/s.
      - Paα: 750 ± 170 km/s, centred at −1,190 km/s.
      - Brα: 53 ± 3 km/s, narrower than the instrument, so that fit caught a spike, not the line.
      - Only Paβ's estimate is usable. It is already 3× the 400 km/s cap.
    - *(Replaced 2026-11-23 by my final line choice; see "Decisions" and the next bullet.)*
  - **W2246 with the final line choice: narrow and broad Paβ, Paα and Brα** (2026-11-23, run set `w2246lines`, j = 0, 1, 2; `m5_fit.py`, `w2246_summary.py`, `W2246/line_bounds.py`; logs `logs/w2246_summary.txt` (both runs side by side) and `logs/line_bounds_W2246.txt`).
    - **Setup:** as the first run, with `params/inpars_jwst_miri_W2246_M5_spec_lines.ini` and `fit_spec(force_all_lines=True)`; `dev` @ `6b9fe9e`.
      - The inpars copy differs from my file by the first copy's 10 changes plus: `hrecomb_input = 'lines.H_recombination_W2246_M5_3lines.txt'`, `FitWave0_LIN_B`, `FitGamma_LIN_N` and `FitGamma_LIN_B` True, `EPSWave0_LIN_B` 1500, `EPSGamma_LIN_B` 3000 (diff in `logs/inpars_W2246_M5_spec_lines_diff.txt`).
      - That table copy differs from my H table only by MASK 0 and DOUBLE 1 for Paschen(5-3), Paschen(4-3) and Brackett(5-4) (`logs/H_table_W2246_M5_3lines_diff.txt`).
      - 27 free parameters: the 12 before, plus each line's narrow width and peak, and broad centre, width and peak.
    - **Bounds** (km/s; CAFE sets the narrow and broad options separately, as asked):
      - Narrow: centre fixed at 0; FWHM from 89, 100 and 174 (Paβ, Paα, Brα: the instrumental width) within 85–400, 95–400 and 165–400.
      - Broad: centre free from −200 within −1,493 to +1,500 (CAFE puts the blue limit at λ₀/(1 + 1500/c)); FWHM from 3× the instrumental width (266, 300, 521) within 85–3,000, 95–3,000 and 165–3,000.
      - Peaks in [0, ∞). Paα's starting peak is the smallest positive one (`force_all`).
    - **χ² (floored):**
      - 108,487.41 (j = 2), 109,177.30 (j = 1), 109,266.38 (j = 0); χ²/N 10.96–11.04.
      - Only 1 of 3 within Δχ² < 1 of the best; spread 779, against 292 with the lines masked.
      - The best is 954 below the best with the lines masked. Each fit took 20 s.
    - **Continuum, best fits** (lines / lines masked):
      - HOT_TMP 793 ± 296 K / 1303 ± 185 K (704–801 / 1063–1303 over the fits); HOT_FLX 0.815 / 0.723; HOT_TAU 2.45 / 2.82.
      - WRM_TMP 215 / 264 K; WRM_FLX 0.86 (fixed after the fit) / 0.61; WRM_TAU 7.7 / 7.4.
      - DSK_FLX 0 (its lower bound, fixed after the fit) / 0.006; STB_FLX 0.012 / 0; STB_010 0 / 0.28.
    - **Share of the continuum, best fits** (lines / lines masked):
      - over 1.0–5.12 µm: HOT 0.73 / 0.66, WRM 0.26 / 0.31, DSK 0 / 0.035, STB 0.007 / 0;
      - at 1.0–1.5 µm: HOT 0.74 / 0.56, STB 0.26 / 0, DSK 0 / 0.44;
      - at 4.5–5.12 µm: HOT 0.39 / 0.32, WRM 0.61 / 0.67.
    - **Lines** (best fit, j = 2; the three fits agree unless noted; "fixed" = fixed by CAFE after the fit):

      | Component | Centre | FWHM | Flux (observed) | Ends at a bound |
      |---|---|---|---|---|
      | Paβ narrow | fixed | 90 km/s (lower bound 85) | 3×10⁻²² ± 7×10⁻²¹ W/m² | no; fixed after the fit |
      | Paβ broad | +20 ± 92 km/s | 1,206 ± 234 km/s (1,174–1,206 over the fits) | 9.7×10⁻²⁰ ± 1.1×10⁻¹⁹ W/m² | no |
      | Paα narrow | fixed | 400 km/s | 6×10⁻²¹ ± 2×10⁻²⁰ W/m² | width at its upper bound, all fits |
      | Paα broad | −1,493 km/s | 3,000 km/s | 2.3×10⁻¹⁹ ± 2.5×10⁻¹⁹ W/m² | centre at its lower and width at its upper bound, all fits |
      | Brα narrow | fixed | 400 km/s | 1×10⁻²⁰ ± 1.2×10⁻¹⁹ W/m² | width at its upper bound, all fits |
      | Brα broad | +1,500 km/s | 3,000 km/s | 1.0×10⁻¹⁸ ± 1.0×10⁻¹⁸ W/m² | centre and width at their upper bounds in j = 2; in j = 0 and 1, −373 and −406 ± ~470 km/s, FWHM 1,171 and 1,245 ± ~590 km/s, flux 2.9×10⁻¹⁹ ± 3.4×10⁻¹⁹ W/m² |

      - Every line flux has S/N ≤ 1.
    - **3.3 µm PAH:** its peak ends at 0, at its lower bound, and is fixed after the fit, in all six fits.
    - **χ²/N per band, best fits** (lines / lines masked):

      | Band | Lines | Lines masked |
      |---|---|---|
      | ch1-medium | 16.28 | 15.67 |
      | ch1-long | 8.62 | 9.30 |
      | ch2-short | 11.40 | 11.41 |
      | ch2-medium | 10.61 | 10.56 |
      | ch2-long | 7.57 | 8.21 |
      | ch3-short | 3.76 | 4.84 |
      | ch3-medium | 3.60 | 3.50 |
      | ch3-long | 2.26 | 2.33 |
      | ch4-short | 26.87 | 25.69 |
      | ch4-medium | 17.30 | 16.65 |
      | ch4-long | 23.53 | 24.00 |
      | all | 10.96 | 11.06 |
  - Cost (information only): each extraction 16–22 s, 0.7 GB; the mega-cube comparison about 23 min. Its 823 MB of scratch boxes (`full_pass/`) were deleted (my request).
- **W2246 test closed (2026-11-24, my decision).** It was a check of CAFE and CRETA, not a fit of W2246's science: no more W2246 runs. W2246's specific results above stay as they are. Its general findings:
  1. **CRETA's errors are too small in every band of both sources** (W2246 and NGC7469; added 2026-11-24, my decision). This sets CAFE's weights and inflates χ².
     - The scatter is 1.4826 × the MAD of successive differences / √2, per band, on the spectrum as `fit_spec` reads it.
     - It is about 2–6× CRETA's quoted errors in W2246 (1.9–6.0; `tests/M5/logs/fit_setup_W2246.txt`).
     - It is 5–40× in NGC7469's NIRSpec + MIRI extraction (`extractions/NGC7469_NIRSpec+MIRI_dqfix/`, median S/N 600–7,000; `tests/M5/scatter_check.py`, log `tests/M5/logs/scatter_check_NGC7469.txt`).
     - The 1% floor hides it in bright spectra: in NGC7469 the errors are ≥ the scatter in 13 of 15 bands (scatter / error 0.24–0.78; 1.01 in ch4-medium, 1.58 in ch4-long).
     - It does not hide it in faint ones: W2246 is still 1.5–3.8× short outside ch3, and about 1 in ch3 (median S/N about 300).
  2. **The fits again don't converge to one solution** (M4's known behaviour). In each of the three run sets (lines masked, narrow and broad lines, 1-D residual-fringe corrected), only 1 of 3 plain fits with rounding-level inputs is within Δχ² < 1 of the best; the spreads are 292, 779 and 277.
  3. **CAFE dims the lines by the PAH extinction, tied to WRM_TAU.** So line fluxes depend on a possibly poorly constrained continuum parameter. A design question, not a bug.
     - In `get_model_fluxes`, `fLIN = extPAH ×` the Gaussians.
     - Every shipped inpars file ties `PAH_TAU` to `WRM_TAU`, with `PAH_MIX = 1` (mixed).
     - `extPAH` is computed only when `PAH_FLX > 0`; `PAH_FLX` is fixed at 1 in every shipped file.
     - In W2246's fit with lines (WRM_TAU 7.7), the lines kept 0.063 (Paβ), 0.097 (Paα) and 0.26 (Brα) of their unextincted flux.
  4. **MAST's MRS cubes skip both the residual-fringe step (`S_RESFRI`) and adaptive trace modelling (`S_TRCMOD`).** This holds for all 12 `c1003` cubes, pipeline 3.0.0.
     - The pipeline's 1-D residual-fringe fitter removes fringes where they dominate the noise:
       - It used `fit_residual_fringes_1d`, jwst 3.0.0 defaults, env `cafe-jwst`.
       - ch2-long's 2.89 cm⁻¹ ripple drops from 1.1% to 0.2% of the continuum.
       - It found the dichroic fringe (0.35–0.48 cm⁻¹) in every ch3 and ch4 band.
       - With the correction, χ²/N fell most in ch4-medium (16.65 → 9.56) and ch3-long (2.33 → 1.69).
     - It fails in faint ch1: in ch1-long it fits 1.44 cm⁻¹ and leaves the 2.78 cm⁻¹ ripple (6.5% of the continuum) untouched.
     - See M8.

### M6 — Cube-fit performance and parallelisation
- **First item (logged 2026-11-19): R2's fits at the 50 K wall.** In the M4 baseline, 2 of 10 R2 plain fits ended at the 50 K wall between the COO and WRM ranges (WRM_TMP at its lower bound, COO_TMP 48.3 K), with χ² 2.6× the best (see "Biases", 2026-11-18). M6's cube fits will show how often this happens. The candidate remedy is the ratio constraint on the dust temperatures under "Later".
- **The M4 fit times are not a timing baseline** (logged 2026-11-19): the M4 fits ran while other jobs loaded the machine (during the baseline, load average 24–67 on 8 cores). M6 measures its own timing baseline.
- **Stage 3 cost** (logged 2026-11-19, read-only; `tests/M4/logs/stage3_cost.txt`; in model evaluations, since the machine was loaded): on R1, restarts cost 5.5–19.3× the plain fit's nfev (median 11.6), and after 20 restarts the chains were still 610 (median) above their end point; `x_scale='jac'` + restart cost 1.0–14.7× (median 2.6) and was within 0.05 of its end point after 20 restarts in 9 of 10. On R2 and S1c both cost 0.5–1.5× the plain fit. *(Decided 2026-11-19: no restarts and no `x_scale` by default; their cost is revisited here, where spaxels start from their neighbours' fits.)*
- **At the start of M6, rerun the M4 baseline with the current code** (decided 2026-11-19): `init_feats` (`5e70c62`) now changes R1's line set and starting values.
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
- `inpars_jwst_NGC7469_NIRSpec+MIRI_reg.ini` (logged 2026-11-20): it cannot be loaded (see "Biases"). Bringing it to the current format needs my choices then (line lists, PAH and opacity tables, OPC/Vgrad settings). `read_inst`'s case-insensitive matching (option (i), chosen 2026-11-20 for this file) waits with it.
- The other items logged for the clean-up in this brief (e.g. keywords the parameter file overrides, the README's keyword tables, the line table's row order, G13).

### M8 — Point-source cubes prepared before CRETA *(added 2026-11-24; starts only after my approval)*
- Rebuild point-source cubes from the stage-2 cal files with `adaptive_trace_model`, apply the 1-D residual-fringe correction (Law & Clarke 2026, arXiv:2603.26916), and test it.
- **The PSF-based aperture correction is part of M8** (2026-11-24, my decision). Compute it with the same cone and the same background annulus as the data: MIRI's real PSF wings put some of the source's light in the annulus, so the PSF must lose the same annulus background (decided for W2246, 2026-11-23).
- Why (W2246 test, M5, finding 4):
  - MAST's MRS cubes skip both steps.
  - The 1-D fitter with its defaults fails in faint ch1.
- Needs:
  - the cal files, which my MAST downloads don't include (checked for W2246, 2026-11-24);
  - jwst ≥ 3.0.0 (env `cafe-jwst`). There, `adaptive_trace_model` is off by default and runs in calwebb_spec3 before cube_build; its oversampling factor is `oversample`.

### CRETA aperture-correction path (separate item, not a milestone)
- G10, G11 and G11's two related problems (see "GOALS bugs found after M2"): fixed and tested end to end together once CRETA's PSF cubes are found, not with stand-in PSFs.
- *(The W2246 to-do "when its PSF arrives, compute the aperture correction with the same cone and annulus" is closed (2026-11-24, my decision). The PSF-based aperture correction becomes part of M8 and won't wait for PSFs here.)*

### Later (do not start)
- Tests and CI.
- **A NIRSpec FWHM law for CRETA's point-source cones** (logged 2026-11-23; my choice to make).
  - Until then, NIRSpec cones scale with λ (FWHM ∝ λ), and a MIRI cube needs `lambda_ap` ≥ 4.9 µm (`2818075`).
  - With a NIRSpec law, any `lambda_ap` works, and the cone is continuous at the NIRSpec–MIRI join. Today, with λ_ap = 5.4 µm, it steps by 3% at 5.0 µm.
  - **Published laws** (read-only search, 2026-11-24, my request; λ in µm, FWHM in arcsec). No measured law like Law et al. 2023's for MIRI exists from STScI or the NIRSpec team: JDox, the pipeline docs, Jakobsen et al. 2022, and Böker et al. 2022 and 2023 give none.
    - **D'Eugenio et al. 2024** (Nature Astronomy 8, 1443; arXiv:2308.06317, Methods, Eqs. 2–4, Fig. 7; equations checked on the arXiv text):
      - Empirical: matching NIRCam images of two galaxies (GS-10578, GS-3073) to synthetic images from drizzled PRISM cubes (0.03″ spaxels).
      - Along the slices (PSF major axis): FWHM = 0.12 + 1.9 λ exp(−24.4/λ).
      - Across the slices: FWHM = 0.09 + 0.2 λ exp(−12.5/λ).
      - Eq. 2 is a star near the field's edge: 0.13 + 1.6 λ exp(−21.4/λ).
      - No uncertainties and no validity range. They note an unexplained drop between F210M and F277W, not modelled.
    - **Pascalau et al. 2026** (arXiv:2603.00232, §3.1, Eq. 1; checked on the arXiv text):
      - σ = 0.076 + 0.013 λ exp(−7.6/λ), the same form fitted to STPSF's PSF sizes. It is circular: the geometric mean of the along- and across-slice FWHM, which differ by < 10% at 4–5.3 µm. FWHM 0.22″ at 5.43 µm.
      - STPSF's NIRSpec IFU broadening is a fixed 0.05″ Gaussian σ that its own code calls approximate. So this curve is a model, not a measurement. Jones et al. 2026 (arXiv:2509.20455) found STPSF agrees with calibration stars, qualitatively.
    - **Measurements without a formula:** Jones et al. 2026 (calibration stars of PIDs 1219, 1222 and 1537); Marshall et al. 2025 (0.14″ at 3.35 µm, 0.18″ at 4.52 µm); Goold et al. 2026; Law et al. 2026 (arXiv:2603.26916, an unpublished low-order fit).
    - The pipeline has no NIRSpec formula. Its point-source radius against λ is a table in the CRDS `extract1d` reference file (not downloaded).
    - **What they imply:**
      - Both laws are flat below about 3 µm and rise towards 5 µm; neither is ∝ λ.
      - FWHM at 2 / 3 / 4 / 5 µm: D'Eugenio along the slices 0.120 / 0.122 / 0.137 / 0.192″, across 0.091 / 0.099 / 0.125 / 0.172″; Pascalau 0.180 / 0.182 / 0.197 / 0.212″.
      - So the two differ by about 1.8× at 2 µm.
      - CRETA's FWHM ∝ λ, anchored at 5 µm, would give about 2–3× smaller cones than either at 1–2 µm.
    - *(My choice before any code; see "Awaiting my OK".)*
- R1's two end states (M4 stage 3, logged 2026-11-18): A (HOT 665 K, STB ≈ 0) and B, 773 lower (HOT at its 200 K lower bound, STB_FLX 0.58, COO 16 K), whose net gain comes from MIRI channel 4C (24.4–28.8 µm observed; 39% of R1's χ²). Look at channel 4C's data and what drives B. R1 fitted without channel 4C stays here too (decided 2026-11-19).
- S1c with several noise seeds (M4 stage 3, logged 2026-11-18), to tell a bias in COO_TMP, COO_TAU and WRM from the noise of one realisation.
- A NIRSpec + MIRI spectrum (from M4, logged 2026-11-18), for NGC7469 also for the HOT–STB degeneracy (decided 2026-11-19). What the pre-sync folder holds (checked 2026-11-19, read-only):
  - `my_notebooks/input_data/NGC7469_NIRSpec+MIRI_reg1_04arcsec.dat` (May 2023), the only combined file:
    - 11,358 channels from 2.8245 to 28.1442 µm, with columns wavelength, flux and uncertainty and no header;
    - the flux is 2.9 mJy at 3 µm and 0.61 Jy at 27 µm; no NaN, no channel < 0, one gap at 3.94–4.14 µm (G395H's detector gap).
    - Its wavelengths are in the rest frame, so read it with z = 0 (confirmed 2026-11-19): × 1.0163 they give 2.8705 and 28.603 µm, the observed ends of my G395H and 2023 MIRI CRETA extractions. My `script/NIRSpec-MIRI_spec_script.py` (July 2023, path commented out) reads it with z = 0.0163, which would shift it twice (see "Biases").
    - The name says region 1 and 0.4″. Nothing in the folder records how it was extracted.
  - `CAFE/output/NGC7469_sum_sf_spec/NGC7469_sum_sf_spec_cafefit.asdf` (July 2023, a fit output; the same file is tracked in the repo): its `obsspec` holds a NIRSpec + MIRI spectrum, by its name the sum of the star-forming regions. It has 12,541 channels from 2.825 to 27.55 µm and fluxes of 0.046–5.6 Jy. The source `.dat` it was fitted from is not in the folder; the notebook that read it points to another person's disk.
  - Separate CRETA single extractions, never combined:
    - G395H only (2.86–5.28 µm): r = 0.05, 0.5, 0.564, 1.0 and 1.5″ (`my_notebooks/extractions/`, December 2023 to January 2024);
    - MIRI only: r = 0.15–0.3″ (May 2024), and 0.35, 0.9, 1.2 and 1.5″ (`my_notebooks/input_data/CYGNUS_JWST/`, 2024–2025). R1 is a 1.5″ MIRI extraction.
    - Only three have a parameter file, which records the centre. The r = 0.564″ G395H and 0.3″ MIRI extractions are 0.025″ apart; the 0.25″ MIRI one is 1.3″ from both. The centres of the 1.5″ ones are not recorded.
- A ratio constraint on the dust temperatures, like Onion's (`HOT_WRM`, `WRM_COO`), to keep the components in order (logged 2026-11-18; for now the order comes from non-overlapping T ranges in the inpars files). It is the candidate remedy for R2's fits at the 50 K wall (M6, first item; logged 2026-11-19).
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
- **G15: `mask_spec` drops every channel with flux < 0** (logged 2026-11-19; first noted 2026-11-18, see "Biases"). Both branches (cube, `cafe_lib.py:91`; 1-D, `:104`, at `84dc4c1`) add `(data.fluxes < 0)` to the mask, which was never intended. In a faint spectrum or spaxel whose noise reaches below 0, the fit sees only the channels where the noise is positive and fits data biased high, more so the fainter the source. Same code in GOALS `master` (`ca10c84`, `cafe_lib.py:90`, `:103`). Failing case and test in `tests/mask_spec/` (work folder): at S/N 1 per channel `mask_spec` dropped 16% of the channels and the level fitted to the rest was 1.29× the truth (2.02× at S/N 0.5, 1.03× at S/N 2, 1.00 from S/N 5 up); three CAFE fits of a faint synthetic spectrum (S/N 1) gave a continuum 1.23–1.28× the truth before the fix and 0.95–0.99× after. *(Fixed on `dev` 2026-11-19, commit `3fd7e7e`, awaiting my approval. No PR to GOALS.)*
- **G16: `get_model_fluxes` stops with a `NameError` when `PAH_FLX = 0` and lines are in the fit** (logged 2026-11-24; found by reading, from the W2246 test's finding 3).
  - With the PAH component off, `extPAH` was set only when `comps` was True (`cafe_lib.py:872` at `c946aab`).
  - But `fLIN = extPAH ×` the Gaussians (`:1013`) needs it in both paths, so the fit's objective (`comps=False`) raised `UnboundLocalError`.
  - Same code in GOALS `master` (`ca10c84`, `cafe_lib.py:873`). No shipped file sets `PAH_FLX = 0`.
  - Fix: `extPAH = 1` in that branch for both paths, as the `comps=True` path already set it. So with PAH_FLX = 0 the lines are not dimmed, in both paths.
  - Failing case and test in `tests/pah_flx_zero/` (work folder), on a noiseless synthetic continuum with one line, PAH_FLX = 0:
    - before the fix: the `NameError`;
    - after it: the `comps=False` model equals the sum of the `comps=True` components exactly; fPAH = 0; extPAH = 1; fLIN equals the line's unextincted Gaussian exactly;
    - with `PAH_FLX = 1`, the model is bit-identical before and after.
  - *(Fixed on `dev` 2026-11-24, commit `6e7aee1`; approved 2026-11-25. No PR to GOALS.)*
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
`cafe-jwst` (2026-11-24, my request; for the JWST pipeline's own steps, e.g. the 1-D residual-fringe fitter; no environment file): jwst 3.0.0 from PyPI, with numpy 2.5.5, scipy 1.18.1, astropy 8.0.3.
```
~/miniforge3/bin/mamba create -y -q -n cafe-jwst -c conda-forge python=3.12 pip
~/miniforge3/envs/cafe-jwst/bin/python -m pip install jwst
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
cd /Users/tanio/pywork/cafe_work/scratch/m4_flux0 && env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/Users/tanio/Sync/pywork/CAFE ~/miniforge3/envs/cafe-dev/bin/python ../../tests/M4/test_flux0.py /Users/tanio/Sync/pywork/CAFE   # flux0 fix test (logs/test_flux0_{before,after}.txt)
cd /Users/tanio/pywork/cafe_work/tests/M4 && (for setup in R1 R2; do for j in 0 1 2 3 4 5 6 7 8 9; do echo "$setup $j"; done; done) | xargs -n 2 -P 3 ./run_baseline.sh   # M4 baseline: 20 plain fits, 3 at a time (out/<setup>/base_j<j>, logs/<setup>_base_j<j>.txt)
cd /Users/tanio/pywork/cafe_work/tests/M4 && env PYTHONDONTWRITEBYTECODE=1 ~/miniforge3/envs/cafe-dev/bin/python baseline_summary.py > logs/baseline_summary.txt && ./m4_report_baseline.sh   # baseline summary and report
cd /Users/tanio/pywork/cafe_work/tests/M4 && env PYTHONDONTWRITEBYTECODE=1 ~/miniforge3/envs/cafe-dev/bin/python stage3_cost.py > logs/stage3_cost.txt   # stage 3 cost (nfev, wall time) and restart-chain convergence, read-only (2026-11-19)
cd /Users/tanio/Sync/pywork/CAFE && mkdir -p /Users/tanio/pywork/cafe_work/cmp/dev_84dc4c1 && git archive 84dc4c1 CAFE | tar -x -C /Users/tanio/pywork/cafe_work/cmp/dev_84dc4c1   # before the mask_spec fix; cmp/dev_maskfix = the same with 3fd7e7e's cafe_lib.py
cd /Users/tanio/pywork/cafe_work/tests/mask_spec && env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/Users/tanio/Sync/pywork/CAFE ~/miniforge3/envs/cafe-dev/bin/python mask_level.py > logs/mask_level.txt   # G15: what mask_spec hands to the fit, S/N 0.5-10, before/after
cd /Users/tanio/Sync/pywork/CAFE && mkdir -p /Users/tanio/pywork/cafe_work/tests/pah_flx_zero/checkout_before && git archive c946aab CAFE | tar -x -C /Users/tanio/pywork/cafe_work/tests/pah_flx_zero/checkout_before   # G16: the code before the fix (deleted after the test; recreate to rerun)
cd /Users/tanio/pywork/cafe_work/tests/pah_flx_zero && for checkout in checkout_before /Users/tanio/Sync/pywork/CAFE; do label=$([ $checkout = checkout_before ] && echo before || echo after); env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=$checkout ~/miniforge3/envs/cafe-dev/bin/python -W ignore pah_flx_zero_test.py $(cd $checkout && pwd) $label > log_$label.txt 2>&1; done   # G16: before, the NameError (exit 1); after, the checks pass (exit 0); then compare model_pah_flx_1_before.npy and _after.npy (identical)
cd /Users/tanio/pywork/cafe_work/tests/M5 && env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/Users/tanio/Sync/pywork/CAFE ~/miniforge3/envs/cafe-dev/bin/python -W ignore scatter_check.py /Users/tanio/pywork/cafe_work/extractions/NGC7469_NIRSpec+MIRI_dqfix/ NGC7469_NIRSpec+MIRI_SingleExt_r1.5as_cube.fits 0.0163 > logs/scatter_check_NGC7469.txt   # M5: channel-to-channel scatter / CRETA's errors per band, read as fit_spec reads it
cd /Users/tanio/pywork/cafe_work/tests/mask_spec && ~/miniforge3/envs/cafe-dev/bin/python faint_make.py && xargs -P 3 -L 1 ./run_faint.sh < queue.txt && ~/miniforge3/envs/cafe-dev/bin/python faint_summary.py > logs/faint_summary.txt   # G15: faint CAFE fits before/after (out/<before|after>/seed<k>)
cd /Users/tanio/pywork/cafe_work/tests/init_feats && env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/Users/tanio/pywork/cafe_work/cmp/dev_maskfix ~/miniforge3/envs/cafe-dev/bin/python line_selection.py > logs/line_selection.txt   # init_feats line pre-selection test, 1000 draws, before/after
cd /Users/tanio/Sync/pywork/CAFE && W=/Users/tanio/pywork/cafe_work && git archive b8acb9c CAFE | tar -x -C $W/cmp/dev_b8acb9c && git archive 688a02a CAFE | tar -x -C $W/cmp/dev_flux0abs   # before/after the flux0 change (dev_flux0abs was made from b8acb9c plus the tested cafe_helper.py; identical to 688a02a's)
cd /Users/tanio/pywork/cafe_work/tests/flux0_abs && env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/Users/tanio/pywork/cafe_work/cmp/dev_flux0abs ~/miniforge3/envs/cafe-dev/bin/python faint_make.py /Users/tanio/pywork/cafe_work/cmp/dev_flux0abs > logs/faint_make.txt   # flux0: faint spectra with known components (inputs/)
cd /Users/tanio/pywork/cafe_work/tests/flux0_abs && env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/Users/tanio/pywork/cafe_work/cmp/dev_flux0abs ~/miniforge3/envs/cafe-dev/bin/python test_flux0_abs.py > logs/test_flux0_abs.txt   # flux0: bit-identity and flux0 > 0, no fit
cd /Users/tanio/pywork/cafe_work/tests/flux0_abs && xargs -P 3 -L 1 ./run_fit.sh < queue.txt && ~/miniforge3/envs/cafe-dev/bin/python faint_summary.py > logs/faint_summary.txt   # flux0: faint CAFE fits before/after (out/<before|after>/seed<k>)
cd /Users/tanio/pywork/cafe_work/tests/M5 && env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/Users/tanio/Sync/pywork/CAFE ~/miniforge3/envs/cafe-dev/bin/python centring_check.py > logs/centring_check.txt   # M5: nucleus position per cube with CRETA's centring (both NIRSpec WCS versions)
cd /Users/tanio/pywork/cafe_work/tests/M5 && env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/Users/tanio/Sync/pywork/CAFE ~/miniforge3/envs/cafe-dev/bin/python coverage_check.py > logs/coverage_check.txt && env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/Users/tanio/Sync/pywork/CAFE ~/miniforge3/envs/cafe-dev/bin/python offset_effect.py > logs/offset_effect.txt   # M5: 1.5" aperture coverage, and the flux change for the 0.19" offset
cd /Users/tanio/pywork/cafe_work && env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/Users/tanio/Sync/pywork/CAFE ~/miniforge3/envs/cafe-dev/bin/python tests/M5/extract.py > tests/M5/logs/extract.txt   # M5: CRETA NIRSpec+MIRI single extraction (params in tests/M5/params/; cubes symlinked in data/NGC7469/cubes_nirspec_wcsfix+miri/)
cd /Users/tanio/pywork/cafe_work/tests/M5 && ~/miniforge3/envs/cafe-dev/bin/python compare.py > logs/compare.txt   # M5: stitching ratios, new vs R1 per band, new vs reg1 shape, plot
cd /Users/tanio/pywork/cafe_work/tests/M5 && env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/Users/tanio/Sync/pywork/CAFE ~/miniforge3/envs/cafe-dev/bin/python resolution_check.py [ignore_DQ] > logs/resolution_check[_ignoreDQ].txt   # M5 step 2: channels the fit sees, resolving-power tables per band and line, HOT/STR/STB settings
cd /Users/tanio/pywork/cafe_work/tests/M5 && (for j in 0 1 2 3 4 5 6 7 8 9; do echo $j; done) | xargs -n 1 -P 3 ./run_fit.sh   # M5 step 2: 10 plain fits, 3 at a time (out/j<j>, logs/fit_j<j>.txt)
cd /Users/tanio/pywork/cafe_work/tests/M5 && env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/Users/tanio/Sync/pywork/CAFE ~/miniforge3/envs/cafe-dev/bin/python m5_summary.py > logs/m5_summary.txt   # M5 step 2: χ², HOT/STB/STR, 5–6 µm fractions vs R1 states A/B, χ² per band
cd /Users/tanio/pywork/cafe_work/tests/M5 && env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/Users/tanio/Sync/pywork/CAFE ~/miniforge3/envs/cafe-dev/bin/python dq_check.py > logs/dq_check.txt   # M5 fix (a): synthetic DQ planes (with PYTHONPATH at the pre-fix code: logs/dq_check_before.txt)
cd /Users/tanio/pywork/cafe_work && env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/Users/tanio/Sync/pywork/CAFE ~/miniforge3/envs/cafe-dev/bin/python tests/M5/extract.py NGC7469_NIRSpec+MIRI_dqfix > tests/M5/logs/extract_dqfix.txt   # M5 fix (a): the extraction redone
cd /Users/tanio/pywork/cafe_work/tests/M5 && env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/Users/tanio/Sync/pywork/CAFE ~/miniforge3/envs/cafe-dev/bin/python dq_compare.py > logs/dq_compare.txt   # M5 fix (a): extraction before vs after
cd /Users/tanio/pywork/cafe_work/tests/M5 && env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/Users/tanio/Sync/pywork/CAFE ~/miniforge3/envs/cafe-dev/bin/python resolving_power_test.py /Users/tanio/Sync/pywork/CAFE > logs/resolving_power_test.txt   # M5 fix (b): synthetic, NIRSpec+MIRI, R1, R2
cd /Users/tanio/pywork/cafe_work/tests/M5/out/fixb_j0 && env PYTHONHASHSEED=0 PYTHONDONTWRITEBYTECODE=1 MPLBACKEND=Agg OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 PYTHONPATH=/Users/tanio/Sync/pywork/CAFE ~/miniforge3/envs/cafe-dev/bin/python ../../m5_fit.py /Users/tanio/Sync/pywork/CAFE 0 > ../../logs/fit_fixb_j0.txt   # M5 fix (b): one plain fit, end to end
cd /Users/tanio/pywork/cafe_work/tests/M5 && env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/Users/tanio/Sync/pywork/CAFE ~/miniforge3/envs/cafe-dev/bin/python hot_tmp_check.py /Users/tanio/Sync/pywork/CAFE > logs/hot_tmp_check.txt   # M5: HOT_TMP, grain T_eq, sublimation, HOT's shape at the top
cd /Users/tanio/pywork/cafe_work/tests/M5 && env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/Users/tanio/Sync/pywork/CAFE ~/miniforge3/envs/cafe-dev/bin/python line_pedestal_check.py > logs/line_pedestal_check.txt   # M5: gauss_prof's constant tails on step 2's best fit
cd /Users/tanio/pywork/cafe_work/tests/M5 && env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/Users/tanio/Sync/pywork/CAFE MPLBACKEND=Agg ~/miniforge3/envs/cafe-dev/bin/python resolving_power_test.py /Users/tanio/Sync/pywork/CAFE > logs/resolving_power_test_kw.txt 2>&1   # M5: fix (b)'s test with bandname as a keyword; section 4: the old arguments give the old starting object
cd /Users/tanio/pywork/cafe_work/tests/M5 && env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/Users/tanio/Sync/pywork/CAFE MPLBACKEND=Agg ~/miniforge3/envs/cafe-dev/bin/python band_table_test.py /Users/tanio/Sync/pywork/CAFE > logs/band_table_test.txt 2>&1   # M5: SB_and_AGN's NIRSpec tables; the error for a band without a table (synthetic, shipped inpars, R1, R2)
cd /Users/tanio/pywork/cafe_work/tests/M5 && env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/Users/tanio/Sync/pywork/CAFE MPLBACKEND=Agg ~/miniforge3/envs/cafe-dev/bin/python carbon_sublimation_test.py /Users/tanio/Sync/pywork/CAFE > logs/carbon_sublimation_test.txt 2>&1   # M5: carbon at 1750 K: silicates and opacities unchanged, carbon kept to 1750 K, HOT's shape to the grid's top
cd /Users/tanio/pywork/cafe_work/tests/M5 && (for j in 0 1 2 3 4 5 6 7 8 9; do echo "$j hot1750"; done) | xargs -n 2 -P 3 ./run_fit.sh   # M5: 10 plain fits, HOT_TMP up to 1750 K, DQ-fixed extraction with the DQ used (out/hot1750_j<j>, logs/fit_hot1750_j<j>.txt)
cd /Users/tanio/pywork/cafe_work/tests/M5 && env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/Users/tanio/Sync/pywork/CAFE MPLBACKEND=Agg ~/miniforge3/envs/cafe-dev/bin/python hot1750_summary.py > logs/hot1750_summary.txt   # M5: hot1750 against step 2: χ², HOT/STB/STR/DSK, 5–6 µm fractions, χ² per band
cd /Users/tanio/pywork/cafe_work/tests/M5 && env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/Users/tanio/Sync/pywork/CAFE MPLBACKEND=Agg ~/miniforge3/envs/cafe-dev/bin/python inpars_tau_test.py /Users/tanio/Sync/pywork/CAFE > logs/inpars_tau_test.txt 2>&1   # M5: the seven shipped inpars after 9ffc4b7 against 29893bb (τ starts, DSK_TAU, HOT_TMP's bound; all else identical)
cd /Users/tanio/pywork/cafe_work/tests/M5 && (for j in 0 1 2 3 4 5 6 7 8 9; do echo "$j tau01"; done) | xargs -n 2 -P 3 ./run_fit.sh   # M5: 10 plain fits with the shipped inpars after 9ffc4b7 (work-folder copy), DQ-fixed extraction with the DQ used (out/tau01_j<j>, logs/fit_tau01_j<j>.txt)
cd /Users/tanio/pywork/cafe_work/tests/M5 && env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/Users/tanio/Sync/pywork/CAFE MPLBACKEND=Agg ~/miniforge3/envs/cafe-dev/bin/python tau01_summary.py > logs/tau01_summary.txt   # M5: tau01 against hot1750: χ², end states, every τ, HOT_TMP, 5–6 µm fractions, χ² per band
cd /Users/tanio/pywork/cafe_work/tests/M5 && env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/Users/tanio/Sync/pywork/CAFE MPLBACKEND=Agg ~/miniforge3/envs/cafe-dev/bin/python tau01_check.py > logs/tau01_check.txt 2>&1   # M5: both best fits' χ² rebuilt from m5_run.json; hot1750's best with DSK_TAU = 0 (no fit)
cd /Users/tanio/pywork/cafe_work/tests/M5 && (for j in 0 1 2; do echo "$j dskfree"; done) | xargs -n 2 -P 3 ./run_fit.sh   # M5: 3 plain fits with the tau01 copy and DSK_TAU = 0.1, True, 0., 0.5, DQ-fixed extraction with the DQ used (out/dskfree_j<j>, logs/fit_dskfree_j<j>.txt)
cd /Users/tanio/pywork/cafe_work/tests/M5 && env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/Users/tanio/Sync/pywork/CAFE MPLBACKEND=Agg ~/miniforge3/envs/cafe-dev/bin/python dskfree_summary.py > logs/dskfree_summary.txt   # M5: dskfree against hot1750 and tau01: χ², end states, every τ, bounds, HOT_TMP, COO_TMP, 5–6 µm fractions, χ² per band
cd /Users/tanio/pywork/cafe_work/tests/M5 && env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/Users/tanio/Sync/pywork/CAFE MPLBACKEND=Agg ~/miniforge3/envs/cafe-dev/bin/python inpars_dsktau_test.py /Users/tanio/Sync/pywork/CAFE > logs/inpars_dsktau_test.txt 2>&1   # M5: the seven shipped inpars after 72e9edd against 669ebe2 (DSK_TAU where DSK is free; all else identical)
cd /Users/tanio/pywork/cafe_work && env PYTHONDONTWRITEBYTECODE=1 MPLBACKEND=Agg PYTHONPATH=/Users/tanio/Sync/pywork/CAFE ~/miniforge3/envs/cafe-dev/bin/python tests/M5/extract_W2246.py > tests/M5/logs/extract_W2246.txt 2>&1   # M5: W2246 MIRI single extraction, stage3 cubes (linked in data/W2246/cubes_miri_stage3/; params tests/M5/params/W2246_MIRI_r0.5as_params.txt; out extractions/W2246_MIRI/)
cd /Users/tanio/pywork/cafe_work && env PYTHONDONTWRITEBYTECODE=1 MPLBACKEND=Agg PYTHONPATH=/Users/tanio/Sync/pywork/CAFE ~/miniforge3/envs/cafe-dev/bin/python tests/M5/extract_W2246.py cubes_miri_mast_c1003 W2246_MIRI_c1003 > tests/M5/logs/extract_W2246_c1003.txt 2>&1   # M5: the same with the 12 MAST c1003 cubes (linked in data/W2246/cubes_miri_mast_c1003/)
cd /Users/tanio/pywork/cafe_work/tests/M5/W2246 && env PYTHONDONTWRITEBYTECODE=1 MPLBACKEND=Agg PYTHONPATH=/Users/tanio/Sync/pywork/CAFE ~/miniforge3/envs/cafe-dev/bin/python -W ignore centring_diag.py > ../logs/centring_diag_W2246.txt   # M5: W2246's background in CRETA's centring box and CRETA's centring per cube, stage3; with the arguments cubes_miri_mast_c1003 "jw01712-c1003_t001_miri_{band}_s3d.fits" for c1003 (log ../logs/centring_diag_W2246_c1003.txt)
cd /Users/tanio/pywork/cafe_work/tests/M5/W2246 && for run in W2246_MIRI_c1003 W2246_MIRI; do env PYTHONDONTWRITEBYTECODE=1 ~/miniforge3/envs/cafe-dev/bin/python -W ignore stitch_diag.py /Users/tanio/pywork/cafe_work/extractions/$run/W2246_MIRI_SingleExt_r0.5as.fits; echo; done > ../logs/stitch_diag_W2246_c1003.txt 2>&1   # M5: per-band fluxes, overlap means and ratios, the last band per 0.5 µm
cd /Users/tanio/pywork/cafe_work/tests/M5/W2246 && env PYTHONDONTWRITEBYTECODE=1 ~/miniforge3/envs/cafe-dev/bin/python -W ignore mast_inventory.py > ../logs/mast_inventory_W2246.txt   # M5: W2246's MAST MIRI cubes: observation, target, band, pipeline, coordinates, background keywords, input exposures
cd /Users/tanio/pywork/cafe_work/tests/M5/W2246 && env PYTHONDONTWRITEBYTECODE=1 MPLBACKEND=Agg PYTHONPATH=/Users/tanio/Sync/pywork/CAFE ~/miniforge3/envs/cafe-dev/bin/python -W ignore annulus_check.py > ../logs/annulus_check_W2246_c1003.txt   # M5: CRETA's centring at 8.0 µm in c1003; whether one fixed annulus fits outside the 0.5″ cone and inside every cube's field
cd /Users/tanio/pywork/cafe_work/tests/M5/W2246 && env PYTHONDONTWRITEBYTECODE=1 ~/miniforge3/envs/cafe-dev/bin/python -W ignore x1d_check.py /Users/tanio/pywork/cafe_work/extractions/W2246_MIRI_c1003/W2246_MIRI_SingleExt_r0.5as.fits > ../logs/x1d_check_W2246_c1003.txt   # M5: the pipeline's c1003 x1d per band (source type, area, background column, flux) and against CRETA's c1003 extraction
cd /Users/tanio/pywork/cafe_work/tests/M5/W2246 && env PYTHONDONTWRITEBYTECODE=1 ~/miniforge3/envs/cafe-dev/bin/python -W ignore x1d_background_check.py > ../logs/x1d_background_check_W2246_c1003.txt   # M5: what the x1d BACKGROUND column holds; FLUX against the whole-cube sum
cd /Users/tanio/pywork/cafe_work/tests/M5/annulus && env PYTHONDONTWRITEBYTECODE=1 MPLBACKEND=Agg PYTHONPATH=/Users/tanio/Sync/pywork/CAFE ~/miniforge3/envs/cafe-dev/bin/python -W ignore test_point_source_annulus.py /Users/tanio/Sync/pywork/CAFE > ../logs/test_point_source_annulus.txt 2>&1   # M5: CRETA's per-plane point-source annulus on synthetic cubes with known truth; before the change: the same from annulus/before/ with the checkout cmp/annulus_before (git archive of 96dced6's CRETA)
cd /Users/tanio/pywork/cafe_work/tests/M3 && env PYTHONDONTWRITEBYTECODE=1 MPLBACKEND=Agg PYTHONPATH=/Users/tanio/Sync/pywork/CAFE ~/miniforge3/envs/cafe-dev/bin/python -W ignore stitch_run.py /Users/tanio/Sync/pywork/CAFE single single_all_bkgsub.txt annulus_after_single_all_bkgsub   # M5: annulus regression; likewise single_all.txt, and annulus_before_* with /Users/tanio/pywork/cafe_work/cmp/annulus_before
cd /Users/tanio/pywork/cafe_work/tests/M3/out/d6 && ~/miniforge3/envs/cafe-dev/bin/python -W ignore ../../../M5/annulus/regression_compare.py annulus_before_single_all_bkgsub annulus_after_single_all_bkgsub   # M5: before/after identical (.fits, _cube.fits, .csv table); likewise single_all (log ../../../M5/logs/annulus_regression_compare.txt)
cd /Users/tanio/pywork/cafe_work/tests/M5/W2246 && env PYTHONDONTWRITEBYTECODE=1 MPLBACKEND=Agg PYTHONPATH=/Users/tanio/Sync/pywork/CAFE ~/miniforge3/envs/cafe-dev/bin/python -W ignore annulus_fit_fwhm.py > ../logs/annulus_fit_fwhm_W2246_c1003.txt   # M5: W2246, one-FWHM cone, multiple 2: annulus pixels per band, largest multiple with >= 50 everywhere (run on 9017022, wavelength-scaled cone, r_ap 0.28; after 2818075 the same command gives the FWHM-scaled radii, log ../logs/annulus_fit_fwhm_W2246_c1003_fwhmscaled.txt, r_ap 0.2842 by default)
cd /Users/tanio/pywork/cafe_work/tests/M5/fwhm && env PYTHONDONTWRITEBYTECODE=1 MPLBACKEND=Agg PYTHONPATH=/Users/tanio/Sync/pywork/CAFE ~/miniforge3/envs/cafe-dev/bin/python -W ignore test_fwhm_cone.py /Users/tanio/Sync/pywork/CAFE > ../logs/test_fwhm_cone.txt 2>&1   # M5: FWHM-scaled cone on synthetic Gaussians (12 MRS bands + NIRSpec); before: the same from fwhm/before/ with the checkout /Users/tanio/pywork/cafe_work/cmp/fwhm_before (git archive of bebd239's CRETA), log ../logs/test_fwhm_cone_before.txt
cd /Users/tanio/pywork/cafe_work && tests/M5/fwhm/run_regressions.sh   # M5: NGC7469 M3 single (no background; extended background), 3x3 grid and M5 NIRSpec+MIRI extractions with bebd239's and the current CRETA (logs tests/M5/logs/fwhm_regression_*)
cd /Users/tanio/pywork/cafe_work && ~/miniforge3/envs/cafe-dev/bin/python -W ignore tests/M5/fwhm/compare_extractions.py extractions/NGC7469_NIRSpec+MIRI_fwhm_before extractions/NGC7469_NIRSpec+MIRI_fwhm_after   # M5: before/after identical; likewise tests/M3/out/d6/fwhm_{before,after}_{single_all,single_all_bkgsub,grid_all}; and cmp of every .fits (log tests/M5/logs/fwhm_regression_compare.txt)
cd /Users/tanio/pywork/cafe_work && env PYTHONDONTWRITEBYTECODE=1 MPLBACKEND=Agg PYTHONPATH=/Users/tanio/Sync/pywork/CAFE ~/miniforge3/envs/cafe-dev/bin/python tests/M5/extract_W2246.py cubes_miri_mast_c1003 W2246_MIRI_c1003_bkg W2246_MIRI_r0.2842as_bkg_params.txt > tests/M5/logs/extract_W2246_c1003_bkg.txt 2>&1   # M5: W2246, c1003 cubes, one-FWHM cone, two-FWHM annulus, centring at 8.0 um, stitching to ch2-short
cd /Users/tanio/pywork/cafe_work/tests/M5/W2246 && ~/miniforge3/envs/cafe-dev/bin/python -W ignore bkg_extraction_check.py /Users/tanio/pywork/cafe_work/extractions/W2246_MIRI_c1003_bkg/W2246_MIRI_SingleExt_r0.2842as.csv > ../logs/bkg_extraction_check_W2246_c1003.txt   # M5: background per band, NaN planes, overlap ratios with S/N, stitched signs, ch4-long beyond 27 um
cd /Users/tanio/pywork/cafe_work/tests/M5/W2246 && ~/miniforge3/envs/cafe-dev/bin/python -W ignore step3_compare.py /Users/tanio/pywork/cafe_work/extractions/W2246_MIRI_c1003_bkg/W2246_MIRI_SingleExt_r0.2842as.csv > ../logs/step3_compare_W2246_c1003.txt   # M5: step 3, shape against M3's spectrum (normalised in ch2-short), the 12.0 and 22.0 um points, and W4's red-source correction both ways
cd /Users/tanio/pywork/cafe_work/tests/M5/annulus && env PYTHONDONTWRITEBYTECODE=1 MPLBACKEND=Agg PYTHONPATH=/Users/tanio/Sync/pywork/CAFE ~/miniforge3/envs/cafe-dev/bin/python -W ignore test_point_source_annulus.py /Users/tanio/Sync/pywork/CAFE > ../logs/test_point_source_annulus.txt 2>&1   # M5: the fixed-width ring (2383c67) on synthetic cubes; before: the same from annulus/before_ring/ with the checkout /Users/tanio/pywork/cafe_work/cmp/ring_before (git archive of 1c93f9a's CRETA), log ../logs/test_point_source_annulus_before_ring.txt. Replaces the 9017022 version of this test (logs of that version overwritten)
cd /Users/tanio/pywork/cafe_work && tests/M5/fwhm/run_regressions.sh /Users/tanio/pywork/cafe_work/cmp/ring_before ring   # M5: NGC7469 extractions before/after the ring change (outputs ring_{before,after}_*; logs tests/M5/logs/ring_regression_*); compare with compare_extractions.py and cmp as for fwhm (log tests/M5/logs/ring_regression_compare.txt)
cd /Users/tanio/pywork/cafe_work/tests/M5/W2246 && env PYTHONDONTWRITEBYTECODE=1 MPLBACKEND=Agg PYTHONPATH=/Users/tanio/Sync/pywork/CAFE ~/miniforge3/envs/cafe-dev/bin/python -W ignore ring_fit.py > ../logs/ring_fit_W2246_c1003.txt   # M5: W2246's ring per band as CRETA sets it (cone 0.4263", r_ann_in 0.8526", ann_width 1.0" by default)
cd /Users/tanio/pywork/cafe_work && env PYTHONDONTWRITEBYTECODE=1 MPLBACKEND=Agg PYTHONPATH=/Users/tanio/Sync/pywork/CAFE ~/miniforge3/envs/cafe-dev/bin/python tests/M5/extract_W2246.py cubes_miri_mast_c1003 W2246_MIRI_c1003_ring W2246_MIRI_r0.4263as_ring_params.txt > tests/M5/logs/extract_W2246_c1003_ring.txt 2>&1   # M5: W2246 with the 1.5-FWHM cone and the 1" ring from 3 FWHM
cd /Users/tanio/pywork/cafe_work/tests/M5/W2246 && ~/miniforge3/envs/cafe-dev/bin/python -W ignore bkg_extraction_check.py /Users/tanio/pywork/cafe_work/extractions/W2246_MIRI_c1003_ring/W2246_MIRI_SingleExt_r0.4263as.csv > ../logs/bkg_extraction_check_W2246_c1003_ring.txt   # M5: its backgrounds, overlap ratios with S/N, NaN planes, stitched signs (the stitching-factor check per band: inline, log ../logs/stitch_factors_W2246_c1003_ring.txt)
cd /Users/tanio/pywork/cafe_work && ~/miniforge3/envs/cafe-dev/bin/python -W ignore tests/M5/W2246/drop_band.py extractions/W2246_MIRI_c1003_ring/W2246_MIRI_SingleExt_r0.4263as_cube.fits data/W2246/spectra/W2246_MIRI_r0.4263as_ring_noch1s_cube.fits ch1_SHORT   # M5: W2246's spectrum without ch1-short (fails if the output exists)
cd /Users/tanio/pywork/cafe_work/tests/M5/W2246 && ~/miniforge3/envs/cafe-dev/bin/python make_cafe_dir.py   # M5: cafe_dir for W2246 on dev: links to dev's tables plus my five W2246 tables (pre-sync)
cd /Users/tanio/pywork/cafe_work/tests/M5/W2246 && env PYTHONDONTWRITEBYTECODE=1 MPLBACKEND=Agg PYTHONPATH=/Users/tanio/Sync/pywork/CAFE ~/miniforge3/envs/cafe-dev/bin/python -W ignore fit_setup.py > ../logs/fit_setup_W2246.txt 2>&1   # M5: W2246's spectrum-only fit setup, no fit (z = 4.601 by default; logs fit_setup_W2246_z4.593.txt and _z4.6.txt with the z as argument)
cd /Users/tanio/pywork/cafe_work/tests/M5 && (for j in 0 1 2; do echo "$j w2246"; done) | xargs -n 2 -P 3 ./run_fit.sh   # M5: W2246's first spectrum-only fits (inpars params/inpars_jwst_miri_W2246_M5_spec.ini; out/w2246_j<j>, logs/fit_w2246_j<j>.txt)
cd /Users/tanio/pywork/cafe_work/tests/M5 && env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/Users/tanio/Sync/pywork/CAFE ~/miniforge3/envs/cafe-dev/bin/python -W ignore w2246_summary.py > logs/w2246_summary.txt 2>&1   # M5: their report (setup, chi^2, continuum, shares, PAH, chi^2/N per band)
cd /Users/tanio/pywork/cafe_work/tests/M5/W2246 && env PYTHONDONTWRITEBYTECODE=1 MPLBACKEND=Agg PYTHONPATH=/Users/tanio/Sync/pywork/CAFE ~/miniforge3/envs/cafe-dev/bin/python -W ignore line_width_check.py > ../logs/line_width_check_W2246.txt   # M5: the three unmasked lines' width bounds (force_all False/True) and their widths in the first run's residual
cd /Users/tanio/pywork/cafe_work/tests/M5/W2246 && env PYTHONDONTWRITEBYTECODE=1 MPLBACKEND=Agg PYTHONPATH=/Users/tanio/Sync/pywork/CAFE ~/miniforge3/envs/cafe-dev/bin/python -W ignore line_bounds.py > ../logs/line_bounds_W2246.txt   # M5: the final line choice's narrow and broad bounds in km/s, as fit_spec builds them (force_all)
cd /Users/tanio/pywork/cafe_work/tests/M5 && (for j in 0 1 2; do echo "$j w2246lines"; done) | xargs -n 2 -P 3 ./run_fit.sh   # M5: W2246 with narrow and broad Pa beta, Pa alpha and Br alpha (params/inpars_jwst_miri_W2246_M5_spec_lines.ini, force_all_lines; out/w2246lines_j<j>); then w2246_summary.py reports both run sets side by side (logs/w2246_summary.txt)
cd /Users/tanio/pywork/cafe_work/tests/M5/W2246_megacubes && env PYTHONDONTWRITEBYTECODE=1 MPLBACKEND=Agg ~/miniforge3/envs/cafe-dev/bin/python <script>.py   # M5: W2246's NIRSpec mega cubes, read only; scripts inspect_hdus, compare_headers, explore_nucleus, plot_quick_spectrum, make_maps, wcs_offsets, check_unit_scaling, check_hdu2_and_pixel11, test_psf_sub_smoothing, full_pass (writes full_pass/, deleted 2026-11-23), analyse_full_pass (needs full_pass/), spotcheck_megacubes; outputs in <script>_output.txt
cd /Users/tanio/pywork/cafe_work/tests/init_feats && env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/Users/tanio/pywork/cafe_work/cmp/dev_maskfix ~/miniforge3/envs/cafe-dev/bin/python real_spectra.py > logs/real_spectra.txt   # lines init_feats keeps on R1 and R2, before/after (no fit)
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
- 2026-11-18: **After M4 stage 3:** no more diagnostics in M4. HOT keeps its 200–1027.2 K range. The shipped fit settings stay as they are (`default_opt.cafe`: its FTOL, no restarts, no `x_scale`). R1's two end states and channel 4C, S1c with several noise seeds, and NIRSpec + MIRI go under "Later".
- 2026-11-18: **M4 next: the `flux0` fix.** Each component's `flux0` is the median flux of N = 20 channels around its reference wavelength λ₀, one-sided at the data edges. Diff hunk by hunk with its reason paragraph and its test; then stop.
- 2026-11-18: **Commit `c071ab1` (`flux0` fix) approved.**
- 2026-11-18: **M4's last step: the baseline.** Plain fits only, with the shipped settings, on R1 and R2, 10 each with the stage 1 rounding-level inputs, as the reference for M6. Then DESIGN.md brought up to date with all M4 changes.
- 2026-11-19: **M4 closed.** Push of `dev` to my fork approved. First M6 item: R2's fits at the 50 K wall between the COO and WRM ranges; M6's cube fits will show how often it happens, and the ratio constraint under "Later" is the candidate remedy. The M4 fit times are not a timing baseline.
- 2026-11-19: **Three items, then report and stop.** (1) Read-only, from the stage 3 records: the cost per fit in model evaluations (nfev; the machine was loaded) and wall time; for the restart chains, the distance to the chain's end point after 1, 2, 3, 5, 10 and 20 restarts, with the cumulative nfev relative to the plain fit. (2) Fix `mask_spec`: stop dropping channels with flux < 0 in both branches, keep the DQ, NaN and outlier masks; list, without changing it, any other code that drops negative channels or assumes positive flux; own commit with a synthetic test (a faint spectrum, S/N ~1 per channel); add it to the GOALS bug list, no PR. (3) On top of (2), a better line pre-selection in `init_feats`, keeping the rule "a line is fitted if its estimated peak is > 0": the peak as a least-squares amplitude over the channels within ±1 instrumental FWHM, weighted by the line's Gaussian profile; the continuum as the mean of the two sides' medians of the nearest 5 channels beyond 2 FWHM that are not within ±1 FWHM of another line in the tables. Keep the three-pass subtraction, the ×2 on the guesses, `force_all` and the PAH and opacity estimates. Own commit with a synthetic test over many noise realisations.
- 2026-11-19: **Commits `3fd7e7e` (`mask_spec`, G15) and `5e70c62` (`init_feats` peak estimate) approved as they are.** Both readings stay: the continuum windows avoid only the candidate lines, and the amplitude is Σ g (F − C) / Σ g². Logged, not acted on:
  - (a) intrinsically broad lines (see "Biases");
  - (b) the S/N 1 continuum shortfall (see "Biases");
  - (c) the other code that assumes positive flux, as listed with the `mask_spec` fix, except `flux0`, which changes.
- 2026-11-19: **No restarts and no `x_scale` by default** (from the stage 3 cost tables). Their cost is revisited in M6, where spaxels start from their neighbours' fits.
- 2026-11-19: **The HOT–STB degeneracy goes to M5** (near-IR photometry) **and to NIRSpec + MIRI for NGC7469.** R1 without channel 4C stays under "Later".
- 2026-11-19: **The M4 baseline is rerun with the current code at the start of M6**, since `init_feats` now changes R1's line set and starting values.
- 2026-11-19: **`flux0` becomes the median |flux| of the same 20 channels**, the convention `spec_norm_factor` already uses, so that channels < 0 never make it ≤ 0. `flux0` only sets the scale of `_FLX`.
  - Own commit, with its diff, reason and test: bit-identical when all 20 channels are > 0; on a faint synthetic spectrum whose window median is ≤ 0, `flux0` > 0 and the component fluxes in Jy recovered.
  - Commit the brief.
  - Read-only: is there an extracted NIRSpec + MIRI spectrum of NGC7469 in the pre-sync folder? Then report and stop.
- 2026-11-19: **Commit `688a02a` (`flux0` = median |flux|) approved.** In the faint test, "recovered" means within 2 stderr of the truth, for the components whose stderr is smaller than their flux. COO passes.
  - Logged: `NGC7469_NIRSpec+MIRI_reg1_04arcsec.dat` is in the rest frame (read it with z = 0), and `script/NIRSpec-MIRI_spec_script.py` reads it with z = 0.0163.
  - Commit the brief, show what a push of `dev` to my fork would publish, and stop.
- 2026-11-19: **Push of `dev` to my fork approved** (`84dc4c1`→`9b381cd`).
- 2026-11-19: **M5 approved.** First step: the NGC7469 NIRSpec + MIRI spectrum, with CRETA only (its single extraction and parameter files; no custom extraction code).
  1. Check that the NIRSpec and MIRI data folders can be read, and list the NGC7469 cubes in each (gratings, channels and bands, file names, pipeline version, date).
  2. Find out whether CRETA can take NIRSpec and MIRI cubes in one single extraction and stitch across the two instruments.
     - If it can, extract into the work folder with these settings:
       - centre on the nucleus with CRETA's centring, at the same sky position for every cube;
       - radius 1.5″ in every cube, as R1;
       - no aperture correction;
       - stitching reference band MIRI ch1-short.
     - If CRETA can't do any of these as stated, stop and tell me before extracting.
     - Then show the stitching ratios between bands and at the NIRSpec–MIRI join. Compare the new spectrum with R1 (the MIRI part, ratio per band) and with reg1 (read with z = 0; shape only, normalised, since the apertures differ).
     - If it can't: don't extract. The NIRSpec + MIRI spectrum is then reg1 (read with z = 0); tell me what CRETA would need to combine the two instruments.
  3. Report and stop; no fits yet.
- 2026-11-19: **M5 step 1's extraction choices approved:** the `wcsfix` NIRSpec cubes, all three gratings, centring at 5.4 µm.
- 2026-11-19: **M5 step 2: fit the NIRSpec + MIRI spectrum** (z = 0.0163) with `inpars_jwst_nirspec-miri_AGN.ini` and the shipped `default_opt.cafe`, no photometry: 10 plain fits with the rounding-level inputs.
  - For these fits only, in a work-folder copy of the inpars (the shipped file untouched): `read_spec(ignore_DQ=True)`; `STR_FLX = 0.2, True, 0., 2.` with STR_TAU fixed at 0; `Source_HOT = 'AGN'`; line resolving powers as they are.
  - Report the χ² spread and how many fits agree (Δχ² < 1); HOT, STB and STR per fit and their correlation; HOT's and STB's fractions of the continuum over 5–6 µm against R1's states A and B.
  - Log, not fixed yet: (a) CRETA's DQ, (b) the line resolving powers, (c) the shipped `nirspec-miri_AGN` inpars heating HOT with the ISRF. Then propose fixes for (a) and (b), no code, and stop.
- 2026-11-20: **Fixes (a) and (b) approved as proposed**, each its own commit, shown hunk by hunk with its reason and the tests listed in the proposals. Spectra without band names keep today's rule.
  - Also, read-only: where HOT_TMP's upper bound of 1027.2 comes from (code, tables, inpars history), what HOT_TMP represents (the radiation field's T_bb or a grain temperature), and what the emissivity grid allows at the top. I decide HOT's range from that. Then stop.
- 2026-11-20: **Review of (a) and (b).** `a1ff60a` approved. `9e8ccd5` approved with one change: `bandname` becomes an optional keyword at the end of `CAFE_param_generator`'s arguments (default: today's rule), so scripts that build it with the old arguments keep working; show me that hunk.
  - A band with no table in the inpars raises an error that names the band. Add the missing NIRSpec tables to the `SB_and_AGN` and `_reg` inpars; show me that diff.
  - Carbon sublimation: `sSubCar` = 1750 K for carbon grains; silicates stay at 1400 K. Its own commit, the diff hunk by hunk with its reason, and a test: silicate emissivities unchanged; carbon grains between 1400 and 1750 K kept; HOT's shape against T_bb up to the grid's top.
  - Then, in the work-folder inpars copy only, HOT_TMP's upper bound at 1750 K (the grid's top). Rerun the 10 plain NIRSpec + MIRI fits on the DQ-fixed extraction, without `ignore_DQ`. Report the χ² spread, HOT_TMP, and HOT's and DSK's fractions of the 5–6 µm continuum, against step 2. Shipped inpars unchanged until I've seen it. Then stop.
- 2026-11-20: **`5f3a533`, `173f758`, `fb585da` and `5073617` approved.** Fix the wording of `5073617`'s message (61% at 1027.2 K) before any push. *(Done: `076adbd`, same tree.)*
  - `_reg`: option (i), `read_inst` matches table names case-insensitively. Its own commit, hunk by hunk, with a test (the `_reg` inpars loads; every other shipped inpars gets the same tables as before). *(On hold: (i) alone does not make `_reg` load; see "Awaiting my OK".)*
  - Log, don't fix: DSK taking the near-power-law continuum is a limitation of CAFE's dust components (a temperature gradient seen as a power law), not something to fix.
  - Shipped inpars, all seven, one commit shown file by file *(done: `9ffc4b7`)*:
    - every free `_TAU` of COO, WRM, HOT and STB starts at 0.1, so extinction grows only where the data need it;
    - wherever DSK is free, `DSK_TAU = 0.0, False` (`miri_AGN`, `nirspec-miri_AGN`, `NGC7469_NIRSpec+MIRI_reg`), as `SB_and_AGN` already has it, so the disc can't take over other components' shape *(replaced 2026-11-22: `0.1, True, 0., 0.5`, commit `72e9edd`)*;
    - HOT_TMP's upper bound becomes 1750 K (the grid's top, now that carbon survives to 1750 K).
    - Every other bound, vary flag and expression stays as it is.
  - Then rerun the 10 NIRSpec + MIRI fits with the same changes in the work-folder copy (DQ-fixed extraction, no `ignore_DQ`). Report against `hot1750`: the χ² spread and end states, every `_TAU`, HOT_TMP, and HOT's, DSK's and STR's fractions of the 5–6 µm continuum. Then stop.
- 2026-11-20: **`9ffc4b7`: keep the 0.1 starts and HOT_TMP's bound; DSK_TAU's fix is under review.**
  - `inpars_jwst_NGC7469_NIRSpec+MIRI_reg.ini` goes to the M7 clean-up list (it can't load). Nothing else on it now.
  - One set that tests the candidate: NIRSpec + MIRI fits with the `tau01` copy, changing only DSK_TAU to `0.1, True, 0., 0.5` (DQ-fixed extraction, no `ignore_DQ`). Changed the same day: only j = 0, 1 and 2 (one batch of 3), not 10.
  - Report against `hot1750` and `tau01`: the χ² spread and end states, every `_TAU` (and whether DSK_TAU ends at its bound), HOT_TMP and COO_TMP (and whether at a bound), DSK_FLX, and HOT's, DSK's, WRM's, STR's and STB's fractions of the 5–6 µm continuum. Commit the brief; then stop.
- 2026-11-22: **DSK_TAU's shipped default: `0.1, True, 0., 0.5` wherever DSK is free** (`miri_AGN`, `nirspec-miri_AGN`, and `SB_and_AGN`, which I confirmed when asked; `_reg` stays on the M7 list). Its own commit, shown file by file *(done: `72e9edd`)*.
  - Log, don't act: (a) with DSK free, HOT_TAU and COO_TAU still end at 8–9 despite the 0.1 starts. Like DSK's role, this is the single-temperature dust components being bent toward a power law, part of the logged limitation. (b) The NGC7469 NIRSpec + MIRI fits have two end states 2% apart in χ². In one, STR is at 0 and DSK_TAU is 0.09. In the other, STR is on and DSK_TAU is 0.39. With the 0.1 starts the fits reach the STR-on one.
  - This closes the NIRSpec + MIRI step: NIRSpec removes M4's MIRI-only valley.
  - Commit the brief, show me what a push of `dev` to my fork would publish, and stop.
- 2026-11-23: **W2246 in M5: MIRI only.**
  - Test with W2246's MIRI cubes only. The NIRSpec mega cubes stay out of any extraction or fit. When we get to NIRSpec, `fix_wcs` is the mega cube for W2246's total SED.
  - No aperture correction until W2246's PSF arrives from a collaborator.
  - The three W2246 folders on `/Volumes/Photon` (MIRI `stage3` and `mast/202611`, NIRSpec `processed`) are read-only data folders (CLAUDE.md §5, commit `aeabec2`).
  - Extraction: CRETA's single extraction with a cone of 0.5″ at 5.4 µm (M3's `W2246_SingleExt_r0.5as.fits`), centring at 5.4 µm from M3's position, no background subtraction, `stitch_band = ch1-short`. Report W2246's centroid offset per cube.
  - The MIRI set: the 12 MAST `c1003_t001` cubes (master background subtracted), linked into a folder of their own in the work folder.
  - Stop if CRETA can't read the cubes, the centring fails or any stitching ratio is ≤ 0. *(2026-11-23: the centring failed and one ratio was negative, as with the stage3 cubes; see M5.)*
  - Then (step 3) compare the spectrum with M3's, band by band, and the 12.0 and 22.0 µm points with the spectrum interpolated there (no WISE response curves yet).
- 2026-11-23: **W2246: no local background with CRETA's annulus, for now.**
  - Asked: CRETA's own annulus on the `c1003` cubes, centred at 8.0 µm (ch2-short), with stitching reference ch2-short. Stopped before extracting, because no single annulus fits (see "Biases").
  - Rejected: an annulus that scales with wavelength like the cone, which would be a thin ring (0.50–0.64″ at 5.4 µm) in W2246's PSF wings; and per-band CRETA runs, which would need stitching outside CRETA.
  - Next, read only: the pipeline's `c1003` x1d spectra (extraction settings, background, aperture correction), and their fluxes against CRETA's.
- 2026-11-23: **W2246: the x1d route is closed**, because the pipeline treated W2246 as extended (see M5).
  - Next: a CRETA change for faint point sources, as its own commit for my review, with no extraction yet.
  - When `point_source = True` and background subtraction is on, each wavelength plane gets its own annulus. Its inner radius is a fixed multiple of the cone radius at that wavelength. Its outer radius is the largest circle around the source inside that cube's field.
  - Say what happens in a plane where the annulus has too few pixels, and propose the multiple and the minimum number of pixels.
  - Test it on synthetic data with known truth: a point source on a known, spatially flat background of either sign, in cubes with small fields. The background must be recovered and the source flux unchanged.
  - For W2246: which cone radius at 5.4 µm is about one FWHM of MIRI's PSF there, and whether the annulus then fits in all 12 bands.
  - *(Done 2026-11-23: commit `9017022`, waiting for my review; the multiple and the minimum under "Awaiting my OK".)*
- 2026-11-23: **Commit `9017022` approved:** CRETA's per-plane annulus for point sources, with the multiple 2 (`r_ann_in = 2 × user_r_ap`) and a minimum of 50 valid annulus pixels per plane.
  - For when W2246's PSF arrives: compute the aperture correction with the same cone and annulus as the data. MIRI's real PSF wings put some of the source's light in the annulus (see "CRETA aperture-correction path").
  - Next, its own commit on top of `9017022` for my review, with the W2246 extraction on hold: for point sources, scale the cone and the annulus's inner radius with the PSF's FWHM instead of with wavelength, r(λ) = r_ap × FWHM(λ) / FWHM(λ_ap), so the aperture stays a fixed number of FWHM.
    - One FWHM function per instrument, chosen from the cube. MIRI MRS follows Law et al. 2023: FWHM = 0.033″ (λ/µm) + 0.106″.
    - NIRSpec: FWHM ∝ λ, so its behaviour is unchanged until I choose a NIRSpec law.
    - FWHM(λ_ap) comes from the instrument that covers λ_ap. Extended sources unchanged.
  - Test it on synthetic data with known truth: Gaussian point sources whose FWHM follows Law et al. The fraction of flux in the cone must be the same at every wavelength, and is shown varying before the change. NGC7469's extractions must stay bit-identical.
  - For W2246, r_ap = 0.2842″ at 5.4 µm (one FWHM) and r_ann_in = 0.5684″ (two FWHM): say how they fit in all 12 bands.
  - *(Done 2026-11-23: commit `2818075`, waiting for my review; my choices in it are under "Awaiting my OK".)*
- 2026-11-23: **Commit `2818075` approved**, with its three choices:
  - NIRSpec cones keep r_ap × λ/λ_ap, even when λ_ap lies in MIRI;
  - a MIRI cube with `lambda_ap` below 4.9 µm stops with a `ValueError`;
  - the boundary is MIRI MRS's shortest wavelength, 4.9 µm.
  - A NIRSpec FWHM law is still to be chosen (see "Later"). With it, any `lambda_ap` works and the cone is continuous at the NIRSpec–MIRI join.
  - Next: the synthetic cubes under `tests/M5/fwhm/` deleted. Then W2246 from the `c1003` cubes:
    - centring at 8.0 µm with CRETA's centring; `point_source = True`, r_ap = 0.2842″ at 5.4 µm (one FWHM);
    - background on with r_ann_in = 0.5684″ (two FWHM); no aperture correction; `stitch_band = ch2-short`.
  - Report:
    - the background removed per band (median), and the NaN planes per band;
    - the raw overlap ratios with their S/N;
    - whether any stitched band is negative, and ch4-long beyond 27 µm.
  - Stop before using the stitched spectrum if any overlap ratio is ≤ 0 or has S/N < 3. Otherwise do step 3:
    - the shape against M3's spectrum, normalised, since the apertures and reductions differ;
    - the 12.0 and 22.0 µm points, approximately. Without aperture correction, the spectrum should come out low by the fraction of the PSF outside a one-FWHM cone.
- 2026-11-23: **W2246 after its first extraction with a local background** (see M5):
  - **ch1-short is unreliable** and is left out of W2246's fits. It is barely detected, 24% of its channels are negative, and its overlap ratio of 1.65 sets its stitching.
  - **M3's spectrum is superseded** by this extraction (`extractions/W2246_MIRI_c1003_bkg/`). The shape differences between them are not pursued.
  - **At 22 µm,** the spectrum/photometry ratio (0.70) is likely lowered by W4's known red-source issue: an effective wavelength of about 22.8 µm, and catalogued fluxes about 8–10% too high for steeply rising spectra (Wright et al. 2010; Brown et al. 2014; checked against the Explanatory Supplement).
    - It is to be handled with M5's photometry conventions.
    - With it, both points are about 0.8, consistent with one aperture-correction factor.
    - *(2026-11-23: this rests on the inference that the 12.0 and 22.0 µm points are WISE W3 and W4; the bands and origin of W2246.txt are unknown. See the next entry.)*
- 2026-11-23: **W2246 is fitted on its spectrum alone**, with no scaling to photometry and no W4 correction.
  - W2246.txt's photometry has unknown bands and origin. Photometry enters only once its origin is known (M5's photometry conventions).
  - **The cone becomes 1.5 FWHM** (r_ap = 0.4263″ at 5.4 µm), because it captures more of the PSF.
  - Next, a CRETA change as its own commit for my review, for point sources only:
    - the background ring is a fixed 1.0″ wide (`ann_width`) at every wavelength;
    - its inner edge scales with the FWHM like the cone (`r_ann_in` at `lambda_ap`);
    - in each plane where inner edge + 1″ would leave the largest circle inside the field, the ring moves inward just enough for the full 1″ ring to fit;
    - it never moves inside the cone. If the ring can't fit outside the cone, that plane's background is NaN, and CRETA says how many such planes there are;
    - `MIN_ANNULUS_PIXELS` becomes 20.
  - Update the parameter-file comments, README and DESIGN.md; adapt the synthetic annulus test (fixed width, pull-in, 20-pixel minimum); NGC7469's extractions must stay byte-identical.
  - For W2246, with r_ap = 0.4263″ and r_ann_in = 0.8526″ (3 FWHM) at 5.4 µm: per band, the cone, the ring's inner and outer edges (and where it was pulled in), the fewest pixels and any NaN planes.
  - *(Done 2026-11-23: commit `2383c67`, waiting for my review; my choices in it are under "Awaiting my OK".)*
- 2026-11-23: **Commit `2383c67` approved**, with its three choices: `ann_width` ≤ 0 with a point source stops with a `ValueError`; "no room" means the fitted inner edge inside the largest cone radius; and the per-band messages.
  - **Next, step 1:** re-extract W2246 from the `c1003` cubes:
    - centring at 8.0 µm with CRETA's centring; `point_source = True`, r_ap = 0.4263″ at 5.4 µm (1.5 FWHM);
    - background on with r_ann_in = 0.8526″ (3 FWHM) and `ann_width` = 1.0″; no aperture correction; `stitch_band = ch2-short`.
    - Report the background removed per band (median), the raw overlap ratios with their S/N, the NaN planes per band, and whether any stitched band is negative.
    - Stop before using the stitched spectrum if any overlap ratio is ≤ 0 or has S/N < 3.
  - **Then, step 2:** prepare W2246's spectrum-only fit (no photometry) and show me the setup, with no fits yet:
    - the new spectrum without ch1-short, and z;
    - my `inpars_jwst_miri+phot_W2246.ini` and its five tables. How its continuum settings differ from the current shipped rules (T ranges, the 0.1 starts of the optical depths, HOT_TMP up to 1750 K, DSK_TAU free up to 0.5), and which components are free;
    - which components the rest-frame range (about 1.0–5.1 µm) can't constrain;
    - the opt file, and the number of free parameters.
  - Then stop for my choices.
- 2026-11-23: **W2246 step 2 goes on with the stitched spectrum without ch1-short.** The failed ch1-short → ch1-medium ratio sets only ch1-short's own factor, and ch1-short is excluded. In the setup, give per band the ratio of the channel-to-channel scatter to CRETA's quoted errors, since the fit weights by those errors. *(Done 2026-11-23; see M5.)*
- 2026-11-23: **W2246's spectrum-only fit setup.** This is W2246's own setup, not a general rule.
  - It lives in a copy of my `inpars_jwst_miri+phot_W2246.ini` in the work folder. My pre-sync file and the shipped inpars stay untouched.
  - **Spectrum:** the ring extraction without ch1-short (`data/W2246/spectra/W2246_MIRI_r0.4263as_ring_noch1s_cube.fits`); z = 4.601 ([CII], Díaz-Santos et al. 2016); no photometry.
  - **Lines and opacity features:** masked, as in my tables, so only the continuum and the 3.3 µm PAH are fitted.
  - **CIR, CLD and COO:** off. Their FLX is fixed at 0, so their other parameters are fixed too.
  - **WRM:** as in my file, heated by the AGN, 100–300 K; its TAU starts at 0.1.
  - **HOT:** 300–1750 K, so it doesn't overlap WRM. HOT_TAU and STB_TAU start at 0.1, and DSK_TAU = 0.1, True, 0., 0.5.
  - **FLX starts:** as in my file.
  - **Errors:** as CRETA gives them, with the shipped `default_opt.cafe` (whose 1% floor applies).
  - **First run:** 3 plain fits with the usual rounding-level inputs (j = 0, 1, 2).
  - Report, starting with the setup header: the free parameters; the χ² of each fit and whether they agree (Δχ² < 1); the fitted continuum parameters with their errors; each component's share of the continuum across the range; the 3.3 µm PAH; and χ²/N per band. Then stop.
  - *(Done 2026-11-23: inpars copy `tests/M5/params/inpars_jwst_miri_W2246_M5_spec.ini`, run set `w2246`; see M5.)*
- 2026-11-23: **Change to W2246's setup: Paα 1.875, Paβ 1.282 and Brα 4.051 µm unmasked.**
  - Each is one Gaussian with its width free, with no broad second component. Every other line and opacity feature stays masked.
  - Show the three lines' width bounds in km/s, and stop before fitting if they would stop a broad line.
  - Then rerun the 3 fits with the lines unmasked and report both runs side by side.
  - *(2026-11-23: set up in `inpars_jwst_miri_W2246_M5_spec_lines.ini`, with a work-folder copy of my H table that has those three lines at MASK = 0.)*
  - *(Stopped before fitting: `EPSGamma_LIN_N = 400` km/s caps each width at 400 km/s, which would stop a broad line. See M5.)*
  - *(Replaced 2026-11-23 by the next entry.)*
- 2026-11-23: **W2246's lines, final choice** (W2246's setup; it replaces my previous line choices above).
  - Paβ, Paα and Brα each get a narrow and a broad component: their double-component flag is set in the work-folder copy of my H table. Every other line and opacity feature stays masked.
  - **Narrow components:** widths free up to 400 km/s; centres fixed at z = 4.601.
  - **Broad components:** widths free up to 3,000 km/s; centres free within ±1,500 km/s of z = 4.601.
  - **`force_all_lines = True`.** With every other line masked, it forces only these three lines.
  - Show the copy's diff against my files and every resulting bound in km/s. Stop before fitting if CAFE can't set the narrow and broad components' options separately as stated.
  - Then 3 plain fits (j = 0, 1, 2), reported next to the first run (lines masked).
  - **No fit until the PSF arrives.**
  - Commit the brief, show me what a push of `dev` to my fork would publish, and stop.
- 2026-11-24: **W2246 test closed** (see M5): it was to check CAFE and CRETA, not to fit W2246's science; no more W2246 runs. Only its general findings go in the brief; W2246's specific results stay as they are. **New milestone M8** after M7 (point-source cubes prepared before CRETA); it starts only after my approval.
- 2026-11-24: **After the W2246 test.**
  - **Finding (1) is general:** CRETA's errors are too small in every band of both sources (see M5, finding 1).
  - **NIRSpec FWHM law:** read-only search for a published formula first, then my choice before any code (see "Later").
  - **The PSF-based aperture correction becomes part of M8.** It won't wait for PSFs here; the "when W2246's PSF arrives" to-do is closed.
  - **G16 fixed now:** own commit, failing case first, diff hunk by hunk with its reason, and a test.
  - **Photometry for now: HST and ALMA only, monochromatic only, so no filter curves.** Plan first, no code: a calibration floor per instrument, points beyond 1000 µm rest not used, and the reference wavelength of a monochromatic point (see "Awaiting my OK").
- 2026-11-25: **Commit `6e7aee1` (G16) approved as it is.** With `PAH_FLX = 0` the lines are not dimmed, in both paths of `get_model_fluxes`.
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
- 2026-11-17: **Candidate for the `flux0` fix:** the median over N channels around λ₀ (one-sided at the data edges). N is my decision. *(Decided 2026-11-18: N = 20; see "Decisions".)*
- 2026-11-17: **G14: fix the emissivity interpolation to the bracketing pair of grid temperatures?** (from M4 stage 2) A model change; it would shift every fit with a dust temperature between grid points. Stage 2's sets would be rerun after it. *(Decided 2026-11-18: fix it next; see "Decisions".)*
- 2026-11-17: **Constrain the order of the cool and warm dust temperatures** (e.g. WRM_TMP > COO_TMP)? (from M4 stage 2) Without it, R2 ends in either of two minima with the temperatures swapped. A physics choice. *(Decided 2026-11-18: non-overlapping T ranges in the inpars files, no code change; see "Decisions".)*
- 2026-11-17: **Fit settings after G14** (CLAUDE.md §4): `x_scale='jac'`, FTOL, restarts or another convergence test. In stage 2, `x_scale='jac'` found R2's better minimum in all 10 fits; in R1 its lower χ² came only with temperatures on G14's jumps. Stage 3 (2026-11-18, G14 fixed, new ranges): no setting is best on all three. `x_scale='jac'` + restart reaches R1's lowest end state in 9 of 10 fits but ends worse than plain on R2 in 8 of 10; restart alone takes R1 to its higher end state (A) and S1c to the noise level; the shipped plain fit stops 1,246–2,549 above R1's best and 4–63 above S1c's. *(Decided 2026-11-18: the shipped settings stay as they are; see "Decisions".)*
- 2026-11-18: **Dust T ranges for the shipped inpars files** (non-overlapping, my decision of 2026-11-18). Proposed, from my pre-sync `inpars_jwst_miri_SB.ini` (the only pre-sync JWST file with ranges; also used for my IIZw096, NGC3256 nuc1 and VV114 fits): COO 0–50 K, WRM 50–200 K, HOT 200–1027.2 K in all 7 files (now 0–∞, 0–∞, 100–1027.2). The two AGN files start COO at 75 K, outside that range: proposed start 40 K, as in the other files (R1's fits end at 23–29 K). CIR and CLD unchanged (fixed, flux 0). M4's fits lie inside these ranges (R1: COO 23–29, WRM 76–78, HOT 530–650 K; R2: 30.5, 59.4, 649 K), and R2's swapped state (COO 59.4 K) is excluded. My pre-sync IIZw096 fit with them ended at both lower bounds (WRM 50.0, HOT 200.0 K). Alternative from my pre-sync files: CLD 5–25, COO 25–100, WRM 100–300, HOT 300–1027.2 K (CYGNUS, MIRI + photometry), which would exclude R1's and R2's WRM (59–78 K). *(Decided 2026-11-18: COO 3–50, WRM 50–200, HOT 200–1027.2 K, all files but IIZw096; see "Decisions".)*
- 2026-11-18: **Rerun plan, M4 stage 3** (proposed). `dev` with G14 fixed and the new T ranges; shipped `default_opt.cafe`; no photometry; 10 fits per set with the stage 1 rounding-level inputs; new run names, stage 1 and 2 outputs kept. Setups: R1 and R2 as before (their inpars now with the new ranges), and S1c, built as S1b was but from the new R1 plain fit (j = 0), so S1b's files stay. Sets per setup: plain (shipped settings), restart, and `x_scale='jac'` + restart. To decide: the restart stop rule (recommended: stop when 5 successive restarts together lower χ² by < 1, as stage 2's single-restart rule stopped R1's chains while they still fell ~2 per restart). Measured as in stage 2, plus: end temperatures at a range edge, and none on a former G14 jump. *(Decided 2026-11-18: as proposed, with the 5-restart rule, before the `flux0` fix; see "Decisions".)*
- 2026-11-18: **R1's lowest χ² puts HOT at its 200 K lower bound** (from M4 stage 3). End state B (HOT_TMP 200 K fixed "at lower bound", HOT_FLX 0.11, STB_FLX 0.58, COO 16 K, WRM 71 K) lies 773 below A (HOT 665 K, STB_FLX ≈ 0.001, COO 23.7 K, WRM 77.1 K). B's net gain comes from channel 4C (24.4–28.8 µm observed: −5,215, against +4,400 elsewhere), which holds 39% of R1's χ² at B. So the fit wants a third dust component cooler than 200 K, and the short-wavelength continuum then goes to the stars instead of the hot dust. A physics choice for me: accept B as R1's fit, change HOT's range for this source, or look at channel 4C first. *(Decided 2026-11-18: HOT keeps 200–1027.2 K; R1's two end states and channel 4C go under "Later".)*
- 2026-11-18: **S1c: separate a bias from the noise?** (from M4 stage 3) On its one noise realisation, the converged S1c fits agree with each other but sit 2–3 stderr from the truth in COO_TMP (+4%), COO_TAU (+10–16%) and WRM (−1 to −7%); S1b showed the same pattern. Telling a bias from noise needs several noise realisations of the same truth (e.g. 10 seeds, restart set). Not run. *(Decided 2026-11-18: under "Later".)*
- 2026-11-17: **A component's TAU at 0: fix its MIX and COV too?** (from M4 step 1) The model skips a component's extinction when its TAU is 0 (`if p["STB_TAU"] > 0: … else: ext = 1`), so MIX and COV then have no effect, as the other parameters do when `_FLX` is 0. `check_fit_pars` fixes the TAU at 0 but leaves MIX and COV free: a free parameter with no effect, so no error bars and a refit. Free in the shipped inpars: `STB_COV` (SB, nirspec-miri SB, IIZw096). Recommended: yes, the same rule as for `_FLX`. *(Decided 2026-11-17: yes, under one principle; see "Decisions".)*
- 2026-11-17: **Keep a parameter free when another component's expression uses it?** (from M4 step 1) All 7 shipped inpars tie `PAH_TAU` to `WRM_TAU`. When `WRM_FLX` reaches 0, `check_fit_pars` fixes `WRM_TAU` (before and after `d6bd782`), although it still sets the PAH extinction. Recommended: the zero-flux (and zero-TAU) freeze leaves free any parameter that a parameter of another component uses in its expression. *(Decided 2026-11-17: yes, under one principle; see "Decisions".)*
- 2026-11-19: **Commits `3fd7e7e` (`mask_spec`, G15) and `5e70c62` (`init_feats` peak estimate)**, with their diffs, reasons and tests. Not pushed. *(Approved 2026-11-19; see "Decisions".)*
- 2026-11-24: **Commit `6e7aee1` (G16, `get_model_fluxes` with `PAH_FLX = 0`)**, with its diff, reason and test. Not pushed. *(Approved 2026-11-25; see "Decisions".)*
- 2026-11-24: **The NIRSpec FWHM law for CRETA's cones** (see "Later" for the sources). The options:
  - (a) D'Eugenio et al. 2024, along and across the slices, combined (e.g. their geometric mean) or the along-slice one;
  - (b) Pascalau et al. 2026 (STPSF-based, circular);
  - (c) keep FWHM ∝ λ;
  - (d) fit our own law to calibration-star cubes (PIDs 1128, 1219, 1222, 1536, 1537 and 3399; needs downloads).
- 2026-11-24: **Photometry plan: HST and ALMA, monochromatic only** (my decision of the same day; plan, no code). Proposals:
  - **Calibration floor per instrument**, added in quadrature: σ_fit² = σ² + (f × F)². It is applied in the fit like the spectrum's floor; the products keep the quoted errors. Documented values (f is my choice):
    - HST WFC3/UVIS: absolute up to 1.5%, internal 0.5% for wide, medium and narrow filters (WFC3 Data Handbook v6.0 §5.7; ISR 2021-04).
    - HST WFC3/IR: 1–2% absolute, 1% statistical; repeatability 1.5% in staring mode (Data Handbook §7.11; ISR 2020-10).
    - HST ACS/WFC: about 1% external (Bohlin 2016, AJ 152, 60); the ACS Data Handbook §5.1.2 says 1–2%.
    - ALMA: better than 5% in Bands 1–5, 10% in Bands 6–8, 20% in Bands 9–10 (Cycle 13 Proposer's Guide, Appendix A.9.2; not stated as 1σ).
  - **How CAFE knows a point's instrument:**
    - The name column starts with a key: `HST_WFC3UVIS_`, `HST_WFC3IR_`, `HST_ACSWFC_` or `ALMA_`. A small table in `CAFE/tables/` holds each key's floor and its source.
    - For ALMA, the band comes from the point's frequency, using the documented band ranges.
    - `read_phot` refuses an unknown key, with a message listing the known ones, so photometry still enters only once its origin is known.
    - Alternative: a sixth column for the instrument.
  - **Points beyond 1000 µm rest are not used.** `read_phot` raises a `ValueError` naming each such point (name, observed and rest wavelength); the user removes them from the file.
    - 1000 µm is where CAFE's source SEDs stop (they are clamped beyond) and where the grain cross-section tables end.
    - `read_phot` already needs `read_spec` first, for z.
  - **Monochromatic only:** `read_phot` refuses a point whose width is not 0. A width of 0 already makes `synphot` take the monochromatic path, whatever `DoFilter` is.
  - **The reference wavelength of a monochromatic point:**
    - HST: the filter's pivot wavelength λ_p (`PHOTPLAM`), with F_ν = ⟨F_λ⟩ λ_p²/c, the same for ST and AB magnitudes (Tokunaga & Vacca 2005, Eq. A10; WFC3 and ACS Instrument Handbooks).
      - This is exact for spectra flat in F_ν or in F_λ.
      - For F_ν ∝ λ^−2 or λ^4 the band average is about 0.3% high for a 10%-wide band, 1.3% for 20%, 3% for 30% and 9% for 50% (top-hat illustration). Wide HST filters span 20–45%.
      - An optional check: a table of pivot wavelengths per filter, against which `read_phot` compares the given wavelength.
    - ALMA: the frequency the flux density refers to, i.e. the continuum image's reference frequency (CASA tclean `reffreq`, by default the middle of the selected range; `CRVAL3` in the FITS). Not the proposal's representative frequency, which is a planning parameter. Given in the file as c/ν in µm.
- 2026-11-19: **Commit `688a02a` (`flux0` = the median |flux| of its 20 channels)**, with its diff, reason and test (`tests/flux0_abs/`, work folder). Not pushed. DESIGN.md: `f4af609`.
  - Bit-identical: 108 windows with all 20 channels > 0 (10 noisy synthetic spectra, R1, R2) give the same `flux0` bit for bit.
  - Faint truth: CAFE's own continuum at the AGN inpars' starting values, with no lines and no PAHs. The S/N per channel falls log-linearly from 10 to 0.1, so it is 0.16 at 24 µm. Seeds 4, 7 and 19 are the first three whose COO window median is ≤ 0.
  - Before the change: COO's `flux0` was −3.3 to −5.7 mJy and COO was lost (0 Jy) in all three fits. WRM (1.20–1.29×) and STB (4.7–10.2×) took its place, and the continuum ∫F_ν dν was 0.65–0.69× the truth.
  - After it: `flux0` > 0 everywhere. COO came out at 0.79–1.11× the truth (∫F_ν dν) and the continuum at 0.905–1.003×. Every component's flux at λ₀ was within 0.3 stderr of the truth. At this S/N only COO's stderr is below its true flux (46–85% of it); WRM, HOT, STB and DSK are unconstrained. *(Approved 2026-11-19. My rule for "recovered": within 2 stderr of the truth, for components whose stderr is smaller than their flux. COO passes, within 0.3 stderr in all three fits.)*
- 2026-11-19: **`init_feats`: which lines the continuum windows avoid.** I read "any other line in the line tables" as the other candidate lines: the table lines with mask 0 inside the data and the instrument ranges, the ones `init_feats` estimates. The tables also hold masked lines (mask 1) in the MIRI range: 43 of 81 atomic and 15 of 18 H recombination lines in the AGN tables, 61 of 81 and 26 of 31 in the SB tables. Avoiding them too would need their FWHM from the resolving-power tables (more code) and would push the continuum windows further out. *(Decided 2026-11-19: kept as implemented.)*
- 2026-11-19: **`init_feats`: the least-squares amplitude.** Implemented as Σ g (F − C) / Σ g², with g the line's Gaussian profile (peak 1) and equal weights per channel. Another reading of "weighted by the profile" is a fit with weights g, Σ g² (F − C) / Σ g³, which gives the line's centre more weight. The quoted uncertainties are not used (about constant over ±1 FWHM). *(Decided 2026-11-19: kept as implemented.)*
- 2026-11-19: **Other code that assumes positive flux** (listed with the `mask_spec` fix; not changed): *(Decided 2026-11-19: `flux0` becomes the median |flux|, commit `688a02a`; the rest stays as logged.)*
  - `flux0` (`make_cont_profs`): the median of 20 channels around λ₀ can now be ≤ 0 in a faint spectrum or spaxel. A component is `_FLX` (≥ 0) × `flux0`, and the model clips it to 0 (e.g. `fCOO[fCOO < 0] = 0.0`), so that component is lost from the fit.
  - `init_feats`' PAH scale: the reference PAH's peak is F(λ₀) minus the mean of F at λ₀(1 ± 0.033), one interpolated point each. If it is ≤ 0, every PAH starts at ≤ 0, which lmfit moves to the lower bound 0; if it is exactly 0, `init_feats` raises "Input spectrum does not contain any PAH band…".
  - `read_spec(..., read_columns=…, flux_unc=<fraction>)`: the uncertainty is the flux × the fraction, so a channel < 0 gets a negative uncertainty, and a channel near 0 an uncertainty near 0, which then dominates χ².
  - Plots with a log flux axis cannot show channels ≤ 0: `plot_spec` (`cafe.py`, both copies), `sedplot` and `cafeplot` (`cafe_lib.py`). The last two also set the lower y limit from the minimum flux (0.8 × the minimum; 0.1 × the minimum of the 5 channels at each end), which is ≤ 0 when a channel is.
  - Not affected: the normalisation (median |flux|), the error floor ((0.01 F)²), the line-peak rule (it works on F minus the continuum) and the cube's fitting order (the `nansum` of the raw cube, which `mask_spec` does not touch). No code takes the log of the data's flux.
  - Outside the fit, CRETA: `cube_preproc.py:387`, `:412` skip a centroid image whose sum is ≤ 0.
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
- 2026-11-19: **Fix proposal for (a): CRETA's single-extraction DQ over the circle** (see "Biases", (a)). *(Approved 2026-11-20; done, commit `a1ff60a`, see M5.)*
  - In `getApertureDQList` (`cube_preproc.py`), take the maximum over the pixels the aperture covers (photutils `ApertureMask.get_values`, the pixels with weight > 0) instead of over the cutout square.
  - A channel is then flagged only when a flagged pixel overlaps the circle. Since CRETA turns flagged pixels into NaN, that is exactly when its flux is NaN. The fluxes do not change.
  - Test: a synthetic cube with flagged pixels only in the square's corners (DQ 0 expected) and one with a flagged pixel inside the circle (DQ ≠ 0, flux NaN); then NGC7469's extraction redone: fluxes bit-identical, DQ ≠ 0 exactly on the NaN channels, and the channels reaching the fit identical to step 2's with `ignore_DQ=True`.
- 2026-11-19: **Fix proposal for (b): each line takes the resolving power of the band its data come from** (see "Biases", (b)). *(Approved 2026-11-20; done, commit `9e8ccd5`, see M5.)*
  - CRETA cubes carry each channel's band; `read_spec` keeps it and `mask_spec` returns it, but the fit's `Spectrum1D` drops it before `CAFE_prof_generator`.
  - Pass the band names on to `init_feats`. Give each line the table of the band of the channel nearest its observed wavelength, through a fixed map from CRETA's band names (`G140H` … `ch4_LONG`, stored as `('G140H')`) to the tables (`G140H` … `MIRI_CH4L`). Which lines are fitted stays as now.
  - Spectra without band names (`.dat`, `.txt`, `.csv`: `UNKNOWN`) keep today's rule. Whether they need more, R1 included, is my decision.
  - Test: a synthetic spectrum with two bands whose tables overlap and lines inside and beyond the overlap (known resolving powers); on the NIRSpec + MIRI spectrum only the lines listed under (b) change; R1 unchanged.
- 2026-11-20: **(b): a band with no table of its own in the inpars keeps today's rule** (my choice in the fix, needs my OK). Example: `inpars_jwst_nirspec-miri_SB_and_AGN.ini` and `inpars_jwst_NGC7469_NIRSpec+MIRI_reg.ini` list only G395H and MIRI. On a spectrum with G235H data, the lines at 2.9–3.2 µm (observed) sit on G235H data and would still get G395H's resolving power. Alternative: stop with an error that names the band. *(Decided 2026-11-20: an error that names the band, commit `fb585da`; the NIRSpec tables added to `SB_and_AGN`, commit `173f758`. `_reg` not done: see the next entries.)*
- 2026-11-20: **HOT's temperature range** (my decision; see M5, "HOT_TMP"). The grain model caps what HOT can do: the bluest shape it reaches is at T_bb ≈ 1148 K, only 3–4% bluer in F_ν(2 µm)/F_ν(5 µm) than at 1027.2 K. Above that it gets redder, and from ≈ 1450 K it is a flat F_ν.
  - *(2026-11-20, with carbon at 1750 K (`076adbd`): the bluest shape is at the 1521.3 K grid point (F_ν(2)/F_ν(5) 3.31, AGN), and nothing emits at 1750 K. With the bound at 1750 K in a work-folder copy, HOT_TMP ends at that grid point in all 10 NIRSpec + MIRI fits (see M5). The shipped inpars keep 1027.2.)*
  - *(Decided 2026-11-20: HOT_TMP's upper bound is 1750 K, the grid's top, in all seven shipped inpars; commit `9ffc4b7`.)*
- 2026-11-20: **Carbon's sublimation temperature: 1400 K as now, or 1750 K** (`sSubCar`, defined in `grainSizeDF` but unused; see "Biases"). A dust-model change and a physics choice. With 1750 K, carbon grains could survive to higher T_bb, which would change what HOT can do at the top of its range. *(Decided 2026-11-20: 1750 K for carbon, silicates at 1400 K; commit `076adbd`.)*
- 2026-11-20: **`inpars_jwst_NGC7469_NIRSpec+MIRI_reg.ini` cannot be loaded, so its NIRSpec tables are not added yet** (see "Biases"). Adding `JWST_NIRSpec_G140H` and `JWST_NIRSpec_G235H` in the file's own spelling would leave it failing. Options: (i) `read_inst` matches the names to the file names case-insensitively (code, two lines); the file then loads as written, and the two tables are added in its spelling. (ii) The file's NIRSpec names become `G140H`, `G235H`, `G395H` (inpars only).
  - *(Chosen 2026-11-20: (i). On hold the same day: (i) alone does not make `_reg` load. It also lacks `PAH_INPUT`, `GOPACITIES_INPUT` and seven OPC/Vgrad options, and names three line tables that do not exist (see "Biases"). Loading it means bringing it to the current format, which needs my choices: which line lists, PAH and opacity tables, and OPC/Vgrad settings (e.g. those of `nirspec-miri_AGN`). Or it stays as it is, logged. (i) on its own is still a fix for mixed-case table names.)*
  - *(Decided 2026-11-20: `_reg` goes to the M7 clean-up list; nothing else on it now.)*
- 2026-11-20: **DSK_TAU in the shipped inpars where DSK is free** (`miri_AGN`, `nirspec-miri_AGN`; my decision; *corrected 2026-11-22: `SB_and_AGN` has DSK free too*). Now `0.0, False` (`9ffc4b7`, under review). The candidate is `0.1, True, 0., 0.5`. On NGC7469's NIRSpec + MIRI spectrum (M5, `tau01` and `dskfree`):
  - **Fixed at 0:** the disc drops out, and COO_TMP sits at its 50 K bound. χ² is 50,414 higher.
  - **Free:** the disc keeps 46% of the 5–6 µm continuum, and DSK_TAU ends at 0.39. With the 0.1 starts, the three fits all ended in `hot1750`'s STR-on state, 3,924 above its best.
  - *(Decided 2026-11-22: `0.1, True, 0., 0.5` in `miri_AGN`, `nirspec-miri_AGN` and `SB_and_AGN`; commit `72e9edd`.)*
- 2026-11-23: **CRETA's per-plane annulus for point sources, commit `9017022`: the change itself, the multiple and the minimum** (see M5, W2246).
  - **The multiple:** 2, so `r_ann_in = 2 × user_r_ap` (0.56″ with W2246's 0.28″ cone). Recommended.
    - The annulus starts at 2 cone radii: 2 FWHM at 5.4 µm and 2.8 FWHM at 28.7 µm, since the cone grows faster than the FWHM. That is beyond the PSF's core and first ring (about 1.2 FWHM for an Airy pattern; an inference, not MIRI's measured PSF).
    - W2246's ch4-long allows at most 2.2 (with 50 pixels), so a larger multiple would not fit.
    - MIRI's real PSF has wings beyond a Gaussian. Their light in the annulus lowers the flux, by an unknown amount until the PSF arrives (for a Gaussian, 3×10⁻⁸ of it).
  - **The minimum:** 50 valid pixels per plane (`MIN_ANNULUS_PIXELS`, `cube_handler.py`). Recommended.
    - The median of N pixels has an error of about 1.25σ/√N per plane. Cube pixels are correlated (the pipeline's covariance prefactor is 1.8, so about N/3 are independent), so 50 pixels give about 0.3σ.
    - A plane with fewer, or with no room for an annulus, gets a NaN background and so a NaN flux, and CRETA prints how many planes per band. A round number, not set from W2246 (whose smallest plane has 98).
  - **For W2246:** a cone of 0.28″ at 5.4 µm is about one FWHM there (0.284″; Law et al. 2023, Eq. 1: FWHM = 0.033 (λ/µm) + 0.106″). It grows to 1.49″ (1.41 FWHM) at 28.7 µm.
  - *(Decided 2026-11-23: `9017022` approved, with the multiple 2 and the 50-pixel minimum; see "Decisions".)*
- 2026-11-23: **CRETA's FWHM-scaled point-source cone, commit `2818075`: the change and three choices I made in it** (see M5, W2246).
  - **NIRSpec cubes keep r_ap × λ/λ_ap even when λ_ap lies in MIRI.** With NIRSpec's FWHM only "∝ λ", its absolute FWHM is unknown, so FWHM(λ_ap) from MIRI cannot set a NIRSpec cone. This keeps NIRSpec unchanged, as asked.
    - In a NIRSpec + MIRI point-source run the cone then steps at the join: with λ_ap = 5.4 µm, at 5.0 µm it is 0.953 r_ap in MIRI and 0.926 r_ap in NIRSpec (3%).
  - **A MIRI cube with `lambda_ap` below 4.9 µm stops with a `ValueError`**, rather than extrapolating Law et al. below MIRI. There, FWHM(λ_ap) would have to come from NIRSpec, which has no law.
    - It also stops a MIRI-only run with such a `lambda_ap`, which used to work with λ scaling. None of the shipped or work-folder parameter files has one.
  - **The boundary is MIRI MRS's shortest wavelength, 4.9 µm** (`MIRI_MRS_SHORTEST_UM`). Above MIRI's longest wavelength, Law et al. is extrapolated; no instrument covers that range.
  - *(Decided 2026-11-23: `2818075` approved with the three choices; see "Decisions". A NIRSpec FWHM law is still to be chosen; see "Later".)*
- 2026-11-23: **CRETA's fixed-width ring, commit `2383c67`: the change and three choices I made in it** (see M5, W2246).
  - **`ann_width` ≤ 0 with a point source stops with a `ValueError`.** The shipped parameter files have `ann_width = 0.0`, which point sources used to ignore. With a fixed-width ring, 0 would silently make every plane NaN.
  - **"No room" means the fitted inner edge lies inside the largest cone radius in that plane.** An edge exactly on the cone is allowed. With several aperture radii, the largest one counts.
  - **Messages:** CRETA prints the planes pulled in and those without room, per band. The under-20-pixels message no longer counts the no-room planes, which have their own.
  - Seen in the synthetic test: a ring pulled in to just outside the cone holds the PSF's wings, which lower the flux (a Gaussian: 0.7–1.5%). For W2246 the pulled-in rings stay at least 2.47 FWHM out.
  - *(Decided 2026-11-23: `2383c67` approved with the three choices; see "Decisions".)*
- 2026-11-23: **W2246's spectrum-only fit: choices before any fit** (see M5, "W2246's spectrum-only fit: the setup").
  - **z:** 4.601 ([CII]), 4.593 (UV and optical), or 4.6 (M3).
  - **Lines and opacity features:** every one in the range is masked (MASK = 1) in my W2246 tables, so only the continuum and the 3.3 µm PAH would be fitted. Paα, Paβ and Brα (broad in W2246) would stay in the residuals.
  - **Components the range cannot constrain:** CIR_TMP is free with CIR off (no effect); CLD is free but invisible. COO is visible only at its 100 K bound, at the red end. Fix or turn them off for a spectrum-only fit?
  - **WRM:** AGN-heated up to 300 K, it can emit far more than the data even at 1 µm, so it overlaps HOT. Keep its source and range?
  - **My W2246 settings or the shipped rules:**
    - the T ranges (COO 25–100 K, WRM 100–300 K, HOT 300–1027.2 K, against 3–50, 50–200 and 200–1750 K);
    - the optical-depth starts (1 or 4, against 0.1);
    - DSK_TAU's upper bound (2, against 0.5).
  - **Errors:** the channel-to-channel scatter is 2–6× CRETA's quoted errors. With the 1% floor it matches in ch3, but is 1.5–2× in ch1–ch2 and 3.4–3.8× in ch4-medium and ch4-long. The fit weights by these errors.
  - **Opt file:** `default_opt.cafe`.
  - *(Decided 2026-11-23: W2246's own setup, recorded under "Decisions" as "W2246's spectrum-only fit setup".)*
- 2026-11-23: **W2246's three unmasked lines: choices before the rerun** (see M5).
  - **The width cap:** `EPSGamma_LIN_N` = 400 km/s caps a single component's FWHM at 400 km/s, below Paβ's ~1,250 km/s in the first run's residual. Raising it in the copy affects only these three lines, since every other line stays masked. The new value is my choice.
  - **Paα:** `fit_spec`'s default drops it, because its starting amplitude at the instrumental width is ≤ 0. Keep it with `force_all_lines = True` in the run?
  - **Centres:** fixed at z = 4.601 (`FitWave0_LIN_N` False). Free them, and with what range (`EPSWave0_LIN_N`, 100 km/s now)?

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
- 2026-11-16: **`init_feats`' line selection depends on the noise.** It leaves out lines whose guessed peak is negative. On M4's S1 (R1's fit plus 1% noise) it left out three lines the truth has ([Al VI] 9.12 µm, [Ar V] 13.10 µm, the broad Na VIII 5.18 µm component; peaks 1.4–6.7 mJy) and kept two the truth lacks. Not acted on. *(2026-11-19: the peak estimate is now a profile fit over the line's core, with a continuum that avoids the other lines, commit `5e70c62`. The > 0 rule stays, and with it some dependence on the noise; see "Awaiting my OK", 2026-11-19.)*
- 2026-11-17: **The 0.5σ test in `check_fit_pars` also reaches opacity-feature peaks**, which are optical depths: it compares them with the (normalised) flux error at the feature's wavelength and sets those below half of it to 0. The units don't match, so the threshold has no meaning there; it only removes very small optical depths. No shipped setup fits opacity features (0 in R1 and R2). Not acted on.
- 2026-11-17: **The onion path in `check_fit_pars` looks up `HOT_WRM` and `WRM_COO` in the inpars**, where no shipped file has them, so with `Onion = True` it would stop with a KeyError (older code; `Onion = False` in all three opt files). Not acted on.
- 2026-11-17: **`PAH_FLX` only switches the PAH continuum component on or off.** The model uses `fPAH = jPAH`; the scaling by `PAH_FLX` is commented out (`cafe_lib.py`, PAH component). A free `PAH_FLX` would have no effect above 0. It is fixed at 1 in all 7 shipped inpars. Not acted on.
- 2026-11-17: **The expression exception keeps `WRM_TAU` free also when the PAH component is dropped** (`WRM_FLX` and `PAH_FLX` both 0), where it then has no effect. Not possible with the shipped inpars (`PAH_FLX` fixed at 1). Not acted on.
- 2026-11-17: **A `_FLX` or `_TAU` fixed at 0 in the inpars, with that component's other parameters (or MIX and COV) left free:** `check_fit_pars` fixes them only after the first fit, so that fit returns no error bars and one refit follows. No shipped inpars does this. Not acted on.
- 2026-11-17: **`flux0` is `np.interp` of one or two channels**, so their noise sets the scale of every `_FLX`. A channel ≤ 0 in a faint spaxel would stop that component from being positive: `_FLX` ≥ 0 times `flux0` ≤ 0 gives a component ≤ 0, which the model clips to 0. Not acted on (the `flux0` fix comes after M4 stage 2). *(Corrected 2026-11-18: every fit passes the data through `mask_spec`, which drops NaN channels and channels with flux < 0, so only an exact 0 can reach `flux0`; the noise point stands.)* *(2026-11-19: with the `mask_spec` fix, channels < 0 reach `flux0` again. Since `c071ab1` it is the median of 20 channels, which can be ≤ 0 in a faint spectrum or spaxel; see "Awaiting my OK", 2026-11-19.)* *(2026-11-19: `flux0` is now the median |flux| of the 20 channels, commit `688a02a`, so it is > 0 unless more than half of them are exactly 0.)*
- 2026-11-18: **`mask_spec` drops every channel with flux < 0** (`cafe_lib.py:91`, `:104`; also in GOALS `master`). In a faint spectrum or spaxel whose noise reaches below 0, the fit then sees only the channels where the noise is positive, so the data it fits are biased high, more so the fainter the source. Found while preparing the `flux0` fix (M4). Not acted on. *(2026-11-19: fixed on `dev`, commit `3fd7e7e`; GOALS bug G15.)*
- 2026-11-18: **R2's plain fit can end with COO and WRM pressed against their shared 50 K boundary** (M4 baseline). 2 of 10 fits end with WRM_TMP at its 50 K lower bound and COO_TMP at 48.3 K, χ² 2.6× the best (Δχ² 450,295), already in the first call. That is the direction of stage 1's COO/WRM swap (then about 3,000 higher), which the non-overlapping ranges now block at 50 K. None of stage 3's 30 R2 fits (same ranges, before the `flux0` fix) went there; 10 fits can't tell whether the `flux0` fix made it likelier. Not acted on (no more diagnostics in M4). *(2026-11-19: logged as M6's first item.)*
- 2026-11-19: **At S/N 1 per channel, the fitted continuum sits 2–4% below the data's mean**, the same before and after the `mask_spec` fix (fitted / data mean 0.956–0.978 in both; 3 fits each, `tests/mask_spec/`, synthetic λ² power law). χ²(fit) − χ²(truth) is −30 to +24 with 74–106 free parameters, so either the fit stops before its minimum (as in M4) or CAFE's components cannot follow a pure λ² power law; this test cannot tell which. Not acted on. *(2026-11-19, my reading: likely because the lines and PAHs, whose peaks can only be ≥ 0, absorb positive noise. Logged, not acted on.)*
- 2026-11-19: **Intrinsically broad lines in `init_feats`' selection** (`5e70c62`). The continuum windows start 2 instrumental FWHM from λ₀, so a line broader than the instrument has its own wings in them, and the line's selection rests on its narrow core. In R1 the broad Na VIII 5.18 µm component is no longer kept. Logged, not acted on (my decision, 2026-11-19).
- 2026-11-19: **Where `flux0`'s window is dominated by noise, `flux0` measures the noise, not the signal** (`688a02a`). The median |flux| of 20 channels whose S/N is ≪ 1 is about 0.67 σ, and `flux0` sets each `_FLX`'s starting flux in Jy (`_FLX` × `flux0`) and its upper limit (2 × `flux0`, all 7 shipped inpars).
  - In the faint test (`tests/flux0_abs/`, S/N 0.16 per channel at 24 µm), COO's `flux0` was 12.5–22.7 mJy, where COO's true flux at 24 µm is 3.74 mJy. So COO started at 2.2–3.9× its true flux, with its limit 6.7–12× above it.
  - Where the 20 channels are > 0 nothing changes. Elsewhere the start and the limit can only rise, since median |F| ≥ median F.
  - Only the start and the limit change, not the model. Not acted on.
- 2026-11-19: **`script/NIRSpec-MIRI_spec_script.py` (pre-sync folder, July 2023) reads `NGC7469_NIRSpec+MIRI_reg1_04arcsec.dat` with z = 0.0163, but the file is in the rest frame** (read it with z = 0; see "Later", NIRSpec + MIRI). The path is commented out in the script, so only a run that restores it is affected. Logged, not acted on (the pre-sync folder is read only).
- 2026-11-19: **R1 holds NIRSpec channels** (M5 step 1). The tutorial spectrum `NGC7469_SingleExt_r1.5as_MIRI.dat` contains 471 G395H channels at 4.957–5.270 µm (observed), interleaved with ch1-short's, stitched with the same chain. It was cut from a G395H + MIRI extraction at 4.957 µm.
  - In M4 these channels were fitted with `inpars_jwst_miri_AGN.ini`, so the line profiles there used MIRI ch1's resolving power instead of G395H's.
  - Not acted on.
- 2026-11-19: **The stitching reference sets the absolute flux level** (M5 step 1). In NGC7469's 1.5″ extraction the MIRI band-to-band ratios multiply to 0.87 from ch1-short to ch4-long. So stitching to ch1-short puts every MIRI band 15.4% above R1 (stitched to ch4-long), and the NIRSpec bands 13–18% above their own calibration.
  - With photometry (M5) the absolute level matters; which band, if any, is right is not known.
  - The NIRSpec–MIRI join (1.18 at 4.90–5.28 µm) is a level difference between the two instruments' reductions: the aperture, at one sky position, changes it by ≤ 0.4%. Not acted on.
- 2026-11-19: **NIRSpec's and MIRI's WCS place NGC7469's nucleus 0.19″ apart** (the `wcsfix` NIRSpec cubes; 0.60″ with the December 2022 ones), measured with CRETA's centring. For a 1.5″ aperture this changes the flux by ≤ 0.4%; for small apertures it would matter. Not acted on.
- 2026-11-19: **CRETA's "contains all NaNs" warning in `singleExtraction` checks only the first plane of each band** (`final_apers` holds plane 0 of each band). It fires for bands whose first plane is NaN; NGC7469's three NIRSpec bands are 92% valid. For the clean-up list.
- 2026-11-19: **(a) CRETA's single-extraction DQ is the maximum over the square around the aperture, not over the circle** (`getApertureDQList`, `cube_preproc.py`: `np.max(mask.cutout(DQ))`). Not fixed yet (proposal under "Awaiting my OK"). *(Fixed 2026-11-20, commit `a1ff60a`.)*
  - Where the square's corners reach the flagged edge of a cube's field (DQ 513), every channel is flagged, and CAFE's `mask_spec` drops every channel with DQ ≠ 0.
  - In NGC7469's 1.5″ extraction (M5 step 1) this flags all of ch1-short and ch1-long, 948 of 971 ch1-medium channels and 31 channels per NIRSpec grating. None of them has a flagged pixel in the circle: CRETA turns flagged pixels into NaN, and their fluxes are finite.
  - Not affected: R1 (`.dat`, no DQ); R2 (DQ ≠ 0 only on its NaN channels); CRETA's grid extraction, which sums the DQ over the circle.
- 2026-11-19: **(b) CAFE gives each line the resolving power of the first table, in the inpars' order, whose range contains the line, not that of the band its data come from** (`init_feats`, `cafe_helper.py`). Not fixed yet (proposal under "Awaiting my OK"). *(Fixed 2026-11-20 for spectra with band names, commit `9e8ccd5`. R1 has none and keeps today's rule, so its four lines below are unchanged.)*
  - The tables' ranges are wider than the bands' data, and narrow-line widths are fixed at that resolving power (`FitGamma_LIN_N = False`).
  - NIRSpec + MIRI (M5 step 2): G395H's table (to 6.00 µm) gives [S VII] 5.23, [Si VIII] 5.29, [Fe II] 5.34, [Fe VIII] 5.45, [Mg VII] 5.50, H₂ S(7) 5.51 and [Mg V] 5.61 µm (rest), on ch1-short data, a resolving power 10–13% too high, and [Fe II] 5.67 µm (ch1-medium) 28% too high.
  - Within MIRI, so also in R1: [P III] 17.89 and [Fe II] 17.94 µm +80% (ch3-long's table on ch4-short data), [Ne V] 24.32 µm +12%, H I 8.67 µm +11%.
- 2026-11-19: **(c) The shipped `inpars_jwst_nirspec-miri_AGN.ini` heats HOT with the ISRF** (`Source_HOT = 'ISRF'`), where `inpars_jwst_miri_AGN.ini` uses `'AGN'`. Apart from `resolutions`, this is the only difference between the two files. Not acted on.
- 2026-11-19: **In the NIRSpec + MIRI fit, HOT_TMP ends at its upper bound (1027.2) in all 10 fits, and the AGN disc takes 46% of the 5–6 µm continuum** (M5 step 2). STR ends at 0 and STB_010 at 1 (all 10 Myr). With the 1–5 µm data the hot dust reaches the top of its range and the disc fills in. HOT's range is my decision (kept in M4). Not acted on.
- 2026-11-19: **ch4-long holds 27% of the NIRSpec + MIRI fit's χ²** (χ²/N 79; median residual −2.3%, a dip and a rise at 24–28 µm), as channel 4C held 39% of R1's at state B. Not acted on.
- 2026-11-20: **`gauss_prof` adds a constant outside each Gaussian** (`component_model.py`). It samples the profile at −5 … +4.8σ and `np.interp` holds the end values beyond, so every line adds 3.7×10⁻⁶ of its peak at all shorter wavelengths and 9.9×10⁻⁶ at all longer ones. The fit's line model (`fLIN`) and the Gaussian opacities (`tau_gopc`) use it, and so do `init_feats`' peak guesses.
  - In M5 step 2's best fit (126 line components, peaks summing to 18.6 Jy) the constant is 0.14% of the flux in G140H (median; max 0.30%), 0.08% in G235H, 0.05% in G395H and ≤ 0.04% in MIRI: below the 1% error floor. Check: `tests/M5/line_pedestal_check.py` (work folder). Not acted on.
- 2026-11-20: **Carbonaceous grains are removed at 1400 K, the silicates' sublimation temperature** (`grainSizeDF`, `dustgrainfunc.py`). The function defines `tSubSil = 1400.` and `sSubCar = 1750.` but cuts both species at `tSubSil`; `sSubCar` is never used. The same in GOALS `master`, since its first commit. Probably meant 1750 K for carbon; that would be a change in the dust model, so a physics choice (see "Awaiting my OK"). Not acted on. *(Fixed 2026-11-20, commit `076adbd`: carbon grains are removed above 1750 K, silicates above 1400 K.)*
- 2026-11-20: **Above T_bb ≈ 1450 K the HOT component is a flat F_ν.** At the 1521.3 K grid point no grain survives sublimation, so `j` is the 10⁻²⁰⁰ floor at every wavelength. Normalised at λ₀, the component then has the same F_ν everywhere. Between 1322 and 1521 K its shape comes from interpolating toward that empty grid point. This matters only if HOT's upper bound goes above about 1322 K. Not acted on. *(Moved up 2026-11-20 by `076adbd`, see the next entry.)*
- 2026-11-20: **With carbon kept to 1750 K, HOT has no emission at the grid's top (1750 K) and flattens between 1521.3 and 1750 K.** The largest carbon grains sit at about 1.02 T_bb, so at T_bb = 1750 K every grain is above its sublimation temperature. The 1521.3 K grid point keeps 36% of the carbon mass (AGN SED). Between the two, the log-j interpolation gives the 1521.3 K shape raised to a power that falls to 0 at 1750 K: F_ν(2 µm)/F_ν(5 µm) is 3.31 at 1521.3 K, 2.15 at 1600 K and 1 at 1750 K (AGN; `tests/M5/carbon_sublimation_test.py`). So the shapes HOT takes above 1521.3 K are not set by the grain model. Matters for HOT's range (see "Awaiting my OK"). In the NIRSpec + MIRI fits with the bound at 1750 K, HOT_TMP ends just below 1521.3 K (M5). Not acted on.
- 2026-11-20: **`inpars_jwst_NGC7469_NIRSpec+MIRI_reg.ini` cannot be loaded.** It is in an older format than the other inpars, unchanged since GOALS' first commit (`4e667dd`) apart from M4's temperature bounds and `9ffc4b7`. Only a commented-out line of `script/NIRSpec-MIRI_spec_script.py` names it. *(Corrected 2026-11-20: this entry first gave only the last cause below. In fact the fit stops at the first.)*
  - `MODULES & TABLES` has no `PAH_INPUT` or `GOPACITIES_INPUT`: `make_parobj` stops there with `KeyError: 'PAH_INPUT'`.
  - Its line tables, `lines.atomic_jwst.txt`, `lines.molecular.txt` and `lines.H_recombination.txt`, are not in `CAFE/tables/` and never were in the history.
  - `PAH & LINE OPTIONS` lacks `FitWave0_OPC`, `FitGamma_OPC`, `FitVgrad`, `EPSWave0_OPC`, `EPSGamma_OPC`, `EPSPeak_OPC` and `EPSVgrad`, which `make_feat_pars` reads. The continuum lacks `CORV_TAU` and has the old `ADD_TAU`.
  - `read_inst` upper-cases the inpars' table names but not the file names, so `JWST_NIRSPEC_G395H` never matches `R_JWST_NIRSpec_G395H.txt`.
  - Not acted on (see "Awaiting my OK"). On the M7 clean-up list (my decision, 2026-11-20).
- 2026-11-20: **The AGN disc (DSK) takes the near-power-law part of the continuum** (46% of 5–6 µm in M5 step 2 and `hot1750`). A limitation of CAFE's dust components: a temperature gradient, which looks like a power law, has no component of its own. Not something to fix (my decision, 2026-11-20).
- 2026-11-22: **With DSK free, HOT_TAU and COO_TAU still end at 8–9 despite the 0.1 starts** (NGC7469 NIRSpec + MIRI, `dskfree`: HOT_TAU 8.30, COO_TAU 8.93; `hot1750`: 8.24, 9.18). Like DSK's role, this is the single-temperature dust components being bent toward a power law. Part of the limitation above, not acted on (my decision, 2026-11-22).
- 2026-11-22: **The NGC7469 NIRSpec + MIRI fits have two end states 2% apart in χ²** (M5, `hot1750` and `dskfree`). One has STR at 0 and DSK_TAU 0.09 (`hot1750`'s best, 200,549.87). The other has STR on and DSK_TAU 0.39 (3,924 higher). With the 0.1 starts, all three `dskfree` fits reach the STR-on state; `hot1750`'s starts reached the lower state in 7 of 10. Not acted on (my decision, 2026-11-22).
- 2026-11-23: **W2246's MIRI cubes are negative around W2246 in ch1-short and ch1-long, although master background subtracted.** This holds for both `stage3` (pipeline 1.13.4) and MAST `c1003` (3.0.0), both with `S_MSBSUB = COMPLETE`.
  - Box medians around W2246: −6.6 and −3.7 MJy/sr per plane in stage3, −6.0 and −4.9 in `c1003`.
  - In the 0.5″ cone this gives negative fluxes (ch1-short median −0.042 mJy). Not acted on.
- 2026-11-23: **CRETA's centring gives up on faint sources** (`userCentroid`, `cube_preproc.py`).
  - When the sum of its 11×11-pixel box (5 planes) is ≤ 0, NaN or inf, it returns the start position. It only prints a message, and the extraction goes on, with `Centering: True` in its metadata.
  - W2246: ch1-short and ch1-long, in both cube sets. Not acted on.
- 2026-11-23: **CRETA's stitching takes ratios of fluxes near 0** (`stitchSpectrum`).
  - Each band's factor is a product of overlap ratios. A ratio of two near-zero mean fluxes is meaningless, and a negative one flips the sign of every band scaled through it.
  - W2246: ch1-medium → ch1-long, −1.68 (stage3) and −5.32 (`c1003`). Not acted on.
- 2026-11-23: **CRETA's background annulus is fixed in arcsec** (`doBackgroundSubtraction`, `cube_handler.py`).
  - One annulus (`r_ann_in`, `ann_width`) is used at every wavelength and in every cube, even for a point source. The lines that would scale it with wavelength for point sources are commented out.
  - With a cone that grows with wavelength, the annulus must start beyond the largest cone radius and still fit inside the smallest field.
  - W2246 (`c1003`, 0.5″ cone at 5.4 µm, centred at 8.0 µm): the cone reaches 2.657″ at 28.7 µm, while the largest circle inside the field is 1.89–1.96″ in ch1, 2.30–2.33″ in ch2 and 2.50–2.62″ in ch3. No annulus fits; each band alone has room for one. Check: `tests/M5/W2246/annulus_check.py`. Not acted on. *(2026-11-23: changed for point sources by commit `9017022`, awaiting my review; see "Awaiting my OK".)*
- 2026-11-23: **MAST `c1003` ch4-long of W2246 goes negative beyond 27 µm** (median −94 mJy at 27.5–28 µm, −350 mJy at 28–28.5 µm in the 0.5″ cone). Stage3 is negative only at 28–28.5 µm (−75 mJy). Not acted on. *(2026-11-23: with the local annulus, ch4-long beyond 27 µm is positive; see M5, W2246.)*
- 2026-11-23: **WISE W4 overestimates red sources** (WISE All-Sky Explanatory Supplement, sec. IV.4.h, last updated 2017-08-07; read on IRSA).
  - For F_ν ∝ ν^−α with α ≥ 1, the catalogued W4 flux needs about an 8–10% correction downward; the Supplement's example decreases it by 8%. The stated cause is the uncertain calibration of W4's relative spectral response.
  - Brown et al. (2014, PASA 31, 49) explain the residuals by scaling the W4 response's wavelengths by 1.033, which puts W4's effective wavelength at 22.8 µm (nominal isophotal 22.08 µm). They caution that this may not be unique.
  - The Supplement presents the flux correction and the wavelength shift as ways of handling the same discrepancy, so apply one, not both (my reading; the page does not say so explicitly).
  - Wright et al. (2010) also found red sources too faint in W3, by 17%. The Supplement's correction is for W4 only. Not acted on.
  - For W2246 (α = 2.1 at 20–24 µm), the 22 µm ratio becomes 0.76–0.77 either way (M5). To be handled with M5's photometry conventions (my decision, 2026-11-23).
  - *(2026-11-23: for W2246 this rests on the inference that its 22.0 µm point is WISE W4; W2246.txt's bands and origin are unknown. W2246 gets no W4 correction; see "Decisions".)*
- 2026-11-20: **`grainEQTemp` finds each grain's T_eq by inverting a table built on the T_bb values it is given** (`T = T_bb`, `interp1d` in log, extrapolating beyond the ends). So what `grainSizeDF` keeps at one T_bb depends on the other T_bb values in the same call. Example (AGN, carbon cut at 1400 K): 0.317 of the carbon mass at 1148.3 K on the fit's 30-point grid, 0.359 with T_bb = [996.9, 1027.2, 1148.3].
  - The fit always passes its fixed grid. Adding points to it leaves the values at its points unchanged (996.9–1521.3 K, both cuts), so the fit is not affected. Only direct calls with a short T_bb list are. Not acted on.
- 2026-11-20: **The inpars comment `_HOT_TMP = 571.6 -> <HOT_TMP> = 1250K` is not reproduced** by the grain model. At T_bb = 571.6 K the mass-weighted mean T_eq of the surviving grains is 1196 K (silicates) and 926 K (carbon) for the AGN SED, and 1015 K and 988 K for the ISRF. For the clean-up list.
- 2026-11-17: **The cool and warm dust components can swap temperatures**: both TMP bounds are [0, ∞) in the shipped inpars, with no order between them. In R2 (M4 stage 2), 7 of 10 stage 1 fits end with COO at 59.4 K and WRM at 29.5 K, about 3,000 higher in χ² than the other state, because `PAH_TAU = WRM_TAU` makes the two labellings differ. Not acted on (see "Awaiting my OK").
- 2026-11-17: **The restart test in M4 stage 2 (stop when a restart lowers χ² by < 1) ended R1's chains while they were still falling ~2 per restart.** A diagnostic setting only; R1's minimum along the valley is not reached.
- 2026-11-17: **Line components at their lower bound stay there.** In R2, the end points within the better minimum differ by which narrow or broad component of H I Humphreys 9–6 (5.91 µm) and 7–6 (12.37 µm) sits at 0; restarts don't bring it back. TRF's step shrinks for parameters near a bound, which may hold them there (not tested). Not acted on.
- 2026-11-17: **In R2, two first `minimize` calls end on the evaluation limit** (47,200, j = 2 and 4, at χ² 4.1–4.7×10⁵, also in stage 1). The refit loop (or a restart) rescues them. Not acted on.
- 2026-11-18: **G14 affected my pre-sync fits.** In the 269 `fitpars.ini` files of my pre-sync folder (121 distinct fits), 51 fits have a free temperature on a G14 jump. CLD_TMP sits on the 6.351 K jump in 42 of the 91 fits where it was free, mostly in the CYGNUS (Spitzer U/LIRG) sample; the others are COO at 19.12 K, WRM at 83.38, 119.4 and 141.5 K, and HOT at several jumps (119–865 K). Those results would change with the fix. Not acted on.
