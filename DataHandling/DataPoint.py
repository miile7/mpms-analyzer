# -*- coding: utf-8 -*-
"""
Created on Tue Oct 17 10:29:04 2017

@author: Maximilian Seidler
"""

import warnings
import copy
import re

import Constants
import my_utilities
import DataHandling.calculation
import DataHandling.PlotData
import DataHandling.DataContainer

class DataPoint:
    LINENUMBER = "linenumber"
    COMMENT = "comment"
    TIMESTAMP = "timestamp"
    RAW_POSITION = "raw_position"
    RAW_VOLTAGE = "raw_voltage"
    PROCESSED_VOLTAGE = "processed_voltage"
    FIXED_FIT_VOLTAGE = "fixed_c_fit"
    FREE_FIT_VOLTAGE = "free_c_fit"
    INDEX = "index"
    FIT = "fit"
    
    EMPTY_ROW = "empty"
    
    def __init__(self, parent_datacontainer = None, index = None):
        """Initialize the Datapoint with empty data.
        
        Parameters
        ----------
            parent_datacontainer : DataContainer, optional
                The datacontainer which created this DataPoint
        """
        
        # the names of the lines found in the file
        self._column_names = []
        # the units of the lines found in the file
        self._column_units = []
        # the rows for this data point
        self._data_rows = []
        # the fixed fit done by the manufacturers software in [V]
        self._fixed_c_fit = []
        # the free fit done by the manufacturers software in [V]
        self._free_c_fit = []
        # the environment variables when the measurement has been done (e.g. temperature)
        self._environment_variables = []
        # the environment variables units 
        self._environment_variables_units = []
        # the absolute path of the file (at the moment when it was opened) where
        # the data comes from
        self._raw_file = None
        # the fit variables over the raw position
        self._raw_pos_fit = []
        # this is a list which olds how the background has been subtracted for 
        # manual inspection. For further information visit the DataHandling.fit.subtractBackgroundData
        # function. The format is:
        #   self._background_remove_data[i][0] : x value
        #   self._background_remove_data[i][1] : y value including the background (the original data)
        #   self._background_remove_data[i][2] : y value of the background
        #   self._background_remove_data[i][3] : y value of the result (after the subtraction)
        self._background_remove_data = None
        # the labels for the remove data
        self._background_remove_labels = None
        # the axis that have been used for removing the background
        self._background_remove_axis = None
        # the parent datacontainer
        if isinstance(parent_datacontainer, DataHandling.DataContainer.DataContainer):
            self._parent = parent_datacontainer
        else:
            self._parent = None
        # the index of the current data point
        self._index = index
        # the unit regexp
        self._environment_variables_unit_regexp = re.compile(r"[^\d]+\s*$")
        
        self.fitting_not_possible = False
        self.disabled = False
        
    @property
    def column_names(self):
        return self._column_names

    @column_names.setter
    def column_names(self, column_names):
        try:
            self._column_names = tuple(column_names)
            return True
        except ValueError:
            return False
        
    @property
    def column_units(self):
        return self._column_units

    @column_units.setter
    def column_units(self, column_units):
        try:
            self._column_units = tuple(column_units)
            return True
        except ValueError:
            return False
        
    @property
    def filepath(self):
        if self._parent != None and isinstance(self._parent, DataHandling.DataContainer.DataContainer):
            return self._parent.filepath
        else:
            return None

    @filepath.setter
    def filepath(self, filepath):
        return False
        
    @property
    def parent(self):
        if self._parent != None and isinstance(self._parent, DataHandling.DataContainer.DataContainer):
            return self._parent
        else:
            return None

    @parent.setter
    def parent(self, parent):
        return False
    
    @property
    def background_remove_data(self):
        return self._background_remove_data
    
    @background_remove_data.setter
    def background_remove_data(self, background_remove_data):
        pass
    
    @property
    def background_remove_labels(self):
        return self._background_remove_labels
    
    @background_remove_labels.setter
    def background_remove_labels(self, background_remove_labels):
        pass
    
    @property
    def background_remove_axis(self):
        return self._background_remove_axis
    
    @background_remove_axis.setter
    def background_remove_axis(self, background_remove_axis):
        pass
    
    @property
    def index(self):
        return self._index
    
    @index.setter
    def index(self, index):
        self._index = index
    
    def addEmptyDataRow(self):
        self._data_rows.append(DataPoint.EMPTY_ROW)
    
    def addDataRow(self, raw_position, raw_voltage, processed_voltage = None, linenumber = None, timestamp = None, comment = None):
        """Add a row of data (of the raw file) to the current data point. This
        is not meant for adding the Fit!
        
        Parameters
        ----------
        raw_position : float
            The position of the probe in [mm]
        raw_voltage : float
            The measured raw voltage in [V]
        processed_voltage : float
            The voltage processed by the manufacturers software in [V] (default: None)
        linenumber : int, optional
            The linenumber in the internal file (default: None)
        timestamp : int, optional
            The timestamp when the data row has been created (default: None)
        comment : string, optional
            The comment for the data row (default: None)
            
        Returns
        -------
        boolean:
            Whether the data has been added successfully
        """
        
        # add the data as a tupel to the current data rows, the order is the same
        # as in the raw files for better readibility
        self._data_rows.append((
                int(linenumber), 
                str(comment), 
                my_utilities.force_float(timestamp, True),
                my_utilities.force_float(raw_position, True),
                my_utilities.force_float(raw_voltage, True), 
                my_utilities.force_float(processed_voltage, True))
        )
    
        return True
    
    def clearDataRows(self):
        self._data_rows = []
    
    def addEmptyFixedFit(self):
        self._fixed_c_fit.append(DataPoint.EMPTY_ROW)
    
    def addFixedFit(self, raw_position, fixed_fit_voltage, linenumber = None, timestamp = None, comment = None):
        """Add a Row for the fixed fit (done by the manufacturers software).
        
        Parameters
        ----------
        raw_position : float
            The position of the probe in [mm]
        fixed_fit_voltage : float
            The voltage of the fixed c fit in [V]
        linenumber : int, optional
            The linenumber in the internal file (default: None)
        timestamp : int, optional
            The timestamp when the data row has been created (default: None)
        comment : string, optional
            The comment for the data row (default: None)
            
        Returns
        -------
        boolean:
            Whether the data has been added successfully
        """
        # add the data as a tupel to the fixed c fit data, the order corresponds
        # to the order in the raw files for better readibility
        self._fixed_c_fit.append((int(linenumber), str(comment), float(timestamp), 
                                  float(raw_position), float(fixed_fit_voltage)))
        return True
    
    def addFreeFit(self, raw_position, free_fit_voltage, linenumber = None, timestamp = None, comment = None):
        """Add a Row for the ree fit (done by the manufacturers software).
        
        Parameters
        ----------
        raw_position : float
            The position of the probe in [mm]
        free_fit_voltage : float
            The voltage of the free c fit in [V]
        linenumber : int, optional
            The linenumber in the internal file (default: None)
        timestamp : int, optional
            The timestamp when the data row has been created (default: None)
        comment : string, optional
            The comment for the data row (default: None)
            
        Returns
        -------
        boolean:
            Whether the data has been added successfully
        """
        
        # add the data as a tupel to the free c fit data, the order corresponds
        # to the order in the raw files for better readibility
        self._free_c_fit.append((int(linenumber), str(comment), float(timestamp), 
                                 float(raw_position), float(free_fit_voltage)))
        return True
    
    def addEmptyFreeFit(self):
        self._free_c_fit.append(DataPoint.EMPTY_ROW)
        
    def addEnvironmentVariables(self, variables, linenumber = None):
        """Add a set of environmnent variables for the data point. Try to set the linenumber,
        this will make it possible to detect for which data rows this variables are
        
        Parameters
        ----------
        variables : dict
            The variables as a dict, the names of the variable name should hold
            the variables value
        linenumber : int, optional
            The number of the line
            
        Returns
        -------
        boolean:
            Whether the data has been added successfully
        """
        
        try:
            self._environment_variables.append((dict(variables), linenumber))
            return True
        except ValueError:
            return False
    
    def getEnvironmentVariable(self, key, index):
        """Get the environmnetn variable with the given key, if it does not exist
        false will be returned
        
        Parameters
        ----------
            key : String
                The key to get the value of
            index : int
                The index of the environment variable
                
        Returns
        -------
            anything
                The value or False if the key does not exist
        """
        
        
        if key == DataHandling.DataContainer.DataContainer.FIELD:
            hf = self.getEnvironmentVariable(DataHandling.DataContainer.DataContainer.HIGH_FIELD, index)
            lf = self.getEnvironmentVariable(DataHandling.DataContainer.DataContainer.LOW_FIELD, index)
            
            if hf != False and lf != False:
                unit = hf
                hf = my_utilities.force_float(hf)
                lf = my_utilities.force_float(lf)
                
                unit = unit.strip().replace(str(hf), "")
                
                # calculate the mean and standard deviation for returning
                mean, error = my_utilities.mean_std((hf, lf))
                
                return str(mean) + unit
            elif hf != False:
                return hf
            else:
                return lf
        else:
            try:
                return self._environment_variables[index][0][key]
            except KeyError:
                return False
            except IndexError:
                return False
            except TypeError:
                return False
    
    def getEnvironmentVariableAvg(self, key, force_number = True):
        """Get the average (and standard diviation) of the environmnent variable
        with the given key.
        
        Parameters
        ----------
            key : String
                The key to get the value of
            force_number : boolean, optional
                Whether to convert the value into a boolean (true) or not (false),
                default is true
                
        Returns
        -------
            anything
                The value or False if the key does not exist
            float
                If the value is a numeric value the standard diviation will be
                returned
        """
        
        count = self.getEnvironmentVariablesCount()
        values = []
        
        for i in range(0, count):
            value = self.getEnvironmentVariable(key, i)
            if force_number:
                try:
                    value = my_utilities.force_float(value)
                except:
                    print(self._environment_variables)
                    raise
            else:
                try:
                    value = float(value)
                except ValueError:
                    # do nothing
                    pass
            
            if my_utilities.is_numeric(value):
                values.append(value)
        
        if len(values) > 0:
            return my_utilities.mean_std(values)
        else:
            return False
    
    def getEnvironmentVariableIndexByLinenumber(self, linenumber):
        """Get the index by passing the line number
        
        Parameters
        ----------
            linenumber : int
                The linenumber
                
        Returns
        -------
            int
                The index of of the variables or false if it does not exist
        """
        
        try:
            return [i[1] for i in self._environment_variables].search(linenumber)
        except ValueError:
            return False
    
    def getEnvironmentVariablesCount(self):
        """Get the count of variable collections
        
        Returns
        -------
            int
                The number of dicts which contain the environmnetn variables
        """
        
        return len(self._environment_variables)
    
    def getEnvironmentVariablesUnit(self, key, index = 0):
        """Get the unit of the environment variable with the given key. If the
        index is not given the first envifonment variable will be used
        
        Parameters
        ----------
            key : String
                The key to get the value of
            index : int
                The index of the environment variable
                
        Returns
        -------
            String, the unit
        """
        
        value = self.getEnvironmentVariable(key, index)
        
        result = self._environment_variables_unit_regexp.search(str(value))
        
        if result == None:
            return ""
        else:
            return str(result.group(0)).strip()
    
    def getEnvironmnetVariableKeys(self):
        """Get the keys that the environment variables support in the current
        datapoint
        
        Returns
        -------
            list
                A list of keys that the datacontainer supports as environment
                variable keys
        """
        
        keys = set()
        
        for environment_variable, linenumber in self._environment_variables:
            keys.update(set(environment_variable.keys()))
        
        return list(keys)
    
    def getEnvironmentVariables(self):
        """Get the environment variables, this will return a list of dicts
        
        Returns
        -------
            list of dicts
                The environment variables dictionaries
        """
        
        return [i[0] for i in self._environment_variables]
    
    def getPlotData(self, x_axis, y_axis, plain_lists = False, include_empty_rows = False):
        """Get the data for plotting the y_axis data over the x_axis data. This
        will return a tuple containing the x_axis values in index 0, the y axis
        data will be in index 1. If the data could not be plotted over eachother
        None will be returned
        
        Parameters
        ---------
            x_axis : string
                The name of the data which should be used for the x axis
            y_axis : string
                The name of the data which should be used for the y axis
            plain_lists : boolean, optional
                Whether to return two plain lists (True) or to return a PlotData
                object (False), default: False
            include_empty_rows : boolean, optional
                Whether to include empty rows, this can be only used if 
                plain_lists=True, default:False
                
        Returns
        -------
            PlotData
                The data of the plot
        """
        
        # holds all the indices which (should) be in all the lists
        general_indices = (DataPoint.COMMENT, DataPoint.TIMESTAMP, 
                           DataPoint.RAW_POSITION, DataPoint.LINENUMBER,
                           DataPoint.INDEX)
        
        # the index in the data list for the x axis
        x_index = None
        # the index in the data list for the y axis
        y_index = None
        # the x-y-plot data as an multidimensional array, mostyl only one of the
        # datas is being used
        x_data = None
        y_data = None
        
        # whether to go through the returned data and return the <axis>_index
        # value or not
        redo_x = True
        redo_y = True
        
        # detect the length of a valid row to immitate this length
        row_length = None
        plot_data_mode = None
        if include_empty_rows:
            plot_data_mode = 1
            
            for row in self._data_rows:
                if isinstance(self._data_rows, (list, tuple)):
                    row_length = len(row)
                    break
        
        if ((x_axis == DataPoint.RAW_POSITION and y_axis == DataPoint.FIT) or
            (y_axis == DataPoint.RAW_POSITION and x_axis == DataPoint.FIT)):
            # fit is only allowed by position
            
            # receive the voltage data, this is the value that has been fit so 
            # use the x data of this values
            voltage_index, voltage_data = self._getPlotData(DataPoint.RAW_VOLTAGE)
            # get the raw position data index
            x_index, x_data = self._getPlotData(DataPoint.RAW_POSITION, voltage_data)
            # extract the raw position from the voltage data
            x_data = [float(item[x_index]) for item in voltage_data]
            # prepare the y data
            y_data = []
            
            if self._raw_pos_fit != None and isinstance(self._raw_pos_fit, (tuple, list)):
                # apply the fit values and execute the dipol funciton in the calculation.py
                fit = self.getRawFitResults()
                
                if isinstance(fit, (list, tuple)) and len(fit) >= 2:
                    fit_results = fit[0]
                    
                    fit_results = tuple(fit_results)
                    for x in x_data:
                        parameters = (x,) + fit_results
                        y_data.append(DataHandling.calculation.dipolfunction(*parameters))
                else:
                    x_data = []
            
            # check if the axis have been the other way around, if they were
            # switch the axis
            if y_axis == DataPoint.RAW_POSITION:
                x_data, y_data = y_data, x_data
            
            # prevent doing anyting
            redo_x = False
            redo_y = False
            # x and y indices have to exist, otherwise this will cause an error
            x_index = -1
            y_index = -1
        elif x_axis not in general_indices and y_axis in general_indices:
            # y_axis is a general variable an should be plotted over a specific
            # variable
            x_index, x_data = self._getPlotData(x_axis, None, plot_data_mode, row_length)
            y_index, y_data = self._getPlotData(y_axis, x_data, plot_data_mode, row_length)
            
            # just to make sure
            y_data = x_data
            
        elif x_axis in general_indices and y_axis not in general_indices:
            # x_axis is a general variable an should be plotted over a specific
            # variable
            y_index, y_data = self._getPlotData(y_axis, None, plot_data_mode, row_length)
            x_index, x_data = self._getPlotData(x_axis, y_data, plot_data_mode, row_length)
            
            # just to make sure
            x_data = y_data
            
        elif x_axis in general_indices and y_axis in general_indices:
            # two general variables should be plotted over each other, ignore
            # the data, data will be received from ALL internal lists
            if x_axis == DataPoint.INDEX:
                y_index, y_data = self._getPlotData(y_axis, None, plot_data_mode, row_length)
                x_index, x_data = self._getPlotData(x_axis, y_data, plot_data_mode, row_length)
            else:
                x_index, x_data = self._getPlotData(x_axis, None, plot_data_mode, row_length)
                y_index, y_data = self._getPlotData(y_axis, x_data, plot_data_mode, row_length)
            
            # combine all lists for containing ALL results, delete entries in
            # x_data/y_data (even though there should not be any entry anyway)
