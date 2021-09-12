# -*- coding: utf-8 -*-
"""
Created on Mon Feb 26 08:36:59 2018

@author: miile7
"""
from PyQt5 import QtWidgets, QtGui, QtCore
import copy

import Constants
import my_utilities
import View.MainWindow
import View.ToolWizard.Tool
import DataHandling.DataPoint
import DataHandling.DataContainer
import View.SelectDataContainerWidget

class DataPointCutTool(View.ToolWizard.Tool.Tool):
    def __init__(self):
        """Initialize the tool"""
        
        super(DataPointCutTool, self).__init__("datapoint_cut",
                title="Edit datapoints",
                tooltip="Edit the datapoints",
                action_name="Edit datapoints",
                calculating_text="Editing points...",
                icon=my_utilities.image("icon_edit.svg")
                )
        
        self._page = None
        
    def initializeTool(self):
        """Initialize the tool"""
        
        self._page = DataPointCutPage(self.wizard)
        self.wizard.addPage(self._page)
        self.addCalculation(self.cutDataPoints)
    
    @property
    def preview(self):
        return (self.wizard.measurement_variable, 
                DataHandling.DataContainer.DataContainer.MAGNETIZATION)

    @preview.setter
    def preview(self, value):
        return False
    
    def cutDataPoints(self):
        """Cut the datapoints for the wizards datacontainers. This is the 
        calculation callback"""
        
        self.wizard.result_datacontainer = self.wizard.controller.cutDataPointRows(
               self.wizard.result_datacontainer, 
                self._page.getConditions())

