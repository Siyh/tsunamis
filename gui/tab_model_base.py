# Base tab for NHWAVE and FUNWAVE showing a 3D viewer window and config options
# Simon Libby 2020

from PyQt5 import QtWidgets as qw
from PyQt5.QtCore import Qt
import numpy as np
import os
import requests
from PIL import Image


from mayavi_widget import MayaviQWidget
from common import WidgetMethods, build_wms_url


class TabModelBase(qw.QSplitter, WidgetMethods):
    
    def __init__(self, parent):
        super().__init__(parent)
        
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
        self.plot = MayaviQWidget(self, self)
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
        self.timestepper = qw.QSlider(Qt.Horizontal)
        self.timestepper.setTickPosition(qw.QSlider.TicksBelow)
        self.timestepper.valueChanged.connect(self.timestep_changed)
        steppersplit.addWidget(plot_buttons)
        steppersplit.addWidget(self.timestepper)
        plot_controls.setLayout(steppersplit)
        
        
        #=====================================================================
        # Setup inputs
        #=====================================================================
        
        #TODO set tooltips using .setToolTip
        self.create_input_group('General')        
        self.add_button('Run ' + self.model.model, self.run_model_clicked)  
        
        self.add_button('Set results folder', self.set_results_clicked)        
        self.add_input('Processor number X', 'PX', 2)
        self.add_input('Processor number Y', 'PY', 2)
        
        self.create_input_group('Run setup')
        self.add_input('Model run title', 'TITLE', 'test')
        steps = qw.QSpinBox()
        steps.setSingleStep(1000)
        self.add_input('Simulation steps', 'SIM_STEPS', 100000, steps)        
        #TODO make this accept different units of time, not just seconds
        self.add_input('Total time', 'TOTAL_TIME', 300.0, function=self.total_time_changed)
        self.add_input('Output time start', 'PLOT_START', 0.0, function=self.plot_start_changed)
        self.add_input('Output interval', 'PLOT_INTV', 10.0, function=self.plot_interval_changed)
        self.add_input('Screen output interval', 'SCREEN_INTV', 10.0)
        self.add_input('Initial timestep size', 'DT_INI', 2.0)
        self.add_input('Minimium timestep', 'DT_MIN', 0.01)
        self.add_input('Maximum timestep', 'DT_MAX', 10.0)
        
        
        self.create_input_group('Bathymetry')
        self.add_button('Load bathymetry from grid', self.load_depth_clicked)
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
        
        
       
        
        
        # Make dummy x and y grids
        dx = self.parameters['DX'].value()
        dy = self.parameters['DY'].value()
        nx = self.parameters['Mglob'].value()
        ny = self.parameters['Nglob'].value()
        self.xs, self.ys = np.meshgrid(np.arange(0, dx * nx, dx),
                                       np.arange(0, dy * ny, dy))
        self.zs = (self.ys - self.ys.max()) / 2
        
        self.bathymetry = self.zs
        
        self.plot.draw_bathymetry()
        
        
    def total_time_changed(self):
        self.timestepper.setMaximum(self.pv('TOTAL_TIME'))
        
    def plot_start_changed(self):
        self.timestepper.setMinimum(self.pv('PLOT_START'))
        
    def plot_interval_changed(self):
        interval = self.pv('PLOT_INTV')
        self.timestepper.setSingleStep(interval)
        self.timestepper.setTickInterval(interval)
        
    @property
    def timestep(self):
        return self.timestepper.value()
    
    def timestep_changed(self):
        pass
    # TODO update wave output
        
        
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
        

    
        
    def load_depth_clicked(self):
        desktop = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop')
        
        formats = ['Any compatible (*.nc *.asc, *.txt)',
                   'NetCDF (*.nc)',
                   'Arc Ascii (*.asc)',
                   'Ascii elevation array (*.txt)',
                   'Other (*.*)']

        fname, extension = qw.QFileDialog.getOpenFileName(self,
                                                          'Open depth grid',
                                                          desktop,
                                                          ';;'.join(formats))
        if not fname: return
        
        extension = fname.rsplit('.', 1)[1].lower()
        
        if extension == 'nc':
            self.load_netcdf(fname)
        elif extension == 'asc':
            self.load_arcascii(fname)
        elif extension == 'txt':
            self.zs = np.loadtxt(fname)
            
        # TODO set cell size according to file
        #self.parameters['DX'].setValue()
        
        self.plot.render_plot(self.zs)
        
    
    
    def set_results_clicked(self):
        pass
    
    
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
        for k, w in self.paramters.items():
            self.model.parameters[k] = w.value()
            
        self.model.depth = -self.zs
            
        self.model.write_config()
        
        self.model.run()
        
        
if __name__ == '__main__':
    from run_gui import run
    run()