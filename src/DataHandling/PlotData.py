# -*- coding: utf-8 -*-
"""
Created on Mon Nov  6 13:29:02 2017

@author: miile7
"""

import os

import my_utilities
import DataHandling.DataContainer
import DataHandling.DataPoint

class PlotData:
    DATA_TITLE = "title"
    
    def __init__(self, **kwargs):
        """Initialize the PlotData
        Parameters
        ----------
            x : array_like, optional
                The x data
            y : array_like, optional
                The y data
            x_errors : array_like, optional
                The x data errors
            y_errors : array_like, optional
                The y data errors
            x_label : String, optional
                The label of the x axis
            y_label : String, optional
                The label of the y axis
            x_unit : String, optional
                The unit for the x axis
            y_unit : String, optional
                The unit for the y axis
            origin : DataContainer or DataPoint, optional
                The DataContainer where the data comes from
            sorting_list : list, optional
                A list to sort the x and y values by
            indices_list : list, optional
                The list of the indices in the origin datacontainer
        """
        
        # the x data
        self._x = []
        # the y data
        self._y = []
        # the x data errors
        self._x_errors = []
        # the y data errors
        self._y_errors = []
        # the x label
        self._x_label = ""
        # the y label
        self._y_label = ""
        # the x unit
        self._x_unit = ""
        # the y unit
        self._y_unit = ""
        # the x axis constant
        self._x_axis = None
        # the y axis constant
        self._y_axis = None
        # the origin
        self._origin = None
        # a list that contains the sorting order
        self._sorting_list = None
        # the indices list
        self._indices_list = None
        # some more custom data to store in this plot data, this may be some
        # external settings to identify the dataset like pressure, field or 
        # something like this
        self._data = {}
        
        settings_list = {
                "x": "x",
                "y": "y",
                "x_label": "x_label",
                "y_label": "y_label",
                "x_unit": "x_unit",
                "y_unit": "y_unit",
                "x_axis": "x_axis",
                "y_axis": "y_axis",
                "indices_list": "indices_list",
                "origin": "origin",
                "mpl_settings" : "mpl_settings"
        }
        
        for key in settings_list:
            if key in kwargs:
                try:
                    setattr(self, key, kwargs[key])
                except Exception:
                    raise
        
        # set the sorting list
        if "sorting_list" in kwargs:
            self.setSortingList(kwargs["sorting_list"])
        
        # set the title
        if "title" in kwargs and isinstance(kwargs["title"], str):
            self.setTitle(kwargs["title"])
        
    @property
    def x(self):
        data = self.getPlotData()
        if data != None:
           return data[0] 
        else:
            return self._x

    @x.setter
    def x(self, x):
        if my_utilities.is_iterable(x):
            self._x = x
            return True
        else:
            raise ValueError("x is not iterable")
            return False
        
    @property
    def y(self):
        data = self.getPlotData()
        if data != None:
           return data[1] 
        else:
            return self._y

    @y.setter
    def y(self, y):
        if my_utilities.is_iterable(y):
            self._y = y
            return True
        else:
            raise ValueError("y is not iterable")
            return False
        
    @property
    def x_errors(self):
        return self._x_errors

    @x_errors.setter
    def x_errors(self, x_errors):
        if my_utilities.is_iterable(x_errors):
            self._x_errors = x_errors
            return True
        else:
            raise ValueError("x_errors is not iterable")
            return False
        
    @property
    def y_errors(self):
        return self._y_errors

    @y_errors.setter
    def y_errors(self, y_errors):
        if my_utilities.is_iterable(y_errors):
            self._y_errors = y_errors
            return True
        else:
            raise ValueError("y is not iterable")
            return False
        
    @property
    def x_label(self):
        return self._x_label

    @x_label.setter
    def x_label(self, x_label):
        if isinstance(x_label, str):
            self._x_label = x_label
            return True
        else:
            raise ValueError("x label is not a String")
            return False
        
    @property
    def y_label(self):
        return self._y_label

    @y_label.setter
    def y_label(self, y_label):
        if isinstance(y_label, str):
            self._y_label = y_label
            return True
        else:
            raise ValueError("y label is not a String")
            return False
        
    @property
    def x_unit(self):
        return self._x_unit

    @x_unit.setter
    def x_unit(self, x_unit):
        if isinstance(x_unit, str):
            self._x_unit = x_unit
            return True
        else:
            raise ValueError("x unit is not a String")
            return False
        
    @property
    def y_unit(self):
        return self._y_unit

    @y_unit.setter
    def y_unit(self, y_unit):
        if isinstance(y_unit, str):
            self._y_unit = y_unit
            return True
        else:
            raise ValueError("y unit is not a String")
            return False
        
    @property
    def x_axis(self):
        return self._x_axis

    @x_axis.setter
    def x_axis(self, x_axis):
        if isinstance(x_axis, str):
            self._x_axis = x_axis
            return True
        else:
            raise ValueError("x axis is not a String")
            return False
        
    @property
    def y_axis(self):
        return self._y_axis

    @y_axis.setter
    def y_axis(self, y_axis):
        if isinstance(y_axis, str):
            self._y_axis = y_axis
            return True
        else:
            raise ValueError("y axis is not a String")
            return False
        
    @property
    def title(self):
        return self.getTitle()

    @title.setter
    def title(self, title):
        return self.setTitle(title)
        
    @property
    def origin(self):
        return self._origin

    @origin.setter
    def origin(self, origin):
        if (isinstance(origin, DataHandling.DataContainer.DataContainer) or
            isinstance(origin, DataHandling.DataPoint.DataPoint)):
            self._origin = origin
            return True
        else:
            raise ValueError("origin label neither is a DataContainer nor a DataPoint")
            return False
        
    @property
    def indices_list(self):
        return self._indices_list

    @indices_list.setter
    def indices_list(self, indices_list):
        if isinstance(indices_list, (list, tuple)):
            self._indices_list = indices_list
            
    @property
    def mpl_settings(self):
        return self._mpl_settings

    @mpl_settings.setter
    def mpl_settings(self, mpl_settings):
        self._mpl_settings = mpl_settings
    
    def getPlotData(self):
        """Get the data to plot, this will sort the data by the x keys
        Returns
        -------
            xdata, ydata
                The data for the x and y axis, sorted by the x values or None
                if not given
        """
        
        if my_utilities.is_iterable(self._x) and my_utilities.is_iterable(self._y):
            if (self._sorting_list != None and isinstance(self._sorting_list, list) and
                len(self._sorting_list) == len(self._x)):
                s = sorted(zip(self._sorting_list, self._x, self._y))
    
                return ([e[1] for e in s], [e[2] for e in s])
            
            else:
                s = sorted(zip(self._x, self._y))
    
                return ([e[0] for e in s], [e[1] for e in s])
        else:
            return None
    
    def setSortingList(self, sorting_list):
        """Set a list which defines the order of the x and y values. The x and y
        values will be sorted by this list then.
        Parameters
        ----------
            sorting_list : list
                The list to sort the values like
        Returns
        -------
            boolean
                success
        """
        
        if isinstance(sorting_list, list):
            self._sorting_list = sorting_list
            return True
        else:
            return False
    
    def getOriginFilePath(self, basename = True):
        """Get the filepath of the origin where this plot data comes from.
        Parameters
        ----------
            basename : boolean, optional
                Whether to return only the basename (true) or to return the full
                path (false)
        Returns
        -------
            String
                The path or None if not given
        """
        
        if self._origin != None and (
                (isinstance(self._origin, DataHandling.DataContainer.DataContainer) or
                 isinstance(self._origin, DataHandling.DataPoint.DataPoint))):
            if basename:
                return os.path.basename(self._origin.filepath)
            else:
                return self._origin.filepath
        else:
            return None
    
    def createTitle(self, auto_create = True, axis = True, filename = True, data = True):
        """Tries to create a title for this plot data depending on the internal
        values. If there is a data with the key "title" this will be returned
        and all the other parameters will be ignored
        Parameters
        ----------
            auto_create : boolean, optional
                This will make sure to create a title but the title will only
                contain the first data that has been found to keep it short, if
                this is set to false *all* the data that is possible to keep in
                the title will be returned (if not specified differently)
            axis : boolean, optional
                Whether to include the names of the axis in the title
            filename : boolean, optional
                Whether to include the origin filename in the title
            data : boolean, optional
                Whether to include data that has been added later to to the title
        Returns
        -------
            String
                The title String or an empty String
        """
        
