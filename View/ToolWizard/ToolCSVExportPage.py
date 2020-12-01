# -*- coding: utf-8 -*-
"""
Created on Mon Jan  8 11:14:50 2018

@author: Maximilian Seidler
"""

from PyQt5 import QtCore, QtGui, QtWidgets
import os.path
import math
import html

import View.MainWindow
import DataHandling.DataContainer
import my_utilities
import Constants

class ToolCSVExportPage(QtWidgets.QWizardPage):
    def __init__(self, parent = None):
        """Initialize the CSVExporter.
        Parameters
        ----------
            datacontainer : DataContainer
                The datacontainer to export
            parent : QWidget, optional
                The parent
        """
        
        super(ToolCSVExportPage, self).__init__(parent)
        
        self.csv_filename = None
    
    def initializePage(self):
        wizard = self.wizard()
        
        # get the name of the datacontainer
        self._container_name = str(os.path.basename(wizard.result_datacontainer.filepath))
        self._container_name = self._container_name.rsplit(".rw.dat", 1)
        
        if len(self._container_name) == 1:
            self._container_name = self._container_name[0].rsplit(".dat", 1)
            
        self._container_name = self._container_name[0]
        
        # set title and icon
        self.setWindowTitle("Export {} to CSV".format(self._container_name))
        self.setWindowIcon(QtGui.QIcon(View.MainWindow.MainWindow.ICON))
        self.resize(500, 680)
        
        # the description
        self.setSubTitle(("Export the {} to a .csv file. The <i>Full swipe data</i> mode " + 
                         "uses the processed and fitted data. This means that one set of values " + 
                         "(which is one row in the csv file) will be one full swipe. " + 
                         "The <i>Full swipe data</i> mode provides for example the magnetization. " +
                         "<br />The <i>Single data points</i> mode will add each record " + 
                         "that the squid has done. This will create a .csv file which " + 
                         "contains the raw data which are not (necessarily) fitted. <br /><br />" + 
                         "<b>Note</b>: The preview is rounded, the resulting csv " + 
                         "will contain the full numbers without <b>any</b> rounding.").format(html.escape(self._container_name)))
        
        # the mode
        mode_label = QtWidgets.QLabel("Export mode")
        self._mode_datacontainer = QtWidgets.QRadioButton("Full swipe data")
        self._mode_datacontainer.setChecked(True)
        self._mode_datacontainer.toggled.connect(self._actionChangeMode)
        self._mode_datapoints = QtWidgets.QRadioButton("Single data points")
        self._mode_datapoints.toggled.connect(self._actionChangeMode)
        
        # the mode layout
        modes = QtWidgets.QHBoxLayout()
        modes.setContentsMargins(10, 2, 10, 2)
        modes.addWidget(self._mode_datacontainer)
        modes.addWidget(self._mode_datapoints)
        modes.addStretch(1)
        
        # add and remove buttons
        add_remove_label = QtWidgets.QLabel("Add/remove column in the csv file")
        add = QtWidgets.QPushButton("+")
        rem = QtWidgets.QPushButton("-")
        
        add.clicked.connect(self._actionAddColumn)
        rem.clicked.connect(self._actionRemoveColumn)
        
        add_remove_box = QtWidgets.QHBoxLayout()
        add_remove_box.addWidget(add)
        add_remove_box.addWidget(rem)
        add_remove_box.addStretch(1)
        
        # the preview table settings
        self._preview_row_count = 16
        self._preview_col_count = 4
        
        # the preview table
        self._content_table = QtWidgets.QTableWidget()
        
#        buttons.layout().setDirection(QtWidgets.QBoxLayout.RightToLeft)
        
        # add all contantes to the layout
        layout = QtWidgets.QGridLayout()
        
        l = 0
        
#        layout.addWidget(View.MainWindow.MainWindow.createSeparatorLine(), l, 0, 1, 3)
#        l += 1
        
