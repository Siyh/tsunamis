# Tab for FUNWAVE for Tsunami GUI
# Simon Libby 2020

from tab_model_base import TabModelBase
from tsunamis.models.funwave import config as funwave_config


class TabFUNWAVE(TabModelBase):
    
    def __init__(self, parent):
        super().__init__(parent)
        
        self.model = funwave_config()
        
        
        
        
        
if __name__ == '__main__':
    from run_gui import run
    run()
    