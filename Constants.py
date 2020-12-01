# -*- coding: utf-8 -*-
"""
Created on Tue Oct 17 12:19:36 2017

@author: Maximilian Seidler
"""

import numpy as np

# indicates that there is an error but the error is only important for debugging
# reasons
DEBUG = -1

# indicates that there is a fatal error which will make the program not work
# properly
FATAL = 0

# indicates that there is an error which should be displayed in an error message
# to the user but this error is not fatal
NOTICE_ERROR = 1

# indicates that there is an error which should be noticed but it will not 
# affect the users experiance
NOTICE = 2

# fit starting values
FIT_STARTING_AMPLITUDE = 0.0
FIT_STARTING_DRIFT = 0.0001
FIT_STARTING_Y = 1
FIT_STARTING_X = 30
# fit lower bounds
FIT_LOWER_BOUND_AMPLITUDE = -np.inf
FIT_LOWER_BOUND_DRIFT = -np.inf
FIT_LOWER_BOUND_Y = -np.inf
FIT_LOWER_BOUND_X = 25
# fit upper bounds
FIT_UPPER_BOUND_AMPLITUDE = np.inf
FIT_UPPER_BOUND_DRIFT = np.inf
FIT_UPPER_BOUND_Y = np.inf
FIT_UPPER_BOUND_X = 37.5

# the map for the raw data where each line is
RAW_FILE_OFFSET_COMMENT = 0
RAW_FILE_OFFSET_TIMESTAMP = 1
RAW_FILE_OFFSET_RAW_POSITION = 2
RAW_FILE_OFFSET_RAW_VOLTAGE = 3
RAW_FILE_OFFSET_PROCESSED_VOLTAGE = 4
RAW_FILE_OFFSET_FIXED_C_FIT = 5
RAW_FILE_OFFSET_FREE_C_FIT = 6

# the map for the environment variable names
ENVIRONMENT_VARIABLE_NAMES =  {
        "low temp": "low temperature",
        "high temp": "high temperature",
        "avg. temp": "average temperature",
        "low field": "low field",
        "high field": "high field",
        "avg. field": "average field",
        "field": "average field",
        "drift": "drift",
        "slope": "slope",
        "given center": "given center",
        "calculated center": "calculated center",
        "amp fixed": "fixed center fit amplitude",
        "amp free": "free center fit amplitude",
        }

# the log constants
LOG_STATUS_BAR = 0b001
LOG_CONSOLE = 0b010
LOG_DEBUG = 0b100

# the name and the organization
NAME = "MPMS Analyzer"
COMPANY = "Universitaet Augsburg"
VERSION = "1.0"

# there have to be at least TEMPERATURE_MIN_DEVIATION_COUNT temperatures that 
# differ by TEMPERATURE_THRESHOLD Kelvin to display the temperature as a range
TEMPERATURE_THRESHOLD = 5
TEMPERATURE_MIN_DEVIATION_COUNT = 5

# same for the field
FIELD_THRESHOLD = 5
FIELD_MIN_DEVIATION_COUNT = 5

# The factor that the background and the original measurement environment variables
# can differ. This is calculated in each datapoint while subtracting the data for 
# checkig if this background datapoint is for this original datapoint. The calculation
# is done like:
#   a = abs(original_measurement_temp - background_measurement_temp)
#   m = max(original_measurement_temp, background_measurement_temp)
# allowed if 
#   a > m * MAXIMUM_DIVIATION_BACKGROUND_ENVIRONMENT
# if this is not the case a warning will be displayed but the subtraction will still
# be performed
MAXIMUM_DIVIATION_BACKGROUND_ENVIRONMENT = 0.01

# the threshold ratio to define if one parameter is mesured with an constant other
# parameter. This is used in the GraphWizard to decet whether for example the
# temperature is measured with static field (ranges) or the field is measured with 
# static temperature (ranges). Therefore the different x (for example temperature)
# values and the different y values (for example field) will be detected using the
# STATIC_VALUE_THRESHOLD. The ratio of x values to y values will be calculated, 
# if it is lower 1 - PLOT_STATIC_OVER_VARIABLE_RATIO the x values will be assumed
# to be static, if the value is greater than 1 + PLOT_STATIC_OVER_VARIABLE_RATIO
# the y values will be assumed to be static.
PLOT_STATIC_OVER_VARIABLE_RATIO = 0.2
# This holds the threshold which tells whether the value is still the same envrionment
# variable or not.
# This means that two temperatures t1 = 100.00 and t2 = 100.01 will be the same 
# because min(t1, t2) / STATIC_VALUE_THRESHOLD = 0.1 but abs(t1 - t2) < 0.1 
# This is used in the GraphWizardFormatPage and the BackgroundCreation
STATIC_VALUE_THRESHOLD = 1000

# whether to interpolate the static variable in the background creation too. This
# means that if there e.g. is a measurement M(T) at 1000 Oe, 10000 Oe and 100000 Oe 
# but the background is only measured at 1000 Oe and 100000 Oe the background
# creation will interpolate a background measurement M(T)at 10000 Oe, then it 
# will create the interpolation for each temperature point in the background
INTERPOLATE_STATIC_VARIABLE = True

# The length of the header in lines for the csv export, the CSVExporter will
# guarantee that the header will always have this length
HEADER_LINE_NUMBER = 30

# a list of modes that are shown if the background is too short, the index 1 will
# be passed to the fit.py, the index 0 will be displayed to the user
BACKGROUND_INCREASE_MODES = (
    ("Repeat the (selected) background data to fill in the missing data", "repeat"),
    ("Mirror the (selected) background data and repeate it to in fill the missing data", "mirror"),
)