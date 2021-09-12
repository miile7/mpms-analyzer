# -*- coding: utf-8 -*-
"""
Created on Mon Dec  4 12:44:56 2017

@author: miile7
"""

from PyQt5 import QtCore, QtGui, QtWidgets
import matplotlib.colors
import matplotlib.artist
import matplotlib.backend_bases

import View.PlotCanvas
import View.MainWindow
import DataHandling.DataPoint
import my_utilities
import Constants

class DataPointViewer(QtWidgets.QDialog):
    def __init__(self, datacontainer, parent=None, *indices, **kwargs):
        """Initialize the DataPointViewer
        
        Parameters
        ----------
            datacontainer : DataContainer
                The datacontainer of which to plot the datapoints
            parent : QtWidgets.QWidget, optional
                The parent
            indices : list of int
                The indices 
        """
        
        super(DataPointViewer, self).__init__(parent, QtCore.Qt.WindowCloseButtonHint |
                QtCore.Qt.WindowMaximizeButtonHint | QtCore.Qt.WindowMinimizeButtonHint)
        
        # set title and icon
        self.setWindowTitle("View datapoints")
        self.setWindowIcon(QtGui.QIcon(View.MainWindow.MainWindow.ICON))
        self.setStyleSheet("QDialog{background: #ffffff;}")
        self.setModal(False)
        
        # save datacontainer
        self._datacontainer = datacontainer
        
        # the referece datacontainer plot
        self._datacontainer_plot = None
        
        # a naming callback, this is not used in general, this should be a function
        # which returns a string which is the name for each datapoint
        self._name_callback = None
        if isinstance(kwargs, dict) and "name_callback" in kwargs and callable(kwargs["name_callback"]):
            self._name_callback = kwargs["name_callback"]
        
        # all the PlotCanvas
        self._plots = []
        
        # grid size
        self._grid_width = 2
        self._grid_height = 2
        
        if isinstance(kwargs, dict) and "grid_width" in kwargs and my_utilities.is_numeric(kwargs["grid_width"]):
            self._grid_width = int(kwargs["grid_width"])
        
        if isinstance(kwargs, dict) and "grid_height" in kwargs and my_utilities.is_numeric(kwargs["grid_width"]):
            self._grid_height = int(kwargs["grid_height"])
        
        # grid size
        n = self._grid_width * self._grid_height
        
        # the indices of the plot data in the plot canvas
        self._plot_data_background_index = [None] * n
        self._plot_data_original_index = [None] * n
        self._plot_data_removed_index = [None] * n
        self._plot_data_fit_index = [None] * n
        self._plot_data_raw_index = [None] * n
        self._plot_data_raw_fit_index = [None] * n
        self._indices_axes = [None] * n
        
        # save the indices
        self._indices = []
        self.fixIndices(indices)
        
        # the layout
        layout = QtWidgets.QVBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # horizontal splitter
        vertical_splitter = QtWidgets.QSplitter(QtCore.Qt.Vertical)
        layout.addWidget(vertical_splitter)
        
        # the header group
        horizontal_splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        vertical_splitter.addWidget(horizontal_splitter)
        
        # the legend layout
        self._legend = QtWidgets.QGridLayout()
        self._legend.setSpacing(5)
        self._legend.setContentsMargins(5, 5, 5, 5)
        
        legend_widget = QtWidgets.QWidget()
        legend_widget.setLayout(self._legend)
        horizontal_splitter.addWidget(legend_widget)
        
        # the stats of the current datapoints
        self._stats = QtWidgets.QGridLayout()
        self._stats.setSpacing(5)
        self._stats.setContentsMargins(5, 2, 5, 2)
        
        stats_widget = QtWidgets.QWidget()
        stats_widget.setLayout(self._stats)
        horizontal_splitter.addWidget(stats_widget)
        
        # the plot grid
        self._grid = QtWidgets.QGridLayout()
        self._grid.setSpacing(0)
        self._grid.setContentsMargins(0, 0, 0, 0)
        
        grid_widget = QtWidgets.QWidget()
        grid_widget.setLayout(self._grid)
        
        vertical_splitter.addWidget(grid_widget)
        
        # the box for the next and prev buttons
        button_box = QtWidgets.QHBoxLayout()
        
        # the step list
        steps = (4, 24, float("inf"))
        
        # adding previous buttons
        for index, step in enumerate(reversed(steps)):
            step *= -1
            i = "\u25C4"
            if step == float("-inf"):
                t = 3*i + " (First)"
            elif index + 2 == len(steps):
                t = 2*i + " ({0:+})".format(step)
            else:
                t = i + " ({0:+})".format(step)
                
            # create the button and add it
            button = QtWidgets.QPushButton(t)
            button.setProperty("step", step)
            button.clicked.connect(self.actionNextPrevButton)
            button_box.addWidget(button)
        
        # add a spacer
        button_box.addStretch(1)
        
        # create the index inputs for the datapoint indices
        self._indices_edits = QtWidgets.QHBoxLayout()
        self.setIndexEdits()
        button_box.addItem(self._indices_edits)
        
        # the "Go" button
        update_button = QtWidgets.QPushButton("Go")
        update_button.clicked.connect(self.actionLoadIndices)
        button_box.addWidget(update_button)
        
        # add a spacer
        button_box.addStretch(1)
        
        # adding next buttons
        for index, step in enumerate(steps):
            i = "\u25BA"
            if step == float("inf"):
                t = "(Last) " + 3*i
            elif index + 2 == len(steps):
                t = "({0:+}) ".format(step) + 2*i
            else:
                t = "({0:+}) ".format(step) + i
                
            button = QtWidgets.QPushButton(t)
            button.setProperty("step", step)
            button.clicked.connect(self.actionNextPrevButton)
            button_box.addWidget(button)
        
        # add the button box
        button_box_widget = QtWidgets.QWidget()
        button_box_widget.setLayout(button_box)
        layout.addWidget(button_box_widget)
        
        self._more_widget = None
        
        # plot the grid
        self.plotDataPointGrid()
        # draw the legend
        self.drawLegend()
        # update the stats
        self.genereteStats()
        # highlight points
        self.showPointsInDataContainerPlot()
        
        self.setLayout(layout)
    
    def setDataContainerPlot(self, plot):
        """Set a PlotCanvas where to highlight the currently shown datapoint in
        
        Parameters
        ----------
            plot : PlotCanvas
                The plot canvas where the currently shown DataContainer is shown
        """
        
        if (isinstance(plot, View.PlotCanvas.PlotCanvas)):
            self._datacontainer_plot = plot
            
            # highlight points
            self.showPointsInDataContainerPlot()
    
    def setIndexEdits(self):
        """Set the edits for the index input in the bottom"""
        
        self.fixIndices()
        
        # the grid size
        n = self._grid_width * self._grid_height
        # the datapoint count
        l = len(self._datacontainer.datapoints)
        # the size
        size = QtCore.QSize(25, 25)
        
        # if grid size is more than the current edits count
        if n > self._indices_edits.count():
            for i in range(0, n - self._indices_edits.count()):
                # create the line edtis
                index_edit = QtWidgets.QLineEdit()
                index_edit.setValidator(QtGui.QIntValidator(0, l))
                index_edit.setFixedSize(size)
                
                # set the text of the current index
                if len(self._indices) > i:
                    index_edit.setText(str(self._indices[i]))
                else:
                    # increase the last index
                    index_edit.setText(str(int(self._indices[-1]) + (i - len(self._indices) + 1)))
                
                # add the edit
                self._indices_edits.addWidget(index_edit)
        elif n < self._indices_edits.count():
            for i in range(self._indices_edits.count() - 1, n, -1):
                # receive the edit
                item = self._indices_edits.takeAt(i)
                widget = item.widget()
                
                # remve the widget
                if widget != None:
                    self._indices_edits.removeWidget(widget)
                del widget
                del item
    
    def plotDataPointGrid(self):
        """Plot the grid of datapoints"""
        
        # the index of the datapoint
        index = 0
        
        # fixes the indices
        self.fixIndices()
        
        # go through the grid
        counter = 0
        for j in range(0, self._grid_height):
            self._plots.append([])
            for i in range(0, self._grid_width):
                # the indiex of the datapoint
                index = self._indices[counter]
                
                # the datapoint to plot
                datapoint = self._datacontainer.datapoints[index]
                 
                # check the sweep direction
                direction = datapoint.isUpSweep()
                if direction:
                    direction = "Up"
                else:
                    direction = "Down"
                    
                # prepare plot data
                plot_data_background = None
                plot_data_original = None
                plot_data_removed = None
                plot_data_fit = None
                plot_data_raw = None
                plot_data_raw_fit = None
                    
                # the data how the background data has been removed, this is saved
                # in the remove method directly and comes directly from the calculation.py
                background_remove_data = datapoint.background_remove_data
                background_remove_labels = datapoint.background_remove_labels
                
                # check whether there is data that has been removed
                if isinstance(background_remove_data, (list, tuple)):
                    # prepare all the data lists
                    original_data = []
                    background_data = []
                    result_data = []
                    fit_data = []
                    fit_raw_data = []
                    raw_data = []
                    
                    # conversion table for converting index into position
                    index_position_conversion = {}
                    
                    # add the remove data to the specific plot data list
                    for data in background_remove_data:
                        if isinstance(data, (list, tuple)):
                            if len(data) > 0:
                                # the x value
                                x = data[0]
                                
                                # the original data (with background)
                                if len(data) > 1:
                                    original_data.append((x, data[1]))
                                
                                # the background data alone
                                if len(data) > 2:
                                    background_data.append((x, data[2]))
                                
                                # the result so the data without the background
                                if len(data) > 3:
                                    result_data.append((x, data[3]))
                    
                    # check if there are labels for the data, they are set in the
                    # calculation.py too
                    if (background_remove_labels == None or 
                        not isinstance(background_remove_labels, (list, tuple)) or
                        len(background_remove_labels) < 2):
                        x_label = ""
                        y_label = ""
                    else:
                        x_label = background_remove_labels[0]
                        y_label = background_remove_labels[1]
                    
                    # set the raw data for the axis that have been used for removing
                    # the data
                    if (datapoint.background_remove_axis != None and 
                        isinstance(datapoint.background_remove_axis, (tuple, list)) and
                        len(datapoint.background_remove_axis) >= 2):
                        raw_data = datapoint.getPlotData(
                                datapoint.background_remove_axis[0],
                                datapoint.background_remove_axis[1],
                                plain_lists=True)
                        
                        # the y values of the results
                        result_y = [item[1] for item in result_data]
                        
                        for ind, x in enumerate(raw_data[0]):
                            if ind < len(raw_data[1]):
                                # the y value to search
                                y = raw_data[1][ind]
                                
                                if y in result_y:
                                    # index for the y value
                                    y_index = result_y.index(y)
                                    # remove this y value, if there are two exact
                                    # same y values this will not cause an error
                                    # when the value is removed
                                    result_y[y_index] = None
                                    
                                    # save in the conversion dict
                                    index_position_conversion[x] = y_index
                    
                    # the fit data depending on the raw position
                    fit_raw_data = datapoint.getPlotData(
                            datapoint.background_remove_axis[0],
                            DataHandling.DataPoint.DataPoint.FIT,
                            plain_lists=True)
                    
                    # convert the raw fit data to fit data depending on the index
                    # for better comparism
                    if (fit_raw_data != None and isinstance(fit_raw_data, (list, tuple)) and
                        len(fit_raw_data) >= 2):
                        
                        for x, y in zip(fit_raw_data[0], fit_raw_data[1]):
                            if x in index_position_conversion:
                                fit_data.append((index_position_conversion[x], y))
                    
                    # the data which is used without the background
                    plot_data_original = DataHandling.PlotData.PlotData(
                            x=[it[0] for it in original_data], 
                            y=[it[1] for it in original_data],
                            title="Data with background (index)",
                            x_label=x_label,
                            y_label=y_label)
                    
                    # the data which is used without the background
                    plot_data_background = DataHandling.PlotData.PlotData(
                            x=[it[0] for it in background_data], 
                            y=[it[1] for it in background_data],
                            title="Background alone (index)",
                            x_label=x_label,
                            y_label=y_label)
                    
                    # the data which is used without the background
                    plot_data_removed = DataHandling.PlotData.PlotData(
                            x=[it[0] for it in result_data], 
                            y=[it[1] for it in result_data],
                            title="Background removed (index)",
                            x_label=x_label,
                            y_label=y_label)
                    
                    # the raw voltage over the raw position data, the result
                    # without the background
                    plot_data_raw = datapoint.getPlotData(
                                datapoint.background_remove_axis[0],
                                datapoint.background_remove_axis[1])
                    plot_data_raw.title = "Background removed (position)"
                    
                    if len(fit_data) > 0:
                        # the fit depending on the indices
                        plot_data_fit = DataHandling.PlotData.PlotData(
                                x=[it[0] for it in fit_data], 
                                y=[it[1] for it in fit_data],
                                title="Fit (background removed - index)",
                                x_label=x_label,
                                y_label=y_label)
                    else:
                        plot_data_fit = None
                    
                    # the fit depending on the indices
                    if fit_raw_data != None and len(fit_raw_data) > 0:
                        plot_data_raw_fit = DataHandling.PlotData.PlotData(
                                x=fit_raw_data[0], 
                                y=fit_raw_data[1],
                                title="Fit (background removed - position)",
                                x_label=datapoint.background_remove_axis[0],
                                y_label=y_label)
                    else:
                        plot_data_raw_fit = None
                    
