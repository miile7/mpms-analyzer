# -*- coding: utf-8 -*-
"""
Created on Wed Feb 14 15:32:17 2018

@author: Maximilian Seidler
"""
from PyQt5 import QtCore, QtGui, QtWidgets
import os

import View.PlotCanvas
import DataHandling.DataContainer

class ToolOutputPage(QtWidgets.QWizardPage):
    def __init__(self, parent = None):
        
        super(ToolOutputPage, self).__init__(parent)
        
        self._replace_path = {
                'mpms_raw': False,
                'mpms_dat': False,
                'csv': False}
        
        # set title and description
        self.setTitle("Save data")
        self.setSubTitle("Select how to save the new data.")
        
        self.initialized = False
        
    def initializePage(self):
        """Initialize the QWizardPage"""
        wizard = self.wizard()
        
        layout = QtWidgets.QGridLayout()
        
        # preview
        wizard.result_canvas = self.getPreview(wizard.getResultPreview(), True)
        layout.addWidget(wizard.result_canvas, 0, 0, 1, 3)
        
        # create mpms raw file
        self._save_to_mpms_raw_file = QtWidgets.QCheckBox("Create a new raw mpms file")
        self._save_to_mpms_raw_file.stateChanged.connect(self.actionValuesChanged)
        layout.addWidget(self._save_to_mpms_raw_file, 1, 0)
        
        self._save_mpms_raw_file_name = QtWidgets.QLineEdit()
        self._save_mpms_raw_file_name.setReadOnly(True)
        layout.addWidget(self._save_mpms_raw_file_name, 1, 1)
        
        self._save_mpms_raw_file_button = QtWidgets.QPushButton("Select file")
        self._save_mpms_raw_file_button.clicked.connect(self.showSaveDialog)
        self._save_mpms_raw_file_button.setProperty("fileending", "rw.dat")
        self._save_mpms_raw_file_button.setEnabled(False)
        layout.addWidget(self._save_mpms_raw_file_button, 1, 2)
        
        # create mpms dat file
        self._save_to_mpms_dat_file = QtWidgets.QCheckBox("Create a new dat mpms file")
        self._save_to_mpms_dat_file.stateChanged.connect(self.actionValuesChanged)
        layout.addWidget(self._save_to_mpms_dat_file, 2, 0)
        
        self._save_mpms_dat_file_name = QtWidgets.QLineEdit()
        self._save_mpms_dat_file_name.setReadOnly(True)
        layout.addWidget(self._save_mpms_dat_file_name, 2, 1)
        
        self._save_mpms_dat_file_button = QtWidgets.QPushButton("Select file")
        self._save_mpms_dat_file_button.clicked.connect(self.showSaveDialog)
        self._save_mpms_dat_file_button.setProperty("fileending", "dat")
        self._save_mpms_dat_file_button.setEnabled(False)
        layout.addWidget(self._save_mpms_dat_file_button, 2, 2)
        
        # create csv file
        self._save_to_csv_file = QtWidgets.QCheckBox("Create a new csv file")
        self._save_to_csv_file.stateChanged.connect(self.actionValuesChanged)
        layout.addWidget(self._save_to_csv_file, 3, 0)
        
        self._save_csv_file_name = QtWidgets.QLineEdit()
        self._save_csv_file_name.setReadOnly(True)
        layout.addWidget(self._save_csv_file_name, 3, 1)
        
        self._save_csv_file_button = QtWidgets.QPushButton("Select file")
        self._save_csv_file_button.clicked.connect(self.showSaveDialog)
        self._save_csv_file_button.setProperty("fileending", "csv")
        self._save_csv_file_button.setEnabled(False)
        layout.addWidget(self._save_csv_file_button, 3, 2)
        
        # load properties
        window_enabled = wizard.view.isVisible()
        
        self._save_in_window_list = QtWidgets.QCheckBox("Save in current window")
        self._save_in_window_list.setEnabled(window_enabled)
        self._save_in_window_list.stateChanged.connect(self.actionValuesChanged)
        layout.addWidget(self._save_in_window_list, 4, 0, 1, 3)
        
        self._overwrite_label = QtWidgets.QLabel("Overwrite opened data")
        layout.addWidget(self._overwrite_label, 5, 0)
        
        overwrite_box = QtWidgets.QHBoxLayout()
        
        self._overwrite_yes = QtWidgets.QRadioButton("Yes")
        overwrite_box.addWidget(self._overwrite_yes)
        
        self._overwrite_no = QtWidgets.QRadioButton("No")
        self._overwrite_no.setChecked(True)
        overwrite_box.addWidget(self._overwrite_no)
        
        overwrite_box.addStretch(1)
        
        layout.addLayout(overwrite_box, 5, 1, 1, 2)
        
        self._plot_in_window = QtWidgets.QCheckBox("Plot to current window")
        self._plot_in_window.setEnabled(window_enabled)
        self._plot_in_window.stateChanged.connect(self.actionValuesChanged)
        layout.addWidget(self._plot_in_window, 6, 0, 1, 3)
        
        self.setLayout(layout)
        
        wizard.button(QtWidgets.QWizard.BackButton).setEnabled(False)
        
        # set defaults
        self._save_to_mpms_raw_file.setChecked(
                wizard.output_mode & View.ToolWizard.ToolWizard.ToolWizard.OUTPUT_MODE_EXPORT_RAW_MPMS > 0)
        self._save_to_mpms_dat_file.setChecked(
                wizard.output_mode & View.ToolWizard.ToolWizard.ToolWizard.OUTPUT_MODE_EXPORT_DAT_MPMS > 0)
        self._save_to_csv_file.setChecked(
                wizard.output_mode & View.ToolWizard.ToolWizard.ToolWizard.OUTPUT_MODE_EXPORT_CSV > 0)
        self._save_in_window_list.setChecked(
                wizard.output_mode & View.ToolWizard.ToolWizard.ToolWizard.OUTPUT_MODE_SAVE_LIST > 0)
        self._plot_in_window.setChecked(
                wizard.output_mode & View.ToolWizard.ToolWizard.ToolWizard.OUTPUT_MODE_PLOT_WINDOW > 0)
        
        # show/hide depending on ToolWizard
        
        # toggle plot output mode
        if wizard.visible_output_modes & View.ToolWizard.ToolWizard.ToolWizard.OUTPUT_MODE_PLOT_WINDOW == 0:
            self._plot_in_window.hide()
        else:
            self._plot_in_window.show()
            
        # toggle files list output mode
        if wizard.visible_output_modes & View.ToolWizard.ToolWizard.ToolWizard.OUTPUT_MODE_SAVE_LIST == 0:
            self._save_in_window_list.hide()
            self._overwrite_label.hide()
            self._overwrite_yes.hide()
            self._overwrite_no.hide()
        else:
            self._save_in_window_list.show()
            self._overwrite_label.show()
            self._overwrite_yes.show()
            self._overwrite_no.show()
            
        # toggle mpms raw output mode
        if wizard.visible_output_modes & View.ToolWizard.ToolWizard.ToolWizard.OUTPUT_MODE_EXPORT_RAW_MPMS == 0:
            self._save_to_mpms_raw_file.hide()
            self._save_mpms_raw_file_name.hide()
            self._save_mpms_raw_file_button.hide()
        else:
            self._save_to_mpms_raw_file.show()
            self._save_mpms_raw_file_name.show()
            self._save_mpms_raw_file_button.show()
            
        # toggle mpms dat output mode
        if wizard.visible_output_modes & View.ToolWizard.ToolWizard.ToolWizard.OUTPUT_MODE_EXPORT_DAT_MPMS == 0:
            self._save_to_mpms_dat_file.hide()
            self._save_mpms_dat_file_name.hide()
            self._save_mpms_dat_file_button.hide()
        else:
            self._save_to_mpms_dat_file.show()
            self._save_mpms_dat_file_name.show()
            self._save_mpms_dat_file_button.show()
            
        # toggle csv output mode
        if wizard.visible_output_modes & View.ToolWizard.ToolWizard.ToolWizard.OUTPUT_MODE_EXPORT_CSV == 0:
            self._save_to_csv_file.hide()
            self._save_csv_file_name.hide()
            self._save_csv_file_button.hide()
        else:
            self._save_to_csv_file.show()
            self._save_csv_file_name.show()
            self._save_csv_file_button.show()
            
        if (wizard.visible_output_modes == View.ToolWizard.ToolWizard.ToolWizard.OUTPUT_MODE_PLOT_WINDOW):
            self.setTitle("Plot data")
        
        self.actionValuesChanged()
        
        if wizard.output_mode == 0:
            wizard.button(QtWidgets.QWizard.NextButton).setEnabled(False)
            wizard.button(QtWidgets.QWizard.FinishButton).setEnabled(False)
        
        own_id = wizard.getIdOfPage(self)
        wizard.addCalculation(own_id, self.performSaveRoutine, "Saving...")
        
        if not wizard.result_canvas.isHidden():
            wizard.changeSize(None, 800)
        else:
            wizard.changeSize(None, None)
            
        self.initialized = True
        
    def getPreview(self, preview, force_plot_canvas = False):
        """Get the perview depending on the given preview parameter. The parameter
        can be the PlotCanvas itself, a PlotData object or a axis list or tuple.
        If no perview can be generated this will return None, if the force_plot_canvas
        is True this will return a hidden PlotCanvas.
        
        Parameters
        ----------
            preview : PlotCanvas, list, tuple or PlotData
                The perview
            force_plot_canvas : boolean
                Whether to force returning a plot canvas or not
        
        Returns
        -------
            PlotCanvas
                The plot canvas or None if there is no plot canvas
        """
        
        wizard = self.wizard()
        
        if isinstance(wizard.result_canvas, View.PlotCanvas.PlotCanvas):
            plot_canvas = wizard.result_canvas
        else:
            plot_canvas = View.PlotCanvas.PlotCanvas()
            
        show = False
        datacontainer_prints = wizard.getAllowedDataContainerAxis()
        
        if isinstance(preview, (list, tuple)):
            x_axis = None
            y_axis = None
            
            for p in preview:
                if isinstance(p, DataHandling.PlotData.PlotData):
                    plot_canvas.addPlotData(p)
                    show = True
                elif isinstance(p, View.PlotCanvas.PlotCanvas):
                    plot_canvas.addPlotData(p.getPlotData())
                    show = True
                elif p in datacontainer_prints:
                    if x_axis == None:
                        x_axis = p
                    elif y_axis == None:
                        y_axis = p
                        
            if x_axis != None and y_axis != None:
                plot_data = None
                
                if (wizard.result_datacontainer != None and 
                    isinstance(wizard.result_datacontainer, DataHandling.DataContainer.DataContainer)):
                    plot_data = wizard.result_datacontainer.getPlotData(x_axis, y_axis)
                
