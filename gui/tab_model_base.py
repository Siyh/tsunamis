# Base tab for NHWAVE and FUNWAVE showing a 3D viewer window and config options
# Simon Libby 2020

from PyQt5 import QtWidgets as qw

from mayavi_widget import MayaviQWidget
from common import WidgetMethods, create_combo


class TabModelBase(qw.QSplitter, WidgetMethods):
    
    def __init__(self, parent):
        super().__init__(parent)
        
        self.parameters = {}
        
        # Make all the components
        self.buttons = qw.QWidget()
        self.viewer = qw.QWidget()
        self.plot = MayaviQWidget()
        self.timestepper = qw.QWidget()
        
        # Arrange them
        viewersplit = qw.QVBoxLayout()
        viewersplit.addWidget(self.plot)
        viewersplit.addWidget(self.timestepper)
        self.viewer.setLayout(viewersplit)
        
        self.addWidget(self.buttons)
        self.addWidget(self.viewer)   
        
        # Setup inputs
        self.buttons.setLayout(self.button_list())
        
        #TODO set tooltips using .setToolTip
        
        self.add_input('Model run title', 'TITLE', 'test')
        self.add_button('Set depth fle', self.load_depth_clicked)
        self.add_button('Set results folder', self.set_results_clicked)
        
        self.add_input('Processor number X', 'PX', 2)
        self.add_input('Processor number Y', 'PY', 2)
        
        steps = qw.QSpinBox()
        steps.setSingleStep(1000)
        self.add_input('Simulation steps', 'SIM_STEPS', 1000000, steps)        
        #TODO make this accept different units of time, not just seconds
        self.add_input('Total time', 'TOTAL_TIME', 600.0)
        self.add_input('Output time start', 'PLOT_START', 0.0)
        self.add_input('Output interval', 'PLOT_INTV', 20.0)
        self.add_input('Screen output interval', 'SCREEN_INTV', 10.0)
        
        self.add_input('Grid size X', 'DX', 500.0)
        self.add_input('Grid size Y', 'DY', 500.0)
        
        self.add_input('Initial timestep size', 'DT_INI', 5.0)
        self.add_input('Minimium timestep', 'DT_MIN', 0.01)
        self.add_input('Maximum timestep', 'DT_MAX', 10.0)
        
        

        self.add_input('Bathymetry grid type', 'DEPTH_TYPE',
                       {'Cell centred':'CELL_CENTER',
                        'Cell vertex aligned':'CELL_GRID'})        
        self.add_input('Analytical bathymetry', 'ANA_BATHY', False)
        self.add_input('DepConst', 'DepConst', 0.3)
        
        


        
        
        
        
        
        
    def load_depth_clicked(self):
        pass
    
    
    def set_results_clicked(self):
        pass

        
        
if __name__ == '__main__':
    from run_gui import run
    run()