# -*- coding: utf-8 -*-
"""
Created on Wed Feb 14 14:15:32 2018

@author: Maximilian Seidler
"""

from PyQt5 import QtCore, QtGui, QtWidgets
import warnings
import sys
import os

import my_utilities
import View.MainWindow
import DataHandling.ToolWorker
import View.ToolWizard.ToolPlotPage
import View.ToolWizard.ToolAxisPage
import View.ToolWizard.ToolInputPage
import View.ToolWizard.ToolOutputPage
import View.ToolWizard.ToolCSVExportPage

class ToolWizard(QtWidgets.QWizard):
    OUTPUT_MODE_PLOT_WINDOW = 0b1
    OUTPUT_MODE_SAVE_LIST = 0b10
    OUTPUT_MODE_EXPORT_RAW_MPMS = 0b100
    OUTPUT_MODE_EXPORT_DAT_MPMS = 0b1000
    OUTPUT_MODE_EXPORT_CSV = 0b10000
    
    def __init__(self, controller, parent = None, *tools):
        """Initialize the graph wizard.
        Parameters
        ----------
            controller : Controller
                The controller
            parent : QWidget, optional
                The parent
        """
        
        super(ToolWizard, self).__init__(parent, QtCore.Qt.WindowCloseButtonHint)
        
        # set title, icon and geometry
        self.setWindowTitle("Graph Manager")
        self.setWindowIcon(QtGui.QIcon(View.MainWindow.MainWindow.ICON))
        self.default_size = QtCore.QSize(640, 480)
        self.resize(self.default_size)
        
        self.controller = controller
        self.view = self.controller.view
        
        self._error_dialog = None
        
        self._tools = []
        self._calculations = {}
        
        self.output_mode = 0
        self.visible_output_modes = (
                ToolWizard.OUTPUT_MODE_PLOT_WINDOW |
                ToolWizard.OUTPUT_MODE_SAVE_LIST |
                ToolWizard.OUTPUT_MODE_EXPORT_RAW_MPMS |
                ToolWizard.OUTPUT_MODE_EXPORT_DAT_MPMS |
                ToolWizard.OUTPUT_MODE_EXPORT_CSV
                )
        
        self.hide_output_page = False
        
        self.show_background_datacontainer = False
        self.show_measurement_type = False
        
        self.standalone = not self.view.isVisible()
        
        self.sample_datacontainer = None
        self.background_datacontainer = None
        self.result_datacontainer = None
        
        self._measurement_variable = None
        
        self.result_mpms_raw_file = None
        self.result_mpms_dat_file = None
        self.result_csv_file = None
        self.result_csv_file_mode = None
        self.result_csv_file_columns = None
        self.overwrite_filelist = False
        self.result_canvas = None
        
        self._performing_calculation = False
        self._current_calculation = -1
        self._current_calculations = None
        self._current_calculation_worker = None
        self._current_calculation_thread = None
        
        self._error_count = 0
        
        input_page = View.ToolWizard.ToolInputPage.ToolInputPage()
        self._input_index = self.addPage(input_page)
        
        if len(tools) > 0:
            for tool in tools:
                self.addTool(tool)
                
        input_page.show_background_datacontainer = self.show_background_datacontainer
        
        # tools can add a page, add this page as the last page
        self._output_index = self.addPage(View.ToolWizard.ToolOutputPage.ToolOutputPage())
        self.axis_index = self.addPage(View.ToolWizard.ToolAxisPage.ToolAxisPage())
        self.plot_index = self.addPage(View.ToolWizard.ToolPlotPage.ToolPlotPage())
        self.csv_export_index = self.addPage(View.ToolWizard.ToolCSVExportPage.ToolCSVExportPage()) 
        
        self._initErrorDialog()
    
    @property
    def first_page_index(self):
        return self._input_index

    @first_page_index.setter
    def first_page_index(self, first_page_index):
        return False
    
    @property
    def last_page_index(self):
        return self._output_index

    @last_page_index.setter
    def last_page_index(self, last_page_index):
        return False
    
    @property
    def measurement_variable(self):
        return self._measurement_variable

    @measurement_variable.setter
    def measurement_variable(self, measurement_variable):
        self._measurement_variable = measurement_variable
        
        if isinstance(self.result_datacontainer, DataHandling.DataContainer.DataContainer):
            self.result_datacontainer.measurement_variable = measurement_variable

    def setInitSampleDataContainer(self, datacontainer):
        """Set the given datacontainer to the initialization datacontainer, this
        means that this will be set already when starting the wizard.
        
        Parameters
        ----------
            datacontainer : DataContainer
                The datacontainer
        """
        
        self.sample_datacontainer = datacontainer
        self.result_datacontainer = self.sample_datacontainer
        
        show_measurement_type = self.show_measurement_type
        
        if isinstance(self.result_datacontainer.measurement_variable, str):
            self.measurement_variable = self.result_datacontainer.measurement_variable
            show_measurement_type = False
        elif isinstance(self.measurement_variable, str):
            self.sample_datacontainer.measurement_variable = self.measurement_variable
            show_measurement_type = False
        
        if (isinstance(self.result_datacontainer, DataHandling.DataContainer.DataContainer) and
            self.show_background_datacontainer == False and 
            show_measurement_type == False):
            
            self.setStartId(self.nextId(self._input_index))
            
