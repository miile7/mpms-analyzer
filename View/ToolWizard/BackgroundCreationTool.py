# -*- coding: utf-8 -*-
"""
Created on Wed Feb 21 12:09:54 2018

@author: Maximilian Seidler
"""

from PyQt5 import QtWidgets, QtGui, QtCore

import my_utilities
import View.ToolWizard.Tool
import DataHandling.DataContainer

class BackgroundCreationTool(View.ToolWizard.Tool.Tool):
    def __init__(self):
        """Initialize the tool"""
        
        super(BackgroundCreationTool, self).__init__("background_creation",
                title="Interpolate background",
                tooltip="Create a new background file by interpolating an existing one",
                action_name="Interpolate background",
                calculating_text="Creating background...",
                icon=my_utilities.image("icon_interpolate.svg"),
                needs_background_datacontainer=True,
                needs_measurement_type=True
                )
        
    def initializeTool(self):
        """Initialize the tool"""
        
        self.addCalculation(self.createBackground)
    
    @property
    def preview(self):
        wizard = self.wizard
        
        return (wizard.measurement_variable, 
                DataHandling.DataContainer.DataContainer.MAGNETIZATION)

    @preview.setter
    def preview(self, value):
        return False
    
    def createBackground(self):
        """Create the background for the wizards datacontainers. This is the 
        calculation callback"""
        self.wizard.result_datacontainer = self.wizard.controller.createNewBackground(
                self.wizard.result_datacontainer,
                self.wizard.background_datacontainer,
                self.wizard.measurement_variable,
                None
                )