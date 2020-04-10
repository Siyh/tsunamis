# Base tab for NHWAVE and FUNWAVE showing a 3D viewer window and config options
# Simon Libby 2020

from PyQt5 import QtWidgets as qw
import cartopy.crs as ccrs
import numpy as np

from common import WidgetMethods
from bokeh_widget import BokehMapQWidget



class TabMap(qw.QWidget, WidgetMethods):
    def __init__(self, parent):
        super(qw.QWidget, self).__init__(parent)
        
        self.parameters = {}
        
        #=====================================================================
        # Setup map and button area
        #=====================================================================
        
        map_view = BokehMapQWidget()        
        map_box = qw.QVBoxLayout()
        map_box.addWidget(map_view)
        map_widget = qw.QWidget()
        map_widget.setLayout(map_box)

        
        input_widget = qw.QWidget()
        self.input_layout = qw.QVBoxLayout()
        input_widget.setLayout(self.input_layout)
        button = qw.QLabel('Buttons')        
        button_box = qw.QVBoxLayout()
        button_box.addWidget(button)                
        
        
        splitter = qw.QSplitter()
        splitter.addWidget(input_widget)
        splitter.addWidget(map_widget)
        top_layout = qw.QVBoxLayout()
        top_layout.addWidget(splitter)
        self.setLayout(top_layout)
        
        #=====================================================================
        # Setup inputs
        #=====================================================================
        
        self.create_input_group('NHWAVE area')
        self.add_input('EPSG code', 'nhw_epsg', 4326)
        self.add_input('X min', 'nhw_xmin', -10.0)
        self.add_input('X max', 'nhw_xmax', 10.0)
        self.add_input('Y min', 'nhw_ymin', -10.0)
        self.add_input('Y max', 'nhw_ymax', 10.0)
        
        self.create_input_group('FUNWAVE area')
        self.add_input('EPSG code', 'fun_epsg', 4326)
        self.add_input('X min', 'fun_xmin', -20.0)
        self.add_input('X max', 'fun_xmax', 20.0)
        self.add_input('Y min', 'fun_ymin', -20.0)
        self.add_input('Y max', 'fun_ymax', 20.0)

        
    def draw_box(xmin, xmax, ymin, ymax, c):
        """
        Returns a list of the points round the box, so that a box in one
        coordinate system is displayed correctly in another.
        """
        xs = list(np.linspace(xmin, xmax, 100))
        ys = list(np.linspace(ymin, ymax, 100))
        x_around = xs + [xmax] * 98 + xs[::-1] + [xmin] * 98
        y_around = [ymin] * 100 + ys[1:-1] + [ymax] * 100 + ys[1:-1:-1]
        return x_around, y_around
        
        
        
if __name__ == '__main__':
    from run_gui import run
    run()
