import os
import numpy as np 
import copy
import matplotlib.pyplot as plt 
from matplotlib.backends.backend_pdf import PdfPages
from specutils import Spectrum1D, SpectrumList
from astropy.nddata import StdDevUncertainty
import lmfit as lm # https://dx.doi.org/10.5281/zenodo.11813
import time, datetime
import warnings
import astropy.units as u
from astropy import constants as const
from astropy.stats import mad_std
import pandas as pd
from astropy.io import fits
import astropy
import pickle
#import importlib as imp

import CAFE
from CAFE.cafe_io import *
from CAFE.cafe_lib import *
from CAFE.cafe_helper import *
from CAFE.get_fit_sequence import get_fit_sequence

cafeio = cafe_io()

#import ipdb

def cafe_grinder(self, params, spec, phot):
    """
    params [lmfit.parameter() object]: parameters of the model
    spec [dictionary]: spectrum/a to be fitted
    phot [dictionary]: photometry to be fitted
    """

    ### Read in global fit settings
    ftol = self.inopts['FIT OPTIONS']['FTOL']
    nproc = self.inopts['FIT OPTIONS']['NPROC']
    
    acceptFit = False
    ### Limit the number of times the fit can be rerun to avoid infinite loop
    niter = 1
    show = False
    f_pert = 1.01
    
    while acceptFit is False:
        
        start = time.time()
        print('Iteration '+str(niter)+' / '+str(self.inopts['FIT OPTIONS']['MAX_LOOPS'])+'(max):', datetime.datetime.now(), '-------------')
        
        old_params = copy.copy(params) # Parameters of the previous iteration

        ### Note that which fitting method is faster here is pretty uncertain, changes by target
        #method = 'leastsq'
        method = 'least_squares' #'nelder' if len(spec['wave']) >= 10000 else 'least_squares'
        fitter = lm.Minimizer(chisquare, params, nan_policy='omit', fcn_args=(spec, phot, self.cont_profs, show))
        
        try:
            result = fitter.minimize(method=method, ftol=ftol, max_nfev=200*(len(params)+1))
        except:
            if result.success is not True: raise ValueError('The fit has not been successful.')

        # Do checks on parameters and rerun fit if no errors are returned or the fit is unsuccessful
        if result.success == True:
            end = time.time()
            print('The fitter reached a solution after', result.nfev, 'steps in', np.round(end-start, 2), 'seconds')
            
            fit_params = copy.copy(result.params) # parameters of the current iteration that will not be changed
            params = result.params # Both params AND result.params will be modified by check_fit_parameters
            
            acceptFit = check_fit_pars(self, spec['wave'], spec['flux_unc'], fit_params, params, old_params, result.errorbars)
            
        else:
            end = time.time()
            raise RuntimeError('The fitter reached the maximum number of function evaluations after', result.nfev, 'steps in', np.round(end-start, 2)/60., 'minutes')
            acceptFit = False
            
        if self.inopts['FIT OPTIONS']['FIT_CHK'] and niter < self.inopts['FIT OPTIONS']['MAX_LOOPS']:
            if acceptFit is True:
                print('Successful fit -------------------------------------------------')
            else:
                print('Rerunning fit')
                niter+=1
                
                # Perturbe the values of parameters that are scaling parameters
                for par in params.keys():
                    if params[par].vary == True:
                        parnames = par.split('_')
                        if parnames[-1] == 'Peak' or parnames[-1] == 'FLX' or parnames[-1] == 'TMP' or parnames[-1] == 'TAU' or parnames[-1] == 'RAT':
                            if params[par].value*f_pert >= params[par].max:
                                 if params[par].value/f_pert > params[par].min: params[par].value /= f_pert
                            else:
                                params[par].value *= f_pert

        else:
            if acceptFit is True:
                print('Successful fit -------------------------------------------------')
            else:
                if result.success == True:
                    print('Hit maximum number of refitting loops. The fit was successful but no errors were returned. Continuing to next spaxel (if any left)')
                else:
                    print('Hit maximum number of refitting loops. The fitting was unsuccessful. Continuing to next spaxel (if any left)')
                acceptFit = True


    return result




