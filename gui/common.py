# Classes for holding common functions
# Simon Libby 2020

from PyQt5 import QtWidgets as qw


def label_to_attribute(label):
    """
    Converts a text string used for a labelling a button/input, and returns
    a text string suitable for assigning an attribute to the class.

    Parameters
    ----------
    label : TYPE
        DESCRIPTION.

    Returns
    -------
    TYPE
        DESCRIPTION.

    """
    return label.lower().replace(' ', '_')


def create_combo(content):
    """
    Creates a combo box from a dictionary of keys and values, or a list of 
    values which are used as the keys with incrementing intefers as the values
    """
    if isinstance(content, list):
        content = {k:i + 1 for i, k in enumerate(content)}
        
    c = qw.QComboBox()
    for i, (k, v) in enumerate(content.items()):
        c.addItem(str(v))
        c.setItemText(i, k)
    return c
        

class WidgetMethods:
    
    def button_list(self):
        """
        Creates a vertical list upon which to place buttons and labelled widgets.
        """
        self._button_list = qw.QVBoxLayout()
        return self._button_list
    
    
    def add_input(self, label, model_varb_name, value, widget=None, default=None):    
        """
        Labels a widget and adds it to the vertical list

        """
        if widget is None:            
            if isinstance(value, bool):
                widget = qw.QCheckBox()
                widget.setChecked(value)
            elif isinstance(value, int):
                widget = qw.QSpinBox()
                widget.setValue(value)
            elif isinstance(value, float):
                widget = qw.QDoubleSpinBox()
                widget.setValue(value)
            elif isinstance(value, (dict, list)):                
                widget = create_combo(value)
                if default is not None:
                    widget.setCurrentIndex(default)
            elif isinstance(value, str):
                widget = qw.QLineEdit()
                widget.setText(value)
            else:
                raise Exception('Input widget type not recognised') 
                
        
        self.parameters[model_varb_name] = widget
        
        hbox = qw.QHBoxLayout()
        hbox.addWidget(qw.QLabel(label))
        hbox.addWidget(widget)
        
        self._button_list.addLayout(hbox)
        
        
    def add_button(self, label, function):
        """
        Adds a button to the vertical list
        """
        button = qw.QPushButton(label)
        button.clicked.connect(function)
        setattr(self, label.replace(' ', '_'), button)
        self._button_list.addWidget(button)
        
    

        
    
        
        
        
        
        
        
        
if __name__ == '__main__':
    from run_gui import run
    run()