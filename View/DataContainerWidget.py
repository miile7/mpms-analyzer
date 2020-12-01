# -*- coding: utf-8 -*-
"""
Created on Wed Oct 25 13:22:01 2017

@author: Maximilian Seidler
"""

from PyQt5 import QtWidgets, QtCore
import os
import re

import View.QCollapsableWidget
import Controller
import my_utilities

class DataContainerWidget(View.QCollapsableWidget.QCollapsableWidget):
    def __init__(self, datacontainer, view, controller = None):
        # preapare header data, bringing everything to a well readable format
        headerdata = {}
        
        # save warnings
        warnings = []
        
        # add the average data of the datapoints to the header, this should be
        # displayed in front of the other settings, therefore add this before
        headerdata["temperature"] = [""]
        headerdata["field"] = [""]
        headerdata["drift"] = [""]
        headerdata["slope"] = [""]
        headerdata["squid range"] = [""]
        headerdata["given center"] = [""]
        headerdata["fixed amplitude"] = [""]
        
        for datapoint in datacontainer.datapoints:
            # adding temperature in K, trying to calculate the standard deviation
            # by using the low and high temperature, fallback is the high or 
            # low temperature
            try:
                headerdata = self._extractEnvironmentVariableToHeader(headerdata,
                                                                      datapoint,
                                                                      ("low temp", 
                                                                       "high temp"),
                                                                       "temperature")
            except (ValueError, TypeError) as e:
                warnings.append(str(e))
               
            # add the field in Oe, add the standard deviation, if not given use
            # the high or low field as fallback
            try:
                headerdata = self._extractEnvironmentVariableToHeader(headerdata,
                                                                      datapoint,
                                                                      ("low field", 
                                                                       "high field"),
                                                                       "field")
            except (ValueError, TypeError) as e:
                warnings.append(str(e))
            
            # add the squid range
            try:
                headerdata = self._extractEnvironmentVariableToHeader(headerdata,
                                                                      datapoint,
                                                                      "drift")
            except (ValueError, TypeError) as e:
                warnings.append(str(e))
            
            # add the squid range
            try:
                headerdata = self._extractEnvironmentVariableToHeader(headerdata,
                                                                      datapoint,
                                                                      "slope")
            except (ValueError, TypeError) as e:
                warnings.append(str(e))
            
            # add the squid range
            try:
                headerdata = self._extractEnvironmentVariableToHeader(headerdata,
                                                                      datapoint,
                                                                      "squid range")
            except (ValueError, TypeError) as e:
                warnings.append(str(e))
            
            # add the given center
            try:
                headerdata = self._extractEnvironmentVariableToHeader(headerdata,
                                                                      datapoint,
                                                                      "given center")
            except (ValueError, TypeError) as e:
                warnings.append(str(e))
            
            # add the given center
            try:
                headerdata = self._extractEnvironmentVariableToHeader(headerdata,
                                                                      datapoint,
                                                                      "amp fixed",
                                                                      "fixed amplitude")
            except (ValueError, TypeError) as e:
                warnings.append(str(e))
        
        # calculating the averages and standard deviations
        digits = 3
        for key in headerdata:
            if isinstance(headerdata[key], list):
                data = headerdata[key]
                if isinstance(data, (list, tuple)) and len(data) > 0:
                    # remove first element, first element contains the unit
                    if isinstance(data[0], str):
                        unit = data[0]
                        data = data[1::]
                    else:
                        unit = ""
                    
                    if len(data) > 0 and isinstance(data[0], (list, tuple)):
                        errors = [i[1] for i in data]
                        data = [i[0] for i in data]
                        if my_utilities.np.any(errors):
                            # there is are diviations, use error propagation,
                            # if all diviations are 0 just keep the diviation
                            # given by the mean_std function which is the diviation
                            # of calculating the mean
                            mean, diviation = my_utilities.mean_std(data, errors)
                        else:
                            mean, diviation = my_utilities.mean_std(data)
                    else:
                        mean, diviation = my_utilities.mean_std(data)
                    
                    if my_utilities.np.isnan(mean):
                        mean = ""
                        
                    if my_utilities.np.isnan(diviation):
                        diviation = ""
                    
                    is_range = False
                    
                    if key == "temperature":
                        is_range = self._checkForRange(data, 
                                                       Controller.Constants.TEMPERATURE_THRESHOLD, 
                                                       Controller.Constants.TEMPERATURE_MIN_DEVIATION_COUNT)
                    elif key == "field":
                        is_range = self._checkForRange(data, 
                                                       Controller.Constants.FIELD_THRESHOLD, 
                                                       Controller.Constants.FIELD_MIN_DEVIATION_COUNT)
                    
                    if is_range:
                        headerdata[key] = ("{low:.{digits}f} - {high:.{digits}f} {unit}".format(
                                low=min(data), high=max(data), unit=unit, digits=digits))
                    
                    else:
                        headerdata[key] = (("{mean:.{digits}f}" if mean != "" else " - ") + " \u00B1 " + 
                                  ("{diviation:.{digits}f}" if diviation != "" else " - ") + " {unit}").format(
                                mean=mean, diviation=diviation, unit=unit, digits=digits)
                else:
                    headerdata[key] = str(data)
        
        # add the number of datapoints
        headerdata["number of datapoints"] = "{d} ({d} up, {d} down)".format(d=len(datacontainer.datapoints) // 2)
        
        # add the butons
        self._del_button = QtWidgets.QPushButton("Remove")
        self._del_button.clicked.connect(self._removeDataContainer)
        
        self._export_button = QtWidgets.QPushButton("Export")
        self._export_button.clicked.connect(self._exportDataContainer)
        
        buttons = QtWidgets.QHBoxLayout()
        buttons.addWidget(self._del_button)
        buttons.addWidget(self._export_button)
        
        headerdata["buttons"] = buttons
        
        # the data of the header in the raw file
#        keep = ("comment", "title", "analyzingsoftware", "headerdata")
        keep = ("title")
        skip_info = ("coil_serial_number", "appname")
        for key in datacontainer.header:
            if key == "info":
                for k in datacontainer.header["info"]:
                    if k.lower() in skip_info or str(datacontainer.header["info"][k]) == "":
                        continue
                    else:
                        headerdata[k.replace("_", " ").lower()] = str(datacontainer.header["info"][k])
            elif key == "fileopentime":
                d = str(datacontainer.header[key]).split(",")
                headerdata["file open time"] = " ".join(d[1::])
            elif key == "startupaxis":
                nk = "startup axis "
                for k in datacontainer.header[key]:
                    headerdata[nk + str(k)] = datacontainer.header[key][k]
            elif key == "records" and ("from" in datacontainer.header[key] or "to" in datacontainer.header[key]):
                headerdata["records"] = "from "
                
                if "from" in datacontainer.header[key]:
                    headerdata["records"] += str(datacontainer.header[key]["from"])
                else:
                    headerdata["records"] += "???"
                
                headerdata["records"] += " to "
                    
                if "to" in datacontainer.header[key]:
                    headerdata["records"] += str(datacontainer.header[key]["to"])
                else:
                    headerdata["records"] += "???"
            elif key in keep:
                headerdata[key] = datacontainer.header[key]
        
        # creating list of files
        collapse_layout = QtWidgets.QGridLayout()
        collapse_layout.setContentsMargins(10, 10, 10, 10)
                
        # add the data to the GUI
        for i, key in enumerate(headerdata):
            if key == "buttons":
                index = 0
                collapse_layout.addItem(headerdata[key], index, 0, 1, 2, QtCore.Qt.AlignTop)
                continue
            
            # key label
            key_label = QtWidgets.QLabel(str(key) + ":".strip()) 
            key_label.setWordWrap(True);
            
            # value label
            value_label = QtWidgets.QLabel(str(headerdata[key]).strip())
            value_label.setWordWrap(True);
            
            # add the labels
            if key == "title":
                # title is always the first
                index = 1
            elif key == "number of datapoints":
                # number of datapoints is always the second
                index = 2
                key_label.setObjectName("border")
                value_label.setObjectName("border")
            else:
                # add the other values just in the order they are coming, keep
                # the index=counter, set the names to make them having borders
                index = i + 3
                
                key_label.setObjectName("border")
                value_label.setObjectName("border")
                
            collapse_layout.addWidget(key_label, index, 0, QtCore.Qt.AlignTop)
            collapse_layout.addWidget(value_label, index, 1, QtCore.Qt.AlignTop)
#            file_list.setRowStretch(0, counter)
        
        bc = "#828790"
        
        # create collapsable widget
        collapsable = QtWidgets.QWidget()
        collapsable.setLayout(collapse_layout)
        collapsable.setObjectName("collapsable_widget")
        collapsable.setStyleSheet(
                "QLabel#border{border-top: 1px solid #dddddd;}" + 
                "#collapsable_widget{" + 
                    "border: 1px solid " + bc + "; " + 
                    "background: #ffffff; " + 
                "}"
                );
        
        super(DataContainerWidget, self).__init__(collapsable, view)
        
        name = datacontainer.createName(False)
        
        self.setButtonText(name)
        
        # add controller
        self._controller = None
        if isinstance(controller, Controller.Controller):
            self._controller = controller
        
        # set warnings
        if (len(warnings) > 0 and self._controller != None and 
            isinstance(self._controller, Controller.Controller)):
            self._controller.error("Some loading routine for loading file '{0}' " + 
                                   "caused some problems".format(datacontainer.filepath),
                                   Controller.Constants.NOTICE,
                                   warnings)
        
        # add the datacontainer
        self._datacontainer = datacontainer
        
        # add the view
        self._view = view
    
    def _extractEnvironmentVariableToHeader(self, headerdata, datapoint, variable_name, target_name = None):
        """Extract the environment variable with the name variable_name from the 
        given datapoint. The headerdata will get a new index with the targe_name
        which will contain the environment variable if it exists.
        
        The variable_name can be a tuple too, in this case the average of the 
        corresponding variable names will be used instead. Also the target_name
        **has to be given** in this case.
        
        Note that this function **always** adds a tuple to the headerdata which 
        contains the value in the first index and the standard deviation in the 
        second index.
        
        Additionally this function sets the headerdata[0] to the unit of the 
        environmnent variable if the headerdata[0] is an empty string ("")
        
        Parameters
        ---------
            headerdata : dict
                The current headerdata
            datapoint : DataPoint
                The datapoin which holds the envirommnent variables
            variable_name : String or tuple of strings
                The name of the environment variable in the datapoint
            target_name : String, optinal
                The name of the environmnent variable in the headerdata, if nothing
                is given the variable_name will be used instead
        Returns
        -------
            dict
                The new headerdata
        """
        
        # check if target name is given
        if not isinstance(target_name, str) or len(target_name) == 0:
            target_name = variable_name
        
        if not isinstance(target_name, str):
            raise TypeError("The target_name cannot be empty if the variable_name " + 
                            "is not a string")
            
        # save the length, prepare array for saving the enviromnent variables
        env_len = datapoint.getEnvironmentVariablesCount()
        env_vars = []
        
        # prepare headerdata
        if target_name not in headerdata or not isinstance(headerdata[target_name], list):
            headerdata[target_name] = []
            
        if my_utilities.is_iterable(variable_name):
            # variable names is a tuple, go through all names and save the 
            # variables
            for name in variable_name:
                for i in range(0, env_len):
                    # go through all environmnent variables of the data point
                    v = datapoint.getEnvironmentVariable(name, i)
                    if v != False:
                        env_vars.append(v)
        else:
            for i in range(0, env_len):
                # go through all environmnent variables of the data point
                v = datapoint.getEnvironmentVariable(variable_name, i)
                if v != False:
                    env_vars.append(v)
        
        # check if the datapoint has (valid) environment variables
        if len(env_vars) <= 0:
            raise ValueError("Could not find datapoint environmnent variable '{0}'"
                     .format(variable_name))
        else:
            # add unit if it does not exist
            unit = re.search("[\D]*$", env_vars[0])
            try:
                if (headerdata[target_name][0] == "" and unit.group(0) and 
                    len(str(unit.group(0)).strip()) > 0):
                    headerdata[target_name][0] = str(unit.group(0)).strip()
            except IndexError:
                unit = None
                
            # add the mean value of all environment variables and the standard
            # deviation
            headerdata[target_name].append(my_utilities.mean_std(map(
                    lambda x: my_utilities.force_float(x), env_vars)))
            
        return headerdata
    
    def _checkForRange(self, data, threshold, minimum_count, reverse_mins = False):
        """Check if the given data is a "range" or a value with a diviation.
        This meas that the highest `minimum_count`and the lowest `minimum_count`
        values will be subtracted from eachother. If each of the results is 
        greater or equal to threshold this will return true, otherwise false
        will be returned. The lowest number will be subtracted from the highest,
        the second lowest from the second highest and so on. If you want to 
        reverse the mimimums use the reverse_mins=True parameter
        Parameters
        ----------
            data : list
                The data
            threshold : float
                The threshold to return true, each subtraction has to be greater
                or equal to this value to count as a range
            mimimum_count : int
                The mimimum count of subtractions that should be greater or equal
                to the threshold to return true
            reverse_mins : boolean, optional
                Whether to reverse the mimimums so the highest number will be
                subtracted from the mimimum_count-th lowest numnber, default: False
        Returns
        -------
            boolean
                Whether to treat the data as a range or as a value with diviation
        """
        
        # maximum and minimum lists
        maxs = []
        mins = []
        
        # go through data
        for d in data:
            # check if element is greater than the lowest element (maxs[-1])
            if len(maxs) < minimum_count or d > maxs[-1]:
                c = 0
                ins = False
                # find the place where to put the element
                for m in maxs:
                    if d > m:
                        ins = True
                        maxs = maxs[0:c] + [d] + maxs[c:minimum_count-1]
                        break
                    c += 1
                
                # if the list is not full now add it to the end
                if ins == False:
                    maxs.append(d)
            
            # same procedure for the mimimum
            if len(mins) < 5 or d < mins[-1]:
                c = 0
                ins = False
                for m in mins:
                    if d < m:
                        ins = True
                        mins = mins[0:c] + [d] + mins[c:minimum_count-1]
                        break
                    c += 1
                
                if ins == False:
                    if reverse_mins:
                        mins.insert(0, d)
                    else:
                        mins.append(d)
        
        # create the differences
        diffs = list(map(lambda x, y: x - y, maxs, mins))
        
        # if the lowest element is greater than the threshold all elements are
        # greater so this should return true
        if min(diffs) >= threshold:
            return True
        else:
            return False
    
    def getDataContainer(self):
        """Get the DataContainer which is the data of this widget"""
        return self._datacontainer
    
    def _removeDataContainer(self):
        """Remove this datacontainer widget from the parent view"""
        confirm = QtWidgets.QMessageBox(self._view)
        confirm.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        confirm.setIcon(QtWidgets.QMessageBox.Warning)
        confirm.setText("Are you sure you want to remove {} from this list?".format(
                os.path.basename(self._datacontainer.filepath)))
        
        ret = confirm.exec()
        
        if ret == QtWidgets.QMessageBox.Yes:
            self._view.removeDataContainerWidget(self)
    
    def _exportDataContainer(self):
        """Show the export dialog"""
        
        self._view.actionTool("export", self._datacontainer, "export", True)
    
    def showControls(self, show):
        """Show or hide the control buttons, the control buttons are the export 
        and the delete buttons
        Parameters
        ----------
            show : boolean
                Whether to show or hide the buttons
        """
        
        if show == False:
            self._export_button.setVisible(False)
            self._del_button.setVisible(False)
        else:
            self._export_button.setVisible(True)
            self._del_button.setVisible(True)
    
    def sizeHint(self):
        if self.getState() == View.QCollapsableWidget.QCollapsableWidget.COLLAPSED:
            h = 15
        else:
            h = 600
            
        return QtCore.QSize(250, h)