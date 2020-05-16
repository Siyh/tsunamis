# Tab for FUNWAVE for Tsunami GUI
# Simon Libby 2020

from tab_model_base import TabModelBase
from tsunamis.models.funwave import config as funwave_config
from PyQt5 import QtGui
from PyQt5 import QtWidgets as qw


class TabFUNWAVE(TabModelBase):    
    def __init__(self, parent, initial_directory):
        self.model = funwave_config()
        
        super().__init__(parent)
        
        
        self._set_initial_directory(initial_directory)        
        
        
        self.create_input_group('Initial wave')                
        self.add_input('wave height',
                       value='eta.txt',
                       dialogue_label='Set initial wave height',
                       formats='txt')
        self.add_input('wave u vector',
                       value='u.txt',
                       dialogue_label='Set initial wave u vector',
                       formats='txt')
        self.add_input('wave v vector',
                       value='v.txt',
                       dialogue_label='Set initial wave v vector',
                       formats='txt')
        
        
        self._set_initial_directory(initial_directory)

        
    
    def set_initial_wave_clicked(self):
        
        # TODO need an open folder icon next to the wave height path
        formats = ['Text file (*.txt)', 'Other (*.*)']

        fname, extension = qw.QFileDialog.getOpenFileName(self,
                                                          'Set wave file grid',
                                                          self.model_folder,
                                                          ';;'.join(formats))
        if fname: 
            self.load_depth_file(fname)
        
        
    def set_initial_wave(self, value=None):
        
        self.restart_timestepper()        
        self.results['depth'][self.pv('PLOT_START')] = heights
        
        
        
if __name__ == '__main__':
    from run_gui import run
    run()
    