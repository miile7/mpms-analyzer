# -*- coding: utf-8 -*-
"""
Created on Tue Feb 20 11:13:41 2018

@author: miile7
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
tools = (View.ToolWizard.FormatDataTool.FormatDataTool(),)

wizard = View.ToolWizard.ToolWizard.ToolWizard(controller, None, *tools)

print("Ready.")
wizard.show()

sys.exit(app.exec_())