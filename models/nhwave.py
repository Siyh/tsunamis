#Class objects for nhwave and funwave
#Simon Libby 2017

import os, sys
import numpy as np
import cartopy.crs as ccrs
from glob import glob
from shutil import copyfile
from scipy.interpolate import griddata

from .base import model      
 
        
class config(model):
    model = 'NHWAVE'
    
    @property
    def default_executable_path(self):
        script_folder = os.path.dirname(os.path.abspath(__file__))
        return os.path.abspath(os.path.join(script_folder, './../executables/nhwave'))
    
#    def __init__(self, *args, **kwargs):        
#        super().__init__(*args, **kwargs)
        
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
        xl = self.gs(ncols, cellsize, xllcorner)
        yl = self.gs(nrows, cellsize, yllcorner)[::-1] #index bit cos longitude
        xs, ys = np.meshgrid(xl, yl)
        
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
        self.update_inputs(Mglob=zz.shape[1], Nglob=zz.shape[0],
                DX=float(res), DY=float(res))
        self.x0 = x0
        self.y0 = y0
       
    def gen_ls(self, time):
        """Function to generate the landslide thicknesses""" 
        x = self.gs(self.Mglob, self.DX)
        y = self.gs(self.Nglob, self.DY)
        lsxs, lsys = np.meshgrid(x, y)
        
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
                
    def nhw_to_funw(self, fwo, funw_crs=None, nhw_crs=None, interpolate=True,
            nx0=None, ny0=None, fx0=None, fy0=None, insert=False,
            result_to_convert=None, method='linear', landslide=True):
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
        ###### implement getting x0s and y0s from surface inputs
        #Get the number (with preceeding zeros) of the result to convert
        if result_to_convert:
            result_to_convert = str(result_to_convert)
            preceeding_zeros = (5 - len(result_to_convert)) * '0'
            result_to_convert = preceeding_zeros + result_to_convert
        else:
            #List of the results
            results = glob(self.results_dir + 'eta_*')
            #Check there are some results to convert
            if not results:
                print('No results to convert')
                sys.exit()
            #Find the largest file number to convert
            result_to_convert = max(results)[-5:]
        #Get the folder to move the results to
        target = fwo.mod_dir
                   
        print('Interpolating nhwave grids to funwave grids')        
    
        #Define coordinate systems
        if not funw_crs: funw_crs = ccrs.PlateCarree()
        if type(funw_crs) == int: funw_crs = ccrs.epsg(funw_crs)
        if type(nhw_crs) == int: nhw_crs = ccrs.epsg(nhw_crs)
        
        #Check what transformation is necessary
        if np.array_equal(self.depth, fwo.depth):
            print('Grids are in the same place')
        else:
            xl = list(self.gs(fwo.Mglob, fwo.DX, fx0))
            yl = list(self.gs(fwo.Nglob, fwo.DY, fy0))      
            
            if ((self.depth.shape != fwo.depth.shape) and 
                    (self.DX == fwo.DX) and
                    (self.DY == fwo.DY) and
                    #Points fit on linspace
                    (nx0 in xl) and
                    (ny0 in yl) or
                    insert):
                print('Common grid points')
                insert = True
                indices = np.zeros_like(fwo.depth, dtype=bool)
                xi = xl.index(nx0)
                yi = yl.index(ny0)
                indices[yi:yi + int(self.Nglob), xi:xi + int(self.Mglob)] = True
                indices = np.where(indices)
                
            elif interpolate:
                print('Interpolating grids')
                #Make cartesian grid of nhwave files
                """
                #For rotating a grid
                #Distance from x0, y0 location
                xl = self.gs(self.Mglob, self.DX, 0)
                yl = self.gs(self.Nglob, self.DY, 0)
                xd, yd = np.meshgrid(xl, yl)
                hx = int(self.Mglob) * float(self.DX) / 2
                hy = int(self.Nglob) * float(self.DY) / 2
                dx = xd - hx
                dy = yd - hy
                a = np.radians(rotation)            
                xc = x0+hx + np.cos(a) * dx - np.sin(a) * dy
                yc = y0+hy + np.sin(a) * dx + np.cos(a) * dy
                """
                xl = self.gs(self.Mglob, self.DX, nx0)
                yl = self.gs(self.Nglob, self.DY, ny0)
                xc, yc = np.meshgrid(xl, yl)
                #Transform points to funwave crs
                transformed = funw_crs.transform_points(nhw_crs, xc, yc)
                xs = transformed[:, :, 0].flatten()
                ys = transformed[:, :, 1].flatten()     
                
                #Make dimensions of grid for funwave files to be interpolated to
                xx = self.gs(fwo.Mglob, fwo.DX, fx0)
                yy = self.gs(fwo.Nglob, fwo.DY, fy0)
            
        
        #For each grid to be copied
        for f in ['eta', 'u', 'v']:
            print('Interpolating "' + f + '" surface')
            source_path = self.results_dir + f + '_' + result_to_convert
            #There are velocity values for each water layer, hence index bit
            zs = np.loadtxt(source_path)[:int(self.Nglob)]
            #Get rid of land elevation on wave data, except where wave over land
            if f == 'eta':
                zs[(zs > 0) * (zs > self.depth)] = 0
            ############## is this bit needed?
                
            #mask spikes
            ############################
            zs[:, -1] = 0 ###### get rid of the source of spikes
            zs[-1] = 0
            ###########################
            if insert:
                nzs = np.zeros_like(fwo.depth)
                nzs[indices] = zs.flatten()
                zs = nzs                
            elif interpolate:
                #nan to num to convert points outside the funwave area,                
                zs = np.nan_to_num(griddata((xs, ys), zs.flatten(),
                        (xx[None,:], yy[:,None]), method=method))
                
            np.savetxt(target + f + '.txt', zs, fmt='%5.5g')
            fwo.__dict__.update({f: zs})
        
        #Put a landslide lump on the bathymetry
        if landslide:                      
            #Manage a copy of the bathymetry without landslide data
            dwlp = os.path.join(fwo.mod_dir, 'depth_without_landslide.txt')
            #If a landslide has already been added to the funwave depth file
            if os.path.isfile(dwlp):
                #Replace depth.txt with the depth without a landslide
                copyfile(dwlp, fwo.depth_path)
                #And reload the depth in the model
                fwo.depth = np.loadtxt(fwo.depth_path)
            else:
                print('Saving a copy of the depth without a landslide')
                #Save a copy of the depth without the landslide
                copyfile(fwo.depth_path, dwlp)
                
            landslide = self.gen_ls(int(result_to_convert) *
                    float(self.TOTAL_TIME) * float(self.PLOT_INTV) /
                    (float(self.TOTAL_TIME) - float(self.PLOT_START)))
            
            print('Adding a landslide to the depth file')  
            #Add the landslide to funwaves depth
            if insert:
                fwo.depth[indices] -= landslide.flatten()
            elif interpolate:
                #nan to num to convert points outside the funwave area,                
                fwo.depth -= np.nan_to_num(griddata((xs, ys),
                        landslide.flatten(),
                        (xx[None,:], yy[:,None]), method=method))
            
            #Replace funwaves depth.txt file
            np.savetxt(fwo.depth_path, fwo.depth, fmt='%5.5g')
            
    