# -*- coding: utf-8 -*-
"""
Created on Tue Oct 17 10:17:05 2017

@author: Maximilian Seidler
"""

import numpy as np
import sys
import re
import os

def pretty(d, indent=0):
    """Get a String which "prettyfies" the given input parameter. This means
    that the type will be included, tupels, lists and dicts will be written
    completeley for better reading
    
    Parameters
    ----------
        d : anything
            The element to bring into a human readable form (does not work with
            objects at the moment)
        indent : int, optional
            The indet, do not use this, this is for internal use only
            
    Returns
    -------
        String
            The object as a prettified string
    """
    sp = "  "
    t = ""
    
    if isinstance(d, dict):
        l = len(d)
        c = 0
        t += "<type 'dict'>:{\n"
        for key, value in d.items():
            t += sp * (indent + 1) + "'" + str(key) + "':" + pretty(value, indent + 1)
            
            if c + 1 < l:
                t += ","
            
            t += "\n"
            c += 1
        t += sp * indent + "}"
    elif isinstance(d, list):
        l = len(d)
        c = 0
        t += "<type 'list'>:[\n"
        for value in d:
            t += sp * (indent + 1) + str(c) + ":" + pretty(value, indent + 1)
            
            if c + 1 < l:
                t += ","
            
            t += "\n"
            c += 1
        t += sp * indent + "]"
    elif isinstance(d, tuple):
        l = len(d)
        c = 0
        t += "<type 'tuple'>:(\n"
        for value in d:
            t += sp * (indent + 1) + str(c) + ":" + pretty(value, indent + 1)
            
            if c + 1 < l:
                t += ","
            
            t += "\n"
            c += 1
        t += sp * indent + ")"
    else:
        t += str(type(d)) + ":'" + str(d) + "'"
    
    return t

def pprint(*d):
    """Prints the parameter(s) to the console as a prettified string.
    
    Parameters
    ----------
        *d : anything
            The object(s) to prettify
    """
    i = 0
    while i < len(d):
        print(pretty(d[i]))
        i += 1

def rreplace(string, old, new, count):
    """Replace the old with the new in the given string count times. This goes
    from the back to the front!
    
    Parameters
    ----------
        string : String
            The string to replace in
        old : String
            The string to replace
        new : String
            The new string to replace the old with
        count : int
            The number of times to perform the replace
            
    Returns
    -------
        String
            The string with replaced old occurances
    """
    
    li = string.rsplit(old, count)
    return new.join(li)
    
def is_numeric(s):
    """Check if the parameter is numeric or not
    
    Parameters
    ----------
        s : anything
            The parameter to check
            
    Returns
    -------
        boolean
            Whether the parameter is numeric or not
    """
    
    if s is False or s is None or s is "" or s is True:
        return False
    
    try:
        float(s)
        return True
    except (ValueError, TypeError):
        return False

def is_iterable(element):
    """Check if the given parameter is any type of a list (not a string)
    
    Parameters
    ----------
        element : anything
            The parameter to check
            
    Returns
    -------
        boolean
            Whether the parameter is a iterable type or not
    """
    return isinstance(element, (set, list, tuple))

# pre-compile pattern to increase speed
convert_pattern = re.compile(r"-?\s*((([\d]+(\.[\d]+)?)|([\d]*\.[\d]+))((([eE]\^?)|\^)(-?([\d]+(\.[\d]+)?)|([\d]*\.[\d]+)))?)")
def force_float(element, surpress_error = False):
    """Return a float if the element has anything to do with a number
    
    Raises
    ------
        ValueError
            If the element cannot be parsed to a float
            
    Parameters
    ----------
        element : anything
            The element to convert to a float
        surpress_error : boolean, optional
            If this is true this will *always* return a float, if an error 
            would occurre this will return 0
            
    Returns
    -------
        float 
            The element parsed to a float
    """
    
    if isinstance(element, float):
        # element is a float, return it
        return element
    else:
        try:
            # try if the element is a number
            return float(element)
        except (ValueError, TypeError):
            # replace all non-digit characters
            element = str(element)
            matches = convert_pattern.match(element)
            
            if matches != None:
                element = matches.group(0)
            
            try:
                return float(element)
            except (ValueError, TypeError):
                if surpress_error:
                    return 0
                else:
                    raise
    

def mean_std(array, errors = None):
    """Get the mean value of the array with the given standard diviation. If the
    errors is an array with the same length like the array parameter this will
    be assumed to be the errors of each element in the array. The error will then
    be calculated by using the error propagation method (which will result in the
    mean value of the error)
    
    Parameters
    ----------
        array : array_like
            An array which contains floats, the mean of this array will be returned
        errors : array_like, optional
            If given the errors will be assumed to be the errors of each element
            in the array parameter, the error will then be calculated by using
            error propagaition
            
    Returns
    -------
        float
            The mean of the array
        float
            The error
    """
    
    array = list(array)
    
    if array == []:
        return np.NaN, np.NaN
    
    if not is_iterable(errors) or len(array) != len(errors):
        return np.mean(array), np.std(array)
    else:
        return np.mean(array), np.mean(errors)

def image(name):
    """Get the image with the given name. This will find the correct image 
    destination for the compiled exe and the raw python code.
    
    Returns
    -------
        String
            The image path where the image is
    """

    # the path where all the images area
    if getattr(sys, 'frozen', False):
        # The application is frozen
        datadir = os.path.dirname(sys.executable)
    else:
        # The application is not frozen
        # Change this bit to match where you store your data files:
        datadir = os.path.dirname(__file__)
    return str(os.path.join(os.path.abspath(datadir), "icons", name))

#    if os.path.isfile(Constants.IMAGE_PATH + "/" + str(name)):
#        return Constants.IMAGE_PATH + "/" + str(name)
#    elif os.path.isfile(str(name)):
#    return "icons/" + str(name)