# CAFE — design notes

This describes my fork's **`dev`** branch: GOALS-survey/CAFE `master` plus the M3 changes (2026-11-14 to 2026-11-15, up to `1e66caf`; listed at the end). The parts outside M3 come from a first read of GOALS `master` @ `39e298b`, not a full review. Keep it current as the code changes.

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
- `[FIT OPTIONS]`: `FTOL`, `SPEC_UNC_FLOOR`, `NPROC`, `FIT_CHK`, `MAX_LOOPS`, …
  - `SPEC_UNC_FLOOR` (M3) is the spectral error floor, as a fraction of the observed flux: 0.01 in the three shipped opt files, and 0.01 for opt files without it; 0 for none.
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
  - `_Peak` is in Jy for lines and PAHs, and an optical depth (unitless) for opacity features.
  - Commit `09f5df6` renamed `'gamma'`→`'width'` only in the feature lists in cafe.py. The parameter suffix is still `_Gamma`.
- **`VGRAD`:** a global velocity shift in km/s, applied to the feature wavelengths.

## 1D flow (`specmod`)
1. **`read_spec(file, z, …)`**
   - Reads `.txt`/`.dat`, a CRETA `.csv`, or a CRETA `.fits` (`extract='Flux_st'` is the stitched spectrum).
   - Trims overlapping band edges (`trim_overlapping`).
   - Moves to the rest frame: `wave/(1+z)`, `flux/(1+z)`, `flux_unc/(1+z)`.
   - Options (M3): `flux_scale` multiplies the fluxes and uncertainties; `ignore_DQ=True` sets all DQ masks to 0.
   - Side effect: when the input is not a CRETA cube, writes `./dummy.fits` into the current directory.
2. **`read_phot(...)`**: optional. Sorts the points by wavelength (M3).
3. **`fit_spec(inparfile, optfile)`**
   1. `mask_spec` produces `spec_dict` with `wave`, `flux`, `flux_unc` and `weight`.
   2. `CAFE_param_generator.make_parobj(get_all=True)` sets the parcube layout. `make_parobj()` then builds the parameters actually fitted.
   3. `CAFE_prof_generator.make_cont_profs()` builds `cont_profs`, which holds:
      - `waveMod`, `wave0` and `flux0`;
      - grain emissivities and opacities;
      - source SEDs;
      - filters.
   4. `cafe_grinder` runs `lm.Minimizer(chisquare, method='least_squares', ftol=FTOL, max_nfev=200*(npar+1))`.
      - **Normalisation (M3):** before the fit, it divides the spectrum and the photometry (fluxes and uncertainties) by the spectrum's median |flux| n. It also divides the line and PAH `_Peak` (value, min, max) and `cont_profs['flux0']` by n (`scale_peaks`). After the fit, it multiplies the peaks (with their stderr) and `flux0` back by n. Everything outside `cafe_grinder` is physical.
        - So the fit's inputs do not depend on the source's flux level. Its fitted values still can: rounding-level input differences move the end point (see the brief, "Biases", 2026-11-15).
        - `check_fit_pars`'s absolute 1e-5 tolerance at lower bounds (#11) acts on the normalised peaks, i.e. relative to n.
      - **Spectral error floor (M3):** `chisquare` gets the uncertainties sqrt(unc² + (f·F)²), with F the observed flux and f = `SPEC_UNC_FLOOR`. `check_fit_pars` and the products keep the quoted uncertainties.
      - **Photometric weights (M3):** each photometric point's χ² term is multiplied by R₀·Δλ/λ, computed once per fit.
        - R₀ comes from the spectral sampling: the mean wavelength times half the number of channels, over the wavelength range (2 channels per resolution element).
        - Δλ is half the distance between the point's two neighbours in the combined spectral + photometric wavelength list (`np.gradient`), or the full gap to its one neighbour at either end.
      - `check_fit_pars` then accepts the fit or asks for a refit.
      - On a refit, the scaling parameters (`Peak`, `FLX`, `TMP`, `TAU`, `RAT`) are perturbed by 1% and the fit is repeated, up to `MAX_LOOPS` times.
   5. `parobj2parcube` stores the results. `get_model_fluxes(comps=True)` gives the component spectra. `CompFluxes_0` includes `fFTS0`, the intrinsic PAHs plus lines (M3).
   6. `save_products` writes the outputs.
