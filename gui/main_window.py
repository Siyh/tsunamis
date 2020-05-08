# Main window for Tsunami GUI
# Simon Libby 

from PyQt5 import QtWidgets as qw
from PyQt5 import QtGui, QtCore
from mayavi import mlab

from tab_map import TabMap
from tab_nhwave import TabNHWAVE
from tab_funwave import TabFUNWAVE


class TsunamiWindow(qw.QMainWindow):
    def __init__(self, nhwave='', funwave=''):
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
        # Setup the window contents
        #======================================================================
        
        # Create the tabs
        self.tabs = qw.QTabWidget(self)        
        self.tab_nhwave = TabNHWAVE(self, nhwave)
        self.tab_funwave = TabFUNWAVE(self, funwave)
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