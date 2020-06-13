# Functions for IO to Tsunami GUI
# Simon Libby and Marcus Wild 2020

import numpy as np
from multiprocessing import Pool



def read_configuration_file(path):     
    parameters = {}
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                if line[0] != '!':
                    try:
                        k, vs = line.split(' = ')
                    except:
                        print('Odd line: ' + line)
                        continue
                    try:                            
                        # Might be a better way to check for different float types
                        if any(c in vs for c in ['.', 'e', 'E']):
                            v = float(vs) 
                        else:
                            v = int(vs)
                    except ValueError:
                        if vs == 'T':
                            v = True
                        elif vs == 'F':
                            v = False
                        else:
                            v = vs
                    parameters[k] = v
                    
    return parameters


def read_results(target, timesteps, file_list, result_type):          
    """
    Read grids of numbers in parallel         
    """
    n = len(file_list)
    with Pool() as pool:        
        for i, (time, result) in enumerate(zip(timesteps,
                                               pool.imap(read_grid, file_list))):
           print('\rLoading {} {} of {}'.format(result_type, i + 1, n), end='')
           target[time] = result
        print()
        
        
def read_grid(path):
    return np.loadtxt(path)



                
def xyz_to_grid(path, elevation=True):
    """
    Convert an ascii file of xyz coordinates to a depth grid.
    also returns Mglob, Nglob, DX and DY
    """
    print('Loading xyz data')
    xs, ys, zs = np.loadtxt(path, unpack=True)
    
    xs = np.unique(xs)
    ys = np.unique(ys)
    minx = np.min(xs)
    maxx = np.max(xs)
    miny = np.min(ys)
    maxy = np.max(ys)
    xn = xs.size
    yn = ys.size
    dx = (maxx - minx) / xn
    dy = (maxy - miny) / yn        
    
    print('Converting xyz data to grid')        
    return zs.reshape((yn, xn)), xn, yn, dx, dy
    
    
    
    
def evg_to_grid(evg_path, elevation=True, to_cell_centre=True):
    """
    Convert from earthvision grid to depth grid
    also returns Mglob, Nglob, DX and DY
    """
    print('Loading EarthVision Grid data')
    xs, ys, zs, Xi, Yi = np.loadtxt(evg_path, skiprows=20, unpack=True)        
    
    yn = int(np.max(Yi))
    xn = int(np.max(Xi))
    zz = np.ndarray((yn, xn))
    #Convert columns/rows to indicies
    yis = (Yi - np.min(Yi)).astype(int)
    xis = (Xi - np.min(Xi)).astype(int)
    #Put zs in right place on grid
    zz[yis, xis] = zs
    
    if to_cell_centre:
        print('Approximating to cell centre')
        yn -= 1
        xn -= 1
        #Change grid to cell center
        depth = np.ndarray((yn, xn))
        #Iterate over all but the last cell
        for yi, xi in np.ndindex(yn, xn):
            #Calculate mean of each cell
            depth[yi, xi] = (zz[yi, xi] + zz[yi, xi + 1] +
                zz[yi + 1, xi] + zz[yi + 1, xi + 1]) / 4
    
    minx = np.min(xs)
    maxx = np.max(xs)
    miny = np.min(ys)
    maxy = np.max(ys)
    dx = (maxx - minx) / xn
    dy = (maxy - miny) / yn

    return depth    , xn, yn, dx, dy
        
        
        
