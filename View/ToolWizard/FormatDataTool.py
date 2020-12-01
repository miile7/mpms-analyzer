# -*- coding: utf-8 -*-
"""
Created on Tue Feb 20 11:01:48 2018

@author: Maximilian Seidler
"""

from PyQt5 import QtWidgets, QtGui, QtCore

import DataHandling.DataContainer
import View.ToolWizard.Tool
import View.PlotCanvas
import View.MainWindow
import my_utilities
import Constants

class FormatDataTool(View.ToolWizard.Tool.Tool):
    def __init__(self):
        """Initialize the tool"""
        
        super(FormatDataTool, self).__init__("format_data",
                title="Format data",
                tooltip="Format the appearence of the data",
                action_name="Format data",
                calculating_text="Formatting...",
                icon=my_utilities.image("icon_format.svg"),
                needs_background_datacontainer=False,
                needs_measurement_type=True
                )
        
        self._page = None
        
    def initializeTool(self):
        """Initialize the tool"""
        
        self._page = ToolFormatPage(self.wizard.controller)
        self.wizard.addPage(self._page)
    
    @property
    def preview(self):
        wizard = self.wizard
        
        return(wizard.measurement_variable, 
               DataHandling.DataContainer.DataContainer.MAGNETIZATION)

    @preview.setter
    def preview(self, value):
        return False

