# -*- coding: utf-8 -*-
"""
Created on Mon Oct 23 13:21:03 2017

@author: Maximilian Seidler
"""

from PyQt5 import QtWidgets, QtCore
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.patches
import matplotlib.artist
import numpy as np
#from matplotlib.backend_bases import NavigationToolbar2
import textwrap
import functools

import DataHandling.DataContainer
import DataHandling.DataPoint
import View.PlotMenuFactory
import my_utilities

plt.ion()
 
class PlotCanvas(FigureCanvas):
    PLOTDATA_PREFIX = "_plotCanvas-"
    
    DEFAULT_Z_ORDER = 1
    LEGEND_Z_ORDER = 2
    HIGHLIGHT_Z_ORDER = 100
    HIGHLIGHT_TEXT_Z_ORDER = HIGHLIGHT_Z_ORDER + 1
    
    datapointClicked = QtCore.pyqtSignal(DataHandling.PlotData.PlotData, int, int)
    datapointDoubleClicked = QtCore.pyqtSignal(DataHandling.PlotData.PlotData, int, int)
    
    def __init__(self, parent = None, width = 5, height = 4, dpi = 100):
        """Initialize the PlotCanvas.
        
        Parameters
        ----------
            parent : QtWidgets.QWidget
                The parent of the PlotCanvas
            width : int
                The width of the matplotlib figure
            height : int
                The height of the matplotlib figure
            dpi : int
                The dpi of the matplotlib figure
        """
        
        # create figure
        fig = Figure(figsize = (width, height), dpi=dpi)
        
        # init figure canvas
        FigureCanvas.__init__(self, fig)
        if parent != None and isinstance(parent, QtWidgets.QWidget):
            self.setParent(parent)
            
        # set figure canvas to expand its size
        FigureCanvas.setSizePolicy(self,
                QtWidgets.QSizePolicy.Expanding,
                QtWidgets.QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)
        
        # the axes
        self.axes = [fig.add_subplot(111)]
        # the axes to draw in
        self._current_axes = 0
        # whether the PlotCanvas has a second x axis, this means that the title
        # has to be shifted
        self._twin_x = False
        
        # connect the clicking acion
        self.mpl_connect("pick_event", self.actionClick)
        
        # create a toolbar
        self._toolbar_widget = QtWidgets.QWidget()
        
        self.plot_menu_factory = View.PlotMenuFactory.PlotMenuFactory(fig.canvas, self)
        self._context_menu = self.plot_menu_factory.context_menu
        
        # clear plot and init all the drawing variables
        self.clear()
        
        # fix the layout
        self.fixLayout()
        
        # all the highlighted points
        self._highlights = []
        self._highlight_texts = []
    
    @property
    def current_axes(self):
        return self._current_axes
    
    @current_axes.setter
    def current_axes(self, current_axes):
        if my_utilities.is_numeric(current_axes):
            try:
                current_axes = int(current_axes)
            except OverflowError:
                return False
            
            if current_axes >= 0 and current_axes < len(self.axes):
                self._current_axes = current_axes
                
    @property
    def title(self):
        return self._title
    
    @title.setter
    def title(self, title):
        self._title = title
    
    def addNewXAxis(self, use_axes = True, ref_axes = None):
        """Add a new x axis.
        
        Parameters
        ----------
            use_axes : boolean, optional
                Whether to use the x axis or not
            ref_axes : int, optional
                The reference axes object which defines the y axis, default:
                current_axes
        """
        
        ref_axes = self._getRefAxes(ref_axes)
            
        self.axes.append(self.axes[ref_axes].twiny())
        self._twin_x = True
        self.updateTitle()
        if use_axes:
            self.current_axes = len(self.axes) - 1
    
    def addNewYAxis(self, use_axes = True, ref_axes = None):
        """Add a new y axis.
        
        Parameters
        ----------
            use_axes : boolean, optional
                Whether to use the y axis or not
            ref_axes : int, optional
                The reference axes object which defines the x axis, default:
                current_axes
        """
        
        ref_axes = self._getRefAxes(ref_axes)
            
        self.axes.append(self.axes[ref_axes].twinx())
        if use_axes:
            self.current_axes = len(self.axes) - 1
    
    def invertXAxis(self, ref_axes = None):
        """Inverts the x axis of the axis with the given axes_index
        
        Parameters
        ----------
            ref_axes : int, optional
                The index of the axes
        """
        
        ref_axes = self._getRefAxes(ref_axes)
        
        try:
            self.axes[ref_axes].invert_xaxis()
        except IndexError:
            pass
    
    def invertYAxis(self, ref_axes = None):
        """Inverts the y axis of the axis with the given axes_index
        
        Parameters
        ----------
            ref_axes : int, optional
                The index of the axes
        """
        
        ref_axes = self._getRefAxes(ref_axes)
        
        try:
            self.axes[ref_axes].invert_yaxis()
        except IndexError:
            pass
    
    def xAxisIsInverted(self, ref_axes = None):
        """Returns whether the x axis of the given ref_axes is inverted. Inverted
        means that the maximum comes left of the minimum
        
        Raises
        ------
            IndexError
                If the ref_axes does not exist
                
        Parameters
        ----------
            ref_axes : int, optional
                The index of the axes
                
        Returns
        -------
            boolean
                Whether the axis is inverted
        """
        
        ref_axes = self._getRefAxes(ref_axes)
        
        try:
            lim = self.axes[ref_axes].get_xlim()
            return lim[0] > lim[1]
        except IndexError:
             raise
    
    def yAxisIsInverted(self, ref_axes = None):
        """Returns whether the y axis of the given ref_axes is inverted. Inverted
        means that the maximum comes left of the minimum
        
        Raises
        ------
            IndexError
                If the ref_axes does not exist
                
        Parameters
        ----------
            ref_axes : int, optional
                The index of the axes
                
        Returns
        -------
            boolean
                Whether the axis is inverted
        """
        
        ref_axes = self._getRefAxes(ref_axes)
        
        try:
            lim = self.axes[ref_axes].get_ylim()
            return lim[0] > lim[1]
        except IndexError:
             raise
    
    def _getRefAxes(self, ref_axes):
        """Get the ref axes for the given ref_axes. This is an internal method
        for getting the correct axes
        
        Parameters
        ----------
            ref_axes : anything
                The ref axes
                
        Returns
        -------
            int
                The ref axes
        """
        
        if (ref_axes == None or not isinstance(ref_axes, int) or ref_axes < 0 or
            ref_axes >= len(self.axes)):
            return self.current_axes
        else:
            return ref_axes
    
    def createTitle(self, include_subtitle = True, complete_string = True):
        """Creates a title String which describes all the plots contained in
        this plot canvas
        
        Parameters
        ----------
            include_subtitle : boolean, optional
                whether to include the subtitle (which is the file where this 
                comes from)
            complete_string : boolean, optional
                Whether to return a string with the format "<title> - <subtilte>"
                (complete_string=True) or to return a tuple with (<title>, <subtilte>)
                (complete_string=False)
        """
        title = ""
        subtitle = ""
        
        if isinstance(self._title, str) and len(self._title) > 0:
            title = self._title
        
        plotdata_names = []
        axis = {}
            
        # go through each plot data, save the x and y label and the origin
        for plotdata in self._plot_data:
            if plotdata["y_label"] not in axis:
                axis[plotdata["y_label"]] = []
            
            if plotdata["x_label"] not in axis[plotdata["y_label"]]:
                axis[plotdata["y_label"]].append(plotdata["x_label"])
            
            if isinstance(plotdata.origin, DataHandling.DataContainer.DataContainer):
                plotdata_names.append(plotdata.origin.createName())
            elif isinstance(plotdata.origin, DataHandling.DataPoint.DataPoint):
                name = ""
                
                if plotdata.origin.index != None:
                    name += "#" + str(plotdata.origin.index)
                
                if (plotdata.origin.parent != None and 
                    isinstance(plotdata.origin.parent, DataHandling.DataContainer.DataContainer)):
                    if name != "":
                        name += " of "
                        
                    name += plotdata.origin.parent.createName()
                
                if name != "":
                    plotdata_names.append("Datapoint " + name)
        
        if title != "":
            title += ": "
        
        if len(plotdata_names) >= 2:
            title += ", ".join(plotdata_names[0:-2]) + " and " + plotdata_names[-1]
        elif len(plotdata_names) == 1:
            title += plotdata_names[0]
        
        if include_subtitle:
            # define variables for the for loop
            counter = 0
            l = len(axis)
            skip = []
            
            # go through all the axis
            for y_axis in axis:
                # check if this axix should be skipped
                if y_axis in skip:
                    continue
                
                # receive the x axis, this is an array of all the x axis for the 
                # corresponding y axis, so if there are multiple x axis for one
                # y axis they will be stored in the x_axis variable
                x_axis = axis[y_axis]
                subtitle += str(y_axis)
                
                # go through all axis again, check if there is another y axis which
                # has the save x axis so you can write <y axis 1> and <y axis 2> over
                # <x axis>
                y_axis_coll = []
                for y_axis2 in axis:
                    if y_axis != y_axis2 and axis[y_axis] == axis[y_axis2]:
                        y_axis_coll.append(y_axis2)
                        # remove this from next iteration, this axis is included in
                        # the string now
                        skip.append(y_axis2)
                
                # add the various y axis for the current x axis
                if len(y_axis_coll) > 0:
                    subtitle += ", ".join(y_axis_coll[:-1]) + " and " + y_axis_coll[-1]
                
                subtitle += " vs "
                
                # now add all the x axis for this (or more) y axis
                if isinstance(x_axis, list):
                    c = len(x_axis)
                    for i in range(0, c):
                        subtitle += x_axis[i]
                        
                        if i < c - 2:
                            subtitle += ", "
                        elif i < c - 1:
                            subtitle += " and "
                
                # print divider for the next <y axis>-<x axis> pair
                if counter < l - 1:
                    subtitle += "; "
            
            if complete_string and subtitle != "":
                title += " [" + subtitle + "]"
            else:
                title = (title, subtitle)
        
        return title
    
    def getNumberOfPlotData(self):
        """Get the number of plot data that is added to this PlotCanvas
        
        Returns
        -------
            int
                The number of plot data this canvas contains
        """
        
        return len(self._plot_data)
    
    def getPlotDataList(self):
        """Get the list of plot data that is currently used
        
        Returns
        -------
            list
                The plot data objects that are displayed
        """
        
        return self._plot_data
    
    def getPlotData(self, plot_data_index):
        """Return the plot data with the given plot_data_index
        
        Parameters
        ----------
            plot_data_index : int
                The index
                
        Returns
        -------
            PlotData
                The plot data object
        """
        
        if isinstance(plot_data_index, int) and plot_data_index > 0 and plot_data_index < len(self._plot_data):
            return self._plot_data[plot_data_index]
        else:
            return None
    
    def addPlotData(self, plotdata, new_axis=False):
        """Add the given plot data to the internal collection and plot it
        
        Parameters
        ----------
            plotdata : PlotData
                The data to plot
                
        Returns
        -------
            index, the index of the plot data
        """
        
        if isinstance(plotdata, DataHandling.PlotData.PlotData):
            self._plot_data.append(plotdata)
            self._plotData(-1)
            return len(self._plot_data) - 1
        elif isinstance(plotdata, list) or isinstance(plotdata, tuple):
            r = []
            for pd in plotdata:
                r.append(self.addPlotData(pd, new_axis))
            
            return all(r)
        else:
            return False
    
    def _plotData(self, index = -1):
        """Plot the plotdata of the given index
        
        Parameters
        ----------
            index : int
                The index of the data to plot
                
        Returns
        -------
            boolean
                success
        """
        
        if len(self._plot_data) <= 0:
            return False
        else:
            # get the data 
            try:
                data = self._plot_data[index]
            except IndexError:
                return False
            
            axes = self.axes[self.current_axes]
            
            if index < 0:
                index = len(self._plot_data) + index
            
            # add the plot to the internal collection (on the right index)
            while len(self._plots) <= index:
                self._plots.append(None)
            
            # plot the plot_data, if it is empty display an error message
            if my_utilities.is_iterable(data.x) and my_utilities.is_iterable(data.y):
                # get the current color, if the color is not set use the normal
                # matplotlib colors
                if self.color == "" or self.color == None:
                    if (isinstance(self._color_cycler, int) and (
                        self._color_cycler >= 0 and self._color_cycler < 9)):
                        self._color_cycler += 1
                    else:
                        self._color_cycler = 0
                    
                    color = "C" + str(self._color_cycler)
                else:
                    color = self.color
                        
                self._plots[index] = axes.plot(
                        data.x, 
                        data.y, 
                        marker = self.marker, 
                        linewidth = self.linewidth, 
                        markersize = self.markersize, 
                        picker = 5,
                        color = color, 
                        linestyle = self.linestyle,
                        zorder = PlotCanvas.DEFAULT_Z_ORDER)
            else:
                # print the error message
                self._plots[index] = axes.plot([None], [None])
                x_pos = my_utilities.mean_std(axes.get_xlim())[0]
                y_pos = my_utilities.mean_std(axes.get_ylim())[0]
                axes.text(x_pos, y_pos, 'Could not print the data', 
                               horizontalalignment='center', verticalalignment='center', 
                               fontsize=20, color='red', transform=axes.transAxes)
            
            # print the x axis label
            if isinstance(data.x_label, str) and len(data.x_label) > 0:
                if self._print_unit and isinstance(data.x_unit, str) and len(data.x_unit) > 0:
                    axes.set_xlabel(data.x_label + " [" + data.x_unit + "]")
                else:
                    axes.set_xlabel(data.x_label)
                
            # print the y axis label
            if isinstance(data.y_label, str) and len(data.y_label) > 0 and len(data.y_unit) > 0:
                if self._print_unit and isinstance(data.y_unit, str):
                    axes.set_ylabel(data.y_label + " [" + data.y_unit + "]")
                else:
                    axes.set_ylabel(data.y_label)
            
            # get the figure
            fig = self.getFigure()
                
            # set the names for the plot lines
            for index, plot_data in enumerate(self._plot_data):
                lines = self._plots[index]
                if lines != None and isinstance(lines, (list, tuple)) and len(lines) > 0:
                    for line in lines:
                        name = plot_data.createTitle()
                        line.set_label(name)
            
            # get the title for this plot canvas
            title = ""
            if isinstance(self._title, str) and len(self._title) > 0:
                title = self._title
            
            # if there are more than just one plot data create a legend, if not
            # just set the title
            if self.print_legend and (len(self._plot_data) > 1 or title != ""):
                l = axes.legend()
                l.set_zorder(PlotCanvas.LEGEND_Z_ORDER)
                
            if title != "":
                self.updateTitle(title)
            else:
                self.updateTitle(self.createTitle())
            
            # redraw the canvas
            fig.canvas.draw()
            fig.canvas.flush_events()
            
            # fix the layout
            self.fixLayout()
            
            return True
    
    def drawXGrid(self, plotdata, ref_axes = None):
        """Plots vertical lines where the plotdata has x values
        
        Parameter
        ---------
            plotdata : PlotData or list
                The plotdata or a list with the x values to print lines
                
        Return
        ------
            boolean
                success
        """
        
        if isinstance(plotdata, DataHandling.PlotData.PlotData):
            plotdata = plotdata.x
        elif not isinstance(plotdata, (list, tuple)):
            return False
        
        return self._drawGrid(True, plotdata)
    
    def drawYGrid(self, plotdata, ref_axes = None):
        """Plots horizontal lines where the plotdata has y values
        
        Parameter
        ---------
            plotdata : PlotData or list
                The plotdata or a list with the y values to print lines
                
        Return
        ------
            boolean
                success
        """
        
        if isinstance(plotdata, DataHandling.PlotData.PlotData):
            plotdata = plotdata.y
        elif not isinstance(plotdata, (list, tuple)):
            return False
        
        return self._drawGrid(False, plotdata)
    
    def drawGrid(self, plotdata, ref_axes = None):
        """Plots grid lines where the plotdata has x and y values
        
        Parameter
        ---------
            plotdata : PlotData
                The plotdata
                
        Return
        ------
            boolean
                success
        """
        
        return self.darwXGrid(plotdata, ref_axes) and self.drawYGrid(plotdata, ref_axes)
    
    def _drawGrid(self, vertical_lines, datalist, ref_axes = None):
        """Draws the actual grid.
        
        Paramters
        ---------
            vertical_lines : boolean
                Whether to print verticale lines or horzontal lines
            datalist : list
                The x or y data depending on the vertical lines
            ref_axes : int, optional
                The index of the axes
                
        Return
        ------
            boolean
                success
        """
            
        ref_axes = self._getRefAxes(ref_axes)
        
        axes = self.axes[ref_axes]
        
        if not isinstance(datalist, (list, tuple)):
            return False
        
        for v in datalist:
            if my_utilities.is_numeric(v):
                v = my_utilities.force_float(v)
                
                if vertical_lines:
                    axes.axvline(v, linewidth=1, color="lightgrey")
                else:
                    axes.axhline(v, linewidth=1, color="lightgrey")
                    
        return True
        
    def highlightDataPoint(self, datapoint_index, line_index = 0, update_plot = True, point_indices = True):
        """Highlight the DataPoint at the given datapoint_index of the plot data
        with the plot_data_index. The line_index defines which line is used, this
        should (nearly) always be the zero.
        
        Parameters
        ----------
            datapoint_index : int or list of ints
                The index/indices of the DataPoint in in the DataContainer, this 
                is not necessarily the same as the index in the plot data!
            line_index : int, optional
                The index of the matplotlib 2DLines, this should (nearly) always
                be the default, default: 0
            update_plot : boolean, optional
                Whether to update the plot or not, if this is False the highlight
                point will be displayed **after** the PlotCanvas.commitUpdate()
                function has been called, default: True
            point_indices : boolean, optional
                Whether to print the indices of the point or not, default: True
        """
        
        plot_data_indices = []
        real_indices = []
                
        if not isinstance(datapoint_index, (list, tuple)):
            datapoint_index = [datapoint_index]
    
        for dp_index in datapoint_index:
            for pdi, plot_data in enumerate(self._plot_data):
                if isinstance(plot_data.indices_list, (list, tuple)) and dp_index in plot_data.indices_list:
                    plot_data_indices.append(pdi)
                    real_indices.append(plot_data.indices_list.index(dp_index))
                    break
        x = []
        y = []
        text = []
        ref_axes = []
        
        for i, plot_data_index in enumerate(plot_data_indices):
            if isinstance(real_indices, (list, tuple)) and i < len(real_indices):
                # get the lines collection
                lines = self._plots[plot_data_index]
                
                if (isinstance(line_index, int) and line_index >= 0 and 
                    line_index < len(lines)):
                    
                    # get te line
                    line = lines[line_index]
                    
                    r = line.axes
                    if r in self.axes:
                        ref_axes.append(self.axes.index(line.axes))
                    else:
                        ref_axes.append(None)
                    
                    # the x and y data
                    xdata = line.get_xdata()
                    ydata = line.get_ydata()
                    
                    x.append(xdata[real_indices[i]])
                    y.append(ydata[real_indices[i]])
                    
                    text.append(datapoint_index[i])
                
        # highlight the position of the datapoint_index
        self.highlightPosition(x, 
                               y,
                               ref_axes,
                               update_plot,
                               text)
                
    
    def highlightPosition(self, x, y, ref_axes = None, update_plot = True, text = None):
        """Highlight the position defined by the x and y value. The highlight
        point will be drawn in the ref_axes.
        
        Parameters
        ----------
            x, y: int or list of ints
                The coordinates of the point(s) to highlight
            ref_axes : int, optional
                The index of the axes
            update_plot : boolean, optional
                Whether to update the plot or not, if this is False the highlight
                point will be displayed **after** the PlotCanvas.commitUpdate()
                function has been called, default: True
            text : String or list of Strings
                Some text to write on the given points
        """
        
        if not isinstance(x, (list, tuple)):
            x = [x]
        if not isinstance(y, (list, tuple)):
            y = [y]
            
        if self.marker != "":
            marker = self.marker
        else:
            marker = "o"
        
        if my_utilities.is_numeric(self.markersize):
            markersize = my_utilities.force_float(self.markersize) + 1
        else:
            markersize = 1
        
        if text != None and not isinstance(text, (list, tuple)):
            text = [text]
        
        if isinstance(text, (list, tuple)):
            fig = self.getFigure()
            transform_matrix = fig.dpi_scale_trans.inverted()
            
            for i, t in enumerate(text):
                if isinstance(ref_axes, (list, tuple)) and i < len(ref_axes):
                    axes_index = self._getRefAxes(ref_axes[i])
                else:
                    axes_index = self._getRefAxes(ref_axes)
                
                axes = self.axes[axes_index]
                    
                bbox = axes.get_window_extent().transformed(transform_matrix)
                height = bbox.height * fig.dpi
                
                lim = axes.get_ylim()
                o = (self.markersize + 2) / height * abs(lim[0] - lim[1])
                
                y_avg = my_utilities.mean_std(y)
                y_avg = y_avg[0]
                
                if i >= 0 and i < len(x) and i < len(y):
                    o = (1 if y[i] >= y_avg else -1) * o
        
                    self._highlights.append(axes.plot(
                            x[i], y[i], 
                            marker = marker, 
                            linestyle = "None", 
                            zorder = PlotCanvas.HIGHLIGHT_Z_ORDER,
                            markersize = markersize,
                            color = "r"
                    ))
                    
                    self._highlight_texts.append(axes.annotate(
                        str(t),
                        xycoords='data',
                        textcoords='data',
                        xy=(x[i], y[i]), 
                        xytext=(x[i], y[i] + o),
                        horizontalalignment='center',
                        zorder = PlotCanvas.HIGHLIGHT_TEXT_Z_ORDER
                    ))
        
        if update_plot:
            self.commitUpdate(False)
    
    def clearHighlights(self, update_plot = True):
        """Removes all highlighted points
        
        Parameters
        ----------
            update_plot : boolean, optional
                Whether to update the plot or not, if this is False the highlight
                point will be displayed **after** the PlotCanvas.commitUpdate()
                function has been called, default: True
        """
        
        for patch in self._highlights + self._highlight_texts:
            if isinstance(patch, matplotlib.artist.Artist):
                patch.remove()
            elif isinstance(patch, (list, tuple)):
                for line in patch:
                    if isinstance(line, matplotlib.artist.Artist):
                        line.remove()
        
        self._highlights = []
        self._highlight_texts = []
        
        if update_plot:
            self.commitUpdate(False)
    
    def updateTitle(self, title = None):
        """Sets the title of the Figure.
        This is an update method, they can be called after the PlotData has been
        plotted. To commit all the updates and display them use the PlotCanvas.commitUpdate()
        function.
        
        Parameters
        ----------
            title : String, optional
                The new title to set
        """
        
        # settings for the title
        fontsize = 10
        y = 1
        # push the title a little bit higer if there is an upper x axis
        if self._twin_x:
            y = 1.20
        
        # check if there is a title, if not use the current title
        if not isinstance(title, str):
            if isinstance(self._title, str) and len(self._title) > 0:
                title = self._title
            else:
                for axes in self.axes:
                    if isinstance(axes.title, str) and len(axes.title) > 0:
                        title = axes.title
                        break
        elif isinstance(title, str) and title != "":
            self._title = title
        
        if not isinstance(title, str):
            title = ""
            
        title = self.autoBreakTitle(title)
        self._title_lines = title.count("\n") + 1
        
        # set title only in the first axes, remove all other titles
        for i, axes in enumerate(self.axes):
            if i == 0:
                self.axes[i].set_title(title, y=y, fontsize=fontsize)
            else:
                self.axes[i].set_title("")
            
        
    def updateLineData(self, xdata, ydata, plot_data_index, line_index = 0):
        """Sets x and y data of the line with the line_index of the given plot_data_index.
        This will change the plot line to a new line.
        The plot data should normally contain only one data set for a line. This means
        that the line_index is (nearly) always 0.
        This is an update method, they can be called after the PlotData has been
        plotted. To commit all the updates and display them use the PlotCanvas.commitUpdate()
        function.
        
        Parameters
        ----------
            xdata, ydata : list of floats
                The new x and y data as a list
            plot_data_index : int
                The index of the plot data
            line_index : int, optional
                The index of the line to update, default: 0
        """
        
        if my_utilities.is_numeric(plot_data_index) and my_utilities.is_numeric(line_index):
            try:
                line = self._plots[plot_data_index][line_index]
            except IndexError:
                return False
        else:
            return False
        
        line.set_data(xdata, ydata)
        return True
    
    def commitUpdate(self, relimit = True):
        """Commits all the updates. This means that the updates in the tile and 
        the line data will be displayed. If the graph is not plotted or will be
        replotted because of using the plotData() method this is not necessary.
        Make sure to update everything before calling this method, it is very
        resource intensive and you should try to use it as less as possible.
        
        Parameters
        ----------
            relimit : boolean, optional
                Whether to relimit the axis so they will have new limits, use false
                if you know the data limits did not change, this will save a
                lot of speed, default: True
        """
        
        fig = self.getFigure()
        
        if relimit:
            for index, axes in enumerate(self.axes):
                axes.relim()
                axes.autoscale_view()
            
        fig.canvas.draw()
        fig.canvas.flush_events()
        self.fixLayout()
    
    def autoBreakTitle(self, title):
        """Auto break the given title. This will guarantee that the title is
        not too long for matplotlib. This returns a string with inserted '\n's
        
        Parameters
        ----------
            title : string
                The title to split into multiple lines if necessary
                
        Returns
        -------
            string
                The title with inserted '\n's
        """
        
        if isinstance(title, str):
            text = textwrap.wrap(title, 60)
            
            if len(text) > 0:
                return functools.reduce(lambda y, x: y + (("\n" + x) if len(x) > 2 else x), text)
        
        return ""
    
    def actionClick(self, event):
        """The action method for the datapoint selection"""
        
        if self.selecting_allowed:
            artist = event.artist
            index = event.ind
            # up/down sweep
            index = index[0]
                
            plot_data_index = -1
            
            for i, artists in enumerate(self._plots):
                for art in artists:
                    if artist == art:
                        plot_data_index = i
            
            if plot_data_index >= 0 and plot_data_index < len(self._plot_data):
                if event.mouseevent.dblclick:
                    self.datapointDoubleClicked.emit(self._plot_data[plot_data_index], index, plot_data_index)
                else:
                    self.datapointClicked.emit(self._plot_data[plot_data_index], index, plot_data_index)
    
    def getFigure(self):
        """Get the figure of the plot canvas
        
        Returns
        -------
            Figure
                The figure
        """
        
        # figure is the same for all axes
        return self.axes[0].get_figure()
    
    def clear(self):
        """Clear the PlotCanvas. This removes all graphs and all settings"""
        
        # create the plot_data
        self._plot_data = []
        
        # whether selecting a datapoint is allowed or not
        self.selecting_allowed = False
        
        self._x_label = ""
        self._y_label = ""
        
        self._title = ""
        self.marker = "h"
        self.linestyle = "solid"
        self.linewidth = 0.4
        self.markersize = 6
        self.color = ""
        self._color_cycler = ""
        
        self._title_lines = 0
        self._print_unit = True
        
        self.print_legend = True
        
        # the plots from the matplotlib
        self._plots = []
        
        # clear axes
        for axes in self.axes:
            axes.cla()
    
    def resizeEvent(self, event):
        """Handle the resize event"""
        
        # perform the default resizing
        super(PlotCanvas, self).resizeEvent(event)
        # fix the layout
        self.fixLayout()
    
    def getToolbarWidget(self):
        """Get the toolbar for this plot canvas
        
        Returns
        -------
            QWidget
                The toolbar
        """
        
        return self._toolbar_widget
    
    def fixLayout(self):
        """Fix the layout of the plot"""
        
#        y = 1 - 0.03 * self._title_lines
        
        if len(self.axes) > 0 and len(self._plot_data) > 0 and len(self._plots) > 0:
            fig = self.getFigure()
            try:
                fig.tight_layout()
            except (ValueError, np.linalg.LinAlgError) as e:
                print("PlotCanvas.fixLayout(): " + str(e))
    #        fig.tight_layout(rect=[0, 0.03, 1, y])
    #        fig.subplots_adjust(top=0.85)
        
    def contextMenuEvent(self, event):
        """Handles the context menu"""
        
        self._context_menu.exec(event.globalPos())