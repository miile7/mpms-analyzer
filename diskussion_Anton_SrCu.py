# -*- coding: utf-8 -*-
"""
Created on Mon Oct 30 10:11:41 2017

@author: Maximilian Seidler
"""

print("Importing packages...")
from PyQt5 import QtWidgets
import matplotlib.pyplot as plt
import sys
import copy
import os
from matplotlib import rc

rc('mathtext', default='regular')

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

print("Laoding files...")

# load data container
dc = DataHandling.DataContainer.DataContainer(rfp, dfp)
dc.readFileData()

print("Getting original data...")
      
x1, y1 = dc.getPlotData(
        DataHandling.DataContainer.DataContainer.FIELD,
        DataHandling.DataContainer.DataContainer.MAGNETIZATION)

print("Correcting datapoints...")

dc = controller.cutDataPointRows(dc, [{"key": "raw_position", "min": }])

print("Getting modified data...")

x2, y2 = dc.getPlotData(
        DataHandling.DataContainer.DataContainer.FIELD,
        DataHandling.DataContainer.DataContainer.MAGNETIZATION)

print("Plotting matplotlib data...")

ms = 6
#plt.plot(x1, y1, label="Originalmessung", marker="s", linestyle="solid", markersize=ms, markeredgewidth=1, color="b", markeredgecolor="b", markerfacecolor='None')
#plt.plot(x2, y2, label="Abgeschnittene Datenpunkte", marker="d", linestyle="None", markersize=ms, markeredgewidth=1, color="r", markeredgecolor="r", markerfacecolor='None')

plt.plot(x1, y1, label="Originalmessung", color="b", linestyle="solid") #, marker="s", markersize=ms, markeredgewidth=1, markeredgecolor="b", markerfacecolor='None')
plt.plot(x2, y2, label="Abgeschnittene Datenpunkte", color="r", linestyle="--")#, marker="d", markersize=ms, markeredgewidth=1, markeredgecolor="r", markerfacecolor='None')

#ax = plt.gca()
#ax.set_xticklabels([])
#ax.set_yticklabels([])

plt.legend()
plt.ylabel("Magnetization [emu]")
plt.xlabel("Tempearatur [K]")
plt.title("Vergleich Torlon Hintergrund, interpoliert und gemessen", y=1.06)

plt.gca().ticklabel_format(style="sci", scilimits=(0.0002, 0.00032), useMathText=True, axis="y")

save = QtWidgets.QMessageBox.question(None, "Save?", "Save the figure?")

if save == QtWidgets.QMessageBox.Yes:
    filename = QtWidgets.QFileDialog.getSaveFileName(
            None, 
            "Save", 
            os.path.join(os.path.dirname(__file__), 'figure.pdf'),
            "Images (*.png *.svg *.pdf)")
    
    filename = str(filename[0])
    
    fig = plt.gcf()
    fig.savefig(filename, bbox_inches='tight')
    
plt.show()

print("Ready.")