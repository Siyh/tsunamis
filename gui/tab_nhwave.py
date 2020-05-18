# Tab for NHWAVE for Tsunami GUI
# Simon Libby 2020

from PyQt5 import QtWidgets as qw
import numpy as np
import os

from tab_model_base import TabModelBase
from tsunamis.models.nhwave import config as nhwave_config
from common import sigfigs


class TabNHWAVE(TabModelBase):
    
    def __init__(self, parent):
        self.model = nhwave_config()
        
        # Add varying bathymetry to the list of outputs to load
        self.result_types['depth'] = 'bathymetry'
        
        super().__init__(parent)       
        
        self.refresh_functions.append(self.display_landslide_changed)
        
        #=====================================================================
        # Add nhwave specific inputs
        #=====================================================================
        
        self.add_input('Vertical layers', 'Kglob', 3)        
        self.add_input('Vertical grid distribution', 'IVGRD',
                       ['uniform', 'exponential']) 
        self.add_input('GRD_R', 'GRD_R', 1.1)
        
        self.create_input_group('Landslide Creator', self.recalculate_landslide)
        
        #TODO use https://www.tutorialspoint.com/pyqt/pyqt_qstackedwidget.htm
        # to make options option specific
        
        # Commented options are for the rigid landslide
        # self.add_input('Slide type', 'SlideType',
        #                {'deformable':'DEFORMABLE',
        #                 'rigid (nhwave 2.0)':'RIGID',
        #                 'rigid (nhwave 3.0)':'RIGID_3D'})
        self.add_input('Thickness', 'SlideT', 30.0)
        self.add_input('Length', 'SlideL', 200.0)
        self.add_input('Width', 'SlideW', 500.0)
        self.add_input('Direction', 'SlideAngle', 270.0)
        self.add_input('Slope angle', 'SlopeAngle', 10.0)
        # TODO add option to make this relative
        self.add_input('X coordinate', 'SlideX0', 1000.0)
        self.add_input('Y coordinate', 'SlideY0', 1000.0)
        # self.add_input('Max speed?', 'SlideUt', 10.0)
        # self.add_input('Acceleration', 'SlideA0', 0.37)
        # self.add_input('Density', 'SlideDens', 2100.0)
        # self.add_input('Viscosity', 'SlideVisc', 0.00001)
        # self.add_input('Lambda', 'SlideLambda', 0.5)
        # self.add_input('Inital speed', 'SlideIniU', 0.0)
        # self.add_input('Cf_ul', 'Cf_ul', 0.02)
        # self.add_input('PhiInt', 'PhiInt', 41.0)
        # self.add_input('PhiBed', 'PhiBed', 23.0)
        # self.add_input('Use rheology', 'RHEOLOGY_ON', False)
        # self.add_input('Yield stress', 'Yield_Stress', 10.0)
        # self.add_input('Plastic viscosity', 'Plastic_Visc', 0.0)   
        
        self.landslide_volume = qw.QLabel()
        self.add_input('Landslide Volume', widget=self.landslide_volume, function=False)        
        self.add_button('Output landslide thickness', self.output_landslide)
        
        
        self.create_input_group('Landslides')
        self.add_input('Slide thickness',
                       'SLIDE_FILE',
                       'SlideThickness.txt',
                       function=self.load_slide_thickness,
                       dialogue_label='Select initial slide thickness',
                       formats='txt')
        
        self.add_input('Rheology option', 'RHEO_OPT', {'Viscous':'VISCOUS',
                                                       'Granular':'GRANULAR'})        
        self.add_input('momentum distribution coefficient', 'SLIDE_GAMMA', 1.0)
        self.add_input('use hydrostatic model?', 'NON_HYDRO_SLD', True)
        self.add_input('dispersion correction in non-hydrostatic model', 'DISP_CORR_SLD', True)
        self.add_input('reduced gravitation in non-hydrostatic model', 'REDU_GRAV_SLD', True)
        self.add_input('non-hydrostatic from upper layer', 'NON_HYDRO_UP', True)
        self.add_input('minimum slide thickness', 'SLIDE_MINTHICK', 1E-4)
        self.add_input('initial velocity of slide in x', 'SLIDE_INIU', 0.0)
        self.add_input('initial velocity of slide in y', 'SLIDE_INIV', 0.0)
        self.add_input('initial velocity of slide in z', 'SLIDE_INIW', 0.0)
        self.add_input('viscous slide density (kg/m\u00b3)', 'SLIDE_DENSITY', 1760.0)
        self.add_input('kinematic viscosity of viscous slide (m\u00b2/s)', 'SLIDE_VISCOSITY', 0.5)
        self.add_input('pure grain density', 'GRAIN_DENSITY', 2600.0)
        self.add_input('sediment concentration', 'SLIDE_CONC', 0.475)
        self.add_input('internal friction angle A', 'PhiInt_A', 41.0)
        self.add_input('bed friction angle A', 'PhiBed_A', 23.0)
        self.add_input('internal friction angle F', 'PhiInt_F', 32.0)
        self.add_input('bed friction angle F', 'PhiBed_F', 18.0)
        self.add_input('% of non-hydrostatic pressure', 'SLIDE_LAMBDA', 1.0)

    
        
        self.start_dropdown('Boundary')
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
        self.finish_dropdown()
                
        self.start_dropdown('Sponge boundary')
        self.add_input('Sponge on', 'SPONGE_ON', False)
        for d in ['North', 'East', 'South', 'West']:
            self.add_input(f'Sponge {d.lower()} width',
                           f'Sponge_{d}_Width', 0.0)           
        self.add_input('Maximum iterations', 'ITMAX', 1000)
        self.add_input('Tolerance', 'TOL', 1E-8)
        self.finish_dropdown()        
        
        self.start_dropdown('Wind')
        self.add_input('Wind speed', 'Iws', ['constant', 'variable'])
        self.add_input('WindU', 'WindU', 0.0)
        self.add_input('WindV', 'WindV', 0.0)
        self.finish_dropdown()
        
        self.start_dropdown('To sort')
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
        self.add_input('Minimum depth for wetting-drying', 'MinDep ', 0.01)
        self.finish_dropdown()        
        
        self.start_dropdown('Flow properties')
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
        self.finish_dropdown()  
        
        self.start_dropdown('Solver')
        self.add_input('Poisson solver', 'ISOLVER',
                       ['Modified Incomplete Cholesky CG',
                        'Incomplete Cholesky GMRES',
                        'Successive Overrelaxation (SOR) GMRES'],
                       default=1)
        self.add_input('Maximum iterations', 'ITMAX', 1000)
        self.add_input('Tolerance', 'TOL', 1E-8) 
        self.finish_dropdown()  
        
        
        self.start_dropdown('Wavemaker')
        self.add_input('Wave type', 'WAVEMAKER', {'None':'NONE'})
        self.add_input('AMP', 'AMP', 0.0144)
        self.add_input('PER', 'PER', 10.5)
        self.add_input('DEP', 'DEP', 0.32)
        self.add_input('incident wave angle', 'THETA', 0.0)
        self.add_input('CUR', 'CUR', 0.0)
        self.add_input('sd_return', 'sd_return', 0.75)
        
        #TODO implement sediment, wavemaker, vegetation     
        #TODO implement probes, hotstart parameters, coupling
        self.finish_dropdown()
        
        self.start_dropdown('Wave average control')
        self.add_input('Enabled', 'WAVE_AVERAGE_ON ', False)
        self.add_input('Start', 'WAVE_AVERAGE_START', 200.0)
        self.add_input('End', 'WAVE_AVERAGE_END', 1800.0)
        self.add_input('ID', 'WaveheightID', 2)
        self.finish_dropdown()  
        
        self.start_dropdown('Sediment')
        self.add_input('Sediment option', 'Sed_Type', {'Cohesive':'COHESIVE',
                                                       'Non-cohesive':'NONCOHESIVE'})
        self.add_input('BED_LOAD', 'BED_LOAD', False)
        self.add_input('COUPLE_FS', 'COUPLE_FS', False)
        self.add_input('Af', 'Af', 0.0)
        self.add_input('D50', 'D50', 1.2e-5)
        self.add_input('ntyws', 'ntyws', 1)
        self.add_input('Sedi_Ws', 'Sedi_Ws', 0.00007)
        self.add_input('Shields_c', 'Shields_c', 0.05)
        self.add_input('Tau_ce', 'Tau_ce', 0.15)
        self.add_input('Tau_cd', 'Tau_cd', 0.07)
        self.add_input('Erate', 'Erate', 4.0e-8)
        self.add_input('Mud_Visc', 'Mud_Visc', 1.e-6)
        self.add_input('Tim_Sedi', 'Tim_Sedi', 0.0)
        self.add_input('MorDt', 'MorDt', 0.0)
        self.add_input('BED_CHANGE', 'BED_CHANGE', True)
        self.finish_dropdown()  
        
        self.start_dropdown('Vegetation')
        self.add_input('Veg_Type', 'Veg_Type', ['RIGID'])
        self.add_input('Veg_X0', 'Veg_X0 ', 2.85)
        self.add_input('Veg_Xn', 'Veg_Xn ', 5.3)
        self.add_input('Veg_Y0', 'Veg_Y0 ', 0.0)
        self.add_input('Veg_Yn', 'Veg_Yn ', 0.1)
        self.add_input('VegH', 'VegH ', 0.135)
        self.add_input('VegDens', 'VegDens ', 1250.0)
        self.add_input('VegVol', 'VegVol ', 0.0)
        self.add_input('StemD', 'StemD ', 0.0064)
        self.add_input('VegDrag', 'VegDrag ', 0.8)
        self.add_input('Cfk', 'Cfk ', 1.0)
        self.add_input('Cfe', 'Cfe ', 1.33)
        self.add_input('VegVM', 'VegVM ', 0.0)
        self.add_input('EI', 'EI ', 8.0e-7)
        self.finish_dropdown()  
        
        
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
        
        # TODO Implement GUI version of probe outputs
        self.add_input('number of probes', 'NSTAT', 0)
        self.add_input('probe start time', 'PLOT_INTV_STAT', 10.0)        
        
        
        self.display_landslide = self.add_input('Landslide', value=True,
                                                function=self.display_landslide_changed,
                                                layout=self.plot_options.layout())        
        self.recalculate_landslide()
        
        # Controls for sending the wave to FUNWAVE
        misc = self.misc_options.layout()
        self.final_wave = qw.QRadioButton('Final Wave')
        self.final_wave.setChecked(True)
        misc.addWidget(self.final_wave)

        current_wave = qw.QRadioButton('Current Wave')
        misc.addWidget(current_wave)
        
        button = qw.QPushButton('Send wave to FUNWAVE')
        button.clicked.connect(self.send_wave_to_funwave)
        misc.addWidget(button)
                
        
    def send_wave_to_funwave(self):
        # Get index of the result to convert
        if self.final_wave.isChecked():
            result_to_convert = self.timestepper.maxIndex + 1
        else:
            result_to_convert = self.timestepper.index + 1
        
        # Set the model outputs
        self.set_model_inputs()
        funwave_tab = self.parent.tab_funwave
        funwave_tab.set_model_inputs()
        
        
        
        # And convert
        self.model.nhw_to_funw(fwo=funwave_tab.model,
                               result_to_convert=result_to_convert)
        
        # And make the tab load the new wave
        pass
        
    
    def vector_output_changed(self, _):
        # TODO why isn't this working
        self.display_wave_vectors.setEnabled(self.pv('OUT_U') or
                                             self.pv('OUT_V') or
                                             self.pv('OUT_W'))
        
        
    def display_landslide_changed(self, value=None):
        if value is None: value = self.display_landslide.value()
        if value:
            self.plot.show_landslide(self.results['depth'][self.timestep])
        else:
            self.plot.hide_landslide()
            
    
    def load_slide_thickness(self, path):
        self.results['depth'][self.pv('PLOT_START')] = np.loadtxt(path)
        
        
    def recalculate_landslide(self):
        """Function to generate the bathymetry with landslide"""  
        if self.refresh_pause: return 
        #TODO add an option for subtractive as well as additive landslides
        
        # For anything but rigid landslides, the start of the model run is
        # the only time when the blob can be valid
        self.restart_timestepper()
        
        blob = self.generate_landslide_blob()        
        self.results['depth'][self.pv('PLOT_START')] = -self.zs - blob
        self.display_landslide_changed()
        
        # Write the estimated volume of the landslide
        vol_est = np.sum(blob * self.pv('DX') * self.pv('DY'))
        if vol_est > 1000:
            vol_str = str(sigfigs(vol_est) / 1E9) + ' km\u00b3'
        else:
            vol_str = str(sigfigs(vol_est)) + ' m\u00b3'
            
        self.landslide_volume.setText(vol_str)
        
        
    def output_landslide(self):
        blob = self.generate_landslide_blob()
        np.savetxt(os.path.join(self.model_folder, 'SlideThickness.txt'), blob)
        
        
    def generate_landslide_blob(self):
        #Rigid landslide 'lumpiness' parameter
        e = 0.717 
        
        alpha0 = np.radians(self.pv('SlideAngle'))
        cosa0 = np.cos(alpha0)
        sina0 = np.sin(alpha0)         
        
        v = 2 * np.arccosh(1 / e)
        kb = v / self.pv('SlideL')
        kw = v / self.pv('SlideW')
        
        # This commented out section for rigid landsides
        # ut = self.pv('SlideUt')
        # a0 = self.pv('SlideA0')
        # #Time to terminal velocity        
        # t0 = ut / a0
        # #Distance of landslide travel before terminal velocity
        # s0 = ut ** 2 / a0        
        # coss0 = np.cos(np.radians(self.pv('SlopeAngle')))  
        # st = s0 * np.log(np.cosh(self.timestep / t0)) * coss0
        
        x = self.pv('SlideX0')
        y = self.pv('SlideY0')
        if not (self.x0 <= x <= self.x1) or not (self.y0 <= y <= self.y1):
            print(self.x0, x, self.x1)
            print('Landslide centre out of grid bounds')
        lsx = x + self.x0 # + st * cosa0
        lsy = y + self.y0 # + st * sina0
        
        xsmlsx = self.xs - lsx
        ysmlsy = self.ys - lsy
        xt = ((ysmlsy * sina0 + xsmlsx * cosa0) * kb).clip(min=-100, max=100)
        yt = ((ysmlsy * cosa0 - xsmlsx * sina0) * kw).clip(min=-100, max=100)
        zt = self.pv('SlideT') / (1 - e) * (1 / np.cosh(xt) / np.cosh(yt) - e)
        
        return zt.clip(min=0)
    

        


if __name__ == '__main__':
    from run_gui import run
    run()