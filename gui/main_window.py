# Main window for Tsunami GUI
# Simon Libby 

from PyQt5 import QtWidgets as qw
from PyQt5 import QtGui, QtCore

from tab_map import TabMap
from tab_nhwave import TabNHWAVE
from tab_funwave import TabFUNWAVE

import os


from tsunamis.utilities.io import load_config_file

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
        load_nhwave_input.triggered.connect(lambda: self.load_configurations(self.tab_nhwave))
        
        # Add load funwave input button and connect to specific function
        load_funwave_input = file_menu.addAction('Load funwave input file')
        load_funwave_input.triggered.connect(lambda: self.load_configurations(self.tab_funwave))

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
        #Implement a current directory system
        desktop = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop')
        
        fname, extension = qw.QFileDialog.getOpenFileName(self,
                                                          'Open model configuration file',
                                                          desktop,
                                                          'Text file (*.txt);;Other (*.*)')

        # Load parameters from input text file
        loadedParameters = load_config_file(fname)
                
        # Run for the provided tab
        for key, value in loadedParameters.items():
            if key in tab.parameters:
                try:
                    tab.parameters[key].setValue(value)
                except TypeError:
                    print('parameter {} with value {} has unexpected type'.format(key, value))
                    print(type(value), 'instead of type', type(tab.parameters[key].value()))

                

    def closeEvent(self, event):
        # Save the window config
        self.settings.setValue('geometry', self.saveGeometry())
        print('Tsunami window closed')
        qw.QApplication.quit()        


if __name__ == '__main__':
    from run_gui import run
    run()