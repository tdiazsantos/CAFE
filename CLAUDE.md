# CLAUDE.md — CAFE project rules

## 0. My personal rules come first
- My personal rules in `~/.claude/CLAUDE.md` apply here **in full**. Claude Code loads them automatically. At the start of every session, check that they are in your context. If they are not, stop and tell me.
- The rules below add project specifics. They may only make the personal rules stricter. If a project rule ever seems to relax a personal rule, the personal rule wins and you ask me.

## 1. Start of every session
- Read `PROJECT_BRIEF.md` (goal, milestones, current state, decisions & biases) and `DESIGN.md` (how the code works).
- Work only on the current milestone, in order. M0 is the starting point and needs no approval. **Start every later milestone only after I explicitly approve it.** Finish and test each milestone, then stop and wait.

## 2. Git and GitHub
- Remotes: `origin` = my fork `tdiazsantos/CAFE`; `upstream` = `GOALS-survey/CAFE`.
- Ask before every `git push`, to any remote. Also ask before creating or pushing tags, deleting branches, `rebase`/`reset` of anything already pushed, any `--force`, and renaming, moving or deleting files or folders.
- **Review of every code change** (decided 2026-11-14). For every code change, on any branch, show me:
  - the full diff, hunk by hunk;
  - for each change, a short paragraph on the reason for it (what the problem was) and how it is addressed.

  Nothing is pushed and no next group starts until I approve it. For anything going to GOALS, the stricter rule below also applies.
- **GOALS (`upstream`) is strictly protected.** I have push rights there, but:
  - Never push to `upstream`. Never merge, close or approve anything on GOALS (`gh pr merge` is forbidden).
  - Nothing you wrote, ported, edited or reformatted reaches GOALS until I have reviewed and approved it **line by line**. Before any PR to GOALS, show me the full diff against `upstream/master`, hunk by hunk, and wait for my approval of each hunk. If anything changes after my approval, show me the changed lines again.
  - Only after that, ask explicitly: "Open PR <branch> → GOALS-survey/CAFE?" and wait for a clear yes.
  - Branches meant for GOALS start from `upstream/master` and never contain the project files (`CLAUDE.md`, `PROJECT_BRIEF.md`, `DESIGN.md`, environment files).
- **No more pushes or PRs to GOALS** (decided 2026-11-14).
  - Fixes to GOALS bugs go only into `dev` on my fork.
  - My fork's `master` stays equal to GOALS `master`.
  - The protections above stay in force.
- **Authorship until M1 is complete.** Every commit, tag, branch and PR text, up to and including the M1 freeze, is mine alone. That means:
  - my git identity;
  - no `Co-Authored-By` trailer, no "Generated with Claude Code" line, no session links.

  `.claude/settings.local.json` (local, not tracked) sets the attribution for this folder. Since I approved M3 (2026-11-14), commit attribution is on and PR attribution is off: `{"attribution": {"pr": ""}}`. Never change my git config (`user.name`, `user.email`). Before every push, check that I am the author and committer of every commit in the range, and that only commits the next rule allows carry a Claude trailer.
- **Claude co-authorship after M1** (decided 2026-11-06):
  - Nothing that goes to GOALS ever shows Claude as co-author: no Claude trailer in commits, and no Claude attribution in PR titles or PR descriptions. This includes M2.
  - Co-authorship applies since M3, and only to commits that stay on my fork.
  - If a change made with co-authorship later goes to GOALS, make the commits for the GOALS PR fresh from `upstream/master`, without any Claude trailer, and check every commit for Claude trailers before pushing.
- Stage files by explicit path only. **Never** use `git add -A`, `git add .` or `git commit -a`. The pre-sync folder holds many untracked personal and data files.
- Commit in small steps, one logical change per commit, with plain messages that say what changed and why.

## 3. Minimal changes in M1
- In M1 you may change code for exactly two reasons:
  (a) porting my own uncommitted local edits;
  (b) fixing a confirmed bug that breaks the normal workflow.
  Each change must be the smallest diff that does the job.
- Not allowed in M1: reformatting, refactoring, renaming, style or comment clean-up, removing old commented-out code, dependency changes, new features, or any "while I'm here" improvement. List these as findings for later milestones instead.
- Old commented-out or debug code in the existing files is not yours to clean in M1. Nothing you add may be commented-out or debug code, though (personal rule). When porting my local edits, leave out debugging leftovers (e.g. `import ipdb`) and point out every omission to me.
- Ported lines follow the style of the file they land in (GOALS reformatted several files). Touch no other lines.
- Every bug fix: first show the failing case, then the fix, then the test. Use synthetic data with known truth when the bug is in the physics or the numerics (personal rule).

