# Base tab for NHWAVE and FUNWAVE showing a 3D viewer window and config options
# Simon Libby 2020

from PyQt5 import QtWidgets as qw
from common import WidgetMethods
from bokeh_widget import BokehMapQWidget



class TabGeneral(qw.QWidget, WidgetMethods):
    def __init__(self, parent):
        super(qw.QWidget, self).__init__(parent)
        
        map_view = BokehMapQWidget()        
        map_box = qw.QVBoxLayout()
        map_box.addWidget(map_view)
        map_widget = qw.QWidget()
        map_widget.setLayout(map_box)

        
        button_widget = qw.QWidget()
        button = qw.QLabel('Buttons')        
        button_box = qw.QVBoxLayout()
        button_box.addWidget(button)                
        button_widget.setLayout(button_box)
        
        
        splitter = qw.QSplitter()
        splitter.addWidget(button_widget)
        splitter.addWidget(map_widget)
        top_layout = qw.QVBoxLayout()
        top_layout.addWidget(splitter)
        self.setLayout(top_layout)
        
        
        
        
        
if __name__ == '__main__':
    from run_gui import run
    run()