class DataPointCutPage(QtWidgets.QWizardPage):
    def __init__(self, parent = None):
        super(DataPointCutPage, self).__init__(parent)
        
        # set title and icon
        self.setWindowTitle("Cut Datapoints")
        self.setSubTitle("Cut data off each datapoint. The sweep points that " + 
                         "fulfill the condition are <b>kept</b>, others will be " + 
                         "removed. <br />" + 
                         "This will modify the fits in each point in the M(T)/M(H) " + 
                         "in the given file but not the M(T)/M(H) measurement " + 
                         "file itself!")
        self.setWindowIcon(QtGui.QIcon(View.MainWindow.MainWindow.ICON))
        
    def initializePage(self):
        """Initialize the page"""
        
        wizard = self.wizard()
        
        # the general dialog layout
        layout = QtWidgets.QVBoxLayout()
        
        # the input layout for the datacontainer
        input_layout = QtWidgets.QGridLayout()
        
        # the preview
        self._preview = View.PlotCanvas.PlotCanvas()
        layout.addWidget(self._preview)
        
        button_size = QtCore.QSize(30, 22)
        
        # create buttons with an increase so you have to click 20 times
        number_datapoints = len(wizard.result_datacontainer.datapoints)
        increment_20 = round(number_datapoints / 20)
        
        datapoint_index_layout = QtWidgets.QHBoxLayout()
        label = QtWidgets.QLabel("Datapoint to display")
        datapoint_index_layout.addWidget(label)
        
        if increment_20 > 1:
            self._datapoint_index_20_prev_button = QtWidgets.QPushButton("-{}".format(increment_20))
            self._datapoint_index_20_prev_button.setProperty("increment", -1 * increment_20)
            self._datapoint_index_20_prev_button.clicked.connect(self.incrementDataPointIndex)
            self._datapoint_index_20_prev_button.setFixedSize(button_size)
            datapoint_index_layout.addWidget(self._datapoint_index_20_prev_button)
        
        self._datapoint_index_prev_button = QtWidgets.QPushButton("-1")
        self._datapoint_index_prev_button.setProperty("increment", -1)
        self._datapoint_index_prev_button.clicked.connect(self.incrementDataPointIndex)
        self._datapoint_index_prev_button.setFixedSize(button_size)
        datapoint_index_layout.addWidget(self._datapoint_index_prev_button)
        
        self._datapoint_index_input = QtWidgets.QLineEdit("0")
        validator = QtGui.QIntValidator()
        validator.setRange(0, 0)
        self._datapoint_index_input.setValidator(validator)
        self._datapoint_index_input.textChanged.connect(self.refreshPreview)
        datapoint_index_layout.addWidget(self._datapoint_index_input)
        
        self._datapoint_index_next_button = QtWidgets.QPushButton("+1")
        self._datapoint_index_next_button.setProperty("increment", 1)
        self._datapoint_index_next_button.clicked.connect(self.incrementDataPointIndex)
        self._datapoint_index_next_button.setFixedSize(button_size)
        datapoint_index_layout.addWidget(self._datapoint_index_next_button)
        
        if increment_20 > 1:
            self._datapoint_index_20_next_button = QtWidgets.QPushButton("+{}".format(increment_20))
            self._datapoint_index_20_next_button.setProperty("increment", increment_20)
            self._datapoint_index_20_next_button.clicked.connect(self.incrementDataPointIndex)
            self._datapoint_index_20_next_button.setFixedSize(button_size)
            datapoint_index_layout.addWidget(self._datapoint_index_20_next_button)
        
        input_layout.addLayout(datapoint_index_layout, 1, 1)
        
        self._datapoint_index_max = QtWidgets.QLabel("Number of datapoints: {}".format(number_datapoints))
        input_layout.addWidget(self._datapoint_index_max, 1, 2, QtCore.Qt.AlignRight)
        
        # add the datacontainer input
        layout.addLayout(input_layout)
        
        # separator line for conditions
        layout.addWidget(View.MainWindow.MainWindow.createSeparatorLine())
        
        # add the refresh button
        refresh_box = QtWidgets.QHBoxLayout()
        refresh_box.addStretch(1)
        refresh_button = QtWidgets.QPushButton("Refresh")
        refresh_button.clicked.connect(self.refreshPreview)
        refresh_box.addWidget(refresh_button)
        layout.addLayout(refresh_box)
        
        # prepare condition inputs
        self._condition_key = []
        self._condition_max = []
        self._condition_min = []
        
        # prepare the seletable values
        self.items = (
                DataHandling.DataPoint.DataPoint.LINENUMBER,
                DataHandling.DataPoint.DataPoint.TIMESTAMP,
                DataHandling.DataPoint.DataPoint.RAW_POSITION,
                DataHandling.DataPoint.DataPoint.RAW_VOLTAGE
        )
        self._default_selected_item = 2
        
        self._condition_layout = QtWidgets.QGridLayout()
        layout.addLayout(self._condition_layout)
        
        self.setLayout(layout)
        
        self.refreshPreview()
        
        self.addCondition()
        
        wizard.changeSize(None, 800)
    
    def addCondition(self):
        """Adds a condition line"""
        
        wizard = self.wizard()
        index = len(self._condition_key)
        
        text = ""
        if index > 1:
            text = "<b>and</b> "
        text += "Condition {}".format(index + 1)
        
        label = QtWidgets.QLabel(text)
        self._condition_layout.addWidget(label, index, 0)
        
        key = QtWidgets.QComboBox()
        
        for item in self.items:
            name = item
            if item in Constants.ENVIRONMENT_VARIABLE_NAMES:
                name = Constants.ENVIRONMENT_VARIABLE_NAMES[item]
            elif isinstance(wizard.result_datacontainer, DataHandling.DataContainer.DataContainer):
                dp_index = self.getDataPointIndex()
                
                name = wizard.result_datacontainer.datapoints[dp_index].getNameForAxis(item)
                
            key.addItem(name, item)
        
        key.setCurrentIndex(self._default_selected_item)
        
        self._condition_layout.addWidget(key, index, 1)
        self._condition_key.append(key)
        
        min_label = QtWidgets.QLabel("min")
        self._condition_layout.addWidget(min_label, index, 2)
        
        min_value = QtWidgets.QLineEdit()
        min_value.setValidator(QtGui.QDoubleValidator())
        self._condition_layout.addWidget(min_value, index, 3)
        self._condition_min.append(min_value)
        
        max_label = QtWidgets.QLabel("max")
        self._condition_layout.addWidget(max_label, index, 4)
        
        max_value = QtWidgets.QLineEdit()
        max_value.setValidator(QtGui.QDoubleValidator())
        self._condition_layout.addWidget(max_value, index, 5)
        self._condition_max.append(max_value)
        
    def refreshPreview(self):
        """Refresh the preview"""
        
        wizard = self.wizard()
        
        if (wizard.result_datacontainer != None and 
            isinstance(wizard.result_datacontainer, DataHandling.DataContainer.DataContainer)):
            index = self.getDataPointIndex()
            
            datapoint = wizard.result_datacontainer.datapoints[index]
            plot_data_normal = datapoint.getPlotData(
                    DataHandling.DataPoint.DataPoint.RAW_POSITION,
                    DataHandling.DataPoint.DataPoint.RAW_VOLTAGE
                    )
            plot_data_normal.title = "Datapoint #{} - original".format(index)
            
            datapoint_cut = copy.deepcopy(datapoint)
            datapoint_cut.cutRows(self.getConditions())
            plot_data_cut = datapoint_cut.getPlotData(
                    plot_data_normal.x_axis,
                    plot_data_normal.y_axis
                    )
            plot_data_cut.title = "Datapoint #{} - edited".format(index)
            
            self._preview.clear()
            
            ms = self._preview.markersize
            self._preview.markersize = self._preview.markersize / 2
            self._preview.addPlotData(plot_data_normal)
            
            self._preview.markersize = ms
            self._preview.addPlotData(plot_data_cut)
            
    def getDataPointIndex(self):
        """Get the index of the current datapoint that is selected by the dialog
        
        Returns
        -------
            int
                The index
        """
        
        wizard = self.wizard()
        
        try:
            index = int(self._datapoint_index_input.text())
        except ValueError:
            index = -1
        
        if (wizard.result_datacontainer != None and 
            isinstance(wizard.result_datacontainer, DataHandling.DataContainer.DataContainer) and
            index < 0 or index >= len(wizard.result_datacontainer.datapoints)):
            index = 0
            self._datapoint_index_input.setText(str(index))
        
        return index
    
    def getConditions(self):
        """Create the conditions list. The return value is a list of dicts, each
        dict has a key index and a min and/or max index
        
        Returns
        -------
            list of dict
                the conditions
        """
        
        conditions = []
        
        for i, key_input in enumerate(self._condition_key):
            if i < len(self._condition_max) and i < len(self._condition_min):
                key = str(self._condition_key[i].itemData(self._condition_key[i].currentIndex()))
                
                min_value = self._condition_min[i].text()
                max_value = self._condition_max[i].text()
                
                if (key != "" and (my_utilities.is_numeric(min_value) or 
                                   my_utilities.is_numeric(max_value))):
                    cond = {"key": key}
                    
                    if my_utilities.is_numeric(min_value):
                        cond["min"] = my_utilities.force_float(min_value)
                    
                    if my_utilities.is_numeric(max_value):
                        cond["max"] = my_utilities.force_float(max_value)
                
                    conditions.append(cond)
                    
        return conditions
    
    def incrementDataPointIndex(self, increment = None):
        """Increments the datapoint index, ifthe increment is not given the 
        value will be incremented by 1
        
        Parameters
        ----------
            increment : int
                The increment
        """
        
        sender = self.sender()
        wizard = self.wizard()
        
        if not my_utilities.is_numeric(increment):
            if (isinstance(sender, QtCore.QObject) and 
                my_utilities.is_numeric(sender.property("increment"))):
                
                increment = int(sender.property("increment"))
            else:
                increment = 1
        
        index = self.getDataPointIndex()
        
        index += increment
        
        if (wizard.result_datacontainer != None and 
            isinstance(wizard.result_datacontainer, DataHandling.DataContainer.DataContainer)):
            l = len(wizard.result_datacontainer.datapoints)
            
            if index < 0 or index >= l:
                index = index % l
        else:
            index = 0
        
        self._datapoint_index_input.setText(str(index))