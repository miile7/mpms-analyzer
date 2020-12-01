# -*- coding: utf-8 -*-
"""
Created on Mon Oct 16 13:47:23 2017

@author: Maximilian Seidler
"""

from PyQt5 import QtCore
import datetime
import warnings
import time
import copy
import os

import Constants
import DataHandling.DataPoint
import DataHandling.PlotData
import my_utilities

class DataContainer(QtCore.QObject):
    MAGNETIZATION = "magnetization"
    MAGNETIZATION_ERROR = "magnetization error"
    TEMPERATURE = "avg. temp"
    HIGH_TEMPERATURE = "high temp"
    LOW_TEMPERATURE = "low temp"
    FIELD = "field"
    HIGH_FIELD = "high field"
    LOW_FIELD = "low field"
    DRIFT = "drift"
    SLOPE = "slope"
    SQUID_RANGE = "squid range"
    FIXED_AMPLITUDE = "amp fixed"
    FREE_AMPLITUDE = "amp free"
    FREE_FIT = "free fit"
    FREE_FIT_ERROR = "free fit error"
    
    ORIGINAL_DATA = "original data"
    BACKGROUND_DATA = "background data"
    
    loadingStart = QtCore.pyqtSignal(int, str, str)
    loadingProgress = QtCore.pyqtSignal(int, str, str)
    loadingEnd = QtCore.pyqtSignal(bool, str, str)
    
    def __init__(self, filepath, dat_filepath = None):
        """Initialize the DataReader.
        
        Parameters
        ----------
            filepath : string
                The absolute path of the raw file where the data comes from
        """
        super(DataContainer, self).__init__()
        
        # create header data
        self.header = {}
        
        # create data points
        self.datapoints = []
        
        # the names for the values
        self.datanames = []
        
        # the units for the values
        self.dataunits = []
        
        # save filepath
        self._filepath = filepath
        
        # save filepath for *.dat file
        self._dat_filepath = dat_filepath
        
        # save some custom data
        self._data = {}
        
        self.attributes = set()
        
        self._formats = []
        self._mpl_settings = None
        self.measurement_variable = None
        
        self.removed_background = False
        self.fitting_not_possible = False
    
    @property
    def filepath(self):
        """Get the filepath in which the data has been stored"""
        return self._filepath

    @filepath.setter
    def filepath(self, filepath):
        """Prevent from chaning the filepath, this will do nothing"""
        self._filepath = filepath
            
    def readFileData(self, replace_values = None):
        """Read the data of the file to the internal buffer. The replace_values
        can be a list with a dict in each index, this dict will replace the 
        environment variables.
        Note that the DataContainer contains 2 times the datapoints as the normal
        SQUID program, the up- and down-sweep are divided in two datapoints
        
        Raises
        ------
            IOError
            
        Warnings
        --------
            UserWarning
            
        Parameters
        ----------
            replace_values : list of dicts, optional
                The environmnet variables for each datapoint index to replace
        """
        
        # check if there are custom values to replace
        if replace_values != None and isinstance(replace_values, tuple):
            replace_values = list(replace_values)
        elif replace_values == None or (not isinstance(replace_values, dict) and 
                                        not isinstance(replace_values, list)):
            replace_values = []
        
        replace_squid_length = -1
        if self._dat_filepath != None and isinstance(self._dat_filepath, str):
            # find the squid ranges (which are index 13) in the dat file to replace
            # them
            replace_squid_ranges = self.readDatFileData(13)
            
            replace_squid_length = len(replace_squid_ranges)
            
            # add the squid ranges to the replace list
            for index in range(0, 2 * replace_squid_length):
                squid_range = replace_squid_ranges[int(index/2)]
                
                if index >= len(replace_values):
                    replace_values.append({"squid range": squid_range})
                elif isinstance(replace_values[index], dict):
                    replace_values[index]["squid range"] = squid_range
                else:
                    replace_values[index]["squid range"] = {"squid range": squid_range}
            
            self.header["dat file"] =  self._dat_filepath
            self.header["dat file datapoints"] = "{0} points ({0} Up, {0} Down)".format(replace_squid_length)
        
        try:
            # open files
            file = open(self._filepath, "r")
            
            # check if file could have been loaded
            if file != None:
                # set mode, 1 = header, 2 = data
                mode = None
                
                # save linenumber for debuggin purposes
                linenumber = 0
                
                lines = file.readlines()
                
                # emit signal for start
                self.loadingStart.emit(len(lines), "loading", self._filepath)
                
                # go through each line of the data
                for line in lines:
                    # refresh line number
                    linenumber += 1
                    
                    # remove whitespace
                    line = line.strip()
                    
                    # wait for header/data
                    if line.lower() == "[header]":
                        # set mode to header, data will now be applied to header,
                        # jump to next run
                        mode = 1
                        continue
                    elif line.lower() == "[data]":
                        # set mode to data
                        mode = 2
                        continue
                    
                    # analyzing header
                    if mode == 1:
                        # line starts with ; => comment
                        if line[0] == ";":
                            # create "comment" section or add a new line
                            if "comment" not in self.header:
                                self.header["comment"] = ""
                            else:
                                self.header["comment"] += "\n"
                            
                            if line[:2] == "; ":
                                # remove the first two characters (which are ";" and space)
                                self.header["comment"] += line[2::]
                            else:
                                # remove only the first character
                                self.header["comment"] += line[1::]
                        else:
                            # split the data by ","
                            line = line.split(",")
                            
                            # detect the key of the information
                            key = line[0].lower()
                            
                            # save the length
                            length = len(line)
                            
                            if key == "info" and length > 1:
                                # header line contains some general information
                                if "info" not in self.header:
                                    self.header["info"] = {}
                                
                                # find name of info, info name is last element in line (always)
                                # remaining line will be treated as value of the info
                                self.header["info"][line[-1]] = ", ".join(line[1:-1])
                            elif key == "title" and length > 1:
                                # header line contains the title
                                self.header["title"] = ", ".join(line[1:])
                            elif key == "fileopentime" and length > 1:
                                # the time when the file was opened
                                self.header["fileopentime"] = ", ".join(line[1:])
                            elif key == "byapp" and length > 1:
                                # the software that was used to create the file
                                self.header["analyzingsoftware"] = ", ".join(line[1:])
                            elif key == "startupaxis" and length >= 3:
                                # the startup of (all) the axis
                                if "startupaxis" not in self.header:
                                    self.header["startupaxis"] = {}
                                
                                if line[1] not in self.header["startupaxis"]:
                                    self.header["startupaxis"][line[1]] = []
                                    
                                self.header["startupaxis"][line[1]].append(",".join(line[2:]))
                            elif key == "records" and length >= 4:
                                # the software that was used to create the file
                                if "records" not in self.header:
                                    self.header["records"] = {}
                                
                                self.header["records"]["from"] = line[2]
                                self.header["records"]["to"] = line[3]
                            else:
                                key = line[0].lower()
                                
                                # unknown data, just save it
                                if key in self.header:
                                    if not isinstance(self.header[key], list):
                                        self.header[key] = [self.header[key]]
                                    
                                    self.header[key].append(", ".join(line[1:]))
                                else:
                                    self.header[key] = ", ".join(line[1:])
                                
                    # analyzing data
                    elif mode == 2 or mode == 3:
                        # a comment with the environement variables, save them to the datapoint
                        if line[0] == ";":
                            # squid changes direction (up/down), create new datapoint
                            dp = self._getCurrentDataPoint(True)
                            
                            # check out the environement variables (like temperature...)
                            variables = line[1:].split(";")
                            variables_dict = {}
                            
                            # go through each variable, split them by =, the first
                            # param is the name, the second is the value
                            for var in variables:
                                elements = var.split("=")
                                
                                # check if splitting was successfully, save them in
                                # the datapoint
                                if len(elements) >= 2:
                                    variables_dict[str(elements[0]).strip()] = str(elements[1]).strip()
                            
                            # the current datapoint index
                            dp_index = len(self.datapoints) - 1
                            
                            if isinstance(replace_values, dict):
                                variables_dict.update(replace_values)
                            elif (isinstance(replace_values, list) and dp_index < len(replace_values) and 
                                  isinstance(replace_values[dp_index], dict)):
                                variables_dict.update(replace_values[dp_index])
                            
                            # append the new datapoint
                            dp.addEnvironmentVariables(variables_dict, linenumber)
                        elif self._getCurrentDataPoint(False) != None:
                            # get the current data point
                            dp = self._getCurrentDataPoint(False)
                            
                            # reached some actual data, the format is:
                            # data[0]: comment
                            # data[1]: timestamp
                            # data[2]: raw position in [mm]
                            # data[3]: raw voltage in [V]
                            # data[4]: processed voltage in [V]
                            # data[5]: fixed c fit in [V]
                            # data[6]: free c fit in [v]
                            data = line.split(",")
                            
                            if len(data) > 0:
                                # reached some data
                                if len(data) >= 7 and data[5] != "" and data[6] != "":
                                    # the current line is a fit line (last
                                    # two rows are defined)
                                    dp.addFixedFit(data[Constants.RAW_FILE_OFFSET_RAW_POSITION], 
                                                   data[Constants.RAW_FILE_OFFSET_FIXED_C_FIT], 
                                                   linenumber, 
                                                   data[Constants.RAW_FILE_OFFSET_TIMESTAMP], 
                                                   data[Constants.RAW_FILE_OFFSET_COMMENT])
                                    dp.addFreeFit(data[Constants.RAW_FILE_OFFSET_RAW_POSITION], 
                                                  data[Constants.RAW_FILE_OFFSET_FREE_C_FIT], 
                                                  linenumber, 
                                                  data[Constants.RAW_FILE_OFFSET_TIMESTAMP], 
                                                  data[Constants.RAW_FILE_OFFSET_COMMENT])
                                    
                                    # save current mode, currently reading
                                    # the fit, after the fit the next data
                                    # point is starting
                                    mode = 3
                                elif (len(data) >= Constants.RAW_FILE_OFFSET_RAW_VOLTAGE + 1 and 
                                      data[Constants.RAW_FILE_OFFSET_RAW_VOLTAGE] != ""):
                                    # the current line contains at least the
                                    # raw voltage
                                    processed_voltage = None
                                    
                                    if len(data) >= Constants.RAW_FILE_OFFSET_PROCESSED_VOLTAGE + 1:
                                        processed_voltage = data[Constants.RAW_FILE_OFFSET_PROCESSED_VOLTAGE]
                                    
                                    dp.addDataRow(data[Constants.RAW_FILE_OFFSET_RAW_POSITION], 
                                                  data[Constants.RAW_FILE_OFFSET_RAW_VOLTAGE], 
                                                  processed_voltage,
                                                  linenumber,
                                                  data[Constants.RAW_FILE_OFFSET_TIMESTAMP], 
                                                  data[Constants.RAW_FILE_OFFSET_COMMENT])
                                
                                    mode = 2
                                else:
                                    # data objects length is too short
                                    warnings.warn(("Data of line {} has length of {} " + 
                                                "chunks which could not be " + 
                                                "interpreted, this dataset will be " + 
                                                "skipped").format(linenumber, 
                                                                     str(len(data))))
                                    dp.addEmptyDataRow()
                                    
                            else:
                                # data object is empty
                                warnings.warn("Data could not be parsed (is empty)" + 
                                              " in line {}, this dataset will be " + 
                                              "ignored".format(linenumber))
                                dp.addEmptyDataRow()
                        else:
                            data = line.split(",")
                            
                            if len(line) > 0:
                                # save the first line as the names
                                self.datanames = []
                                self.dataunits = []
                                
                                if len(self.datanames) <= 0 and len(self.dataunits) <= 0:
                                    for name in data:
                                        name = name.rsplit(" ", 1)
                                        self.datanames.append(name[0])
                                        
                                        if len(name) > 1:
                                            self.dataunits.append(
                                                    name[1].replace("(", "").replace(")", "").
                                                    replace("[", "").replace("]", ""))
                                        else:
                                            self.dataunits.append("")
                                
                    # emit signal for progress, only emit every 5000 lines, otherwise
                    # this is too fast
                    if linenumber % 5000 == 0:
                        self.loadingProgress.emit(linenumber, "loading", self._filepath)
            else:
                # file could not be opened, file == None
                raise IOError("File {0} could not be opened".format(self._filepath))
                                
            # close file connection
            file.close()
            
            if replace_squid_length >= 0 and 2 * replace_squid_length < len(self.datapoints):
                warnings.warn(("The *.dat file has been read successfully but the " + 
                              "it contains {d} datapoints whilst the raw file (*.rw.dat) " + 
                              "file holds {r} datapoints ({r} up and {r} down sweeps).").format(
                                      d=replace_squid_length, r=len(self.datapoints) // 2))
            
            # emit signal for end of loading
            self.loadingEnd.emit(True, "loading", self._filepath)
        except IOError:
            raise
    
    def _getCurrentDataPoint(self, force_new = None):
        """Return the currently active (or a new) data point. If there is no
        active point or the force_new=True a new data point will be returned
        and added to the internal collection. If there is no datapoint and 
        the force_new is False this will return None
        
        Parameters
        ----------
            force_new : boolean, optional
                Whether to force a new data point or to return the currently
                active one
        
        Returns
        -------
            DataPoint or None
                The current or a new data point object
        """
        
        if force_new or (len(self.datapoints) <= 0 and force_new != False):
            # create new datapoint if forced or if there is no datapoint and
            # creating is not prevented
            dp = DataHandling.DataPoint.DataPoint(self)
            self.datapoints.append(dp)
        elif len(self.datapoints) > 0:
            # return the current datapoint if it exists
            dp = self.datapoints[len(self.datapoints) - 1]
        else:
            return None
         
        if len(dp.column_names) <= 0 and len(self.datanames) > 0:
            dp.column_names = self.datanames
        if len(dp.column_units) <= 0 and len(self.dataunits) > 0:
            dp.column_units = self.dataunits
            
        return dp;
    
    def readDatFileData(self, data_index = None):
        """Read the *.dat files contents. If you specify a data_index only the
        values of this index will be returned
        Note:
            This returns the half number of datapoints, this returns one datapoint
            value for an up and down sweep whilst the DataContainer contains
            one datapoint for an up and one datapoint for a down sweep
            
        Raises
        ------
            ValueError, if the dat file is not defined
            IOError, if the file could not be read
            
        Parameters
        ----------
            data_index : int or list of ints, optional
                The index/indices of the data to return
                
        Returns
        -------
            list of anything or list of lists of anything
                The values of the *.dat file specified by the data_index
        """
        
        # prepare the data to return
        return_data = []
        
        if self._dat_filepath == None or not isinstance(self._dat_filepath, str):
            raise ValueError("The *.dat filepath is not specified")
        
        try:
            # open files
            file = open(self._dat_filepath, "r")
            
            # check if file could have been loaded
            if file != None:
                # the data line when to read data
                read_data_line = -1
                
                # save linenumber for debuggin purposes
                linenumber = 0
                
                # read the lines
                lines = file.readlines()
                
                # go through each line of the data
                for line in lines:
                    # refresh line number
                    linenumber += 1
                    
                    # remove whitespace
                    line = line.strip()
                    
                    # wait until data is acutally there
                    if line.lower() == "[data]":
                        # skip next line too, this holds the names of the data
                        read_data_line = linenumber + 2
                        continue
                    
                    # read the data
                    if read_data_line >= 0 and linenumber >= read_data_line:
                        # split the line in a list which contains the values
                        data = line.split(",")
                        
                        if (data_index != None and my_utilities.is_numeric(data_index) and 
                            data_index >= 0 and data_index < len(data)):
                            # data_index is numeric, only add the one index value to
                            # the return list
                            return_data.append(data[data_index])
                        elif data_index != None and isinstance(data_index, (tuple, list)):
                            # data_index is a tuple/list, add all the indices in the
                            # tuple to the list
                            rd = []
                            for i in data_index:
                                if (my_utilities.is_numeric(i) and i >= 0 and i < len(data)):
                                    rd.append(data[i])
                            
                            return_data.append(rd)
                        else:
                            # data_index is anything, just add the complete line
                            return_data.append(data)
            
            # close the file again
            file.close()
        except IOError:
            raise
            
        # return the data
        return return_data
    
    def fitDataPoints(self):
        """Fit the datapoints"""
        
        self.loadingStart.emit(len(self.datapoints), "fitting", self._filepath)
        
        exceptions = []
        
        for i in range(0, len(self.datapoints)):
            datapoint = self.datapoints[i]
            try:
                datapoint.execFit()
            except RuntimeError as e:
                exceptions.append((i, e))
                self.fitting_not_possible = True
                
            self.loadingProgress.emit(i, "fitting", self._filepath)
            
        self.loadingEnd.emit(len(exceptions) == 0, "fitting", self._filepath)
        
        if len(exceptions) > 0:
            exception_string = ""
            for index, exception in exceptions:
                exception_string += str(exception) + " (in datapoint #{})\n".format(index)
                
            raise Exception(exception_string)
            
    def getPlotData(self, x_axis = TEMPERATURE, y_axis = MAGNETIZATION, index_list = None, apply_formats = True):
        """Get the data for plotting the y_axis data over the x_axis data. This
        will return a tuple containing the x axis values in index 0, the y axis
        data will be in index 1. If the data could not be plotted over eachother
        None will be returned
        
        Raises
        ------
            TypeError
                If the min/max parameters are not the correct type
                
        Parameters
        ---------
            x_axis : string
                The name of the data which should be used for the x axis
            y_axis : string
                The name of the data which should be used for the y axis
            index_list : list or tuple, optional
                The list of indices that are should be included in the plot data,
                if nothing given all of them will be included, default: None
                
        Returns
        -------
            PlotData
                The data containing the list for the x axis data and the y axis
                data
        """
        
        if not isinstance(index_list, list) and not isinstance(index_list, tuple):
            index_list = None
            
        if apply_formats and len(self._formats) > 0:
            r = []
            
            if index_list == None:
                index_list = []
            
            for name, indices, settings in self._formats:
                plot_data = self.getPlotData(
                        x_axis, 
                        y_axis, 
                        indices + index_list,
                        False)
                
                plot_data.mpl_settings = settings
                plot_data.title = name
                r.append(plot_data)
            
            return r
        
        xdata = []
        ydata = []
        xerrors = []
        yerrors = []
        sorting = []
        x_unit = ""
        y_unit = ""
        indices = []
        
        try:
            for index, datapoint in enumerate(self.datapoints):
                if datapoint.disabled:
                    continue
                
                if index_list == None or index in index_list:
                    x_point = self._getPlotDataFromDataPoint(datapoint, x_axis)
                    y_point = self._getPlotDataFromDataPoint(datapoint, y_axis)
                    
                    if isinstance(x_point, (list, tuple)) and isinstance(y_point, (list, tuple)):
                        x, x_error, x_unit_temp = x_point
                        y, y_error, y_unit_temp = y_point
                    
                        if x_unit != "" and x_unit != x_unit_temp:
                            warnings.warn(("The changed from {} to {} in datacontainer {} " + 
                                  "in datapoint #{}").format(x_unit, x_unit_temp, os.path.basename(self.filepath), index))
                        
                        if y_unit != "" and y_unit != y_unit_temp:
                            warnings.warn(("The changed from {} to {} in datacontainer {} " + 
                                  "in datapoint #{}").format(y_unit, y_unit_temp, os.path.basename(self.filepath), index))
                        
                        if x_unit == "":
                            x_unit = x_unit_temp
                        if y_unit == "":
                            y_unit = y_unit_temp
                        
                        if x != None and y != None:
                            xdata.append(float(x))
                            ydata.append(float(y))
                            xerrors.append(float(x_error))
                            yerrors.append(float(y_error))
                            indices.append(index)
                            sorting.append(self._getPlotDataFromDataPoint(datapoint, DataHandling.DataPoint.DataPoint.TIMESTAMP))
            
            title = self.createName(True)
            
            return DataHandling.PlotData.PlotData(x=xdata, 
                                                      y=ydata, 
                                                      x_errors=xerrors, 
                                                      y_errors=yerrors, 
                                                      x_label=self.getNameForAxis(x_axis), 
                                                      y_label=self.getNameForAxis(y_axis), 
                                                      x_unit=x_unit,
                                                      y_unit=y_unit,
                                                      x_axis=x_axis,
                                                      y_axis=y_axis,
                                                      title=title,
                                                      origin=self, 
                                                      sorting_list=sorting,
                                                      indices_list=indices,
                                                      formats=self._formats)
                    
        except TypeError:
            raise
    
    def _getPlotDataFromDataPoint(self, datapoint, axis):
        """Get the data for the given for the given axis form the given datapoint
        
        Parameters
        ----------
            datapoint : DataPoint
                The data point from which to get the data
            axis : String
                The name of the data to get from the point
                
        Returns
        -------
            tuple
                A tuple where the 0 index contains the mean value of the axis
                value, the index 1 contains the standard deviation, index 2 is the
                unit of the data or None if an error occurred
        """
        
        datapoint_values = [DataHandling.DataPoint.DataPoint.LINENUMBER, 
                            DataHandling.DataPoint.DataPoint.COMMENT, 
                            DataHandling.DataPoint.DataPoint.TIMESTAMP, 
                            DataHandling.DataPoint.DataPoint.RAW_POSITION, 
                            DataHandling.DataPoint.DataPoint.RAW_VOLTAGE, 
                            DataHandling.DataPoint.DataPoint.PROCESSED_VOLTAGE, 
                            DataHandling.DataPoint.DataPoint.FIXED_FIT_VOLTAGE, 
                            DataHandling.DataPoint.DataPoint.FREE_FIT_VOLTAGE]
        
        unit = ""
        
        if axis == DataContainer.MAGNETIZATION:
            # get the magnetization fit results
            fit = datapoint.getFitResults()
            if isinstance(fit, (list, tuple)) and len(fit) >= 2:
                mean = fit[0]
                error = fit[1]
                unit = "emu"
            else:
                return None
        elif axis == DataContainer.MAGNETIZATION_ERROR:
            # get the magnetization fit results
            fit = datapoint.getFitResults()
            if isinstance(fit, (list, tuple)) and len(fit) >= 2:
                mean = fit[1]
                error = 0
                unit = "emu"
            else:
                return None
        elif axis == DataContainer.FREE_FIT:
            fit = datapoint.getRawFitResults()
            if isinstance(fit, (list, tuple)) and len(fit) >= 2:
                mean = fit[0][0]
                error = fit[1][0]
                unit = "V"
            else:
                return None
        elif axis == DataContainer.FREE_FIT_ERROR:
            fit = datapoint.getRawFitResults()
            if isinstance(fit, (list, tuple)) and len(fit) >= 2:
                mean = fit[1][0]
                error = 0
                unit = "V"
            else:
                return None
        elif axis in datapoint_values:
            # data is some datapoint data, get the plot data over the timestamp
            # because every value has a timestamp, just use the x data for returning
            data = datapoint.getPlotData(axis, DataHandling.DataPoint.DataPoint.TIMESTAMP)
            
            # return the mean and standard deviation
            mean, error = my_utilities.mean_std(data[0])
            unit = data.x_unit
        else:
            r = datapoint.getEnvironmentVariableAvg(axis)
            unit = datapoint.getEnvironmentVariablesUnit(axis)
            if r != False:
                mean, error = r
            else: 
#                    print("DataContainer._getPlotDataFromDatapoint(): datapoint.getEnvironmentVariableAvg() " + 
#                          "returned {} for axis {} in datapoint {}".format(r, axis, datapoint.index))
                return None
        try:
            return float(mean), float(error), unit
        except ValueError:
            raise
            return None
        
    def getNameForAxis(self, axis):
        """Get the name for the given axis
        
        Parameters
        ----------
            axis : String
                The axis
                
        Returns
        -------
            String
                The name how to display the axis
        """
        
        if axis in Constants.ENVIRONMENT_VARIABLE_NAMES:
            return Constants.ENVIRONMENT_VARIABLE_NAMES[axis]
        else:
            return axis
        
    def findDataPointsInRange(self, axis, low, high, include_index = False):
        """Find a datapoint depending on the values it holds. The values are
        detected by the DataContainer._getPlotDataFromDataPoint() function, this 
        means that all the datapoint values will be the average values!
        This will return a list of datapoints that have the axis value between
        the low and the high parameter. The axis parameter can either be one
        of the DataContainer constants or one of the DataPoint constants.
        
        Parameters
        ----------
            axis : String
                The value to check
            low : float
                The lower bounding of the range where the datapoints value should
                be in
            high : float
                The upper bounding of the range where the datapoints value should
                be in
            include_index : boolean, optional
                Whether to return a list of tuples (instead of the list of datapoints)
                which hold the DataPoint at index 0 and the index at index 1
                
        Returns
        -------
            list of Datapoints
                The datapoints or an empty list
        """
        datapoints = []
        
        try:
            low = my_utilities.force_float(low)
        except ValueError:
            raise
        
        try:
            high = my_utilities.force_float(high)
        except ValueError:
            raise
        
        index = -1
        for datapoint in self.datapoints:
            index += 1
            value = self._getPlotDataFromDataPoint(datapoint, axis)
            
            if value == None:
                continue
            
            if isinstance(value, tuple) or isinstance(value, list):
                value = value[0]
            
            try:
                value = my_utilities.force_float(value)
            except ValueError:
                continue
            
            if value >= low and value <= high:
                if include_index:
                    datapoint = (datapoint, index)
                datapoints.append(datapoint)
                
        return datapoints
    
    def getDataForExport(self, axis):
        """Get the data for the csv export. This will **not** sort the data, the
        data will always be returned in the order of the datapoints. This function
        returns the data as an array and the unit if given
        Parameters
        ---------
            axis : string
                The name of the data which should be returned
                
        Returns
        -------
            list
                A list of floats (if the value is invalid None will be returned
                for each invalid point)
            String
                The unit as a string or an empty String if there is no unit
        """
        
        data = []
        unit = None
        
        for i, datapoint in enumerate(self.datapoints):
            try:
                d = self._getPlotDataFromDataPoint(datapoint, axis)
            except RuntimeError as e:
                print("DataContainer.getDataForExport(): An Exception ocurred " + 
                      "when trying to get the export data for dataponit #{}: ".format(i) + 
                      str(e))
                pass
            
            if isinstance(d, tuple):
                try:
                    data.append(my_utilities.force_float(d[0]))
                except (ValueError, TypeError):
                    data.append(None)
                
                if unit == None and len(d) >= 3 and d[2] != "":
                    unit = d[2]
            else:
                data.append(d)
        
        if unit == None:
            unit = ""
        
        return data, unit
    
    def getDataPointDataForCSVExport(self, axis):
        """Get the data of each datapoint for the csv export. This will **not** 
        sort the data, the data will always be returned in the order of the datapoints. 
        The data of each datapoint will be appended so there will only be one 
        linear list as a return value
        This function returns the data as an array and the unit if given.
        
        Parameters
        ---------
            axis : string
                The name of the data which should be returned
                
        Returns
        -------
            list
                A list of floats (if the value is invalid None will be returned
                for each invalid point)
            String
                The unit as a string or an empty String if there is no unit
        """
        
        data = []
        unit = None
        
        for datapoint in self.datapoints:
            d = datapoint.getPlotData(
                    DataHandling.DataPoint.DataPoint.RAW_POSITION,
                    axis,
                    True)
            
            if isinstance(d, (list, tuple)) and len(d) > 1:
                data = data + d[1]
            else:
                data.append(d)
            
            if unit == None:
                unit = datapoint.getUnitForAxis(axis)
                
        if unit == None:
            unit = ""
        
        return data, unit
    
    def exportCSV(self, csv_filename, column_axis, mode):
        """Save the csv file defined by the user to the csv_filename
        
        Parameters
        ----------
            csv_filename : String
                The file name to save the csv file to
        """
        
        # prepare table and rows
        csv_table = []
        rows = 0
        
        for axis in column_axis:
            column = []
            
            # the axis
            if axis != None:
                name = axis
                
                if name in Constants.ENVIRONMENT_VARIABLE_NAMES:
                    name = Constants.ENVIRONMENT_VARIABLE_NAMES[name]
                else:
                    name = self.datapoints[0].getNameForAxis(name)
                
                # check the current mode and get the data for the mode and for 
                # the axis
                if mode == 0:
                    data, unit = self.getDataForExport(axis)
                elif mode == 1:
                    data, unit = self.getDataPointDataForCSVExport(axis)
                
                # parse the unit
                unit = str(unit)
                
                if unit != "":
                    name += " [" + unit + "]"
                
                # save the name and the data
                column.append(name)
                column = column + data
            
            # add the name and the data, get the new maximum rows count
            csv_table.append(column)
            rows = max(rows, len(column))
        
        # open the file
        csv_file = open(csv_filename, "w")
        
        # the lenght of the header in lines, this will always have this length!
        l = Constants.HEADER_LINE_NUMBER
        # number of lines that explain the header
        f = 4
        csv_file.write("# CSV file created with {} by {} at {} \n".format(
                       Constants.NAME, Constants.COMPANY, time.strftime("%c")))
        csv_file.write("# (Processed) header information of the raw file\n#\n")
        
        # the header information of the raw header
        header = self.header
        
        # format the info to the normal datacontainer header
        if "info" in header and isinstance(header["info"], dict):
            for key in header["info"]:
                header[key] = header["info"][key]
            
            del header["info"]
        
        # print the header (maximum is l lines)
        i = 0
        line = ""
        for key in header:
            value = self.header[key]
            
            if key == "dat file":
                value = os.path.basename(value)
            
            if isinstance(value, list):
                # join the array if the value is an array
                value = ", ".join(value)
            elif isinstance(value, dict):
                # format the dict
                val = ""
                for k in value:
                    val += k + ": " + str(value[k])
                    val += ", "
                value = val
            
            # remove the new lines
            value = str(value).replace("\n", ", ")
            
            # print the data
            line += "# " + key + ": " + value
            
            # check if the current number of lines is smaller than l, if it is
            # write the line, if not add it to the content of the last line
            if i + f + 1 < l:
                csv_file.write(line + "\n")
                line = ""
            else:
                line += ", "
            
            i += 1
        
        # check if the last line is empty or not
        if line != "":
            csv_file.write(line + "\n")
        
        # increase the length if it is too short
        while l - i > f:
            csv_file.write("#\n")
            i += 1
        
        # last header line
        csv_file.write("# (This header is guaranteed to have exactly {} lines! It will never have more or less!)\n".format(l))
        
        # the actual data
        for i in range(0, rows):
            line = ""
            
            # print one row
            for j in range(0, len(csv_table)):
                if isinstance(csv_table, (list, tuple)) and i < len(csv_table[j]):
                    line += str(csv_table[j][i])
                
                line += ";"
            
            # write it to the file
            csv_file.write(line[0:-1] + "\n")
        
        # close the file
        csv_file.close()
        
    def exportCreateMPMSHeader(self, additional_header = None):
        """Creates the MPMS header for the raw export.
        
        Returns
        -------
            String
                The header
        """
        
        if isinstance(additional_header, dict):
            header_dict = additional_header
            header_dict.update(self.header)
        else:
            header_dict = self.header
        
        header = "[Header]\n"
        header += "; MPMS3 Data File (default extension .dat)\n"
        header += "; Created with {}, {}\n".format(Constants.NAME, Constants.COMPANY)
        
        header += "TITLE,"
        if "title" in header_dict and isinstance(header_dict["title"], str):
             header += header_dict["title"]
        else:
            header += ""
        header += "\n"
        
        timestamp = time.time()
        header += "FILEOPENTIME,{},{}\n".format(
                timestamp, 
                datetime.datetime.fromtimestamp(timestamp).strftime('%m/%d/%Y %I:%M %p').lower())
        
        header += "BYAPP,{},{}\n".format(Constants.NAME, Constants.VERSION)
        
        if "info" in header_dict and isinstance(header_dict["info"], dict):
            for key in header_dict["info"]:
                if isinstance(header_dict["info"][key], (list, tuple)):
                    val = ",".join(header_dict["info"][key])
                else:
                    val = str(header_dict["info"][key])
                
                header += "INFO,{},{}\n".format(val, key.upper())
       
        keys = list(header_dict.keys())
        skip_keys = ("comment", "dat file", "dat file datapoints", "title",
                       "info", "records", "fileopentime", "analyzingsoftware")
        
        for k in skip_keys:
            if k in keys:
                keys.remove(k)
        
        for key in keys:
            if key in header_dict:
                if isinstance(header_dict[key], (list, tuple)):
                    for val in header_dict[key]:
                        header += "{},{}\n".format(key.upper(), val)
                elif isinstance(header_dict[key], dict):
                    for sub_key in header_dict[key]:
                        val = header_dict[key][sub_key]
                        
                        if isinstance(val, (list, tuple)):
                            for v in val:
                                header += "{},{},{}\n".format(key.upper(), sub_key.upper(), v)
                        else:
                            header += "{},{},{}\n".format(key.upper(), sub_key.upper(), val)
                else:
                    header += "{},{}\n".format(key.upper(), header_dict[key])
        
        if ("records" in header_dict and
            isinstance(header_dict["records"], dict) and 
            "to" in header_dict["records"] and 
            "from" in header_dict["records"]):
            header += "RECORDS,FROM_TO_RECORDS,{},{}\n".format(
                    header_dict["records"]["from"], 
                    header_dict["records"]["to"])
        
        return header
    
    def exportMPMSRaw(self, raw_filename):
        """Exports the datacontainer to a MPMS raw file.
        
        Paramters
        ---------
            raw_filename : String
                The filepath where to save the file to
        """
        
        # the header
        header = self.exportCreateMPMSHeader()
        
        # the file
        file = open(raw_filename, "w")
        
        file.write(header)
        file.write("[Data]\n")
        
        for i, datapoint in enumerate(self.datapoints):
            if i == 0:
                file.write(",".join(map(lambda x: str(x), datapoint.column_names)) + "\n")
                
            env_vars = datapoint.getEnvironmentVariables()
            
            if isinstance(env_vars, (list, tuple)) and len(env_vars) > 0:
                env_vars = env_vars[0]
            
            if isinstance(env_vars, dict):
                env_vars = zip(env_vars.keys(), env_vars.values())
                env_vars = map(lambda key_val: str(key_val[0]) + " = " + str(key_val[1]), env_vars)
                env_vars = list(env_vars)
            
                file.write(";" + ",".join(env_vars))
            
            data = datapoint.getExportRawData()
            
            for line in data:
                file.write(",".join(map(lambda x: str(x), line)) + "\n")
        
        file.close()
        
    def exportCreateMPMSDatHeader(self):
        """Creates the MPMS header for the dat export.
        
        Returns
        -------
            String
                The header
            list
                The column names
        """
        
        header_dict = {}
        col_names = []
        
        file = open(self._dat_filepath)
        m = 0
        
        for line in file:
            line = line.strip()
            
            if line == "[Header]":
                m = 1
            elif line == "[Data]":
                m = 2
            elif m == 1 and line[0] != ";":
                line = line.split(",")
                
                if line[0] == "INFO":
                    if "info" not in header_dict or not isinstance(header_dict["info"], dict):
                        header_dict["info"] = {}
                    
                    if line[-1].lower() not in header_dict["info"]:
                        header_dict["info"][line[-1]] = ",".join(line[1:-1])
                elif line[0].lower() not in header_dict:
                    header_dict[line[0].lower()] = ",".join(line[1:])
                elif isinstance(header_dict[line[0].lower()], list):
                    header_dict[line[0].lower()].append(",".line[1::])
                else:
                    header_dict[line[0].lower()] = [header_dict[line[0].lower()]].append(",".join(line[1::]))
            elif m == 2:
                col_names = line.split(",")
                m = 3
                break
            
        file.close()
        
        if "info" not in header_dict:
            header_dict["info"] = ""
        if "datatype" not in header_dict:
            header_dict["datatype"] = ""
        if "startupaxis" not in header_dict:
            header_dict["startupaxis"] = ""
        if "fieldgroup" not in header_dict:
            header_dict["fieldgroup"] = ""
        if "startgroup" not in header_dict:
            header_dict["startgroup"] = ""
        
        header = self.exportCreateMPMSHeader(header_dict)
        
        return header, col_names
    
    def exportMPMSDat(self, dat_filename):
        """Exports the datacontainer to a MPMS dat file
        
        Paramters
        ---------
            dat_filepath : String
                The filepath where to save the file to
        """
        
        # get data to fill all the lines that are not known
        original_data = self.readDatFileData()
        header, column_names = self.exportCreateMPMSDatHeader()
        
        # the file
        file = open(dat_filename, "w")
        
        file.write(header)
        file.write("[Data]\n")
        file.write(",".join(map(lambda x: str(x), column_names)) + "\n")
        
        for i in range(0, len(self.datapoints), 2):
            target_i = int(i / 2)
            dp1 = self.datapoints[i]
            if i < len(self.datapoints):
                dp2 = self.datapoints[i + 1]
            else:
                dp2 = None
            
            fit_results = dp1.getRawFitResults()
            center = -1
            center_err = -1
            if fit_results != None:
                center = fit_results[0][3]
                center_err = fit_results[1][3]
                
            if isinstance(dp2, DataHandling.DataContainer.DataContainer):
                fit_results2 = dp2.getRawFitResults()
                if fit_results2 != None:
                    center2 = fit_results2[0][3]
                    center = my_utilities.mean_std((center, center2))
                    center = center[0]
                    
                    center_err2 = fit_results[1][3]
                    center_err = my_utilities.mean_std((center_err, center_err2))
                    center_err = center_err[0]
            
            scan_length, unit = dp1.getScanLength()
            if isinstance(dp2, DataHandling.DataContainer.DataContainer):
                scan_length2, unit = dp2.getScanLength()
                scan_length = my_utilities.mean_std((scan_length, scan_length2))
                scan_length = scan_length[0]
            
            scan_time, unit = dp1.getScanTime()
            if isinstance(dp2, DataHandling.DataContainer.DataContainer):
                scan_time2, unit = dp2.getScanTime()
                scan_time = my_utilities.mean_std((scan_time, scan_time2))
                scan_time = scan_time[0]
            
            number_of_dp = len(dp1._data_rows)
            if isinstance(dp2, DataHandling.DataContainer.DataContainer):
                number_of_dp2 = len(dp2._data_rows)
                number_of_dp = my_utilities.mean_std((number_of_dp, number_of_dp2))
                number_of_dp = number_of_dp[0]
                
            data = ([original_data[target_i][0],
                    self._exportGetAverage(DataHandling.DataPoint.DataPoint.TIMESTAMP, dp1, dp2),
                    self._exportGetAverage(DataHandling.DataContainer.DataContainer.TEMPERATURE, dp1, dp2),
                    self._exportGetAverage(DataHandling.DataContainer.DataContainer.FIELD, dp1, dp2)] + 
                    original_data[target_i][4:13] + 
                    [self._exportGetAverage(DataHandling.DataContainer.DataContainer.SQUID_RANGE, dp1, dp2)] + 
                    original_data[target_i][14:35] + 
                    [self._exportGetAverage(DataHandling.DataContainer.DataContainer.LOW_TEMPERATURE, dp1, dp2),
                    self._exportGetAverage(DataHandling.DataContainer.DataContainer.HIGH_TEMPERATURE, dp1, dp2),
                    self._exportGetAverage(DataHandling.DataContainer.DataContainer.LOW_FIELD, dp1, dp2),
                    self._exportGetAverage(DataHandling.DataContainer.DataContainer.HIGH_FIELD, dp1, dp2)] + 
                    original_data[target_i][39:52] + 
                    [self._exportGetAverage(DataHandling.DataContainer.DataContainer.TEMPERATURE, dp1, dp2),
                    original_data[target_i][53],
                    self._exportGetAverage(DataHandling.DataContainer.DataContainer.TEMPERATURE, dp1, dp2)] +  
                    original_data[target_i][55:59] + 
                    [self._exportGetAverage(DataHandling.DataContainer.DataContainer.MAGNETIZATION, dp1, dp2),
                    self._exportGetAverage(DataHandling.DataContainer.DataContainer.MAGNETIZATION_ERROR, dp1, dp2)] + 
                    original_data[target_i][61:65] + 
                    [scan_length,
                    scan_time,
                    number_of_dp] + 
                    original_data[target_i][68:-1])
            
            file.write(",".join(map(lambda x: str(x), data)) + "\n")
        
        file.close()
    
    def _exportGetAverage(self, axis, dp1, dp2 = None):
        result = None
        
        try:
            d = self._getPlotDataFromDataPoint(dp1, axis)
        except RuntimeError as e:
            pass
        
        if d != None:
            result = d[0]
        
        if isinstance(dp2, DataHandling.DataPoint.DataPoint):
            try:
                d = self._getPlotDataFromDataPoint(dp1, axis)
                if d != None:
                    result = my_utilities.mean_std((d[0], result))
                    result = result[0]
            except RuntimeError as e:
                pass
        
        return result
    
    def clearPlotFormat(self):
        self._formats = []
    
    def addPlotFormat(self, key, indices, plot_settings = None):
        l = len(self._formats)
        
        self._formats.append((key, indices, plot_settings))
        
        return l
    
    def getPlotFormat(self, index):
        if isinstance(index, int) and index > 0 and index < len(self._formats):
            return self._formats[index]
        else:
            return None
    
    def getPlotFormatCount(self):
        return len(self._formats)
    
    def editPlotFormat(self, index, key = None, indices = None, plot_settings = None):
        if isinstance(index, int) and index > 0 and index < len(self._formats):
            plot_format = list(self.getPlotFormat(index))
            
            if key != None:
                plot_format[0] = key
            
            if isinstance(indices, (list, tuple)):
                plot_format[1] = indices
            
            if isinstance(plot_settings, dict):
                plot_format[2] = plot_settings
            
            self._formats[index] = tuple(plot_format)
            
            return True
        else:
            return False
    
    def setMPLSettings(self, settings):
        self._mpl_settings = settings
    
    def getMPLSettings(self):
        return self._mpl_settings
    
    def setData(self, key, value):
        """Set some data to save in this object with the specific key
        Parameters
        ----------
            key : String or int
                The key to identify the value with
            value : anything
                The corresponding value
        """
        
        self._data[key] = value
    
    def getData(self, key):
        """Get the value of the specified key
        Returns
        -------
            anything, the value
        """
        
        if key in self._data:
            return self._data[key]
        else:
            return None
    
    def addAttribute(self, attr):
        """Add the given attribute to the internal collection. Note that attributes
        will always exist only one time in the collection. Attributes are used
        for identifying the datacontainer by the user, this is for example used
        in the generation of the name.
        
        Parameters
        ----------
            attr : String
                The attribute
        """
        
        self.attributes.add(attr)
    
    def getAttributes(self):
        """Get the collection of attributes
        
        Returns
        -------
            set
                The attributes
        """
        
        return self.attributes
    
    def createName(self, short = False, max_len = None):
        """Get the "name" of this datacontainer
        Parameters
        ----------
            short : boolean, optional
                If this is True this will return the short name which includes
                only a few values, this has no fixed length
            max_len : int, optional
                The maximum length in characters of the name of this datacontainer,
                this has to be greater than 3
        """
        
        if not my_utilities.is_numeric(max_len) or max_len <= 3:
            max_len = None
        
        text = ""
        apply_brackets = False
        head_contents = (("SAMPLE_MATERIAL", None),
                         ("SAMPLE_COMMENT", None),
                         ("SAMPLE_MASS", "mg"), 
                         ("SAMPLE_VOLUME", None), 
                         ("SAMPLE_MOLECULAR_WEIGHT", None),
                         ("SAMPLE_SIZE", None), 
                         ("SAMPLE_SHAPE", None))
        
        if "title" in self.header and self.header["title"] != "":
            text += self.header["title"]
        
        if "info" in self.header and isinstance(self.header["info"], dict):
            for name, unit in head_contents:
                if name in self.header["info"] and self.header["info"][name] != "":
                    if text != "":
                        text += ", "
                    text += self.header["info"][name]
                    
                    if isinstance(unit, str):
                        text += unit
        
        text_empty = (text == "")
        
        attrs = ", ".join(self.attributes)
        if attrs != "":
            text = attrs + ": " + text
            
        if text_empty or not short:
            if not text_empty:
                apply_brackets = True
                text += " ["
            
            filepath = str(os.path.basename(self.filepath))
            if filepath.count(".rw.dat") > 0:
                filepath = my_utilities.rreplace(filepath, ".rw.dat", "", 1)
            elif filepath.count(".dat") > 0:
                filepath = my_utilities.rreplace(filepath, ".dat", "", 1)
            
            text += filepath
            
            if apply_brackets:
                text += "]"
                
        if my_utilities.is_numeric(max_len) and len(text) > max_len:
            text = text[0:max_len - 3] + "..."
            
#        print("DataContainer.createName(): ", text)
        
        return text
    
    def __len__(self):
        """Get the length of the datacontainer which is the number of datapoints
        Returns
        -------
            int
                The length of the datapoints
        """
        return len(self.datapoints)
    
    def __deepcopy__(self, memo):
        """Implements the deepcopy interface, this prevents recursive infinite
        copying
        Parameters
        ----------
            memo : ??
                The memo
        Returns
        -------
            DataContainer
                The copy of this object
        """
        cls = self.__class__
        result = cls.__new__(cls)
        
        memo[id(self)] = result
        
        for k, v in self.__dict__.items():
            if k == "_data":
                c = copy.copy(v)
                setattr(result, k, c)
            else:
                setattr(result, k, copy.deepcopy(v, memo))
        return result