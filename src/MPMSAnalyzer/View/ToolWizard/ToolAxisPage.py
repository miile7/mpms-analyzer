# -*- coding: utf-8 -*-
"""
Created on Mon Feb 26 13:42:35 2018

@author: miile7
"""

# -*- coding: utf-8 -*-
"""
Created on Wed Feb 21 11:26:53 2018

@author: miile7
"""

from PyQt5 import QtWidgets, QtGui, QtCore

import DataHandling.DataContainer
import View.PlotCanvas
import Constants

class ToolAxisPage(QtWidgets.QWizardPage):
    def __init__(self, parent=None):
        """Initialize the data formatting page. This will be skipped if the user
        is not using a file (=DataContainer).
        Parameters
        ----------
            parent : QWidget, optional
                The parent
        """
        
        # initialize the page
        super(ToolAxisPage, self).__init__(parent)
        self.setTitle("Select the axis")
        self.setSubTitle("Select the x and y axis to define which axis you want " + 
                         "to plot.")
 
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
        
        # add the widgets
        layout.addWidget(wizard.result_canvas)
        self.setLayout(layout)
        
        axes_layout = QtWidgets.QGridLayout()
        
        x_label = QtWidgets.QLabel("X-axis")
        axes_layout.addWidget(x_label, 0, 0)
        
        self._x_axis = QtWidgets.QComboBox()
        self._initAxisCombobox(self._x_axis)
        axes_layout.addWidget(self._x_axis, 0, 1)
        
        y_label = QtWidgets.QLabel("Y-axis")
        axes_layout.addWidget(y_label, 1, 0)
        
        self._y_axis = QtWidgets.QComboBox()
        self._initAxisCombobox(self._y_axis)
        axes_layout.addWidget(self._y_axis, 1, 1)
        
        selected_index = self._x_axis.findData(wizard.measurement_variable)
        if selected_index >= 0:
            self._x_axis.setCurrentIndex(selected_index)
        
        selected_index = self._y_axis.findData(DataHandling.DataContainer.DataContainer.MAGNETIZATION)
        if selected_index >= 0:
            self._y_axis.setCurrentIndex(selected_index)
        
        layout.addLayout(axes_layout)
        
        # increase the size to make everything readable
#        wizard.changeSize(None, 900)
        self._actionToggle()
    
    def _initAxisCombobox(self, combobox):
        """Initialize the comboboxes for the axis. This will add the possible
        axis to the given combobox and connect the signal when the axis are
        toggled for repainting the preview
        Parameters
        ----------
            combobox : QCombobox
                The combobox to dispaly the axis
        """
        
        wizard = self.wizard()
        
        # data form datacontainer
        data = wizard.getAllowedDataContainerAxis()
        
        for value in data:
            name = value
            if value in Constants.ENVIRONMENT_VARIABLE_NAMES:
                name = Constants.ENVIRONMENT_VARIABLE_NAMES[value]
            elif len(wizard.result_datacontainer.datapoints) > 0:
                name = wizard.result_datacontainer.datapoints[0].getNameForAxis(value)
                
            combobox.addItem(name, value)
            
        combobox.activated.connect(self._actionToggle)
    
    def _actionToggle(self):
        """The action method for the checkboxes"""
        
        wizard = self.wizard()
        wizard.result_canvas.clear()
        
        x_axis = self._x_axis.currentData()
        y_axis = self._y_axis.currentData()
        
        plot_data = wizard.result_datacontainer.getPlotData(x_axis, y_axis)
        
        wizard.result_canvas.addPlotData(plot_data)