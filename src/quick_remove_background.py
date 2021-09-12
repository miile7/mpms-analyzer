# -*- coding: utf-8 -*-
"""
Created on Wed Jan 17 10:25:08 2018

@author: miile7
"""

print("Importing packages...")
import View.MainWindow
import Controller

from PyQt5 import QtWidgets, QtCore, QtGui
import sys

class QuickRemove(QtWidgets.QDialog):
    def __init__(self, parent = None):
        
        super(QtWidgets.QDialog, self).__init__(parent)
        
        self.setWindowTitle("Quick Remove - MPMS")
        self.setWindowIcon(QtGui.QIcon(View.MainWindow.MainWindow.ICON))
        self.resize(300, 150)
        
        layout = QtWidgets.QGridLayout()
        
        file_label = QtWidgets.QLabel("Raw file (with background)")
        layout.addWidget(file_label, 0, 0)
        
        self.file_input = QtWidgets.QLineEdit("")
        self.file_input.setProperty("type", "background")
        self.file_input.textChanged.connect(self.openFiles)
        layout.addWidget(self.file_input, 0, 1)
        
        file_select = QtWidgets.QPushButton("Browse")
        file_select.setProperty("type", "data")
        file_select.clicked.connect(self.showOpenFiles)
        layout.addWidget(file_select, 0, 2)
        
        background_label = QtWidgets.QLabel("Raw background file (background only)")
        layout.addWidget(background_label, 1, 0)
        
        self.background_input = QtWidgets.QLineEdit("")
        self.background_input.setProperty("type", "background")
        self.background_input.textChanged.connect(self.openFiles)
        layout.addWidget(self.background_input, 1, 1)
        
        background_select = QtWidgets.QPushButton("Browse")
        background_select.setProperty("type", "background")
        background_select.clicked.connect(self.showOpenFiles)
        layout.addWidget(background_select, 1, 2)
        
        layout.addWidget(View.MainWindow.MainWindow.createSeparatorLine())
        
        buttons = QtWidgets.QDialogButtonBox()
        self.ok_button = buttons.addButton(QtWidgets.QDialogButtonBox.Ok)
        self.ok_button.setEnabled(False)
        buttons.addButton(QtWidgets.QDialogButtonBox.Close)
        buttons.accepted.connect(self.subtractBackground)
        buttons.rejected.connect(self.actionExit)
        
        layout.addWidget(buttons)
        
        # initialize the program without the main window
        self.controller = Controller.Controller(False)
        
        self.controller.view.openedFile.connect(self.actionFileOpened)
#        self.controller.view.openFileAborted.connect(self.actionFileAborted)
        
        self.background_mode = False
        self.input_mode = None
        
        self.setLayout(layout)
        self.openFiles()
        
    def showOpenFiles(self):
        sender = self.sender()
        
        self.input_mode = "button"
        
        if isinstance(sender, QtCore.QObject):
            if sender.property("type") == "background":
                self.background_mode = True
            elif sender.property("type") == "data":
                self.background_mode = False
        
        # auf ready signal warten
        if self.background_mode == False:
            text = "Select raw file with background"
        elif self.background_mode == True:
            text = "Select background draw file with background"
        
        print(text)
        self.controller.view.showOpenDialog(text, False)
    
    def openFiles(self):
        sender = self.sender()
        
        self.input_mode = "input"
        
        if isinstance(sender, QtCore.QObject):
            if sender.property("type") == "background":
                self.background_mode = True
            elif sender.property("type") == "data":
                self.background_mode = False
        
        if self.background_mode == False:
            path = self.file_input.text()
            print("Opening background file from text")
        elif self.background_mode == True:
            path = self.background_input.text()
            print("Opening background file from text")
        
        self.controller.openFiles((path), False)
    
    def subtractBackground(self):
        # data containers
        datacontainers = self.controller.view.getDataContainerList()
        
        if len(datacontainers) >= 2:
            wizard = View.GraphWizard.GraphWizard(None)
            
            print("Subtracting background...")
            # no background data container
            nc = wizard.subtractBackgroundData(datacontainers[0], datacontainers[1])
            wizard.close()
        
            print("Plotting data points...")
            viewer = View.DataPointViewer.DataPointViewer(nc, None, 0)
            viewer.show()
    
    def checkFiles(self):
        datacontainers = self.controller.view.getDataContainerList()
        
        if len(datacontainers) >= 2:
            self.file_input.setText(datacontainers[0].filepath)
            self.background_input.setText(datacontainers[1].filepath)
            
            self.ok_button.setEnabled(False)
            
            return True
        else:
            self.ok_button.setEnabled(True)
            return False
    
    def actionFileOpened(self, datacontainer):
        if self.background_mode == False:
            self.background_mode = True
            self.openFiles()
        elif self.background_mode == True:
            self.background_mode = None
            self.subtractBackground()
        
        self.checkFiles()
    
    def actionExit(self):
        sys.exit(0)

print("Initializing Gui...")
# start qt application and event loop
app = QtWidgets.QApplication.instance()
if not app or app == None:
    app = QtWidgets.QApplication(sys.argv)

print("Starting program...")
quick = QuickRemove()
quick.exec()

sys.exit(app.exec_())