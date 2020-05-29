# Classes for holding common functions
# Simon Libby 2020

from PyQt5 import QtWidgets as qw
from PyQt5 import QtGui
from PyQt5.QtCore import (pyqtSignal,
                          QThread,
                          QPropertyAnimation,
                          Qt,
                          QParallelAnimationGroup,
                          QAbstractAnimation,
                          QSize,
                          #QObject)
                          )
import numpy as np
import time


def sigfigs(number, sigfigs=2):
    # https://stackoverflow.com/questions/3410976/how-to-round-a-number-to-significant-figures-in-python
    return round(number, -int(np.floor(np.log10(number))) + (sigfigs - 1))

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
    
    
class DictionaryCombo(qw.QComboBox):
    """
    Adds some methods to a combobox to allow the text displayed in the 
    combobox to differ from the values they correspond to.
    It does this by storing values in a list (self.values) and looking them up
    via the index of the selected entry in the combobox.
    """
    def assign_content(self, content):
        """
        Fills combo box from either a dictionary of keys and values, or a list of 
        values which are used as the keys with incrementing integers as the values
        """
        if isinstance(content, list):
            self.values = [i + 1 for i in range(len(content))]
            self.addItems(content)
        else:
            # Assumed to be a dictionary
            self.values = list(content.values())
            self.addItems(content.keys())
        
    def value(self):
        return self.values[self.currentIndex()]
    
    def setValue(self, value):
        # Find the index of the value we're looking to set
        # Either in the text on the combobox
        i = self.findText(str(value))
        if i == -1:
            # Or in the values to be returned
            i = self.values.index(value)

        self.setCurrentIndex(i)
        
    
        
        
class DoubleSlider(qw.QSlider):
    """
    Extends a QSlider to use doubles as opposed to ints.
    It does this by converting the specified range and interval to integer
    values that are used internally.
    """

    def __init__(self, *args, **kargs):
        super(DoubleSlider, self).__init__( *args, **kargs)
        self.interval = 1        
        
        # The actual slider minimum is always zero so the index values work
        super(DoubleSlider, self).setMinimum(0)
        self._minimum = 0
        self._maximum = 100
    
    def value(self):
        return self.index * self.interval + self.minimum()
    
    def setValue(self, value):
        index = round((value - self.minimum()) / self.interval)
        return super(DoubleSlider, self).setValue(index)
    
    @property
    def index(self):
        return super(DoubleSlider, self).value()
    
    def setIndex(self, index):
        return super(DoubleSlider, self).setValue(index)
    
    @property
    def maxIndex(self):
        return super(DoubleSlider, self).maximum()
    
    def minimum(self):
        return self._minimum  
     
    def setMinimum(self, value):        
        self._minimum = value
        self._range_adjusted()
        
    def maximum(self):
        return self._maximum

    def setMaximum(self, value):
        span = value - self.minimum()
        remainder = span % self.interval
        if remainder:
            # Make the range inclusive of the provided maximum value
            value += self.interval - remainder
            print(f'Maximum adjusted to {value} to match minimum and interval')
        self._maximum = value
        super(DoubleSlider, self).setMaximum((value - self.minimum()) / self.interval)
        self._range_adjusted()
    
    def setInterval(self, value):
        # To avoid division by zero
        if not value:
            raise ValueError('Interval of zero specified')
        self.interval = value
        self._range_adjusted()
        
    def _range_adjusted(self):
        number_of_steps_f = (self.maximum() - self.minimum()) / self.interval
        number_of_steps_i = int(number_of_steps_f)
        if number_of_steps_f != number_of_steps_i:
            print('Maximum range adjusted to match specified minimum value and interval')
        
        super(DoubleSlider, self).setMaximum(number_of_steps_i)
        
        #TODO try to maintain previous position
        self.setIndex(0)