#            page_ids = self.pageIds()
#            
#            if self._input_index in page_ids:
#                index = page_ids.index(self._input_index)
#                
#                if index + 1 < len(page_ids):
#                    self.setStartId(page_ids[index + 1])
            

    def _initErrorDialog(self):
        """Initialize the error dialog"""
        
        self._error_dialog = QtWidgets.QDialog(self, QtCore.Qt.WindowCloseButtonHint)
        self._error_dialog.setWindowTitle("Error")
        self._error_dialog.setWindowIcon(self.windowIcon())
        
        s = 10
        layout = QtWidgets.QGridLayout()
        layout.setHorizontalSpacing(s)
        layout.setVerticalSpacing(s)
        layout.setContentsMargins(s, s, s, s)
        
        app = QtWidgets.QApplication.instance()
        if not app or app == None:
            app = QtWidgets.QApplication(sys.argv)
        
        icon_size = QtCore.QSize(35, 35)
        style = app.style()
        error_icon = style.standardIcon(QtWidgets.QStyle.SP_MessageBoxWarning)
        icon_label = QtWidgets.QLabel()
        icon_label.setPixmap(error_icon.pixmap(icon_size))
        icon_label.resize(icon_size)
        layout.addWidget(icon_label, 0, 0, 2, 1, QtCore.Qt.AlignTop)
        
        self._error_headline = QtWidgets.QLabel("One or more error(s) occurred.")
        self._error_headline.setMinimumSize(400, icon_size.height())
        layout.addWidget(self._error_headline, 0, 1)
        
        self._error_text = QtWidgets.QLabel()
        self._error_text.setWordWrap(True)
        self._error_text.setStyleSheet("QLabel{background: rgba(0, 0, 0, 0); padding: 5px;}")
        self._error_text.setMinimumSize(400, 10)
        scroll = QtWidgets.QScrollArea()
        scroll.setWidget(self._error_text)
        scroll.setStyleSheet("QScrollArea{background: #fff;}")
        layout.addWidget(scroll, 1, 1)
        
        buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok)
        buttons.accepted.connect(self._error_dialog.accept)
        layout.addWidget(buttons, 2, 1, 1, 2)
        
        self._error_dialog.setLayout(layout)
        self._error_dialog.resize(500, 300)
    
    def addCalculation(self, page_id, handler, calculating_text):
        """Add a calculation. The handler function will be executed when the
        page_id page is active. The calculating_text will be used for the 
        progress dialog
        
        Parameters
        ----------
            page_id : int
                The id of the page after which the handler should be executed
            handler : function
                The function to execute
            calculating_text : String
                The text to show in the progress dialog
        """
        
        if not page_id in self._calculations:
            self._calculations[page_id] = []
            
        self._calculations[page_id].append((handler, calculating_text))
    
    def addTool(self, tool):
        """Add a tool to the internal collection. This will also initialize the
        the tool.
        
        Parameters
        ----------
            tool : Tool
                The tool to add
        
        Returns
        -------
            int
                The id of the tool or None if it could not be added
        """
        
        if isinstance(tool, View.ToolWizard.Tool.Tool):
            tool.wizard = self
            
            tool.initializeTool()
            
            if tool.needs_background_datacontainer == True:
                self.show_background_datacontainer = True
            
            if tool.needs_measurement_type == True:
                self.show_measurement_type = True
            
            i = len(self._tools)
            
            self._tools.append(tool)
            
            return i
        else:
            return None
    
    def removeTool(self, index):
        """Removes the tool at the given index.
        
        Parameters
        ----------
            index : int
                The tool index
        """
        
        if index >= 0 and index < len(self._tools):
            self._tools[index] = None
    
    def getResultPreview(self):
        """Get the result preview. This will go through all the tools an return
        the first valid preview
        
        Returns
        -------
            PlotCanvas, PlotData, list or tuple
                The preview or None if there is no preview
        """
        
        for tool in reversed(self._tools):
            if isinstance(tool, View.ToolWizard.Tool.Tool):
                if self.page(self._output_index).isValidPreview(tool.preview):
                    return tool.preview
        
        if self._measurement_variable != None:
            return (self._measurement_variable, 
                    DataHandling.DataContainer.DataContainer.MAGNETIZATION)
        else:
            return (DataHandling.DataPoint.DataPoint.TIMESTAMP,
                    DataHandling.DataContainer.DataContainer.MAGNETIZATION)
    
    def getDefaultSavePath(self):
        """Get the default save path where to save the datacontainer to
        
        Returns
        -------
            String
                The filepath or None if the save path could not have been found
        """
        
        if (self.sample_datacontainer != None and 
            isinstance(self.sample_datacontainer, DataHandling.DataContainer.DataContainer)):
            return self.sample_datacontainer.filepath
        elif (self.background_datacontainer != None and 
            isinstance(self.background_datacontainer, DataHandling.DataContainer.DataContainer)):
            return self.sample_datacontainer.filepath
        elif (self.result_datacontainer != None and 
            isinstance(self.result_datacontainer, DataHandling.DataContainer.DataContainer)):
            return self.result_datacontainer.filepath
        else:
            return None
    
    def getSaveNameSuffix(self, datacontainer = None):
        """Get the suffix of the datacontainer path
        
        Parameters
        ----------
            datacontainer : DataContainer
                The datacontainer
        
        Returns
        -------
            String
                The file name suffix
        """
        
        suffix = set()
        for tool in reversed(self._tools):
            if isinstance(tool, View.ToolWizard.Tool.Tool):
                if isinstance(tool.save_suffix, str) and len(tool.save_suffix) > 0:
                    suffix.add(tool.save_suffix)
        
        if isinstance(datacontainer, DataHandling.DataContainer.DataContainer):
            suffix |= datacontainer.getAttributes()
        
        if len(suffix) > 0:
            suffix = "[" + ";".join(suffix) + "]"
        else:
            suffix = ""
        
        return "export" + suffix
    
    def getDataContainerIndex(self):
        """Get the index of the datacontainer in the current datacontainer collection
        in the Controller
        
        Returns
        -------
            int
                The datacontainer index
        """
        
        return self.page(self._input_index).getDataContainerIndex()
    
    def getAllowedDataContainerAxis(self):
        """Get the constants of all environment variables that are allowed for
        the selectboxes
        
        Returns
        -------
            list
                The environment variables
        """
        
        return (
            DataHandling.DataPoint.DataPoint.TIMESTAMP,
            DataHandling.DataContainer.DataContainer.MAGNETIZATION,
            DataHandling.DataContainer.DataContainer.TEMPERATURE,
#            DataHandling.DataContainer.DataContainer.HIGH_TEMPERATURE,
#            DataHandling.DataContainer.DataContainer.LOW_TEMPERATURE,
            DataHandling.DataContainer.DataContainer.FIELD,
#            DataHandling.DataContainer.DataContainer.HIGH_FIELD,
#            DataHandling.DataContainer.DataContainer.LOW_FIELD,
            DataHandling.DataContainer.DataContainer.DRIFT,
            DataHandling.DataContainer.DataContainer.SLOPE,
            DataHandling.DataContainer.DataContainer.SQUID_RANGE,
            DataHandling.DataContainer.DataContainer.FIXED_AMPLITUDE,
            DataHandling.DataContainer.DataContainer.FREE_AMPLITUDE
        )

    def validateCurrentPage(self):
        """Get whether the current page is valid or not. This will do the 
        page calculation, after this the pages validatePage() function will be
        called.
        
        Returns
        -------
            boolean
                Whether the page is valid or not
        """
        
        if self._performing_calculation:
            # if this is not here this will cause an infinit loop
            return True
        
        current_id = self.currentId()
        page = self.page(current_id)
        
        if hasattr(page, "beforeCalculation") and callable(page.beforeCalculation):
            page.beforeCalculation()
        
        calcs = []
        
        for tool in self._tools:
            if not isinstance(tool, View.ToolWizard.Tool.Tool):
                continue
            
            calculations = tool.getCalculationsFor(current_id)
            
            if isinstance(calculations, (list, tuple)) and len(calculations) > 0:
                text = [tool.calculating_text] * len(calculations)
                calcs += zip(calculations, text)
        
        if current_id in self._calculations:
            calcs += self._calculations[current_id]
                
        if len(calcs) > 0:
            self._initCalculations(calcs)
            
            return False
        else:
#            if self.nextId() == -1:
#                self.performClosingRoutine()
                
            return self._finishValidateCurrentPage()
    
    def _finishValidateCurrentPage(self):
        """Finish the page validation"""
        
        return self.currentPage().validatePage()
    
    def nextId(self, page_id = None):
        """Get the id of the next page
        
        Parameters
        ----------
            page_id : int
                The page to get the next page of
        
        Returns
        -------
            int
                The id of the next page
        """
        
        if page_id == None:
            next_id = super(ToolWizard, self).nextId()
        else:
            pages = self.pageIds()
            next_id = -1
            
            if page_id in pages:
                index = pages.index(page_id)
                
                if index + 1 < len(pages):
                    next_id = pages[index + 1]
                
        if next_id == self._output_index and self.output_mode > 0 and self.hide_output_page:
            return self.page(self._output_index).nextId()
        else:
            return next_id
    
    def error(self, error):
        """Show the given error in the error dialg.
        
        Parameters
        ----------
            error : Exception, Warning or String
                The error
        """
        
        self._error_count += 1
        
        m = 100
        if self._error_count == m:
            error = "There are more than {} errors, furhter errors will not be shown.".format(m)
        elif self._error_count > m:
            return
        
        error_text = str(error)
        
        if isinstance(error, (list, tuple)):
            for err in error:
                self.error(err)
            
            return
        elif isinstance(error, warnings.WarningMessage):
            error_text = "{} in {} in line {}".format(
                    error.message,
                    os.path.basename(error.filename),
                    error.lineno)
            
            if hasattr(error, "index") and my_utilities.is_numeric(error.index):
                error_text += " in datapoint #{}".format(error.index)
        elif isinstance(sys.exc_info(), (list, tuple)) and len(sys.exc_info()) > 0:
            # use slice for avoiding errors, throwing an exception will cause
            # an infinite loop
            exception_type = sys.exc_info()[0]
            traceback = sys.exc_info()[-1]
            
            if traceback != None:
                error_text += ", last exception ({}) in {} in line {}".format(
                        exception_type,
                         os.path.split(traceback.tb_frame.f_code.co_filename)[1],
                         traceback.tb_lineno)
        
        if error_text[-1] != ".":
            error_text += "."
        
        old_text = self._error_text.text()
        
        self._error_text.setText(("<b>Error:</b> " + 
                                  error_text[0].upper() + 
                                  error_text[1:] + 
                                 "<br />" + 
                                 old_text))
        self._error_text.adjustSize()
        
        if not self._error_dialog.isVisible():
            self._error_dialog.show()
    
    def _initCalculations(self, calculations):
        """Initialize the calculations. This will perform the given calculations,
        The calculations have to be a list of tuples, each tuple has to contain
        the handler function in the index 0, the index 1 has to contain the
        laoding text.
        
        Parameters
        ----------
            calculations : list of tuples
                The calculations
        """
        
        if len(calculations) > 0:
            self.setEnabledButtons(False)
            
            self._current_calculations = calculations
            self._current_calculation = -1
            self._performing_calculation = True
            self._error_count = 0
            
            self._performNextCalculation()
    
    def _performNextCalculation(self):
        """Performs the calculation. This will go through each calculation which
        have been stored by the _initCalculations() function.
        """
        
        self._current_calculation += 1
        
        if (isinstance(self._current_calculations, (list, tuple)) and 
            self._current_calculation >= 0 and
            self._current_calculation < len(self._current_calculations)):
            
            handler, calculating_text = self._current_calculations[self._current_calculation]
            
            self._current_calculation_worker = DataHandling.ToolWorker.ToolWorker(handler, self)
            self._current_calculation_thread = QtCore.QThread()
            self._current_calculation_worker.moveToThread(self._current_calculation_thread)
            
            self.view.showProgress(calculating_text, self._current_calculation_worker.stop)
            self._current_calculation_worker.error.connect(self.error)
            self._current_calculation_worker.warning.connect(self.error)
            
            self._current_calculation_thread.started.connect(self._current_calculation_worker.run)
            
            self._current_calculation_worker.finished.connect(self.view.updateProgressClose)
            self._current_calculation_worker.finished.connect(self._performNextCalculation)
            self._current_calculation_worker.finished.connect(self._current_calculation_thread.quit)
            self._current_calculation_thread.finished.connect(self._current_calculation_worker.deleteLater)
            
            self._current_calculation_thread.start()
        else:
            self._finishCalculations()
    
    def _finishCalculations(self):
        """Finishes the calculations, this will reset all the values and go to
        the next page or end the wizard"""
        
        if self._finishValidateCurrentPage():
            if self.nextId() == -1:
#                self.performClosingRoutine()
                self.accept()
            else:
                self.next()
            
        self.setEnabledButtons(True)
            
        self._performing_calculation = False
        self._current_calculation = -1
        self._current_calculations = None
            
        self.repaint()
    
    def performClosingRoutine(self, view = None):
        """Performs the closing routine. This will save all the files in the
        way defined by the OutputPage
        
        Parameters
        ----------
            view : MainWindow
                The View
        """
        
        if not isinstance(view, View.MainWindow.MainWindow):
            view = self.controller.view
        
        if (self.output_mode & ToolWizard.OUTPUT_MODE_EXPORT_RAW_MPMS > 0 and
            self.result_mpms_raw_file != None and 
            isinstance(self.result_mpms_raw_file, str)):
            
            self.result_datacontainer.exportMPMSRaw(self.result_mpms_raw_file)
        
        if (self.output_mode & ToolWizard.OUTPUT_MODE_EXPORT_DAT_MPMS > 0 and
            self.result_mpms_dat_file != None and 
            isinstance(self.result_mpms_dat_file, str)):
            
            self.result_datacontainer.exportMPMSDat(self.result_mpms_dat_file)
        
        if (self.output_mode & ToolWizard.OUTPUT_MODE_EXPORT_CSV > 0 and
            isinstance(self.result_csv_file, str) and
            isinstance(self.result_csv_file_mode, int) and
            isinstance(self.result_csv_file_columns, (list, tuple))):
            self.result_datacontainer.exportCSV(
                    self.result_csv_file, 
                    self.result_csv_file_columns,
                    self.result_csv_file_mode)
        
        if self.output_mode & ToolWizard.OUTPUT_MODE_SAVE_LIST > 0:
            if self.overwrite_filelist:
                index = self.getDataContainerIndex()
                
                self.controller.replaceDataContainer(index, self.result_datacontainer)
            else:
                self.controller.addDataContainer(self.result_datacontainer)
        
        if (self.output_mode & ToolWizard.OUTPUT_MODE_PLOT_WINDOW > 0 and 
            isinstance(self.result_canvas, View.PlotCanvas.PlotCanvas)):
            self.result_canvas.show()
            view.plotNewWindow(self.result_canvas)
    
    def getIdOfPage(self, page):
        """Get the id of the given page
        
        Parameters
        ----------
            page : QWizardPage
                The page
        
        Returns
        -------
            int
                The page id or -1 if it does not exist
        """
        
        ids = self.pageIds()
        
        for i in ids:
            if self.page(i) == page:
                return i
        
        return -1
    
    def setEnabledButtons(self, enabled):
        """Set wether **all** buttons in the wizard should be enabled or disabled
        
        Parameters
        ----------
            enabled : boolean
                Whether to enable the buttons or not
        """
        
        if self.testOption(QtWidgets.QWizard.HaveCustomButton1):
            self.button(QtWidgets.QWizard.CustomButton1).setEnabled(enabled)
            
        if self.testOption(QtWidgets.QWizard.HaveCustomButton2):
            self.button(QtWidgets.QWizard.CustomButton2).setEnabled(enabled)
            
        if self.testOption(QtWidgets.QWizard.HaveCustomButton3):
            self.button(QtWidgets.QWizard.CustomButton3).setEnabled(enabled)
        
        buttons = (
            QtWidgets.QWizard.BackButton,
            QtWidgets.QWizard.NextButton,
            QtWidgets.QWizard.CommitButton,
            QtWidgets.QWizard.FinishButton,
            QtWidgets.QWizard.CancelButton,
            QtWidgets.QWizard.HelpButton
        )
        
        for button in buttons:
            self.button(button).setEnabled(enabled)
 
    def changeSize(self, width=None, height=None):
        """Change the size of the wizard and center it on the screen
        Parameters
        ----------
            width : int or float, optional
                The new width or the default width if nothing given
            height : int or float, optional
                The new height or the default height if nothing given
        """
        
        if not isinstance(width, int) and not isinstance(width, float):
            width = self.default_size.width()
            
        if not isinstance(height, int) and not isinstance(height, float):
            height = self.default_size.height()
        
        # receive current geometry
        geometry = self.geometry()
        
        # detect deltas