class cubemod:

    def __init__(self, cafe_dir='../CAFE/'):

        self.cafe_dir = cafe_dir


    def read_parcube_file(self, file_name, file_dir='cafe_results/'):

        if file_dir == 'cafe_results/': file_dir = './' + file_dir
        parcube = fits.open(file_dir+file_name)
        parcube.info()
        self.parcube = parcube
        self.parcube_dir = file_dir
        self.parcube_name = file_name.replace('.fits', '')
        self.result_file_name = self.parcube_name.replace('_parcube', '')
        #parcube.close()



    def read_cube(self, file_name, file_dir='./extractions/', extract='Flux_st', trim=True, keep_next=False, z=None):
        """
        file_name [str]: Name of the cube to read
        file_dir [str]: Folder where the data are
        extract [str]: In case of ingesting a CRETA-produced cube, read the column that have the spectra stitched
        trim [bool]: CRETA cubes retain info on the bands/channels, which is used to trim the spectra and avoid wavelength duplications (default: True)
        keep_next [bool]: The trimming process keeps the shortest wavelength data in overlapping bands/channels (default: False)
        z (float): Redshift of the source (default: 0.)
        """

        if file_dir == 'extractions/': file_dir = './' + file_dir
        
        try:
            cube = cafeio.read_cretacube(file_dir+file_name, extract)
        except:
            raise IOError('Could not open fits file')
        else:
            if cube.cube['FLUX'].header['CUNIT3'] != 'um':
                raise ValueError("The cube wavelength units are not micron")
        
        
        self.file_name = file_name #cube.cube.filename().split('/')[-1]
        self.result_file_name = 'p'.join(self.file_name.split('.')[0:-1]) # Substitute dots by "p"'s to avoid confusion with file type
        self.extract = extract
        
        # Remove the overlapping wavelengths between the spectral modules
        val_inds = trim_overlapping(cube.bandnames, keep_next) if trim == True else np.full(len(cube.waves), True)
        waves = cube.waves[val_inds]
        fluxes = cube.fluxes[val_inds,:,:]
        flux_uncs = cube.flux_uncs[val_inds,:,:]
        masks = cube.masks[val_inds,:,:]
        bandnames = cube.bandnames[val_inds]
        header = cube.header
        
        # Warning if z=0
        if z == 0.0: print('WARNING: No redshfit provided. Assuming object is already in rest-frame (z=0).')        
        
        self.z = z
        self.waves = waves / (1+z)
        self.fluxes = fluxes / (1+z)
        self.flux_uncs = flux_uncs / (1+z)
        self.masks = masks
        self.bandnames = bandnames
        self.header = header
        self.nx, self.ny, self.nz = cube.nx, cube.ny, cube.nz
        self.cube = cube
        
    

    def fit_cube(self,
                 inparfile,
                 optfile,
                 output_path=None,
                 fit_pattern='default',
                 init_parcube=False,
                 cont_profs=None,
                 force_all_lines=False,
                 pattern=None):
        """
        Main function setting up the parameters and profiles for cafe_grinder()
        """
        
        cube = self.cube
        
        # Get the fitting sequence
        snr_image = np.nansum(self.fluxes[10:20,:,:], axis=0)
        ind_seq, ref_ind_seq = get_fit_sequence(snr_image, sorting_seq=pattern)
        print('Highest SNR spaxel is:',np.flip((ind_seq[0][0],ind_seq[1][0])))
        
        # Convert the highest SNR spaxel to a spectrum1D
        wave, flux, flux_unc, bandname, mask = mask_spec(self,ind_seq[1][0],ind_seq[0][0])
        spec = Spectrum1D(spectral_axis=wave*u.micron, flux=flux*u.Jy, uncertainty=StdDevUncertainty(flux_unc), redshift=self.z)

        self.inpars = cafeio.read_inifile(inparfile)
        self.inopts = cafeio.read_inifile(optfile)

        #self.inpar_fns = np.full((self.ny, self.nx), '')
        #self.inpar_fns[ind_seq[0][0], ind_seq[1][0]] = inparfile  # (y,x)

        # Initialize CAFE param generator for the highest SNR spaxel
        print('Generating initial/full parameter object with all potential lines')        
        param_gen = CAFE_param_generator(spec, inparfile, optfile, cafe_path=self.cafe_dir)
        # These are keywords used by deeper layers of cafe
        _, outPath = cafeio.init_paths(self.inopts, cafe_path=self.cafe_dir, file_name=self.result_file_name, output_path=output_path)
        self.outPath = outPath
        
        # Make parameter object with all features available
        print('Generating parameter cube using the initial/full parameter object')
        all_params = param_gen.make_parobj(get_all=True)
        # Parcube is initialized with all possible parameters
        # Then only the ones fitted will be injected in the appropiate keys
        cube_gen = CAFE_cube_generator(self)
        parcube = cube_gen.make_parcube(all_params)        

        ## Initiate CAFE profile loader
        #print('Generating continuum profiles')
        #prof_gen = CAFE_prof_generator(spec, inparfile, optfile, None, cafe_path=self.cafe_dir)
        #
        #if cont_profs is None: # Use default run option file
        #    start = time.time()
        #    self.cont_profs = prof_gen.make_cont_profs()
        #    end = time.time()
        #    print(np.round(end-start,2), 'seconds to make continnum profiles')
        
        # ### Create logfile
        # if not self.inopts['OUTPUT FILE OPTIONS']['OVERWRITE']:
        #     logFile = open(outpath+obj+'.log', 'a')
        # else:
        #     logFile = open(outpath+obj+'.log', 'w+')        
        # self.inpars['METADATA']['OUTDIR'] = outpath
        # self.inpars['METADATA']['LOGFILE'] = outpath+obj+'.log'
        # ### FIXME - RA/DEC/Spaxel info should go here, once we have a spectrum format that uses it
        
        start_cube = time.time()
        spax = 1
        for snr_ind in zip(ind_seq[0], ind_seq[1]): # (y,x)

            wave, flux, flux_unc, bandname, mask = mask_spec(self, x=snr_ind[1], y=snr_ind[0])
            weight = 1./flux_unc**2

            if np.isnan(flux).any():
                #ipdb.set_trace()
                raise ValueError('Some of the flux values in the spectrum are NaN, which should not happen')
            
            spec = Spectrum1D(spectral_axis=wave*u.micron, flux=flux*u.Jy, uncertainty=StdDevUncertainty(flux_unc), redshift=self.z)
            spec_dict = {'wave':wave, 'flux':flux, 'flux_unc':flux_unc, 'weight':weight}
            
            print('##############################################################################################################')
            print('Regenerating parameter object for current spaxel:',np.flip(snr_ind), '(', spax, '/', len(ind_seq[0]), ')')        
            param_gen = CAFE_param_generator(spec, inparfile, optfile, cafe_path=self.cafe_dir)
            init_params = param_gen.make_parobj(force_all=force_all_lines)
            
            print('Regenerating continuum profiles')
            prof_gen = CAFE_prof_generator(spec, inparfile, optfile, None, cafe_path=self.cafe_dir)
            self.cont_profs = prof_gen.make_cont_profs()
            
            #if spax == 1:
            #    if 'AGN' in inparfile: inparfile.replace('AGN', 'SB')
            
            # If it's not the first spaxel
            if snr_ind != (ind_seq[0][0], ind_seq[1][0]):
                print('Current spaxel',np.flip(snr_ind), 'will be initialized with results from spaxel',
                      np.flip((ref_ind_seq[0,snr_ind[0],snr_ind[1]], ref_ind_seq[1,snr_ind[0],snr_ind[1]])))#,
                #      'and set to a SB inppar file')
                #
                #self.inpar_fns[snr_ind[0], snr_ind[1]] = inparfile  # (y,x)

                # We inject the common params in the parameter cube of the reference (fitted) spaxel
                # assigned for the initialization of the current spaxel to the current spaxel params
                cube_params = parcube2parobj(parcube, 
                                             ref_ind_seq[1,snr_ind[0],snr_ind[1]],
                                             ref_ind_seq[0,snr_ind[0],snr_ind[1]],
                                             init_parobj=init_params) # indexation is (x=1,y=0)
                
                # The params file is regenerated but with the VARY, LIMS and ARG reset based on the new VALUES injected
                params = param_gen.make_parobj(parobj_update=cube_params, get_all=True, init_parobj=init_params)

            else:
                if init_parcube is not False:
                    print('The params will be set to the parameters of the parcube provided for initialization')
                    cube_params = parcube2parobj(init_parcube, init_parobj=init_params)
                    params = param_gen.make_parobj(parobj_update=cube_params, get_all=True, init_parobj=init_params)
                else:
                    params = init_params


            unfixed_params = [True if params[par].vary == True else False for par in params.keys()]
            print('Fitting',unfixed_params.count(True), 'unfixed parameters, out of the', len(params), 'defined in the parameter object')
            # Fit the spectrum
            result = cafe_grinder(self, params, spec_dict, None)
            print('The VGRAD of the current spaxel is:',result.params['VGRAD'].value, '[km/s]')

            # Inject the result into the parameter cube
            parcube = parobj2parcube(result.params, parcube, snr_ind[1], snr_ind[0]) # indexation is (x,y)

            spax += 1
            
        self.parcube = parcube
        
        end_cube = time.time()
        print('Cube fitted in', np.round(end_cube-start_cube, 2)/60., 'minutes')

        # Save parcube to disk
        self.parcube_dir = outPath
        self.parcube_name = self.result_file_name+'_parcube'
        print('Saving parameters in cube to disk:',self.parcube_dir+self.parcube_name+'.fits')
        parcube.writeto(self.parcube_dir+self.parcube_name+'.fits', overwrite=True)
        
        # Write .ini file as paramfile
        print('Saving init file of the central spaxel to disk:', self.parcube_dir+self.result_file_name+'_fitpars.ini')
        cafeio.write_inifile(parcube2parobj(parcube, x=ind_seq[1][0], y=ind_seq[0][0]), self.inpars, self.parcube_dir+self.result_file_name+'_fitpars.ini')
        
        ## Make and save tables (IMPROVE FOR CUBES: NOW WILL ONLY WRITE DOWN THE CENTRAL SPAXEL)
        ## Save .asdf to disk
        #print('Saving components of the central spaxel in asdf to disk:',self.parcube_dir+self.result_file_name+'_cafefit.asdf')
        #cafeio.save_asdf(self, x=ind_seq[1][0], y=ind_seq[0][0], file_name=self.parcube_dir+self.result_file_name+'_cafefit')
                
        return self


    def make_map(self, parname, map_dir=''):

        if map_dir == '':
            if hasattr(self, 'outPath') is True:
                self.map_dir = self.outPath
            else:
                raise ValueError('A directory where to store the map must be provided with the keyword map_dir=""')
        else:
            self.map_dir = map_dir
            
        cube_gen = CAFE_cube_generator(self)
        self.parmap = cube_gen.make_map(parname)
        
        # Feature map
        self.map_name = self.result_file_name+'_'+parname+'_map'
        print('Saving map to disk:',self.map_dir+self.map_name+'.fits')
        self.parmap.writeto(self.map_dir+self.map_name+'.fits', overwrite=True)



    def plot_cube_ini(self, x, y,
                      inparfile, 
                      optfile, 
                      cont_profs=None,
                      force_all_lines=False):
        """
        Plot the SED generated by the inital parameters
        """

        wave, flux, flux_unc, bandname, mask = mask_spec(self, x, y)

        if np.isnan(flux).any() == True: raise ValueError('Requested spaxel has NaN values')

        spec = Spectrum1D(spectral_axis=wave*u.micron, flux=flux*u.Jy, uncertainty=StdDevUncertainty(flux_unc), redshift=self.z)
        spec_dict = {'wave':wave, 'flux':flux, 'flux_unc':flux_unc}
        
        # Plot features based on inital intput parameters
        # -----------------------------------------------
        
        # Initiate CAFE param generator and make parameter file
        print('Generating continuum profiles for guess model from the .ini file')
        param_gen = CAFE_param_generator(spec, inparfile, optfile, cafe_path=self.cafe_dir)
        params = param_gen.make_parobj(force_all=force_all_lines)

        # Initiate CAFE profile loader and make cont_profs
        prof_gen = CAFE_prof_generator(spec, inparfile, optfile, None, cafe_path=self.cafe_dir)
        cont_profs = prof_gen.make_cont_profs()

        # Scale continuum profiles with parameters and get spectra
        CompFluxes, CompFluxes_0, extComps, e0, tau0, _ = get_model_fluxes(params, wave, cont_profs, comps=True)
        
        # Get spectrum out of the feature parameters
        gauss, drude, gauss_opc = get_feat_pars(params, apply_vgrad2waves=True)

        cafefig = cafeplot(spec_dict, None, CompFluxes, gauss, drude, pahext=extComps['extPAH'])
        


    def plot_cube_fit(self, x, y,
                      inparfile, 
                      optfile,
                      savefig=None):
        """
        Plot the spectrum itself. If params already exists, plot the fitted results as well.
        """
        if hasattr(self, 'parcube') is False:
            raise ValueError("The spectrum is not fitted yet")
        else:
            params = parcube2parobj(self.parcube, x, y)

            wave, flux, flux_unc, bandname, mask = mask_spec(self, x, y)
            spec = Spectrum1D(spectral_axis=wave*u.micron, flux=flux*u.Jy, uncertainty=StdDevUncertainty(flux_unc), redshift=self.z)
            spec_dict = {'wave':wave, 'flux':flux, 'flux_unc':flux_unc}

            prof_gen = CAFE_prof_generator(spec, inparfile, optfile, None, cafe_path=self.cafe_dir)
            cont_profs = prof_gen.make_cont_profs()

            CompFluxes, CompFluxes_0, extComps, e0, tau0, vgrad = get_model_fluxes(params, wave, cont_profs, comps=True)

            gauss, drude, gauss_opc = get_feat_pars(params, apply_vgrad2waves=True)  # params consisting all the fitted parameters

            #sedfig, chiSqrFin = sedplot(wave, flux, flux_unc, CompFluxes, weights=weight, npars=result.nvarys)
            cafefig = cafeplot(spec_dict, None, CompFluxes, gauss, drude, vgrad=vgrad, pahext=extComps['extPAH'])

            # figs = [sedfig, cafefig]
            
            # with PdfPages(outpath+obj+'_fitplots'+tstamp+'.pdf') as pdf:
            #     for fig in figs:
            #         plt.figure(fig.number)
            #         pdf.savefig(bbox_inches='tight')

            if savefig is not None:
                cafefig.savefig(savefig)



    def plot_spec(self, x, y, savefig=None):

        wave, flux, flux_unc, bandname, mask = mask_spec(self,x,y)
        spec = Spectrum1D(spectral_axis=wave*u.micron, flux=flux*u.Jy, uncertainty=StdDevUncertainty(flux_unc), redshift=self.z)
        
        fig = plt.figure()
        ax = fig.add_subplot(111)
        ax.plot(spec.spectral_axis, spec.flux, linewidth=1, color='k', alpha=0.8)
        ax.scatter(spec.spectral_axis, spec.flux, marker='o', s=8, color='k', alpha=0.7)
        ax.errorbar(spec.spectral_axis.value, spec.flux.value, yerr=spec.uncertainty.quantity.value, fmt='none', ecolor='gray', alpha=0.4)

        ax.set_xlabel('Wavelength (' + spec.spectral_axis.unit.to_string() + ')')
        ax.set_ylabel('Flux (' + spec.flux.unit.to_string() + ')')
        ax.set_xscale('log')
        ax.set_yscale('log')

        if savefig is not None:
            fig.savefig(savefig)

        return ax


        #TBD