class WidgetMethods:
    
    def create_input_group(self, title, function=None, main_layout=True):
        """
        Creates a vertical list upon which to place buttons and labelled widgets.
        If a function is given, it is called whenever one of the input group changes.
        """
        gb = qw.QGroupBox(title)
        self._current_input_group = qw.QVBoxLayout()
        gb.setLayout(self._current_input_group)     
        if main_layout:
            self.input_layout.addWidget(gb)
        self._current_input_group_function = function
        return gb
    
    
    def start_dropdown(self, title, function=None, main_layout=True):
        """
        Creates a vertical list upon which to place buttons and labelled widgets.
        If a function is given, it is called whenever one of the input group changes.
        """
        self._current_dropdown = Spoiler(title=title)
        self._current_input_group = qw.QVBoxLayout()        
        self._current_input_group_function = function
        if main_layout:
            self.input_layout.addWidget(self._current_dropdown)
        
    
    def finish_dropdown(self):
        # TODO change this to use a with statement
        self._current_dropdown.setContentLayout(self._current_input_group)   
        
    
    
    def add_input(self,
                  label,
                  model_varb_name='',
                  value=None,
                  widget=None,
                  default=None,
                  function=None,
                  layout=None,
                  dialogue_label='',        
                  formats=''):  
        """
        Labels a widget and adds it to the input group. The widget type
        depends on the value used unless a widget is specified. 
        
        if model_varb_name is specified, the variable will be added to the list
        that will be exported for the mode.
        
        Setting function to False will stop the widget being linked to the
        function of the group.       

        Parameters
        ----------
        label : str
            label attached to the input in the GUI.
        model_varb_name : str
            name of the variable as used by the model.
        value : int/float/str/dict 
            value for the input. 
        widget : pyqt widget, optional
            widget to attach the label to. The default is None.
        default :  optional
            Only used if the value was a dict. The default is None.
        function : function, optional
            function to call when the value of the widget changes, with the 
            new value passed as an argument.
            If not provided, uses the one specified for the input group if that
            was provided.
        layout : optional
            layput to add the input to. Defaults to the current group
        dialogue_label : str, optionl
            if provided, adds a button that opens a dialogue box with this
            label. The dialogue can open folders or files according to the 
            provided format.
        formats: str, optional
            if provided, sets the button type to a file and sets the format
            of the dialogue.
            if 'txt', then 'Text file (*.txt);;Other (*.*)' is used.

        Raises
        ------
        Exception
            If the input type is not recognised.

        Returns
        -------
        None.

        """

        # Create a widget based on the value type
        # Map the getting and setting of values to a common method
        if widget is None:            
            if isinstance(value, bool):
                widget = qw.QCheckBox()
                widget.valueChanged = widget.stateChanged
                widget.setValue = widget.setChecked
                widget.value = widget.isChecked
            elif isinstance(value, int):
                widget = qw.QSpinBox()
                widget.setRange(0, 2147483647)
            elif isinstance(value, float):
                widget = qw.QDoubleSpinBox()
                widget.setRange(0, 1E10)                
            elif isinstance(value, (dict, list)):                
                widget = DictionaryCombo()
                widget.assign_content(value)
                # So the value gets set to the default below
                value = default
                widget.valueChanged = widget.currentIndexChanged
            elif isinstance(value, str):
                widget = qw.QLineEdit()                
                widget.setValue = widget.setText
                widget.value = widget.text
                widget.valueChanged = widget.textChanged
            else:
                raise Exception('Input data type not recognised')
                
        # Put a label next to the widget
        hbox = qw.QHBoxLayout()
        hbox.addWidget(qw.QLabel(label))
        hbox.addWidget(widget)           
                
        if value is not None:
            widget.setValue(value)
            
        # Turn off calling valueChanged after every key press
        if hasattr(widget, 'setKeyboardTracking'):
            widget.setKeyboardTracking(False)
                
        # Remember the widget acoording the model variable name, so the values
        # can be looked up when the model inputs are output
        if model_varb_name: self.parameters[model_varb_name] = widget 
        
        # Add it to the input list if desired
        if layout is None: layout = self._current_input_group
        layout.addLayout(hbox)
        
        # Link it to a function if desired
        #if hasattr(widget, 'valueChanged'):
        if function is None:
            if self._current_input_group_function is not None:
                widget.valueChanged.connect(self._current_input_group_function)
        elif function:
            # The lamda function means the called function will be passed
            # the new value of the widget when it changes
            widget.valueChanged.connect(lambda: function(widget.value()))
            
        # Add a button to open a file/folder directory if desired
        if dialogue_label:
            button = qw.QPushButton()  
            hbox.addWidget(button)            
            
            if formats:            
                icon = 'SP_FileIcon'
                if formats == 'txt': formats = 'Text file (*.txt);;Other (*.*)'
                f = lambda: self.file_dialogue(dialogue_label, formats, widget)                
            else:
                icon = 'SP_DirOpenIcon'
                f = lambda: self.folder_dialogue(dialogue_label, widget) 
            
            self.set_button_icon(button, icon=icon)
            button.clicked.connect(f)

        return widget
    
    
    def folder_dialogue(self, label, target):
        path = qw.QFileDialog.getExistingDirectory(self,
                                                   label,
                                                   self.model_folder.value())
        if path:
            target.setValue(path)
            
        
    def file_dialogue(self, label, formats, target):
        path, extension = qw.QFileDialog.getOpenFileName(self,
                                                         label,
                                                         self.model_folder.value(),
                                                         formats)
        if path:
            # TODO make relative
            target.setValue(path)
        
        
    def add_button(self, label=None, function=None, icon=None):
        """
        Adds a button to the vertical list
        """
        button = qw.QPushButton(label)
        button.clicked.connect(function)
        if icon is not None:
            self.set_button_icon(button, icon)
            
        self._current_input_group.addWidget(button)
        return button
    
    
    def set_button_icon(self, button, icon='SP_DirOpenIcon'):
        button.setIcon(self.style().standardIcon(getattr(qw.QStyle, icon)))
        
            
    
