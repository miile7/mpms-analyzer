# -*- coding: utf-8 -*-
"""
Created on Wed Mar 14 16:14:37 2018

@author: miile7
"""

import scipy.optimize
import numpy as np
import warnings
import operator
import copy
import time

import DataHandling.DataContainer
import DataHandling.DataPoint
import my_utilities
import Constants

def dipolfunction(x, A = -1, B = 0, C = 0, D = 0):
    """Create a dipol function f(x) = dipulfunction(x). The parameters A, B, C and
    D are fitting parameters: A describes the amplitude of the function, B is a
    linear function added to the dipolfunction. In this program this is caused by
    the linear SQID drive. The C is a constant offset in the y axis, D is a x
    offset of the peak centre
    
    Parameters
    ----------
        x : float
            The x axis values
        A : float
            The amplitude of the dipol funciton
        B : float
            The linear part in the dipol function
        C : float
            The constant y offset in the dipol function
        D : float
            The constant x offset in the dipol function
            
    Returns
    -------
        float
            The y value for the given x value with the parameters A, B, C and D
    """
    
    radius = 8.3654 # Spulenradius
    space  = 7.960  # Spulenabstand  
    posint = 1.0 * (x - D) #30.8, relative Position bezogen auf das Peakzentrum  
    
    x1 = singleturn(radius,-space, posint) # der Uebersichtlichkeit halber in separater funktion 'singleturn' ermittelt
    x2 = singleturn(radius,     0, posint)
    x3 = singleturn(radius, space, posint)
    
    return A * ((-x1 + 2*x2 - x3)) + B * posint + C # fuer Dipol ermittelter, theoretischer Spannungsverlauf   

def singleturn(cradius, cspace, z):
    """Singleturn method for the dipolfunction, this is used for creating the
    dipol funciton only
    """
    
    return cradius**2 / pow(cradius**2 + (z-cspace)**2.0, 1.5)

def datapointFit(xdata, ydata, squid_range):
    """Fit the xdata and ydata to the dipolfunction. This function will be called
    in the DataHandling.DataContainer when fitDataPoints() function is being called.
    
    Parameters
    ----------
        xdata, ydata: list of float
            The x and y data as a list
        squid_range: int
            The squid range for the given datapoint
            
    Returns
    -------
        float, float, list, list
            The magnetization in emu, the error of the magnetization in emu,
            the result array for all the fit parameters, the errorrs for every
            fit parameter
    """
    
#    result, errors = scipy.optimize.curve_fit(dipolfunction, xdata, ydata, p0=[-1.0, 0.0001, 0.0001, 35])
    result, errors = scipy.optimize.curve_fit(dipolfunction, xdata, ydata, p0=[
            Constants.FIT_STARTING_AMPLITUDE,
            Constants.FIT_STARTING_DRIFT,
            Constants.FIT_STARTING_Y,
            Constants.FIT_STARTING_X],
            bounds=((Constants.FIT_LOWER_BOUND_AMPLITUDE,
                     Constants.FIT_LOWER_BOUND_DRIFT,
                     Constants.FIT_LOWER_BOUND_Y,
                     Constants.FIT_LOWER_BOUND_X
                     ),
                     (Constants.FIT_UPPER_BOUND_AMPLITUDE,
                      Constants.FIT_UPPER_BOUND_DRIFT,
                      Constants.FIT_UPPER_BOUND_Y,
                      Constants.FIT_UPPER_BOUND_X
                     )))
    
#    print("calculation.datapointFit(): squid_range: ", squid_range)
    
    # the errors contains the variances in the diagonal, the standard diviation
    # is the square root of those errors
    errors = np.sqrt(np.diag(errors))
    
    # calculate magnetization and error
    magnetization_factor = -0.00285897 * 14.7029 * squid_range / 1000
    magnetization = magnetization_factor * result[0]
    magnetization_error = magnetization_factor * errors[0]
    
    # parse the results, the errors are in the diagonal of the reutrned array
    # result form is: magnetization, error of magnetization, all the fit results
    # the errors for each fit result
    return (magnetization, magnetization_error, result, errors)

