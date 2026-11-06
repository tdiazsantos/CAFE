# CAFE — design notes

This describes **GOALS-survey/CAFE `master` @ `39e298b`**. It was written from a first read of the code, not a full review. M1 must verify it and correct anything wrong, and it should be kept current as the code changes.

## What the code does
CAFE (Continuum And Feature Extraction) decomposes infrared spectra into physical components by least-squares fitting with lmfit. The inputs are JWST NIRSpec and MIRI or Spitzer IRS spectra, optionally with photometry. The components are:
- dust continua (with their heating sources);
- stellar, starburst and AGN-disk emission;
- PAH features;
- emission lines;
- absorption features.

The repo contains two packages:
- **CRETA** (CAFE Region Extraction Tool Automaton) extracts spectra from JWST IFU cubes. It makes either a single-aperture 1D spectrum or a grid of apertures, written out as a cube.
- **CAFE** fits a single spectrum (`specmod`) or every spaxel of a cube (`cubemod`).

## Repository layout

### CAFE/ (code)
- `cafe.py`
  - User entry points: `specmod` and `cubemod`.
  - `cafe_grinder()`: the fit driver.
  - `plot_cafefit()`.
- `cafe_helper.py`
  - `CAFE_param_generator`: builds lmfit `Parameters` from the inpars/opt files and the spectrum, including the initial guesses for features.
  - `CAFE_prof_generator`: loads tables and builds the unscaled continuum profiles (`cont_profs`).
  - `CAFE_cube_generator`: parameter cubes.
  - `parobj2parcube` / `parcube2parobj`: convert between a parameter object and a parameter cube.
- `cafe_lib.py`
  - Model and fit machinery: `trim_overlapping`, `mask_spec`, `chisquare` (the objective), `get_model_fluxes` (model evaluation, about 630 lines), `get_feat_pars`, `synphot`, and `check_fit_pars` (the accept-or-refit decision).
  - Plotting: `cafeplot` and others.
- `cafe_io.py`
  - `cafe_io` class:
    - paths (`init_paths`);
    - CRETA cube and FITS readers;
    - instrument resolving power (`read_inst`);
    - `.ini` read and write;
    - PAH and line tables;
    - ASDF output.
- `component_model.py`: feature profiles. Drude for PAHs, Gauss for lines, and integrated Drude fluxes.
- `dustgrainfunc.py`: dust-grain emissivities.
- `sourceSED.py`: heating-source SEDs (ISRF, AGN, starburst from SB99), the Planck function and the opacity loader.
- `get_fit_sequence.py`: decides the order in which spaxels are fitted, and which already-fitted neighbour initialises each one.
- `mathfunc.py`: small helpers that duplicate `spline` and `intTab` in cafe_lib.

### CAFE/ (inputs, tables and outputs)
- `inp_parfiles/*.ini`: model definition per setup ("inpars").
- `opt_parfiles/*.cafe`: fit and run options ("inopts").
- `tables/`: grain optical constants, opacities (`opacity/`), line lists, PAH templates, SB99 SEDs and instrument resolving power (`resolving_power/`).
- `output/`: example output for NGC7469.

### CRETA/
- `creta.py`: the `creta` class, with `singleExtraction` and `gridExtraction`.
- `cube_handler.py`: one sub-band cube.
- `cube_preproc.py`: aperture photometry, centring and stitching.
- `userAPI.py`: file handling and FITS-cube writers.
- `param_files/`, `PSF_centroids/`, `PSF_infaps/`.

### Other folders
- `notebooks/CAFE_tutorial_NGC7469_1D.ipynb`: tutorial. It downloads its input spectrum.
- `script/`: example scripts.
- `docs/`: Sphinx docs (readthedocs).

## Configuration
Each fit reads two files, both with `cafe_io.read_inifile`.

**inpars (`.ini`)** has these sections:
- `[METADATA]`
- `[COMPONENT SOURCE SEDs]`
- `[MODULES & TABLES]`, which includes `RESOLUTIONS` (instrument resolving-power tables)
- `[PAH & LINE OPTIONS]`
- `[CONTINUA INITIAL VALUES AND OPTIONS]`. Each line is `value, vary[, min, max[, expr]]`.

**inopts (`.cafe`)** has these sections:
- `[PATHS]`
- `[FIT OPTIONS]`: `FTOL`, `NPROC`, `FIT_CHK`, `MAX_LOOPS`, …
- `[SWITCHES]`
- `[OUTPUT FILE OPTIONS]`
- `[PLOT OPTIONS]`
- `[MODEL OPTIONS]`, e.g. `FITPHOT`
- `[REFERENCE WAVELENGTHS]`

## Parameter naming
- **Continuum:** `<COMP>_<QTY>`.
  - `COMP` is one of:
    - dust: `CIR`, `CLD`, `COO`, `WRM`, `HOT`;
    - stars: `STR`;
    - starburst: `STB`;
    - AGN disk: `DSK`;
    - PAH continuum scaling: `PAH`.
  - `QTY` is `FLX`, `TMP`, `TAU`, `MIX` or `COV`.
  - There are a few others, e.g. `STB_100`, `STB_010`, `HOT_WRM`, `WRM_COO`. See `make_cont_pars`.
  - `_FLX` is a **ratio to the observed flux at the component's reference wavelength** (`flux0`), not an absolute flux.
