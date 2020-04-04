# Base tab for NHWAVE and FUNWAVE showing a 3D viewer window and config options
# Simon Libby 2020

from PyQt5 import QtWidgets as qw
from common import WidgetMethods



class TabGeneral(qw.QWidget, WidgetMethods):
    def __init__(self, parent):
        super(qw.QWidget, self).__init__(parent)
        
        layout = qw.QVBoxLayout()
        
        self.pushButton1 = qw.QPushButton("PyQt5 button")
        
        
        
        label_widget = qw.QLabel('label')
        
        hbox = qw.QHBoxLayout()
        hbox.addWidget(label_widget)
        hbox.addWidget(self.pushButton1)
        
        layout.addLayout(hbox)
        
        
        self.setLayout(layout)
        
        
        
        
        
        
if __name__ == '__main__':
    from run_gui import run
    run()
