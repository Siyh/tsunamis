# Main window for Tsunami GUI
# Simon Libby 

import os
from PyQt5 import QtWidgets as qw
from PyQt5 import QtGui, QtCore
from mayavi import mlab

from tab_map import TabMap
from tab_nhwave import TabNHWAVE
from tab_funwave import TabFUNWAVE
from common import ResultReader
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
            
        # Setup the thread for reading results. This is done in a separate 
        # thread so the gui doesn't hang
        self.reader = ResultReader()
        self.reader.progress.connect(self.progress)
        
        #======================================================================
        # Setup the window contents
        #======================================================================
        
        # Create the tabs
        self.tabs = qw.QTabWidget(self)        
        self.tab_nhwave = TabNHWAVE(self)
        self.tab_funwave = TabFUNWAVE(self)
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
        
        load_config = file_menu.addAction('Load configuration')
        load_config.triggered.connect(self.load_config_clicked)
        
        save_config = file_menu.addAction('Save configuration')
        save_config.triggered.connect(self.save_config_clicked)     
        
        set_nhwave_executable = file_menu.addAction('Set NHWAVE executable')
        set_nhwave_executable.triggered.connect(self.tab_nhwave.set_executable_path)
        
        set_funwave_executable = file_menu.addAction('Set FUNWAVE executable')
        set_funwave_executable.triggered.connect(self.tab_funwave.set_executable_path)
        
        
        # Load the initial config if one was provided
        if config:
            self.load_config(config)
        else:
            self.config_folder = os.path.join(os.environ['USERPROFILE'], 'Desktop')
        
        
    def save_config_clicked(self):
        # Open a dialogue to define the config
        fname, extension = qw.QFileDialog.getSaveFileName(self,
                                                          'Save Tsunami modelling configuration file',
                                                          self.config_folder,
                                                          'Tsunami configuration file (*.tsu)')
        if fname:
            parameters = {k: w.value() for k, w in self.tab_map.parameters.items()}
            # Implemented as a loop to make easy expansion later
            for folder_key, tab in [('NHWAVE_folder', self.tab_nhwave),
                                    ('FUNWAVE_folder', self.tab_funwave)]:
                parameters[folder_key] = tab.model_folder.value()
            
            # Write the config file
            with open(fname, 'w') as f:
                for k, v in parameters.items():
                    f.write(f'{k} = {v}\n')
    
    
    def load_config_clicked(self):
        # Open a dialogue to the config
        fname, extension = qw.QFileDialog.getOpenFileName(self,
                                                          'Open Tsunami modelling configuration file',
                                                          self.config_folder,
                                                          'Tsunami configuration file (*.tsu)')
        if fname:            
            self.load_config(fname)
        
    
    def load_config(self, path):        
        parameters = read_configuration_file(path)        
        self.config_folder = os.path.dirname(path)
        
        self.tab_map.update_parameters(parameters)
        
        # Pause loading incase there are results from both programs
        self.reader.active = False
        # Load the provided inputs for nhwave and funwave
        for folder_key, tab in [('NHWAVE_folder', self.tab_nhwave),
                                ('FUNWAVE_folder', self.tab_funwave)]:            
        
            folder = parameters.get(folder_key, '')
            if folder:
                folder_full_path = os.path.join(self.config_folder, folder)
                tab.load_directory(folder_full_path)
        
        # Read in results
        self.reader.run_threads()
        
        
    @QtCore.pyqtSlot(float, str)
    def progress(self, fraction, message):
        self.progressBar.setValue(round(fraction * 100))
        self.statusBar.showMessage(message, 2000)
                

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