#                if (plot_data == None and
#                    wizard.sample_datacontainer != None and 
#                    isinstance(wizard.sample_datacontainer, DataHandling.DataContainer.DataContainer)):
#                    plot_data = wizard.sample_datacontainer.getPlotData(x_axis, y_axis)
#                
#                if (plot_data == None and
#                    wizard.background_datacontainer != None and 
#                    isinstance(wizard.background_datacontainer, DataHandling.DataContainer.DataContainer)):
#                    plot_data = wizard.background_datacontainer.getPlotData(x_axis, y_axis)
                    
                if plot_data != None:
                    plot_canvas.addPlotData(plot_data)
                    show = True
        elif isinstance(preview, DataHandling.PlotData.PlotData):
            plot_canvas.addPlotData(preview)
            show = True
        elif isinstance(preview, View.PlotCanvas.PlotCanvas):
            plot_canvas = preview
            show = True
        
        if show:
            return plot_canvas
        elif force_plot_canvas:
            plot_canvas.setVisible(False)
            return plot_canvas
        else:
            return None
        
    def isValidPreview(self, preview):
        """Get whether the given preview is valid or not
        
        Returns
        -------
            boolean
                Whether the perview is valid or not
        """
        
        p = preview
        preview = self.getPreview(preview)
        
        valid = (preview != None and isinstance(preview, View.PlotCanvas.PlotCanvas))
        
        print("ToolOutputPage.isValidPreview(): preview", p, ", valid: ", valid)
        
        return valid
