# -*- coding: utf-8 -*-
"""
Created on Wed Feb 14 15:20:54 2018

@author: miile7
"""

from PyQt5 import QtCore, QtGui, QtWidgets
import copy

import View.MainWindow
import View.SelectDataContainerWidget
import DataHandling.DataContainer

class ToolInputPage(QtWidgets.QWizardPage):
    def __init__(self, parent = None):
        
        super(ToolInputPage, self).__init__(parent)
        
        # set title and description
        self.setTitle("Select data")
        
        self._show_background_datacontainer = True
        
        self._datacontainer_mode = "normal"
        
        self._background_label = None
        self._background_name = None
        self._temp_loaded_datapoints = set()
        
    @property
    def show_background_datacontainer(self):
        return self._show_background_datacontainer

    @show_background_datacontainer.setter
    def show_background_datacontainer(self, show_background_datacontainer):
        self._show_background_datacontainer = show_background_datacontainer
        
        self._initializeBackground()
    
    def initializePage(self):
        """Initialize the QWizardPage"""
        
        wizard = self.wizard()
        parent = self.parent()
        
        layout = QtWidgets.QGridLayout()
        
        # the file selecting
        file_label = QtWidgets.QLabel("Sample measurement (contains background)")
        layout.addWidget(file_label, 0, 0)
        
        self._file_name = View.SelectDataContainerWidget.SelectDataContainerWidget(
                wizard.controller, parent)
        self._file_name.setProperty("datacontainer_mode", "normal")
        self._file_name.openedDataContainer.connect(self.actionDataContainerSelected)
        
        # set initial datacontainer 
        if (wizard.sample_datacontainer != None and 
            isinstance(wizard.sample_datacontainer, DataHandling.DataContainer.DataContainer)):
            self._file_name.selected_datacontainer = wizard.sample_datacontainer
            
        layout.addWidget(self._file_name, 0, 1)
        
        # the background selecting
        self._background_label = QtWidgets.QLabel("Background measurement")
        layout.addWidget(self._background_label, 1, 0)
        
        self._background_name = View.SelectDataContainerWidget.SelectDataContainerWidget(
                wizard.controller, parent)
        self._background_name.setProperty("datacontainer_mode", "background")
        self._background_name.openedDataContainer.connect(self.actionDataContainerSelected)
        
        # set initial datacontainer 
        if (wizard.background_datacontainer != None and 
            isinstance(wizard.background_datacontainer, DataHandling.DataContainer.DataContainer)):
            self._background_name.selected_datacontainer = wizard.background_datacontainer
            
        layout.addWidget(self._background_name, 1, 1)
        
        # whether the measurement is M(T) or M(H)
        measurement_type = QtWidgets.QLabel("Measurement type")
        layout.addWidget(measurement_type, 2, 0)
        
        self._measurement_T = QtWidgets.QRadioButton("M(T)")
        self._measurement_T.toggled.connect(self.actionMeasurementVaraibleChanged)
        self._measurement_H = QtWidgets.QRadioButton("M(H)")
        self._measurement_H.toggled.connect(self.actionMeasurementVaraibleChanged)
        
        # set initial datacontainer 
        if (wizard.sample_datacontainer != None and 
            isinstance(wizard.sample_datacontainer, DataHandling.DataContainer.DataContainer)):
            
            if wizard.sample_datacontainer.measurement_variable == DataHandling.DataContainer.DataContainer.FIELD:
                self._measurement_H.setChecked(True)
            elif wizard.sample_datacontainer.measurement_variable == DataHandling.DataContainer.DataContainer.TEMPERATURE:
                self._measurement_T.setChecked(True)
            
        radio_buttons_layout = QtWidgets.QHBoxLayout()
        radio_buttons_layout.addWidget(self._measurement_T)
        radio_buttons_layout.addWidget(self._measurement_H)
        radio_buttons_layout.addStretch(1)
        
        layout.addItem(radio_buttons_layout, 2, 1, 1, 2)
        
        self._initializeBackground()
        
        # set the layout
        self.setLayout(layout)
    
    def _initializeBackground(self, has_background = None):
        """Initialize the background, this will change the labels depending whether
        the tool needs a background or not
        
        Parameters
        ----------
            has_background : boolean
                Whether the input page should show the background input or not
        """
        
        if has_background == None:
            has_background = self._show_background_datacontainer
        
        # set the subtitle text
        text = "Select the source of the sample measurmenet"
        if has_background:
            text += (" (which includes the background data) and the data of the " + 
                "background measurement")
        text += "."
        
        self.setSubTitle(text)
        
        # hide/show the input for the background
        if self._background_label != None and self._background_name:
            self._background_label.setVisible(has_background)
            self._background_name.setVisible(has_background)
    
    def isComplete(self):
        """Check whether the page is complete
        
        Returns
        -------
            boolean
                Whether the page is complete or not
        """
        
        datacontainer = self._file_name.selected_datacontainer
        
        if not isinstance(datacontainer, DataHandling.DataContainer.DataContainer):
            return False
        
        if self._show_background_datacontainer:
            background = self._background_name.selected_datacontainer
            
            if not isinstance(background, DataHandling.DataContainer.DataContainer):
                return False
        
        return self._measurement_T.isChecked() or self._measurement_H.isChecked()
        
    def actionShowOpenDialog(self):
        """Action method for showing the open dialog"""
        
        wizard = self.wizard()
        sender = self.sender()
        
        if isinstance(sender, QtCore.QObject):
            self._datacontainer_mode = str(sender.property("type"))
            if self._datacontainer_mode  == "background":
                title = "Select the background File"
            else:
                title = "Selet the measurement including background"
                
            wizard.view.showOpenDialog(title, False, {"add_to_filelist": False,
                                                    "exec_fit": False})
    
    def actionMeasurementVaraibleChanged(self):
        """Action method for changing the measurement type"""
        
        wizard = self.wizard()
        
        if self._measurement_T.isChecked():
            wizard.measurement_variable = DataHandling.DataContainer.DataContainer.TEMPERATURE
        elif self._measurement_H.isChecked():
            wizard.measurement_variable = DataHandling.DataContainer.DataContainer.FIELD
            
        self.updateMeasurementVariable()
        
        self.completeChanged.emit()
    
    def updateMeasurementVariable(self, datacontainer = None):
        """Update the measurement variable in the wizards datacontainers, in the
        wizard and in the given datacontainer
        
        Parameter
        ---------
            datacontainer : DataContainer, optional
                The datacontainer to set the measurement variable in
        """
        
        wizard = self.wizard()
        
        if isinstance(wizard.sample_datacontainer, DataHandling.DataContainer.DataContainer):
            wizard.sample_datacontainer.measurement_variable = wizard.measurement_variable
        
        if isinstance(wizard.result_datacontainer, DataHandling.DataContainer.DataContainer):
            wizard.result_datacontainer.measurement_variable = wizard.measurement_variable
        
        if isinstance(wizard.background_datacontainer, DataHandling.DataContainer.DataContainer):
            wizard.background_datacontainer.measurement_variable = wizard.measurement_variable
            
        if isinstance(self._file_name.selected_datacontainer, DataHandling.DataContainer.DataContainer):
            self._file_name.selected_datacontainer.measurement_variable = wizard.measurement_variable
            
        if isinstance(self._background_name.selected_datacontainer, DataHandling.DataContainer.DataContainer):
            self._background_name.selected_datacontainer.measurement_variable = wizard.measurement_variable
            
        if isinstance(datacontainer, DataHandling.DataContainer.DataContainer):
            datacontainer.measurement_variable = wizard.measurement_variable
         
    def actionDataContainerSelected(self, datacontainer):
        """Action method when a datacontainer has been selected
        
        Parameters
        ----------
            datacontainer : DataContainer
                The selected datacontainer
        """
        
        sender = self.sender()
        
        if isinstance(datacontainer, DataHandling.DataContainer.DataContainer):
            self._temp_loaded_datapoints.add(datacontainer)
            
            self._file_name.additional_datacontainers = self._temp_loaded_datapoints
            self._background_name.additional_datacontainers = self._temp_loaded_datapoints
        
        if isinstance(sender, QtCore.QObject):
            datacontainer_mode = sender.property("datacontainer_mode")
            wizard = self.wizard()
            
            if datacontainer.measurement_variable == DataHandling.DataContainer.DataContainer.TEMPERATURE:
                self._measurement_T.setChecked(True)
            elif datacontainer.measurement_variable == DataHandling.DataContainer.DataContainer.FIELD:
                self._measurement_H.setChecked(True)
            else:
                self.updateMeasurementVariable(datacontainer)
            
            if datacontainer_mode == "normal":
                wizard.sample_datacontainer = datacontainer
                # prepare the result so there always is a result, pages are only
                # working on the result datacontainer
                wizard.result_datacontainer = copy.deepcopy(datacontainer)
            elif datacontainer_mode == "background":
                wizard.background_datacontainer = datacontainer
            
        self.completeChanged.emit()
    
    def getDataContainer(self):
        """Get the datacontainer
        
        Returns
        -------
            DataContainer
                The datacontainer
        """
        
        return self._file_name.selected_datacontainer
    
    def getBackgroundDataContainer(self):
        """Get the background datacontainer
        
        Returns
        -------
            DataContainer
                The background datacontainer
        """
        
        return self._background_name.selected_datacontainer

    def getMode(self):
        """Get the measurement variable mode
        
        Returns
        -------
            String
                The mode as a environment variable constant
        """
        
        if self._measurement_T.isChecked():
            return DataHandling.DataContainer.DataContainer.TEMPERATURE
        elif self._measurement_H.isChecked():
            return DataHandling.DataContainer.DataContainer.FIELD
        else:
            return None
    
    def getDataContainerIndex(self):
        """Get the index of the datacontainer in the current datacontainer collection
        in the Controller
        
        Returns
        -------
            int
                The datacontainer index
        """
        
        return self._file_name.getDataContainerIndex()