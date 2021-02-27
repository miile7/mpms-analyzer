# -*- coding: utf-8 -*-
"""
Created on Mon Oct 30 10:11:41 2017

@author: miile7
"""

print("Importing packages...")
import DataHandling.DataContainer
import View.DataPointViewer
import Controller
from PyQt5 import QtWidgets
import sys

print("Preparing program...")
one_point_only = False
subtract_background = True
show_background = False

path = "//cfs-student.student.uni-augsburg.de/seidlema/Bachlorarbeit/Auswertungsdaten/Pd (Ich)/M(T), m=3,9mg - Torlon/"
#path = "//cfs-student.student.uni-augsburg.de/seidlema/Bachlorarbeit/Auswertungsdaten/Li3N-Mn - Rotator (Tanita)/"

if one_point_only:
    rfp = path + "M20171205_Pd_one_torlon_M(T)_at_10000_Oe.first-data-point.rw.dat"
    dfp = path + "M20171205_Pd_one_torlon_M(T)_at_10000_Oe.first-data-point.dat"
        
    rbfp =  path + "M20171205_Pd_one_torlon_M(T)_at_10000_Oe_background.first-data-point.rw.dat"
    dbfp =  path + "M20171205_Pd_one_torlon_M(T)_at_10000_Oe_background.first-data-point.dat"
else:
    rfp =  path + "M20171121_Pd_one_torlon_M(T)_at_10000_Oe.rw.dat"
    dfp =  path + "M20171121_Pd_one_torlon_M(T)_at_10000_Oe.dat"
    
    rbfp =  path + "M20171121_Pd_one_torlon_M(T)_at_10000_Oe_background.rw.dat"
    dbfp =  path + "M20171121_Pd_one_torlon_M(T)_at_10000_Oe_background.dat"


#rfp =  path + "TBA1_DFRotator_0.1T_2K.rw.dat"
#dfp =  path + "TBA1_DFRotator_0.1T_2K.dat"

#rbfp =  path + "TBA1_DFRotator_BG_0.1T_2K.rw.dat"
#dbfp =  path + "TBA1_DFRotator_BG_0.1T_2K.dat"
    
#rfp = "\\\\cfs-student.student.uni-augsburg.de/seidlema/Bachlorarbeit/Auswertungsdaten/SrCu (Anton)/Sample_datapoints_perp.rw.dat"
#dfp = "\\\\cfs-student.student.uni-augsburg.de/seidlema/Bachlorarbeit/Auswertungsdaten/SrCu (Anton)/Sample_datapoints_perp.dat"

app = QtWidgets.QApplication.instance()
if not app or app == None:
    app = QtWidgets.QApplication(sys.argv)

controller = Controller.Controller(False)

print("Laoding files...")
# data container
dc = DataHandling.DataContainer.DataContainer(rfp, dfp)
dc.readFileData()

if show_background or subtract_background:
    # background data container
    bc = DataHandling.DataContainer.DataContainer(rbfp, dbfp)
    bc.readFileData()
    
if subtract_background:
    print("Subtracting background...")
    # no background data container
    nc = controller.subtractBackgroundData(dc, bc)
elif show_background:
    nc = bc
else:
    nc = dc

print("Plotting data points...")
viewer = View.DataPointViewer.DataPointViewer(nc, None, 0)

print("Ready.")
viewer.show()

sys.exit(app.exec_())