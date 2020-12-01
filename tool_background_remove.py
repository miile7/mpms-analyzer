# -*- coding: utf-8 -*-
"""
Created on Wed Feb 14 15:16:37 2018

@author: Maximilian Seidler
"""

print("Importing packages...")
import sys
from PyQt5 import QtWidgets
    
import View.ToolWizard.ToolWizard
import View.ToolWizard.BackgroundSubtractionTool
import Controller

print("Preparing program...")
app = QtWidgets.QApplication.instance()
if not app or app == None:
    app = QtWidgets.QApplication(sys.argv)

controller = Controller.Controller(False)
    
print("Starting editing GUI...")
tools = (View.ToolWizard.BackgroundSubtractionTool.BackgroundSubtractionTool(),)

wizard = View.ToolWizard.ToolWizard.ToolWizard(controller, None, *tools)

print("Ready.")
wizard.show()

sys.exit(app.exec_())