class ToolFormatPage(QtWidgets.QWizardPage):
    def __init__(self, controller, parent = None):
        """Initialize the data formatting page. This will be skipped if the user
        is not using a file (=DataContainer).
        Parameters
        ----------
            parent : QWidget, optional
                The parent
        """
        
        # initialize the page
        super(ToolFormatPage, self).__init__(parent)
        self.setTitle("Formatting data")
        self.setSubTitle("Format the data in the way you need to use it.")
        
        self.is_initialized = False
        self._controller = controller
        
        # set layout
        layout = QtWidgets.QGridLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(30, 15, 30, 15)
        
        # add axis select
        layout.addWidget(QtWidgets.QLabel("Select the x and y axis for plotting " + 
                                          "the data"), 0, 0)
        
        # x axis
        axis_label = QtWidgets.QLabel("x-axis")
        axis_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        layout.addWidget(axis_label, 1, 0)
        
        self._x_axis_combobox = QtWidgets.QComboBox(self)
        layout.addWidget(self._x_axis_combobox, 1, 1)
        
        # y axis
        axis_label = QtWidgets.QLabel("y-axis")
        axis_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        layout.addWidget(axis_label, 2, 0)
        
        self._y_axis_combobox = QtWidgets.QComboBox(self)
        layout.addWidget(self._y_axis_combobox, 2, 1)
        
        # cut data table
        cut_data_label = QtWidgets.QLabel("Data segmets:")
        layout.addWidget(cut_data_label, 3, 0)
        
        # cut buttons for adding and removing segments
        self._add_button = QtWidgets.QPushButton("Add segmet")
        self._add_button.clicked.connect(self._actionAddRow)
        self._rem_button = QtWidgets.QPushButton("Remove segmet")
        self._rem_button.setEnabled(False)
        self._rem_button.clicked.connect(self._actionRemoveSelectedRow)
        
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addWidget(self._add_button)
        button_layout.addWidget(self._rem_button)
        button_layout.addStretch(1)
        layout.addItem(button_layout, 3, 1)
        
        # the segment list
        self._cut_data_list = QtWidgets.QTableWidget(self)
        self._cut_data_list.setRowCount(0)
        self._cut_data_list.setColumnCount(2)
        self._cut_data_list.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self._cut_data_list.itemSelectionChanged.connect(self._actionListSelect)
        self._cut_data_list.setHorizontalHeaderLabels(["segmet name",
                                                       "datapoints"])
        self._cut_data_list.itemChanged.connect(self._actionSegmentsChanged)
        
        # set the header and the resizing behaviour
        header = self._cut_data_list.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
        layout.addWidget(self._cut_data_list, 5, 0, 1, 2)
        
        # create preview
        self._preview = View.PlotCanvas.PlotCanvas()
        layout.addWidget(self._preview, 6, 0, 1, 2)
        
        self.setLayout(layout)
 
    def initializePage(self):
        """Initialize the page"""
        
        self._is_initialized = False
        
        # the parent wizard
        wizard = self.wizard()
        
        # get the datacontainer
        self._datacontainer = wizard.result_datacontainer
        
        # add the possible plot variables
        self._initAxisCombobox(self._x_axis_combobox)
        self._initAxisCombobox(self._y_axis_combobox)
            
        # insert a new row
        self._cut_data_list.setRowCount(1)
        
        # set the unused points, QTableCellItems do not support html!
        label = QtWidgets.QLabel("<i>Unused points</i>")
        self._cut_data_list.setCellWidget(0, 0, label)
        
        unused_points = QtWidgets.QLabel("")
        self._cut_data_list.setCellWidget(0, 1, unused_points)
        
        if self._datacontainer != None:
            # check if the measurement is M(T) or M(H), for this plot H vs T
            temp_field_plot = self._datacontainer.getPlotData(DataHandling.DataContainer.DataContainer.FIELD,
                                                              DataHandling.DataContainer.DataContainer.TEMPERATURE,
                                                              None,
                                                              False)
            
            # get running variable
            if wizard.measurement_variable == DataHandling.DataContainer.DataContainer.TEMPERATURE:
                groups, ranges = self._controller.uniqueListThreshold(
                        temp_field_plot.x, 
                        abs(min(temp_field_plot.x) /  Constants.STATIC_VALUE_THRESHOLD))
                
                divide_label = temp_field_plot.x_label
                divide_key = DataHandling.DataContainer.DataContainer.FIELD
            else:
                groups, ranges = self._controller.uniqueListThreshold(
                        temp_field_plot.y, 
                        abs(min(temp_field_plot.y) /  Constants.STATIC_VALUE_THRESHOLD))
                
                divide_label = temp_field_plot.y_label
                divide_key = DataHandling.DataContainer.DataContainer.TEMPERATURE
            
            # check if all datapoints are in the ranges
            remaining = set(range(0, len(self._datacontainer.datapoints)))
            
            # create the segments and add them to the segments list
            if isinstance(ranges, dict):
                # go through all ranges
                for i in ranges:
                    # create the segments value/the cause why this is in this segment
                    mi = min(ranges[i])
                    ma = max(ranges[i])
                    name = divide_label
                    segment_value = my_utilities.mean_std((mi, ma))
                    segment_value = str(round(segment_value[0], 3)) + "\u00B1" + str(round(segment_value[1], 3))
                    
                    name = name + ": " + segment_value
                    
                    # find all the datapoints that are in this segment
                    datapoints = self._datacontainer.findDataPointsInRange(divide_key,
                                                                           mi, ma,
                                                                           True)
                    datapoints = [d[1] for d in datapoints]
                    
                    remaining = remaining - set(datapoints)
                    
                    self.addRow(name, datapoints)
            else:
                self.addRow("", list(range(0, len(self._datacontainer.datapoints))))
        
        # if there are missing datapoints display them, otherwise the user will
        # not immediately see that there are missing points
        if len(remaining) > 0:
            self.addRow("<unknown>", list(remaining))
            
        # select the index that the program assumed is the control variable
        index = self._x_axis_combobox.findData(wizard.measurement_variable)
            
        if index >= 0:
            self._x_axis_combobox.setCurrentIndex(index)
            
        # select the magnetization index
        index = self._y_axis_combobox.findData(DataHandling.DataContainer.DataContainer.MAGNETIZATION)
            
        if index >= 0:
            self._y_axis_combobox.setCurrentIndex(index)
        
        self.is_initialized = True
        self._actionSegmentsChanged()
        
        # increase the size to make everything readable
        wizard.changeSize(None, 800)
    
    def addRow(self, segment_name = "", datapoint_indices = None):
        """Add a row to the segments table. The segment_name should tell any name
        which may clarify what this segemt is about, the segment_value tells the
        exact reason why this segment is a different segment. The datapoint_indices
        are the indices that define this segment.
        Parameters
        ----------
            segment_name: String, QTableWidgetItem or QWidget, optional
                The name of the segment
            datapoint_indices: list of int, String or QWidget, optional
                The indices of the datapoints
        """
        
         # create the segments/ranges name, this is the non-control-variable
        if not isinstance(segment_name, QtWidgets.QTableWidgetItem):
            segment_name = QtWidgets.QTableWidgetItem(str(segment_name))
        
        if isinstance(datapoint_indices, list) or isinstance(datapoint_indices, tuple):
            # create a human readable string of all the datapoints using
            # the colons for ranges and semikolons for dividing, for example
            # 100:200;203;204;210:223
            datapoint_indices = self._controller.zipIndices(datapoint_indices)
        elif datapoint_indices == None or datapoint_indices == False:
            datapoint_indices = ""
        elif not isinstance(datapoint_indices, QtWidgets.QWidget):
            datapoint_indices = str(datapoint_indices)
        
        if not isinstance(datapoint_indices, QtWidgets.QWidget):
            # set the qline edit, add the validator
            datapoint_indices = QtWidgets.QLineEdit(datapoint_indices)
            datapoint_indices.setFrame(False)
            datapoint_indices.setValidator(QtGui.QRegExpValidator(QtCore.QRegExp(r"^[\d;:]*$")))
            datapoint_indices.setStyleSheet("QLineEdit{background: rgba(0, 0, 0, 0)}")
            datapoint_indices.textChanged.connect(self._actionSegmentsChanged)
        
        # insert a new row
        current_row = self._cut_data_list.rowCount()
        self._cut_data_list.insertRow(current_row)
        
        # set all the cells
        self._cut_data_list.setItem(current_row, 0, segment_name)
        self._cut_data_list.setCellWidget(current_row, 1, datapoint_indices)
    
    def _initAxisCombobox(self, combobox):
        """Initialize the comboboxes for the axis. This will add the possible
        axis to the given combobox and connect the signal when the axis are
        toggled for repainting the preview
        Parameters
        ----------
            combobox : QCombobox
                The combobox to dispaly the axis
        """
        
        # the values that do not make sense to plot are commented but it is 
        # technically possible to plot them all
        
        # data form datacontainer
        data = self.wizard().getAllowedDataContainerAxis()
        
        for value in data:
            name = value
            if value in Constants.ENVIRONMENT_VARIABLE_NAMES:
                name = Constants.ENVIRONMENT_VARIABLE_NAMES[value]
            elif len(self._datacontainer.datapoints) > 0:
                name = self._datacontainer.datapoints[0].getNameForAxis(value)
                
            combobox.addItem(name, value)
            
        combobox.activated.connect(self._actionToggle)
    
    def getDatapointScopes(self):
        """Detect the scopes entered in the segments/cut_data list. They have 
        to be in the format with integer ranges (with colons) and integer divided
        by semikolons (have a look at the Controller.zipIndices()
        function)
        """
        
        # prepare the variables, pre-compile the regex to save some speed
        scopes = []
        
        if self._cut_data_list.rowCount() > 0:
            # go through all rows of the segments table
            for i in range(0, self._cut_data_list.rowCount()):
                # receive the name
                
                segment_name = self._cut_data_list.item(i, 0)
                if isinstance(segment_name, QtWidgets.QTableWidgetItem):
                    segment_name = str(segment_name.text())
                
                # split the datapoints
                datapoints_text = self._cut_data_list.cellWidget(i, 1)
                datapoints = None
                if isinstance(datapoints_text, QtWidgets.QLineEdit):
                    datapoints_text = datapoints_text.text()
                    datapoints = self._controller.unzipIndices(datapoints_text)
                
                # add the current scope
                if (isinstance(datapoints, (list, tuple)) and 
                    isinstance(segment_name, str)):
                    scopes.append((sorted(datapoints), segment_name))
                    
        return scopes
    
    def _actionToggle(self, datapoint_scopes = None):
        """This is the action method when the combobox is toggled"""
        
        # get the x and y axis
        x_axis = self._x_axis_combobox.itemData(self._x_axis_combobox.currentIndex())
        y_axis = self._y_axis_combobox.itemData(self._y_axis_combobox.currentIndex())
            
        # save plot_data for wizard
        plot_data_wizard = []
        
        # check if they are selected
        if x_axis != "" and y_axis != "":
            # check the current scopes
            if datapoint_scopes == None or not isinstance(datapoint_scopes, list):
                datapoint_scopes = self.getDatapointScopes()
            
            # clear the plot formats
            self._datacontainer.clearPlotFormat()
            
            # clear preview
            self._preview.clear()
            
            # set title
            if "title" in self._datacontainer.header:
                self._preview.title = self._datacontainer.header["title"]
                self.wizard().plot_title = self._preview.title
            
            # print the current scopes with the given axis
            for scope, segment_name in datapoint_scopes:
                plotdata = self._datacontainer.getPlotData(x_axis, y_axis, scope, False)
                if segment_name != "" and segment_name != None:
                    plotdata.setTitle(segment_name)
                
                # draw the graph
                self._preview.addPlotData(plotdata)
                plot_data_wizard.append(plotdata)
                
                self._datacontainer.addPlotFormat(segment_name, scope)
        
    def _actionListSelect(self):
        """This is the action method if the list is being selected or deselected. 
        This will enable or disable the remove button"""
        
        # receive the selected indices
        indices = self._cut_data_list.selectedIndexes()
        
        # check if there are any selected indices, if there are enable the 
        # delete button
        if isinstance(indices, list) and len(indices) > 0:
            self._rem_button.setEnabled(True)
        else:
            self._rem_button.setEnabled(False)
        
    def _actionAddRow(self):
        """This is the action method for adding a row to the segments list. This
        will be triggered when the add button is hit"""
        
        self.addRow()
        self._actionSegmentsChanged()
    
    def _actionRemoveSelectedRow(self):
        """This is the action method for removing a row to the segments list. This
        will be triggered when the remove button is hit. For removing the rows
        they have to be selected"""
        
        # receive the selected indices
        indices = self._cut_data_list.selectedIndexes()
        
        # get the selected rows, unique the rows first, this is very important!
        # for every *cell* there will be a selected index, this means iterating
        # over the cells and removing immediately will remove the last row 
        # multiple times!
        rows = set()
        if isinstance(indices, list) and len(indices) > 0:
            for index in indices:
                if index.row() > 0:
                    rows.add(index.row())
        
        # sort the rows from end to beginning, otherwise the removing will also
        # change the indices
        rows = sorted(list(rows), reverse=True)
        
        # remove all the rows that are selected
        for row in rows:
            self._cut_data_list.removeRow(row)
        
        if len(rows) > 0:
            self._actionSegmentsChanged()
    
    def _actionSegmentsChanged(self):
        """This is the action method when the segments changed"""
        
        if self.is_initialized:
            # receive the segments, save used and unused segments
            segments = self.getDatapointScopes()
            used = []
            unused = list(range(0, len(self._datacontainer.datapoints)))
            
            # go through segments, remove the segments form the ununsed and add
            # them to the used
            for scope, scope_name in segments:
                used = used + scope
                unused = list(set(unused) - set(scope))
            
            # print the label
            widget = self._cut_data_list.cellWidget(0, 1)
            if isinstance(widget, QtWidgets.QLabel):
                if len(unused) == 0:
                    widget.setText("-")
                else:
                    widget.setText("{}".format(self._controller.zipIndices(unused)))
            
            # trigger the segments change to update the graph
            self._actionToggle(segments)