#    
    def actionValuesChanged(self):
        """The action method when the checkboxes for the output changed"""
        
        if self._save_to_mpms_raw_file.isChecked():
            self._save_mpms_raw_file_name.setEnabled(True)
            self._save_mpms_raw_file_button.setEnabled(True)
        else:
            self._save_mpms_raw_file_name.setEnabled(False)
            self._save_mpms_raw_file_button.setEnabled(False)
            
        if self._save_to_mpms_dat_file.isChecked():
            self._save_mpms_dat_file_name.setEnabled(True)
            self._save_mpms_dat_file_button.setEnabled(True)
        else:
            self._save_mpms_dat_file_name.setEnabled(False)
            self._save_mpms_dat_file_button.setEnabled(False)
            
        if self._save_to_csv_file.isChecked():
            self._save_csv_file_name.setEnabled(True)
            self._save_csv_file_button.setEnabled(True)
        else:
            self._save_csv_file_name.setEnabled(False)
            self._save_csv_file_button.setEnabled(False)
            
        if self._save_in_window_list.isChecked():
            self._overwrite_yes.setEnabled(True)
            self._overwrite_no.setEnabled(True)
        else:
            self._overwrite_yes.setEnabled(False)
            self._overwrite_no.setEnabled(False)
        
        self.completeChanged.emit()
    
    def isComplete(self):
        """Check whether the page is complete
        
        Returns
        -------
            boolean
                Whether the page is complete or not
        """
        if not self.initialized:
            return False
        
        if (self._save_to_mpms_raw_file.isChecked() and 
            len(self._save_mpms_raw_file_name.text()) > 0):
            return True
        elif (self._save_to_mpms_dat_file.isChecked() and 
            len(self._save_mpms_dat_file_name.text()) > 0):
            return True
        elif (self._save_to_csv_file.isChecked() and 
            len(self._save_csv_file_name.text()) > 0):
            return True
        elif self._save_in_window_list.isChecked():
            return True
        elif self._plot_in_window.isChecked():
            return True
        
        return False
    
    def validatePage(self):
        """Check whether the page is valid. If there is no checkbox selected
        this will show a confirm message.
        
        Returns
        -------
            boolean
                Whether the page is valid or not
        """
        
        if not self.isComplete():
            msg_box = QtWidgets.QMessageBox()
            msg_box.setWindowTitle("Changes will be lost!")
            msg_box.setWindowIcon(QtGui.QIcon(View.MainWindow.MainWindow.ICON))
            msg_box.setText("No checkbox has been checked!")
            msg_box.setIcon(QtWidgets.QMessageBox.Warning)
            msg_box.setInformativeText("All changes of this data which have been " + 
                                       "made in this wizard will be lost!")
            msg_box.setStandardButtons(QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel)
            msg_box.setDefaultButton(QtWidgets.QMessageBox.Cancel)
            ret = msg_box.exec()
            
            if ret == QtWidgets.QMessageBox.Ok:
                return True
            else:
                return False
        else:
            return True
            
    def showSaveDialog(self):
        """Display the save dialog. The selected name will be chosen by the 
        senders fileending property and the name of the wizards result datacontainer
        """
        
        wizard = self.wizard()
        
        file_filter = "All files (*.*)"
        sender = self.sender()
        
        if isinstance(sender, QtCore.QObject):
            fileending = sender.property("fileending")
            
            if fileending == "csv":
                file_filter = "CSV files (*.csv);;" + file_filter
            elif fileending == "rw.dat":
                file_filter = "Raw mpms files (*.rw.dat);;" + file_filter
            elif fileending == "dat":
                file_filter = "Mpms files (*.dat);;" + file_filter
        
        path = os.path.dirname(wizard.getDefaultSavePath())
        
        name = str(os.path.basename(wizard.getDefaultSavePath()))
        name = name.rsplit(".rw.dat", 1)
        
        if len(name) == 1:
            name = name.rsplit(".dat", 1)
        
        name = name[0]
        name += "-" + wizard.getSaveNameSuffix()
        
        filename, filters = QtWidgets.QFileDialog.getSaveFileName(
                self, 
                "Save to file",
                os.path.join(path, name),
                file_filter)
        
        if isinstance(filename, str):
            if fileending == "csv":
                self._save_csv_file_name.setText(filename)
            elif fileending == "rw.dat":
                self._save_mpms_raw_file_name.setText(filename)
            elif fileending == "dat":
                self._save_mpms_dat_file_name.setText(filename)
            
            self.completeChanged.emit()

