# -*- coding: utf-8 -*-
"""
Created on Wed Feb 14 14:18:37 2018

@author: miile7
"""

from PyQt5 import QtCore, QtGui, QtWidgets
import os

class Tool(QtCore.QObject):
    def __init__(self, unique_name, **kwargs):
        """Initialize the tool
        
        Parameters
        ----------
            unique_name : String
                The name of the tool to identify it
            kwargs
                The attributes of the tool
        """
        
        super(Tool, self).__init__()
        
        attributes = (
                ("_unique_name", unique_name),
                ("title", ""), 
                ("shorttitle", ""),
                ("icon", ""),
                ("subtitle", ""),
                ("tooltip", ""),
                ("action_name", ""),
                ("calculating_text", "Working..."),
                ("needs_background_datacontainer", False),
                ("needs_measurement_type", False),
                ("preview", None),
                ("save_suffix", None)
            )
        
        for name, default_value in attributes:
            if name in kwargs:
                setattr(self, name, kwargs[name])
            else:
                setattr(self, name, default_value)
        
        self._calculations = {}
        
        self.wizard = None
    
    def getShorttitle(self):
        """Get the short title of this Tool
        
        Returns
        -------
            String
                The short title
        """
        
        if isinstance(self.shorttitle, str) and len(self.shorttitle) > 0:
            return self.shorttitle
        else:
            return self.title.split(" ")[0]
    
    def initializeTool(self):
        """Initialize the tool"""
        pass
    
    def addCalculation(self, handler, relative_page_step = 0):
        """Add a calculation after the page for this tool is finished. The 
        handler function will be executed after relative_page_step pages after
        the page that is currently the last one
        
        Parameters
        ----------
            handler : function
                The function to execute
            relative_page_step : int
                The number of pages after the current page when to execute the
                handler
        """
        
        if self.wizard != None:
            pages = self.wizard.pageIds()
        else:
            pages = [0]
        
        if relative_page_step <= 0:
            try:
                page_id = pages[-1 + relative_page_step]
            except:
                page_id = 0
        else:
            page_id = pages[-1] + relative_page_step
        
        if page_id not in self._calculations:
            self._calculations[page_id] = []
        
        self._calculations[page_id].append(handler)
    
    def getCalculationsFor(self, page_id):
        """Get the calculation function for the given page id
        
        Parameters
        ----------
            page_id : int
                The id of the page
        
        Returns
        -------
            function
                The function or None if there is no funciton
        """
            
        if page_id in self._calculations:
            return self._calculations[page_id]
        else:
            return None
    
    def getUniqueName(self):
        return self._unique_name
    
    def createAction(self, parent, icon = True, shorttitle = False):
        """Creates the action for this tool. This is for adding this tool to a 
        button, a toolbar or a menubar
        
        Parameters
        ----------
            parent : QWidget
                The parent
            icon : boolean
                Whether to add an icon or not
            shorttitle : boolean
                Whether to use the shorttitle instead of the title
        
        Returns
        -------
            QAction
                The action
        """
        
        if isinstance(self.title, str) and len(self.title) > 0:
            if shorttitle:
                title = self.getShorttitle()
            else:
                title = self.title
        else:
            title = type(self).__name__
            
        action = QtWidgets.QAction(title, parent)
        
        if icon and os.path.isfile(self.icon):
            action.setIcon(QtGui.QIcon(self.icon))
        
        if isinstance(self.tooltip, str) and len(self.tooltip) > 0:
            action.setToolTip(self.tooltip)
            action.setStatusTip(self.tooltip)
        
        return action