# ================================================================
class specmod:
    """ 
    CAFE spectral modeling. When initialized, it contains the functionalities needed for fitting a 1D spectrum and plotting the results
    """
    def __init__(self, cafe_dir='../CAFE/'):
                
        self.cafe_dir = cafe_dir


    def read_parcube_file(self, file_name, file_dir='cafe_results/'):

        if file_dir == 'cafe_results/': file_dir = './' + file_dir
        parcube = fits.open(file_dir+file_name)
        parcube.info()
        self.parcube = parcube
        self.parcube_dir = file_dir
        self.parcube_name = file_name.replace('.fits','')
        self.result_file_name = self.parcube_name.replace('_parcube','')
        #parcube.close()


    def read_spec(self, file_name, xy=None, file_dir='./extractions/', extract='Flux_st', trim=True,
                  keep_next=False, z=0., is_SED=False, read_columns=None, flux_unc=None,
                  wave_min=None, wave_max=None, rwave_min=None, rwave_max=None):
        """
        file_name: [string] Name of the file to be read. It can be a plain text file (.txt, .dat) with wavelength, flux and
                   flux uncertainty columns, a .csv file from CRETA, or a .fits cube from CRETA
        xy:        [2-element touple] If the input is a cube, this specifies the spaxel that is read
        file_dir:  [string] The directory where the file is
        extract:   [string] The name of the extraction to be used when importing a CRETA cube (default: stitched spectrum)
        trim:      [bool] Whether to trim overlapping wavelengths (only available for spectra extracted with CRETA)
        keep_next: [bool] If trim=True, whether to keep the longer wavelength data/band instead of the shorter wavelength one
        z:         [float] redshift of the source
        is_SED:    [bool] Whether the spectrum is SED-like, i.e., it has an unknown, low resolution (active but currently not supported)
        read_columns: [string list] If the input is a table with many columns, this specifies the names of the columns to be read
                      Usually, 'wave', 'flux', and 'flux_unc'
        flux_unc:  [float] If read_columns is specified, this keyword allows override the uncertainty by specifying
                   a relative error wrt the flux. I.e., flux_unc=0.2 will force the errors to be 20% of the flux
        wave_min:  [float] Minimum observed wavelength to be kept in the spectrum
        wave_max:  [float] Maximum observed wavelength to be kept in the spectrum
        rwave_min: [float] Minimum rest-frame wavelength to be kept in the spectrum
        rwave_max: [float] Maximum rest-frame wavelength to be kept in the spectrum
        """
        
        if file_dir == 'input/data/': 
            file_dir = self.cafe_dir + file_dir

        print('Spec data:',file_dir+file_name)
        try:
            cube = cafeio.read_cretacube(file_dir+file_name, extract)
        except:
            hdu = fits.PrimaryHDU()
            dummy = fits.ImageHDU(np.full(1,np.nan), name='Flux')
            dummy.header['EXTNAME'] = 'FLUX'
            hdulist = fits.HDUList([hdu, dummy])
            hdulist.writeto('./dummy.fits', overwrite=True)
            cube = fits.open('./dummy.fits')
            try:
                spec = cafeio.customFITSReader(file_dir+file_name, extract) # Returns a spectrum1D
            except:
                try:
                    from astropy.table import Table
                    # If the user wants to read selected columns from the file and/or set an arbitrary flux uncertainty if there's none
                    if read_columns != None:
                        tab = Table.read(file_dir+file_name, format='ascii.basic', data_start=0, comment='#')
                        tab_col_names = read_columns.copy()
                        import string
                        for i in range(len(tab[0])-len(read_columns)): tab_col_names.append(string.ascii_lowercase[i])
                        tab = Table.read(file_dir+file_name, format='ascii.basic', names=tab_col_names, data_start=0, comment='#')
                        if flux_unc != None:
                            tab['flux_unc'] = tab['flux'] * flux_unc

                    else:
                        name, extension = os.path.splitext(file_dir+file_name)

                        # If the file is a generic .dat or .txt file
                        if extension == '.dat' or extension == '.txt':
                            if is_SED is False:
                                tab = Table.read(file_dir+file_name, format='ascii.basic', names=['wave', 'flux', 'flux_unc'], data_start=0, comment='#')
                            else:
                                tab = Table.read(file_dir+file_name, format='ascii.basic', names=['name', 'wave', 'flux', 'flux_unc', 'width'], data_start=0, comment='#')

                        # If the file is the .csv output from CRETA
                        if extension == '.csv':
                            df = pd.read_csv(file_dir+file_name, skiprows=31)

                            # Test whether the file is standard CAFE output .csv file
                            if sum(df.columns == ['Wave', 'Band_name', 'Flux_ap', 'Err_ap', 'R_ap', 'Flux_ap_st', 'Err_ap_st', 'DQ']) == 8:
                                out_df = df[['Wave', 'Flux_ap_st', 'Err_ap_st']]
                                tab = Table.from_pandas(out_df)
                                tab.rename_column('Wave', 'wave')
                                tab.rename_column('Flux_ap_st', 'flux')
                                tab.rename_column('Err_ap_st', 'flux_unc')
                            else:
                                raise IOError('Only the CAFE produced csv file can be ingested.')

                    #if wave_min is not None:
                    #    tab = tab[tab['wave'].value >= wave_min]
                    #if wave_max is not None:
                    #    tab = tab[tab['wave'].value <= wave_max]

                except:
                    raise IOError('The file is not a valid .txt (column-based) or .fits (CRETA output) file. Or maybe the data are not there.')
                else:
                    spec = Spectrum1D(spectral_axis=tab['wave']*u.micron, flux=tab['flux']*u.Jy, uncertainty=StdDevUncertainty(tab['flux_unc']), redshift=z)
                    spec.mask = np.full(len(spec.flux), 0)
                    spec.meta = {'bandname':[None]}

            else:
                cube.bandnames = spec.meta['band_name'][0]
            #finally:
            if spec.spectral_axis.unit != 'micron':
                raise ValueError("Make sure wavelength is in micron")                            
            cube.waves = spec.spectral_axis.value
            cube.fluxes = spec.flux.value
            cube.flux_uncs = spec.uncertainty.quantity.value
            cube.masks = spec.mask
            cube.nx = 1
            cube.ny = 1
            cube.nz = spec.flux.shape
            cube.header = dummy.header #spec.meta
            cube.bandnames = np.full(len(cube.waves), 'UNKNOWN')
            trim = False
            cube.close()
            try:
                os.remove('./dummy.fits')
            except OSError as e:
                print('Failed with:', e.strerror)
                print('Error code:', e.code)
        else:
            cube.header = cube.cube['FLUX'].header
            if cube.cube['FLUX'].header['CUNIT3'] != 'um':
                raise ValueError("The cube wavelength units are not micron")


        self.file_name = file_name #cube.cube.filename().split('/')[-1]
        self.result_file_name = ''.join(self.file_name.split('.')[0:-1])
        self.extract = extract
        
        # Remove the overlapping wavelengths between the spectral modules
        val_inds = trim_overlapping(cube.bandnames, keep_next) if trim == True else np.full(len(cube.waves), True)

        if (wave_min is not None and rwave_min is not None) or (wave_max is not None and rwave_max is not None):
            raise ValueError('Observed and rest-frame wavelength limits cannot be set simultaneously')
        minWave = wave_min if wave_min is not None else np.nanmin(cube.waves[val_inds])
        maxWave = wave_max if wave_max is not None else np.nanmax(cube.waves[val_inds])
        minWave = rwave_min*(1+z) if rwave_min is not None else np.nanmin(cube.waves[val_inds])
        maxWave = rwave_max*(1+z) if rwave_max is not None else np.nanmax(cube.waves[val_inds])

        fit_wave_inds = (cube.waves[val_inds] >= minWave) & (cube.waves[val_inds] <= maxWave)
        
        waves = cube.waves[val_inds][fit_wave_inds]
        bandnames = cube.bandnames[val_inds][fit_wave_inds]
        header = cube.header
        if xy is not None:
            cube.nx = 1
            cube.ny = 1
            (x,y) = xy
            fluxes = cube.fluxes[val_inds,y,x][fit_wave_inds]
            flux_uncs = cube.flux_uncs[val_inds,y,x][fit_wave_inds]
            masks = cube.masks[val_inds,y,x][fit_wave_inds]
            
        else:
            fluxes = cube.fluxes[val_inds][fit_wave_inds]
            flux_uncs = cube.flux_uncs[val_inds][fit_wave_inds]
            masks = cube.masks[val_inds][fit_wave_inds]

        # Warning if z=0
        if z == 0.0: print('WARNING: No redshift provided. Assuming object is already in rest-frame (z=0).')

        self.z = z
        self.waves = waves / (1+z)
        self.fluxes = fluxes / (1+z)
        self.flux_uncs = flux_uncs / (1+z)   
        self.masks = masks
        self.bandnames = bandnames
        self.header = header
        self.nx, self.ny, self.nz = cube.nx, cube.ny, cube.nz
        self.cube = cube



    def read_phot(self, file_name, file_dir='./extractions/'):

        #tab = Table.read(file_dir+file_name, format='ascii.basic', names=['name', 'wave', 'flux', 'flux_unc', 'width'], data_start=0, comment='#')
        #self.pwaves = tab['wave'] / self.z
        #self.pfluxes = tab['flux'] / self.z
        #self.pflux_uncs = tab['flux_unc'] / self.z
        #self.pbandnames = tab['name']
        #self.pwidths = tab['width']

        print('Phot data:',file_dir+file_name)
        tab = np.genfromtxt(file_dir+file_name, comments='#', dtype='str')
        self.pwaves = tab[:,1].astype(float) / (1+self.z)
        self.pfluxes = tab[:,2].astype(float) / (1+self.z)
        self.pflux_uncs = tab[:,3].astype(float) / (1+self.z)
        self.pbandnames = tab[:,0]
        self.pwidths = tab[:,4].astype(float) / (1+self.z)



    def fit_spec(self, 
                 inparfile,
                 optfile,
                 output_path=None,
                 init_parcube=False,
                 cont_profs=None,
                 force_all_lines=False):
        """
        Output result from lmfit
        """

        self.inparfile = inparfile
        self.optfile = optfile
        
        self.inpars = cafeio.read_inifile(inparfile)
        self.inopts = cafeio.read_inifile(optfile)

        # Get the spectrum details from self.
        wave, flux, flux_unc, bandname, mask = mask_spec(self)
        weight = 1./flux_unc**2
        # Assemble it in a Spectrum1D for the profile generator and in a dictionary for the fitting and plotting
        spec = Spectrum1D(spectral_axis=wave*u.micron, flux=flux*u.Jy, uncertainty=StdDevUncertainty(flux_unc), redshift=self.z)
        spec_dict = {'wave':wave, 'flux':flux, 'flux_unc':flux_unc, 'weight':weight}
        self.spec_dict = spec_dict
        
        # See if the user wants to fit photometric data and check whether they have been read
        self.fitphot = self.inopts['MODEL OPTIONS']['FITPHOT']
        if self.fitphot is True:
            if hasattr(self, 'pwaves') is False: raise AttributeError('You are trying to fit photometry but the data have not been loaded. Use cafe.read_phot() to do so.')
            phot_dict = {'wave':self.pwaves, 'flux':self.pfluxes, 'flux_unc':self.pflux_uncs, 'width':self.pwidths}
        else:
            phot_dict = None
        self.phot_dict = phot_dict
            
        # Initiate CAFE param generator
        param_gen = CAFE_param_generator(spec, inparfile, optfile, cafe_path=self.cafe_dir)
        _, outPath = cafeio.init_paths(self.inopts, cafe_path=self.cafe_dir, file_name=self.result_file_name, output_path=output_path)

        print('Generating parameter cube with initial/full parameter object')
        all_params = param_gen.make_parobj(get_all=True)
        cube_gen = CAFE_cube_generator(self)
        parcube = cube_gen.make_parcube(all_params)
        
        print('Generating parameter object')        
        init_params = param_gen.make_parobj(force_all=force_all_lines)
        
        if init_parcube is not False:
            print('The parameters in the parcube provided for initialization will be used to initialize the parameter object')
            cube_params = parcube2parobj(init_parcube, init_parobj=init_params)
            params = param_gen.make_parobj(parobj_update=cube_params, get_all=True, init_parobj=init_params)
        else:
            params = init_params

        # Initiate CAFE profile loader
        print('Generating continuum profiles')
        prof_gen = CAFE_prof_generator(spec, inparfile, optfile, phot_dict, cafe_path=self.cafe_dir)

        if cont_profs is None:
            self.cont_profs = prof_gen.make_cont_profs() # Generate the selected unscaled continuum profiles
        else:
            self.cont_profs = cont_profs
            
        unfixed_params = [True if params[par].vary == True else False for par in params.keys()]
        print('Fitting',unfixed_params.count(True), 'unfixed parameters, out of the', len(params), 'defined in the parameter object')

        # Fit the spectrum
        result = cafe_grinder(self, params, spec_dict, phot_dict)
        print('The VGRAD of the spectrum is:', result.params['VGRAD'].value, '[km/s]')

        self.params = result.params
        
        # Inject the result into the parameter cube
        parcube = parobj2parcube(result.params, parcube)
        self.parcube = parcube

        # Get compdict
        CompFluxes, CompFluxes_0, extComps, e0, tau0, vgrad = get_model_fluxes(self.params, self.spec_dict['wave'], self.cont_profs, comps=True)

        compdict = {'CompFluxes': CompFluxes,
                    'CompFluxes_0': CompFluxes_0,
                    'extComps': extComps,
                    'e0': e0,
                    'tau0': tau0,
                    }

        self.compdict = compdict 
                     
        self.save_products(outPath)

        return self

    
    def save_products(self, product_dir):
        
        # Save products to disk
        self.product_dir = product_dir
        
        # Parcube
        self.parcube_name = self.result_file_name+'_parcube'
        print('Saving parameters in cube to disk:',self.product_dir+self.parcube_name+'.fits')
        self.parcube.writeto(self.product_dir+self.parcube_name+'.fits', overwrite=True)
        
        ## Save fCON cube to disk
        cube_gen = CAFE_cube_generator(self)
        self.contcube = cube_gen.make_profcube(self.inparfile, self.optfile, prof_names={'fCon':['Comp', 'fCON'], 'fDSK':['Comp', 'fDSK'], 'fHOT':['Comp', 'fHOT']})
        self.contcube_name = self.result_file_name+'_contcube'
        print('Saving total continuum profile in cube to disk:',self.product_dir+self.contcube_name+'.fits')
        self.contcube.writeto(self.product_dir+self.contcube_name+'.fits', overwrite=True)
        
        #self.compdict_name = self.result_file_name+'_compdict'
        #print('Saving component profiles in dictionary to disk:',self.compdict_dir+self.compdict_name+'.pkl')
        ##compcube.writeto(self.compcube_dir+self.compdict_name+'.fits', overwrite=True)
        #with open(self.compcube_dir+self.compdict_name+'.pkl', 'wb') as f:
        #    pickle.dump(compdict, f)
        
        # Write best fit as an .ini parameter file
        print('Saving init file to disk:', self.product_dir+self.result_file_name+'_fitpars.ini')
        cafeio.write_inifile(self.params, self.inpars, self.product_dir+self.result_file_name+'_fitpars.ini')

        # Save component dictionary .asdf to disk
        print('Saving parameters in asdf to disk:', self.product_dir+self.result_file_name+'_cafefit.asdf')
        cafeio.save_asdf(self, file_name=self.product_dir+self.result_file_name+'_cafefit')

        print('Saving figure in png to disk:',self.product_dir+self.result_file_name+'_fitfigure.png')
        CompFluxes, CompFluxes_0, extComps, e0, tau0, vgrad = get_model_fluxes(self.params, self.spec_dict['wave'], self.cont_profs, comps=True)
        gauss, drude, gauss_opc = get_feat_pars(self.params, apply_vgrad2waves=True)  # params consisting all the fitted parameters        
        # Save figure
        cafefig = cafeplot(self.spec_dict, self.phot_dict, CompFluxes, gauss, drude, vgrad=vgrad, pahext=extComps['extPAH'], save_name=self.product_dir+self.result_file_name+'_fitfigure.png', params=self.params)

        # Save the PAH table
        output_fn = os.path.join(self.product_dir, self.result_file_name+'_pahtable.ecsv')
        self.pahtable = cafeio.pah_table(self.parcube, self.compdict, pah_obs=True, savetbl=output_fn)
        
        # Save the line table
        output_fn = os.path.join(self.product_dir, self.result_file_name+'_linetable.ecsv')
        self.linetable = cafeio.line_table(self.parcube, self.compdict, line_obs=True, savetbl=output_fn)
    

    def plot_spec_ini(self,
                      inparfile, 
                      optfile, 
                      init_parcube=False,
                      cont_profs=None,
                      force_all_lines=False):
        """
        Plot the SED generated by the inital parameters
        """

        self.inpars = cafeio.read_inifile(inparfile)
        self.inopts = cafeio.read_inifile(optfile)

        wave, flux, flux_unc, bandname, mask = mask_spec(self)
        spec = Spectrum1D(spectral_axis=wave*u.micron, flux=flux*u.Jy, uncertainty=StdDevUncertainty(flux_unc), redshift=self.z)
        spec_dict = {'wave':wave, 'flux':flux, 'flux_unc':flux_unc}

        self.fitphot = self.inopts['MODEL OPTIONS']['FITPHOT']
        if self.fitphot is True:
            if hasattr(self, 'pwaves') is False: raise AttributeError('You are trying to fit photometry but the data have not been loaded. Use cafe.read_phot() to do so.')
            phot_dict = {'wave':self.pwaves, 'flux':self.pfluxes, 'flux_unc':self.pflux_uncs, 'width':self.pwidths}
        else:
            phot_dict = None

        # Plot features based on inital intput parameters
        # -----------------------------------------------

        # Initiate CAFE param generator and make parameter file
        print('Generating continuum profiles for guess model from the .ini file')
        param_gen = CAFE_param_generator(spec, inparfile, optfile, cafe_path=self.cafe_dir)
        params = param_gen.make_parobj(force_all=force_all_lines)
        
        if init_parcube is not False:
            print('The initial parameters will be set to the values from the parameter cube provided')
            cube_params = parcube2parobj(init_parcube, init_parobj=params)
            params = param_gen.make_parobj(parobj_update=cube_params, get_all=True)
        
        # Initiate CAFE profile loader and make cont_profs
        prof_gen = CAFE_prof_generator(spec, inparfile, optfile, phot_dict, cafe_path=self.cafe_dir)
        cont_profs = prof_gen.make_cont_profs() # load the selected unscaled continuum profiles

        # Scale continuum profiles with parameters and get spectra
        CompFluxes, CompFluxes_0, extComps, e0, tau0, _ = get_model_fluxes(params, wave, cont_profs, comps=True)

        # Get feature spectrum out of the feature parameters
        gauss, drude, gauss_opc = get_feat_pars(params, apply_vgrad2waves=True)
        
        cafefig = cafeplot(spec_dict, phot_dict, CompFluxes, gauss, drude, pahext=extComps['extPAH'])



    def plot_spec_fit(self,
                      inparfile, 
                      optfile, 
                      save_name=None):
        """
        Plot the spectrum itself. If params already exists, plot the fitted results as well.
        """

        self.inpars = cafeio.read_inifile(inparfile)
        self.inopts = cafeio.read_inifile(optfile)

        wave, flux, flux_unc, bandname, mask = mask_spec(self)
        spec = Spectrum1D(spectral_axis=wave*u.micron, flux=flux*u.Jy, uncertainty=StdDevUncertainty(flux_unc), redshift=self.z)
        spec_dict = {'wave':wave, 'flux':flux, 'flux_unc':flux_unc}

        self.fitphot = self.inopts['MODEL OPTIONS']['FITPHOT']
        if self.fitphot is True:
            if hasattr(self, 'pwaves') is False: raise AttributeError('You are trying to fit photometry but the data have not been loaded. Use cafe.read_phot() to do so.')
            phot_dict = {'wave':self.pwaves, 'flux':self.pfluxes, 'flux_unc':self.pflux_uncs, 'width':self.pwidths}
        else:
            phot_dict = None

        if hasattr(self, 'parcube') is False:
            raise ValueError("The spectrum is not fitted yet")
        else:
            params = parcube2parobj(self.parcube)

        prof_gen = CAFE_prof_generator(spec, inparfile, optfile, phot_dict, cafe_path=self.cafe_dir)
        cont_profs = prof_gen.make_cont_profs()
        
        CompFluxes, CompFluxes_0, extComps, e0, tau0, vgrad = get_model_fluxes(params, wave, cont_profs, comps=True)
        
        gauss, drude, gauss_opc = get_feat_pars(params, apply_vgrad2waves=True)  # params consisting all the fitted parameters
        
        #sedfig, chiSqrFin = sedplot(wave, flux, flux_unc, CompFluxes, weights=weight, npars=result.nvarys)
        cafefig = cafeplot(spec_dict, phot_dict, CompFluxes, gauss, drude, vgrad=vgrad, pahext=extComps['extPAH'], params=params)
        
        # figs = [sedfig, cafefig]
        
        # with PdfPages(outpath+obj+'_fitplots'+tstamp+'.pdf') as pdf:
        #     for fig in figs:
        #         plt.figure(fig.number)
        #         pdf.savefig(bbox_inches='tight')
        
        if save_name is not None:
            cafefig[0].savefig(save_name, dpi=500, format='png', bbox_inches='tight')

    
    
    def plot_spec(self, savefig=None):

        wave, flux, flux_unc, bandname, mask = mask_spec(self)
        spec = Spectrum1D(spectral_axis=wave*u.micron, flux=flux*u.Jy, uncertainty=StdDevUncertainty(flux_unc), redshift=self.z)
        
        fig = plt.figure()
        ax = fig.add_subplot(111)
        ax.plot(spec.spectral_axis, spec.flux, linewidth=1, color='k', alpha=0.8)
        ax.scatter(spec.spectral_axis, spec.flux, marker='o', s=8, color='k', alpha=0.7)
        ax.errorbar(spec.spectral_axis.value, spec.flux.value, yerr=spec.uncertainty.quantity.value, fmt='none', ecolor='gray', alpha=0.4)

        ax.set_xlabel('Wavelength (' + spec.spectral_axis.unit.to_string() + ')')
        ax.set_ylabel('Flux (' + spec.flux.unit.to_string() + ')')
        ax.set_xscale('log')
        ax.set_yscale('log')

        if savefig is not None:
            fig.savefig(savefig)

        return ax


    # TO BE DEPRECATED AS ALL READ AND WRITE FUNCTIONS SHOULD BE IN CAFE IO
    def save_result(self, asdf=True, pah_tbl=True, line_tbl=True, file_name=None):

        if hasattr(self, 'parcube') is False:
            raise AttributeError('The spectrum is not fitted yet. Missing fitted result - parcube.')

        params = self.parcube.params
        wave = self.spec.spectral_axis.value

        if asdf is True:
            params_dict = params.valuesdict()
            
            # Get fitted results
            gauss, drude, gauss_opc = get_feat_pars(params, apply_vgrad2waves=True)  # params consisting all the fitted parameters
            CompFluxes, CompFluxes_0, extComps, e0, tau0, _ = get_model_fluxes(params, wave, self.cont_profs, comps=True)

            # Get PAH powers (intrinsic/extinguished)
            pah_power_int = drude_int_fluxes(CompFluxes['wave'], drude)
            pah_power_ext = drude_int_fluxes(CompFluxes['wave'], drude, ext=extComps['extPAH'])

            # Quick hack for output PAH and line results
            output_gauss = {'wave':gauss[0], 'width':gauss[1], 'peak':gauss[2], 'name':gauss[3], 'strength':np.zeros(len(gauss[3]))} #  Should add integrated gauss
            output_drude = {'wave':drude[0], 'width':drude[1], 'peak':drude[2], 'name':drude[3], 'strength':pah_power_int.value}

            # Make dict to save in .asdf
            obsspec = {'wave': self.wave, 'flux': self.flux, 'flux_unc': self.flux_unc}
            cafefit = {'cafefit': {'obsspec': obsspec,
                                   'fitPars': params_dict,
                                   'CompFluxes': CompFluxes,
                                   'CompFluxes_0': CompFluxes_0,
                                   'extComps': extComps,
                                   'e0': e0,
                                   'tau0': tau0,
                                   'gauss': output_gauss,
                                   'drude': output_drude
                                   }
                       }

            # Save output result to .asdf file
            target = AsdfFile(cafefit)
            if file_name is None:
                target.write_to(self.cafe_dir+'cafe_results/last_unnamed_cafefit.asdf', overwrite=True)
            else:
                target.write_to(file_name+'.asdf', overwrite=True)


def plot_cafefit(asdf_fn):
    """ Recover the CAFE plot based on the input asdf file
    INPUT:
        asdf_fn: the asdf file that store the CAFE fitted parameters
    OUTPUT:
        A mpl axis object that can be modified for making the figure
    """
    af = asdf.open(asdf_fn)
    
    wave = np.asarray(af.tree['cafefit']['obsspec']['wave'])
    flux = np.asarray(af['cafefit']['obsspec']['flux'])
    flux_unc = np.asarray(af['cafefit']['obsspec']['flux_unc'])
    
    comps = af['cafefit']['CompFluxes']
    extPAH = af['cafefit']['extComps']['extPAH']
    g = af['cafefit']['gauss']
    d = af['cafefit']['drude']
    
    gauss = [g['wave'], g['gamma'], g['peak']]
    drude = [d['wave'], d['gamma'], d['peak']]
    
    spec_dict = {'wave':wave, 'flux':flux, 'flux_unc':flux_unc}
    
    # Assuming there is no phot input.
    # TODO: include phot_dict as input.
    (cafefig, ax1, ax2) = cafeplot(spec_dict, None, comps, gauss, drude, pahext=extPAH)