def build_wms_url(epsg='4326',
                  xmin='{XMIN}', xmax='{XMAX}',
                  ymin='{YMIN}', ymax='{YMAX}',
                  width=1024, height=1024,
                  data_format='image/jpeg',
                  layer='gebco_2019_grid'):
    
    # Setup the GEBCO WMS url
    url = ('https://www.gebco.net/data_and_products/gebco_web_services/'
           '2019/mapserv?request=getmap&service=wms&'
           'BBOX={ymin},{xmin},{ymax},{xmax}&crs=EPSG:{epsg}'
           '&format={data_format}&layers={layer}&'
           'width={width}&height={height}&version=1.3.0')
    return url.format(xmin=xmin, xmax=xmax, ymin=ymin, ymax=ymax,
                      epsg=epsg, width=width, height=height,
                      data_format=data_format, layer=layer)
        
    
        
        
class ResultReader(QThread):
    progress = pyqtSignal(float, str)

    def __init__(self):
        QThread.__init__(self)
        self.targets = []
        self.paths = []
        self.keys = []
        # To allow running to be paused (to queue stuff to read from multiple sources)
        self.active = False        

    # def __del__(self):
    #     self.wait()
    
    def start(self):
        if self.active:
            super(ResultReader, self).start()
    
    
    def add_task(self, target, key, path):
        self.targets.append(target)
        self.keys.append(key)
        self.paths.append(path)
        
    def run_threads(self):
        self.active = True
        self.start()  
        

    def run(self):
        n = len(self.targets)
        for i, (target, key, path) in enumerate(zip(self.targets,
                                                    self.keys,
                                                    self.paths)):
            # Load the data
            target[key] = np.nan_to_num(np.loadtxt(path))
            
            # Report the progress
            self.progress.emit(i / n, 'Loading: ' + path)
            
        self.progress.emit(1, f'{n} Results loaded.')        
        time.sleep(2)
        self.progress.emit(0, '')
        
        
       
