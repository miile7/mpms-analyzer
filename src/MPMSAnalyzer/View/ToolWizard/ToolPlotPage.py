# -*- coding: utf-8 -*-
"""
Created on Wed Feb 21 11:26:53 2018

@author: miile7
"""

from PyQt5 import QtWidgets, QtGui, QtCore
from formlayout import (FontLayout, ColorLayout, ColorButton, FormDialog)

import DataHandling.DataContainer
import View.ToolWizard.Tool
import View.PlotCanvas

class ToolPlotPage(QtWidgets.QWizardPage):
    def __init__(self, parent=None):
        """Initialize the data formatting page. This will be skipped if the user
        is not using a file (=DataContainer).
        Parameters
        ----------
            parent : QWidget, optional
                The parent
        """
        
        # initialize the page
        super(ToolPlotPage, self).__init__(parent)
        self.setTitle("Change plot appearance")
        self.setSubTitle("Format the data in the way you need to use it.")

        # fake attributes of formlaoyut.FormDialog
        # self.result = None
        # self.type = None
        # self.widget_color = None
 
    def initializePage(self):
        """Initialize the page"""
        
        # the parent wizard
        wizard = self.wizard()
        
        # set layout
        layout = QtWidgets.QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(30, 15, 30, 15)
        
        # create preview
        if (wizard.result_canvas == None or 
            not isinstance(wizard.result_canvas, View.PlotCanvas.PlotCanvas)):
            wizard.result_canvas = View.PlotCanvas.PlotCanvas()
        
        if len(wizard.result_canvas.getPlotDataList()) == 0:
            wizard.result_canvas.addPlotData(wizard.result_datacontainer.getPlotData(
                    wizard.measurement_variable,
                    DataHandling.DataContainer.DataContainer.MAGNETIZATION))
        
        # the menu factory for creating the edits
        self._menu_factory = View.PlotMenuFactory.PlotMenuFactory(wizard.result_canvas, self)
        
        # axes = wizard.result_canvas.axes[0]
        # self._edit_widget, apply_callback = self._menu_factory.figure_edit(axes, self)
        
        layout.addWidget(wizard.result_canvas)
        # layout.addWidget(self._edit_widget)
        self.setLayout(layout)
        
        # call the setup **after** adding the widget to the layout otherwise the 
        # widget does not have a parent (dialog) which will cause an error
        # self._edit_widget.setup
        # self.setWidgetChangeCallback(self._edit_widget, lambda: apply_callback(self._edit_widget.get(), self._edit_widget))
        
        # increase the size to make everything readable
        wizard.changeSize(None, 900)
    
    def getData(self):
        """Returns the widget data, this is a matplotlib function"""
        return self._edit_widget.get()
    
    def nextId(self):
        """Get the id of the next page
        
        Returns
        -------
            int
                The id of the next page
        """
        
        wizard = self.wizard()
        
        if wizard.output_mode & View.ToolWizard.ToolWizard.ToolWizard.OUTPUT_MODE_EXPORT_CSV > 0:
            return wizard.csv_export_index
        else:
            return -1
    
    def setWidgetChangeCallback(self, formwidget, callback):
        """Set a the callback for all the fields in the given formwidget recursively.
        Parameters
        ----------
            formwidget : formlayout.FormWidget,
                         formlayout.FormTabWidget, 
                         formlayout.FormComboWidget
                The form widget to set all the fields callbacks of
            callback : function
                The callback function when the field is changing
        """
        
        if formwidget == None:
            # formwidget not given (for example a comment), just ignore
            pass
        elif (isinstance(formwidget, (FormTabWidget, FormComboWidget)) and 
              formwidget.widgetlist != None and 
              isinstance(formwidget.widgetlist, (list, tuple))):
            # formwidget is a FormTabWidget or a FormComboWidget, perform the
            # setWidgetChangeCallback on the child FormWidgets
            for widget in formwidget.widgetlist:
                self.setWidgetChangeCallback(widget, callback)
        elif isinstance(formwidget, FontLayout):
            # set the callback on the fields of the form layout
            self.setWidgetChangeCallback(formwidget.family, callback)
            self.setWidgetChangeCallback(formwidget.size, callback)
            self.setWidgetChangeCallback(formwidget.bold, callback)
            self.setWidgetChangeCallback(formwidget.italic, callback)
        elif isinstance(formwidget, ColorLayout):
            # set the callback on the fields of the color layout
            self.setWidgetChangeCallback(formwidget.lineedit, callback)
            self.setWidgetChangeCallback(formwidget.colorbtn, callback)
        elif isinstance(formwidget, ColorButton):
            # the formwidget is a color button, this has a different signal
            formwidget.colorChanged.connect(callback)
        elif isinstance(formwidget, QtWidgets.QComboBox):
            # default qt combo box
            formwidget.currentIndexChanged.connect(callback)
        elif isinstance(formwidget, QtWidgets.QCheckBox):
            # default qt check box
            formwidget.stateChanged.connect(callback)
        elif isinstance(formwidget, QtWidgets.QLineEdit):
            # default qt line edit
            formwidget.editingFinished.connect(callback)
        elif isinstance(formwidget, QtWidgets.QAbstractSpinBox):
            # default qt abstract spin box, this is for a spiner and date and
            # datetime edit which all inherit the QAbstractSpinBox
            formwidget.editingFinished.connect(callback)
        elif isinstance(formwidget, QtWidgets.QAbstractButton):
            # default abstract qt button for all qt buttons
            formwidget.clicked.connect(callback)