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
    Creates a combo box from either a dictionary of keys and values, or a list of 
    values which are used as the keys with incrementing integers as the values
    """
    if isinstance(content, list):
        content = {k:i + 1 for i, k in enumerate(content)}
        
    c = qw.QComboBox()
    for i, (k, v) in enumerate(content.items()):
        c.addItem(str(v))
        c.setItemText(i, k)
    return c
        

class WidgetMethods:
    
    def create_input_group(self, title):
        """
        Creates a vertical list upon which to place buttons and labelled widgets.
        """
        gb = qw.QGroupBox(title)
        self._current_input_group = qw.QVBoxLayout()
        gb.setLayout(self._current_input_group)        
        self.input_layout.addWidget(gb)
        return self._current_input_group
    
    
    def add_input(self, label, model_varb_name, value, widget=None, default=None):  
        """
        Labels a widget and adds it to the input group. The widget type
        depends on the value used unless a widget is specified. 

        Parameters
        ----------
        label : TYPE str
            label attached to the input in the GUI.
        model_varb_name : str
            name of the variable as used by the model.
        value : TYPE 
            starting value for the input. 
        widget : TYPE pyqt widget, optional
            widget to attach the label to. The default is None.
        default : TYPE, optional
            Only necessary if . The default is None.

        Raises
        ------
        Exception
            If the input type is not recognised.

        Returns
        -------
        None.

        """

        #Create a widget based on the value type
        if widget is None:            
            if isinstance(value, bool):
                widget = qw.QCheckBox()
                widget.setChecked(value)
            elif isinstance(value, int):
                widget = qw.QSpinBox()
                widget.setRange(0, 2147483647)
                widget.setValue(value)
            elif isinstance(value, float):
                widget = qw.QDoubleSpinBox()
                widget.setRange(0, 1E10)
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
                
        # Remember the widget acoording the model variable name, so the values
        # can be looked up when the model inputs are output
        self.parameters[model_varb_name] = widget
        
        # Put a label next to the widget and add them to the input list
        hbox = qw.QHBoxLayout()
        hbox.addWidget(qw.QLabel(label))
        hbox.addWidget(widget)        
        self._current_input_group.addLayout(hbox)
        
        
    def add_button(self, label, function):
        """
        Adds a button to the vertical list
        """
        button = qw.QPushButton(label)
        button.clicked.connect(function)
        setattr(self, label.replace(' ', '_'), button)
        self._current_input_group.addWidget(button)
        
    

        
    
        
        
        
        
        
        
        
if __name__ == '__main__':
    from run_gui import run
    run()