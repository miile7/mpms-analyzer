# -*- coding: utf-8 -*-
"""
Created on Mon Nov  6 14:31:40 2017

@author: Maximilian Seidler
"""

from PyQt5 import QtCore, QtWidgets, QtGui

import Constants
import View.MainWindow

class AboutDialog(QtWidgets.QDialog):
    def __init__(self, parent = None):
        super(AboutDialog, self).__init__(parent, QtCore.Qt.WindowCloseButtonHint |
                QtCore.Qt.WindowMinimizeButtonHint)
        
        self.setModal(True)
        self.setWindowIcon(QtGui.QIcon(View.MainWindow.MainWindow.ICON))
        self.resize(QtCore.QSize(600, 300))
        
        # the icon
        size = QtCore.QSize(150, 150)
        pixmap = QtGui.QPixmap(View.MainWindow.MainWindow.ICON)
        pixmap = pixmap.scaled(size, QtCore.Qt.KeepAspectRatio)
#         qp.drawPixmap(posX, posY, width, height, pixmap.scaled(width, height, transformMode=QtCore.Qt.SmoothTransformation))
        icon = QtWidgets.QLabel(self)
        icon.setPixmap(pixmap);
#        icon.setMask(pixmap.mask());
#        icon.setScaledContents(True)
        icon.resize(size)
        
        text = ("<b>" + Constants.NAME + " v" + Constants.VERSION + "</b><br />" + 
                Constants.COMPANY + "<br />" + 
                "Licensed under GNU General Public License (GPL v3)<br />" + 
                "2018<br /><br />" + 
                "Created by Maximilian Seidler with help of Dr. Anton Jesche<br />" + 
                "Many thanks to Prof. Dr. Philipp Gegenwart and the Chair of " + 
                "Experimental Physics VI. <br />" + 
                "If you have any questions ask the developers or have a look in " + 
                "the code, there is no help or docs available at the moment.<br /><br />" + 
                "Version: 1.0<br />" + 
                "Recommended python version: 3.x<br />" + 
                "Recommended Qt version: 5.5.x<br /><br />" + 
                "Icons are done by Archil Imnadze (downloaded via " + 
                "<a href='https://www.iconfinder.com'>iconfinder.com</a>) and " + 
                "Maximilian Seidler")
                
        
        text = QtWidgets.QLabel(text)
        text.setWordWrap(True)
        
        top_layout = QtWidgets.QHBoxLayout()
        top_layout.addStretch(1)
        top_layout.addWidget(icon)
        top_layout.addStretch(1)
        top_layout.addWidget(text)
        
        dialog_layout = QtWidgets.QVBoxLayout()
        dialog_layout.addItem(top_layout)
        
        # OK and Cancel buttons
        buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok)
        buttons.accepted.connect(self.accept)
        
        dialog_layout.addWidget(buttons)
        
        self.setLayout(dialog_layout)