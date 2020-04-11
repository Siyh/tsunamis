# Base tab for NHWAVE and FUNWAVE showing a 3D viewer window and config options
# Simon Libby 2020

from PyQt5 import QtWidgets as qw
import cartopy.crs as ccrs
import numpy as np

from common import WidgetMethods, build_wms_url
from bokeh_widget import BokehMapQWidget
from bokeh.models import ColumnDataSource, Line


class TabMap(qw.QWidget, WidgetMethods):
    def __init__(self, parent):
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
        for model, colour in [('NHWAVE', 'darkblue'),
                              ('FUNWAVE', 'red')]:
            
            model_tab = getattr(self.parent(), 'tab_' + model.lower())
            
            self.create_input_group(model + ' area', model_tab.update_map_box)
            self.add_input('EPSG code', model + '_epsg', 4326)
            self.add_input('X min', model + '_xmin', -10.0)
            self.add_input('X max', model + '_xmax', 10.0)
            self.add_input('Y min', model + '_ymin', -10.0)
            self.add_input('Y max', model + '_ymax', 10.0)
            
            model_tab.map_box = ColumnDataSource(self.box_coordinates(model))
            self.map.figure.line(source=model_tab.map_box,
                                 x='x', y='y', line_color=colour,
                                 legend_label=model)
        
        self.map.update()
        
        
    
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
        
        # Convert the CS if necessary
        epsg = self.parameters[prefix + '_epsg'].value()
        if epsg != 4326:
            cs = ccrs.epsg(epsg)        
            tf = ccrs.Geodetic().transform_points(cs, x_around, y_around)
            print(tf)
            #TODO use updated coordinates
            
        return dict(x=x_around, y=y_around)
    
    
    
    
    
    
    
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
