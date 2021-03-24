# Tab for FUNWAVE for Tsunami GUI
# Simon Libby 2020

from tab_model_base import TabModelBase
from tsunamis.models.funwave import config as funwave_config
# from PyQt5 import QtGui
from PyQt5 import QtWidgets as qw
import os
from tsunamis.utilities.io import read_grid
from common import InputGroup


class TabFUNWAVE(TabModelBase):    
    def __init__(self, parent):
        self.model = funwave_config()
        
        self.mask_extra_depth_parameter = 'MinDepth'

        
        super().__init__(parent)
        
        self.bathymetry_group.add_input('Depth file',
                                        'DEPTH_FILE',
                                        'depth.txt',
                                        dialogue_label='Set bathymetry depth file',
                                        formats='txt',                       
                                        layout=self.bathymetry_group.layout())
        
        g = InputGroup(self, 'Initial wave')               
        g.add_input('Use initial wave', 'INI_UVZ', True, group_enabler=True)
        g.add_button('Load initial wave folder from folder',
                     self.load_initial_wave_from_folder),
        g.add_input('wave height',
                    'ETA_FILE',
                    value='eta.txt',
                    dialogue_label='Set initial wave height',
                    formats='txt')
        g.add_input('wave u vector',
                    'U_FILE',
                    value='Us.txt',
                    dialogue_label='Set initial wave u vector',
                    formats='txt')
        g.add_input('wave v vector',
                    'V_FILE',
                    value='Vs.txt',
                    dialogue_label='Set initial wave v vector',
                    formats='txt')
        
        g = InputGroup(self, 'Miscellaneous')
        g.add_input('Depth type', 'DEPTH_TYPE',
                    {'from depth file':'DATA',
                     'idealized flat':'FLAT',
                     'idealized slope':'SLOPE'})
        g.add_input('High order', 'HIGH_ORDER',
                    {'third':'THIRD'})
        g.add_input('CFL', 'CFL', 0.5)
        g.add_input('Froude number cap', 'FroudeCap', 2.0)
        g.add_input('Minimum depth for wetting-drying', 'MinDepth', 1.0)
        g.add_input('Minimum depth to limit bottom friction', 'MinDepthFrc', 1.0)
        
        
        g = InputGroup(self, 'Sponge layer')
        g.add_input('Direct sponge', 'SPONGE_ON', True)
        g.add_input('Friction sponge', 'FRICTION_SPONGE', True)
        g.add_input('A constant', 'A_sponge', 5.0)
        g.add_input('R constant', 'R_sponge', 0.85)
        for d in ['north', 'east', 'south', 'west']:
            g.add_input(f'Sponge {d} width',
                        f'Sponge_{d}_Width', 0.0)           
        g.add_input('SWE_ETA_DEP', 'SWE_ETA_DEP', 0.6)
        g.add_input('Cd', 'Cd', 0.001)
        g.add_input('Depth type', 'Time_Scheme',
                    {'Runge Kutta':'Runge_Kutta'})
        
        g = InputGroup(self, 'Outputs')
        g.add_input('water depth', 'ETA', True,
                    function=self.display_wave_height.setEnabled)
        g.add_input('velocity in x direction', 'U', True,
                    function=self.vector_output_changed)
        g.add_input('velocity in y direction', 'V', True,
                    function=self.vector_output_changed)   
        g.add_input('max wave height', 'Hmax', True,
                    function=self.display_wave_max.setEnabled)
        
        # TODO Implement GUI version of probe outputs
        g.add_input('number of stations', 'NumberStations ', 0)
        g.add_input('Stations files',
                    'STATIONS_FILE',
                    value='stations.txt',
                    dialogue_label='Set stations file',
                    formats='txt')
        
        self.initial_wave_folder = None
        
        self.fps = 10
        
        
    def load_directory_extras(self):
        # Load the initial changes
        self.load_initial_wave()
        
        
    
    def load_initial_wave_from_folder(self):     
        # Check if a folder has already been specified
        if self.initial_wave_folder is None:
            initial = self.model_folder.value()
        else:
            initial = self.initial_wave_folder
            
        path = qw.QFileDialog.getExistingDirectory(self,
                                                   'Select initial wave folder',
                                                   initial)
        if path:
            # Remember the folder specified
            self.initial_wave_folder = path
            # Copy the files into the model folder
            for p, v in [('ETA_FILE', 'eta'), ('U_FILE', 'Us'), ('V_FILE', 'Vs')]:
                pass
                # TODO, join this folder with p variable b
            self.load_initial_wave()
        
        
    def load_initial_wave(self):        
        self.restart_timestepper()     
        
        # Load the initial waves
        start = self.pv('PLOT_START')        
        for p, v in [('ETA_FILE', 'eta'), ('U_FILE', 'Us'), ('V_FILE', 'Vs')]:
            path = os.path.join(self.model_folder.value(), self.pv(p))
            if os.path.isfile(path):
                self.results[v][start] = read_grid(path)
            else:
                print(f'Specified {p} {self.pv(p)} not found at "{path}"')
            
        self.refresh_plots()
        
            
    def vector_output_changed(self, _):
        self.display_wave_vectors.setEnabled(self.pv('OUT_U') or
                                             self.pv('OUT_V'))

        
if __name__ == '__main__':
    from run_gui import run
    run()
    