#        print("PlotData.createTitle(): title: ", self._data[PlotData.DATA_TITLE])
        
        # check if there is a title set
        if data and len(self._data) > 0:
            if PlotData.DATA_TITLE in self._data:
                return self._data[PlotData.DATA_TITLE][0]
        
        # there is not title set, create a title
        title = ""
        
        # if axis are allowed print the axis
        if axis:
            if self._x_label != None and self._y_label != None:
                title += self._y_label + " vs " + self._x_label
        
        if auto_create and title != "":
            return title
        
        # check if there is additional data that should be added
        if data and len(self._data) > 0:
            for data_key in self._data:
                if self._data[data_key][1]:
                    if title != "":
                        title += ", "
                        
                    title += str(data_key) + ": " + str(self._data[data_key][0])
                    
        if auto_create and title != "":
            return title
        
        # add the filepath
        fp = self.getOriginFilePath(True)
        if fp != None and filename:
            if title != "":
                title += " "
            
            if isinstance(fp, str):
                title += fp
            elif isinstance(fp, DataHandling.DataContainer.DataContainer):
                title += fp.filepath
            elif isinstance(fp, DataHandling.DataPoint.DataPoint):
                if fp.index != None:
                    title += "#" + fp.infex + " " 
                title += fp.filepath
            
        if auto_create and title != "":
            return title
        
        # return the title
        return title
    
    def addData(self, key, value, add_to_title = False):
        """Add some more data to identify this plot data. This may be some
        external values like pressure or anything else.
        If you want to display the value in the title use add_to_title=True but
        make sure your value can be converted to a string!
        Parameters
        ----------
            key : String or int
                The key to store the data with
            value : anything
                The corresponding value
            add_to_title : boolean, optional
                Whether to display this information in the title or not, default:
                False
        """
        
        self._data[key] = (value, add_to_title == True)
    
    def setTitle(self, title):
        """Set the title of the plot data
        Parameters
        ----------
            title : String
                The title of the data
        """
        
        self.addData(PlotData.DATA_TITLE, title, True)
    
    def getTitle(self):
        """Get the title of the plot data. This returns the title only if there
        is a title set explicitly. If you want to get any title just to name
        this plot data use the PlotData.createTitle() function.
        Returns
        -------
            String
                The title or None if there is no title set.
        """
        
        if PlotData.DATA_TITLE in self._data:
            return self._data[PlotData.DATA_TITLE][0]
        else:
            return None
    
    def __iter__(self):
        """Initialize the iterator"""
        self._current_iteration_index = 0
        return self
    
    def __next__(self):
        """Get the next element to iterate over it"""
        if self._current_iteration_index == 0:
            self._current_iteration_index += 1
            return self.x
        elif self._current_iteration_index == 1:
            self._current_iteration_index += 1
            return self.y
        else:
            raise StopIteration()
    
    def __getitem__(self, index):
        """Get the item of the given index. This magic function makes the PlotData
        be key accessable (which means that plotdata[0] will return the x data and
        so on). This is very important for backwards compatibility
        Raises
        ------
            KeyError
                When the given index is not set
        Parameters
        ----------
            index : int or String
                The index or the name of the value to get
        Returns
        -------
            mixed
                The value
        """
        
        if index == 0 or index == "x":
            return self.x
        elif index == 1 or index == -1 or index == "y":
            return self.y
        elif index == "x_errors":
            return self.x_errors
        elif index == "y_error":
            return self.y_errors
        elif index == "x_label":
            return self.x_label
        elif index == "y_label":
            return self.y_label
        elif index == "origin":
            return self.origin
        else:
            raise KeyError("The key " + str(index) + " is not set")