#            if x_index >= 0:
#                x_data = [float(item[x_index]) for item in row_data]
#                x_data = x_data + [float(item[x_index]) for item in self._fixed_c_fit]
#                x_data = x_data + [float(item[x_index]) for item in self._free_c_fit]
            
#            if y_index >= 0:
#                y_data = [float(item[y_index]) for item in row_data]
#                y_data = x_data + [float(item[y_index]) for item in self._fixed_c_fit]
#                y_data = x_data + [float(item[y_index]) for item in self._free_c_fit]
            
#            redo_x = False
#            redo_y = False
        else:
            # cannot create a plot of the given axis
            return None
        
        if redo_x and x_index >= 0 and (isinstance(x_data, list) or isinstance(x_data, tuple)):
            # generate the x data list
            x_data = [float(item[x_index]) for item in x_data]
        
        if redo_y and y_index >= 0 and (isinstance(y_data, list) or isinstance(y_data, tuple)):
            # generate the y data list
            y_data = [float(item[y_index]) for item in y_data]
        
        # returning the specific column
        if plain_lists:
            return x_data, y_data
        else:
            # the x and y units and the names
            x_label, x_unit = self._getNameDataForAxis(x_axis)
            y_label, y_unit = self._getNameDataForAxis(y_axis)
            
            return DataHandling.PlotData.PlotData(x=x_data, 
                                                  y=y_data, 
                                                  x_label=x_label, 
                                                  y_label=y_label, 
                                                  x_unit=x_unit,
                                                  y_unit=y_unit,
                                                  x_axis=x_axis,
                                                  y_axis=y_axis,
                                                  origin=self)
        
    def _getPlotData(self, name, data = None, mode = None, row_length = 1):
        """Get the data to plot an index for the column in the also returned 
        multidimensional array. The data you want to plot (which is given as the
        name parameter) will be the column with index which is saved in the
        returned tuple at index 0, the index 1 of the returned tuple will contain
        the multidimensional list in which the column can be found
        
        Parameters
        ----------
            name : string
                The name of the data to plot
            data : list of tuples or list of lists, optional
                If this is passed the same data will be returned as the second
                parameter, this is for future use only
            mode : int, optional
                Use mode=1 for including empty rows, this means that all empty
                rows will be filled with row_length times DataPoint.EMPTY to keep
                the length. You have to pass the row_length in this case
                Use mode=2 for returning the data list exactly as it is, this will
                return a reference, not a copy!
                Use mode=<anything else> if you want to remove empty rows, this 
                is the default
            row_length : int, optional
                The length of one valid data row, this is used only if the 
                mode=1
                
        Returns
        -------
            int
                The index of the data row in the returned data
            list
                The data table in which the row with the returned index is the
                requested data
        """
        
        index = None
        
        # maybe later the returned index will depend on the given data, therefore
        # just save memory by returning the same data if there is data
        
        if name == DataPoint.LINENUMBER:
            # prevent from exiting because of wrong type of data
            if data == None:
                data = self._data_rows
