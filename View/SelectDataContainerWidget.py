# -*- coding: utf-8 -*-
"""
Created on Wed Jan 24 09:08:56 2018

@author: Maximilian Seidler
"""

from PyQt5 import QtWidgets, QtCore, QtGui

import DataHandling.DataContainer
import View.DataContainerWidget
import View.QCollapsableWidget
import View.MainWindow
import my_utilities

class SelectDataContainerWidget(QtWidgets.QWidget):
    OPEN_MODE_FILE = "file"
    OPEN_MODE_VIEW = "view" 
    
    # this is more open, PyQt_PyObject is the C++ wrapper object for each python
    # object but setting the Signal to the DataContainer directly this does not
    # work for any reason, getting an error
    openedDataContainer = QtCore.pyqtSignal('PyQt_PyObject')
    
    @property
    def selected_datacontainer(self):
        return self._selected_datacontainer
    
    @selected_datacontainer.setter
    def selected_datacontainer(self, datacontainer):
        if isinstance(datacontainer, DataHandling.DataContainer.DataContainer):
            self._setDataContainerDisplay(datacontainer)
            self._selected_datacontainer = datacontainer
            return True
        else:
            return False
    
    def __init__(self, controller, parent = None):
        """Initialize the SelectDataContainerWidget
        
        Parameters
        ----------
            controller : Controller
                The current controller object
            parent : QWidget, optional
                The parent
        """
        
        super(SelectDataContainerWidget, self).__init__(parent)
        
        # save the view
        self.controller = controller
        
        # the temporary datacontainer list when the datacontainers are loaded
        # from the view
        self._current_datacontainers = None
        
        # additional datacontainers that can be added to the current datacontainers 
        # from outside
        self.additional_datacontainers = None
        
        # the datacontainer that has been selected
        self._selected_datacontainer = None
        
        # the mode how the datacontainer has been opend
        self.open_mode = None
        
        # the radio buttons in the datacontainer open dialog and the ok button
        self._dialog_radios = []
        self._dialog_ok_button = None
        
        # whether the widget is currently opening a file or not
        self._opening_file = False
        
        # the internal layout
        layout = QtWidgets.QHBoxLayout()
        
        # the display of the currently selected datacontainer
        self._display = QtWidgets.QLineEdit()
        self._display.setReadOnly(True)
        layout.addWidget(self._display)
        
        # the menu for the button
        button_menu = QtWidgets.QMenu()
        
        # the browse file menu entry
        self._browse_file = QtWidgets.QAction("Open new file", self)
        self._browse_file.triggered.connect(self._showOpenFile)
        button_menu.addAction(self._browse_file)
        
        # the browse datacontainers menu entry
        self._browse_datacontainers = QtWidgets.QAction("Select from open files", self)
        self._browse_datacontainers.triggered.connect(self._showOpenFromView)
        button_menu.addAction(self._browse_datacontainers)
        
        # the button
        self._browse_button = QtWidgets.QToolButton()
        self._browse_button.setText("Browse")
        self._browse_button.setPopupMode(QtWidgets.QToolButton.MenuButtonPopup);
        self._browse_button.setMenu(button_menu)
        self._browse_button.setMinimumSize(75, 22)
        self._browse_button.clicked.connect(self.showMenu)
        layout.addWidget(self._browse_button)
        
        self.setLayout(layout)
    
    def _showOpenFile(self):
        """Displays the file open dialog of the MainWindow"""
        
        # the open file callback
        self.controller.openedDataContainer.connect(self._openedFile)
        self._opening_file = True
        
        self.controller.view.showOpenDialog("Open the raw file", self)
    
    def _openedFile(self, datacontainer):
        """Action method for the view when a file has been opened
        
        Parameters
        ----------
            datacontainer : DataContainer
                The datacontainer that has been opened
        """
        
        if self._opening_file:
            self._opening_file = False
            
            # disconnecting the file opened signal
            self.controller.openedDataContainer.disconnect(self._openedFile)
            
            self._selected_datacontainer = datacontainer
            self.open_mode = SelectDataContainerWidget.OPEN_MODE_FILE
            
            self._openedFileFinish()
    
    def _showOpenFromView(self):
        """Displays the already opened datacontainers of the view"""
        
        # save the current datacontainers for keeping the indices
        self._current_datacontainers = self.controller.getDataContainerList()
        datacontainers = self._getCurrentDataContainers()
        
        # create the dialog
        dialog = QtWidgets.QDialog(self, 
                QtCore.Qt.WindowCloseButtonHint)
        dialog.setWindowTitle("Open the file already opened datacontainers")
        dialog.setWindowIcon(QtGui.QIcon(View.MainWindow.MainWindow.ICON))
        dialog.setStyleSheet("QRadioButton{padding: 7px 4px;}" + 
                             "QRadioButton.dark{background-color: #eee;}")
        
        # the dialog layout
        dialog_layout = QtWidgets.QVBoxLayout()
        
        # the splitter
        self._dialog_splitter = QtWidgets.QSplitter()
        
        # the scroll pane layout
        layout = QtWidgets.QVBoxLayout()
        
        # the radio buttons
        self._dialog_radios = []
        
        # show the datacontainers in the dialog
        for i, datacontainer in enumerate(datacontainers):
            # the selection radio button
            radio = QtWidgets.QRadioButton(datacontainer.createName())
            radio.setProperty("datacontainer_index", i)
            
            if i % 2 == 1:
                radio.setObjectName("dark")
                radio.setProperty("class", "dark")
                
            radio.toggled.connect(self._dialogRadioCallback)
            self._dialog_radios.append(radio)
            
            layout.addWidget(radio)
        
        layout.addStretch()
        
        # the scroll area
        scroll_widget = QtWidgets.QScrollArea()
        scroll_widget.setStyleSheet("QScrollArea{background: #fff;}")
        scroll_widget.setLayout(layout)
        
        self._dialog_splitter.addWidget(scroll_widget)
        dialog_layout.addWidget(self._dialog_splitter)
        
        dialog_preview_widget = QtWidgets.QWidget()
        self._dialog_splitter.addWidget(dialog_preview_widget)
        
        self._dialog_splitter.setSizes([300, 400])
        
        # the buttons
        buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok |
                QtWidgets.QDialogButtonBox.Cancel)
        buttons.rejected.connect(dialog.reject)
        buttons.accepted.connect(dialog.accept)
        
        # the ok button
        self._dialog_ok_button = buttons.button(QtWidgets.QDialogButtonBox.Ok)
        self._dialog_ok_button.setEnabled(False)
        
        dialog_layout.addWidget(buttons)
        
        dialog.setLayout(dialog_layout)
        
        dialog.resize(700, 600)
        
        # execute the dialog
        result = dialog.exec()
        
        if result == 1:
            # save the datacontainer
            self._selected_datacontainer = self._getRadioDataContainer()
            
            if self._selected_datacontainer != None:
                self._current_datacontainers = None
                self._openedFileFinish()
        
        # reset the values
        self._dialog_ok_button = None
        self._dialog_radios = []
    
    def _getCurrentDataContainers(self):
        """Get the current datacontainers with the additional datacontainers for
        the opened files dialog
        
        Returns
        -------
            list
                The current datacontainers with the additional datacontainers
        """
        
        if my_utilities.is_iterable(self.additional_datacontainers):
            datacontainers = self._current_datacontainers[:]
            
            for datacontainer in self.additional_datacontainers:
                if datacontainer not in datacontainers:
                    datacontainers.append(datacontainer)
        else:
            datacontainers = self._current_datacontainers
        
        return datacontainers
    
    def _getRadioDataContainer(self):
        """Find the checked radio box which holds the datacontainer index and
        return the corresponding datacontainer
        
        Returns
        -------
            DataContainer
                The selected datacontainer
        """
        
        for radio in self._dialog_radios:
            if radio.isChecked():
                # the index of the datacontainer in the internal list
                index = int(radio.property("datacontainer_index"))
                
                datacontainers = self._getCurrentDataContainers()
                
                # check if the index is valid
                if index >= 0 and index < len(datacontainers):
                    return datacontainers[index]
        
        return None
    
    def _dialogRadioCallback(self):
        """The action method for the dialog if a radio button is clicked. If there
        is no selected radio button the ok button is disabled, if there is a 
        button the ok button will be enabled"""
        
        disable = True
        
        for radio in self._dialog_radios:
            if radio.isChecked():
                self._dialog_ok_button.setEnabled(True)
                disable = False
        
        if disable:
            self._dialog_ok_button.setEnabled(False)
        
        datacontainer = self._getRadioDataContainer()
        
        if datacontainer != None:
            # the container widget
            dialog_preview_widget = View.DataContainerWidget.DataContainerWidget(
                    datacontainer, self.controller.view)
            dialog_preview_widget.setState(View.QCollapsableWidget.QCollapsableWidget.EXPANDED)
            dialog_preview_widget.showControls(False)
            
            w = self._dialog_splitter.widget(1)
            w.hide()
            w.setParent(None)
            del w
            
            self._dialog_splitter.insertWidget(1, dialog_preview_widget)
    
    def _openedFileFinish(self):
        """The opening has been finished, this will update the display and emit
        the finish signal"""
        
        if isinstance(self._selected_datacontainer, DataHandling.DataContainer.DataContainer):
            self._setDataContainerDisplay(self._selected_datacontainer)
        
        self.openedDataContainer.emit(self._selected_datacontainer)
        
    def _setDataContainerDisplay(self, datacontainer):
        """Update the display, display the name of the given datacontainer"""
        
        self._display.setText(datacontainer.createName())
        self._display.setCursorPosition(0)
    
    def showMenu(self):
        """Opens the menu"""
        self._browse_button.showMenu()
    
    def setEnabled(self, enabled):
        """Overwrite the parent method for passing the value to the child widgets"""
        self._display.setEnabled(enabled)
        self._browse_button.setEnabled(enabled)
        
        super(SelectDataContainerWidget, self).setEnabled(enabled)
    
    def setReadOnly(self, read_only):
        """Overwrite the parent method for passing the value to the child widgets"""
        self._display.setReadOnly(read_only)
        self._browse_button.setReadOnly(read_only)
        
        super(SelectDataContainerWidget, self).setReadOnly(read_only)
    
    def getDataContainerIndex(self):
        """Get the index of the selected datacontainer in the controller collection
        
        Return
        ------
            int
                The index or None if it is not found or not from the list"""
        
        datacontainer_list = self.controller.getDataContainerList()
        
        if self._selected_datacontainer in datacontainer_list:
            return datacontainer_list.index(self._selected_datacontainer)
        else:
            return None