#        layout.addWidget(filename_label, l, 0)
#        layout.addWidget(filename_display, l, 1)
#        layout.addWidget(filename_select, l, 2)
#        l += 1
        
        layout.addWidget(mode_label, l, 0)
        layout.addItem(modes, l, 1, 1, 2)
        l += 1
        
        layout.addWidget(add_remove_label, l, 0)
        layout.addItem(add_remove_box, l, 1, 1, 2)
        l += 1
        
        layout.addWidget(self._content_table, l, 0, 1, 3)
        l += 1
        l += 1
        
        self.setLayout(layout)
        self._actionChangeMode()
        
        own_id = wizard.getIdOfPage(self)
        wizard.addCalculation(own_id, self.saveCSV, "Exporting to csv...")
        wizard.changeSize(None, 800)
    
    def clearTable(self):
        """Clear the table, make it preview_row_count x preview_col_count big,
        all cells are empty"""
        
        self._content_table.setRowCount(self._preview_row_count)
        self._content_table.setColumnCount(self._preview_col_count)
        
        self._content_table.clear()
    
    def getMode(self):
        """Get the mode, 0 is for datacontainer mode, 1 stands for datapoint mode
        Returns
        -------
            int
                The mode
        """
        
        if self._mode_datacontainer.isChecked():
            return 0
        else:
            return 1
    
    def addCombobox(self, column, preselect = 0):
        """Add a combobox to the current table at the column. If the table does
        not have enough columns the column will be added automatically. You can
        pre-select one of the combobox entries. The preselect parameter can either
        be the index or the text that should be selected.
        In addition this will fill the whole table column with the corresponding
        values of the datacontainer if the preselect is valid
        Parameters
        ----------
            column : int
                The index of the column where to add a new combobox in
            preselect : int or String, optional
                The selected index or text
        """
        
        mode = self.getMode()
        
        # create the combobox
        combobox = QtWidgets.QComboBox()
        combobox.setProperty("column", column)
        self._setComboboxText(combobox, mode)
        combobox.activated.connect(self._actionCombobox)
        
        # check if the table is big enough
        if self._content_table.columnCount() <= column:
            self._content_table.setColumnCount(column + 1)
        
        # add the combobox
        self._content_table.setCellWidget(0, column, combobox)
        
        # check if the preselect is valid
        index = -1
        if isinstance(preselect, str):
            index = combobox.findData(preselect)
        elif isinstance(preselect, int):
            index = preselect
        
        # if it is emit the activated signal so the column will be filled
        if index >= 0 and index < combobox.count():
            combobox.setCurrentIndex(index)
            combobox.activated.emit(index)
    
    def _setComboboxText(self, combobox, mode = 0):
        """Initialize the comboboxes for the axis. This will add the possible
        axis to the given combobox and connect the signal when the axis are
        toggled for repainting the preview
        Parameters
        ----------
            combobox : QComboBox
                The combobox to dispaly the axis
        """
        
        wizard = self.wizard()
        combobox.clear()
        
        # data from datacontainer/datapoint
        if mode == 0:
            data = (DataHandling.DataContainer.DataContainer.MAGNETIZATION,
                    DataHandling.DataContainer.DataContainer.TEMPERATURE,
                    DataHandling.DataContainer.DataContainer.HIGH_TEMPERATURE,
                    DataHandling.DataContainer.DataContainer.LOW_TEMPERATURE,
                    DataHandling.DataContainer.DataContainer.FIELD,
                    DataHandling.DataContainer.DataContainer.HIGH_FIELD,
                    DataHandling.DataContainer.DataContainer.LOW_FIELD,
                    DataHandling.DataContainer.DataContainer.DRIFT,
                    DataHandling.DataContainer.DataContainer.SLOPE,
                    DataHandling.DataContainer.DataContainer.FIXED_AMPLITUDE,
                    DataHandling.DataContainer.DataContainer.FREE_AMPLITUDE,
                    DataHandling.DataContainer.DataContainer.SQUID_RANGE,
                    DataHandling.DataPoint.DataPoint.TIMESTAMP)
        else:
            data = (
                DataHandling.DataPoint.DataPoint.LINENUMBER,
                DataHandling.DataPoint.DataPoint.COMMENT,
                DataHandling.DataPoint.DataPoint.RAW_POSITION,
                DataHandling.DataPoint.DataPoint.RAW_VOLTAGE,
                DataHandling.DataPoint.DataPoint.PROCESSED_VOLTAGE,
                DataHandling.DataPoint.DataPoint.FIXED_FIT_VOLTAGE,
                DataHandling.DataPoint.DataPoint.FREE_FIT_VOLTAGE,
                DataHandling.DataPoint.DataPoint.FIT,
                DataHandling.DataPoint.DataPoint.TIMESTAMP)
        
        # replace the value with a proper name
        for value in data:
            name = value
            if value in Constants.ENVIRONMENT_VARIABLE_NAMES:
                name = Constants.ENVIRONMENT_VARIABLE_NAMES[value]
            elif len(wizard.result_datacontainer.datapoints) > 0:
                name = wizard.result_datacontainer.datapoints[0].getNameForAxis(value)
                
            combobox.addItem(name, value)
        
    def _actionCombobox(self):
        """The action method for the combobox. This will change the column to 
        contain a preview of the datacontainers values"""
        
        wizard = self.wizard()
        sender = self.sender()
        
        if isinstance(sender, QtWidgets.QComboBox):
            # the axis and the column
            column = sender.property("column")
            axis = sender.itemData(sender.currentIndex())
            
            if my_utilities.is_numeric(column) and axis != None:
                column = int(column)
                mode = self.getMode()
                name = sender.currentText()
                
                # check the current mode and get the data for the mode and for 
                # the axis
                if mode == 0:
                    data, unit = wizard.result_datacontainer.getDataForExport(axis)
                elif mode == 1:
                    data, unit = wizard.result_datacontainer.getDataPointDataForCSVExport(axis)
                
                data = data[0:self._preview_row_count - 1]
                
                # find exponent of the highest value
                d = int(math.log10(abs(max(data))))
                if d < 1:
                    d -= 1
                
                # parse the unit
                unit = str(unit)
                
                # add the table items
                for i in range(0, self._preview_row_count - 1):
                    # add the name and the unit in the 2nd row, in the last row
                    # add ...
                    if i == self._preview_row_count - 2:
                        text = "..."
                        align = QtCore.Qt.AlignCenter
                    elif i == 0:
                        text = str(name)
                        if unit != "":
                            text += " [" + unit + "] (rounded)"
                        align = QtCore.Qt.AlignCenter
                    else:
                        if d < 1:
                            text = str(round(data[i]* 10**(-1 * d), 3)) + "E" + str(d)
                        else:
                            text = str(round(data[i]))
                        align = QtCore.Qt.AlignLeft
                    
                    # create and add the item
                    item = QtWidgets.QTableWidgetItem(text)
                    item.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
                    item.setTextAlignment(align)
                    
                    self._content_table.setItem(i + 1, column, item)
    
    def _actionAddColumn(self):
        """The action method for the add button, this will add a new column 
        and a new combobox to the table"""
        
        self.addCombobox(self._content_table.columnCount())
    
    def _actionRemoveColumn(self):
        """The action method for the remove button, this removes the last column"""
        
        self._content_table.setColumnCount(self._content_table.columnCount() - 1)
    
    def _actionChangeMode(self):
        """The action method for changing the mode, this will reset the table
        to the defaults"""
        
        self.clearTable()
        
        if self.getMode() == 0:
            self.addCombobox(0, DataHandling.DataPoint.DataPoint.TIMESTAMP)
            self.addCombobox(2, DataHandling.DataContainer.DataContainer.TEMPERATURE)
            self.addCombobox(1, DataHandling.DataContainer.DataContainer.FIELD)
            self.addCombobox(3, DataHandling.DataContainer.DataContainer.MAGNETIZATION)
        else:
            self.addCombobox(0, DataHandling.DataPoint.DataPoint.TIMESTAMP)
            self.addCombobox(1, DataHandling.DataPoint.DataPoint.RAW_POSITION)
            self.addCombobox(2, DataHandling.DataPoint.DataPoint.RAW_VOLTAGE)
            self.addCombobox(3, DataHandling.DataPoint.DataPoint.FIT)
    
    def saveCSV(self):
        """Save the csv file defined by the user
        """
        
        wizard = self.wizard()
        column_axis = []
        
        for i in range(0, self._content_table.columnCount()):
            combobox = self._content_table.cellWidget(0, i)
            
            if isinstance(combobox, QtWidgets.QComboBox):
                # the axis
                axis = combobox.itemData(combobox.currentIndex())
                
                if axis != None:
                    column_axis.append(axis)
        
        wizard.result_csv_file_columns = column_axis
        wizard.result_csv_file_mode = self.getMode()