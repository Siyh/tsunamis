# Main window for Tsunami GUI
# Simon Libby 

import os
from PyQt5 import QtWidgets as qw
from PyQt5 import QtGui, QtCore
from mayavi import mlab

from tab_map import TabMap
from tab_nhwave import TabNHWAVE
from tab_funwave import TabFUNWAVE
from tsunamis.utilities.io import read_configuration_file


class TsunamiWindow(qw.QMainWindow):
    def __init__(self, config=''):
        super().__init__()
        
        #======================================================================
        # Setup the window
        #======================================================================
        self.setWindowTitle('Tsunami Modelling')
        self.setWindowIcon(QtGui.QIcon('great_wave_tip.png'))
        
        # Restore the window position
        self.settings = QtCore.QSettings('GoatsAndOats', 'TsunamiGUI')
        geometry = self.settings.value('geometry', '')
        if geometry:
            self.restoreGeometry(geometry)
        else:
            # This seems to be needed to make showMaximized work
            self.setGeometry(100, 100, 1000, 600)
            self.showMaximized()
            
        #======================================================================
        # Load the initial config if one was provided
        #======================================================================        
        
        # TODO call load_config instead
        if config:
            parameters = read_configuration_file(config)
            
            config_folder = os.path.dirname(config)
            
            nhwave_config = parameters.get('NHWAVE_config', '')
            if nhwave_config:
                nhwave_config = os.path.join(config_folder, nhwave_config)
                
            funwave_config = parameters.get('FUNWAVE_config', '')
            if funwave_config:
                funwave_config = os.path.join(config_folder, funwave_config)
            
        else:
            nhwave_config = ''
            funwave_config = ''
            parameters = {}
        
        #======================================================================
        # Setup the window contents
        #======================================================================
        
        # Create the tabs
        self.tabs = qw.QTabWidget(self)        
        self.tab_nhwave = TabNHWAVE(self, nhwave_config)
        self.tab_funwave = TabFUNWAVE(self, funwave_config)
        self.tab_map = TabMap(self, parameters)
        
        # Show the map tab on the other tabs
        self.tab_nhwave.tab_map = self.tab_map
        self.tab_funwave.tab_map = self.tab_map
        
        # Arrange them
        self.tabs.addTab(self.tab_map, 'Locations')
        self.tabs.addTab(self.tab_nhwave, 'NHWAVE')
        self.tabs.addTab(self.tab_funwave, 'FUNWAVE')
        
        # Temporarily set NHWAVE as the selected tab on opening
        self.tabs.setCurrentIndex(1)   

        
        self.statusBar = qw.QStatusBar()
        self.progressBar = qw.QProgressBar()
        self.progressBar.setMaximum(100)
        self.statusBar.addPermanentWidget(self.progressBar)
        self.setStatusBar(self.statusBar)
        
        
        self.setCentralWidget(self.tabs)   
        
        
        
        #======================================================================
        # Configure the menu bars
        #======================================================================
        self.menu_bar = self.menuBar()
        file_menu = self.menu_bar.addMenu('File')
        # Add load nhwave input button and connect to specific function
        load_nhwave_input = file_menu.addAction('Load nhwave input file')
        load_nhwave_input.triggered.connect(self.tab_nhwave.set_configuration_file)
        
        # Add load funwave input button and connect to specific function
        load_funwave_input = file_menu.addAction('Load funwave input file')
        load_funwave_input.triggered.connect(self.tab_funwave.set_configuration_file)

        # Allow the GUI to be quit when run from Spyder
        debugging = self.menu_bar.addMenu('Debugging')
        close = debugging.addAction('Quit Spyder Instance')
        close.triggered.connect(qw.QApplication.quit)
        
        
    def save_config_clicked(self):
        # Open a dialogue to define the config
        pass
    
    def load_config_clicked(self):
        # Open a dialogue to the config
        self.load_config(path)
    
    def load_config(self, path):
        pass
             

                

    def closeEvent(self, event):
        # Save the window config
        self.settings.setValue('geometry', self.saveGeometry())
        # Close the mayavi instances
        mlab.close(all=True)
        print('Tsunami window closed')
        qw.QApplication.quit()        


if __name__ == '__main__':
    from run_gui import run
    run()