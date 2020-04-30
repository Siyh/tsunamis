# Tab for NHWAVE for Tsunami GUI
# Simon Libby 2020

from PyQt5 import QtWidgets as qw
import numpy as np

from tab_model_base import TabModelBase
from tsunamis.models.nhwave import config as nhwave_config


class TabNHWAVE(TabModelBase):
    
    def __init__(self, parent, initial_directory):
        self.model = nhwave_config()
        
        super().__init__(parent)
        
        #=====================================================================
        # Add nhwave specific inputs
        #=====================================================================
        
        self.add_input('Vertical layers', 'Kglob', 3)        
        self.add_input('Vertical grid distribution', 'IVGRD',
                       ['uniform', 'exponential']) 
        self.add_input('GRD_R', 'GRD_R', 1.1)
        
        self.create_input_group('Landslides', self.recalculate_landslide)
        self.add_input('Slide type', 'SlideType',
                       {'rigid (nhwave 2.0)':'RIGID',
                        'rigid (nhwave 3.0)':'RIGID_3D',
                        'deformable':'DEFORMABLE'})
        self.add_input('Thickness', 'SlideT', 30.0)
        self.add_input('Length', 'SlideL', 200.0)
        self.add_input('Width', 'SlideW', 500.0)
        self.add_input('Direction', 'SlideAngle', 270.0)
        self.add_input('Slope angle', 'SlopeAngle', 10.0)
        # TODO add option to make this relative
        self.add_input('X coordinate', 'SlideX0', 1000.0)
        self.add_input('Y coordinate', 'SlideY0', 1000.0)
        self.add_input('Max speed?', 'SlideUt', 10.0)
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
        self.landside_volume = qw.QLabel()
        self.add_input('Landslide Volume', widget=self.landside_volume, function=False)
        self.recalculate_landslide()
        
        self.create_input_group('Boundary')
        self.add_input('Period boundary condition X', 'PERIODIC_X', False)
        self.add_input('Period boundary condition Y', 'PERIODIC_Y', False)        
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
        self.add_input('Latitude', 'slat', 54.0)
        self.add_input('Barotropic', 'BAROTROPIC', True)
        self.add_input('Non-hydrostatic', 'NON_HYDRO', True)
        self.add_input('Cournat number', 'CFL', 0.5)
        self.add_input('Fourde cap', 'FROUDE_CAP', 0.5)
        self.add_input('Time to ramp up simulation', 'TRAMP', 0.0)
        for o in ['HIGH_ORDER', 'TIME_ORDER']:            
            self.add_input(o, o, {'first':'FIRST', 'second':'SECOND'}) 
        self.add_input('Convection', 'CONVECTION',
                       {'TVD':'TVD', 'HLPA':'HLPA'},
                       default='HLPA')        
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
        
        
        self.create_input_group('Wavemaker')
        self.add_input('Wave type', 'WAVEMAKER', {'None':'NONE'})
        
        #TODO implement sediment, wavemaker, vegetation     
        #TODO implement probes, hotstart parameters, coupling
        
        self.create_input_group('Wave average control')
        self.add_input('Enabled', 'WAVE_AVERAGE_ON ', False)
        self.add_input('Start', 'WAVE_AVERAGE_START', 200.0)
        self.add_input('End', 'WAVE_AVERAGE_END', 1800.0)
        self.add_input('ID', 'WaveheightID', 2)       
        
        
        self.create_input_group('Outputs')
        self.add_input('water depth', 'OUT_H', True,
                       function=self.display_wave_height.setEnabled)
        self.add_input('surface elevation', 'OUT_E', True)
        self.add_input('velocity in x direction', 'OUT_U', True,
                       function=self.vector_output_changed)
        self.add_input('velocity in y direction', 'OUT_V', True,
                       function=self.vector_output_changed)
        self.add_input('velocity in z direction', 'OUT_W', False,
                       function=self.vector_output_changed)
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
        self.add_input('max wave height', 'OUT_M', True,
                       function=self.display_wave_max.setEnabled)
        
        # Implement GUI version of probe outputs
        self.add_input('number of probes', 'NSTAT', 0)
        self.add_input('probe start time', 'PLOT_INTV_STAT', 10.0)
        
        
        self._set_initial_directory(initial_directory)
        
    
    def vector_output_changed(self, _):
        # TODO why isn't this working
        print('Vecotr output changed')
        self.display_wave_vectors.setEnabled(self.pv('OUT_U') or
                                             self.pv('OUT_V') or
                                             self.pv('OUT_W'))

        
    def timestep_changed(self):
        self.recalculate_landslide()          
        super().timestep_changed()
        
        
    def recalculate_landslide(self):
        """Function to generate the bathymetry with landslide"""  
        if self.refresh_pause: return 
        #TODO add an option for subtractive as well as additive landslides
        
        #Rigid landslide 'lumpiness' parameter
        e = 0.717 
        
        alpha0 = np.radians(self.pv('SlideAngle'))
        cosa0 = np.cos(alpha0)
        sina0 = np.sin(alpha0)
        coss0 = np.cos(np.radians(self.pv('SlopeAngle')))   
        
        v = 2 * np.arccosh(1 / e)
        kb = v / self.pv('SlideL')
        kw = v / self.pv('SlideW')
        ut = self.pv('SlideUt')
        a0 = self.pv('SlideA0')
        #Time to terminal velocity        
        t0 = ut / a0
        #Distance of landslide travel before terminal velocity
        s0 = ut ** 2 / a0        
        st = s0 * np.log(np.cosh(self.timestep / t0)) * coss0
        
        x = self.pv('SlideX0')
        y = self.pv('SlideY0')
        if not (self.x0 <= x <= self.x1) or not (self.y0 <= y <= self.y1):
            print(self.x0, x, self.x1)
            print('Landslide centre out of grid bounds')
        lsx = x + st * cosa0 + self.x0
        lsy = y + st * sina0 + self.y0
        
        xsmlsx = self.xs - lsx
        ysmlsy = self.ys - lsy
        xt = ((ysmlsy * sina0 + xsmlsx * cosa0) * kb).clip(min=-100, max=100)
        yt = ((ysmlsy * cosa0 - xsmlsx * sina0) * kw).clip(min=-100, max=100)
        zt = self.pv('SlideT') / (1 - e) * (1 / np.cosh(xt) / np.cosh(yt) - e)
        blob = zt.clip(min=0)
        
        self.plot.draw_bathymetry(self.zs + blob)
        
        vol_est = np.sum(blob * self.pv('DX') * self.pv('DY')) / 1E9
        vol_est_str = '%i' % vol_est if vol_est > 10 else '%.1f' % vol_est        
        self.landside_volume.setText(vol_est_str)

        


if __name__ == '__main__':
    from run_gui import run
    run()