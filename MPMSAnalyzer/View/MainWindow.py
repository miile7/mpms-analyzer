# -*- coding: utf-8 -*-
"""
Created on Wed Oct 17 09:25:35 2017

@author: miile7
"""

from PyQt5 import QtWidgets, QtCore, QtGui
import sys
import sip
import os

import Constants
import my_utilities
import View.PlotCanvas
import View.PlotWindow
import View.AboutDialog
import View.DataPointViewer
import View.PreferencesDialog
import View.DataContainerWidget
import DataHandling.DataContainer
import View.ToolWizard.ToolWizard
import View.ToolWizard.FormatDataTool
import View.ToolWizard.DataPointCutTool
import View.ToolWizard.BackgroundCreationTool
import View.ToolWizard.BackgroundSubtractionTool

class MainWindow(QtWidgets.QMainWindow):
    QT_INSTALL_PATHS = {
       'general': 'https://download.qt.io/archive/qt/5.6/5.6.2/',
       'windows': 'https://download.qt.io/archive/qt/5.6/5.6.2/qt-opensource-windows-x86-winrt-msvc2015-5.6.2.exe',
       'linux': 'https://download.qt.io/archive/qt/5.6/5.6.2/qt-opensource-linux-x64-5.6.2.run',
       'mac': 'https://download.qt.io/archive/qt/5.6/5.6.2/qt-opensource-mac-x64-clang-5.6.2.dmg'
    }
    ICON = my_utilities.image("icon_window_icon.png")
    