#                data = []
            index = 0
        elif name == DataPoint.COMMENT:
            # prevent from exiting because of wrong type of data
            if data == None:
                data = self._data_rows
#                data = []
            index = 1
        elif name == DataPoint.TIMESTAMP:
            # prevent from exiting because of wrong type of data
            if data == None:
                data = self._data_rows
#                data = []
            index = 2
        elif name == DataPoint.INDEX:
            if data == None:
                data = self._data_rows
#                data = []
            elif isinstance(data, list) or isinstance(data, tuple):
                data = list(range(0, len(data)))
            index = -1
        elif name == DataPoint.RAW_POSITION:
            # prevent from exiting because of wrong type of data
            if data == None:
                data = self._data_rows
#                data = []
            index = 3
        elif name == DataPoint.RAW_VOLTAGE:
            # data is in _data_rows only
            if data == None:
                data = self._data_rows
            index = 4
        elif name == DataPoint.PROCESSED_VOLTAGE:
            # data is in _data_rows only
            if data == None:
                data = self._data_rows
            index = 5
        elif name == DataPoint.FIXED_FIT_VOLTAGE or name == "fixed_fit":
            # data is in _fixed_c_fit only
            if data == None:
                data = self._fixed_c_fit
            index = 4
        elif name == DataPoint.FREE_FIT_VOLTAGE or name == "free_fit":
            # data is in _free_c_fit only
            if data == None:
                data = self._free_c_fit
            index = 4
        
        if data != None and not isinstance(data, str) and index != None and index >= 0:
            
            if mode == 1:
                data = list(map(lambda x: row_length * [DataPoint.EMPTY] if not isinstance(x, (list, tuple)) else x, data))
            elif mode != 2:
                data = list(filter(lambda x: isinstance(x, (list, tuple)), data))
                
            return (index, data)
        else:
            return None
    
    def getUnitForAxis(self, axis):
        """Get the unit for the given axis
        
        Parameters
        ----------
            axis : String
                The axis
                
        Returns
        -------
            String
                The unit
        """
        val = self._getNameDataForAxis(axis)
        
        return val[1]
    
    def getNameForAxis(self, axis):
        """Get the Name for the given axis
        
        Parameters
        ----------
            axis : String
                The axis
                
        Returns
        -------
            String
                The name
        """
        val = self._getNameDataForAxis(axis)
        
        return val[0]
    
    def _getNameDataForAxis(self, axis):
        """Get the unit for the given axis.
        
        Parameters
        ----------
            axis : String
                The axis
                
        Returns
        -------
            tuple
                The name of the axis and its unit
        """
        
        l = min((len(self.column_units), len(self.column_names)))
        
        if axis == DataPoint.COMMENT and l > Constants.RAW_FILE_OFFSET_COMMENT:
            return (str(self.column_names[Constants.RAW_FILE_OFFSET_COMMENT]),
                    str(self.column_units[Constants.RAW_FILE_OFFSET_COMMENT]))
        elif axis == DataPoint.LINENUMBER:
            return ("linenumber", "")
        elif axis == DataPoint.TIMESTAMP and l > Constants.RAW_FILE_OFFSET_TIMESTAMP:
            return (str(self.column_names[Constants.RAW_FILE_OFFSET_TIMESTAMP]),
                    str(self.column_units[Constants.RAW_FILE_OFFSET_TIMESTAMP]))
        elif axis == DataPoint.RAW_POSITION and l > Constants.RAW_FILE_OFFSET_RAW_POSITION:
            return (str(self.column_names[Constants.RAW_FILE_OFFSET_RAW_POSITION]),
                    str(self.column_units[Constants.RAW_FILE_OFFSET_RAW_POSITION]))
        elif axis == DataPoint.RAW_VOLTAGE and l > Constants.RAW_FILE_OFFSET_RAW_VOLTAGE:
            return (str(self.column_names[Constants.RAW_FILE_OFFSET_RAW_VOLTAGE]),
                    str(self.column_units[Constants.RAW_FILE_OFFSET_RAW_VOLTAGE]))
        elif axis == DataPoint.PROCESSED_VOLTAGE and l > Constants.RAW_FILE_OFFSET_PROCESSED_VOLTAGE:
            return (str(self.column_names[Constants.RAW_FILE_OFFSET_PROCESSED_VOLTAGE]),
                    str(self.column_units[Constants.RAW_FILE_OFFSET_PROCESSED_VOLTAGE]))
        elif axis == DataPoint.FIXED_FIT_VOLTAGE and l > Constants.RAW_FILE_OFFSET_FIXED_C_FIT:
            return (str(self.column_names[Constants.RAW_FILE_OFFSET_FIXED_C_FIT]) + "(MPMS Software)",
                    str(self.column_units[Constants.RAW_FILE_OFFSET_FIXED_C_FIT]))
        elif axis == DataPoint.FREE_FIT_VOLTAGE and l > Constants.RAW_FILE_OFFSET_FREE_C_FIT:
            return (str(self.column_names[Constants.RAW_FILE_OFFSET_FREE_C_FIT]) + "(MPMS Software)",
                    str(self.column_units[Constants.RAW_FILE_OFFSET_FREE_C_FIT]))
        elif axis == DataPoint.INDEX:
            return ("index", "")
        elif axis == DataPoint.FIT:
            return ("Fit (free center)", "V")
        else:
            return (axis, "")
    
    def execFit(self):
        """Fit the initialized DataPoint to a dipol function (by using the 
        DataHandling.calculation.datapointFit() function)
        """
        
        # squid range fallback and initialization
        squid_range = self.getEnvironmentVariableAvg("squid range")
        if squid_range != False and isinstance(squid_range, tuple):
            squid_range = squid_range[0]
        
        # prevent devision by zero
        if not my_utilities.is_numeric(squid_range) or squid_range == 0:
            squid_range = 1
        
        # receive data to fit
        xdata, ydata = self.getPlotData(DataPoint.RAW_POSITION, DataPoint.RAW_VOLTAGE)
        
        # fit the data using DataHandling.calculation.py
        try:
            self._raw_pos_fit = DataHandling.calculation.datapointFit(xdata, ydata, squid_range)
        except Exception as e:
            self.fitting_not_possible = True
            raise e
    
    def getFitResults(self):
        """Get the result of the fit. If the fit is not executed before this 
        will execute the fit automatically
        
        Returns
        -------
            float
                The magnetization as a result of the fit
            float
                The error of the magnetization
            or None
                if an error occurred
        """
        
        if (self._raw_pos_fit == None or not my_utilities.is_iterable(self._raw_pos_fit) or 
            len(self._raw_pos_fit) <= 0):
            if self.fitting_not_possible:
                return None
            else:
                self.execFit()
        
        return (self._raw_pos_fit[0], self._raw_pos_fit[1])
    
    def getRawFitResults(self):
        """Get the result of the fit with all the result values that the square
        fit returned
        
        Returns
        -------
            float
                The fit parameter results
            float
                The fit parameter result errors
        """
        if (self._raw_pos_fit == None or not my_utilities.is_iterable(self._raw_pos_fit) or 
            len(self._raw_pos_fit) <= 0):
            if self.fitting_not_possible:
                return None
            else:
                self.execFit()
        
        return self._raw_pos_fit[2], self._raw_pos_fit[3]
    
    def getScanLength(self):
        """Returns the scan length and the unit for the scan length or None if 
        there is no data
        
        Returns
        -------
            float
                The scan length
            String
                The unit
        """
        
        plotdata = self.getPlotData(DataPoint.RAW_POSITION, DataPoint.RAW_VOLTAGE)
        
        if isinstance(plotdata, DataHandling.PlotData.PlotData):
            xdata = plotdata.x
            
            return max(xdata) - min(xdata), self.getUnitForAxis(DataPoint.RAW_POSITION)
        else:
            return None
        
    def getScanTime(self):
        """Returns the time that the scan took
        
        Returns
        -------
            tuple of float
                The scan speed mean and the standard diviation
            String
                The unit
        """
        
        plotdata = self.getPlotData(DataPoint.TIMESTAMP, DataPoint.RAW_POSITION)
        
        if isinstance(plotdata, DataHandling.PlotData.PlotData):
            xdata = plotdata.x
            
            return max(xdata) - min(xdata), self.getUnitForAxis(DataPoint.TIMESTAMP)
        else:
            return None
        
    def getScanSpeed(self):
        """Returns the speed of the scan
        
        Returns
        -------
            tuple of float
                The scan speed mean and the standard diviation
            String
                The unit
        """
        
        plotdata = self.getPlotData(DataPoint.TIMESTAMP, DataPoint.RAW_POSITION)
        
        xdata = plotdata.x
        ydata = plotdata.y
        
        speed = []
        
        for i, x in enumerate(xdata):
            if i > 0:
                speed.append((ydata[i] - ydata[i - 1]) / (xdata[i] - xdata[i - 1]))
        
        unit = "{}/{}".format(
                self.getUnitForAxis(DataPoint.RAW_POSITION),
                self.getUnitForAxis(DataPoint.TIMESTAMP)
            )
        
        return my_utilities.mean_std(speed), unit
            
    
    def removeBackgroundData(self, background_datapoint, x_axis = RAW_POSITION, 
                             y_axis = RAW_VOLTAGE):
        """Remove the given background_datapoint from this datapoint. This will
        (by default) subtract the raw position from the raw voltage. The actual
        subtracting will be done in the DataHandling.fit file. You can specify
        the x_axis and y_axis for the data to remove.
        Note: This does *not* return a copy, the subtraction will be done in 
            *this* object!
            
        Parameters
        ----------
            background_datapoint : DataPoint
                The datapoint to remove
            x_axis, y_axis : String, optional
                The x and y axis where to subtract the y axis of the background
                data from the current datapoint
        """
        
        # Can't use self.getPlotData(...) right here because otherwise the list
        # can not be set in the last line. The self._getPlotData(...) returns 
        # a reference to the real data where it should be saved whilst the 
        # self.getPlotData(...) function returns a copy of the list
        x_index, xdata = self._getPlotData(x_axis, None, 2)
        y_index, ydata = self._getPlotData(y_axis, None, 2)
        data = []
        
        print("DataPoint.removeBackgroundData(): index: ", self.index)
        
        # set the data list for the empty list
        if xdata != ydata:
            index_str = ""
            if isinstance(self._index, int):
                index_str = " #" + str(self._index)
            
            raise ValueError(("Removing background was not possible in Datapoint" + 
                              index_str + ": x_axis and y_axis cannot be used " + 
                              "for removing background, plotting '{}' vs '{}' " + 
                              "does not make sense.").format(x_axis, y_axis))
        else:
            data = xdata
        
        xdata = []
        ydata = []
        indices_map = {}
        
        # get the x and y data of the sample with background, save the indices
        # in the indices_map to skip empty rows
        for i, row in enumerate(data):
            if row != DataPoint.EMPTY_ROW:
                xdata.append(data[i][x_index])
                ydata.append(data[i][y_index])
                indices_map[i] = len(xdata) - 1
        
        if isinstance(background_datapoint, DataHandling.DataPoint.DataPoint):
            # get the x-y-data of the background
            xbackground_data, ybackground_data = background_datapoint.getPlotData(x_axis, y_axis, True)
            
            # checking if the environment variables of the background point and
            # the current point are the same
            compare_list = (
                    DataHandling.DataContainer.DataContainer.TEMPERATURE,
                    DataHandling.DataContainer.DataContainer.FIELD
                    )
            
            # go through the environment variables to check
            for compare_key in compare_list:
                # the variables
                var = self.getEnvironmentVariableAvg(compare_key)
                b_var = background_datapoint.getEnvironmentVariableAvg(compare_key)
                
                if isinstance(var, (list, tuple)) and isinstance(b_var, (list, tuple)):
                    # check if the difference is in the range of Constants.MAXIMUM_DIVIATION_BACKGROUND_ENVIRONMENT
                    if abs(var[0] - b_var[0]) > (max((var[0], b_var[0])) * Constants.MAXIMUM_DIVIATION_BACKGROUND_ENVIRONMENT):
                        name = compare_key
                        if name in Constants.ENVIRONMENT_VARIABLE_NAMES:
                            name = Constants.ENVIRONMENT_VARIABLE_NAMES[name]
                        
                        unit = self.getEnvironmentVariablesUnit(compare_key)
                        b_unit = background_datapoint.getEnvironmentVariablesUnit(compare_key)
                        
                        # warn if not
                        warnings.warn(("The difference of the {} between the original " + 
                                       "data and the background data point is more " + 
                                       "than {}%: Original data has {}{}, background " + 
                                       "data has {}{}.").format(name, 
                                                 Constants.MAXIMUM_DIVIATION_BACKGROUND_ENVIRONMENT * 100,
                                                 var[0],
                                                 unit,
                                                 b_var[0],
                                                 b_unit))
            
            # get the background squid range
            background_squid_range = background_datapoint.getEnvironmentVariableAvg("squid range")
        elif isinstance(background_datapoint, (list, tuple)) and len(background_datapoint) >= 2:
            # get the x-y-data of the background
            xbackground_data = background_datapoint[0]
            ybackground_data = background_datapoint[1]
            
            # fake the background squid range
            background_squid_range = 1
        
        # get the squid range
        squid_range = self.getEnvironmentVariableAvg("squid range")
        
        # the getEnvironmentVariableAvg returns a tuple with the medium value
        # at index 0, index 1 will hold the standard diviation, this is not neede
        # here
        if isinstance(squid_range, (list, tuple)):
            squid_range = squid_range[0]
        if isinstance(background_squid_range, (list, tuple)):
            background_squid_range = background_squid_range[0]
        
        # remove the squid range otherwise squid range is applied twice
        for i, environment_vars_collection in enumerate(self._environment_variables):
            environment_vars = environment_vars_collection[0]
            
            if "squid range" in environment_vars:
                environment_vars["squid range"] = 1
                
            environment_vars["sample squid range"] = str(squid_range)
            environment_vars["background squid range"] = str(background_squid_range)
                
            self._environment_variables[i] = (environment_vars, environment_vars_collection[1])
        
        # make sure that the squid ranges exist
        if not my_utilities.is_numeric(squid_range):
            squid_range = 1
        if not my_utilities.is_numeric(background_squid_range):
            background_squid_range = 1
        
        # let the DataHandling.calculation.py perform the subtraction of the data
        result = DataHandling.calculation.subtractBackgroundData(
                xdata, ydata, squid_range,xbackground_data, ybackground_data,
                background_squid_range)
        
        if not isinstance(result, (list, tuple)) or len(result) < 2:
            raise ValueError("The result of the background subtraction is incorrect, " + 
                             "there have to be at least two values")
        else:
            xdata = result[0]
            ydata = result[1]
            
            if len(result) > 2:
                self._background_remove_data = result[2]
            if len(result) > 3:
                self._background_remove_labels = result[3]
        
        # save the axis that have been used for removing
        self._background_remove_axis = (x_axis, y_axis)
        
        # save the data to the internal list again, data is a reference to the 
        # correct internal list
        for index, _ in enumerate(data):
            row = data[index]
            
            if row != DataPoint.EMPTY_ROW:
                row = list(row)
                row[x_index] = xdata[indices_map[index]]
                row[y_index] = ydata[indices_map[index]]
            
                data[index] = tuple(row)
    
    def getExportRawData(self):
        """Get the 2d list of the data to export. This is the data to create a
        raw MPMS file.
        
        Returns
        -------
            list of lists
                The data rows as a list
        """
        
        data = []
                
        # the order_list defines the conversion from the internal list to the 
        # export list. The target indices are the indices of the order_list,
        # the indices of the source (= the internal list) are the values
        # 
        # the order of the internal list is:
        #   linenumber
        #   comment
        #   timestamp
        #   raw position
        #   raw voltage
        #   processed voltage
        order_list = {}
        order_list[Constants.RAW_FILE_OFFSET_COMMENT] = 1
        order_list[Constants.RAW_FILE_OFFSET_TIMESTAMP] = 2
        order_list[Constants.RAW_FILE_OFFSET_RAW_POSITION] = 3
        order_list[Constants.RAW_FILE_OFFSET_RAW_VOLTAGE] = 4
        
        # get the raw fit results
        try:
            res = self.getRawFitResults()
            
            # dirft and y offset
            drift = res[0][1]
            y_offset = res[0][2]
        except RuntimeError:
            res = None
            drift = None
            y_offset = None
        
        for row in self._data_rows:
            data_row = [row[order_list[i]] for i in order_list]
            
            # create processed voltage
            if drift != None and y_offset != None:
                processed_voltage = row[Constants.RAW_FILE_OFFSET_RAW_VOLTAGE] - row[Constants.RAW_FILE_OFFSET_RAW_VOLTAGE] * drift - y_offset
            else:
                processed_voltage = ""
            
            data_row.append(processed_voltage)
            
            data.append(data_row)
        
        if len(self._fixed_c_fit) > 0 or len(self._free_c_fit) > 0:
            # order of the _free_c_fit/_fixed_c_fit:
            # 
            #   linenumber
            #   comment
            #   timestamp
            #   raw position
            #   free fit  voltage/ fixed fit voltage
            order_list = {}
            order_list[Constants.RAW_FILE_OFFSET_COMMENT] = 1
            order_list[Constants.RAW_FILE_OFFSET_TIMESTAMP] = 2
            order_list[Constants.RAW_FILE_OFFSET_RAW_POSITION] = 3
            
            try:
                res = self.getRawFitResults()
                    
            except Exception:
                res = None
            
            fit_results = None
            if isinstance(res, (list, tuple)) and len(res) >= 2:
                fit_results = res[0]
                fit_results = tuple(fit_results)
            
            for i in range(0, max(len(self._free_c_fit), len(self._fixed_c_fit))):
                fixed_fit = ""
                free_fit = ""
                if i < len(self._free_c_fit):
                    row = self._free_c_fit[i]