- **Absorption:** `ICE3_TAU`, `ICE6_TAU`, `CO2_TAU`, `HAC_TAU`, `CORV_TAU`, `CRYSI_233_TAU`.
- **Features:**
  - lines: `g_<name><comp>_{Wave,Gamma,Peak}`;
  - PAHs: `d<name>…`;
  - opacity features: `o_<name>…`.
  - `_Peak` is in flux units.
  - Commit `09f5df6` renamed `'gamma'`→`'width'` only in the feature lists in cafe.py. The parameter suffix is still `_Gamma`.
- **`VGRAD`:** a global velocity shift in km/s, applied to the feature wavelengths.

## 1D flow (`specmod`)
1. **`read_spec(file, z, …)`**
   - Reads `.txt`/`.dat`, a CRETA `.csv`, or a CRETA `.fits` (`extract='Flux_st'` is the stitched spectrum).
   - Trims overlapping band edges (`trim_overlapping`).
   - Moves to the rest frame: `wave/(1+z)`, `flux/(1+z)`, `flux_unc/(1+z)`.
   - Side effect: when the input is not a CRETA cube, writes `./dummy.fits` into the current directory.
2. **`read_phot(...)`**: optional.
3. **`fit_spec(inparfile, optfile)`**
   1. `mask_spec` produces `spec_dict` with `wave`, `flux`, `flux_unc` and `weight`.
   2. `CAFE_param_generator.make_parobj(get_all=True)` sets the parcube layout. `make_parobj()` then builds the parameters actually fitted.
   3. `CAFE_prof_generator.make_cont_profs()` builds `cont_profs`, which holds:
      - `waveMod`, `wave0` and `flux0`;
      - grain emissivities and opacities;
      - source SEDs;
      - filters.
   4. `cafe_grinder` runs `lm.Minimizer(chisquare, method='least_squares', ftol=FTOL, max_nfev=200*(npar+1))`.
      - `check_fit_pars` then accepts the fit or asks for a refit.
      - On a refit, the scaling parameters (`Peak`, `FLX`, `TMP`, `TAU`, `RAT`) are perturbed by 1% and the fit is repeated, up to `MAX_LOOPS` times.
   5. `parobj2parcube` stores the results. `get_model_fluxes(comps=True)` gives the component spectra.
   6. `save_products` writes the outputs.
4. **Outputs:** `<name>_parcube.fits`, the continuum cube, `_fitpars.ini`, `_cafefit.asdf`, `_fitfigure.png`, `_pahtable.ecsv` and `_linetable.ecsv`.

## Cube flow (`cubemod`), the M2 target
1. **`read_cube`**
   - Reads a CRETA cube (`cafe_io.read_cretacube`). Wavelengths must be in µm.
   - Trims overlaps and moves to the rest frame, as in 1D.
2. **`fit_cube(inparfile, optfile, output_path, init_parcube, force_all_lines, pattern)`**
   1. **"SNR" image** = `nansum(fluxes[10:20])`. This is a flux sum used as the SNR proxy.
   2. **`get_fit_sequence(image, sorting_seq=pattern)`** returns:
      - `ind_seq`: the order in which spaxels are fitted, as (y, x);
      - `ref_ind_seq`: for each spaxel, the already-fitted neighbour (within 1.5 px, highest "SNR") that initialises it.
      - The modes are `'snr'` and `'spiral'`.
   3. The parcube is created with all possible parameters (`CAFE_cube_generator.make_parcube`).
   4. **The spaxel loop is strictly sequential.** For each spaxel:
      - `mask_spec` gets its spectrum;
      - a new `CAFE_param_generator` runs `make_parobj`;
      - a **new `CAFE_prof_generator` runs `make_cont_profs`, re-reading the tables and rebuilding every continuum profile**;
      - if this is not the first spaxel, `parcube2parobj` takes the values of the reference spaxel and `make_parobj(parobj_update=…)` resets vary flags and limits around them;
      - `cafe_grinder` fits it;
      - `parobj2parcube` stores the result.
   5. Writes the parcube FITS and the `_fitpars.ini` of the first (highest-"SNR") spaxel.
3. **Facts relevant to performance:**
   - Tables are read and profiles rebuilt for every spaxel. Only `flux0`, the observed flux at the reference wavelengths, really depends on the spaxel.
   - `NPROC` is read in `cafe_grinder` but never used.
   - The neighbour initialisation creates a dependency between spaxels. Any parallel scheme must either keep each spaxel's initialisation source, or count as a change in results.
   - `least_squares` estimates the Jacobian numerically, so the cost is about (npar+1) evaluations of `get_model_fluxes` per iteration, times the number of refit loops.

## Conventions and invariants
- Wavelengths are in µm and in the rest frame after reading. Fluxes are in Jy (`Spectrum1D(..., flux=...*u.Jy)`). The redshift is stored on the object.
- Parcube: FITS image HDUs (e.g. `VALUE`) with shape `(n_params, ny, nx)`. In the tutorial, `parcube['VALUE'].data[-1,0,0]` is `VGRAD`.
- Index order is mixed:
  - `ind_seq` and `ref_ind_seq` are (y, x);
  - several helpers take `(x, y)`; see comments such as "indexation is (x=1,y=0)".
  - Check carefully when touching the loop.
- `cafe_dir` points to the CAFE package folder, and tables are found through it and `[PATHS]`. The tutorial uses `site-packages`. To compare versions side by side, pass each checkout's `CAFE/` path.
- Dependencies in `setup.py`: astropy, lmfit, matplotlib, numpy, pandas, photutils, scipy, specutils, ipykernel. `asdf` is used but not listed.
- GOALS master needs `scipy.integrate.simpson` and `trapezoid`. The fork and local versions still use `simps` and `np.trapz`.