#    openedFile = QtCore.pyqtSignal(DataHandling.DataContainer.DataContainer)
    # this is more open, PyQt_PyObject is the C++ wrapper object for each python
    # object but setting the Signal to the DataContainer directly this does not
    # work for any reason, getting an error
    openedFile = QtCore.pyqtSignal('PyQt_PyObject')
    openFileFinished = QtCore.pyqtSignal(list)
    
    def __init__(self, controller, show_window = True, parent = None):
        """Initialize the Main window (View)
        Parameters
        ---------
            controller : Controller
                The controller which handles all the program routines
            show_window: boolean, False
                Whehter the window should be shown or not, default: True
            parent : QWidget, optional
                The parent
        """
        
        super(MainWindow, self).__init__(parent)
        
        # save controller
        self._controller = controller
        
        # the progress dialog and its parent
        self._progress_parent = self
        self._progress = None
        
        # quick open plot type, this can be H or T
        self._quick_open_plot_type = None
        
        # initialize UI
        self._initUI(show_window)
        
        # reading stored settings
        self.readSettings()
        
        # set open signal
        self._controller.openedDataContainer.connect(self.openedFile.emit)
        self.openedFile.connect(self.actionLogFileOpen)
        self.openedFile.connect(self.actionOpenFinished)
        self._open_data = None
        
        self.log("GUI ready")
    
    @property
    def controller(self):
        return self._controller
    
    @controller.setter
    def controller(self, value):
        return False
        
    def _initUI(self, show_window = True):
        """Setup the UI
        Parameters
        ---------
            show_window: boolean, False
                Whehter the window should be shown or not, default: True
        """
        
        # set the window dimensions, set the window into the center of the screen
        screen_object = QtWidgets.QDesktopWidget().screenGeometry(-1)
        w = 600
        h = 400
        
        x = (screen_object.width() - w) // 2
        y = (screen_object.height() - h) // 2
        
        self.setGeometry(x, y, w, h)
        
        # set title and icon
        self.setWindowTitle(Constants.NAME)
        self.setWindowIcon(QtGui.QIcon(MainWindow.ICON))
                
        # setting up console
        self._console = QtWidgets.QTextEdit()
        self._console.setReadOnly(True)
        
        date = QtCore.QDateTime.currentDateTime()
        self._console.append("<b>Starting log console, {0}</b><br />".format(date.toString()))
        
        # creating dockable pane for console
        self._console_pane = QtWidgets.QDockWidget("Console", self)
        self._console_pane.setWidget(self._console)
        self._console_pane.resize(QtCore.QSize(450, 300))
        
        # setting up files list
        file_list_layout = QtWidgets.QVBoxLayout()
        file_list_layout.addStretch(1)
        
        self._file_list = QtWidgets.QWidget()
        self._file_list.setLayout(file_list_layout)
        
        # creating scroll pane for list
        scroll_area = QtWidgets.QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(self._file_list)
        scroll_area.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        scroll_area.resize(QtCore.QSize(450, 500))
        
        # creating dockable pane for files
        self._files_pane = QtWidgets.QDockWidget("Files", self)
        self._files_pane.setWidget(scroll_area)
        self._files_pane.resize(QtCore.QSize(450, 600))
        
        # adding dock windows
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self._files_pane)
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self._console_pane)
        
        # create mdi area
        self._mdiArea = QtWidgets.QMdiArea(self)
        self._plot_window_count = 0
        
        # create main widget which is the splitter, add the mdi area and the
        # console to the splitter, add the splitter as central widget
        self.setCentralWidget(self._mdiArea)
        
        # initialize the menubar
        self._initMenubar()
        # initialize the statusbar
        self._initStatusbar()
        # initialize the toolbar
        self._initToolbar()
        
        # show window
        if show_window:
            self.showMaximized()
    
    def _initMenubar(self):
        """Initialize the menubar"""
        
        # create menubar
        menubar = self.menuBar()
        
        # create file menu
        file_menu = menubar.addMenu('File')
        
        open_menu = file_menu.addMenu('Open')
        
        # open graph as a new plot
        open_action_t = QtWidgets.QAction('Open M(T)', self)
        open_action_t.setShortcut('Ctrl+O')
        open_action_t.setProperty("measurement_variable", DataHandling.DataContainer.DataContainer.TEMPERATURE)
        open_action_t.setStatusTip('Open a file to load the M(T) measurement')
        open_action_t.setToolTip(open_action_t.statusTip())
        open_action_t.triggered.connect(self.actionOpen)
        
        open_action_h = QtWidgets.QAction('Open M(H)', self)
        open_action_h.setShortcut('Ctrl+O')
        open_action_h.setProperty("measurement_variable", DataHandling.DataContainer.DataContainer.FIELD)
        open_action_h.setStatusTip('Open a file to load the M(H) measurement')
        open_action_h.setToolTip(open_action_h.statusTip())
        open_action_h.triggered.connect(self.actionOpen)
        
        # quick M(T) open
        openQuickMT = QtWidgets.QAction('Quick open: M(T)', self)
        openQuickMT.setStatusTip('Open a file and plot it as an M(T) measurement')
        openQuickMT.setProperty("plot", DataHandling.DataContainer.DataContainer.TEMPERATURE)
        openQuickMT.triggered.connect(self.actionQuickOpen)
        
        # quick M(H) open
        openQuickMH = QtWidgets.QAction('Quick open: M(H)', self)
        openQuickMH.setStatusTip('Open a file and plot it as an M(H) measurement')
        openQuickMH.setProperty("plot", DataHandling.DataContainer.DataContainer.FIELD)
        openQuickMH.triggered.connect(self.actionQuickOpen)
        
        # add the menus to the open menu
        open_menu.addAction(open_action_t)
        open_menu.addAction(open_action_h)
        open_menu.addSeparator()
        open_menu.addAction(openQuickMT)
        open_menu.addAction(openQuickMH)
        
        # open settings
        openSettingsAct = QtWidgets.QAction('Settings', self)
        openSettingsAct.setShortcut('Ctrl+Alt+Shift+P')
        openSettingsAct.setStatusTip('Open Settings')
        openSettingsAct.triggered.connect(self.actionOpenSettings)
        
        # exit program
        exitAct = QtWidgets.QAction('Exit', self)
        exitAct.setShortcut('Ctrl+Q')
        exitAct.setStatusTip('Exit application')
        exitAct.triggered.connect(self.actionQuit)
        
        # add the items to the file menu
        file_menu.addSeparator()
        file_menu.addAction(openSettingsAct)
        file_menu.addSeparator()
        file_menu.addAction(exitAct)
        
        # create tools menu
        toolMenu = menubar.addMenu('Tools')
        
        # create all the tools
        tools = [
            View.ToolWizard.FormatDataTool.FormatDataTool(),
            View.ToolWizard.DataPointCutTool.DataPointCutTool(),
            View.ToolWizard.BackgroundCreationTool.BackgroundCreationTool(),
            View.ToolWizard.BackgroundSubtractionTool.BackgroundSubtractionTool()
        ]
        
        # create the menus
        for i, tool in enumerate(tools):
            toolMenuItem = tool.createAction(self, False)
            toolMenuItem.setProperty("tool", tool.getUniqueName())
            
            if isinstance(tool, View.ToolWizard.BackgroundCreationTool.BackgroundCreationTool):
                toolMenuItem.setProperty("output_mode", ("export", "plot"))
            else:
                toolMenuItem.setProperty("output_mode", "plot")
                
            toolMenuItem.triggered.connect(self.actionTool)
            
            toolMenu.addAction(toolMenuItem)
        
        # export menu is always included, just start the wizard
        toolMenuItem = QtWidgets.QAction("Export", self)
        toolMenuItem.setProperty("tool", "export")
        toolMenuItem.setProperty("output_mode", "export")
        toolMenuItem.setToolTip("Export data to an dat, raw or csv file")
        toolMenuItem.triggered.connect(self.actionTool)
        
        toolMenu.addAction(toolMenuItem)
        
        # create window menu
        windowMenu = menubar.addMenu('Windows')
        
        # cascading windows
        cascadingAct = QtWidgets.QAction('Cascacing windows', self)
        cascadingAct.setShortcut('Alt+C')
        cascadingAct.setStatusTip('Cascade the subwindows')
        cascadingAct.triggered.connect(self._mdiArea.cascadeSubWindows)
        
        # tile windows
        tileAct = QtWidgets.QAction('Tile windows', self)
        tileAct.setShortcut('Alt+T')
        tileAct.setStatusTip('Tile the subwindows')
        tileAct.triggered.connect(self._mdiArea.tileSubWindows)
        
        windowMenu.addAction(cascadingAct)
        windowMenu.addAction(tileAct)
        
        # create help menu
        helpMenu = menubar.addMenu('Help')
        
        # about the program menu
        infoAct = QtWidgets.QAction('About', self)
        infoAct.setShortcut('Ctrl+Alt+Shift+I')
        infoAct.setStatusTip('Get information about the program')
        infoAct.triggered.connect(self.actionInfo)
        
        # about qt
        infoQtAct = QtWidgets.QAction('About Qt', self)
        infoQtAct.setStatusTip('Get information about the Qt Framework version')
        infoQtAct.triggered.connect(lambda: QtWidgets.QMessageBox.aboutQt(self, "About Qt"))
        
        # add the items to the help
        helpMenu.addAction(infoAct)
        helpMenu.addAction(infoQtAct)
    
    def _initStatusbar(self):
        """Initialize the statusbar"""
        # initialize status bar
        self.statusBar()
        
    def _initToolbar(self):
        """Initialize the toolbar"""
        toolbar_icon_size = QtCore.QSize(32, 32)
        self.toolbar = self.addToolBar('Tools')
        
        open_menu = QtWidgets.QMenu(self)
        
        action = QtWidgets.QAction("M(T)", self)
        action.setProperty("measurement_variable", DataHandling.DataContainer.DataContainer.TEMPERATURE)
        action.setStatusTip("Plot a M(T) measurement")
        action.setToolTip(action.statusTip())
        action.triggered.connect(self.actionOpen)
        open_menu.addAction(action)
        
        action = QtWidgets.QAction("M(H)", self)
        action.setProperty("measurement_variable", DataHandling.DataContainer.DataContainer.FIELD)
        action.setStatusTip("Plot a M(H) measurement")
        action.setToolTip(action.statusTip())
        action.triggered.connect(self.actionOpen)
        open_menu.addAction(action)
        
        openbutton = QtWidgets.QToolButton(self)
        openbutton.setToolButtonStyle(QtCore.Qt.ToolButtonTextUnderIcon)
        openbutton.setText('Open')
        openbutton.setIcon(QtGui.QIcon(my_utilities.image('icon_open.svg')))
        openbutton.setIconSize(toolbar_icon_size)
        openbutton.setStatusTip('Open data file')
        openbutton.setMenu(open_menu)
        openbutton.clicked.connect(openbutton.showMenu)
        self.toolbar.addWidget(openbutton)
        
        graphbutton = QtWidgets.QToolButton(self)
        graphbutton.setToolButtonStyle(QtCore.Qt.ToolButtonTextUnderIcon)
        graphbutton.setText('Plot')
        graphbutton.setIcon(QtGui.QIcon(my_utilities.image('icon_graph.svg')))
        graphbutton.setIconSize(toolbar_icon_size)
        graphbutton.setStatusTip('Plot some data')
        graphbutton.clicked.connect(self.actionGraphs)
        self.toolbar.addWidget(graphbutton)
        
        self.toolbar.addSeparator()
        
        tools = [
            View.ToolWizard.FormatDataTool.FormatDataTool(),
            View.ToolWizard.DataPointCutTool.DataPointCutTool(),
            View.ToolWizard.BackgroundCreationTool.BackgroundCreationTool(),
            View.ToolWizard.BackgroundSubtractionTool.BackgroundSubtractionTool()
        ]
        
        # create the menus
        for i, tool in enumerate(tools):
            toolMenuItem = QtWidgets.QToolButton(self)
            tool_action = tool.createAction(self, True, True)
            toolMenuItem.setDefaultAction(tool_action)
            toolMenuItem.setProperty("tool", tool.getUniqueName())
            
            if isinstance(tool, View.ToolWizard.BackgroundCreationTool.BackgroundCreationTool):
                toolMenuItem.setProperty("output_mode", ("export", "plot"))
            else:
                toolMenuItem.setProperty("output_mode", "plot")
                
            toolMenuItem.clicked.connect(self.actionTool)
            toolMenuItem.setToolButtonStyle(QtCore.Qt.ToolButtonTextUnderIcon)
            toolMenuItem.setIconSize(toolbar_icon_size)
            
            toolMenuItem.setToolTip(tool_action.toolTip())
            toolMenuItem.setStatusTip(tool_action.statusTip())
            
            self.toolbar.addWidget(toolMenuItem)
        
        # export menu is always included, just start the wizard
        toolMenuItem = QtWidgets.QToolButton(self)
        toolMenuItem.setToolButtonStyle(QtCore.Qt.ToolButtonTextUnderIcon)
        toolMenuItem.setText('Export')
        toolMenuItem.setToolTip("Export data to an dat, raw or csv file")
        toolMenuItem.setStatusTip("Export data to an dat, raw or csv file")
        toolMenuItem.setIcon(QtGui.QIcon(my_utilities.image('icon_export.svg')))
        toolMenuItem.setIconSize(toolbar_icon_size)
        toolMenuItem.setProperty("tool", "export")
        toolMenuItem.setProperty("output_mode", "export")
        toolMenuItem.clicked.connect(self.actionTool)
        
        self.toolbar.addWidget(toolMenuItem)
        
        self.toolbar.addSeparator()
        
        exitbutton = QtWidgets.QToolButton(self)
        exitbutton.setToolButtonStyle(QtCore.Qt.ToolButtonTextUnderIcon)
        exitbutton.setText('Exit')
        exitbutton.setIcon(QtGui.QIcon(my_utilities.image('icon_exit.svg')))
        exitbutton.setIconSize(toolbar_icon_size)
        exitbutton.setStatusTip('Exit application')
        exitbutton.clicked.connect(self.actionQuit)
        self.toolbar.addWidget(exitbutton)
    
    def showOpenDialog(self, title = None, max_file_count = 1, parent = None):
        """Show a dialog for opening files. 
        
        This emits the openedFile Signal.
        
        Parameters
        ---------
            title : String, optional
                The title, if not given "Open file(s)" will be used
            max_file_count : int, optional
                The maximum count of files the user can open, if the parameter
                is not numeric (or < 0) unlimited files can be opened
            parent : QWidget
                The parent widget
                
        Returns
        -------
            boolean
                success
        """
        
        if title == None or not isinstance(title, str) or len(title) <= 0:
            title = "Open file"
        
        if parent == None and self.isVisible():
            parent = self
            
        dialog = QtWidgets.QFileDialog(parent)
        dialog.setWindowTitle(title)
        dialog.setNameFilter("MPMS raw files (*.rw.dat);;MPMS files (*.dat);;All files (*.*)")
        result = dialog.exec()
        
        if result:
            files = dialog.selectedFiles()
            
            if my_utilities.is_iterable(files):
                self.log("Trying to open {0} files".format(len(files)))
                
                fs = []
                for i, file in enumerate(files):
                    filepath = os.path.dirname(file)
                    filename = os.path.basename(file)
                    dat_filepath = os.path.join(filepath, 
                                             my_utilities.rreplace(str(filename), ".rw.dat", ".dat", 1))
                    
                    if not os.path.isfile(dat_filepath):
                        dat_filepath = self.showMissingDatfileDialog(file, dat_filepath, parent)
                    
                    if dat_filepath == False:
                        self.openFileAborted.emit()
                        self.log("Opening file(s) aborted.")
                        
                        return False
                    
                    fs.append((file, dat_filepath))
                        
                    if (my_utilities.is_numeric(max_file_count) and 
                        max_file_count > 0 and len(fs) >= max_file_count):
                        break
                
                self.openFiles(fs, parent)
            else:
                # this should never happen
                self.openFileAborted.emit()
                self._error("The file(s) cannot be received from the dialog")
    
    def showMissingDatfileDialog(self, file, dat_filepath, parent = None):
        """Displays a message dialog if the *.dat file can not be found.
        
        Parameters
        ----------
            file : String
                The absolute path of the raw file (*.rw.dat)
            dat_filepath : String
                The absolute path of the dat file (*.dat) which does not exist
            parent : QWidget
                The parent, if not given the MainWindow will be the parent
                
        Returns
        -------
            String, False or None
                The absolute path of the dat file to use or None if the dat file
                should not be loaded or False if the opening process should be 
                canceld
        """
        
        if parent == None and self.isVisible():
            parent = self
        
        # the message dialog
        dialog = QtWidgets.QMessageBox(parent)
        dialog.setText(("Could not find *.dat file for the given raw file '{}'. " + 
                    "<br /><br />If there is no *.dat file given the squid_range " + 
                    "will be read out of the *.rw.dat file which may cause <b>wrong " + 
                    "results!</b><br /><br />If you click on <i>Ignore</i> the squid " + 
                    "range will be read from the *.rw.dat file, if you click " + 
                    "<i>Select File</i> you can select another file which will be assumed " + 
                    "to be the *.dat file.").format(os.path.basename(file)))
        
        # some more details explaining the problem
        dialog.setDetailedText(("The automatically guessed *.dat file with the " + 
                               "filename '{}' does not exist.\n\nThe " + 
                               "*.dat file is used to detect the squid range. The " + 
                               "squid range is also written in the *.rw.dat file " + 
                               "but it is not always correct in the *.rw file. " + 
                               "Opening the file without the *.dat file may cause " + 
                               "wrong results. This means that they may be scaled " + 
                               "partly or completely with a factor of 10, 100, or 1000 " + 
                               "or the reciprocal of it.").format(dat_filepath))
        
        dialog.setIcon(QtWidgets.QMessageBox.Warning)
        
        # the buttons
        select_button = dialog.addButton("Select File", QtWidgets.QMessageBox.ActionRole)
        ignore_button = dialog.addButton(QtWidgets.QMessageBox.Ignore)
        dialog.addButton(QtWidgets.QMessageBox.Cancel)
        
        # start the dialog
        dialog.exec()
        
        # check which button has been clicked
        if dialog.clickedButton() == select_button:
            # show a file open dialog to select the dat file
            dialog = QtWidgets.QFileDialog(parent)
            dialog.setWindowTitle("Select *.dat file for {}".format(os.path.basename(file)))
            dialog.setNameFilter("MPMS files (*.dat);;MPMS raw files (*.rw.dat);;All files (*.*)")
            result = dialog.exec()
            
            # check if the result is valid, if it is return the dat file, if not
            # return *ignore* value
            if result:
                files = dialog.selectedFiles()
                if isinstance(files, (list, tuple)):
                    return files[0]
                elif isinstance(files, str):
                    return files
                else:
                    return None
            else:
                return None
        elif dialog.clickedButton() == ignore_button:
            # ignore the dat file
            return None
        else:
            # cancel the opening process
            return False
                
    def openFiles(self, files, parent = None):
        """Openes the file with the given filename. For further information
        about the data parameter have a look at the MainWindow.addFileToFileList
        function.
        
        This emits the openedFile Signal.
        
        Parameters
        ---------
            files : list of Strings
                The absolute path(s) of the file(s) to open
            parenet : QWiget
                The parent
        """
        
        self._controller.openFiles(files, parent)
    
    def addFileToFilelist(self, datacontainer):
        """Add the datacontainer to the file list for interacting with it.
        
        Parameters
        ----------
            datacontainer : DataContainer
                The data container which holds the data
        """
        
        if isinstance(datacontainer, DataHandling.DataContainer.DataContainer):
            # receive layout
            layout = self._file_list.layout()
            
            index = None
            index = layout.count() - 1
            
            # get last item which is a spacer with stretch=1
            spacer = layout.takeAt(index)
            
            self.replaceDataContainerWidget(datacontainer, index)
            
            if isinstance(spacer, QtWidgets.QSpacerItem):
                # this should always be true
                layout.addItem(spacer)
    
    def replaceDataContainerWidget(self, datacontainer, index = None):
        """Replace or add the given datacontainer to the internal list.
        
        Parameters
        ----------
            datacontainer : DataContainer
                The datacontainer to add
            index : int, optional
                The index to replace, None to append
        """
        
         # creating widget
        container_widget = View.DataContainerWidget.DataContainerWidget(
                datacontainer, 
                self, 
                self._controller)
        
        # setting widget
        if (my_utilities.is_numeric(index) and index >= 0 and
            index < self._file_list.layout().count()):
            self._file_list.layout().insertWidget(index, container_widget, 0)
        else:
            self._file_list.layout().addWidget(container_widget, 0)
    
    def removeDataContainerWidget(self, datacontainer_widget):
        """Removes the given datacontainer_widget from the layout. This will
        also remove the datacontainer because it is saved in the datacontainer
        widget only
        Parameters
        ----------
            datacontainer_widget : DataContainerWidget
                The datacontainer widget to remove
        Returns
        -------
            boolean
                success
        """
        
        layout = self._file_list.layout()
        
        if isinstance(datacontainer_widget, QtWidgets.QWidget):
            # get the name for the log 
            name = os.path.basename(datacontainer_widget.getDataContainer().filepath)
            
            # remove the widget in QT, garbage collector should remove it now
            layout.removeWidget(datacontainer_widget)
            datacontainer_widget.setParent(None)
            datacontainer_widget.deleteLater()
            
            # remove the C++ object just to make sure
            sip.delete(datacontainer_widget)
            
            # delete the python object just to make sure
            del datacontainer_widget
            
            self.log("Removed {} from the files list.".format(name))
            
            return True
        
        return False
    
    def plotNewWindow(self, plotdata):
        """Plot the given PlotData in a new subwindow
        Parameters
        ----------
            plotdata : PlotData or PlotCanvas
                The PlotData to plot
        """
        
        self._plot_window_count += 1
        
        # create a new sub window
        sub = View.PlotWindow.PlotWindow(self, self._plot_window_count, plotdata, 
                                         self._mdiArea)
        self._mdiArea.addSubWindow(sub)
        sub.show()
    
    def showDataPoints(self, datacontainer, index, plot_data_index):
        """Show the datapoints with the index1 and index2 of the given datacontainer
        Parameters
        ----------
            datacontainer : DataContainer
                The datacontainer which holds the data
            index : int
                The index of the one datapoint to show
        """
        
        sender = self.sender()
        
        if isinstance(sender, View.PlotCanvas.PlotCanvas):
            plot_data = sender.getPlotData(plot_data_index)
            
            if (isinstance(plot_data, DataHandling.PlotData.PlotData) and 
                isinstance(plot_data.indices_list, (list, tuple))):
                if isinstance(index, (list, tuple)):
                    i = []
                    for ind in index:
                        if ind >= 0 and ind <= len(plot_data.indices_list):
                            i.append(plot_data.indices_list[ind])
                    
                    index = i
                else:
                    index = plot_data.indices_list[index]
        
        datapoint_view = View.DataPointViewer.DataPointViewer(datacontainer, self, index)
        
        if isinstance(sender, View.PlotCanvas.PlotCanvas):
            datapoint_view.setDataContainerPlot(sender)
        
        datapoint_view.exec()
    
    def showErrorDialog(self, error_message, error_details = None, error_type = Constants.FATAL):
        """Show an error message to the uers with the given error_message and
        details if there are some
        Parameters
        ----------
            error_message : String
                The message of the error to display
            error_details : String, optional
                The details of the error as a String
        """
        
        error_dialog = QtWidgets.QMessageBox(self)
        error_dialog.setText(error_message)
        if error_type == Constants.NOTICE_ERROR:
            error_dialog.setWindowTitle("Notice")
            error_dialog.setIcon(QtWidgets.QMessageBox.Warning)
        else:
            error_dialog.setWindowTitle("Error")
            error_dialog.setIcon(QtWidgets.QMessageBox.Critical)
        error_dialog.show()
        error_dialog.resize(QtCore.QSize(600, 200))
        
        if isinstance(error_details, str) and len(error_details) > 0:
            error_dialog.setDetailedText(error_details)
        
    def setProgressParent(self, parent):
        """Sets the progress bar parent
        Parameters
        ----------
            parent : QtWidgets.QWidget
                The parent
        """
        
        if parent != None and parent.isVisible():
            self._progress_parent = parent
        elif self.isVisible():
            self._progress_parent = self
        else:
            self._progress_parent = None
        
        if isinstance(self._progress, QtWidgets.QWidget):
            self._progress.setParent(self._progress_parent)
        
    def showProgress(self, text, handler):
        """Show a progress dialog for loading the files, do not use this method!
        This is for the controller for file opening only
        Parameters
        ----------
            text : String
                The text which is displayed on the loader
            handler : function
                The callback function which is executed if the progress 
                bars abord button is hit
        """
        
        self._update_progress_aborted_msg_shown = None
        
        if isinstance(self._progress, QtWidgets.QDialog):
            self.updateProgressClose()
        
        self._progress = QtWidgets.QProgressDialog(str(text), "Abort", 0, 0, self._progress_parent, 
                                                   QtCore.Qt.WindowSystemMenuHint | 
                                                   QtCore.Qt.WindowTitleHint)
        self._progress.setWindowModality(QtCore.Qt.WindowModal)
        self._progress.setWindowTitle(Constants.NAME)
        self._progress.setWindowIcon(QtGui.QIcon(View.MainWindow.MainWindow.ICON))
        self._progress.canceled.connect(
            handler, type=QtCore.Qt.DirectConnection)
        self._progress.forceShow()
        
    def updateProgressStart(self, length, mode, file):
        """Updates the progress bar and initializes it.
        Parameters
        ----------
            length : int
                The amout of data that should be loaded (this is the maximum that
                the progress bar can reach)
            mode : String
                The mode, use "loading" for loading, use "fitting" for fitting
            file : String
                The filename of the currently loaded/fitted file
        """
        
        if isinstance(self._progress, QtWidgets.QWidget):
            self._progress.setMaximum(length)
            self._updateProgress(0, mode, file)
    
    def updateProgress(self, count, mode, file):
        """Updates the progress bar.
        Parameters
        ----------
            count : int
                The amout of data that already has been processed
            mode : String
                The mode, use "loading" for loading, use "fitting" for fitting
            file : String
                The filename of the currently loaded/fitted file
        """
        
        self._updateProgress(count, mode, file)
    
    def updateProgressEnd(self, success, mode, file):
        """Updates the progress bar.
        Parameters
        ----------
            success : boolean
                Whether the opening was successfully or not
            mode : String
                The mode, use "loading" for loading, use "fitting" for fitting
            file : String
                The filename of the currently loaded/fitted file
        """
        
        self._updateProgress(self._progress.maximum(), mode, file)
    
    def updateProgressClose(self):
        """Closes the progress bar"""
        if isinstance(self._progress, QtWidgets.QWidget):
            self._progress.close()
            self._progress.hide()
            self._progress.setParent(None)
            self._progress.deleteLater()
            self._progress = None
    
    def _updateProgress(self, value, mode, file):
        """Internal method for updating the progress bar.
        Parameters
        ----------
            value : int
                The amout of data that already has been processed
            mode : String
                The mode, use "loading" for loading, use "fitting" for fitting
            file : String
                The filename of the currently loaded/fitted file
        """
        
        if isinstance(self._progress, QtWidgets.QWidget):
            if not self._progress.wasCanceled():
                m = "Loading"
                if mode == "fitting":
                    m = "Fitting"
                    
                self._progress.setLabelText('{m} file {f}'.format(m=m, f=os.path.basename(file)))
                self._progress.setValue(value)
            elif self._update_progress_aborted_msg_shown == None:
                self._update_progress_aborted_msg_shown = True
                self.openFileAborted.emit()
                QtWidgets.QMessageBox.warning(
                    self, 'Load Files', 'Loading Aborted!')
    
    def actionQuit(self):
        """Perform the action for the Quit Menu Item"""
        sys.exit(0)
    
    def actionOpen(self):
        """Perform the action for the Open Menu Item"""
        
        self._open_data = "normal"
        
        sender = self.sender()
        if (isinstance(sender.property("measurement_variable"), str) and
            sender.property("measurement_variable") != ""):
            self._open_data = ("normal", sender.property("measurement_variable"))
        
        self.showOpenDialog()
    
    def actionOpenFinished(self, datacontainer):
        """Perform the action if a new file has been opened
        
        Parameters
        ----------
            datacontainer : DataContainer
                The opened datacontainer
        """
        
        open_data = self._open_data
        self._open_data = None
        
        if open_data == "normal":
            self.actionGraphs(datacontainer)
        elif (isinstance(open_data, (list, tuple)) and 
              len(open_data) >= 2):
            if open_data[0] == "quick":
                self.plotNewWindow(datacontainer.getPlotData(
                        open_data[1], 
                        DataHandling.DataContainer.DataContainer.MAGNETIZATION
                        ))
            elif open_data[0] == "normal":
                self.actionGraphs(datacontainer, open_data[1])
    
    def actionLogFileOpen(self, datacontainer):
        """Perform the action for logging an opened file
        
        Parameters
        ----------
            datacontainer : DataContainer
                The datacontainer that has been opened
        """
        
        self._controller.log("Opened file {0} ".format(os.path.basename(datacontainer.filepath)))
    
    def actionQuickOpen(self):
        """Perform the action for the quick open menu item"""
        
        sender = self.sender()
        
        if isinstance(sender, QtCore.QObject):
            plot = sender.property("plot")
            self._open_data = ("quick", plot)
            
        self.showOpenDialog()
    
    def actionOpenSettings(self):
        """Perform the action for the Settings Menu Item"""
        View.PreferencesDialog.PreferencesDialog.getPreferences(self)
    
    def actionInfo(self):
        """Perform the action for the Settings Menu Item"""
        dialog = View.AboutDialog.AboutDialog()
        dialog.exec()
    
    def actionGraphs(self, datacontainer = None, measurement_variable = None):
        """Perform the action for the graph wizzard (graph manager) to start
        
        Parameters
        -----------
            datacontainer : DataContainer, optional
                The datacontainer that should be used as the initial datacontainer
            measurement_variable : String, optional
                The measurement variable
        """
        
        self.actionTool("format_data", datacontainer, None, True, measurement_variable)
    
    def actionTool(self, tools = None, datacontainer = None, output_modes = None, hide_output_page = False, measurement_variable = None):
        """Perform the action for the tools. The sender object can have the 
        tool property which defines the tool to show. The additional tools parameter
        can specify more tools. The datacontainer defines an initialization 
        datacontainer which will be shown in the beginning.
        
        Parameters
        ----------
            tools : list, tuple, String or Tool, optional
                The id of the tool or the tool itself or a collection of those
            datacontainer : DataContainer, optional
                The datacontainer to show in the beginning
            output_modes : list, tuple, int or String, optional
                The possible output mode(s) to show in the ToolWizard
            hide_output_page : boolean, optional
                Whether to hide the output page or not
            measurement_variable : String, optional
                The measurement variable
        """
        
        sender = self.sender()
        
        # get the values of the parameters if there are some
        tool_objs = self._getTools(tools)
        visible_output_modes = self._getOutputMode(output_modes)
        
        print("MainWindow.actionTool(): hide_output_page: ", hide_output_page, ", tools: ", tools)
        
        # check the sender and if it has a tool/output mode
        if isinstance(sender, QtCore.QObject):
            tool = sender.property("tool")
            tool_objs = self._getTools(tool, tool_objs)
            
            output_mode = sender.property("output_mode")
            visible_output_modes = self._getOutputMode(output_mode, visible_output_modes)
        
        # create the tool wizard with the tools
        wizard = View.ToolWizard.ToolWizard.ToolWizard(self.controller, self, *tool_objs)
        
        # if there is no output mode use the default which is the plot mode
        if visible_output_modes == 0:
            visible_output_modes = (
                    View.ToolWizard.ToolWizard.ToolWizard.OUTPUT_MODE_PLOT_WINDOW | 
                    View.ToolWizard.ToolWizard.ToolWizard.OUTPUT_MODE_SAVE_LIST)
        
        # set the output mode
        wizard.visible_output_modes = visible_output_modes
        
        # always check the OUTPUT_MODE_PLOT_WINDOW and the OUTPUT_MODE_SAVE_LIST if
        # they are enabled, this is for a better user experience only so the user
        # saves two clicks
        if visible_output_modes & View.ToolWizard.ToolWizard.ToolWizard.OUTPUT_MODE_PLOT_WINDOW > 0:
            wizard.output_mode |= View.ToolWizard.ToolWizard.ToolWizard.OUTPUT_MODE_PLOT_WINDOW
        if visible_output_modes & View.ToolWizard.ToolWizard.ToolWizard.OUTPUT_MODE_SAVE_LIST > 0:
            wizard.output_mode |= View.ToolWizard.ToolWizard.ToolWizard.OUTPUT_MODE_SAVE_LIST
        
        # hide output page
        if hide_output_page == True:
            wizard.hide_output_page = True
        
        # set the measurement variable
        if isinstance(measurement_variable, str):
            wizard.measurement_variable = measurement_variable
        
        # set the init datacontainer if there is one
        if isinstance(datacontainer, DataHandling.DataContainer.DataContainer):
            wizard.setInitSampleDataContainer(datacontainer)
        
        # the result = wizard.exec() is very important, if the result is not
        # captured the QT event loop will continue running. This does not make
        # sense but it works
        result = wizard.exec()
        
        if result:
            wizard.performClosingRoutine()
        
        wizard.deleteLater()
        wizard = None
    
    def _getTools(self, tools, tool_objs = None):
        """Get the ToolWizard tools by the given output_mode tools. This can be 
        a list of the ids, the id or the tool object itself. The tool will be 
        added to the tool_objs if they exist.
        
        Parameters
        ----------
            tools : list, int or Tool
                The tool(s)
            tool_objs : list, optional
                The current tools to add the new tool to
        
        Returns
        -------
            list of Tool
                The tools
        """
        
        if isinstance(tool_objs, (list, tuple)):
            tool_objs = list(tool_objs)
        elif not isinstance(tool_objs, list):
            tool_objs = []
        
        if isinstance(tools, (list, tuple)):
            for tool in tools:
                tool_objs = self._getTools(tool, tool_objs)
        elif isinstance(tools, str):
            if tools == "background_creation":
                tool_objs.append(View.ToolWizard.BackgroundCreationTool.BackgroundCreationTool())
            elif tools == "background_subtraction":
                tool_objs.append(View.ToolWizard.BackgroundSubtractionTool.BackgroundSubtractionTool())
            elif tools == "datapoint_cut":
                tool_objs.append(View.ToolWizard.DataPointCutTool.DataPointCutTool())
            elif tools == "format_data":
                tool_objs.append(View.ToolWizard.FormatDataTool.FormatDataTool())
        elif isinstance(tools, View.ToolWizard.Tool.Tool):
            tool_objs.append(tools)
        
        return tool_objs
    
    def _getOutputMode(self, output_mode, visible_output_modes = 0):
        """Get the ToolWizard output mode by the given output_mode parameter.
        This can be a list of output modes, a String or the int constant. If the
        visible_output_modes parameter is given the current output mode will be
        added to this mode
        
        Parameters
        ----------
            output_mode : list, tuple, int or String
                The output mode
            visible_output_modes : int, optional
                The current output modes where to add the new ones
        
        Returns
        -------
            int
                The output mode constant
        """
        
        if isinstance(output_mode, (list, tuple)):
            for mode in output_mode:
                visible_output_modes = self._getOutputMode(mode, visible_output_modes)
        elif output_mode == "export":
            visible_output_modes |= (
                    View.ToolWizard.ToolWizard.ToolWizard.OUTPUT_MODE_EXPORT_RAW_MPMS |
                    View.ToolWizard.ToolWizard.ToolWizard.OUTPUT_MODE_EXPORT_DAT_MPMS | 
                    View.ToolWizard.ToolWizard.ToolWizard.OUTPUT_MODE_EXPORT_CSV)
        elif output_mode == "plot":
            visible_output_modes |= (
                    View.ToolWizard.ToolWizard.ToolWizard.OUTPUT_MODE_PLOT_WINDOW | 
                    View.ToolWizard.ToolWizard.ToolWizard.OUTPUT_MODE_SAVE_LIST)
        elif my_utilities.is_numeric(output_mode):
            visible_output_modes |= output_mode
        
        return visible_output_modes
        
    def closeEvent(self, event):
        """Perform the close event. This is overwriting the parents `QtWidgets.QWidget::closeEvent`
        method. This function will save all the sub window positions before exiting
        Parameters
        ----------
            event : QEvent
                The event
        """
        
        # saving window geometry
        self._saveWindowSettings(self)
        
        super(QtWidgets.QMainWindow, self).closeEvent(event)
    
    def _saveWindowSettings(self, widget):
        """Save the settings of the given widget. The given widget has to have an
        *unique* object name in order to be savend and restored properly
        Parameters
        ----------
            widget : QtWidgets.QWidget
                The widget to save the settings of
        """
        
        if isinstance(widget, QtWidgets.QWidget):
            # load the settings
            settings = QtCore.QSettings(Constants.COMPANY, Constants.NAME)
        
            name = widget.objectName()
            
            if isinstance(name, str) and len(name) > 0:
                # add the widget geometry and its state with the name as 
                # prefix
                settings.setValue(name + '/geometry', widget.saveGeometry())
                settings.setValue(name + '/windowState', widget.saveState())
            
            # store settings to internal storage
            del settings
     
    def readSettings(self):
        """Read the stored settings of all the windows"""
        # restoring window geometry
        self._restoreWindowSettings(self)
                
    def _restoreWindowSettings(self, widget):
        """Restore the settings of the given widget. The given widget has to have an
        *unique* object name in order to be saved and restored properly
        Parameters
        ----------
            widget : QtWidgets.QWidget
                The widget to restore the settings of
        """
        
        if isinstance(widget, QtWidgets.QWidget):
            # load the settings object
            settings = QtCore.QSettings(Constants.COMPANY, Constants.NAME)
            
            name = widget.objectName()
            
            if isinstance(name, str) and len(name) > 0:
                # check if the widget has saved data, if it has load it
                geometry = settings.value(name + "/geometry")
                if geometry != None:
                    widget.restoreGeometry(geometry)
                    
                windowState = settings.value(name + "/windowState")
                if windowState != None:
                    widget.restoreGeometry(windowState)
    
    def log(self, message, message_type = Constants.LOG_CONSOLE):
        """Log the given message depending on the type. The type has to be a
        bitmask, use the Constants.LOG_* constants. You can log the message to multiple
        targets by using `message_type = Constants.LOG_*type 1*  | Constants.LOG_*type 2*`
        Parameters
        ----------
            message : String
                The message to log
            message_type : int, optional
                The bitmask which describes the type where to add the message
        """
        message = str(message)
        
        if Constants.LOG_STATUS_BAR & message_type > 0:
            self.statusBar().showMessage(message)
        
        if Constants.LOG_CONSOLE & message_type > 0:
            self._console.append("> " + message)
            
        message = message.replace("\n", "<br />").replace("\r", "")
        
        if Constants.LOG_DEBUG & message_type > 0:
           self._console.append("> <i>Debug log: {0}</i>".format(message))
                         
    def _error(self, error_msg, error_type = Constants.NOTICE, error_details = None):
        """Throw the error with the given message. The error will be passed to
        the controller
        Parameters
        ----------
            error_msg : String
                The message of the error to display
            error_type : int, optional
                The type of the error
        """
        self._controller.error(error_msg, error_type, error_details)
    
    @staticmethod
    def createSeparatorLine(horizontal = True):
        """Create a vertical/horizontal separator line.
        Parameters
        ----------
            horizontal : boolean
                True for creating a horizontal line, false for creating a 
                vertical line
        Returns
        -------
            QtWidgets.QFrame
                The line
        """
        
        line = QtWidgets.QFrame();
        if horizontal:
            line.setFrameShape(QtWidgets.QFrame.HLine);
        else:
            line.setFrameShape(QtWidgets.QFrame.VLine);
            
        line.setFrameShadow(QtWidgets.QFrame.Sunken);
        
        return line
        
    @staticmethod    
    def showView(controller):
        """Create a new view with the given controller. This will also start the
        QApplication (if there is none), so this is in fact starting the gui
        Parameters
        ----------
            controller : Controller
                The controller of the view
        Returns
        -------
            View
                The view
        """
        app = QtWidgets.QApplication.instance()
        if not app or app == None:
            app = QtWidgets.QApplication(sys.argv)
        
        app.setWindowIcon(QtGui.QIcon(MainWindow.ICON))
        
        view = MainWindow(controller)
            
        sys.exit(app.exec_())
        
        return view