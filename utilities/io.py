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
                                               pool.imap(np.loadtxt, file_list))):
           print('\rLoading {} {} of {}'.format(result_type, i + 1, n), end='')
           target[time] = result
        print()
        
        
        
