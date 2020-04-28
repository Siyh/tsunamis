# Base tab for NHWAVE and FUNWAVE showing a 3D viewer window and config options
# Simon Libby 2020

from PyQt5 import QtWidgets as qw
from PyQt5.QtCore import Qt
import numpy as np
import os
import requests
from PIL import Image
import datetime
from glob import glob


from mayavi_widget import MayaviQWidget, mlab
from common import WidgetMethods, build_wms_url, DoubleSlider
from tsunamis.utilities.io import read_configuration_file, read_results

class TabModelBase(qw.QSplitter, WidgetMethods):
    
    def __init__(self, parent, model_folder=''):
        super().__init__(parent)
        
        self.results_folder = 'results'
        self.configuration_path = 'input.txt'
        self.depth_path = 'depth.txt'
        self.parameters = {}
        
        # Make all the components
        config_input_widget = qw.QWidget()
        self.input_layout = qw.QVBoxLayout()
        config_input_widget.setLayout(self.input_layout)
        
        self.config_input_scroller = qw.QScrollArea()
        self.config_input_scroller.setWidgetResizable(True)
        self.config_input_scroller.setWidget(config_input_widget)
        self.config_input_scroller.setMinimumWidth(400)
        
        viewer = qw.QWidget()
        self.plot = MayaviQWidget(self)
        plot_controls = qw.QWidget()
        
        # Arrange them
        viewersplit = qw.QVBoxLayout()
        viewersplit.addWidget(self.plot)
        viewersplit.addWidget(plot_controls)
        viewer.setLayout(viewersplit)
        
        self.addWidget(self.config_input_scroller)
        self.addWidget(viewer)   
        
        steppersplit = qw.QVBoxLayout()
        plot_buttons = qw.QWidget()
        self.timestepper = DoubleSlider(orientation=Qt.Horizontal)
        self.timestepper.setTickPosition(qw.QSlider.TicksBelow)
        self.timestepper.valueChanged.connect(self.timestep_changed)
        steppersplit.addWidget(plot_buttons)
        steppersplit.addWidget(self.timestepper)
        plot_controls.setLayout(steppersplit)
        plot_options = self.create_input_group('Plot options',
                                                  main_layout=False)
        self.display_wave_height = self.add_input('Wave height', value=True,
                                                  function=self.display_wave_height_changed)
        self.display_wave_max = self.add_input('Maximum wave height', value=False,
                                               function=self.display_wave_max_changed)
        self.display_wave_vectors = self.add_input('Wave vectors', value=False,
                                                   function=self.display_wave_vectors_changed)
        
        display_options = self.create_input_group('Display options',
                                                  main_layout=False)
        self.vertical_exaggeration = self.add_input('Vertical exaggeration', value=10,
                                                    function=self.plot.set_vertical_exaggeration)
        self.plot.set_vertical_exaggeration(10)

        
        stepper_buttons = qw.QHBoxLayout()
        stepper_buttons.setAlignment(Qt.AlignRight)
        plot_control_layout = qw.QHBoxLayout()
        plot_control_layout.addWidget(plot_options)
        plot_control_layout.addWidget(display_options)
        plot_control_layout.addLayout(stepper_buttons)
        plot_buttons.setLayout(plot_control_layout)
        
        self.play_pause_button = qw.QPushButton('|>') 
        next_step = qw.QPushButton('>') 
        previous_step = qw.QPushButton('<') 
        restart = qw.QPushButton('<<') 
        
        self.play_pause_button.clicked.connect(self.play_pause_clicked)
        next_step.clicked.connect(self.next_timestep)
        previous_step.clicked.connect(self.previous_timestep)
        restart.clicked.connect(self.restart_timestepper)
        
        stepper_buttons.addWidget(restart)
        stepper_buttons.addWidget(previous_step)
        stepper_buttons.addWidget(next_step)
        stepper_buttons.addWidget(self.play_pause_button)
        
        
        self.playing = False
        
        #=====================================================================
        # Setup inputs
        #=====================================================================
        
        #TODO set tooltips using .setToolTip
        self.create_input_group('General')        
        self.add_button('Run ' + self.model.model, self.run_model_clicked)  
        
        self.add_button('Set model folder', self.set_model_folder) 
        self.add_button('Set results folder', self.set_results_folder)      
        self.add_button('Load configuration', self.set_configuration_file)
        self.add_input('Processor number X', 'PX', 2)
        self.add_input('Processor number Y', 'PY', 2)
        
        self.create_input_group('Run setup')
        self.add_input('Model run title', 'TITLE', 'test')
        step_widget = self.add_input('Simulation steps', 'SIM_STEPS', 1000)   
        step_widget.setSingleStep(100)
        #TODO make this accept different units of time, not just seconds
        self.add_input('Total time', 'TOTAL_TIME', 300.0, function=self.total_time_changed)
        self.timestepper.setMaximum(300)
        self.add_input('Output time start', 'PLOT_START', 0.0, function=self.plot_start_changed)
        self.timestepper.setMinimum(0.0)
        output_interval = self.add_input('Output interval', 'PLOT_INTV', 10.0,
                                         function=self.plot_interval_changed)
        output_interval.setMinimum(1E-5)
        self.timestepper.setInterval(10.0)
        self.recalculate_timesteps()
        
        self.add_input('Screen output interval', 'SCREEN_INTV', 10.0)
        self.add_input('Initial timestep size', 'DT_INI', 2.0)
        self.add_input('Minimium timestep', 'DT_MIN', 0.01)
        self.add_input('Maximum timestep', 'DT_MAX', 10.0)
        # TODO implement hotstarting
        self.add_input('Hotstart', 'HOTSTART', False)
        
        
        self.create_input_group('Bathymetry', self.make_grid_coords)
        self.add_button('Load bathymetry from grid', self.set_depth_file)
        self.add_button('Load bathymetry from map', self.download_bathymetry)
        
        self.add_input('Number of cells in the X direction', 'Mglob', 400)
        self.add_input('Number of cells in the Y direction', 'Nglob', 300)        

        #TODO Interpolation of bathymetry 
        self.add_input('Grid size X', 'DX', 5.0)
        self.add_input('Grid size Y', 'DY', 5.0)

        self.add_input('Bathymetry grid type', 'DEPTH_TYPE',
                       {'Cell centred':'CELL_CENTER',
                        'Cell vertex aligned':'CELL_GRID'})        
        self.add_input('Analytical bathymetry', 'ANA_BATHY', False)
        self.add_input('DepConst', 'DepConst', 0.3)        
        
        self.x0 = 0
        self.y0 = 0
        self.make_grid_coords()
        
        # Make dummy zs
        self.zs = (self.ys - self.ys.max()) / 2        
        
        self.plot.draw_bathymetry(self.zs)
        
        if model_folder:
            self.model_folder = model_folder
            self.load_directory()
        else:
            # TODO this is windows specific
            self.model_folder = os.path.join(os.environ['USERPROFILE'],
                                             'Desktop',
                                             self.model.model) 
        
   
        
    def display_wave_height_changed(self):
        if self.display_wave_height.isChecked():
            self.plot.draw_wave_height(self.wave_heights[self.timestep])
        else:
            self.plot.hide_wave_height()
        
    def display_wave_max_changed(self):
        if self.display_wave_max.isChecked():
            pass
        
    def display_wave_vectors_changed(self):
        if self.display_wave_vectors.isChecked():
            pass
            
        
    def recalculate_timesteps(self):
        self.timesteps = np.arange(self.pv('PLOT_START'),
                                   # Extra to make the end time inclusive
                                   self.pv('TOTAL_TIME') + self.pv('PLOT_INTV') / 2,
                                   self.pv('PLOT_INTV'))
        
        # Create a dictionary to hold the results
        empty = {t: None for t in self.timesteps}
        
        # Copy this dictionary for each value, probably a better way of doing this
        self.wave_heights = {**empty}
        self.wave_maxs = {**empty}
        self.wave_us = {**empty}
        self.wave_vs = {**empty}
        
        
    def total_time_changed(self, value):
        self.timestepper.setMaximum(value)
        self.recalculate_timesteps()
        
        
    def plot_start_changed(self, value):
        self.timestepper.setMinimum(value)
        self.recalculate_timesteps()
        
        
    def plot_interval_changed(self, value):
        self.timestepper.setInterval(value)
        self.recalculate_timesteps()
        
        
    @property
    def timestep(self):
        return self.timestepper.value()
    
    
    @property
    def num_of_timesteps(self):
        return int((self.pv('TOTAL_TIME') - self.pv('PLOT_START'))
                   / self.pv('PLOT_INTV'))
    
    
    def timestep_changed(self):
        time = datetime.timedelta(seconds=self.timestep)
        self.plot.timestep_label.input = str(time)
        
        wave = self.wave_heights[self.timestep]
        if wave is None:
            self.plot.hide_wave_height()
        else:
            self.plot.draw_wave_height(wave)
        
        
    def play_pause_clicked(self):
        #TODO make this initiate the animate
        if self.playing:
            self.playing = False
            self.play_pause_button.setText('|>')
            
            # Make it stop playings
            self.animator.timer.Stop()
        else:
            self.playing = True
            self.play_pause_button.setText('||')
            
            # Make it play
            if hasattr(self, 'animator'):
                self.animator.timer.Start(100)
            else:
                self.animator = self.animate()
                
                
    @mlab.animate(delay=100, ui=False)    
    def animate(self):
        #So that the animation loop stops when the window is closed
        while self.playing:
            if self.timestep == self.pv('TOTAL_TIME'):
                # Go back to the start if it reached the end
                self.restart_timestepper()
            else:
                self.next_timestep()
            yield
            
    
    def next_timestep(self):
        self.timestepper.setIndex(self.timestepper.index + 1)
        
        
    def previous_timestep(self):
        self.timestepper.setIndex(self.timestepper.index - 1)
        
        
    def restart_timestepper(self):
        self.timestepper.setValue(0)
        
        
    def make_grid_coords(self):
        dx = self.parameters['DX'].value()
        dy = self.parameters['DY'].value()
        self.x1 = self.x0 + dx * self.parameters['Mglob'].value()
        self.y1 = self.y0 + dy * self.parameters['Nglob'].value()
        self.xs, self.ys = np.meshgrid(np.arange(self.x0, self.x1, dx),
                                       np.arange(self.x0, self.y1, dy))
        self.plot.set_location(self.xs, self.ys)

        
    def download_bathymetry(self):
        # Get the bathmetry limits from the maps tab
        xmin, xmax, ymin, ymax = self.tab_map.box_limits(self.model.model)
        
        url = build_wms_url(xmin=xmin, xmax=xmax,
                            ymin=ymin, ymax=ymax,
                            data_format='image/tiff',
                            layer='gebco_2019_grid_2')
        
        response = requests.get(url, stream=True)
        print('Downloading...', end='')
        tiff = response.content
        print(' done.')
        # TODO sort
        with Image.open(tiff) as image:         
             elevation_colours = np.array(image) 
        
        print(elevation_colours)
        
        #TODO map colours to elevation        

    
        
    def set_depth_file(self):
        
        formats = ['Any compatible (*.nc *.asc, *.txt)',
                   'NetCDF (*.nc)',
                   'Arc Ascii (*.asc)',
                   'Ascii elevation array (*.txt)',
                   'Other (*.*)']

        fname, extension = qw.QFileDialog.getOpenFileName(self,
                                                          'Open depth grid',
                                                          self.model_folder,
                                                          ';;'.join(formats))
        if fname: 
            self.load_depth_file(fname)
            
            
    def set_results_folder(self):        
        # TODO make this relative to self.directory
        folder = qw.QFileDialog.getExistingDirectory(self,
                                                     'Select {} results folder'.format(self.model.model),
                                                     self.model_folder)   
        if folder:
            self.results_folder = folder        
            self.load_results()
        
    
    def set_model_folder(self):        
        folder = qw.QFileDialog.getExistingDirectory(self,
                                                     'Select {} folder'.format(self.model.model),
                                                     self.model_folder) 
        if folder:
            self.model_folder = folder
            self.load_directory()
            
            
    def set_configuration_file(self):        
        fname, extension = qw.QFileDialog.getOpenFileName(self,
                                                          'Open {} configuration file'.format(self.model.model),
                                                          self.model_folder,
                                                          'Text file (*.txt);;Other (*.*)')
        if fname:
            self.configuration_path = fname
            self.load_configuration_file(fname)
            
        
    def load_depth_file(self, path):
        
        extension = path.rsplit('.', 1)[1].lower()
        
        if extension == 'nc':
            self.load_netcdf(path)
        elif extension == 'asc':
            self.load_arcascii(path)
        elif extension == 'txt':
            self.zs = -np.loadtxt(path)
            
        # Set cell size according to file if appropriate
        #self.parameters['DX'].setValue()
        
        ny, nx = self.zs.shape
        self.parameters['Mglob'].setValue(nx)
        self.parameters['Nglob'].setValue(ny)    
        
        self.make_grid_coords()
        
        self.plot.draw_bathymetry(self.zs)        
        
        
    def load_directory(self):
        """
        For loading everything possible when a new modelling directory is given
        """
        # If the inputs exists then load them
        for check_path, function in [(self.configuration_path, self.load_configuration_file),
                                     (self.depth_path, self.load_depth_file)]:
            
            path = os.path.join(self.model_folder, check_path)
            # Check if the check_path is relative
            if os.path.exists(path):
                function(path)
            # Check if the check_path is absolute        
            elif os.path.exists(check_path):
                function(check_path)
            else:
                # If the path isn't valid, don't continue
                return  
            
        self.load_results()
        

    def load_configuration_file(self, path):
        # Load parameters from input text file
        loadedParameters = read_configuration_file(path)
        # Run for the provided tab
        for key, value in loadedParameters.items():
            if key in self.parameters:
                try:
                    self.parameters[key].setValue(value)
                except TypeError:
                    print('parameter {} with value {} has unexpected type'.format(key, value))
                    print(type(value), 'instead of type', type(self.parameters[key].value()))

 
    
    def load_arcascii(self, path):
        with open(path) as f:
            header = {}
            for _ in range(6):
                name, value = f.readline().split(' ', 1)
                header[name] = float(value)
                
        self.zs = np.loadtxt(path, skiprows=6)
        
        xstart = header['xllcorner']
        ystart = header['yllcorner']
        
        nx = int(header['ncols'])
        ny = int(header['nrows'])        
        self.parameters['Mglob'].setValue(nx)
        self.parameters['Nglob'].setValue(ny)
        
        d = header['cellsize']
        self.parameters['DX'].setValue(d)
        self.parameters['DY'].setValue(d)
        
        self.xs, self.ys = np.meshgrid(np.linspace(xstart, xstart + d * nx, nx),
                                       np.linspace(ystart, ystart + d * ny, ny))
        
    
    
    def load_netcdf(self, path):
        pass
    
    
    def update_map_box(self):
        #TODO find a better place for this function
        new_box = self.tab_map.box_coordinates(self.model.model)
        self.map_box.data.update(new_box)
        #TODO do this without rerendering the map
        self.tab_map.map.update()
        

    def pv(self, parameter):
        """
        Convenience method to get a parameter value
        """
        return self.parameters[parameter].value()
    
    
    def run_model_clicked(self):
        # Set parameters
        for k, w in self.parameters.items():
            self.model.parameters[k] = w.value()            
        self.model.parameters['RESULT_FOLDER'] = self.results_folder            
        self.model.depth = -self.zs            
        self.model.output_directory = self.model_folder
        
        # Output them
        self.model.write_config()
        
        # And run
        run = self.model.run()
        
        if run: self.read_results()
        
        
    def load_results(self):
        # Check if there are any results and load them   
        
        folder = os.path.join(self.model_folder, self.results_folder)
        # Check if the results path is relative
        if not os.path.isdir(folder):
            # Check if the results path is absolute
            if os.path.isdir(self.results_folder):
                folder = self.results_folder
            else:
                # If the folder isn't valid, don't try and load the results
                return             

        #TODO generalise this function so it can load other types       
        # Get a list of the results
        files = glob(os.path.join(folder, 'eta_*'))
        
        if not files: return
        # Sort the files by the number at the end of the file
        file_list = sorted(files, key=lambda name: int(name[-5:]))        
        
        # No wave for the first timestep
        self.wave_heights[self.timesteps[0]] = np.zeros_like(self.zs)
        
        # Load the remaining waves
        read_results(self.wave_heights, self.timesteps[1:], file_list)

        # for i, (time, path) in enumerate(zip(self.timesteps[1:], file_list)):
        #     print('\rLoading output {} of {}'.format(i + 1, len(file_list)), end='')
        #     self.wave_heights[time] = np.loadtxt(path)
        # print()
        
        self.display_wave_height_changed()
        

        
        
        
        
if __name__ == '__main__':
    from run_gui import run
    run()