#                    free_fit = row[4]
                    
                if i < len(self._fixed_c_fit):
                    row = self._fixed_c_fit[i]
#                    fixed_fit = row[4]
                
                row = [row[order_list[i]] for i in order_list]
                    
                # add processed voltage
                row.append("")
                
                # calculate free fit
                x = row[Constants.RAW_FILE_OFFSET_RAW_POSITION]
                if fit_results != None and my_utilities.is_numeric(x):
                    x = my_utilities.force_float(x)
                    parameters = (x,) + fit_results
                    free_fit = DataHandling.calculation.dipolfunction(*parameters)
                
                # add fits
                row.append(fixed_fit)
                row.append(free_fit)
                
                data.append(row)
        
        return data
    
    def isUpSweep(self):
        """Return True if the current data point is an up sweep, if it is a down
        sweep this returns False
        
        Returns
        -------
            boolean
                Whether the sweep is an up sweep or not
        """
        
        xdata, ydata = self.getPlotData(DataPoint.LINENUMBER, DataPoint.RAW_POSITION)
        
        # subtract the last position from the current
        ly = 0
        for index, y in enumerate(ydata):
            if index == 0:
                continue
            
            ydata[index] = y - ly
            ly = y
        
        # if (nearly) all the values are greater than 0 the last position is 
        # smaller than the current, this means that the sweep is down sweep
        # (x=24 is at the highest position of the probe)
        greater_zero = sum(1 for x in ydata if x > 0)
        
        # x position is measured from the bottom of the probe to the bottom of
        # the mpms, this means that an increasing x is an upsweep, a decreasing
        # x is a downsweep
        if greater_zero > len(ydata)/2:
            return True
        else:
            return False
    
    def calculateDerivation(self, x_axis, y_axis):
        """Calculate the derivation of the y_axis over the x_axis. The derviation
        will be a list with one point less than the data received from the 
        DataPoint.getPlotData(x_axis, y_axis). Each (x/y) point will contain the 
        linear derivation between the current point and the next point
        
        Parameters
        ----------
            x_axis : string
                The name of the data which should be used for the x axis
            y_axis : string
                The name of the data which should be used for the y axis
                
        Returns
        -------
            list, list
                The x and y data of the derviation, if the x_axis-y_axis combination
                is not allowed this will return None
        """
            
        result = self.getPlotData(x_axis, y_axis, True)
        xderivation = []
        yderivation = []
        
        if isinstance(result, (list, tuple)):
            xdata = result[0]
            ydata = result[1]
            
            for i, y in enumerate(ydata):
                if i < len(ydata) - 1 and i < len(xdata) - 1:
                    xderivation.append(xdata[i])
                    yderivation.append((ydata[i + 1] - y) / (xdata[i + 1] - xdata[i]))
            
            return xderivation, yderivation
        else:
            return None
    
    def makeSymmetric(self):
        """Makes the raw data of this datapoint to a symmetric function. This is
        done by subtracting the squid drift from form this datapoint.
        """
        
        # get the raw fit results
        try:
            res = self.getRawFitResults()
        except RuntimeError:
            res = None
            
        if res == None:
            raise RuntimeError(("The datapoint {} could not be made symmetric, the " + 
                               "datapoint could not be fitted so the squid drift " + 
                               "could not be detected").format(self._index))
        # dirft and y offset
        drift = res[0][1]
        y_offset = res[0][2]
        
        # subtract the drift and the y offset
        for i, row in enumerate(self._data_rows):
            if isinstance(row, (list, tuple)):
                self._data_rows[i] = tuple(
                             list(row[0:Constants.RAW_FILE_OFFSET_RAW_VOLTAGE]) + 
                             [row[Constants.RAW_FILE_OFFSET_RAW_VOLTAGE] - row[Constants.RAW_FILE_OFFSET_RAW_VOLTAGE] * drift - y_offset] + 
                             list(row[Constants.RAW_FILE_OFFSET_RAW_VOLTAGE + 1:-1]))
            else:
                # row is empty
                self._data_rows[i] = row
        
        # fit again so the fit is correct
        self.execFit()

    def cutRows(self, condition):
        """Removes all rows which do not match the given condition. The condition
        parameter has to be a list or tuple which contains dictionarys which have
        a min and/or a max index which define the minimum and/or maximum value.
        The key (or axis) index of the condition holds the value to check. Note
        that not all of them are supported! Only values that are included in the
        data_rows are allowed. Use the DataPoint Constants for definin which 
        value to check
        
        Parameters
        ----------
            condition : list
                List of condition dictionarys
        """
        
        conditions = []
        
        for cond in condition:
            if (isinstance(cond, (dict)) and (
                ("min" in cond and my_utilities.is_numeric(cond["min"])) or 
                ("max" in cond and my_utilities.is_numeric(cond["max"]))) and 
                ("key" in cond or "axis" in cond)):
                    
                cond = copy.copy(cond)
                
                if "axis" in cond and "key" not in cond:
                    cond["key"] = cond["axis"]
                
                if cond["key"] == DataHandling.DataPoint.DataPoint.LINENUMBER:
                    cond["key"] = 0
                elif cond["key"] == DataHandling.DataPoint.DataPoint.COMMENT:
                    cond["key"] = 1
                elif cond["key"] == DataHandling.DataPoint.DataPoint.TIMESTAMP:
                    cond["key"] = 2
                elif cond["key"] == DataHandling.DataPoint.DataPoint.RAW_POSITION:
                    cond["key"] = 3
                elif cond["key"] == DataHandling.DataPoint.DataPoint.RAW_VOLTAGE:
                    cond["key"] = 4
                elif cond["key"] == DataHandling.DataPoint.DataPoint.PROCESSED_VOLTAGE:
                    cond["key"] = 5
                elif cond["key"] == DataHandling.DataPoint.DataPoint.INDEX:
                    cond["key"] = -1
                else:
                    continue
                
                conditions.append(cond)
        
        rows = []
        
        for i, row in enumerate(self._data_rows):
            if row == DataHandling.DataPoint.DataPoint.EMPTY_ROW or not isinstance(row, (list, tuple)):
                continue
            
            matches = True
            for cond in conditions:
                if cond["key"] == -1:
                    check_value = i
                else:
                    check_value = row[cond["key"]]
                
                if (("min" in cond and check_value < cond["min"]) or 
                    ("max" in cond and check_value > cond["max"])):
                    matches = False
                    break
            
            if matches:
                rows.append(row)
        
        self._data_rows = rows
    
    def __deepcopy__(self, memo):
        """Implements the deepcopy interface, this prevents recursive infinite
        copying
        
        Parameters
        ----------
            memo : ??
                The memo
                
        Returns
        -------
            DataPoint
                The copy of this object
        """
        
        cls = self.__class__
        result = cls.__new__(cls)
        
        memo[id(self)] = result
        
        for k, v in self.__dict__.items():
            if k in ("_parent", "_environment_variables_unit_regexp"):
                setattr(result, k, v)
            else:
                setattr(result, k, copy.deepcopy(v, memo))
                
        return result