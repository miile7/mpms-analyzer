# -*- coding: utf-8 -*-
"""
Created on Wed Oct 18 10:31:40 2017

@author: miile7
"""

import warnings
import matplotlib
# tell not to use tk, this causes an error in the cx_freeze for the exe,
# also it is not used
# the error that is thrown by this code should be ignored, spyder is already
# coosing the backend, in the exe this will have no effect
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    matplotlib.use("Qt5Agg")

from PyQt5 import QtWidgets, QtCore, QtGui
import copy
import time
import sys
import re
import os

import View.MainWindow
import DataHandling.FileOpeningWorker
import DataHandling.DataContainer
import DataHandling.calculation
import Constants
import my_utilities

class Controller(QtCore.QObject):
    openedDataContainer = QtCore.pyqtSignal('PyQt_PyObject')
    
    def __init__(self, show_window = True):
        """Initialize the Controller which will load the View and the models too
        
        Parameters
        ---------
            show_window: boolean, False
                Whehter the window should be shown or not, default: True
        """
        
        super(QtCore.QObject, self).__init__()
        
        if show_window:
            app = QtWidgets.QApplication.instance()
            if not app or app == None:
                app = QtWidgets.QApplication(sys.argv)
            
            app.setWindowIcon(QtGui.QIcon(View.MainWindow.MainWindow.ICON))
        
        self.view = View.MainWindow.MainWindow(self, show_window)
        
        self._error_collection = []
        self._block_errors = False
        
        self._datacontainer = []
        
        self.show_window = show_window
        
        if show_window:
            sys.exit(app.exec_())
    
    def openFiles(self, files, parent = None):
        """Open the file with the filename. For further information
        about the data parameter have a look at the MainWindow.addFileToFileList
        function.
        
        Parameters
        ----------
            files : list of Strings
                The absolute path(s) of the file(s) to open
            parent : QWidget
                The parent of the progress dialogs
                
        Returns
        -------
            boolean
                success
        """
        
        if (isinstance(files, list) or isinstance(files, tuple)) and len(files) > 0:
            # create worker and thread, this is an extrenal thread for starting 
            # the DataContainer file opening methods. This is important because 
            # otherwise the view will freeze
            #
            # **IMPORTANT:** This has to be a value of the current controller
            # instance, if those variables are in the current scope only the 
            # garabge collector will remove the thread and the worker which will
            # cause the function to fail!
            self._worker = DataHandling.FileOpeningWorker.FileOpeningWorker(files, self)
            self._thread = QtCore.QThread()
        
            self._worker.moveToThread(self._thread)
            
            self._worker.finished.connect(self._thread.quit)
            self._worker.finished.connect(self.view.updateProgressClose)
            
            self._thread.started.connect(self._worker.run)
            self._thread.started.connect(lambda: self.pauseErrorDisplay(True))
            self._thread.finished.connect(self._worker.deleteLater)
            self._thread.finished.connect(lambda: self.pauseErrorDisplay(False))
            
            # set the progress events
            self.view.setProgressParent(parent)
            self.view.showProgress('Buffering file(s)', self._worker.stop)
            self._worker.loadingStart.connect(self.view.updateProgressStart)
            self._worker.loadingProgress.connect(self.view.updateProgress)
            self._worker.loadingEnd.connect(self.view.updateProgressEnd)
            self._worker.finishedDataPoint.connect(lambda x : self.addDataContainer)
            self._worker.finishedDataPoint.connect(self.openedDataContainer.emit)
            
            # start loading
            self._thread.start()
            
            return True
        else:
            return False
    
    def addDataContainer(self, datacontainer):
        """Add the given datacontainer to the view. This is used in the file
        open method 
        
        Parameters
        ----------
            datacontainer : DataContaienr
                The datacontainer to add to the view
            open_graph_manager : boolean, optional
                Whether to show the GraphManager with the opened datacontainer
                if the open process is finished, default: True
            data : anything, optional
                Additional data that will affect the opening. What this exactly
                does depends on the data object, this may also effect other
                parameters, default: None
        """
        
        if isinstance(datacontainer, DataHandling.DataContainer.DataContainer):
            self._datacontainer.append(datacontainer)
            
            if self.show_window:
                self.view.addFileToFilelist(datacontainer)
    
    def getDataContainerList(self):
        """Get all the datacontainers that are currently loaded
        
        Returns
        -------
            list 
                The list of datacontainers"""
                
        return self._datacontainer
    
    def replaceDataContainer(self, index, datacontainer):
        """Replace the datacontainer at the given index.
        
        Parameters
        ----------
            index : int
                The index to replace
            datacontainer : DataContainer
                The datacontainer to set to the given position
                
        Returns
        -------
            boolean
                success
        """
        
        if (isinstance(datacontainer, DataHandling.DataContainer.DataContainer) and
            index >= 0 and
            index < len(self._datacontainer)):
            self._datacontainer[index] = datacontainer
            
            if self.show_window:
                self.view.replaceDataContainerWidget(index, datacontainer)
            
            return True
        else:
            return False
    
    def subtractBackgroundData(self, datacontainer, background_datacontainer, extend_mode = None, indices_list = None):
        """Subtract the backgrdound_datacontainer from the datacontainer. The actual
        subtracting will be done in the DataPoint
        
        Parameters
        ----------
            datacontainer : DataContainer
                The datacontainer which contains the original data where the
                background data should be subtracted from
            background_datacontainer: DataContainer
                The datacontainer which holds the background data
                
        Returns
        -------
            DataContainer
                A new datacontainer which holds the data with subtracted background
        """
        
        print("Controller.subtractBackgroundData():", len(datacontainer.datapoints), len(background_datacontainer.datapoints))
        
        if (isinstance(datacontainer, DataHandling.DataContainer.DataContainer) and 
            isinstance(background_datacontainer, DataHandling.DataContainer.DataContainer)):
                # create a copy of the original datacontainer
                new_datacontainer = copy.deepcopy(datacontainer)
                new_datacontainer.setData(DataHandling.DataContainer.DataContainer.ORIGINAL_DATA, datacontainer)
                new_datacontainer.setData(DataHandling.DataContainer.DataContainer.BACKGROUND_DATA, background_datacontainer)
                new_datacontainer.addAttribute("Background removed")
                new_datacontainer.removed_background = True
                
                # store the errors
                errors = []
                
                if len(datacontainer.datapoints) != len(background_datacontainer.datapoints):
                    # get the extend type
                    extend_keys = [i[1] for i in Constants.BACKGROUND_INCREASE_MODES]
                    
                    if extend_mode == None or extend_mode not in extend_keys:
                        extend_mode = extend_keys[0]
                    
                    if not isinstance(indices_list, (list, tuple)):
                        indices_list = self.zipFullRange(background_datacontainer.datapoints)
                    
                    # prepare the plain
                    data = []
                    for datapoint in datacontainer.datapoints:
                        data.append(datapoint.getPlotData(
                                DataHandling.DataPoint.DataPoint.RAW_POSITION,
                                DataHandling.DataPoint.DataPoint.RAW_VOLTAGE,
                                True))
                    
                    # prepare the background data
                    background = []
                    for datapoint in background_datacontainer.datapoints:
                        background.append(datapoint.getPlotData(
                                DataHandling.DataPoint.DataPoint.RAW_POSITION,
                                DataHandling.DataPoint.DataPoint.RAW_VOLTAGE,
                                True))
                    
                    try:
                        # get the processed (extended) background data
                        background_data = DataHandling.calculation.extendBackgroundData(
                                data, background, extend_mode, indices_list, 
                                datacontainer, background_datacontainer)
                    except Exception as e:
                        error_loc = ""
                        
                        if isinstance(sys.exc_info(), (list, tuple)) and len(sys.exc_info()) > 0:
                            # use slice for avoiding errors, throwing an exception will cause
                            # an infinite loop
                            exception_type = sys.exc_info()[0]
                            traceback = sys.exc_info()[-1]
                            
                            if traceback != None:
                                error_loc += "; Last exception ({}) in {} in line {}".format(
                                        exception_type,
                                         os.path.split(traceback.tb_frame.f_code.co_filename)[1],
                                         traceback.tb_lineno)
        
                        errors.append(type(e).__name__ + ": " + str(e) + error_loc)
                else:
                    background_data = background_datacontainer
                
                with warnings.catch_warnings(record=True) as ws:
                    # go through all the datapoints of the original data
                    for index, datapoint in enumerate(new_datacontainer.datapoints):
                        print("Controller.subtractBackgroundData(): index: ", index)
                        # perform the background removing
                        try:
                            new_datacontainer.datapoints[index].index = index
                            new_datacontainer.datapoints[index].removeBackgroundData(
                                    self._getBackgroundDataPoint(background_data, index))
                        except Exception as e:
                            errors.append("Datapoint #{} raised Error: ".format(index) + str(e))
                    
                        # fit the datapoint again
                        try:
                            new_datacontainer.datapoints[index].execFit()
                        except Exception as e:
                            errors.append("Datapoint #{} raised Error: ".format(index) + str(e))
                        
                        for w in ws:
                            w.index = index
    
                for error in errors:
                    if isinstance(error, warnings.WarningMessage):
                        error = str(error.message)
                        
                        if hasattr(error, "index") and my_utilities.is_numeric(error.index):
                            error += " in datapoint #{}".foramt(error.index)
                        
                        error += " in {} in file {}".format(
                                error.lineno, os.path.basename(error.filename))
                    else:
                        error = str(error)
                        
                    warnings.warn(error)
                        
                return new_datacontainer
        
        return None
    
    def _getBackgroundDataPoint(self, background_datacontainer, index):
        """Get the datapoint of the background_datacontainer at the given 
        index
        
        Parameters
        ----------
            background_datacontainer : DataContainer
                The datacontainer to take the datapoint from
            index : int
                The index of the datapoint
                
        Returns
        -------
            DataPoint
                The datapoint at the given index of the datacontainer
        """
        
        if isinstance(background_datacontainer, DataHandling.DataContainer.DataContainer):
            return background_datacontainer.datapoints[index]
        elif isinstance(background_datacontainer, (list, tuple)):
            return background_datacontainer[index]
    
    def zipIndices(self, list_data):
        """Create a human readable string of the indices in the list_data. The
        list_data is assumed to be a list full of integers. This function will
        create a string where integer ranges are written with a colon (:), single
        integers will be separated with a semikolon (;). This means that a list
        like [1,2,3,4,5,6,9,10,12,14] will result in the string '1:6;9:10;12;14'
        
        Parameters
        ----------
            list_data : list of integers
                The list of integers that should be zipped to a human readable
                string
                
        Returns
        -------
            String
                The zipped list or an empty string if an error occurred or the
                list is empty
        """
        
        # sort the list
        list_data.sort()
        
        # the return value
        zip_indices = ""
        # the last element in the list_data
        last_element = None
        # the index of the list_data when an element had been added
        added_i = None
        
        for i, element in enumerate(list_data):
            # check if the last element is the current element - 1, if it is 
            # this will be in the range
            if last_element != None and last_element + 1 == element:
                last_element = element
                continue
            else:
                # element is not in the range, check if the last element exists
                if last_element != None:
                    # if it exists check if the last element has been added 
                    # already, if not this is a range so end the range
                    if added_i != i -1:
                        zip_indices += ":" + str(last_element)
                    
                    # indicate that a new element is starting
                    zip_indices += ";"
                
                # add the current element
                zip_indices += str(element)
                # save the added index
                added_i = i
                # save the element as the last element for the next iteration
                last_element = element
        
        # check if the list_data is a range form the first element to the last
        if len(list_data) > 1 and zip_indices == str(list_data[0]):
            zip_indices += ":" + str(list_data[-1])
        
        return zip_indices
    
    def unzipIndices(self, indices_string):
        """Creates an array which contains all the indices in the given indices_string.
        This is the inverted method for the GraphWizard.zipIndices method.
        
        Paramters
        ---------
            indices_string : String
                The indices in a human readable string
                
        Returns
        -------
            list
                The list of indices of the datapoints
        """
        
        space_regexp = re.compile("\\s+")
        indices_string = space_regexp.sub("", indices_string)
        datapoints = []
        
        # split datapoints by ;
        indices_string = indices_string.split(";")
        for datapoint_range in indices_string:
            # split datapoint ranges by :
            datapoint_range = datapoint_range.split(":")
            # remove empty or non-strings
            datapoint_range = filter(lambda x : my_utilities.is_numeric(x), 
                                     datapoint_range)
            # convert to int
            datapoint_range = list(map(lambda x: int(my_utilities.force_float(x, True)), 
                                  datapoint_range))
            
            if len(datapoint_range) == 1:
                # only one element so this is a single datapoint index
                datapoints.append(my_utilities.force_float(datapoint_range[0]))
            elif len(datapoint_range) > 1:
                # create range
                mi = min(datapoint_range)
                ma = max(datapoint_range) + 1
                
                datapoints = datapoints + list(range(mi, ma))
        
        return datapoints
    
    def zipFullRange(self, iterable):
        """Get the full range of the given iterable, this will return a zip-String
        received by the Controller.zipIndices() index of the given iterable
        
        Parameters
        ----------
            iterable : Iterable
                The iterable to get the zip list of
                
        Returns
        -------
            String
                The zipped list or an empty string if the iterable is not iterable
        """
        
        try:
            l = len(iterable)
        except TypeError as e:
            return ""
        
        return self.zipIndices(list(range(0, l)))
    
    
    def uniqueListThreshold(self, list_data, threshold):
        """Removes all the list elements in the list_data that are the same.
        This supports only numeric lists. The threshold can be a numeric value
        which defines how much the list_datas elements can differ form the others
        and still count as the "same value"
        
        Parameters
        ----------
            list_data : list
                The list to check
            threshold : number
                The threshold
                
        Returns
        -------
            list
                A list with removed duplicates
        """
        
        # prepare variables
        uniques = []
        full_list = {}
        
        # go through each list element
        for x in list_data:
            # tells whether the element has been found or not
            found = False
            
            # go through the existing elements in the uniques list
            for u in uniques:
                # check if the current list_datas element is in the range
                # of the current unique value
                if u - threshold < x and u + threshold > x:
                    found = True
                    full_list[u].append(x)
                    break;
            
            # if the element is not in the uniques add it as a new unique
            if not found:
                full_list[x] = [x]
                uniques.append(x)
        
        return uniques, full_list
    
    def createNewBackground(self, datacontainer, background_datacontainer, measurement_type, filepath = None):
        """Create a new background for the given datacontainer file by intermpolating
        the background_datacontainer. The measurement_type tells whether the 
        file is a M(T) or a M(H) measurement. The filepath is the target filepath
        to save in the generated background.
        
        Parameters
        ----------
            datacontainer : DataContainer
                The datacontainer to create the background for
            background_datacontainer : DataContainer
                The background to interpolate
            measurement_type : String
                The environment variable which tells which measurement type this
                is
            filepath : String, optional
                The filepath of the background datacontainer
        
        Returns
        -------
            DataContainer
                The generated background datacontainer
        """
        
        if not isinstance(filepath, str):
            filepath = "<temporary created background>"
        
        return DataHandling.calculation.createBackgroundDataContainer(
            datacontainer,
            background_datacontainer,
            measurement_type,
            filepath,
            self
            )
    
    def cutDataPointRows(self, datacontainer, conditions):
        """Cut all the datapoints of the given datacontainer with the given condition.
        The condition has to be a list of dicts, each dict has to have a key index
        which holds the key and a min and/or a max index.
        
        Parameters
        ----------
            datacontainer : DataContainer
                The datacontainer to cut the datapoints of
            conditions : list of dicts
                The conditions which datapoint rows to keep and which to delete
        
        Returns
        -------
            DataContainer
                The edited datacontainer or None if an error occurred
        """
        
        if isinstance(datacontainer, DataHandling.DataContainer.DataContainer):
            datacontainer = copy.deepcopy(datacontainer)
            datacontainer.addAttribute("Datapoints edited")
            
            for datapoint in datacontainer.datapoints:
                datapoint.cutRows(conditions)
                datapoint.execFit()
                datapoint.parent = datacontainer
            
            return datacontainer
        else:
            return None
        
    def log(self, message, log_type = Constants.LOG_CONSOLE):
        """Log the given message. There are (currently) 3 different log_type, they are
        all given in the View Constants. There is the LOG_STATUSBAR which will print the
        message in the status bar in the view, the LOG_CONSOLE will log in the internal
        console and the LOG_DEBUG will also log in the console but this will be only
        displayed if the program runs in debug mode
        
        Parameters
        ----------
            message : String
                The meassage to log
            log_type : int
                The int constant of the log type
        """
        
        self.view.log(message, log_type)
    
    def pauseErrorDisplay(self, pause):
        """Pause or un-pause the displaying of errors. The errors will be added to the
        internal collection and they will be displayed when the error displaying is 
        unpaused again.
        **Use with caution! This may hide errors so the user does not know what is
        going on!**
        
        Parameters
        ----------
            pause : boolean
                Whether to pause the errors or to unpause them
        """
        b = self._block_errors
        
        self._block_errors = (pause == True)
        
        if self._block_errors == False and b != self._block_errors:
            for error in self._error_collection:
                self.error(error[0], error[1], error[2])
            
            self._error_collection = []
    
    def error(self, message, error_type = Constants.NOTICE, error_details = None):
        """Raise an error message with the given error_type. The types are defined in the
        Constants. The error_details will be added to the error dialog, they can contain
        further information
        
        Parameters
        ----------
            message : String
                The meassage to display as an error
            error_type : int, optional
                The int constant of the error type
            error_details : String or list, optional
                A String with further error details
        """
        
        if self._block_errors:
            self._error_collection.append((message, error_type, error_details, time.time()))
            return False
        
        error_string = "An Error"
        error_details_string = ""
        
        # parse the error type to a string for logging
        if error_type == Constants.NOTICE:
            error_string = "A Notice"
        elif error_type == Constants.FATAL:
            error_string = "A Fatal Error"
            
        # parse the details to a string
        if isinstance(error_details, str):
            error_details_string = error_details
        elif my_utilities.is_iterable(error_details):
            for key, value in enumerate(error_details):
                error_details_string += value + "\n"
        
        self.log("<b style='color: red;'>{0} occurred: {1}{2}</b>".format(error_string, str(message),
                 error_details_string))
        
        if self._block_errors != True and (error_type == Constants.FATAL or error_type == Constants.NOTICE_ERROR):
            self.view.showErrorDialog(message, error_details_string, error_type)
            
        return True

def launch():
    """Launch the program"""
    Controller()
        
if __name__ == "__main__":
    launch()