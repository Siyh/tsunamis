# Run the Tsunami GUI
# Simon Libby 2020

import sys
from pyface.qt import QtGui
from PyQt5 import QtWidgets as qw


from main_window import TsunamiWindow

    
    
def run(path=r'C:\Users\Simon\OneDrive\Tsunamis\test2'):
    
    # Written as a function to prevent things from getting into the console
    # namespace, as Spyder also runs in PyQt5   
    app = qw.QApplication(sys.argv)
    
    # Don't create a new QApplication, it would unhook the Events
    # set by Traits on the existing QApplication. Simply use the
    # '.instance()' method to retrieve the existing one.
    #app = QtGui.QApplication.instance()
    
    # This needs to point to an argument to make it persistant
    window = TsunamiWindow(path)
    window.show()
    
    # Start Qt event loop unless running in interactive mode or using pyside
    if (sys.flags.interactive != 1):# or not hasattr(pg.QtCore, 'PYQT_VERSION'):
        sys.exit(app.exec_())
        
if __name__ == '__main__': run()   