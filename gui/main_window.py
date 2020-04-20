# Main window for Tsunami GUI
# Simon Libby 

from PyQt5 import QtWidgets as qw
from PyQt5 import QtGui, QtCore

from tab_map import TabMap
from tab_nhwave import TabNHWAVE
from tab_funwave import TabFUNWAVE

import os

import re

from tsunamis.utilities.io import LoadInput

class TsunamiWindow(qw.QMainWindow):
    def __init__(self, initial_directory=''):
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
        # Configure the menu bars
        #======================================================================
        self.menu_bar = self.menuBar()
        file_menu = self.menu_bar.addMenu('File')
        # Add load nhwave input button and connect to specific function
        load_nhwave_input = file_menu.addAction('Load nhwave input file')
        load_nhwave_input.triggered.connect(lambda: self.load_configurations('nhwave'))
        
        # Add load funwave input button and connect to specific function
        load_funwave_input = file_menu.addAction('Load funwave input file')
        load_funwave_input.triggered.connect(lambda: self.load_configurations('funwave'))

        # Allow the GUI to be quit when run from Spyder
        debugging = self.menu_bar.addMenu('Debugging')
        close = debugging.addAction('Quit Spyder Instance')
        close.triggered.connect(qw.QApplication.quit)

            
            
        #======================================================================
        # Setup the window contents
        #======================================================================
        
        # Create the tabs
        self.tabs = qw.QTabWidget(self)        
        self.tab_nhwave = TabNHWAVE(self, initial_directory)
        self.tab_funwave = TabFUNWAVE(self, initial_directory)
        self.tab_map = TabMap(self)
        
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
        self.setStatusBar(self.statusBar)
        
        self.setCentralWidget(self.tabs)   
             
        

        #======================================================================
        # Deal with data
        #======================================================================        
        
        # Load in the initial data if there is any
        if initial_directory:        
            self.load_data(initial_directory)  
            # TODO
        else:
            pass
       
        
    def load_data(self, path):
        pass
    
    def load_configurations(self, tab):
        # Ask user for folder containing input.txt file
        folder = str(qw.QFileDialog.getExistingDirectory(self, \
                 "Select Directory containing configuration data"))
        # Load parameters from input.txt
        loadedParameters = LoadInput(os.path.join(folder, 'input.txt'))
        
        # Bools to figure out which button was clicked
        isNhwave = bool(re.match(tab, 'nhwave'))
        isFunwave = bool(re.match(tab, 'funwave'))
        
        # Run for either nhwave tab or funwave tab depending in bools
        if isNhwave:
            for key,value in loadedParameters.items():
                if key in self.tab_nhwave.parameters:
                    self.tab_nhwave.parameters[key].setValue(value)
        elif isFunwave:
            for key,value in loadedParameters.items():
                if key in self.tab_funwave.parameters:
                    self.tab_funwave.parameters[key].setValue(value)
                

    def closeEvent(self, event):
        # Save the window config
        self.settings.setValue('geometry', self.saveGeometry())
        print('Tsunami window closed')
        qw.QApplication.quit()        


if __name__ == '__main__':
    from run_gui import run
    run()