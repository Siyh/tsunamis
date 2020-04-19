# Tab for NHWAVE for Tsunami GUI
# Simon Libby 2020

from PyQt5 import QtWidgets as qw
import numpy as np

from tab_model_base import TabModelBase
from tsunamis.models.nhwave import config as nhwave_config


class TabNHWAVE(TabModelBase):
    
    def __init__(self, parent, initial_directory):
        self.model = nhwave_config()
        
        super().__init__(parent, initial_directory)
        
        
        

        
        #=====================================================================
        # Add nhwave specific inputs
        #=====================================================================
        
        self.add_input('Vertical layers', 'Kglob', 3)        
        self.add_input('Vertical grid distribution', 'IVGRD',
                       ['uniform', 'exponential']) 
        self.add_input('GRD_R', 'GRD_R', 1.1)
        self.add_input('Vertical grid distribution', 'IVGRD',
                       {'TVD':'TVD', 'HLPA':'HLPA'},
                       default=1)
        
        self.create_input_group('Landslides', self.recalculate_landslide)
        self.add_input('Slide type', 'SlideType',
                       {'rigid':'RIGID_3D', 'deformable':'DEFORMABLE'})
        self.add_input('Thickness', 'SlideT', 30.0)
        self.add_input('Length', 'SlideL', 200.0)
        self.add_input('Width', 'SlideW', 500.0)
        self.add_input('Direction', 'SlideAngle', 270.0)
        self.add_input('Slope angle', 'SlopeAngle', 10.0)
        self.add_input('X coordinate', 'SlideX0', 1000.0)
        self.add_input('Y coordinate', 'SlideY0', 1000.0)
        self.add_input('Max speed?', 'SlideUt', 10)
        self.add_input('Acceleration', 'SlideA0', 0.37)
        self.add_input('Density', 'SlideDens', 2100.0)
        self.add_input('Viscosity', 'SlideVisc', 0.00001)
        self.add_input('Lambda', 'SlideLambda', 0.5)
        self.add_input('Inital speed', 'SlideIniU', 0.0)
        self.add_input('Cf_ul', 'Cf_ul', 0.02)
        self.add_input('PhiInt', 'PhiInt', 41.0)
        self.add_input('PhiBed', 'PhiBed', 23.0)
        self.add_input('Use rheology', 'RHEOLOGY_ON', False)
        self.add_input('Yield stress', 'Yield_Stress', 10.0)
        self.add_input('Plastic viscosity', 'Plastic_Visc', 0.0)
        self.recalculate_landslide()
        
        self.create_input_group('Boundary')
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
                
        self.create_input_group('Sponge boundary')
        self.add_input('Sponge on', 'SPONGE_ON', False)
        for d in ['North', 'East', 'South', 'West']:
            self.add_input('Sponge {} width'.format(d.lower()),
                           'Sponge_{}_Width'.format(d), 0.0)            
            
        self.add_input('Maximum iterations', 'ITMAX', 1000)
        self.add_input('Tolerance', 'TOL', 1E-8)
        
        self.create_input_group('Wind')
        self.add_input('Wind speed', 'Iws', ['constant', 'variable'])
        self.add_input('WindU', 'WindU', 0.0)
        self.add_input('WindV', 'WindV', 0.0)
        
        self.create_input_group('To sort')
        self.add_input('INITIAL_EUVW', 'INITIAL_EUVW', False)
        self.add_input('INITIAL_SALI', 'INITIAL_SALI', False)
        self.add_input('Latitude', 'slat', 54)
        self.add_input('Barotropic', 'BAROTROPIC', True)
        self.add_input('Non-hydrostatic', 'NON_HYDRO', True)
        self.add_input('Cournat number', 'CFL', 0.5)
        self.add_input('Fourde cap', 'FROUDE_CAP', 0.5)
        self.add_input('Time to ramp up simulation', 'TRAMP', 0.0)
        for o in ['HIGH_ORDER', 'TIME_ORDER']:            
            self.add_input(o, o, {'first':'FIRST', 'second':'SECOND'})            
        self.add_input('Minimum depth for wetting-drying', 'MinDep', 0.1)
        self.add_input('HLLC', 'HLLC', False)        
        self.add_input('Bottom roughness method', 'Ibot',
                       {'use drag coefficient':1,
                        'use bottom roughness height':2})
        self.add_input('Drag coefficient', 'Cd0', 0.006)
        self.add_input('Bottom roughtness height', 'Zob', 0.0001)
        self.add_input('Dfric_Min', 'Dfric_Min', 0.0)
        
        self.create_input_group('Flow properties')
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
        
        self.create_input_group('Solver')
        self.add_input('Poisson solver', 'ISOLVER',
                       ['Modified Incomplete Cholesky CG',
                        'Incomplete Cholesky GMRES',
                        'Successive Overrelaxation (SOR) GMRES'],
                       default=1)
        self.add_input('Maximum iterations', 'ITMAX', 1000)
        self.add_input('Tolerance', 'TOL', 1E-8)        
        
        #TODO implement sediment, wavemaker, vegetation           
        #TODO implement probes, hotstart parameters, coupling
        
        self.create_input_group('Outputs')
        self.add_input('water depth', 'OUT_H', True)
        self.add_input('surface elevation', 'OUT_E', True)
        self.add_input('velocity in x direction', 'OUT_U', True)
        self.add_input('velocity in y direction', 'OUT_V', False)
        self.add_input('velocity in z direction', 'OUT_W', False)
        self.add_input('dynamic pressure', 'OUT_P', False)
        self.add_input('turbulent kinetic energy', 'OUT_K', False)
        self.add_input('turbulent dissipation rate', 'OUT_D', False)
        self.add_input('shear production', 'OUT_S', False)
        self.add_input('eddy viscosity', 'OUT_C', False)
        self.add_input('bubble void fraction', 'OUT_B', False)
        self.add_input('Reynolds stress', 'OUT_A', False)
        self.add_input('bottom shear stress', 'OUT_T', False)
        self.add_input('sediment concentration', 'OUT_F', False)
        self.add_input('bed elevation', 'OUT_G', False)
        self.add_input('salinity', 'OUT_I', False)
        self.add_input('varying bathymetry', 'OUT_Z', False)
        self.add_input('max wave height', 'OUT_M', True)
        
        
    def timestep_changed(self):
        self.recalculate_landslide()          
        super().timestep_changed()
        
        
    def recalculate_landslide(self):
        """Function to generate the bathymetry with landslide"""  
        #TODO add an option for subtractive as well as additive landslides
        
        #Rigid landslide 'lumpiness' parameter
        e = 0.717 
        
        alpha0 = np.radians(self.pv('SlideAngle'))
        cosa0 = np.cos(alpha0)
        sina0 = np.sin(alpha0)
        coss0 = np.cos(np.radians(self.pv('SlopeAngle')))   
        
        v = 2.0 * np.arccosh(1.0 / e)
        kb = v / self.pv('SlideL')
        kw = v / self.pv('SlideW')
        ut = self.pv('SlideUt')
        a0 = self.pv('SlideA0')
        #Time to terminal velocity        
        t0 = ut / a0
        #Distance of landslide travel before terminal velocity
        s0 = ut ** 2 / a0
        
        st = s0 * np.log(np.cosh(self.timestep / t0)) * coss0
        lsx = self.pv('SlideX0') + st * cosa0 + self.xs[0, 0]
        lsy = self.pv('SlideY0') + st * sina0 + self.ys[0, 0]
        
        xsmlsx = self.xs - lsx
        ysmlsy = self.ys - lsy
        xt = xsmlsx * cosa0 + ysmlsy * sina0
        yt = -xsmlsx * sina0 + ysmlsy * cosa0
        zt = self.pv('SlideT') / (1 - e) * (1 / np.cosh(kb * xt) / np.cosh(kw * yt) - e)
        blob = zt.clip(min=0)
        vol_est = np.sum(blob * self.pv('DX') * self.pv('DY')) / 1E9
        self.vol_est = '%i' % vol_est if vol_est > 10 else '%.1f' % vol_est
        self.bathymetry = self.zs + blob
        self.plot.draw_bathymetry()
        



if __name__ == '__main__':
    from run_gui import run
    run()