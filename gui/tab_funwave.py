# Tab for FUNWAVE for Tsunami GUI
# Simon Libby 2020

from tab_model_base import TabModelBase
from tsunamis.models.funwave import config as funwave_config


class TabFUNWAVE(TabModelBase):
    
    def __init__(self, parent, initial_directory):
        self.model = funwave_config()
        
        super().__init__(parent)
        
        
        self._set_initial_directory(initial_directory)
        
        
        
        self.create_input_group('Initial wave')      
        
        self.add_button('Set initial wave', self.set_initial_wave)

        self.add_input('wave height', value='eta.txt')
        self.add_input('wave u vector', value='u.txt')
        self.add_input('wave v vector', value='v.txt')
        
        
    
        
    def set_initial_wave(self, value=None):
        
        
        
        
if __name__ == '__main__':
    from run_gui import run
    run()
    