# Tab for NHWAVE for Tsunami GUI
# Simon Libby 2020

from PyQt5 import QtWidgets as qw

from tab_model_base import TabModelBase
from Tsunamis.models.nhwave import config as nhwave_config
from common import create_combo


class TabNHWAVE(TabModelBase):
    
    def __init__(self, parent):
        super().__init__(parent)
        
        self.model = nhwave_config()
        
        # Add nhwave specific inputs
        self.add_input('Vertical layers', 'Kglob', 3)
        
        self.add_input('Vertical grid distribution', 'IVGRD',
                       ['uniform', 'exponential']) 
        self.add_input('GRD_R', 'GRD_R', 1.1)
        
        self.add_input('INITIAL_EUVW', 'INITIAL_EUVW', False)
        self.add_input('INITIAL_SALI', 'INITIAL_SALI', False)
        
        #TODO hotstart parameters, coupling
        
        for o in ['HIGH_ORDER', 'TIME_ORDER']:            
            self.add_input(o, o, {'first':'FIRST', 'second':'SECOND'})            
        self.add_input('Vertical grid distribution', 'IVGRD',
                       {'TVD':'TVD', 'HLPA':'HLPA'},
                       default=1)
        self.add_input('HLLC', 'HLLC', False)
        
        self.add_input('Bottom roughness method', 'Ibot',
                       {'use drag coefficient':1,
                        'use bottom roughness height':2})
        self.add_input('Drag coefficient', 'Cd0', 0.006)
        self.add_input('Bottom roughtness height', 'Zob', 0.0001)
        self.add_input('Dfric_Min', 'Dfric_Min', 0.0)
        
        self.add_input('Wind speed', 'Iws', ['constant', 'variable'])
        self.add_input('WindU', 'WindU', 0.0)
        self.add_input('WindV', 'WindV', 0.0)
        
        self.add_input('Latitude', 'slat', 54)
        self.add_input('Barotropic', 'BAROTROPIC', True)
        self.add_input('Non-hydrostatic', 'NON_HYDRO', True)
        self.add_input('Cournat number', 'CFL', 0.5)
        self.add_input('Fourde cap', 'FROUDE_CAP', 0.5)
        self.add_input('Time to ramp up simulation', 'TRAMP', 0.0)
        
        self.add_input('Viscous flow', 'VISCOUS_FLOW', False)
        self.add_input('IVTURB', 'IVTURB', 10)
        self.add_input('IHTURB', 'IHTURB', 10)
        self.add_input('PRODTYPE', 'PRODTYPE', 3)
        self.add_input('Viscosity', 'VISCOSITY', 1E-6)
        self.add_input('Schmidt', 'Schmidt', 1.0)
        self.add_input('Chs', 'Chs', 0.001)
        self.add_input('Cvs', 'Cvs', 0.001)
        self.add_input('RNG', 'RNG', True)        
        self.add_input('Viscous number', 'VISCOUS_NUMBER', 0.1666667)
        
        self.add_input('Minimum depth for wetting-drying', 'MinDep', 0.1)
        

        self.add_input('Poisson solver', 'ISOLVER',
                       ['Modified Incomplete Cholesky CG',
                        'Incomplete Cholesky GMRES',
                        'Successive Overrelaxation (SOR) GMRES'],
                       default=1)
        self.add_input('Maximum iterations', 'ITMAX', 1000)
        self.add_input('Tolerance', 'TOL', 1E-8)
        
        self.add_input('Period boundary condition X', 'PERIODIC_X', False)
        self.add_input('Period boundary condition Y', 'PERIODIC_y', False)
        
        self.add_input('External forcing', 'EXTERNAL_FORCING', False)
        self.add_input('Pgrad0', 'Pgrad0', 9.81e-4)
        
        for d in ['X', 'Y', 'Z']:
            for v in ['0', 'n']:
                self.add_input('Boundary condition ' + d + v, 'BC_' + d + v,
                               ['free-slip',
                                'no-slip',
                                'influx',
                                'outflux (specified eta)',
                                'bottom friction',
                                'radiation bc'])
        
        




if __name__ == '__main__':
    from run_gui import run
    run()