# this is checked by the file open dialog already
#    def beforeCalculation(self):
#        conflicts = {}
#        
#        if (self._save_to_mpms_raw_file.isChecked() and 
#            os.path.isfile(self._save_mpms_raw_file_name.text())):
#            conflicts['mpms_raw'] = self._save_mpms_raw_file_name.text()
#        
#        if (self._save_to_mpms_dat_file.isChecked() and 
#            os.path.isfile(self._save_mpms_dat_file_name.text())):
#            conflicts['mpms_dat'] = self._save_mpms_dat_file_name.text()
#        
#        if (self._save_to_csv_file.isChecked() and 
#            os.path.isfile(self._save_csv_file_name.text())):
#            conflicts['csv'] = self._save_csv_file_name.text()
#        
#        if conflicts != False:
#            for i, key in enumerate(conflicts):
#                conflict = conflicts[key]
#                r = len(conflicts) - i - 1
#                
#                text = ("The file <i>{}</i> already exists. Do you want to rename " + 
#                    "it into {} to keep the original file?<br />If you click on " + 
#                    "'No' the file will be replaced.").format(
#                            conflict, self.getNoConflictName(conflict))
#                
#                if r > 0:
#                    text += "<br /><br />There are {} more conflicts.".format(r)
#                
#                dialog = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Question,
#                                               "The file does already exist",
#                                               text,
#                                               QtWidgets.QMessageBox.YesToAll | 
#                                               QtWidgets.QMessageBox.Yes | 
#                                               QtWidgets.QMessageBox.No
#                                               )
#                
#                result = dialog.exec()
#                
#                if result == QtWidgets.QMessageBox.YesToAll:
#                    for replace_key in self._replace_path:
#                        self._replace_path[replace_key] = False
#                    break
#                elif result == QtWidgets.QMessageBox.Yes:
#                    self._replace_path[key] = False
#                else:
#                    self._replace_path[key] = True
    
    def getNoConflictName(self, path):
        """Returns a valid path for the given path
        
        Parameters
        ----------
            path : String
                The path to check
        
        Returns
        -------
            String
                The path that should be used instead of the given path
        """
        
        return path
        
        # disabled conflicting names are warned in the QFileDialog
        i = 1
        filename, extension = os.path.splitext(path)
        
        while os.path.isfile(filename + " ({})".format(i) + extension) and i < 10000:
            i += 1
        
        return filename + " ({})".format(i) + extension
    
    def nextId(self):
        """Get the id of the next page
        
        Returns
        -------
            int
                The id of the next page
        """
        
        wizard = self.wizard()
        
        if wizard.output_mode & View.ToolWizard.ToolWizard.ToolWizard.OUTPUT_MODE_PLOT_WINDOW > 0:
            return wizard.axis_index
        elif wizard.output_mode & View.ToolWizard.ToolWizard.ToolWizard.OUTPUT_MODE_EXPORT_CSV > 0:
            return wizard.csv_export_index
        else:
            return -1
    
    def performSaveRoutine(self):
        """Performs the saving routine, this will set all the values in the 
        ToolWizard so it knows what to save where"""
        
        wizard = self.wizard()
        
        # the actual saving is done in the ToolWizard.performClosingRoutine() function,
        # this is just preparing all values to save
        
        if self._save_to_mpms_raw_file.isChecked():
            filename = self._save_mpms_raw_file_name.text()
            if os.path.isfile(filename) and not self._replace_path['mpms_raw']:
                filename = self.getNoConflictName(filename)
                
            wizard.result_mpms_raw_file = filename
            # add mode
            wizard.output_mode |= View.ToolWizard.ToolWizard.ToolWizard.OUTPUT_MODE_EXPORT_RAW_MPMS
        else:
            # remove mode, it is not selected
            wizard.output_mode &= ~View.ToolWizard.ToolWizard.ToolWizard.OUTPUT_MODE_EXPORT_RAW_MPMS
                
        if self._save_to_mpms_dat_file.isChecked():
            filename = self._save_mpms_dat_file_name.text()
            if os.path.isfile(filename) and not self._replace_path['mpms_dat']:
                filename = self.getNoConflictName(filename)
                
            wizard.result_mpms_dat_file = filename
            wizard.output_mode |= View.ToolWizard.ToolWizard.ToolWizard.OUTPUT_MODE_EXPORT_DAT_MPMS
        else:
            # remove mode, it is not selected
            wizard.output_mode &= ~View.ToolWizard.ToolWizard.ToolWizard.OUTPUT_MODE_EXPORT_DAT_MPMS
                
        if self._save_to_csv_file.isChecked():
            filename = self._save_csv_file_name.text()
            if os.path.isfile(filename) and not self._replace_path['csv']:
                filename = self.getNoConflictName(filename)
                
            wizard.result_csv_file = filename
            wizard.output_mode |= View.ToolWizard.ToolWizard.ToolWizard.OUTPUT_MODE_EXPORT_CSV
        else:
            # remove mode, it is not selected
            wizard.output_mode &= ~View.ToolWizard.ToolWizard.ToolWizard.OUTPUT_MODE_EXPORT_CSV
        
        if self._save_in_window_list.isChecked():
            wizard.output_mode |= View.ToolWizard.ToolWizard.ToolWizard.OUTPUT_MODE_SAVE_LIST
            
            if self._overwrite_yes.isChecked():
                wizard.overwrite_filelist = True
        else:
            # remove mode, it is not selected
            wizard.output_mode &= ~View.ToolWizard.ToolWizard.ToolWizard.OUTPUT_MODE_SAVE_LIST
        
        if self._plot_in_window.isChecked():
            wizard.output_mode |= View.ToolWizard.ToolWizard.ToolWizard.OUTPUT_MODE_PLOT_WINDOW
        else:
            # remove mode, it is not selected
            wizard.output_mode &= ~View.ToolWizard.ToolWizard.ToolWizard.OUTPUT_MODE_PLOT_WINDOW