4. **Outputs:** `<name>_parcube.fits`, the continuum cube, `_fitpars.ini`, `_cafefit.asdf`, `_fitfigure.png`, `_pahtable.ecsv` and `_linetable.ecsv`.
   - The continuum cube (`_contcube`, M3) has 10 profile extensions: `fCON`, `fDSK`, `fHOT`, `fWRM` and `fCOO` (extinguished, from `CompFluxes`), and `fCON0` … `fCOO0` (intrinsic, from `CompFluxes_0`; `make_profcube`'s `'Comp_0'`). The first was called `fCon` before M3. It is built on the fit's model grid, which includes the photometry when photometry is fitted.
   - `_cafefit.asdf` stores each parameter's stderr as `fitParsErr`, next to `fitPars` (M3).
   - The fit figure's y-range includes the photometry (M3).

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
      - `cafe_grinder` fits it, normalised by that spaxel's own median |flux|, with the error floor (M3);
      - `parobj2parcube` stores the result.
   5. Writes the parcube FITS and the `_fitpars.ini` of the first (highest-"SNR") spaxel.
3. **Facts relevant to performance:**
   - Tables are read and profiles rebuilt for every spaxel. Only `flux0`, the observed flux at the reference wavelengths, really depends on the spaxel.
   - `NPROC` is read in `cafe_grinder` but never used.
   - The neighbour initialisation creates a dependency between spaxels. Any parallel scheme must either keep each spaxel's initialisation source, or count as a change in results.
   - `least_squares` estimates the Jacobian numerically, so the cost is about (npar+1) evaluations of `get_model_fluxes` per iteration, times the number of refit loops.

## CRETA extraction and stitching
1. Each band (sub-band cube) is measured slice by slice with photutils `aperture_photometry`, given the cube's celestial (2-D) WCS (M3 for the grid, G4).
   - The single extraction uses one aperture.
   - The grid extraction uses a grid of square spaxels; it takes each grid point's pixel centre from the aperture's `positions` (M3, G8).
2. **Stitching** works per aperture or grid point, over the bands in the order of `cubes` in the parameter file.
   - `calculateStitchRatios` gives, for each pair of adjacent bands, r = median(next band) / median(this band) over their overlap. It is 1.0 when they do not overlap or the overlap has no valid data.
   - `stitchSpectrum` (M3) multiplies band i by prod(r[i:]) / prod(r[ref:]), so every band lands on the flux level of the reference band `ref`. A gap is chained through with its ratio of 1.0.
   - `stitch_band` in the parameter file names the reference band as written in `cubes`, e.g. `ch1-short`. Default: the last entry of `cubes`. A name not in `cubes` stops the extraction with a `ValueError`.
   - The single and grid extractions use the same code. The grid stitches every band, the last one included (before M3 it appended the last band unstitched).
   - `Flux` and `Err` are unstitched. `Flux_st` and `Err_st` carry the stitching factors.
3. **Environment:** the results depend on the photutils version (see the brief, "Biases", 2026-11-15).
   - For rectangles (the grid's spaxels), photutils 1.10 replaces `method='exact'` with 32×32 subpixels, while 3.1.1 computes the exact overlap.
   - For the errors, 1.10 sums σ²·w, while 3.1.1 sums σ²·w² (w = the fraction of the pixel inside the aperture).

## Conventions and invariants
- **Units are fixed** (decided 2026-11-15): fluxes in Jy, wavelengths in µm. The reading code labels the data so (`Spectrum1D(..., flux=...*u.Jy)`) without converting them. Nothing depends on "flux units": a result that changes with the flux scale depends on the source's flux level (brightness).
- Only `cafe_grinder` works on normalised data (M3). Everything it receives, stores or returns is physical: the parcube (VALUE, STDERR, MIN, MAX), `cont_profs['flux0']` and the products.
- Wavelengths are in the rest frame after reading. The redshift is stored on the object.
- Parcube: FITS image HDUs (e.g. `VALUE`) with shape `(n_params, ny, nx)`. In the tutorial, `parcube['VALUE'].data[-1,0,0]` is `VGRAD`.
- Index order is mixed:
  - `ind_seq` and `ref_ind_seq` are (y, x);
  - several helpers take `(x, y)`; see comments such as "indexation is (x=1,y=0)".
  - Check carefully when touching the loop.
- `cafe_dir` points to the CAFE package folder, and tables are found through it and `[PATHS]`. The tutorial uses `site-packages`. To compare versions side by side, pass each checkout's `CAFE/` path.
- Dependencies in `setup.py`: astropy, lmfit, matplotlib, numpy, pandas, photutils, scipy, specutils, ipykernel. `asdf` is used but not listed.
- GOALS master needs `scipy.integrate.simpson` and `trapezoid`. The fork and local versions still use `simps` and `np.trapz`.

## M3 changes on `dev` (2026-11-14 to 2026-11-15)
My local changes brought in, and the GOALS bugs fixed on `dev` along the way (G numbers as in the brief). Each is described above, where it applies.
- `6d62e73`, `b51b5b9`: `read_spec(flux_scale=…, ignore_DQ=…)`.
- `b95e58f`: `fitParsErr` in the `.asdf`.
- `2263c17`: extinguished and intrinsic profiles in the continuum cube; `fCon` → `fCON`.
- `2063569`: the continuum cube is built on the fit's model grid with the photometry.
- `44f0d34`: `fFTS0` in `CompFluxes_0`.
- `ee33a5d`: the fit figure's y-range includes the photometry.
- `d7f07bb`: photometric weights R₀·Δλ/λ in the fit.
- `88d648b` (G3): `synphot` converts the model to f_λ on a copy, not in place once per filter.
- `39c930a` (G1): `read_phot` sorts the photometry by wavelength.
- `1f6bca0`: the spectral error floor, `SPEC_UNC_FLOOR`.
- `476c6ef`: the normalisation in `cafe_grinder` (replaces my local `norm_factor`).
- `be4201c`: CRETA's `stitch_band`, the reference band for stitching.
- `5c7085a`, `56b4c75` (G4): CRETA's grid and PSF-grid photometry pass the celestial WCS.
- `d41e6b1` (G7): `pyplot.get_cmap` for the grid plot colours.
- `1e66caf` (G8): the grid aperture centres come from the aperture.
