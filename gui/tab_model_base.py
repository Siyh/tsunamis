# Base tab for NHWAVE and FUNWAVE showing a 3D viewer window and config options
# Simon Libby 2020

from PyQt5 import QtWidgets as qw
from PyQt5.QtCore import Qt
from PyQt5 import QtGui

import numpy as np
import os
import requests
from PIL import Image
import datetime
from glob import glob


from mayavi_widget import MayaviQWidget, mlab
from common import WidgetMethods, build_wms_url, DoubleSlider, InputGroup
from tsunamis.utilities.io import read_configuration_file, read_grid




class TabModelBase(qw.QSplitter, WidgetMethods):    

    # Result types and descriptions to be loaded
    result_types = {'eta':'wave height result',
                    #DEBUG commented out to speed up loading during testing
                    #'hmax':'max wave height result',
                     'Us':'wave vector u component',
                    'Vs':'wave vector v component',
                    #'Ps':'?',
                    }                         
    
    
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        
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
        
        self.console = qw.QTextEdit()
        self.console.setReadOnly(True)
        self.console.setFont(QtGui.QFont('Consolas', 10)) 
 
        self.addWidget(self.config_input_scroller)
        self.addWidget(viewer)   
        self.addWidget(self.console)        
        
        
        steppersplit = qw.QVBoxLayout()
        plot_buttons = qw.QWidget()
        self.timestepper = DoubleSlider(orientation=Qt.Horizontal)
        self.timestepper.setTickPosition(qw.QSlider.TicksBelow)
        self.timestepper.valueChanged.connect(self.timestep_changed)
        steppersplit.addWidget(self.timestepper)
        steppersplit.addWidget(plot_buttons)        
        plot_controls.setLayout(steppersplit)
        self.plot_options = InputGroup(self, 'Plot options', main_layout=False)
        self.display_bathymetry = self.plot_options.add_input('Bathymetry',
                                                              value=True,
                                                              function=self.display_bathymetry_changed)
        self.display_wave_height = self.plot_options.add_input('Wave height', value=True,
                                                  function=self.display_wave_height_changed)
        self.display_wave_max = self.plot_options.add_input('Maximum wave height', value=False,
                                               function=self.display_wave_max_changed)
        self.display_wave_vectors = self.plot_options.add_input('Wave vectors', value=False,
                                                   function=self.display_wave_vectors_changed)
        
        

        self.play_pause_button = qw.QPushButton() 
        self.playing = False
        self.set_button_icon(self.play_pause_button, 'SP_MediaPlay')
        next_step = qw.QPushButton() 
        self.set_button_icon(next_step, 'SP_MediaSeekForward')
        previous_step = qw.QPushButton() 
        self.set_button_icon(previous_step, 'SP_MediaSeekBackward')
        restart = qw.QPushButton() 
        self.set_button_icon(restart, 'SP_MediaSkipBackward')
        
        self.play_pause_button.clicked.connect(self.play_pause_clicked)
        next_step.clicked.connect(self.next_timestep)
        previous_step.clicked.connect(self.previous_timestep)
        restart.clicked.connect(self.restart_timestepper)
        
        stepper_buttons = qw.QHBoxLayout()
        stepper_buttons.setAlignment(Qt.AlignRight)
        stepper_buttons.addWidget(restart)
        stepper_buttons.addWidget(previous_step)
        stepper_buttons.addWidget(next_step)
        stepper_buttons.addWidget(self.play_pause_button)
        
        display_options = InputGroup(self, 'Display options', main_layout=False)        
        display_options.addLayout(stepper_buttons)        
        self.vertical_exaggeration = display_options.add_input('Vertical exaggeration', value=10,
                                                               function=self.plot.set_vertical_exaggeration)        
        self.plot.set_vertical_exaggeration(10)
        
        
        self.rhs_buttons = InputGroup(self,
                                      self.model.model + ' controls',
                                      main_layout=False)
        self.run_button = self.rhs_buttons.add_button('Run ' + self.model.model, self.run_model_clicked)  
        self.console_toggle = self.rhs_buttons.add_button('Show console output', self.toggle_console)
        self.console.hide() 

        
        plot_control_layout = qw.QHBoxLayout()
        plot_control_layout.addWidget(self.plot_options.widget)
        plot_control_layout.addWidget(display_options.widget)
        plot_control_layout.addWidget(self.rhs_buttons.widget)
        plot_buttons.setLayout(plot_control_layout)        
        
                
        
        
        #=====================================================================
        # Setup inputs
        #=====================================================================
        
        #TODO set tooltips using .setToolTip
        g = InputGroup(self, 'General')        
        
        g.add_button('Write model inputs', self.write_model_inputs)
        
        desktop = os.path.join(os.environ['USERPROFILE'],
                               'Desktop',
                               self.model.model)
        self.model_folder = g.add_input('Model folder',
                                        value=desktop,
                                        function=self.load_directory,
                                        dialogue_label=f'Select {self.model.model} folder')

        self.results_folder = g.add_input('Results folder',
                                          value='results',
                                          function=self.load_results,
                                          dialogue_label='Select results folder')
        
        g.add_button('Load configuration', self.set_configuration_file)
        g.add_input('Processor number X', 'PX', 2)
        g.add_input('Processor number Y', 'PY', 2)
        
        g = InputGroup(self, 'Run setup')
        g.add_input('Model run title', 'TITLE', 'test')
        step_widget = g.add_input('Simulation steps', 'SIM_STEPS', 1000)   
        step_widget.setSingleStep(100)
        #TODO make this accept different units of time, not just seconds
        g.add_input('Total time', 'TOTAL_TIME', 300.0, function=self.total_time_changed)
        self.timestepper.setMaximum(300)
        g.add_input('Output time start', 'PLOT_START', 0.0, function=self.plot_start_changed)
        self.timestepper.setMinimum(0.0)
        output_interval = g.add_input('Output interval', 'PLOT_INTV', 10.0,
                                      function=self.plot_interval_changed)
        output_interval.setMinimum(1E-5)
        self.timestepper.setInterval(10.0)
        self.recalculate_timesteps()
        
        g.add_input('Screen output interval', 'SCREEN_INTV', 10.0)
        g.add_input('Initial timestep size', 'DT_INI', 2.0)
        g.add_input('Minimium timestep', 'DT_MIN', 0.01)
        g.add_input('Maximum timestep', 'DT_MAX', 10.0)
        # TODO implement hotstarting
        g.add_input('Hotstart', 'HOTSTART', False, enabled=False)
        
        g = InputGroup(self, 'Bathymetry', self.make_grid_coords)
        self.bathymetry_group = g
        g.add_button('Load bathymetry from grid', self.load_bathymetry)
        g.add_button('Load bathymetry from map', self.download_bathymetry, enabled=False)
        
        g.add_input('Number of cells in the X direction', 'Mglob', 400, editable=False)
        g.add_input('Number of cells in the Y direction', 'Nglob', 300, editable=False)        

        #TODO Interpolation of bathymetry 
        g.add_input('Grid size X', 'DX', 5.0)
        g.add_input('Grid size Y', 'DY', 5.0)

        g.add_input('Bathymetry grid type', 'DEPTH_TYPE',
                       {'Cell centred':'CELL_CENTER',
                        'Cell vertex aligned':'CELL_GRID'})        
        g.add_input('Analytical bathymetry', 'ANA_BATHY', False)
        g.add_input('DepConst', 'DepConst', 0.3)        
        
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
            self.plot.show_wave_height(self.mask_above_ground(self.results['eta'][self.timestep]))
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
            
    def mask_above_ground(self, zs):   
        # TODO make the masking happen when the results are loaded
        if zs is None:
            return None
            
        zs = zs.copy()         
        extra = self.pv(self.mask_extra_depth_parameter)
        mask = zs <= (self.zs + extra)
        zs[mask] = np.nan
        return zs
        
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
            self.set_button_icon(self.play_pause_button, 'SP_MediaPlay')

            # Make it stop playings
            self.animator.timer.Stop()
        else:
            self.playing = True
            self.set_button_icon(self.play_pause_button, 'SP_MediaPause')
            
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

    
        
    def load_bathymetry(self):
        
        formats = ['Any compatible (*.nc *.asc, *.txt)',
                   'NetCDF (*.nc)',
                   'Arc Ascii (*.asc)',
                   'Ascii elevation array (*.txt)',
                   'Other (*.*)']

        fname, extension = qw.QFileDialog.getOpenFileName(self,
                                                          'Open depth grid',
                                                          self.model_folder.value(),
                                                          ';;'.join(formats))
        if fname: 
            self.load_depth_file(fname)
            
            
    def set_configuration_file(self):        
        fname, extension = qw.QFileDialog.getOpenFileName(self,
                                                          f'Open {self.model.model} configuration file',
                                                          self.model_folder.value(),
                                                          'Text file (*.txt);;Other (*.*)')
        if fname:            
            self.load_configuration_file(fname)
            
        
    def load_depth_file(self, path):
        
        extension = path.rsplit('.', 1)[1].lower()
        
        if extension == 'nc':
            self.load_netcdf(path)
        elif extension == 'asc':
            self.load_arcascii(path)
        elif extension == 'txt':
            self.zs = -read_grid(path)            
            # Set cell size according to file if appropriate
            # dz = self.zs.max() - self.zs.min()
            # maxdim = max(self.pv('DX'), self.pv('DY'))
            # if dz > maxdim:
            #     v = sigfigs(dz / maxdim, 1)
            #     self.parameters['DX'].setValue(v)
            #     self.parameters['DY'].setValue(v)
        
        ny, nx = self.zs.shape
        self.parameters['Mglob'].setValue(nx)
        self.parameters['Nglob'].setValue(ny)    
        
        self.make_grid_coords()
        self.display_bathymetry_changed() 
        
        
    def load_directory(self, directory):
        """
        For loading everything possible when a new modelling directory is given
        """
        # Catch recursive setting of the directory
        if directory == self.model_folder.value():
            return
        else:
            self.model_folder.setValue(directory)
            
        # If the inputs exists then load them
        for check_path, function in [(self.configuration_path, self.load_configuration_file),
                                     (self.depth_path, self.load_depth_file)]:
            
            path = os.path.join(directory, check_path)
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
        
        # Draw landslide for NWHAVE and load initial wave for FUNWAVE
        self.load_directory_extras()

        

    def load_configuration_file(self, path):
        self.configuration_path = path
        
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
        

    def pv(self, parameter):
        """
        Convenience method to get a parameter value
        """
        return self.parameters[parameter].value()
    
    def toggle_console(self):
        if self.console.isVisible():
            self.console.hide()   
            self.console_toggle.setText('Show console output')
        else:
            self.show_console()
            
    def show_console(self):
        self.console.show()
        self.console_toggle.setText('Hide console output')
    
    def write_to_console(self, text):
        # TODO this should really be a signal slot
        self.console.moveCursor(QtGui.QTextCursor.End)
        self.console.insertPlainText(text)
        
    def model_run_finished(self):
        #TODO load results progressively
        self.load_results()
        self.hide_console()
    
    def run_model_clicked(self):        
        
        if self.model.linux_link.running:
            self.model.linux_link.terminate()
            self.run_button.setText('Run ' + self.model.model)
            
        else:
            self.show_console()
            self.console.setText(self.model.model + ' initialising...\n')            
            
            # Ouputs inputs
            self.write_model_inputs()
            
            # And run
            self.model.run(self.write_to_console)  
            
            self.run_button.setText('Stop ' + self.model.model)
               
    
    def write_model_inputs(self):
        self.set_model_inputs()        
        # Output them
        self.model.write_config()
        
        self.parent.status(self.model.model + ' inputs written to '
                           + self.model.output_directory)
        
        
    def set_model_inputs(self):
        # Set parameters
        for k, w in self.parameters.items():
            self.model.parameters[k] = w.value()            
            
        self.model.parameters['RESULT_FOLDER'] = self.results_folder.value() + '/'
        self.model.depth = -self.zs            
        self.model.output_directory = self.model_folder.value()
        
        self.model.x0 = self.tab_map.parameters[self.model.model + '_xmin'].value()
        self.model.y0 = self.tab_map.parameters[self.model.model + '_ymin'].value()
        self.model.ccrs = self.tab_map.parameters[self.model.model + '_epsg'].value()
        
        # Check the path to the exe is correct
        if not os.path.isfile(self.model.source_executable_path):
            self.set_executable_path()
            
    
    def set_executable_path(self):
        if os.path.isfile(self.model.source_executable_path):
            initial_folder = self.model.source_executable_path
        else:
            initial_folder = self.model_folder.value()
            
        fname, extension = qw.QFileDialog.getOpenFileName(self,
                                                          f'Select {self.model.model} executable',
                                                          initial_folder) 
        if fname:
            self.model.source_executable_path = fname
        
        
    def load_results(self, folder=''):
        """
        Check if there are any results and load them   
        """        
        
        if not folder: folder = self.results_folder.value()
        
        # Check if the results path is absolute
        if not os.path.isdir(folder):
            # Built an absolute path from the (possibly) relative one
            folder = os.path.join(self.model_folder.value(), folder)
            # Check it's valid
            if not os.path.isdir(folder):
                # If the folder isn't valid, don't try and load the results
                return      

        for label, record in self.results.items():
            # Get a list of the results
            files = glob(os.path.join(folder, label + '_*'))            
            if not files: continue
            print('loading {} {} files'.format(len(files), label))
        
            # Sort the files by the number at the end of the file
            file_list = sorted(files, key=lambda name: int(name[-5:]))        
            
            # No result for the first timestep
            record[self.timesteps[0]] = np.zeros_like(self.zs)
            
            for timestep, path in zip(self.timesteps[1:], file_list):
                self.parent.reader.add_task(record, timestep, path)
        
        self.parent.reader.start()

        # Refresh any plots that are showing
        self.refresh_plots()
        




        
if __name__ == '__main__':
    from run_gui import run
    run()