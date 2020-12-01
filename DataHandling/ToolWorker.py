# -*- coding: utf-8 -*-
"""
Created on Wed Feb 14 14:27:18 2018

@author: Maximilian Seidler
"""

from PyQt5 import QtCore
import warnings

class ToolWorker(QtCore.QObject):
    started = QtCore.pyqtSignal(int)
    stepComplete = QtCore.pyqtSignal(int)
    finished = QtCore.pyqtSignal(list)
    
    error = QtCore.pyqtSignal(Exception)
    warning = QtCore.pyqtSignal(list)

    def __init__(self, handler, wizard, *params):
        """Initialize the worker.
        Parameters
        ----------
        """
        
        super().__init__()
        
        self.wizard = wizard
        
        if isinstance(handler, (list, tuple)):
            self._handler = handler
            self._params = params
        else:
            self._handler = [handler]
            self._params = [params]
            
        self.return_values = []
        
        self._step = 0
        self._stop = False

    def run(self):
        """Run the thread. This will create the DataContainers by parsing the 
        files
        """
        
        l = len(self._handler)
        
        self.started.emit(l)
        self._step = 0
        self._return_values = []
        
        self._performStep()
        
        self.finished.emit(self._return_values)
        
    def stop(self):
        """Stop the worker"""
        self._stop = True
    
    def _performStep(self):
        """Do one handler call"""
        
        if self._step >= 0 and self._step < len(self._handler):
            with warnings.catch_warnings(record=True) as ws:
                try:
                    self.return_values.append(self._handler[self._step](*self._params[self._step]))
                except Exception as e:
                    self.error.emit(e)
                    raise e
                
                if len(ws) > 0:
                    self.warning.emit(ws)
            
            self.stepComplete.emit(self._step)
            self._step += 1
            
            self._performStep()