def subtractBackgroundData(xdata, ydata, squid_range, xbackground_data, ybackground_data, background_squid_range, debug_messages=False):
    """Subtract the ybackground_data from the ydata. The xdata and ydata are
    the data of the original datapoint, the xbackground_data and ybackground_data
    are the background data for this datapoint
    
    Parameters
    ----------
        xdata, ydata : list of float
            The x and y data as a list
        squid_range : float
            The squid range of original data
        xbackground_data, ybackground_data : list of float
            The x and y data of the background as a list
        background_squid_range : float
            The squid range of the backgroun data
            
    Returns
    -------
        list of float, list of float
            The x and y data for the datapoint with subtracted background
        list of tuples
            A list which tells how the subtraction has been done
        tuple of strings
            The names of the axis
    """
    
    # This holds all the values that are used for the remove. This means that
    # the remove_values list should contain a tuple where index 0 is the x 
    # value, index 1 is the original y value including the background, 
    # index 2 is the background y value and index 3 is the result y value
    #   remove_values[i][0] : x value
    #   remove_values[i][1] : y value including the background (the original data)
    #   remove_values[i][2] : y value of the background
    #   remove_values[i][3] : y value of the result (after the subtraction)
    remove_values = []
    
    # pepare return x and y data
    rx = []
    ry = []
    squid_range = my_utilities.force_float(squid_range)
    background_squid_range = my_utilities.force_float(background_squid_range)
    
    if debug_messages:
        l = 70
        bys = []
    
    counter = 0
    for x, y in zip(xdata, ydata):
        # parse the real data x and y to a float
        x = my_utilities.force_float(x)
        y = my_utilities.force_float(y) * squid_range
        
        # append the x value to the return x values
        rx.append(x)
        
        if counter >= 0 and counter < len(ybackground_data):
            by = ybackground_data[counter]
        else:
            by = 0
        
        try:
            by = my_utilities.force_float(by) * background_squid_range
        except (ValueError, TypeError):
            by = 0
            
        if debug_messages:
            bys.append(by)
        
        # subtract the background from the real original y and save it to the return value
        result_y = y - by
        ry.append(result_y)
        counter += 1
        
        # add the values for the removing
        remove_values.append((counter, y, by, result_y))
    
    if debug_messages:
        print("Calculating new y data by using <original data> - <background data> = <result data>")
        cols = 3
        
        print(("{: ^" + str(l/cols - 1) + "}").format("original data") + "|" + 
              ("{: ^" + str(l/cols - 1) + "}").format("background data") + "|" + 
              ("{: ^" + str(l/cols - 0) + "}").format("result data"))
        
        for index, y_original in enumerate(ydata):
            y_original = round(y_original, 5)
            y_background = round(bys[index], 5)
            y_result = round(ry[index], 5)
            print(("{: ^" + str(round(l/cols - 1)) + "}").format(y_original) + "|" + 
                  ("{: ^" + str(round(l/cols - 1)) + "}").format(y_background) + "|" + 
                  ("{: ^" + str(round(l/cols - 1)) + "}").format(y_result))
#    
#    plt.figure()
#    plt.plot(rx, ry, label="result data")
#    plt.plot(xdata, ydata, label="original data")
#    plt.plot(xbackground_data, ybackground_data, label="background data")
#    plt.legend()
    
    return rx, ry, remove_values, ("index", "raw voltage [V]")

