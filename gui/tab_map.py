# Base tab for NHWAVE and FUNWAVE showing a 3D viewer window and config options
# Simon Libby 2020

from PyQt5 import QtWidgets as qw
import cartopy.crs as ccrs
import numpy as np

from common import WidgetMethods#, build_wms_url
from bokeh_widget import BokehMapQWidget
from bokeh.models import ColumnDataSource#, Line


class TabMap(qw.QWidget, WidgetMethods):
    def __init__(self, parent, parameters={}):
        super(qw.QWidget, self).__init__(parent)
        
        self.parameters = {}
        
        #=====================================================================
        # Setup map and button area
        #=====================================================================
        
        self.map = BokehMapQWidget()        
        map_box = qw.QVBoxLayout()
        map_box.addWidget(self.map)
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
        
        self.map_boxes = ColumnDataSource()
        self.add_map_area('NHWAVE', 'darkblue')
        self.add_map_area('FUNWAVE', 'red')
        self.update_parameters(parameters)
        self.map.update()
        
    
    def add_map_area(self, model, colour):
        self.create_input_group(model + ' area',
                                lambda: self.update_map_box(model))
        self.add_input('EPSG code', model + '_epsg', 4326)
        self.add_input('X min', model + '_xmin', -10.0)
        self.add_input('X max', model + '_xmax', 10.0)
        self.add_input('Y min', model + '_ymin', -10.0)
        self.add_input('Y max', model + '_ymax', 10.0)
        
        new_box = self.box_coordinates(model)
        for k, v in new_box.items():
            self.map_boxes.add(data=v, name=k)                  
        
        self.map.figure.line(source=self.map_boxes,
                             x=model + '_x',
                             y=model + '_y',
                             line_color=colour,
                             legend_label=model)            
            
        
    
    def box_limits(self, prefix):
        xmin = self.parameters[prefix + '_xmin'].value()
        xmax = self.parameters[prefix + '_xmax'].value()
        ymin = self.parameters[prefix + '_ymin'].value()
        ymax = self.parameters[prefix + '_ymax'].value()
        return xmin, xmax, ymin, ymax
        
    
    def box_coordinates(self, prefix):
        xmin, xmax, ymin, ymax = self.box_limits(prefix)
        # Get a list of the points round the box, so that a box in one
        # coordinate system is displayed correctly in another.
        xs = list(np.linspace(xmin, xmax, 100))
        ys = list(np.linspace(ymin, ymax, 100))
        x_around = xs + [xmax] * 98 + xs[::-1] + [xmin] * 98
        y_around = [ymin] * 100 + ys[1:-1] + [ymax] * 100 + ys[1:-1][::-1]
        x_around = np.array(x_around)
        y_around = np.array(y_around)
        
        # Convert the CS if necessary
        epsg = self.parameters[prefix + '_epsg'].value()
        if epsg != 4326:
            cs = ccrs.epsg(epsg)        
            tf = ccrs.Geodetic().transform_points(cs, x_around, y_around)
            x_around, y_around, _ = tf.T            
            
        return {prefix + '_x' : x_around, prefix + '_y' : y_around}
    
        
    def update_map_box(self, model):
        #TODO there must be a tidier way to move the dictionares around
        new_box = self.box_coordinates(model)
        data = dict(self.map_boxes.data)
        data.update(new_box)
        self.map_boxes.data = data
        #TODO do this without rerendering the map
        self.map.update()
    
    
    def update_parameters(self, new_parameters):
        for p, v in new_parameters.items():
            if p in self.parameters:
                self.parameters[p].setValue(v)
    
    
    
    
    # for downloading european bathymetry
        # # define the connection
        # url = 'http://ows.emodnet-bathymetry.eu/wcs?'
        # wcs = WebCoverageService(url, version='1.0.0', timeout=320)
        
        # # define variables
        # requestbbox = (2.097,52.715,4.277,53.935)
        # layer = 'emodnet:mean_atlas_land'
        # # get the data
        
        # sed = wcs[layer] #this is necessary to get essential metadata from the layers advertised
        
        # cx, cy = map(int,sed.grid.highlimits)
        # bbox = sed.boundingboxes[0]['bbox']
        # lx,ly,hx,hy = map(float,bbox)
        # resx, resy = (hx-lx)/cx, (hy-ly)/cy
        # width = round(cx/1000)
        # height = round(cy/1000)
        
        # gc = wcs.getCoverage(identifier='emodnet:mean',
        #                         bbox=requestbbox,
        #                         coverage=sed,
        #                         format='GeoTIFF',
        #                         crs=sed.boundingboxes[0]['nativeSrs'],
        #                         width=width,
        #                         height=height)

        # with Image.open(gc) as image:         
        #     elevation = np.array(image)  
        
        
        
if __name__ == '__main__':
    from run_gui import run
    run()
