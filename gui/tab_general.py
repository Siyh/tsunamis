# Base tab for NHWAVE and FUNWAVE showing a 3D viewer window and config options
# Simon Libby 2020

from PyQt5 import QtWidgets as qw
import cartopy.crs as ccrs
import numpy as np

from common import WidgetMethods
from bokeh_widget import BokehMapQWidget



class TabGeneral(qw.QWidget, WidgetMethods):
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

        
    def draw_box(self,xmin, xmax, ymin, ymax, c):
        """
        Draw a box using the xmin, xmax, ymin and ymax coordinates
        
        Parameters
        ------------
        xmin : X coordinate of bottom left corner
        ymin : Y coordinate of bottom left corner
        xmax : X coordinate of right top corner
        ymax : Y coordinate of right top corner
        c : ?
        
        Returns
        ------------
        boxCoords : two row matrix, first row contains the x coordinates of 
        the box going from the bottom left corner anti-clockwise. second row is
        the Y coordinates.
        """
        sampPerSide = 100
        xCoord = np.linspace(xmin,xmax,sampPerSide)
        yCoord = np.linspace(ymin,ymax,sampPerSide)
        boxCoords = np.zeros([sampPerSide*4-4,2])
        boxCoords[:,0]=np.concatenate((xCoord,np.repeat(xmax,sampPerSide-2,axis=0),\
                        np.flipud(xCoord),np.repeat(xmin,sampPerSide-2,axis=0)))
        boxCoords[:,1]=np.concatenate((np.repeat(ymin,sampPerSide-1,axis=0),yCoord,\
                        np.repeat(ymax,sampPerSide-2,axis=0),np.flipud(yCoord[1:])),axis=0)
        return boxCoords
        
        
if __name__ == '__main__':
    from run_gui import run
    run()
