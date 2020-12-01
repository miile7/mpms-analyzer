# -*- coding: utf-8 -*-
"""
Created on Wed Nov  8 11:27:46 2017

@author: Maximilian Seidler
"""

from PyQt5 import QtCore
from os import path
import warnings

import DataHandling.DataContainer
import Constants
import my_utilities

class FileOpeningWorker(QtCore.QObject):
    loadingStart = QtCore.pyqtSignal(int, str, str)
    loadingProgress = QtCore.pyqtSignal(int, str, str)
    loadingEnd = QtCore.pyqtSignal(bool, str, str)
    finishedDataPoint = QtCore.pyqtSignal(DataHandling.DataContainer.DataContainer)
    
    finished = QtCore.pyqtSignal()

    def __init__(self, files, controller, data = None):
        """Initialize the worker. For further information
        about the data parameter have a look at the MainWindow.addFileToFileList
        function.
        Parameters
        ----------
            files : list
                A list of tuples which are the file names and the *.dat file names
                of the files to open
            controller : Controller
                The controller
            data : anything, optional
                Additional data that will affect the opening. What this exactly
                does depends on the data object, this may also effect other
                parameters, default: None
        """
        
        super().__init__()
        
        self._files = files
        self._controller = controller
        self._data = data

    def run(self):
        """Run the thread. This will create the DataContainers by parsing the 
        files
        """
        
        self._stop = False
        
        for fs in self._files:
            if isinstance(fs, list) or isinstance(fs, tuple):
                filename = fs[0]
                dat_filename = fs[1]
            else:
                filename = fs
                dat_filename = None
                
            data = DataHandling.DataContainer.DataContainer(filename, dat_filename)
            
            filename = path.basename(filename)
            
            # initialize the signals
            data.loadingStart.connect(self.loadingStart.emit)
            data.loadingProgress.connect(self.loadingProgress.emit)
            data.loadingEnd.connect(self.loadingEnd.emit)
            
            # check if to stop
            if self._stop:
                break
            
            # save all the eventually thrown warnings too
            with warnings.catch_warnings(record=True) as warns:
                # Cause all warnings to always be triggered.
                warnings.simplefilter("always")
                
                # try to read data
                try:
                    data.readFileData()
                    # readFileData takes a long time, check again if the process
                    # has stopped
                    if self._stop:
                        break
                except IOError as e:
                    self._controller.error(str(e), Constants.FATAL)
                    return False
                
                # check if some warnings occurred
                if len(warns) > 1:
                    warn_str = ""
                    
                    # get the count of digits to format all the same
                    p = len(str(len(warns)))
                    
                    # go through warning, add leading 0 to the warning number
                    i = 0
                    for w in warns:
                        warn_str += str(i).zfill(p) + ": " + str(w.message) + "<br />"
                        i += 1
                    
                    # show an error message
                    self._controller.error("{0} errors occurred when trying to open the file '{1}': <br />".format(
                            len(warns), filename), Constants.NOTICE, warn_str)
                elif len(warns) > 0:
                    # only one warning occurred, show an error message immediately
                    self._controller.error("An error occurred when trying to open the file '{0}': ".format(
                            filename), Constants.NOTICE, str(warns[0].message))
            
            if my_utilities.is_iterable(data.datapoints):
                if self.getData('exec_fit', True):
                    self._controller.log("Fitting data points")
                    
                    # fit the datapoints
                    try:
                        data.fitDataPoints()
                    except Exception as e:
                        self._controller.error("Fitting data caused an error: " + str(e))
                    
                # check again if the process has stopped
                if self._stop:
                    break
                    
                # emit ready signal and pass the datapoint, this will add it to
                # the controller and to the view (methods defined in the controller)
                self.finishedDataPoint.emit(data)
            else:
                self._controller.error(("Completed opening and reading file {0} " + 
                                       "sucessfully but file is empty").format(filename))
                
            if self._stop:
                break
            
        self.finished.emit()
        
    def stop(self):
        """Stop the worker"""
        self._stop = True
        
    def getData(self, key, default_value = None):
        """Returns the value of the given key in the internal data collection,
        if there is no data or the key does not exist this will return the given
        default_value
        Parameters
        ----------
            key : String
                The name of the key of the data to return
            default_value : anything, optional
                The default value to return if the key is not found or there is
                no data
        """
        
        if isinstance(self._data, dict) and key in self._data:
            return self._data[key]
        else:
            return default_value