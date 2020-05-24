#Class objects for nhwave and funwave
#Simon Libby 2017

import os
import numpy as np

from tsunamis.models.base import model       
    
class config(model):
    model = 'FUNWAVE'

    def __init__(self,
                 eta_file='eta.txt',
                 u_file='Us.txt',
                 v_file='Vs.txt',
                 **kwargs):
        
        super().__init__(**kwargs)
        
        #TODO do stuff with eta, u, v
        
    @property
    def default_executable_path(self):
        script_folder = os.path.dirname(os.path.abspath(__file__))
        return os.path.abspath(os.path.join(script_folder, './../executables/funwave'))
        
    def make_obstacle_file(self):
        """Needed where some points of the depth are above ground???"""        
        self.obstacles = np.ones_like(self.depth, dtype=int)
        self.obstacles[self.depth <= 0] = 0 #less than beacuse depth not elev
        np.savetxt(self.obstacles_path, self.obstacles, fmt='%1i')
        
        
 