def extendBackgroundData(original_data, background_data, mode, index_list, original_datacontainer, background_datacontainer):
    """Extend the background data. This function will be called if the data
    (with the background) has not the same length as the background data. This
    function should return a background data which has the same length like the
    original data (with background).
    
    The original_data and the background_data are lists which contain a tuple 
    of the x and y raw data of each datapoint. They look like this:
        *_data = [
            ([x1, x2, x3, ..., xn], [y1, y2, y3, ..., yn]), # this is one swipe
            ...
        ].
    The xn are the raw position data, the yn are the raw voltage data. The squid
    range is not applied! Do not multiply the squid range, the calculation.subtractBackgroundData()
    function is being executed right after this function.
    
    The mode defines how the missing values in the background data should be 
    created. The modes are defined in the Constants in the BACKGROUND_INCREASE_MODES
    list.
    
    The index_list is a list which contains all the indices (of the background data) 
    that should be used
    
    If you need more information you can use the original_datacontainer and the
    background_datacontainer. They both are DataHandling.DataContainer.DataContainer
    objects which old **all** information that the raw file (and the dat file)
    hold. If you need information about the temperature, field, squid range or 
    anything like this check out the DataContainer class and ignore the *_data 
    lists
    
    Parameters
    ----------
        original_data, background_data : list of tuples of lists
            A list which contains tuples which contain the x and y data of one
            swipe as a list, the x data is the raw position, the y data is the
            raw voltage, the original_data contains the data with background, 
            the background_data contains the background only
        mode : String
            The name of the mode, the modes are defined in the Constants file
        index_list : list of ints
            A list which contains the indices (of the background data) which 
            swipes should be used and which should not
        original_datacontainer, background_datacontainer : DataContainer
            The datacontainer for the original data (with background) and the 
            background data, those contain the original_data and the
            background_data but they also have a lot more information about each
            swipe
    Returns
    -------
        list of tuples of lists
            The background data list in the same shape as the original_data/
            background_data, this has to have the same length (= number of swipes
            = `len(<return value>)`) as the original_data
    """
    # the number of values that are missing (so the number of values that should
    # be added to the background data)
    number_missing_values = len(original_data) - len(background_data)
    
    # background data has more entries than the original data, just return the
    # part to use
    if number_missing_values < 0:
        return background_data[0:len(original_data)]
    elif number_missing_values == 0:
        return background_data
    
    # the background data which is allowed to use for extending the data
    usable_background_data = []
    
    # check the index_list, this will create the usable_background_data list to
    # contain the allowed indices only
    if isinstance(index_list, (list, tuple)):
        # go through the index list
        for index in index_list:
            # check if the index exists, if it does copy the value to the usable
            # backgroun data
            if index >= 0 and index < len(background_data):
                usable_background_data.append(background_data[index])
    else:
        # the index list is not valid, use all background data, **copy** the data,
        # this is very important, otherwise the background_data will be changed 
        # too
        usable_background_data = background_data[:]
    
    # prepare the result
    result = background_data
    
    if mode == "mirror":
        # the number of times the background data can be added completely (like
        # in the repeat mode)
        add_total = number_missing_values // len(usable_background_data)
        
        # go through the total number and reverse the background data each time,
        # this will make the function periodic and smooth
        for i in range(0, add_total):
            usable_background_data.reverse()
            result += usable_background_data
        
        # the reverse the background again
        usable_background_data.reverse()
        # then add the remaining number of values
        result += usable_background_data[0:(number_missing_values % len(usable_background_data))]
    else:
        # repeat mode, this means that the background data should be added to 
        # the end of the background just like it is
        
        # increase the result with the **full** allowed background data list
        # as much as possible
        result += usable_background_data * (number_missing_values // len(usable_background_data))
        # then add the remaining number of values
        result += usable_background_data[0:(number_missing_values % len(usable_background_data))]
    
    # return the result
    return result

def createBackgroundDataContainer(datacontainer, background_datacontainer, measurement_type, background_filepath, controller):
    """Create a new background DataContainer which is the exact background 
    measurement for the given datacontainer. The values of the given background_datacontainer
    will be inter-/extrapolated so that there is exactly one point for the given
    datacontainer values
    
    Parameters
    ----------
        datacontainer : DataContainer
            The datacontainer to create the background measurement of
        background_datacontainer : DataContainer
            The datacontainer for the background measurement which contains the
            background partly, this is used to interpolate (linear) to create
            the correct background values
        measurement_type : String
            The type of the measurement, use DataContainer.TEMPERATURE for a 
            M(T) measurement, use DataContainer.FIELD for a M(H) measurement
        background_filepath : String
            The filepath for displaying in the new datacontainer as its origin,
            this can be anything but it should be descriptive to the user
            
    Returns
    -------
        DataContainer
            A new datacontainer which is the background measurement for the given
            datacontainer
    """
    
    # clone the background datacontainer
    new_background = copy.deepcopy(background_datacontainer)
    new_background.filepath = background_filepath
    new_background.datapoints = []
    
    new_background.addAttribute("Interpolated background")
        
    # receive the column names and units
    column_names = background_datacontainer.datapoints[0].column_names
    column_units = background_datacontainer.datapoints[0].column_units
    
    # find the opposite type, this is the staic
    if measurement_type == DataHandling.DataContainer.DataContainer.TEMPERATURE:
        static_type = DataHandling.DataContainer.DataContainer.FIELD
    elif measurement_type == DataHandling.DataContainer.DataContainer.FIELD:
        static_type = DataHandling.DataContainer.DataContainer.TEMPERATURE
        
    # the keys to replace in the environment variable dict
    replace_keys = getEnvironmentVariableReplaceKeys(measurement_type)
        
    static_name = static_type
    if static_type in Constants.ENVIRONMENT_VARIABLE_NAMES:
        static_name = Constants.ENVIRONMENT_VARIABLE_NAMES[static_type]
    measurement_name = measurement_type
    if measurement_type in Constants.ENVIRONMENT_VARIABLE_NAMES:
        measurement_name = Constants.ENVIRONMENT_VARIABLE_NAMES[measurement_type]
    
    # get the list to interpolate the values in, the index 0 contains the measurement
    # type value to interpolate as x (e.g. temperature), the index 1 contains
    # the x and y data for each datapoint, index 2 contains the environment variables
    interpolation_ranges = createInterpolationRanges(background_datacontainer, measurement_type, controller)
    
#    print("BackgroundCreation_old.createBackgroundDataContainer(): len(interpolation_ranges):", len(interpolation_ranges), "\nkeys:")
#    for key in interpolation_ranges:
#        print("{}: {}".format(key, len(interpolation_ranges)))
        
    # "fake" linenumber, setting to 30
    linenumber = 30
        
    # go through each datapoint
    for dp_index, datapoint in enumerate(datacontainer.datapoints):
        # the static value, for a M(T) measurement this is the H field
        static_value = datapoint.getEnvironmentVariableAvg(static_type)
        static_unit = datapoint.getEnvironmentVariablesUnit(static_type)
        
        if isinstance(static_value, (list, tuple)):
            # get the target static variable
            static_value = static_value[0]
            
            # get the interpolation values for the up and down sweep for this
            # static value (e.g. for this field for a M(T) measurement)
            interpolation_values_up, interpolation_values_down = getInterpolationValues(
                    interpolation_ranges,
                    static_value,
                    static_unit,
                    static_type)
            
            # create a map, this is for fast access, the indices are the same but this
            # contains the measurement type value only (e.g. temperature)
            interpolation_map_up = [i[0] for i in interpolation_values_up]
            interpolation_map_down = [i[0] for i in interpolation_values_down]
            
            if datapoint.isUpSweep():
                interpolation_map = interpolation_map_up
                interpolation_values = interpolation_values_up
            else:
                interpolation_map = interpolation_map_down
                interpolation_values = interpolation_values_down
            # create new datapoint
            background_datapoint = DataHandling.DataPoint.DataPoint(new_background, dp_index)
            # save the column names and units in the new datapoint
            background_datapoint.column_names = column_names
            background_datapoint.column_units = column_units
            
            # get the target x value to interpolate to
            val = datapoint.getEnvironmentVariableAvg(measurement_type)
            
            # check if the value exists
            if isinstance(val, (list, tuple)):
                # index 0 holds the value, index 1 holds the standard diviation
                val = my_utilities.force_float(val[0])
                # get the index in the map, i is the index of the first value that
                # is **bigger** than the val
                i = 0
                while i < len(interpolation_map) and interpolation_map[i] < val:
                    i += 1
                
                if i == 0:
                    # if this is the first element extrapolate
                    result = extrapolate(True, val, i, interpolation_values)
                elif i == len(interpolation_map):
                    # if this is the last element extrapolate
                    result = extrapolate(False, val, i, interpolation_values)
                    i = len(interpolation_map) - 1
                else:
                    # just any element, interpolate between this and the next point
                    result = interpolate(val, i, interpolation_values)
                    
                # add the environment variables, they are used for DataContainer 
                # plotting so they are very important
                if (i >= 0 and i < len(interpolation_map) and
                    isinstance(interpolation_values[i], (list, tuple)) and 
                    len(interpolation_values[i]) >= 3 and
                    isinstance(interpolation_values[i][2], (list, tuple))):
                    # go through each dict
                    for j, environment_variables in enumerate(interpolation_values[i][2]):
                        if isinstance(environment_variables, dict):
                            # the measurement type e.g. the temperature is saved in
                            # the environment variable so this has to be changed to
                            # the value which was interpolated. This is very important,
                            # otherwise there will be a correct interpolation but 
                            # the program will not know about it
                            for key in replace_keys:
                                if key in environment_variables:
                                    unit = datapoint.getEnvironmentVariablesUnit(key, j)
                                    environment_variables[key] = str(val) + unit
                                
                            background_datapoint.addEnvironmentVariables(environment_variables, linenumber)
                            linenumber += 1
                
                # "fake" timestamp
                timestamp = time.time()
                # processed voltage is not saved
                processed_voltage = 0
                
                # add the data row in the same order that it is in the raw file
                for raw_position, raw_voltage in result:
                    background_datapoint.addDataRow(
                            raw_position, 
                            raw_voltage, 
                            processed_voltage, 
                            linenumber, 
                            timestamp,
                            "")
                    
                    # increase the linenumber
                    linenumber += 1
            else:
                warnings.warn(("The {} (control variable) is not defined in datapoint " + 
                              "#{} (average environment variable returned {}). This " + 
                              "datapoint will be skipped").format(
                              measurement_name, dp_index, val))
            
            # add the datapoint
            new_background.datapoints.append(background_datapoint)
        else:
            warnings.warn(("The {} (static variable) is not defined in datapoint " + 
                          "#{} (average environment variable returned {}). This " + 
                          "datapoint will be skipped").format(
                          static_name, dp_index, static_value))
    
    # return the created background
    return new_background

def getEnvironmentVariableReplaceKeys(measurement_type):
    """Returns the keys depending on the measurement_type which keys in the 
    environment variables dict should be replaced
    
    Parameters
    ----------
        measurement_type : String
            The type of the measurement, use DataContainer.TEMPERATURE for a 
            M(T) measurement, use DataContainer.FIELD for a M(H) measurement
            
    Returns
    -------
        list of String
            The keys to replace
    """
    
    replace_keys = [measurement_type]
    
    if measurement_type == DataHandling.DataContainer.DataContainer.TEMPERATURE:
        replace_keys += [DataHandling.DataContainer.DataContainer.LOW_TEMPERATURE,
                         DataHandling.DataContainer.DataContainer.HIGH_TEMPERATURE]
    elif measurement_type == DataHandling.DataContainer.DataContainer.FIELD:
        replace_keys += [DataHandling.DataContainer.DataContainer.LOW_FIELD,
                         DataHandling.DataContainer.DataContainer.HIGH_FIELD]
    
    return replace_keys

def getInterpolationValues(interpolation_ranges, static_value, static_unit, static_type):
    """Returns the list of the interpolation x value (of the measurement_type) and
    the x and y data to interpolate depending on the interpolation ranges and 
    the static target value.
    
    Paramters
    ---------
        interpolation_ranges : dict
            The interpolation ranges dict created by the createInterpolationRanges
            function
        static_value : float
            The target static value (e.g. the static field)
        static_unit : String
            The unit of the static value
        static_type : String
            The key which variable is the static variable, this is the "opposite" 
            of the createBackgroundDataContainer()s measurement_type parameter,
            use DataContainer.FIELD for a M(T) measurement with static field(s), 
            use DataContainer.TEMPERATURE for a M(H) measurement with static 
            temperature(s)
            
    Returns
    -------
        list, list
            The interpolation list for the up and for the down sweep
    """
    
    # the map for the static values, this holds all static variable values (e.g.
    # the field for a M(T) measurement) that the background
    static_values_map = list(interpolation_ranges.keys())
    # the threshold for the static variable when to treat a value as a new 
    # static value, this defines the error tolerance
    static_threshold = abs(min(static_values_map) / Constants.STATIC_VALUE_THRESHOLD)
    
    # the closest supported static value 
    closest_static = min(static_values_map, key=lambda x: abs(x - static_value))
    
#    print("BackgroundCreation_old.getInterpolationValues(): closest_static:", closest_static, 
#          ", abs(closest_static - static_value):", abs(closest_static - static_value), ", static_threshold:", static_threshold)
    
    # check if it is in the threshold
    if abs(closest_static - static_value) > static_threshold:
#        print("BackgroundCreation_old.getInterpolationValues(): interpolating {}".format(static_type))
        
        prev_closest_static = None
        next_closest_static = None
        
        # sort for next/previous detection
        static_values_map.sort()
        
        # check whether the static variable should be interpolated too
        if Constants.INTERPOLATE_STATIC_VARIABLE:
            # find the index of the closest value
            closest_static_index = static_values_map.index(closest_static)
            
            # check if it is before or after the static value, find the next higher
            # static vlaue and the next lower static value
            if closest_static < static_value and closest_static_index + 1 < len(static_values_map):
                prev_closest_static = closest_static
                next_closest_static = static_values_map[closest_static_index + 1]
            elif closest_static_index > 0:
                prev_closest_static = static_values_map[closest_static_index - 1]
                next_closest_static = closest_static
            else:
                prev_closest_static = None
                next_closest_static = None
            
#            print("BackgroundCreation_old.getInterpolationValues(): " + 
#                  "target (static_value): ", static_value,
#                  "\nprev_closest_static: ", prev_closest_static,
#                  "\nnext_closest_static: ", next_closest_static)
            
            # if there is only one static range (so e.g. only one field is measured)
            # it is not possible to iterate, skip and use the only existing data
            if prev_closest_static != None and next_closest_static != None:
                # prepare the interpolation_ranges dict and add the new static
                # range, index 0 is up sweep, index 1 is down sweep
                interpolation_ranges[static_value] = [[], []]
                
                # prepare replacing the environment variable for the static type,
                # the replace_keys holds the keys which to replace
                replace_keys = getEnvironmentVariableReplaceKeys(static_type)
                
                # prepare the unti of the static variable
                if not isinstance(static_unit, str):
                    static_unit = ""
                
                # go through the previous values
                for sweep_type, prev_interpolation_values in enumerate(interpolation_ranges[prev_closest_static]):
                    # The map for the next interpolation values, this contains a
                    # list of the measurement variables (e.g. the temperature) in
                    # the next static range (e.g. the next higher field).
                    next_interpolation_values_map = [i[0] for i in interpolation_ranges[next_closest_static][sweep_type]]
                    
#                    print("BackgroundCreation_old.getInterpolationValues(): " + 
#                          "\nprev_interpolation_values: ", prev_interpolation_values,
#                          "\nnext_interpolation_values_map: ", next_interpolation_values_map,
#                          "\ninterpolation_ranges[next_closest_static][sweep_type]: ", interpolation_ranges[next_closest_static][sweep_type])
                    
                    # go through the interpolation values of the previous point
                    for prev_measurement_value, prev_xydata, prev_environment_variables in prev_interpolation_values:
                        # get the closest measurement value of the next point
                        closest_measurmement_value = min(next_interpolation_values_map, 
                                                         key=lambda x: abs(x - prev_measurement_value))
                        # the corresponding index
                        closest_measurement_value_index = next_interpolation_values_map.index(closest_measurmement_value)
                        
                        # the interpolation values for the next point, this is a 
                        # list where index 0 contains the measurement varaible
                        # e.g. the temperature, the index 1 contains the 
                        # x and y data to interpolate, the index 2 contains
                        # the environment variables
                        next_interpolation_values = interpolation_ranges[next_closest_static][sweep_type][closest_measurement_value_index]
                        
                        # split for better looks
                        next_measurement_value = next_interpolation_values[0]
                        next_xydata = next_interpolation_values[1]
                        next_environment_variables = next_interpolation_values[2]
                        
                        # create a fake interpoltion tuple, this contains only
                        # two points, between those two points there will be 
                        # interpolated.
                        # Both points are at one specific value of the measurement
                        # type (e.g. the temperature), the first point is lower
                        # in the static vairable (e.g. the field), the second
                        # is higher. The x and y data will now be interpolated
                        # between those two points to get new x/y data for the
                        # new static value range
                        static_interpolation_values = (
                                (prev_measurement_value, prev_xydata, prev_environment_variables),
                                (next_measurement_value, next_xydata, next_environment_variables)
                                )
                        
                        # interpolate
                        result = interpolate(static_value, 1, static_interpolation_values)
                        
                        # replace the environment variable to let the program
                        # knwo that those values have a different static type
                        for key in replace_keys:
                            for env_vars in prev_environment_variables:
                                if key in env_vars:
                                    print(key)
                                    prev_environment_variables[key] = str(static_value) + static_unit
                        
                        # create the interpolation value row
                        row = (prev_measurement_value, result, prev_environment_variables)
                        
                        # add the row to the new static value range
                        interpolation_ranges[static_value][sweep_type].append(row)
                
                # re-set the closest staic value, the closest is now the value 
                # itself
                closest_static = static_value
        
        # interpolating is not allowed or not possible, write a warning
        if not Constants.INTERPOLATE_STATIC_VARIABLE or prev_closest_static == None or next_closest_static == None:
            static_name = static_type
            
            if static_type in Constants.ENVIRONMENT_VARIABLE_NAMES:
                static_name = Constants.ENVIRONMENT_VARIABLE_NAMES[static_type]
            
            warnings.warn(("The interpolation requires measurement data with a {0} of " + 
                           "{1} but the next closest {0} is {2}. The interpolation " + 
                           "useses this {0} now but this may cause wrong results.").format(
                                   static_name, closest_static, static_value))
    
    # return the interpolation data
    return interpolation_ranges[closest_static][0], interpolation_ranges[closest_static][1]

def createInterpolationRanges(background_datacontainer, measurement_type, controller):
    """Returns a sorted list for the given background_datacontainer and measurement_type.
    
    This will return a dictionary where the indices are the variables that are not
    the measurement_type. If the measurement_type is the temperature there will
    be all measured (static ranges) of the field as the key.
    
    Each static range index of the dict will hold a list which has two indices,
    the first index holds the interpolation values for the up sweeps, the second 
    holds the values for the down sweep interpolation.
    
    The interpolation values is a list which holds the interpolation x value of
    the measurement_type (e.g. the temperature) in the first index, the second
    will hold a list with the x and y data to interpolate (only interpolate the
    y data). The thrid index is the environment variables of this point.
    
    If the measurement_type is the temperature the return value could look like t
    this:
    {
        1000 Oe => [
            0 (= up sweep data): [
                    300 K,
                    [<raw position = x values>, <raw voltage = y values>],
                    <environment variables
            ],
            1 (= down sweep data): [
                    300 K,
                    [<raw position = x values>, <raw voltage = y values>],
                    <environment variables
            ]
        ]
    }
            
    Note:
        The environment variables are the x/y values of the interpolating so the 
        measurement_type is a key in the environment variables. This has to be
        corrected when interpolating!
        
    Parameters
    ----------
        background_datacontainer : DataContainer
            The datacontainer for the background
        measurement_type : String
            The type of the measurement, use DataContainer.TEMPERATURE for a 
            M(T) measurement, use DataContainer.FIELD for a M(H) measurement
            
    Returns
    -------
        list
            The sorted list in the form mentioned above
    """
    
    # the result list
    result = {}
    
    # the measurmenet type and the static variable
    if measurement_type == DataHandling.DataContainer.DataContainer.TEMPERATURE:
        static_variable = DataHandling.DataContainer.DataContainer.FIELD
    else:
        static_variable = DataHandling.DataContainer.DataContainer.TEMPERATURE
    
    static_name = static_variable
    if static_variable in Constants.ENVIRONMENT_VARIABLE_NAMES:
        static_name = Constants.ENVIRONMENT_VARIABLE_NAMES[static_variable]
    
    # get all the static values, this is plotted over the timestamp because there
    # always is a timestamp
    static_data = []
    for datapoint in background_datacontainer.datapoints:
        value = datapoint.getEnvironmentVariableAvg(static_variable)
#        print("BackgroundCreation_old.createInterpolationRanges(): value:", value)
        if isinstance(value, (list, tuple)):
            static_data.append(my_utilities.force_float(value[0]))
    
    # calculate the threshold
    threshold = abs(min(static_data) / Constants.STATIC_VALUE_THRESHOLD)
    
    # get the ranges of the static variable
    ranges, full_list = controller.uniqueListThreshold(static_data, threshold)
    
    # go through each datapoint
    for dp_index, datapoint in enumerate(background_datacontainer.datapoints):
        # the range selector
        value = datapoint.getEnvironmentVariableAvg(static_variable)
        if isinstance(value, (list, tuple)):
            range_selector = my_utilities.force_float(value[0])
        else:
            range_selector = None
            
        range_value = None
        
        # find the real value that this datapoint has
        for range_val in full_list:
            if range_selector in full_list[range_val]:
                range_value = range_val
                break
        
        if range_value == None:
            # this is not possible to happen, the full list contains ALL values!
            warnings.warn(("The {} = {} defined in the datapoint #{} of the " + 
                          "background data is not listed in the range list. This " + 
                          "is a severe error which has no solution.").format(
                                  static_name, range_selector, dp_index))
            continue
        
        # prepare the result
        if not range_value in result:
            result[range_value] = [[], []]
        
        # get the value
        val = datapoint.getEnvironmentVariableAvg(measurement_type)
        
        if isinstance(val, (list, tuple)):
            # the plot data
            data = datapoint.getPlotData(
                    DataHandling.DataPoint.DataPoint.RAW_POSITION,
                    DataHandling.DataPoint.DataPoint.RAW_VOLTAGE,
                    True
                    )
            
            # check if there is some data
            if isinstance(data, (list, tuple)) and len(data) >= 2:
                # add the data
                row = (val[0], data[0:2], datapoint.getEnvironmentVariables())
                
                if datapoint.isUpSweep():
                    result[range_value][0].append(row)
                else:
                    result[range_value][1].append(row)
#            else:
#                print("BackgroundCreation_old.createInterpolationRanges(): data is not a tuple or list")
#        else:
#            print("BackgroundCreation_old.createInterpolationRanges(): val is not a tuple or list")
    
    for key in result:
        # sort by the measurement type variable
        result[key][0].sort(key=operator.itemgetter(0))
        result[key][1].sort(key=operator.itemgetter(0))
    
    return result

def interpolate(target_x, index, interpolation_values):
    """Interpolate to find the target_x between the index and the index-1 values 
    in the interpolation_values list. The interpolation_values list has to have
    the format returned by the createInterpolationRanges() function!
    
    Parameters
    ----------
        target_x : float
            The x value to interpolate to
        index : int
            The first index where the corresponding value is bigger than the value
            to interpolate to
        interpolation_values : list
            The datapoint values to interpolate in
            
    Returns
    -------
        list
            The list of the x and y (raw) values for the given target_x
    """
    
    # the x2/y2 coordinate, y2 is a list because y is one whole datapoint with
    # x and y values. The y values will be interpolated, the x values do not change,
    # they are just kept for creating a valid datapoint again
    x2 = interpolation_values[index][0]
    y2_values = interpolation_values[index][1]
    
    # the x1/y1 coordinate
    i = index - 1
    while i >= 0 and i < len(interpolation_values) and interpolation_values[i][0] == x2:
        i -= 1
    x1 = interpolation_values[i][0]
    y1_values = interpolation_values[i][1]
    
    
    # the max count
    count = max(len(y1_values[0]), len(y1_values[1]), len(y2_values[0]), len(y2_values[1]))
    # the result
    result = []
    
    # go through each of the ~200 raw position/raw voltage points
    for i in range(0, count):
        if i < len(y1_values[1]) and i < len(y2_values[1]):
            # the slope and the y intercept
            m = (y2_values[1][i] - y1_values[1][i]) / (x2 - x1)
            t = y1_values[1][i] - m * x1
            
            # the resulting y value for the target_y
            y = m * target_x + t
        elif i < len(y1_values):
            y = y1_values
        elif i < len(y2_values):
            y = y2_values
        else:
            continue
        
        # get the x value, normally this should be the y2 value because this is 
        # interpolating with the slope of the target point and the point before
        # but if it is not possible use the point before. There are ~200 points
        # on a distance of ~4cm, it does not matter if there is a shift of one
        # point or not
        if i < len(y2_values[0]):
            x = y2_values[0][i]
        elif i < len(y1_values[1]):
            x = y2_values[1][i]
        else:
            x = None
        
        # add the result
        if x != None and y != None:
            result.append((x, y))
    
    # the result
    return result

def extrapolate(extrapolate_beginning, target_x, index, interpolation_values):
    """Extrapolating the values, this is only used for the beginning and the end
    of the datapoints. This will return the values given by te getInterpolateValues()
    function with passing the first two or the last two points for determining
    the slope
    
    Parameters
    ----------
        extrapolate_beginning : boolean
            Whether the extrapolating is in the beginning or in the end
        target_x : float
            The x value to interpolate to
        index : int
            The first index where the corresponding value is bigger than the value
            to interpolate to
        interpolation_values : list
            The datapoint values to interpolate in
            
    Returns
    -------
        list
            The list of the y values for the given target_x
    """
    
    if extrapolate_beginning:
        # use the first two datapoints to get the slope
        return interpolate(target_x, index + 1, interpolation_values)
    else:
        # use the last two datapoints for calculating the slope
        return interpolate(target_x, index - 1, interpolation_values)