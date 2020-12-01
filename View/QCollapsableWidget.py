# -*- coding: utf-8 -*-
"""
Created on Wed Oct 25 12:09:57 2017

@author: Maximilian Seidler
"""

from PyQt5 import QtWidgets, QtCore, QtGui

import my_utilities

class QCollapsableWidget(QtWidgets.QFrame):
    BORDER_COLOR = "#828790"
    UP_ARROW  = "\u25B2"
    DOWN_ARROW= "\u25BC"
#    UP_ARROW  = "&#25B2;"
#    DOWN_ARROW= "&#25BC;"
    
    COLLAPSED = 0b01
    EXPANDED = 0b10
    BOTH = 0b11
    
    def __init__(self, content_widget, state = None, parent = None):
        """Initialize the collapsable widget. The content_widget will be
        the content, the state can either be `QCollapsableWidget.COLLAPSED`
        or `QCollapsableWidget.EXPANDED`. If nothing given the widget will be
        created in the expanded state
        Parameters
        ----------
            content_widget : QtWidgets.QWidget
                The widget to place in the center
            state : int, optional
                The constant which tells in which state to initialize the widget
            parent : QtWidgets.QWidget, optinal
                The parent
        """
        
        super(QCollapsableWidget, self).__init__(parent)
        
        # check the state if it is not set
        if state != QCollapsableWidget.COLLAPSED:
            state = QCollapsableWidget.EXPANDED
        
        # initialize the content widget
        self._content_widget = None
        
        # initialize the ui
        self._initUi(content_widget, state)
        
        self.setFrameStyle(QtWidgets.QFrame.Panel | QtWidgets.QFrame.StyledPanel)
    
    def _initUi(self, content_widget, state):
        # creating button
        self._expand_button = CustomPushButton(state)
        self._expand_button.clicked.connect(self.toggleState)
        
        # creating layout
        layout = QtWidgets.QVBoxLayout()
        layout.setSpacing(0)
        layout.addWidget(self._expand_button)
        layout.addItem(QtWidgets.QSpacerItem(1, 1, QtWidgets.QSizePolicy.Minimum, 
                                             QtWidgets.QSizePolicy.Fixed))
        
        # apply the layout
        self.setLayout(layout)
        
        # add the content widget
        if content_widget != None:
            self.setWidget(content_widget)
            
        layout.addItem(QtWidgets.QSpacerItem(1, 1, QtWidgets.QSizePolicy.Minimum, 
                                             QtWidgets.QSizePolicy.Expanding))
        
        # set the current state
        self.setState(state)
    
    def toggleState(self):
        """Toggle the state of the current widget. If the widget is collapsed
        it will be expanded after calling.
        """
        
        if self._state == QCollapsableWidget.EXPANDED:
            self.setState(QCollapsableWidget.COLLAPSED)
        else:
            self.setState(QCollapsableWidget.EXPANDED)
    
    def setState(self, state):
        """Set the state of the widget. Use the constants to set the state to
        either `QCollapsableWidget.COLLAPSED` or `QCollapsableWidget.EXPANDED`
        state
        Parameters
        ----------
            state : int
                The state to set the widget to
        """
        
        # check if the content exists
        if isinstance(self._content_widget, QtWidgets.QWidget):
            # toggle the state depending on the given constant
            if state & QCollapsableWidget.COLLAPSED:
                self._state = QCollapsableWidget.COLLAPSED
                self._content_widget.setVisible(False)
            elif state & QCollapsableWidget.EXPANDED:
                self._state = QCollapsableWidget.EXPANDED
                self._content_widget.setVisible(True)
            
            self._updateButtonText()

    def getState(self):
        return self._state
    
    def setWidget(self, widget):
        """Set the content widget which will be hidden or shown depending on 
        the widget state
        Parameters
        ----------
            widget : QtWidgets.QWidget
                The widget which is the content
        """
        
        # check if the widget is a QWidget
        if isinstance(widget, QtWidgets.QWidget):
            # remove the old widget if it exists
            if self._content_widget != None and isinstance(self._content_widget, QtWidgets.QWidget):
                self.layout().remove(self._content_widget)
                self._content_widget.setParent(None)
            
            # add the new widget
            self.layout().addWidget(widget)
            self._content_widget = widget
    
    def setButtonText(self, text, state = None):
        """Sets the text of the button for the corresponding state. If no state
        is given the `QCollapsableWidget.BOTH` will be used which sets the text
        for expanded and collapsed widget state
        Parameters
        ----------
            text : string
                The text of the button
            state : int, optional
                The state in which the button should hold the given text
        """
        
        self._expand_button.setText(text, state)
    
    def _updateButtonText(self):
        """Update the button text depending on the internal state"""
        self._expand_button.setState(self._state)


class CustomPushButton(QtWidgets.QPushButton):
    def __init__(self, state, *args):
        super(CustomPushButton, self).__init__(*args)
        
        self.setState(state)
        
        self._collapsed_text = "Expand"
        self._expanded_text = "Collapse"
    
    def setText(self, text, state = None):
        if my_utilities.is_numeric(state) and state & QCollapsableWidget.COLLAPSED:
            self._collapsed_text = text
        elif my_utilities.is_numeric(state) and state & QCollapsableWidget.EXPADED:
            self._expanded_text = text
        else:
            self._collapsed_text = text
            self._expanded_text = text
    
    def setState(self,  state): 
        self._state = state
        
    def paintEvent(self, paint_event):
        width = self.width()
        height = self.height()
        
        painter = QtGui.QPainter(self)
        render_hints = painter.renderHints()
        
        brush = QtGui.QBrush(QtGui.QColor(220, 220, 220))
        painter.setBrush(brush)
        
        painter.drawRect(QtCore.QRectF(0, 0, width-1, height-1))
        
        brush = QtGui.QBrush(QtGui.QColor(0, 0, 0))
        painter.setBrush(brush)
        painter.setRenderHints(QtGui.QPainter.Antialiasing | 
                QtGui.QPainter.SmoothPixmapTransform)
        
        polygon = QtGui.QPolygonF()
        
        tw = 10 # triangle width
        th = 10 # triangle height
        tm = 8 # triangle margin
        
        if self._state & QCollapsableWidget.COLLAPSED:
            polygon.append(QtCore.QPointF(tm, (height - th) / 2))
            polygon.append(QtCore.QPointF(tm + tw, (height - th) / 2))
            polygon.append(QtCore.QPointF(tm + tw/2, (height + th) / 2))
            
            text = self._collapsed_text
        else:
            polygon.append(QtCore.QPointF(tm, (height + th) / 2))
            polygon.append(QtCore.QPointF(tm + tw, (height + th) / 2))
            polygon.append(QtCore.QPointF(tm + tw/2, (height - th) / 2))
            
            text = self._expanded_text
            
        painter.drawPolygon(polygon)
        
        painter.setRenderHints(render_hints)
        
        tx = 2 * tm + tw # text x position
        
        font_metrics = painter.fontMetrics()
        text_width = font_metrics.width(text)
        dot_width = font_metrics.width("...")
        
        if text_width > width - tx:
            while font_metrics.width(text) > width - dot_width - tx:
                text = text[:-1]
            
            text += "..."
        
        painter.drawText(
                QtCore.QPoint(tx, (height + font_metrics.ascent()) / 2),
                text)
        
        painter.end()