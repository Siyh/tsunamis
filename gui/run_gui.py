# Run the Tsunami GUI
# Simon Libby 2020

import sys
from PyQt5 import QtWidgets as qw

from main_window import TsunamiWindow
    
    
def run(config=r'C:\Users\Simon\OneDrive\Documents\PostPostdoc\test1\config.tsu'):
    
    # Written as a function to prevent things from getting into the console
    # namespace, as Spyder also runs in PyQt5   
    app = qw.QApplication(sys.argv)
    
    # This needs to point to an argument to make it persistant
    window = TsunamiWindow(config)
    window.show()
    # Delay the start of loading results until the GUI appears, otherwise it happens slower for some reason
    window.reader.run_threads()
    
    # Start Qt event loop unless running in interactive mode or using pyside
    if (sys.flags.interactive != 1):# or not hasattr(pg.QtCore, 'PYQT_VERSION'):
        sys.exit(app.exec_())
        
if __name__ == '__main__': run()   