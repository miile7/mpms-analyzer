# -*- coding: utf-8 -*-
"""
Created on Mon Oct 23 10:09:51 2017

@author: Maximilian Seidler
"""

from PyQt5 import QtCore, QtWidgets

import Constants

class PreferencesDialog(QtWidgets.QDialog):
    def __init__(self, parent = None):
        super(PreferencesDialog, self).__init__(parent)
        
        self._preferences = QtCore.QSettings(Constants.COMPANY, Constants.NAME, parent)
        
        self.setModal(True)
        self.resize(QtCore.QSize(600, 300))
        
        layout = QtWidgets.QFormLayout()

        tabs = QtWidgets.QTabWidget()
        
        # create tab for general settings
        languages = QtWidgets.QComboBox()
        languages.addItem("English")
        languages.addItem("Deutsch")
        languages.setEnabled(False)
#        languages.setProperty("language")
#        languages.activated.connect(self._setPreferences)
        layout.addRow(QtWidgets.QLabel("Language"), languages)
        
        constants_hint = QtWidgets.QLabel("Most of the preferences can be set " + 
                                          "in the Constants.py.")
        layout.addRow(constants_hint)
        
        general_tab = QtWidgets.QWidget()
        general_tab.setLayout(layout)
        
        # add the tabs
        tabs.addTab(general_tab, "General")
        
        # add the tabs to the dialog
        dialog_layout = QtWidgets.QVBoxLayout()
        dialog_layout.addWidget(tabs)

        # OK and Cancel buttons
        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel,
            QtCore.Qt.Horizontal, self)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        
        dialog_layout.addWidget(buttons)
        
        self.setLayout(dialog_layout)
    
    @property
    def preferences(self):
        return self._preferences

    @preferences.setter
    def preferences(self, preferences):
        if isinstance(preferences, QtCore.QSettings):
            self._preferences = preferences
            return True
        else:
            return False

    def _setPreferences(self, key = None, value = None):
        if key == None:
            sender = self.sender()
            
            if isinstance(sender, QtWidgets.QComboBox):
                name = sender.property("language")
                i = sender.currentIndex()
                value = sender.itemData(i)
                
                self._setPreferences(name, value)
        else:
            self._preferences.value(key, value)
        
    # static method to create the dialog and return (date, time, accepted)
    @staticmethod
    def getPreferences(parent = None):
        dialog = PreferencesDialog(parent)
        result = dialog.exec_()
        return (dialog.preferences, result == QtWidgets.QDialog.Accepted)