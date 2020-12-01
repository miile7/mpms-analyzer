# -*- coding: utf-8 -*-
"""
Created on Mon Oct 30 10:11:41 2017

@author: Maximilian Seidler
"""

print("Importing packages...")
from PyQt5 import QtWidgets
import sys

import View.QCollapsableWidget

print("Preparing program...")
app = QtWidgets.QApplication.instance()
if not app or app == None:
    app = QtWidgets.QApplication(sys.argv)

dialog = QtWidgets.QDialog()

widget = View.QCollapsableWidget.QCollapsableWidget(
        QtWidgets.QLabel("hi"))
widget.setButtonText("A very long text for this button which is way too long to display the complete text so it has to be cutted off anywhere in here")

layout = QtWidgets.QVBoxLayout()
layout.addWidget(widget)

dialog.setLayout(layout)

print("Ready.")

dialog.show()

sys.exit(app.exec())