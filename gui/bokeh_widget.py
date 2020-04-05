# Make a Bokeh Qt widget
# Simon Libby 2020

from bokeh.plotting import figure
from bokeh.embed import file_html
from bokeh.resources import CDN
from bokeh.models import BBoxTileSource, Range1d

# Make it so we can import the Qwebengine from iPython
# https://stackoverflow.com/questions/57426219/  
def webengine_hack():      
    from PyQt5 import QtWidgets
    app = QtWidgets.QApplication.instance()
    if app is not None:
        import sip
        app.quit()
        sip.delete(app)
    # import sys
    # from PyQt5 import QtCore, QtWebEngineWidgets
    # QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_ShareOpenGLContexts)
    # app = QtWidgets.qApp = QtWidgets.QApplication(sys.argv)
    # return app
try:
    from PyQt5 import QtWebEngineWidgets
except ImportError:
    print('Reimporting web engine')
    app = webengine_hack()
    from PyQt5 import QtWebEngineWidgets
    

# Setup the GEBCO WMS url
crs = 'EPSG:4326'
xmin = -180
ymin = -90
xmax = 180
ymax = 90
width = 1024
height = 1024
url1 = ('https://www.gebco.net/data_and_products/gebco_web_services/'
       '2019/mapserv?request=getmap&service=wms&'
       'BBOX={YMIN},{XMIN},{YMAX},{XMAX}&')
url2 = ('crs={crs}&format=image/jpeg&layers=gebco_2019_grid&'
       'width={width}&height={height}&version=1.3.0')
url_set = url1 + url2.format(crs=crs, width=width, height=height)



class BokehMapQWidget(QtWebEngineWidgets.QWebEngineView):
    
    def __init__(self, parent=None):
        QtWebEngineWidgets.QWebEngineView.__init__(self, parent)
        
        p = figure(tools='wheel_zoom,pan,box_zoom,reset',
                   active_scroll='wheel_zoom',
                   lod_threshold=None,
                   #TODO make the bounds work
                   x_axis_label='Longitude',
                   y_axis_label='Latitude',
                   x_range=Range1d(start=xmin, end=xmax, bounds=None),
                   y_range=Range1d(start=ymin, end=ymax, bounds=None),
                   sizing_mode='stretch_both')
        
        p.toolbar_location = 'above'

        p.add_tile(BBoxTileSource(url=url_set))


        
        self.setHtml(file_html(p, CDN, 'GEBCO map plot'))
        
 
        
        
if __name__ == '__main__':
    from run_gui import run
    run()