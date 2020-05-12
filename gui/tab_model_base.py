# Base tab for NHWAVE and FUNWAVE showing a 3D viewer window and config options
# Simon Libby 2020

from PyQt5 import QtWidgets as qw
from PyQt5.QtCore import Qt, pyqtSlot
import numpy as np
import os
import requests
from PIL import Image
import datetime
from glob import glob


from mayavi_widget import MayaviQWidget, mlab
from common import WidgetMethods, build_wms_url, DoubleSlider, ResultReader
from tsunamis.utilities.io import read_configuration_file

class TabModelBase(qw.QSplitter, WidgetMethods):    

    # Result types and descriptions to be loaded
    result_types = {'eta':'wave height result',
                    'hmax':'max wave height result',
                    'Us':'wave vector u component',
                    'Vs':'wave vector v component',
                    'Ws':'wave vector w component',
                    'Ps':'?'}
                         
    
    
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        
        self.results_folder = 'results'
        self.configuration_path = 'input.txt'
        self.depth_path = 'depth.txt'
        self.parameters = {}
        self.results = dict.fromkeys(self.result_types, None) 
        
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
        steppersplit.addWidget(self.timestepper)
        steppersplit.addWidget(plot_buttons)        
        plot_controls.setLayout(steppersplit)
        self.plot_options = self.create_input_group('Plot options',
                                                  main_layout=False)
        self.display_bathymetry = self.add_input('Bathymetry', value=True,
                                                  function=self.display_bathymetry_changed)
        self.display_wave_height = self.add_input('Wave height', value=True,
                                                  function=self.display_wave_height_changed)
        self.display_wave_max = self.add_input('Maximum wave height', value=False,
                                               function=self.display_wave_max_changed)
        self.display_wave_vectors = self.add_input('Wave vectors', value=False,
                                                   function=self.display_wave_vectors_changed)
        
        self.misc_options = self.create_input_group('',
                                                    main_layout=False)
        self.vertical_exaggeration = self.add_input('Vertical exaggeration', value=10,
                                                    function=self.plot.set_vertical_exaggeration)
        
        self.plot.set_vertical_exaggeration(10)

        
        stepper_buttons = qw.QHBoxLayout()
        stepper_buttons.setAlignment(Qt.AlignRight)
        plot_control_layout = qw.QHBoxLayout()
        plot_control_layout.addWidget(self.plot_options)
        plot_control_layout.addWidget(self.misc_options)
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
        self.add_button('Write model inputs', self.write_model_inputs)
        
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
        self.zs = (self.ys - self.ys.max()) / 20
        
        self.display_bathymetry_changed()

        
        self.refresh_pause = False
        self.refresh_functions = [self.display_wave_height_changed,
                                  self.display_wave_max_changed,
                                  self.display_wave_vectors_changed]
        
         
    def _set_initial_directory(self, path):
        """
        To be run after the initialisation of the nhwave and funwave tabs
        """
        if path:
            self.model_folder = path
            self.load_directory()
        else:
            # TODO this is windows specific
            self.model_folder = os.path.join(os.environ['USERPROFILE'],
                                             'Desktop',
                                             self.model.model)
   
        
    def refresh_plots(self):
        for f in self.refresh_functions: f()
        
    def display_bathymetry_changed(self, value=None):
        if value is None: value = self.display_bathymetry.value()
        if value:
            self.plot.show_bathymetry(self.zs)
        else:
            self.plot.hide_bathymetry()
        
    def display_wave_height_changed(self, value=None):
        if value is None: value = self.display_wave_height.value()
        if value:
            self.plot.show_wave_height(self.results['eta'][self.timestep])
        else:
            self.plot.hide_wave_height()
        
    def display_wave_max_changed(self, value=None):
        if value is None: value = self.display_wave_max.value()
        if value:
            self.plot.show_wave_max(self.results['hmax'][self.timestep])
        else:
            self.plot.hide_wave_max()
        
    def display_wave_vectors_changed(self, value=None):
        if value is None: value = self.display_wave_vectors.value()
        if value:
            self.plot.show_wave_vectors(self.results['Us'][self.timestep],
                                        self.results['Vs'][self.timestep])
        else:
            self.plot.hide_wave_vectors()
            
        
    def recalculate_timesteps(self):
        self.timesteps = np.arange(self.pv('PLOT_START'),
                                   # Extra to make the end time inclusive
                                   self.pv('TOTAL_TIME') + self.pv('PLOT_INTV') / 2,
                                   self.pv('PLOT_INTV'))
        
        # Done on existing keys in case this ever changes
        for result in self.results:
            # Create an empty dictionary to hold the results
            self.results[result] = {t: None for t in self.timesteps}
            
        
        
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
        self.refresh_plots()
        
        
    def play_pause_clicked(self):
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
                                       np.arange(self.y0, self.y1, dy))
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
        
        self.display_bathymetry_changed() 
        
        
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
        
        # Refresh the plot
        # TODO might not be needed
        #self.timestep_changed()
        

    def load_configuration_file(self, path):
        # Load parameters from input text file
        loadedParameters = read_configuration_file(path)
        
        self.refresh_pause = True
        # Run for the provided tab
        for key, value in loadedParameters.items():
            if key in self.parameters:
                try:
                    self.parameters[key].setValue(value)
                except TypeError:
                    print('parameter {} with value {} has unexpected type'.format(key, value))
                    print(type(value), 'instead of type', type(self.parameters[key].value()))

        self.refresh_pause = False
 
    
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
        # Ouputs inputs
        self.write_model_inputs()
        
        # And run
        run = self.model.run()
        
        if run: self.load_results()
        
    
    def write_model_inputs(self):
        self.set_model_inputs()        
        # Output them
        self.model.write_config()
        
        
    def set_model_inputs(self):
        # Set parameters
        for k, w in self.parameters.items():
            self.model.parameters[k] = w.value()            
        self.model.parameters['RESULT_FOLDER'] = self.results_folder + '/'
        self.model.depth = -self.zs            
        self.model.output_directory = self.model_folder
        
        
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
            
        
        reader = ResultReader()
        reader.progress.connect(self.progress)


        for label, record in self.results.items():
            # Get a list of the results
            files = glob(os.path.join(folder, label + '_*'))            
            if not files: continue
            print('loading {} {} files'.format(len(files), label))
        
            # Sort the files by the number at the end of the file
            file_list = sorted(files, key=lambda name: int(name[-5:]))        
            
            # No result for the first timestep
            record[self.timesteps[0]] = np.zeros_like(self.zs)
                       
            # DEBUG OPTION
            # file_list = file_list[:5]
            
            for timestep, path in zip(self.timesteps[1:], file_list):
                reader.add_task(record, timestep, path)
        
        reader.start()
        
        # Probably a better way to do this
        if hasattr(self, 'recalculate_landslide'):
            self.recalculate_landslide()
        
        # Refresh any plots that are showing
        self.refresh_plots()
        
        




    @pyqtSlot(float, str)
    def progress(self, fraction, message):
        self.parent.progressBar.setValue(round(fraction * 100))
        self.parent.statusBar.showMessage(message, 2000)


        
if __name__ == '__main__':
    from run_gui import run
    run()