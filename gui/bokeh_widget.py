# Make a Bokeh Qt widget
# Simon Libby 2020

from bokeh.plotting import figure
from bokeh.embed import file_html, server_session
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

from PyQt5.QtCore import QUrl


from common import build_wms_url


class BokehMapQWidget(QtWebEngineWidgets.QWebEngineView):
    
    def __init__(self, parent=None,
                 xmin=-180, xmax=180, ymin=-90, ymax=90):
        
        QtWebEngineWidgets.QWebEngineView.__init__(self, parent)
        
        self.figure = figure(tools='wheel_zoom,pan,box_zoom,reset',
                             active_scroll='wheel_zoom',
                             lod_threshold=None,
                             #TODO make the bounds work
                             x_axis_label='Longitude',
                             y_axis_label='Latitude',
                             x_range=Range1d(start=xmin, end=xmax, bounds=None),
                             y_range=Range1d(start=ymin, end=ymax, bounds=None),
                             sizing_mode='stretch_both')
        self.figure.toolbar_location = 'above'
        
        url = build_wms_url()
        self.figure.add_tile(BBoxTileSource(url=url))  
        
        #Need to update the map here to make it take up space
        self.update()

        
        
    def update(self):
        self.setHtml(file_html(self.figure, CDN, 'GEBCO map plot'))
        #print(server_session(self.figure, 1))
        #self.setUrl(QUrl('http://localhost:5006/'))
        
        

        
 
        
        
if __name__ == '__main__':
    from run_gui import run
    run()