#        dw = geometry.width() - width
#        dh = geometry.height() - height
        
        # set new size
        geometry.setWidth(width)
        geometry.setHeight(height)
        
        # center again (so the users position will be kept as good as possible),
        # increase/decrease height and width on both sides
#        geometry.moveTo( + dw / 2, geometry.top() + dh / 2)
        
        self.setGeometry(geometry)
    
    def register_float_field(self, field):
        """This method is for imitating the FormDialog defined in 
        matplotlib.backends.qt_editor.formlayout.FormDialog. The axes settings 
        dialog is the one used by matplotlib but it needs to have this function
        to run so this GraphWizard provides this function but it does nothing.
        Parameters
        ----------
            field : String
                The name of the filed
        """
        pass
    
    def update_buttons(self):
        """This method is for imitating the FormDialog defined in 
        matplotlib.backends.qt_editor.formlayout.FormDialog. The axes settings 
        dialog is the one used by matplotlib but it needs to have this function
        to run so this GraphWizard provides this function but it does nothing.
        """
        pass
    
    def apply(self):
        """This method is for imitating the FormDialog defined in 
        matplotlib.backends.qt_editor.formlayout.FormDialog. The axes settings 
        dialog is the one used by matplotlib but it needs to have this function
        to run so this GraphWizard provides this function but it does nothing.
        """
        pass
    
    def get(self):
        """This method is for imitating the FormDialog defined in 
        matplotlib.backends.qt_editor.formlayout.FormDialog. The axes settings 
        dialog is the one used by matplotlib but it needs to have this function
        to run so this GraphWizard provides this function but it does nothing.
        """
        pass
