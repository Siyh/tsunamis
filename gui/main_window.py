# Main window for Tsunami GUI
# Simon Libby 

import sys
from PyQt5 import QtWidgets as qw
from PyQt5 import QtGui, QtCore

from tab_general import TabGeneral
from tab_nhwave import TabNHWAVE
from tab_funwave import TabFUNWAVE

class TsunamiWindow(qw.QMainWindow):
    def __init__(self, initial_directory=''):
        super().__init__()
        
        #======================================================================
        # Setup the window
        #======================================================================
        self.setWindowTitle('Tsunami Modelling')
        self.setWindowIcon(QtGui.QIcon('great_wave_tip.png'))
        
        # Restore the window position
        self.settings = QtCore.QSettings('INeedACompanyName', 'TsunamiGUI')
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
        load_configurations = file_menu.addAction('Load configurations')
        load_configurations.triggered.connect(self.load_configurations)

        # Allow the GUI to be quit when run from Spyder
        debugging = self.menu_bar.addMenu('Debugging')
        close = debugging.addAction('Quit Spyder Instance')
        close.triggered.connect(qw.QApplication.quit)

            
            
        #======================================================================
        # Setup the window contents
        #======================================================================
        
        # Create the tabs
        self.tabs = qw.QTabWidget()
        self.tab_general = TabGeneral(self)
        self.tab_nhwave = TabNHWAVE(self)
        self.tab_funwave = TabFUNWAVE(self)
        
        # Arrange them
        self.tabs.addTab(self.tab_general, 'General')
        self.tabs.addTab(self.tab_nhwave, 'NHWAVE')
        self.tabs.addTab(self.tab_funwave, 'FUNWAVE')
        
        self.statusBar = qw.QStatusBar()
        self.setStatusBar(self.statusBar)
        
        self.setCentralWidget(self.tabs)   
             
        

        #======================================================================
        # Deal with data
        #======================================================================        
        
        # Load in the initial data if there is any
        if initial_directory:        
            self.load_data(initial_directory)            
        else:
            pass
       
        
    def load_data(self, path):
        pass
    
    def load_configurations(self):
        pass
    
    
    def closeEvent(self, event):
        # Save the window config
        self.settings.setValue('geometry', self.saveGeometry())
        print('Tsunami window closed')
        qw.QApplication.quit()        


if __name__ == '__main__':
    from run_gui import run
    run()