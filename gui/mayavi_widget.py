# Make a Mayavi Qt widget
# Simon Libby 2020



from traits.api import HasTraits, Instance, on_trait_change
from traitsui.api import View, Item
from mayavi.core.ui.api import MayaviScene, MlabSceneModel, SceneEditor
from mayavi import mlab
from tvtk.api import tvtk


# First, and before importing any Enthought packages, set the ETS_TOOLKIT
# environment variable to qt4, to tell Traits that we will use Qt.
import os
os.environ['ETS_TOOLKIT'] = 'qt4'
# By default, the PySide binding will be used. If you want the PyQt bindings
# to be used, you need to set the QT_API environment variable to 'pyqt'
os.environ['QT_API'] = 'pyqt5'

# To be able to use PySide or PyQt4 and not run in conflicts with traits,
# we need to import QtGui and QtCore from pyface.qt
from pyface.qt import QtGui
# Alternatively, you can bypass this line, but you need to make sure that
# the following lines are executed before the import of PyQT:
#   import sip
#   sip.setapi('QString', 2)


################################################################################
#The actual visualization
class Visualization(HasTraits):
    scene = Instance(MlabSceneModel, ())

    @on_trait_change('scene.activated')
    def update_plot(self):
        # This function is called when the view is opened. We don't
        # populate the scene when the view is not yet open, as some
        # VTK features require a GLContext.
        
        # TODO this is causing errors
        #mlab.orientation_axes(figure=self.scene.mayavi_scene)
        pass

    # the layout of the dialog screated
    view = View(Item('scene', editor=SceneEditor(scene_class=MayaviScene),
                     height=250, width=300, show_label=False),
                     resizable=True # We need this to resize with the parent widget
                )


################################################################################
# The QWidget containing the visualization, this is pure PyQt4 code.
class MayaviQWidget(QtGui.QWidget):
    def __init__(self, parent, data_object):
        
        QtGui.QWidget.__init__(self, parent)
        layout = QtGui.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.visualization = Visualization()           
        self.visualization.draw_bathymetry = self.draw_bathymetry
        # If you want to debug, beware that you need to remove the Qt
        # input hook.
        #QtCore.pyqtRemoveInputHook()
        #import pdb ; pdb.set_trace()
        #QtCore.pyqtRestoreInputHook()

        # The edit_traits call will generate the widget to embed.
        self.ui = self.visualization.edit_traits(parent=self,
                                                 kind='subpanel').control
        
        

        layout.addWidget(self.ui)
        self.ui.setParent(self)   
        
        # Set up the data links
        self.figure = self.visualization.scene.mayavi_scene
        self.data_object = data_object
        
        
        #Add time title
        self.timestep_label = tvtk.TextActor(
            input='0:00:00',
            text_scale_mode='prop',
            height=0.03)

        self.timestep_label.position_coordinate.set(
            coordinate_system='normalized_viewport',
            value=(0.02, 0.02, 0.0))
        
        self.visualization.scene.add_actor(self.timestep_label)
        
        
        
        
   
        
    def draw_bathymetry(self):
        if not self.figure: return

        mlab.clf(figure=self.figure)
        
        self.bathymetry = mlab.surf(self.data_object.xs.T,
                                    self.data_object.ys.T,
                                    self.data_object.bathymetry.T,
                                    warp_scale=1,
                                    colormap='gist_earth',
                                    figure=self.figure) 
                
        self.contours = mlab.contour_surf(self.data_object.xs.T,
                                          self.data_object.ys.T,
                                          self.data_object.bathymetry.T,
                                          contours=[0],
                                          warp_scale=1,
                                          color=(0, 0, 0),
                                          figure=self.figure) 
                
        # self.make_scale_bar()
        
        #if np.any(depth_data):
            ###### generates errors
            #mlab.axes(self.dplot)#, xlabel='X', ylabel='Y', zlabel='Elevation')
                    
        # if self.show_waves and self.have_results:
        #     self.make_wave_plot(self.eta[self.tstep])            
                                        
        #     #self.figure.on_mouse_pick(self.picker_callback)
                   
        #     if self.show_vectors:
        #         self.make_vector_plot()
        
        
if __name__ == '__main__':
    from run_gui import run
    run()