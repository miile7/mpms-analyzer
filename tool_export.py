# -*- coding: utf-8 -*-
"""
Created on Mon Feb 26 14:56:09 2018

@author: Maximilian Seidler
"""

print("Importing packages...")
import sys
from PyQt5 import QtWidgets
    
import View.ToolWizard.ToolWizard
import View.ToolWizard.FormatDataTool
import Controller

print("Preparing program...")
app = QtWidgets.QApplication.instance()
if not app or app == None:
    app = QtWidgets.QApplication(sys.argv)

controller = Controller.Controller(False)
    
print("Starting editing GUI...")
wizard = View.ToolWizard.ToolWizard.ToolWizard(controller, None)

print("Ready.")
wizard.show()

sys.exit(app.exec_())