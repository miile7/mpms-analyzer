# -*- coding: utf-8 -*-
"""
Created on Wed Feb 14 14:22:28 2018

@author: Maximilian Seidler
"""

import my_utilities
import View.ToolWizard.Tool
import DataHandling.DataContainer

class BackgroundSubtractionTool(View.ToolWizard.Tool.Tool):
    def __init__(self):
        """Initialize the tool"""
        
        super(BackgroundSubtractionTool, self).__init__("background_subtraction",
                title="Subtract Background",
                tooltip="Subtract the background data from a sample",
                action_name="Subtract Background",
                calculating_text="Subtracting Background...",
                icon=my_utilities.image("icon_difference.svg"),
                needs_background_datacontainer=True,
                needs_measurement_type=True
                )
    
    def initializeTool(self):
        """Initialize the tool"""
        
        self.addCalculation(self.subtractBackground)
    
    @property
    def preview(self):
        wizard = self.wizard
        
        return(wizard.measurement_variable, 
               DataHandling.DataContainer.DataContainer.MAGNETIZATION)
    
    @preview.setter
    def preview(self, value):
        return False
    
    def subtractBackground(self):
        """Subtract the background for the wizards datacontainers. This is the 
        calculation callback"""
        self.wizard.result_datacontainer = self.wizard.controller.subtractBackgroundData(
                self.wizard.result_datacontainer,
                self.wizard.background_datacontainer
                )