class Spoiler(qw.QWidget):
    def __init__(self, parent=None, title='', animationDuration=200):
        """
        Expandable list of widgets.
        References:
            # Adapted from c++ version
            http://stackoverflow.com/questions/32476006/how-to-make-an-expandable-collapsable-section-widget-in-qt
        """
        super(Spoiler, self).__init__(parent=parent)

        self.animationDuration = animationDuration
        self.toggleAnimation = QParallelAnimationGroup()
        self.contentArea = qw.QScrollArea()
        self.headerLine = qw.QFrame()
        self.toggleButton = qw.QToolButton()
        self.mainLayout = qw.QGridLayout()

        toggleButton = self.toggleButton
        toggleButton.setStyleSheet("QToolButton { border: none; }")
        toggleButton.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        toggleButton.setArrowType(Qt.RightArrow)
        toggleButton.setText(str(title))
        toggleButton.setCheckable(True)
        toggleButton.setChecked(False)

        headerLine = self.headerLine
        headerLine.setFrameShape(qw.QFrame.HLine)
        headerLine.setFrameShadow(qw.QFrame.Sunken)
        headerLine.setSizePolicy(qw.QSizePolicy.Expanding, qw.QSizePolicy.Maximum)

        self.contentArea.setStyleSheet("QScrollArea { background-color: white; border: none; }")
        self.contentArea.setSizePolicy(qw.QSizePolicy.Expanding, qw.QSizePolicy.Fixed)
        # start out collapsed
        self.contentArea.setMaximumHeight(0)
        self.contentArea.setMinimumHeight(0)
        # let the entire widget grow and shrink with its content
        toggleAnimation = self.toggleAnimation
        toggleAnimation.addAnimation(QPropertyAnimation(self, b"minimumHeight"))
        toggleAnimation.addAnimation(QPropertyAnimation(self, b"maximumHeight"))
        toggleAnimation.addAnimation(QPropertyAnimation(self.contentArea, b"maximumHeight"))
        # don't waste space
        mainLayout = self.mainLayout
        mainLayout.setVerticalSpacing(0)
        mainLayout.setContentsMargins(0, 0, 0, 0)
        row = 0
        mainLayout.addWidget(self.toggleButton, row, 0, 1, 1, Qt.AlignLeft)
        mainLayout.addWidget(self.headerLine, row, 2, 1, 1)
        row += 1
        mainLayout.addWidget(self.contentArea, row, 0, 1, 3)
        self.setLayout(self.mainLayout)

        def start_animation(checked):
            arrow_type = Qt.DownArrow if checked else Qt.RightArrow
            direction = QAbstractAnimation.Forward if checked else QAbstractAnimation.Backward
            toggleButton.setArrowType(arrow_type)
            self.toggleAnimation.setDirection(direction)
            self.toggleAnimation.start()

        self.toggleButton.clicked.connect(start_animation)
        

    def setContentLayout(self, contentLayout):
        # Not sure if this is equivalent to self.contentArea.destroy()
        self.contentArea.destroy()
        self.contentArea.setLayout(contentLayout)
        collapsedHeight = self.sizeHint().height() - self.contentArea.maximumHeight()
        contentHeight = contentLayout.sizeHint().height()
        for i in range(self.toggleAnimation.animationCount() - 1):
            spoilerAnimation = self.toggleAnimation.animationAt(i)
            spoilerAnimation.setDuration(self.animationDuration)
            spoilerAnimation.setStartValue(collapsedHeight)
            spoilerAnimation.setEndValue(collapsedHeight + contentHeight)
        contentAnimation = self.toggleAnimation.animationAt(self.toggleAnimation.animationCount() - 1)
        contentAnimation.setDuration(self.animationDuration)
        contentAnimation.setStartValue(0)
        contentAnimation.setEndValue(contentHeight)
        
        
# class EmittingStream(QObject):

#     textWritten = pyqtSignal(str)

#     def write(self, text):
#         self.textWritten.emit(str(text))


        
if __name__ == '__main__':
    from run_gui import run
    run()