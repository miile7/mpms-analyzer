# -*- coding: utf-8 -*-
"""
Created on Wed Nov  8 08:59:36 2017

@author: Maximilian Seidler
"""

from PyQt5 import QtWidgets, QtGui, QtCore

import DataHandling.PlotData
import View.MainWindow
import View.PlotCanvas

class PlotWindow(QtWidgets.QMdiSubWindow):
    def __init__(self, view, index = None, plotdata = None, parent = None):
        """Get a new instance of the PlotWindow. 
        Parameters
        ----------
            index : int, optional
                The index in the main window that this plot window has, default
                is None
            plotdata : PlotData or PlotCanvas, optional
                The data to plot in the plot window
            parent : QtWidgets.QWidget
                The parent
        """
        
        super(PlotWindow, self).__init__(parent)
        
        # set icon
        self.setWindowIcon(QtGui.QIcon(View.MainWindow.MainWindow.ICON))
        
        # central layout
        layout = QtWidgets.QVBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
                                    
        # create the plotting widget
        if plotdata != None and isinstance(plotdata, View.PlotCanvas.PlotCanvas):
            self._plot_widget = plotdata
        else:
            self._plot_widget = View.PlotCanvas.PlotCanvas(self)
        
        self._plot_widget.setMinimumSize(QtCore.QSize(400, 400))
        
        self._plot_widget.selecting_allowed = True
        self._plot_widget.datapointDoubleClicked.connect(self.actionDataPointClicked)
#        self._plot_widget.datapointClicked.connect(self.actionSelectDataPoint)
        
        # a spacer
        layout.addWidget(View.MainWindow.MainWindow.createSeparatorLine())
        
        # toolbar widget
        self._toolbar = self._plot_widget.plot_menu_factory.toolbar_widget
        layout.addWidget(self._toolbar, 0)
        
        # a spacer
        layout.addWidget(View.MainWindow.MainWindow.createSeparatorLine())
        
        # add the plot widget
        layout.addWidget(self._plot_widget, 1)
        
        # central widget
        central = QtWidgets.QWidget()
        central.setLayout(layout)
        self.setWidget(central)
        
        # set index
        if isinstance(index, int):
            self._index = index
        else:
            self._index = None
        
        # set the plotdata
        success = self.addPlotData(plotdata)
        
        # save the view
        self._view = view
        
        self._selected_datapoints = []
        
        # set the title if not done in the addPlotData() function
        if not success:
            self._setTitle()
            
    @property
    def plot_widget(self):
        return self._plot_widget
    
    @plot_widget.setter
    def plot_widget(self, plot_widget):
        return False
    
    def _setTitle(self):
        """Set the title automatically depending on the internal index and
        the plotdata"""
        
        if isinstance(self._plot_widget, View.PlotCanvas.PlotCanvas):
            plot_title = self._plot_widget.createTitle()
        else:
            plot_title = None
        
        title = ""
        if plot_title != None and self._index != None:
            title = "Graph {0} - {1}".format(self._index, plot_title)
        elif plot_title != None:
            title = "{1}".format(plot_title)
        elif self._index != None:
            title = "Graph {0}".format(self._index)
          
        if title != "":
            self.setWindowTitle(title)
        
    def addPlotData(self, plotdata):
        """Add plotdata to plot
        Parameters
        ----------
            plotdata : PlotData or list of PlotData
                The data to plot
        Returns
        -------
            boolean
                Success
        """
        
        if plotdata != None and isinstance(plotdata, DataHandling.PlotData.PlotData):
            self._plot_widget.addPlotData(plotdata)
            self._setTitle()
            return True
        elif plotdata != None and isinstance(plotdata, (list, tuple)):
            r = []
            for pd in plotdata:
                r.append(self.addPlotData(pd))
            return all(r)
        else:
            return False
    
    def actionDataPointClicked(self, plot_data, index, plot_data_index):
        """The action method when a datapoing is clicked
        Parameters
        ---------
            plot_data : PlotData
                The plot data
            index : int
                The index of the datapoint that has been clicked
        """
        
        if (isinstance(plot_data, DataHandling.PlotData.PlotData) and plot_data.origin != None and
            isinstance(plot_data.origin, DataHandling.DataContainer.DataContainer)):
            self._view.showDataPoints(plot_data.origin, index, plot_data_index)
    
#    def actionSelectDataPoint(self, plot_data, index, plot_data_index):
#        if (isinstance(plot_data, DataHandling.PlotData.PlotData) and plot_data.origin != None and
#            isinstance(plot_data.origin, DataHandling.DataContainer.DataContainer)):
#            
#            if index in self._selected_datapoints:
#                self.deselectDataPoint(index, plot_data.origin.datapoints[index]):
#            else:
#                self.selectDataPoint(index, plot_data.origin.datapoints[index])
        