#                    print("DataPointViewer.plotDataPointGrid(): raw_data: ", raw_data)
                        
                else:
                    # there is no background data, just plot the fit and the 
                    # raw data
                    plot_data_raw = datapoint.getPlotData(
                            DataHandling.DataPoint.DataPoint.RAW_POSITION,
                            DataHandling.DataPoint.DataPoint.RAW_VOLTAGE)
                    
                    plot_data_raw.title = "Raw voltage"
                    plot_data_raw.y_label = "Voltage"
                    plot_data_raw.y_unit = "V"
                    
                    plot_data_raw_fit = None
                    
                    try:
                        plot_data_raw_fit = datapoint.getPlotData(
                                DataHandling.DataPoint.DataPoint.RAW_POSITION,
                                DataHandling.DataPoint.DataPoint.FIT)
                        
                        plot_data_raw_fit.title = "Fit"
                        plot_data_raw_fit.y_label = plot_data_raw.y_label
                        plot_data_raw_fit.y_unit = plot_data_raw.y_unit
                    except RuntimeError:
                        pass
                    
                # get the item in the grid position
                item = self._grid.itemAtPosition(j, i)
                
                if (item != None and item.widget() != None and 
                    isinstance(item.widget(), View.PlotCanvas.PlotCanvas)):
                    # the current item in this grid position is a plotcanvas
                    # already, assume that is is formatted correctly so change
                    # the plot data only.
                    # This speeds up the plotting process about 50 times
                    plot = item.widget()
                    
                    # update the background data
                    if isinstance(plot_data_background, DataHandling.PlotData.PlotData):
                        plot.updateLineData(plot_data_background.x, 
                                            plot_data_background.y,
                                            self._plot_data_background_index[counter],
                                            0)
                    
                    # update the original data (with background)
                    if isinstance(plot_data_original, DataHandling.PlotData.PlotData):
                        plot.updateLineData(plot_data_original.x, 
                                            plot_data_original.y,
                                            self._plot_data_original_index[counter],
                                            0)
                    
                    # update the data with removed background
                    if isinstance(plot_data_removed, DataHandling.PlotData.PlotData):
                        plot.updateLineData(plot_data_removed.x, 
                                            plot_data_removed.y,
                                            self._plot_data_removed_index[counter],
                                            0)
                    
                    # update the fit data (depending on index)
                    if isinstance(plot_data_fit, DataHandling.PlotData.PlotData):
                        plot.updateLineData(plot_data_fit.x, 
                                            plot_data_fit.y,
                                            self._plot_data_fit_index[counter],
                                            0)
                    
                    # update the data with removed background, depending on
                    # the raw position
                    if isinstance(plot_data_raw, DataHandling.PlotData.PlotData):
                        plot.updateLineData(plot_data_raw.x, 
                                            plot_data_raw.y,
                                            self._plot_data_raw_index[counter],
                                            0)
                        
                    # update the fit with removed background, depending on
                    # the raw position
                    if isinstance(plot_data_raw_fit, DataHandling.PlotData.PlotData):
                        plot.updateLineData(plot_data_raw_fit.x, 
                                            plot_data_raw_fit.y,
                                            self._plot_data_raw_fit_index[counter],
                                            0)
                    
                    # update the title
                    plot.updateTitle(self.getTitleForDatapoint(index, direction, "grid"))
                    
                    # invert or re-invert (="uninvert") the axis if needed,
                    # have a look at the else clause to see why this is needed
                    if (direction == "Down" and not plot.xAxisIsInverted(self._indices_axes[counter]) or
                        direction == "Up" and plot.xAxisIsInverted(self._indices_axes[counter])):
                        plot.invertXAxis(self._indices_axes[counter])
                                     
                    # apply all the updates to the plot canvas which will 
                    # redraw only the needed parts
                    plot.commitUpdate()
                else:
                    # create a plot canvas
                    plot = View.PlotCanvas.PlotCanvas(self, 4, 3)
                    self._indices_axes[counter] = plot.current_axes
                    
                    # set the title, perevent legend printing
                    plot.title = self.getTitleForDatapoint(index, direction, "grid")
                    plot.print_legend = False
                    
                    # background data style (thiner, solid line, no marker)
                    plot.linestyle = "solid"
                    plot.marker = ""
                    plot.markersize = 3
                    plot.linewidth = 1
                    raw_marker = "D"
                    
                    # draw the background data (dependent on indices)
                    if isinstance(plot_data_background, DataHandling.PlotData.PlotData):
                        plot.color = "limegreen"
                        self._plot_data_background_index[counter] = plot.addPlotData(plot_data_background)
                    else:
                        self._plot_data_background_index[counter] = None
                    
                    # draw the original data (with background - dependent on indices)
                    if isinstance(plot_data_original, DataHandling.PlotData.PlotData):
                        plot.color = "darkgreen"
                        self._plot_data_original_index[counter] = plot.addPlotData(plot_data_original)
                    else:
                        self._plot_data_original_index[counter] = None
                    
                    # result data style (no line, hexagon markers)
                    plot.linestyle = "None"
                    plot.marker = raw_marker
                    
                    # draw the data with removed background (dependent on indices)
                    if isinstance(plot_data_removed, DataHandling.PlotData.PlotData):
                        plot.color = "lightsalmon"
                        self._plot_data_removed_index[counter] = plot.addPlotData(plot_data_removed)
                    else:
                        self._plot_data_removed_index[counter] = None
                    
                    # fit style (thicker, solid line, no marker)
                    plot.linewidth = 2
                    plot.linestyle = "solid"
                    plot.marker = ""
                    
                    # draw the fit (dependent on indices)
                    if isinstance(plot_data_fit, DataHandling.PlotData.PlotData):
                        plot.color = "crimson"
                        self._plot_data_fit_index[counter] = plot.addPlotData(plot_data_fit)
                    else:
                        self._plot_data_fit_index[counter] = None
                    
                    # create a new x axis, this is for position dependent plots
                    if plot.getNumberOfPlotData() > 0:
                        plot.addNewXAxis()
                    
                    # result data style (no line, hexagon markers)
                    plot.linestyle = "None"
                    plot.marker = raw_marker
                    
                    # draw the result data (dependent on position)
                    if isinstance(plot_data_raw, DataHandling.PlotData.PlotData):
                        plot.color = "lightsteelblue"
                        self._plot_data_raw_index[counter] = plot.addPlotData(plot_data_raw)
                    else:
                        self._plot_data_raw_index[counter] = None
                    
                    # fit style (thicker, solid line, no marker)
                    plot.linestyle = "solid"
                    plot.marker = ""
                    
                    # draw the fit (with removed background, depending on position)
                    if isinstance(plot_data_raw_fit, DataHandling.PlotData.PlotData):
                        plot.color = "navy"
                        self._plot_data_raw_fit_index[counter] = plot.addPlotData(plot_data_raw_fit)
                    else:
                        self._plot_data_raw_fit_index[counter] = None
                    
                    # If the sweep direction is down the position is growing
                    # with the index, if the sweep direction is up the
                    # position is decreasing with the index. This will cause
                    # an mirrored plot mirrored by the "center" of the indices,
                    # to prevent this just mirror the x axis
                    if direction == "Down":
                        plot.invertXAxis(self._indices_axes[counter])
                    
                    # reset layout
                    plot.fixLayout()
                    
                    # add the plot to the layout
                    self._grid.addWidget(plot, j, i)
            
                counter += 1
    
    def getTitleForDatapoint(self, index, direction, mode):
        """Get the name for the datapoint
        
        Parameters
        ----------
            index : int
                The index of the datapoint in the parent datacontainer
            direction : String
                "Up", "Down" or None whether the datapoint is an up sweep or a down 
                sweep, None when the direction is not known (this is in mode="stats")
            mode : String
                The mode, this can be "grid" or "stats" which tells where the
                function is called from
                
        Retruns
        -------
            String
                The name of the datapoint
        """
        
        if self._name_callback != None and callable(self._name_callback):
            text = self._name_callback(index, direction, mode)
            
            if isinstance(text, str):
                return text
        
        if mode == "stats":
            return "#<b>{}</b>".format(index)
        else:
            return "Datapoint #{} ({} sweep)".format(index, direction)
    
    def drawLegend(self):
        """Draw the legend"""
        
        # all the lines, sort by name
        lines = {}
        for i in range(0, self._grid_width):
            for j in range(0, self._grid_height):
                item = self._grid.itemAtPosition(j, i)
                if (item != None and item.widget() != None and 
                    isinstance(item.widget(), View.PlotCanvas.PlotCanvas)):
                    # the plot canvas item
                    plot = item.widget()
                    
                    for axes in plot.axes:
                        for line in axes.get_lines():
                            name = line.get_label()
                            if line.get_label() not in lines:
                                # add the line if it is not in the collection
                                # already
                                lines[name] = []
                                
                            lines[name].append(line)
        
        # number of columns
        cols = 2
        # index of the start column
        sc = 0
        # current column index
        cc = sc
        # current row index
        cr = 0
        
        self._legend.addItem(QtWidgets.QSpacerItem(1, 5, QtWidgets.QSizePolicy.Minimum,
                                                        QtWidgets.QSizePolicy.Minimum),
                    0, 0, 1, cols)
        
        # go through each line
        for name in lines:
            line = lines[name][0]
            
            # create the checkbox
            checkbox = QtWidgets.QCheckBox()
            checkbox.setChecked(True)
            checkbox.setProperty("lines", lines[name])
            checkbox.toggled.connect(self.actionLegendCheckboxToggle)
            
            # receive the color
            color = matplotlib.colors.to_rgba_array(line.get_color())
            if len(color) == 0:
                color = [0,0,0,1]
            else:
                color = color[0]
            
            # matplotlib uses color with 0 <= color <= 1, qt uses colors with
            # 0 <= color <= 255
            color = list(map(lambda c: int(c*255), color))
            
            # line width in points (pt)
            linewidth = line.get_linewidth()
            dpi = plot.getFigure().dpi
            # convert pt to px
            linewidth = linewidth / 72 * dpi
            
            marker = line.get_marker()
            
            # convert linestyle to Qt linestyle
            linestyle = line.get_linestyle().lower()
            if linestyle in ("--", "dashed"):
                linestyle = QtCore.Qt.DashLine
            elif linestyle in ("-.", "dashdot"):
                linestyle = QtCore.Qt.DashDotLine
            elif linestyle in (":", "dotted"):
                linestyle = QtCore.Qt.DotLine
            elif linestyle in ("", " ", "none"):
                linestyle = QtCore.Qt.NoPen
            else:
                linestyle = QtCore.Qt.SolidLine
            
            # the lineheight
            lh = 12
            # center of the legend line
            h = (lh - linewidth)/2
            # the width
            w = 30
            # the vertical padding
            p = 2
            # marker width
            mw = 12
            # marker height
            mh = 12
            # start of the marker x pos
            mx = (w - 2 * p) / 2
            # start of the marker y pos
            my = h
            
            # create the line in front of the legend
            picture = QtGui.QPicture()
            painter = QtGui.QPainter(picture)
            color = QtGui.QColor(color[0], color[1], color[2], color[3])
            
            # set all the styles for the line
            pen = QtGui.QPen()
            pen.setColor(color)
            pen.setWidth(linewidth)
            pen.setStyle(linestyle)
            pen.setCapStyle(QtCore.Qt.SquareCap)
            
            # set the fill style
            brush = QtGui.QBrush(QtCore.Qt.SolidPattern)
            brush.setColor(color)
            
            # draw the line
            painter.setRenderHint(QtGui.QPainter.Antialiasing)
            painter.setPen(pen)
            painter.setBrush(brush)
            painter.drawLine(p, h, w, h)
            
            # draw the marker
            if marker == "d" or marker == "D":
                polygon = QtGui.QPolygonF()
                polygon.append(QtCore.QPointF(mx, my))
                polygon.append(QtCore.QPointF(mx + mw/2, my + mh/2))
                polygon.append(QtCore.QPointF(mx + mw, my))
                polygon.append(QtCore.QPointF(mx + mw/2, my - mh/2))
                    
                painter.drawPolygon(polygon)
            elif marker != "" and marker != "None" and marker != "none" and marker != None:
                painter.drawEllipse(QtCore.QPointF(mx + mw/2, my), mw/2, mh/2)
            
            painter.end()
            
            # add the line image to a label to get a QWidget that can be added
            # in a layout
            image = QtWidgets.QLabel()
            image.setPicture(picture)
            image.setFixedSize(w + 2 * p, lh)
            image.setBuddy(checkbox)
            
            # the label for the name of the line
            label = QtWidgets.QLabel(line.get_label())
            label.setBuddy(checkbox)
            
            # the legend element layout
            legend_layout = QtWidgets.QHBoxLayout()
            legend_layout.addItem(QtWidgets.QSpacerItem(5, 1, QtWidgets.QSizePolicy.Fixed,
                                                        QtWidgets.QSizePolicy.Minimum))
            # add all the contents
            legend_layout.addWidget(checkbox)
            legend_layout.addWidget(image)
            legend_layout.addWidget(label)
            legend_layout.addStretch(1)
            
            # add the layout to the legend_widget
            legend_widget = QtWidgets.QWidget()
            legend_widget.setLayout(legend_layout)
            
            # add the legend widget
            self._legend.addWidget(legend_widget, cr, cc)
            
            # find the next position where to add the next label
            if cc + 1 >= cols:
                cc = sc
                cr += 1
            else:
                cc += 1
                
        self._legend.addItem(QtWidgets.QSpacerItem(25, 5, QtWidgets.QSizePolicy.Expanding,
                                                        QtWidgets.QSizePolicy.Minimum),
                    cr, 0, 1, cols)
        self._legend.setRowStretch(cr, 1)
            
    
    def updateIndexEdits(self):
        """Update the index edits depending on the current indices"""
        
        # the grid size
        n = self._grid_width * self._grid_height
        
        # fixes the indices
        self.fixIndices()
        
        # check if the index size and the grid size are the same
        if self._indices_edits.count() != n:
            self.setIndexEdits()
        
        # go through all the index edits
        for i in range(0, self._indices_edits.count()):
            item = self._indices_edits.itemAt(i)
            widget = item.widget()
            
            # set the text
            if widget != None and isinstance(widget, QtWidgets.QLineEdit):
                widget.setText(str(self._indices[i]))
    
    def genereteStats(self):
        """Generate the stats. This is the top left box of the dialog"""
        
        # fixes the indices
        self.fixIndices()
        
        col = 0
        
        # print header
        self._stats.addWidget(QtWidgets.QLabel("Datapoint:"), col, 0)
        col += 1
        for index in self._indices:
            more_button = QtWidgets.QPushButton("...")
            more_button.setProperty("index", index)
            more_button.clicked.connect(self._actionShowMore)
            more_button.setFixedSize(28, 15)
            
            layout = QtWidgets.QHBoxLayout()
            
            layout.addWidget(QtWidgets.QLabel(self.getTitleForDatapoint(index, None,"stats")))
            layout.addStretch(1)
            layout.addWidget(more_button)
            
            self._stats.addLayout(layout, 0, col)
                                  
            col += 1
        col = 0
        
        self._stats.addWidget(View.MainWindow.MainWindow.createSeparatorLine(), 1, 0, 1, 5)
        
        # print the data header
        self._stats.addWidget(QtWidgets.QLabel("Fit amplitude:"), 2, 0)
        self._stats.addWidget(QtWidgets.QLabel("Fit drift:"), 3, 0)
        self._stats.addWidget(QtWidgets.QLabel("Fit y offset:"), 4, 0)
        self._stats.addWidget(QtWidgets.QLabel("Fit x offset:"), 5, 0)
        self._stats.addWidget(QtWidgets.QLabel("H:"), 6, 0)
        self._stats.addWidget(QtWidgets.QLabel("T:"), 7, 0)
        
        self.updateStats()
    
    def updateStats(self):
        """Update the stats. This is the top left box of the dialog"""
        
        # fixes the indices
        self.fixIndices()
        
        # the data of each datapoint
        col = 1
        for index in self._indices:
            stats = [self.getTitleForDatapoint(index, None,"stats"), None]
            # prepare the stats for each data point index
            fit_data = self._datacontainer.datapoints[index].getRawFitResults()
            if isinstance(fit_data, (list, tuple)) and len(fit_data) >= 2:
                stats += zip(list(fit_data[0]), list(fit_data[1]))
            else:
                stats += 4 * ["-"]
            
            result = self._datacontainer.datapoints[index].getEnvironmentVariableAvg(
                    DataHandling.DataContainer.DataContainer.FIELD)
            if isinstance(result, (list, tuple)):
                stats.append(result[0])
            else:
                stats.append("-")
            
            result = self._datacontainer.datapoints[index].getEnvironmentVariableAvg(
                    DataHandling.DataContainer.DataContainer.TEMPERATURE)
            if isinstance(result, (list, tuple)):
                stats.append(result[0])
            else:
                stats.append("-")
            
            digits = 2
            
            # print the rows
            for i, text in enumerate(stats):
                if text == None:
                    # none is separator
                    continue
                elif isinstance(text, (list, tuple)):
                    value = my_utilities.force_float(text[0])
                    error = my_utilities.force_float(text[1])
                    
                    error_format = "f"
                    if round(error, digits) == 0:
                        error_format = "E"
                    
                    text = ("{:+." + str(digits) + "f}\u00B1{:." + str(digits) + error_format + 
                            "}").format(value, 
                            error)
                elif my_utilities.is_numeric(text):
                    # format the numbers
                    text = ("{:+." + str(digits) + "f}").format(my_utilities.force_float(text))
                else:
                    text = str(text)
                
                item = self._stats.itemAtPosition(i, col)
                widget = None
                
                # the first line is a box layout with the text and the button
                if i == 0 and isinstance(item, QtWidgets.QLayout):
                    button_item = item.itemAt(2)
                    if (isinstance(button_item, QtWidgets.QLayoutItem) and 
                        isinstance(button_item.widget(), QtWidgets.QWidget)):
                        button_item.widget().setProperty("index", index)
                        
                    item = item.itemAt(0)
                  
                # get the widget of the item
                if item != None and isinstance(item, QtWidgets.QLayoutItem):
                    widget = item.widget()
                    
                # if the widget does not exist yet craete it
                if widget == None or not isinstance(widget, QtWidgets.QLabel):
                    widget = QtWidgets.QLabel()
                    self._stats.addWidget(widget, i, col)
                    
                widget.setText(text)
            
            col += 1
    
    def _actionShowMore(self):
        """The action method for the "show more" button"""
        
        # get the button
        sender = self.sender()
        
        if isinstance(sender, QtWidgets.QPushButton):
            # get the datapoint index
            index = sender.property("index")
            
            if index != None:
                # show the more dialog
                position = QtCore.QPoint(sender.x() + sender.width(), sender.y() + sender.height())
                position = sender.parent().mapTo(self, position)
                self.showMore(position, index)
    
    def showMore(self, position, index):
        """Displays the *more* menu, this is the menu that is shown when the user
        clicks on the dots button next to the index of the datapoint in the top
        left corner in the stats.
        The position is a QtCore.QPoint which contains the position where to place
        the **right** upper corner of the more menu.
        The index defines which datapoint should be shown
        
        Parameters
        ----------
            position : QtCore.QPoint
                The point where to place the top right corner
            index : int
                The index of the datapoint in the current datacontainer
        """
        
        # create the layout
        layout = QtWidgets.QGridLayout()
        
        # check if the index is valid
        if index >= 0 and index < len(self._datacontainer.datapoints):
            # the datapoint to get the values of
            datapoint = self._datacontainer.datapoints[index]
            
            # title
            title = QtWidgets.QLabel("Values of the datapoint #<b>{}</b>".format(index))
            layout.addWidget(title, 0, 0)
            
            # close button
            close_button = QtWidgets.QPushButton("\u2A09")
            close_button.setStyleSheet("QPushButton{border: none; background: none;}")
            close_button.clicked.connect(self.hideMore)
            layout.addWidget(close_button, 0, 1, QtCore.Qt.AlignRight)
            
            # separator line
            layout.addWidget(View.MainWindow.MainWindow.createSeparatorLine(), 1, 0, 1, 2)
            
            # create title for current values
            environment_title = QtWidgets.QLabel("<i>Environmental conditions " + 
                                                 "(read from file, with background)</i>")
            layout.addWidget(environment_title, 2, 0, 1, 2)
            
            # offset for the following loop, 3 elements have been added before
            offset = 3
            # the values to show
            environment_variable_names = datapoint.getEnvironmnetVariableKeys()
            
            # go through values
            for i, key in enumerate(environment_variable_names):
                name = key
                
                # check if there is a name in the constants
                if key in Constants.ENVIRONMENT_VARIABLE_NAMES:
                    name = Constants.ENVIRONMENT_VARIABLE_NAMES[key]
                
                # get the average value, this should always have a diviation of 
                # 0 because this is just a single sweep up/down
                value = datapoint.getEnvironmentVariableAvg(key)
                
                # format the value, no rounding!!
                if isinstance(value, (list, tuple)) and len(value) >= 2:
                    value = ("{:+f}\u00B1{:f}").format(value[0], abs(value[1]))
                else:
                    value = str(value)
                
                # add the labels
                layout.addWidget(QtWidgets.QLabel(name), i + offset, 0)
                layout.addWidget(QtWidgets.QLabel(value), i + offset, 1)
            
            # calculate the current offset
            offset = i + offset + 1
            
            # calculated title
            calculated_title = QtWidgets.QLabel("<i>Calculated Values</i>")
            layout.addWidget(calculated_title, offset, 0, 1, 2)
            
            # re-calculate offset
            offset += 1
            
            # prepare values list
            calculated_values = [
                    ("Fitting was possible", not datapoint.fitting_not_possible),
                    ("Magnetization", datapoint.getFitResults())
            ]
            
            # add raw fit results
            fit_results = datapoint.getRawFitResults()
            if isinstance(fit_results, (list, tuple)) and len(fit_results) == 2:
                calculated_values.append(("Fit amplitude", 
                                          (fit_results[0][0], fit_results[1][0])))
                calculated_values.append(("Fit drift", 
                                          (fit_results[0][1], fit_results[1][1])))
                calculated_values.append(("Fit y offset", 
                                          (fit_results[0][2], fit_results[1][2])))
                calculated_values.append(("Fit x offset (=center)", 
                                          (fit_results[0][3], fit_results[1][3])))
            
            # add the scan length
            scan_length = datapoint.getScanLength()
            if isinstance(scan_length, (list, tuple)) and len(scan_length) >= 2:
                calculated_values.append(("Scan length in {}".format(scan_length[1]), scan_length[0]))
            
            # add the scan time
            scan_time = datapoint.getScanTime()
            if isinstance(scan_time, (list, tuple)) and len(scan_time) >= 2:
                calculated_values.append(("Scan time in {}".format(scan_time[1]), scan_time[0]))
                
            # add the scan speed
            scan_speed = datapoint.getScanSpeed()
            if isinstance(scan_speed, (list, tuple)) and len(scan_speed) >= 2:
                calculated_values.append(("Scan speed in {}".format(scan_speed[1]), scan_speed[0]))
            
            # print the values
            for i, row in enumerate(calculated_values):
                name = row[0]
                value = row[1]
                
                # format
                if isinstance(value, (list, tuple)):
                    value = ("{:+f}\u00B1{:f}").format(value[0], abs(value[1]))
                else:
                    value = str(value)
                
                layout.addWidget(QtWidgets.QLabel(name), i + offset, 0)
                layout.addWidget(QtWidgets.QLabel(value), i + offset, 1)
            
        else:
            # no valid datapoint given
            layout.addWidget(QtWidgets.QLabel(("The datapoint #{} does not exist " + 
                                              "in the datapoint {}").format(
                                                      index,
                                                      self._datacontainer.createName())),
                    0, 0)
        
        # add a spacer for stretching
        layout.addItem(
                QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding),
                layout.rowCount(), 
                0,
                1,
                layout.columnCount())
        
        # delete the current more widget if it is shown
        self.hideMore()
        
        # (re-)create the more widget, do not use QWidget(parent), this will 
        # result in a wrong display
        self._more_widget = QtWidgets.QFrame()
        self._more_widget.setParent(self)
        self._more_widget.setLayout(layout)
        
        # set style properties
        self._more_widget.setObjectName("more_widget")
        self._more_widget.setStyleSheet("QFrame#more_widget{" + 
                                      "background: #ffffff;" + 
                                  "}")
        self._more_widget.setContentsMargins(3, 3, 3, 3)
        self._more_widget.setFrameStyle(QtWidgets.QFrame.StyledPanel)
        
        # show the widet
        self._more_widget.show()
        # "pack" it so there is no unused space
        self._more_widget.adjustSize()
        # move the top right corner of the widget to the given position
        self._more_widget.move(position - QtCore.QPoint(self._more_widget.width(), 0))
    
    def hideMore(self):
        """Hide the more menu, if it is not shown nothing will be done"""
        
        if isinstance(self._more_widget, QtWidgets.QWidget):
            self._more_widget.setParent(None)
    
    def showPointsInDataContainerPlot(self):
        """Display/Highlight the datapoints in the parent datacontainer in the
        datacontainer plot that are currently shown"""
        
        if (isinstance(self._datacontainer_plot, View.PlotCanvas.PlotCanvas)):
            # fixes the indices
            self.fixIndices()
            
            self._datacontainer_plot.clearHighlights(False)
            
            # draw the highlight
            self._datacontainer_plot.highlightDataPoint(self._indices, 
                                                        0,
                                                        False)
            
            # update the plot
            if len(self._indices) > 0:
                self._datacontainer_plot.commitUpdate(False)
    
    def removeHighlightPointsInDataContainerPlot(self):
        """Removes the highlighted points in the datacontainer plot"""
        
        if isinstance(self._datacontainer_plot, View.PlotCanvas.PlotCanvas):
            self._datacontainer_plot.clearHighlights(True)
    
    def actionLegendCheckboxToggle(self):
        """The action method when the legend checkbox are toggled"""
        
        # the legend checkbox that has been toggled
        sender = self.sender()
        # the matplotib 2DLines list
        lines = sender.property("lines")
        
        # the plot canvas which hold the lines
        plots = []
        
        if (lines != None and isinstance(lines, (list, tuple)) and 
            isinstance(sender, QtWidgets.QAbstractButton)):
            for line in lines:
                if isinstance(line, matplotlib.artist.Artist):
                    # toggle the lines visibility depending on the checkbox state
                    line.set_visible(sender.isChecked())
                    canvas = line.axes.figure.canvas
                    
                    if canvas not in plots:
                        plots.append(canvas)
        
        # update all the PlotCanvas
        for plot in plots:
            if isinstance(plot, View.PlotCanvas.PlotCanvas):
                plot.commitUpdate(False)
            elif isinstance(plot, matplotlib.backend_bases.FigureCanvasBase):
                plot.draw()
        
    def actionLoadIndices(self):
        """The action method for loading the indices of the index inputs in the
        bottom of the dialog"""
        
        # the indices
        indices = []
        
        # go through all the index edits and add their index to the collection
        for i in range(0, self._indices_edits.count()):
            item = self._indices_edits.itemAt(i)
            widget = item.widget()
            
            if widget != None and isinstance(widget, QtWidgets.QLineEdit):
                indices.append(widget.text())
        
        # apply the indices
        self.goList(indices)
    
    def actionNextPrevButton(self):
        """The action method for the next/previous buttons"""
        
        # the button that has been clicked
        sender = self.sender()
        
        if isinstance(sender, QtCore.QObject):
            # the step width
            step = sender.property("step")
            if step != False:
                # go to this index
                self.goList(map(lambda x: float(step) + x, self._indices))
    
    def goTo(self, *indices):
        """An alias method for the goList where the *indices will be passed to
        the goList method
        
        Parameters
        ----------
            *indices : int
                The indices
        """
        
        self.goList(indices)
    
    def goList(self, indices_list):
        """Go to the indices defined in the indices_list
        
        Parameters
        ----------
            indices_list : list of ints
                The indices
        """
        
        self.fixIndices(indices_list)
        
        self.hideMore()
        
        # update the plot grid
        self.plotDataPointGrid()
        # update the edits
        self.updateIndexEdits()
        # update the stats
        self.updateStats()
        # highlight points
        self.showPointsInDataContainerPlot()
    
    def fixIndices(self, indices_list = None):
        """Fix the internal indices and/or save new indices. This will force the
        internal indices to be correct so the number of indices is equal to the 
        grid size and all indices are correct formatted and exist. This can also
        handle infinity (last) and -infinity (first), integers, floats and all 
        iterables as parameter
        
        Parameter
        ---------
            indices_list : list, tuple, iterable, int or float
                The indices or the index to show
        """
            
        # the grid size
        n = self._grid_width * self._grid_height
        # datapoint length
        l = len(self._datacontainer.datapoints)
        
        inf = float("inf")
        
        # convert the index list
        if indices_list == -inf:
            # "parse" to list so indices_list is iterable
            indices_list = [-inf]
        elif indices_list == inf:
            # "parse" to list so indices_list is iterable
            indices_list = [inf]
        elif isinstance(indices_list, dict):
            # convert a dict to the indices_list
            indices_list = indices_list.values()
        elif isinstance(indices_list, (float, int, str)):
            # indices_list is one number, show the next grid size numbers
            try:
                s = int(indices_list)
            except (ValueError, TypeError):
                s = 0
                
            indices_list = range(s, s + n)
        elif not isinstance(indices_list, (tuple, list)):
            # cannot use indices_list or indices_list is not given
            try:
                indices_list = list(indices_list)
            except (ValueError, TypeError):
                if len(self._indices) > 0:
                    # fix the internal indices list
                    indices_list = list(self._indices)
                else:
                    # there is no indices list given, create a new one
                    indices_list = range(0, n)
        
        # check if there is infinity or -infinity in the list
        if inf in indices_list:
            # show the end of the indices
            indices_list = range(l - n, l)
        elif -inf in indices_list:
            # show the start of the indices
            indices_list = range(0, n)
        
        # set the correct length of the indices list
        if len(indices_list) > n:
            indices_list = indices_list[0:n]
        elif len(indices_list) < n:
            try:
                s = int(indices_list[-1])
            except (ValueError, TypeError):
                s = -1
            s += 1
            
            indices_list = indices_list + tuple(range(s, s + n - len(indices_list)))
        
        # parse to list
        indices_list = list(indices_list)
        
        # empyt the internal object indices list
        self._indices = []
        
        # go through the list and save the indices
        for i, index in enumerate(indices_list):
            # parse to int
            try:
                index = int(index)
            except (ValueError, TypeError):
                # could not parse, increase the last value with 1 or use 0 as
                # default fallback
                if i > 0:
                    index = indices_list[i-1] + 1
                else:
                    index = 0
                
            if index < 0 or index >= l:
                # index is greater than the count, start at the beginning again
                # or if the index is negative start from the end
                index = index % l
            
            self._indices.append(index)
    
    def closeEvent(self, close_event):
        """Overwrite the close event for removing highlighted datapoints"""
        
        # remove highlight points
        self.removeHighlightPointsInDataContainerPlot()
        
        super(QtWidgets.QDialog, self).closeEvent(close_event)