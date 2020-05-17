# Make a Mayavi Qt widget
# Simon Libby 2020



from traits.api import HasTraits, Instance, on_trait_change
from traitsui.api import View, Item
from mayavi.core.ui.api import MayaviScene, MlabSceneModel, SceneEditor
from mayavi import mlab
from tvtk.api import tvtk
import numpy as np
from mayavi.core.lut_manager import pylab_luts

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
        pass
    
    # the layout of the dialog screated
    view = View(Item('scene', editor=SceneEditor(scene_class=MayaviScene),
                     height=250, width=300, show_label=False),
                     resizable=True # We need this to resize with the parent widget
                )


################################################################################
# The QWidget containing the visualization, this is pure PyQt4 code.
class MayaviQWidget(QtGui.QWidget):
    def __init__(self, parent):
        
        QtGui.QWidget.__init__(self, parent)
        layout = QtGui.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.visualization = Visualization()           
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
        
        
        #Add time title
        self.timestep_label = tvtk.TextActor(
            input='0:00:00',
            text_scale_mode='prop',
            height=0.03)

        self.timestep_label.position_coordinate.set(
            coordinate_system='normalized_viewport',
            value=(0.02, 0.02, 0.0))
        
        self.visualization.scene.add_actor(self.timestep_label)
        
        
        self.bathymetry = None
        self.coastline = None
        self.wave_height = None
        self.wave_max = None
        self.wave_vectors = None
        self.landslide = None
        # Dictionaries to store the colorbar and luts
        self.cbs = {}
        self.luts = {}
        
        self.vertical_exaggeration = 1
        
        
    def set_location(self, xs, ys):
        self.xs = xs.T
        self.ys = ys.T
        for plot in [self.bathymetry,
                     self.coastline,
                     self.wave_height,
                     self.wave_max,
                     self.wave_vectors,
                     self.landslide]:
            if plot is not None:
                plot.mlab_source.reset(x=self.xs, y=self.ys)
   
        
    def show_bathymetry(self, bathymetry, colormap='gist_earth'):
        if not self.figure: return
        self.bathymetry_data = bathymetry.T
        
        
        # If the bathymetry hasn't yet been plotted, do so
        if self.bathymetry is None:
            
            self.bathymetry = mlab.surf(self.xs,
                                        self.ys,
                                        self.bathymetry_data,
                                        warp_scale=self.vertical_exaggeration,
                                        colormap=colormap,
                                        figure=self.figure) 
            
            # Add a countour to mark the coastline
            self.coastline = mlab.contour_surf(self.xs,
                                               self.ys,
                                               self.bathymetry_data,
                                               contours=[0],
                                               warp_scale=self.vertical_exaggeration,
                                               color=(0, 0, 0),
                                               figure=self.figure) 
            
            # Add an orientation axis            
            mlab.orientation_axes(figure=self.figure)            
        
        #Otherwise update the current bathymetry
        elif self.bathymetry.visible:
            self.bathymetry.mlab_source.scalars = self.bathymetry_data
            self.coastline.mlab_source.scalars = self.bathymetry_data       
        else:
            self.bathymetry.visible = True
            self.coastline.visible = True
            
            
    def hide_bathymetry(self):
        self.hide_plot(self.bathymetry)
        self.hide_plot(self.coastline)        

        
    def show_wave_height(self, heights, colormap='jet'):       
        self.wave_height = self.show_plot(self.wave_height, heights, colormap, 'Wave amplitude (m)')
        
        if self.wave_height is not None:
            self.centre_colormap(self.wave_height)
        
    def hide_wave_height(self):
        self.hide_plot(self.wave_height)
            
    def show_wave_max(self, heights, colormap='jet'):       
        self.wave_max = self.show_plot(self.wave_max, heights, colormap, 'Max wave amplitude (m)')  
        
    def hide_wave_max(self):
        self.hide_plot(self.wave_max)
        
        
    def show_landslide(self, depth):
        if depth is None:
            if self.landslide is not None:
                self.hide_plot(self.landslide)
            return            
        
        zs = -depth.T        
        mask = zs < self.bathymetry_data + 0.1
        
        if self.landslide is None:
            self.landslide = mlab.surf(self.xs,
                                       self.ys,
                                       zs,
                                       warp_scale=self.vertical_exaggeration,
                                       colormap='Reds',
                                       figure=self.figure,
                                       opacity=0.7,
                                       mask=mask)
            
        elif self.landslide.visible:
            self.landslide.mlab_source.reset(scalars=zs, mask=mask)            
        else:
            self.landslide.visible = True
            

    def hide_landslide(self):
        self.landslide.visible = False
            
        
    def show_plot(self, plot, zs, colormap, label):  
        if zs is None:
            if plot is not None:
                self.hide_plot(plot)
            
        # If the wave hasn't already been drawn, do so
        elif plot is None:
            plot = mlab.surf(self.xs,
                             self.ys,
                             zs.T,
                             warp_scale=self.vertical_exaggeration,
                             colormap=colormap,
                             figure=self.figure,
                             opacity=0.7)
            
            self.luts[plot] = (pylab_luts[colormap] * 255).astype(int) 
            
            cb = mlab.colorbar(plot,
                               title=label,
                               orientation='vertical')
            
            cb.scalar_bar.unconstrained_font_size = True
            cb.title_text_property.font_size = 20
            cb.label_text_property.font_size = 20
            cb.label_text_property.bold = False            
            
            self.cbs[plot] = cb
                       
            
        # Otherwise update the existing wave if it hasn't been hidden
        elif plot.visible:
            plot.mlab_source.scalars = zs.T
            
        # Otherwise just make it visible again
        else:
            plot.visible = True
            self.cbs[plot].visible = True
            
        return plot
        
        
    def hide_plot(self, plot):
        if plot is not None:
            plot.visible = False
            if plot in self.cbs:
                self.cbs[plot].visible = False
            
            
    def show_wave_vectors(self): 
        pass
            
    def hide_wave_vectors(self):
        return
        self.hide_plot(self.wave_vectors)
                
    def centre_colormap(self, plot):
        # The lut is a 255x4 array, with the columns representing RGBA
        # (red, green, blue, alpha) coded with integers going from 0 to 255.
                        
        data = plot.mlab_source.scalars
        maxd = np.max(data)
        mind = np.min(data)
        #Data range
        dran = maxd - mind
        
        #If the data range is zero return
        if not dran: return
        
        #Proportion of the data range at which the centred value lies
        zdp = abs(mind) / dran
        
        #index equal portion of distance along colormap
        cmzi = int(round(zdp * 255))
        #linspace from zero to 128, with number of points matching portion to side of zero
        topi = np.around(np.linspace(0, 127, cmzi))
        #and for other side
        boti = np.around(np.linspace(128, 254, 255 - cmzi))
        #convert these linspaces to ints
 
        #and map the new lut from these    
        lut = self.luts[plot][np.hstack([topi, boti]).astype(int)]   
        plot.module_manager.scalar_lut_manager.lut.table = lut
        
        
    def set_vertical_exaggeration(self, exaggeration):
        self.vertical_exaggeration = exaggeration
        
        for plot in [self.bathymetry,
                     self.coastline,
                     self.wave_height,
                     self.wave_max,
                     self.wave_vectors,
                     self.landslide]:
            if plot is not None:
                warp_filter = plot.mlab_source.m_data.children[0]
                warp_filter.filter.scale_factor = exaggeration
                
        
        
        
if __name__ == '__main__':
    from run_gui import run
    run()