## 4. Physics and numbers
- Personal rules: ask before any physics choice; physics decides, cost never does.
- In this project that means: never change fit settings (`FTOL`, `MAX_LOOPS`, `FIT_CHK`, `max_nfev`, fit method), parameter defaults, bounds or expressions, tables, wavelength or temperature grids, or model components to make something faster, simpler or more convenient. Report costs as information only.
- Comparison tolerances for regression tests are my decision. Propose them, with reasons, and wait for my OK.
- Respect the units and conventions in `DESIGN.md`. If you find the docs or the code inconsistent, flag it.
- **CAFE's units are fixed** (decided 2026-11-15): fluxes in Jy, wavelengths in µm. Never describe anything as depending on "flux units". When a result changes with the flux scale, describe it as depending on the source's flux level (brightness).

## 5. Folders
- **Project folder:** the repo. Until the end of M1 that is `/Users/tanio/Sync/pywork/CAFE` (my pre-sync folder). After the freeze it is the fresh clone at the same path. It holds code and project files only.
- **Work folder:** `/Users/tanio/pywork/cafe_work` holds comparison clones and worktrees, downloaded data, regression and profiling runs, and scratch scripts. Large generated data goes here, never into the repo.
- **Conda envs:** `~/miniforge3/envs` (`cafe-dev`, `cafe-legacy`).
- **Data folders (read only):** `/Volumes/Gluon/lowz/goals/jwst/miri/mrs/data` and `/Volumes/Gluon/lowz/goals/jwst/nirspec/ifu/data`; for W2246, `/Volumes/Photon/highz/hotdogs/jwst/w2246/miri/mrs/stage3`, `/Volumes/Photon/highz/hotdogs/jwst/w2246/miri/mrs/mast/202611` and `/Volumes/Photon/highz/hotdogs/jwst/w2246/nirspec/ifu/processed`. Anything derived from them, such as CRETA extractions and fit outputs, goes to the work folder.
- **Pre-sync folder** (my old working copy; after the freeze: `/Users/tanio/Sync/pywork/CAFE_presync_2026-11`): read only.
- Never write into data folders inside the repo (`CAFE/input`, `CAFE/output`, `CRETA/data`, `CRETA/extractions`, notebooks folders) unless I name an output folder there. Run code with the work folder as the current directory, because some CAFE functions write files into the current directory (e.g. `read_spec` writes `./dummy.fits`).
- **Tool temp and caches:** pip, conda/mamba, git and Python may write to the system temp folder and to their own caches (e.g. `~/Library/Caches`, `~/miniforge3/pkgs`). That's allowed. Your own scratch files still go only to the work folder.
- Write nowhere else without asking.
- `/Users/tanio/Sync` is synced by Syncthing. Keep churn inside the repo low: no envs, no scratch files, no large outputs there.

## 6. Environments and running code
- `cafe-dev`: Python 3.12 with the current conda-forge stack (numpy, scipy, astropy, specutils, lmfit, photutils, matplotlib, pandas, asdf). This is for GOALS master and all new work.
- `cafe-legacy`: numpy<2 and scipy<1.14 with matching versions. It runs the fork and local versions unchanged, because they call `scipy.integrate.simps` and `np.trapz`.
- Environment files: `environment-dev.yml` and `environment-legacy.yml` in the project folder. They are project files and never go to GOALS.
- To run a specific version, use `PYTHONPATH=<checkout>` with the matching env, and pass `cafe_dir=<checkout>/CAFE/` to `specmod`/`cubemod`. Don't reinstall packages to switch versions.
- Record the exact commands you use (env creation, test runs, regression runs) in `PROJECT_BRIEF.md` → "Commands" once they work.

## 7. Decisions and biases
- Biases, decisions and defaults awaiting my OK go into `PROJECT_BRIEF.md` → "Decisions & biases", dated (personal rule). Record a decision there only after I have approved it.
- If something is unclear or ambiguous, ask before acting (personal rule).

## 8. Bringing in my local changes (decided 2026-11-14)
- Faithfulness to my old code is not a goal. Write each change in the simplest form that gives the same result (personal rule on simplicity).
- If my old code can be replaced by something shorter, or by an existing NumPy, astropy or lmfit function, do that, and say so in the change's paragraph (review rule, §2).

## 9. Naming (decided 2026-11-15)
- Variable names must identify what they hold. No generic names such as `r_in`, `width`, `s`, `dl`, `norm` or `factor`.
- This applies to all code written or changed from now on, and to the code added in M3.
- Generic names elsewhere in CAFE and CRETA go on the clean-up list. Don't change them in passing.
- The more fundamental a variable is, the less explicit its name needs to be (added 2026-11-15).
  - Core names such as `wave`, `flux`, `z` or `params` stay as they are. Natural derived names stay too, e.g. `par` for one item of `params`.
  - Explicit names are for secondary variables: helpers, indices and intermediate results.
  - The same quantity keeps the same name across functions.
  - Don't propose renaming core or natural names.

## 10. Test reports (decided 2026-11-15)
- Every test report starts with its setup: the spectrum file and z, the inpars and opt files, the photometry with its values and origin, and the number of free parameters.
- The fake-photometry setup is only for functional checks that compare code versions on identical input. Never use it to judge parameter values or fit stability.
