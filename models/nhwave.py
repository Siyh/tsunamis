#Class objects for nhwave and funwave
#Simon Libby 2017

import os
import numpy as np
import cartopy.crs as ccrs
from glob import glob
from shutil import copyfile
from scipy.interpolate import griddata

from tsunamis.models.base import model, sequence
 
        
class config(model):
    model = 'NHWAVE'
    
    @property
    def default_executable_path(self):
        script_folder = os.path.dirname(os.path.abspath(__file__))
        return os.path.abspath(os.path.join(script_folder, './../executables/nhwave'))
    
    # def __init__(self, *args, **kwargs):        
    #     super().__init__(*args, **kwargs)
        
    def load_esri_ascii(self, path, epsg, x0, x1, y0, y1, res, method='cubic'):
        """
        Load values from lat long esri ascii file.
        Set up is for GEBCO 30 second global grid
        """
        print('Interpolating GEBCO lat long data to specified projected grid.')
        #Get header values
        with open(path) as myfile:
            head_vals = [next(myfile).strip().rpartition(' ')[-1] \
                    for _ in range(5)]
        ncols, nrows, xllcorner, yllcorner, cellsize = head_vals   

        #Make lat long grid of depth
        xs, ys = np.meshgrid(sequence(xllcorner, cellsize, ncols),
                             sequence(yllcorner, cellsize, nrows)[::-1]) #index bit cos longitude
        
        #Transform points to projected coordinates
        transformed = ccrs.epsg(epsg).transform_points(ccrs.PlateCarree(),
                xs, ys)
        xc = transformed[:, :, 0].flatten()
        yc = transformed[:, :, 1].flatten()        
            
        #Make dimensions of grid for depths to be interpolated to
        xx = np.arange(x0, x1 + 1, res)
        yy = np.arange(y0, y1 + 1, res)
        
        zs = np.loadtxt(path, skiprows=6)
        zz = griddata((xc, yc), zs.flatten(),
                (xx[None,:], yy[:,None]), method=method)
        #Flip to north up orientation
        zz = zz[::-1]        
                
        #Check if any of the nhwave points are outside the funwave area
        nan_count = np.sum(np.isnan(zz))
        if nan_count:
            print('WARNING,', nan_count,
                    'interpolated points outside the defined area')
            zz = np.nan_to_num(zz)
        #Convert elevations to depths
        zz = -zz        
        #Cap depths
        zz[zz < 1] = 1
        
        if np.mean(zz) < 0:
            print('WARNING, depths should be depths and not elevations')
        
        self.depth = zz
        np.savetxt(self.depth_path, zz, fmt='%5.5g')
        self.parameters['Mglob'] = zz.shape[1]
        self.parameters['Nglob'] = zz.shape[0]
        self.parameters['DX'] = float(res)
        self.parameters['DY'] = float(res)
        self.x0 = x0
        self.y0 = y0
        
       
    def gen_ls(self, time):
        """Function to generate the landslide thicknesses""" 
        lsxs, lsys = np.meshgrid(sequence(0, self.parameters['DX'],
                                          self.parameters['Mglob']),
                                 sequence(0, self.parameters['DY'],
                                          self.parameters['Nglob']))
        
        #Rigid landslide 'lumpiness' parameter
        e = 0.717        
        alpha0 = np.radians(float(self.SlideAngle))
        cosa0 = np.cos(alpha0)
        sina0 = np.sin(alpha0)
        coss0 = np.cos(np.radians(float(self.SlopeAngle)))        
        
        v = 2.0 * np.arccosh(1.0 / e)
        kb = v / float(self.SlideL)
        kw = v / float(self.SlideW)
        t0 = float(self.SlideUt) / float(self.SlideA0)
        s0 = float(self.SlideUt)**2 / float(self.SlideA0)
        
        st = s0 * np.log(np.cosh(time / t0)) * coss0
        self.lsx = float(self.SlideX0) + st * cosa0
        self.lsy = float(self.SlideY0) + st * sina0        
        
        xsmlsx = lsxs - self.lsx
        ysmlsy = lsys - self.lsy
        
        xt = xsmlsx * cosa0 + ysmlsy * sina0
        yt = -xsmlsx * sina0 + ysmlsy * cosa0
        zt = float(self.SlideT) / (1. - e) * (1. / 
                np.cosh(kb * xt) / np.cosh(kw * yt) - e)
        return zt.clip(min=0)
    
                
    def nhw_to_funw(self,
                    fwo,
                    funw_crs=None,
                    nhw_crs=None,
                    interpolate=True,
                    nx0=None,
                    ny0=None,
                    fx0=None,
                    fy0=None,
                    insert=False,
                    result_to_convert=None,
                    method='linear',
                    landslide=True):
        """
        Function to convert from nhwave output to funwave input.
        fwo = funwave object to convert the results for.
        funw_crs = cartopy projection (probably utm) being used by funwave.
                Defaults to lat/long.
                Integer value interpreted as an EPSG number.
        nhw_crs = cartopy projection (utm) being used by nhw.
                Integer value interpreted as an EPSG number.
        x0, y0 = coordinates of the 'bottom left' corner of the grids.
        result_to_convert = the number of the results to convert.
                Defaults to the maximum number.
        method = method of interpolation (see scipy griddata).
        """
        #TODO implement getting x0s and y0s from surface inputs
        #Get the number (with preceeding zeros) of the result to convert
        if result_to_convert is None:
            #List of the results
            results = glob(self.results_path + 'eta_*')
            #Check there are some results to convert
            if not results:
                print('No results to convert')
                return
            #Find the largest file number to convert
            result_to_convert = int(max(results)[-5:])
                   
        print('Interpolating nhwave grids to funwave grids')        
    
        
        
        #Check what transformation is necessary
        if np.array_equal(self.depth, fwo.depth):
            print('Grids are in the same place')
        else:
            # Define coordinate systems
            if not funw_crs: funw_crs = ccrs.PlateCarree()
            if isinstance(funw_crs, int): funw_crs = ccrs.epsg(funw_crs)
            if isinstance(nhw_crs, int): nhw_crs = ccrs.epsg(nhw_crs)
            
            if nx0 is None:
                nx0 = self.x0
                if nx0 is None: raise Exception('NHWAVE x0 not specified')
                
            if ny0 is None:
                ny0 = self.y0
                if ny0 is None: raise Exception('NHWAVE y0 not specified')
                
            if fx0 is None:
                fx0 = fwo.x0
                if fx0 is None: raise Exception('FUNWAVE x0 not specified')
                
            if fy0 is None:
                fy0 = fwo.y0
                if fy0 is None: raise Exception('FUNWAVE y0 not specified') 
                
            nmglob = self.parameters['Mglob']
            fmglob = fwo.parameters['Mglob']
            nnglob = self.parameters['Nglob']
            fnglob = fwo.parameters['Nglob']
            ndx = self.parameters['DX']
            fdx = fwo.parameters['DX']
            ndy = self.parameters['DY']
            fdy = fwo.parameters['DY']
            
            
            xl = sequence(fx0, fdx, fmglob)
            yl = sequence(fy0, fdy, fnglob)  
            
            if (
                    # If the grids are the same resolution
                    (ndx == fdx) and (ndy == fdy) and
                    # And the nhwave grid aligns with the funwave grid
                    (nx0 in xl) and (ny0 in yl)
                    
                ):
                
                print('Common grid points')
                insert = True
                indices = np.zeros_like(fwo.depth, dtype=bool)
                xi = list(xl).index(nx0)
                yi = list(yl).index(ny0)
                indices[yi:yi + nnglob, xi:xi + nmglob] = True
                pass
                #indices = np.where(indices)
                
            elif interpolate:
                print('Interpolating grids')
                #Make cartesian grid of nhwave files
                xc, yc = np.meshgrid(sequence(nx0, ndx, nmglob),
                                     sequence(ny0, ndy, nnglob))
                #Transform points to funwave crs
                transformed = funw_crs.transform_points(nhw_crs, xc, yc)
                xs = transformed[:, :, 0].flatten()
                ys = transformed[:, :, 1].flatten()
            
        
        #For each grid to be copied
        for f in ['eta', 'Us', 'Vs']:
            print(f'Interpolating "{f}" surface')
            source_path = os.path.join(self.results_path, f'{f}_{int(result_to_convert):05d}')
            #There are velocity values for each water layer, hence index bit
            zs = np.loadtxt(source_path)[:nnglob]
            #Get rid of land elevation on wave data, except where wave over land
            if f == 'eta':
                zs[(zs > 0) * (zs > self.depth)] = 0
                
            #mask spikes
            ############################
            zs[:, -1] = 0 ###### get rid of the source of spikes
            #zs[-1] = 0
            ###########################
            if insert:
                nzs = np.zeros_like(fwo.depth)
                nzs[indices] = zs.flatten()
                zs = nzs                
            elif interpolate:
                #nan to num to convert points outside the funwave area,                
                zs = np.nan_to_num(griddata((xs, ys), zs.flatten(),
                                            (xl[None,:], yl[:,None]),
                                            method=method))
                
            np.savetxt(os.path.join(fwo.output_directory, f + '.txt'),
                       zs, fmt='%5.5g')
            setattr(fwo, f, zs)
            
        
        # Put a landslide lump on the bathymetry
        if landslide:                      
            # Make a copy of the bathymetry without landslide data
            dwlp = os.path.join(fwo.output_directory, 'depth_without_landslide.txt')
            if not os.path.isfile(dwlp):
                print('Saving a copy of the depth without a landslide')
                #Save a copy of the depth without the landslide
                copyfile(fwo.depth_path, dwlp)
                
            # Get a copy of the landslide thickness by subtracting the depth 
            # from the landslide
            results_path = os.path.join(self.output_directory,
                                        self.parameters['RESULT_FOLDER'])
            ndwlp = results_path + f'depth_{result_to_convert:05d}'
            landslide = np.loadtxt(ndwlp) - np.loadtxt(self.depth_path)

            print('Adding a landslide to the depth file') 
            # Replace any old landslide
            if insert or interpolate: fwo.depth = np.loadtxt(dwlp)
            # Add the landslide to funwaves depth
            if insert:
                fwo.depth[indices] -= landslide.flatten()
            elif interpolate:
                # nan to num to convert points outside the funwave area,                
                fwo.depth -= np.nan_to_num(griddata((xs, ys),
                        landslide.flatten(),
                        (xl[None,:], yl[:,None]), method=method))
            
            # Replace funwaves depth.txt file
            np.savetxt(fwo.depth_path, fwo.depth, fmt='%5.5g')
            
    