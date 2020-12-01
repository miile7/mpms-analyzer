# -*- coding: utf-8 -*-
"""
Created on Mon Oct 30 10:11:41 2017

@author: Maximilian Seidler
"""

print("Importing packages...")
from PyQt5 import QtWidgets
import sys
import copy
import os

import DataHandling.DataContainer
import View.DataPointViewer

# which data should be loaded
perpendicular = False
# perform on all datapoints
all_datapoints = False
# show magnetization plot
show_plot = False

def symetric(dp):
    """Make the data of the datapoint symmetric, for this the SQUID drift will 
    be subtracted from each raw value
    Parameters
    ----------
        dp : DataPoint
            The datapoint to summetrisize
    Returns
    -------
        DataPoint
            The symmetric datapoint
    """
    
    # get the raw fit results
    try:
        res = dp.getRawFitResults()
    except RuntimeError:
        res = None
        
    if res == None:
        raise RuntimeError(("The datapoint {} could not be made symmetric, the " + 
                           "datapoint could not be fitted so the squid drift " + 
                           "could not be detected").format(dp.index))
    drift = res[0][1]
    y_offset = res[0][2]
    
    # subtract the drift and the y offset
    i = 0
    for row in dp._data_rows:
        if isinstance(row, (list, tuple)):
            dp._data_rows[i] = tuple(
                         list(dp._data_rows[i][0:4]) + 
                         [row[4] - row[3] * drift - y_offset] + 
                         list(dp._data_rows[i][5:-1]))
        else:
            dp._data_rows[i] = row
            
        i += 1
    
    # fit again so the fit is correct
    dp.execFit()
    
    return dp

def cutRaw(dp, xstart, xend):
    """Removes the values outside of the bounds defined by xstart and xend.
    Parameters
    ----------
        dp : DataPoint
            The datapoint to cut
        xstart, xend : float
            The starting and ending raw position where to cut the data, everything
            in this range will be kept
    Returns
    -------
        DataPoint
            The cutted datapoint
    """
    
    i = 0
    
    # check if the start and end are correctly or if they are "inverted"
    if xstart > xend:
        xend, xstart = xstart, xend
    
    # copy all rows
    rows = dp._data_rows
    # empty the datapoint
    dp._data_rows = []
    
    # go through each original row, check the position (raw position is in index
    # 3), keep if the data is in the defined bounds
    for row in rows:
        if row[3] >= xstart and row[3] <= xend:
            dp._data_rows.append(row)
        i += 1
    
    return dp

def name_function(index, direction, mode):
    """A naming function, this will return the real index name of the overworked
    datapoints
    Parameters
    ----------
        index : int
            The index of the datapoin that is currently shown
        direction : String
            The direction ("Up" or "Down" or None if not known)
        mode : String
            The mode, this can be "stats" or "grid"
    Returns
    -------
        String
            The new name or None if the datapoint should not be renamed
    """
    
    global new_indices, datapoint_indices
    
    # check if the index is a re-worked index
    if index in new_indices:
        # get the real index
        real_index = datapoint_indices[new_indices.index(index)]
        
        # create the name
        if mode == "stats":
            return "#<b>{}</b> (s)".format(real_index)
        else:
            return "Datapoint #{} (sym., short - {} sweep)".format(real_index, direction)
    else:
        return None

path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Auswertungsdaten/SrCu (Anton)/")

if perpendicular:
    # perpendicular
    rfp = path + "/M20170517_slow_M-H_KAZIN_Sr-Cu_Hperp_on_quartz1n.rw.dat"
    dfp = path + "/M20170517_slow_M-H_KAZIN_Sr-Cu_Hperp_on_quartz1n.dat"
else:
    # parallel
    rfp = path + "/M20170517b_slow_M-H_KAZIN_Sr-Cu_Hparc_on_quartz1n.rw.dat"
    dfp = path + "/M20170517b_slow_M-H_KAZIN_Sr-Cu_Hparc_on_quartz1n.dat"

# start the gui
app = QtWidgets.QApplication.instance()
if not app or app == None:
    app = QtWidgets.QApplication(sys.argv)

print("Laoding files...")

# load data container
dc = DataHandling.DataContainer.DataContainer(rfp, dfp)
dc.readFileData()

print("Initializing datapoints to correct...")

# the datapoints to work over, those are "beautiful" points
datapoint_indices = []

# define depending on the mode
if all_datapoints:
    datapoint_indices = tuple(range(0, len(dc.datapoints)))
elif perpendicular:
    datapoint_indices = (19, 297)
else:
    datapoint_indices = (129, 168)

# save the original length
l = len(dc.datapoints)

print("Correcting datapoints...")

# rework the datapoints
for index in datapoint_indices:
    if all_datapoints:
        dp = dc.datapoints[index]
    else:
        dp = copy.deepcopy(dc.datapoints[index])
    
    try:
        dp = cutRaw(dp, 10, 40)
        dp = symetric(dp)
    except RuntimeError as e:
        print(e)
    
    if all_datapoints:
        dc.datapoints[index] = dp
    else:
        dc.datapoints.append(symetric(dp))

# save the indices which are new re-worked datapoints and the indices to show
if all_datapoints:
    new_indices = datapoint_indices
    ind = datapoint_indices[0:4]
else:
    new_indices = list(range(l, len(dc.datapoints)))
    ind = list(datapoint_indices[0:2]) + new_indices[0:2]
    
if show_plot:
    plot = View.PlotCanvas.PlotCanvas()
    plot.addPlotData(dc.getPlotData(
            DataHandling.DataContainer.DataContainer.FIELD,
            DataHandling.DataContainer.DataContainer.MAGNETIZATION))
    plot.show()

print("Plotting data points...")
viewer = View.DataPointViewer.DataPointViewer(dc, None, *ind, name_callback=name_function)

viewer.setWindowTitle(viewer.windowTitle() + " - H " + ("perpendicular" if perpendicular else "parallel") + " c")

print("Ready.")
viewer.show()

sys.exit(app.exec_())