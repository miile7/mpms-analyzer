# -*- coding: utf-8 -*-
"""
Created on Mon Dec 18 11:46:35 2017

@author: miile7
"""

import os
import matplotlib
from PyQt5 import QtWidgets, QtCore, QtGui
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import formlayout
import re
from matplotlib.backends.qt_editor.figureoptions import (cm, mcolors, LINESTYLES, 
                                                         DRAWSTYLES, MARKERS)
import formlayout

import View.MainWindow
import my_utilities

class PlotMenuFactory(NavigationToolbar):
    def __init__(self, canvas, parent = None):
        self.context_menu = QtWidgets.QMenu(parent)
        self.toolbar_widget = QtWidgets.QToolBar()
        
        super(PlotMenuFactory, self).__init__(canvas, self.toolbar_widget, False)
    
    def _init_toolbar(self):
        self.basedir = os.path.join(matplotlib.rcParams['datapath'], 'images')
        self.toolitems = list(self.toolitems)
        self.toolitems.append(('Data', 'Show the data', 'icon_data.svg', self._showData))
        
        # NavigationToolbar uses a tuple so keep the type just in case the type is checked
        # anywhere
        self.toolitems = tuple(self.toolitems)

        for text, tooltip_text, image_file, callback in self.toolitems:
            if text is None:
                self.context_menu.addSeparator()
                self.toolbar_widget.addSeparator()
            else:
                if "." in image_file:
                    icon = QtGui.QIcon(my_utilities.image(image_file))
                else:
                    icon = self._icon(image_file + '.png')
                
                if text == 'Subplots':
                    a = self.context_menu.addAction(self._icon("qt4_editor_options.png"),
                                       'Customize', self.edit_parameters)
                    a.setToolTip('Edit axis, curve and image parameters')
                elif callable(callback):
                    a = self.context_menu.addAction(icon, text, callback)
                    self._actions[callback] = a
                else:
                    a = self.context_menu.addAction(icon, text, getattr(self, callback))
                    self._actions[callback] = a
                
                self.toolbar_widget.addAction(a)
                
                if callback in ['zoom', 'pan']:
                    a.setCheckable(True)
                    
                if tooltip_text is not None:
                    a.setToolTip(tooltip_text)

        # self.buttons = {}

        # reference holder for subplots_adjust window
        # self.adj_window = None

        # Esthetic adjustments - we need to set these explicitly in PyQt5
        # otherwise the layout looks different - but we don't want to set it if
        # not using HiDPI icons otherwise they look worse than before.
        self.setIconSize(QtCore.QSize(24, 24))
        self.layout().setSpacing(12)
    
    def _showData(self):
        """The callback for the show data toolbar item in the toolbar and the context menu"""
        allaxes = self.canvas.figure.get_axes()
        
        self._tab_widget = QtWidgets.QTabWidget()
        layout = QtWidgets.QVBoxLayout()
        dialog = QtWidgets.QDialog(self.context_menu.parent())
        
        dialog.setWindowTitle("Plotted data")
        dialog.setWindowIcon(QtGui.QIcon(View.MainWindow.MainWindow.ICON))
        
        for axes in allaxes:
            for i, line in enumerate(axes.lines):
                name = line.get_label()
                if name == "" or name == None:
                    name = "plot {}".format(i)
                    
                if len(allaxes) > 1:
                    name += "[" + axes.get_title() + "]"
                
                x_name = axes.get_xlabel()
                if x_name == "" or x_name == None:
                    x_name = "x"
                    
                y_name = axes.get_ylabel()
                if y_name == "" or y_name == None:
                    y_name = "y"
                
                data_widget = QtWidgets.QTableWidget()
                data_widget.setColumnCount(2)
                data_widget.setHorizontalHeaderLabels([x_name, y_name])
                data_widget.itemSelectionChanged.connect(self._actionSelectionChange)
                
                data = line.get_xydata()
                
                for x, y in data:
                    i = data_widget.rowCount()
                    data_widget.insertRow(i)
                    
                    item = QtWidgets.QTableWidgetItem(str(x))
                    item.setFlags(item.flags() ^ QtCore.Qt.ItemIsEditable);
                    data_widget.setItem(i, 0, item)
                    
                    item = QtWidgets.QTableWidgetItem(str(y))
                    item.setFlags(item.flags() ^ QtCore.Qt.ItemIsEditable);
                    data_widget.setItem(i, 1, item)
                
                self._tab_widget.addTab(data_widget, name)
                
        layout.addWidget(self._tab_widget)
        
        buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok)
        self._copy_button = buttons.addButton("Copy selected data", QtWidgets.QDialogButtonBox.ActionRole)
        self._copy_button.clicked.connect(self._actionCopy)
        self._copy_button.setEnabled(False)
        buttons.accepted.connect(dialog.accept)
        
        layout.addWidget(buttons)
        
        dialog.setLayout(layout)
        
        result = dialog.exec()
       
    def _actionSelectionChange(self):
        """The action method for toggling the copy button"""
        
        sender = self.sender()
        
        if isinstance(sender, QtWidgets.QAbstractItemView) and hasattr(self, "_copy_button"):
            selection_model = sender.selectionModel()
            
            self._copy_button.setEnabled(selection_model.hasSelection())
     
    def _actionCopy(self):
        """The action method for the copy button"""
        
        if hasattr(self, "_tab_widget") and isinstance(self._tab_widget, QtWidgets.QTabWidget):
            self._actionTableCopy(self._tab_widget.currentWidget())
       
    def _actionTableCopy(self, table = None):
        """The action method for copying the table contents. If the table is not
        given the sender will be used instead
        
        Parameters
        ----------
            table : QAbstractItemView
                The table
        """
        
        if not isinstance(table, QtWidgets.QAbstractItemView):
            table = self.sender()
        
        if isinstance(table, QtWidgets.QAbstractItemView):
            model = table.model()
            selection_model = table.selectionModel()
            indices = selection_model.selectedIndexes()
            
            nl = "\n"
            nv = "\t"
            copy_text = ""
            previous = None
            for current in indices:
                
                data = str(model.data(current))
                
                copy_text += data
                
                if previous != None and current.row() == previous.row():
                    copy_text += nl
                else:
                    copy_text += nv
                
                previous = current
            
            cb = QtWidgets.QApplication.clipboard()
            cb.clear(mode=cb.Clipboard)
            cb.setText(copy_text, mode=cb.Clipboard)

    def edit_parameters(self):
        """The method for editing the appearance of the plot"""
        
        allaxes = self.canvas.figure.get_axes()
        if not allaxes:
            QtWidgets.QMessageBox.warning(
                self.parent, "Error", "There are no axes to edit.")
            return
        if len(allaxes) == 1:
            axes = allaxes[0]
        else:
            titles = []
            for axes in allaxes:
                name = (axes.get_title() or
                        " - ".join(filter(None, [axes.get_xlabel(),
                                                 axes.get_ylabel()])) or
                        "<anonymous {} (id: {:#x})>".format(
                            type(axes).__name__, id(axes)))
                titles.append(name)
                
            item, ok = self.selectAxes(titles)
            
            if ok:
                axes = allaxes[titles.index(str(item))]
            else:
                return

        self.figure_edit(axes, self)
    
    def selectAxes(self, titles):
        """Shows the select axes dialog
        Parameters
        ----------
            titles : list
                A list of the names of the axes
        """
        
        dialog = QtWidgets.QDialog()
        dialog.setWindowTitle("Select axes")
        dialog.setWindowIcon(QtGui.QIcon(View.MainWindow.MainWindow.ICON))
        
        layout = QtWidgets.QVBoxLayout()
        
        layout.addWidget(QtWidgets.QLabel("Select the axes to modify"))
        
        radios = []
        
        for title in titles:
            radio = QtWidgets.QRadioButton(title)
            radios.append(radio)
            layout.addWidget(radio)
        
        buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | 
                QtWidgets.QDialogButtonBox.Cancel)
        
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        
        layout.addWidget(buttons)
        
        dialog.setLayout(layout)
        
        result = dialog.exec()
        selected = None
        
        for radio in radios:
            if radio.isChecked():
                selected = radio.text()
        
        return selected, result
        
    def figure_edit(self, axes, parent = None):
        """Edit matplotlib figure options
        
        This is a very very slightly modified version of the 
        matplotlib.backends.qt_editor.figureoptions.figure_edit which shows the
        editing dialog. To use the same layout and to prevent coding the same
        thing again this is used again. 
        
        There is no chance to get the widget of the dialog because the dialog
        is created and executed before the function is finished so there is no
        other way than to copy the code.
        Parameters
        ----------
            axes : matplotlib.artist.Artist.axes
                The matplotlib axes instance of the axes to modify
            parent : QWidget, optional
                The parent widget
        Returns
        -------
            matplotlib.backends.qt_editor.formlayout.FormWidget
                The widget which holds the edit fields
            function
                The callback function which applies all the settings to the 
                axes
        """
        sep = (None, None)  # separator
    
        # Get / General
        xmin, xmax = axes.get_xlim()
        ymin, ymax = axes.get_ylim()
        general = [('Title', axes.get_title()),
                   sep,
                   (None, "<b>X-Axis</b>"),
                   ('Min', xmin), ('Max', xmax),
                   ('Label', axes.get_xlabel()),
                   ('Scale', [axes.get_xscale(), 'linear', 'log']),
                   sep,
                   (None, "<b>Y-Axis</b>"),
                   ('Min', ymin), ('Max', ymax),
                   ('Label', axes.get_ylabel()),
                   ('Scale', [axes.get_yscale(), 'linear', 'log']),
                   sep,
                   ('Show legend', True),
                   ('(Re-)Generate automatic legend', False),
                   ]
    
        # Save the unit data
        xconverter = axes.xaxis.converter
        yconverter = axes.yaxis.converter
        xunits = axes.xaxis.get_units()
        yunits = axes.yaxis.get_units()
    
        # Sorting for default labels (_lineXXX, _imageXXX).
        def cmp_key(label):
            match = re.match(r"(_line|_image)(\d+)", label)
            if match:
                return match.group(1), int(match.group(2))
            else:
                return label, 0
    
        # Get / Curves
        linedict = {}
        for line in axes.get_lines():
            label = line.get_label()
            if label == '_nolegend_':
                continue
            linedict[label] = line
        curves = []
    
        def prepare_data(d, init):
            """Prepare entry for FormLayout.
    
            `d` is a mapping of shorthands to style names (a single style may
            have multiple shorthands, in particular the shorthands `None`,
            `"None"`, `"none"` and `""` are synonyms); `init` is one shorthand
            of the initial style.
    
            This function returns an list suitable for initializing a
            FormLayout combobox, namely `[initial_name, (shorthand,
            style_name), (shorthand, style_name), ...]`.
            """
            # Drop duplicate shorthands from dict (by overwriting them during
            # the dict comprehension).
            name2short = {name: short for short, name in d.items()}
            # Convert back to {shorthand: name}.
            short2name = {short: name for name, short in name2short.items()}
            # Find the kept shorthand for the style specified by init.
            canonical_init = name2short[d[init]]
            # Sort by representation and prepend the initial value.
            return ([canonical_init] +
                    sorted(short2name.items(),
                           key=lambda short_and_name: short_and_name[1]))
    
        curvelabels = sorted(linedict, key=cmp_key)
        for label in curvelabels:
            line = linedict[label]
            color = mcolors.to_hex(
                mcolors.to_rgba(line.get_color(), line.get_alpha()),
                keep_alpha=True)
            ec = mcolors.to_hex(line.get_markeredgecolor(), keep_alpha=True)
            fc = mcolors.to_hex(line.get_markerfacecolor(), keep_alpha=True)
            curvedata = [
                ('Label', label),
                sep,
                (None, '<b>Line</b>'),
                ('Line style', prepare_data(LINESTYLES, line.get_linestyle())),
                ('Draw style', prepare_data(DRAWSTYLES, line.get_drawstyle())),
                ('Width', line.get_linewidth()),
                ('Color (RGBA)', color),
                sep,
                (None, '<b>Marker</b>'),
                ('Style', prepare_data(MARKERS, line.get_marker())),
                ('Size', line.get_markersize()),
                ('Face color (RGBA)', fc),
                ('Edge color (RGBA)', ec)]
            curves.append([curvedata, label, ""])
        # Is there a curve displayed?
        has_curve = bool(curves)
    
        # Get / Images
        imagedict = {}
        for image in axes.get_images():
            label = image.get_label()
            if label == '_nolegend_':
                continue
            imagedict[label] = image
        imagelabels = sorted(imagedict, key=cmp_key)
        images = []
        cmaps = [(cmap, name) for name, cmap in sorted(cm.cmap_d.items())]
        for label in imagelabels:
            image = imagedict[label]
            cmap = image.get_cmap()
            if cmap not in cm.cmap_d.values():
                cmaps = [(cmap, cmap.name)] + cmaps
            low, high = image.get_clim()
            imagedata = [
                ('Label', label),
                ('Colormap', [cmap.name] + cmaps),
                ('Min. value', low),
                ('Max. value', high)]
            images.append([imagedata, label, ""])
        # Is there an image displayed?
        has_image = bool(images)
    
        datalist = [(general, "Axes", "")]
        if curves:
            datalist.append((curves, "Curves", ""))
        if images:
            datalist.append((images, "Images", ""))
    
        def apply_callback(data, widgets):
            """This function will be called to apply changes"""
            general = data.pop(0)
            curves = data.pop(0) if has_curve else []
            images = data.pop(0) if has_image else []
            if data:
                raise ValueError("Unexpected field")
    
            # Set / General
            (title, xmin, xmax, xlabel, xscale, ymin, ymax, ylabel, yscale,
             show_legend, generate_legend) = general
    
            if axes.get_xscale() != xscale:
                axes.set_xscale(xscale)
            if axes.get_yscale() != yscale:
                axes.set_yscale(yscale)
    
            axes.set_title(title)
            axes.set_xlim(xmin, xmax)
            axes.set_xlabel(xlabel)
            axes.set_ylim(ymin, ymax)
            axes.set_ylabel(ylabel)
    
            # Restore the unit data
            axes.xaxis.converter = xconverter
            axes.yaxis.converter = yconverter
            axes.xaxis.set_units(xunits)
            axes.yaxis.set_units(yunits)
            axes.xaxis._update_axisinfo()
            axes.yaxis._update_axisinfo()
    
            # Set / Curves
            for index, curve in enumerate(curves):
                line = linedict[curvelabels[index]]
                (label, linestyle, drawstyle, linewidth, color, marker, markersize,
                 markerfacecolor, markeredgecolor) = curve
                line.set_label(label)
                line.set_linestyle(linestyle)
                line.set_drawstyle(drawstyle)
                line.set_linewidth(linewidth)
                rgba = mcolors.to_rgba(color)
                line.set_alpha(None)
                line.set_color(rgba)
                if marker is not 'none':
                    line.set_marker(marker)
                    line.set_markersize(markersize)
                    line.set_markerfacecolor(markerfacecolor)
                    line.set_markeredgecolor(markeredgecolor)
    
            # Set / Images
            for index, image_settings in enumerate(images):
                image = imagedict[imagelabels[index]]
                label, cmap, low, high = image_settings
                image.set_label(label)
                image.set_cmap(cm.get_cmap(cmap))
                image.set_clim(*sorted([low, high]))
            
            if axes.get_legend() != None:
                if show_legend:
                    axes.get_legend().set_visible(True)
                else:
                    axes.get_legend().set_visible(False)
    
            # re-generate legend, if checkbox is checked
            if generate_legend:
                draggable = None
                ncol = 1
                if axes.legend_ is not None:
                    old_legend = axes.get_legend()
                    draggable = old_legend._draggable is not None
                    ncol = old_legend._ncol
                new_legend = axes.legend(ncol=ncol)
                if new_legend:
                    new_legend.draggable(draggable)
    
            # Redraw
            figure = axes.get_figure()
            figure.canvas.draw()
        
        data = formlayout.fedit(datalist, 
                                title="Figure options", 
                                parent=parent,
                                icon=self._icon('qt4_editor_options.svg'),
                                apply=apply_callback)
        
        if data is not None:
            apply_callback(data, None)
        
        return datalist, apply_callback
        