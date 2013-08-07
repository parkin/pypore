#!/usr/bin/env python
# -*- coding: utf8 -*-

'''

This program is for finding events in files and displaying the results.
'''
import sys

from PyQt4 import QtGui, QtCore, Qt
import PyQt4.Qwt5 as Qwt

import matplotlib
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QTAgg as NavigationToolbar
from matplotlib.figure import Figure

from scipy import arange
import scipy.io as sio

# My stuff
from pypore import AnalyzeDataThread, PlotThread
from views import FileListItem, FilterListItem

# zoom picture? copied from BodeDemo
zoom_xpm = ['32 32 8 1',
            '# c #000000',
            'b c #c0c0c0',
            'a c #ffffff',
            'e c #585858',
            'd c #a0a0a4',
            'c c #0000ff',
            'f c #00ffff',
            '. c None',
            '..######################........',
            '.#a#baaaaaaaaaaaaaaaaaa#........',
            '#aa#baaaaaaaaaaaaaccaca#........',
            '####baaaaaaaaaaaaaaaaca####.....',
            '#bbbbaaaaaaaaaaaacccaaa#da#.....',
            '#aaaaaaaaaaaaaaaacccaca#da#.....',
            '#aaaaaaaaaaaaaaaaaccaca#da#.....',
            '#aaaaaaaaaabe###ebaaaaa#da#.....',
            '#aaaaaaaaa#########aaaa#da#.....',
            '#aaaaaaaa###dbbbb###aaa#da#.....',
            '#aaaaaaa###aaaaffb###aa#da#.....',
            '#aaaaaab##aaccaaafb##ba#da#.....',
            '#aaaaaae#daaccaccaad#ea#da#.....',
            '#aaaaaa##aaaaaaccaab##a#da#.....',
            '#aaaaaa##aacccaaaaab##a#da#.....',
            '#aaaaaa##aaccccaccab##a#da#.....',
            '#aaaaaae#daccccaccad#ea#da#.....',
            '#aaaaaab##aacccaaaa##da#da#.....',
            '#aaccacd###aaaaaaa###da#da#.....',
            '#aaaaacad###daaad#####a#da#.....',
            '#acccaaaad##########da##da#.....',
            '#acccacaaadde###edd#eda#da#.....',
            '#aaccacaaaabdddddbdd#eda#a#.....',
            '#aaaaaaaaaaaaaaaaaadd#eda##.....',
            '#aaaaaaaaaaaaaaaaaaadd#eda#.....',
            '#aaaaaaaccacaaaaaaaaadd#eda#....',
            '#aaaaaaaaaacaaaaaaaaaad##eda#...',
            '#aaaaaacccaaaaaaaaaaaaa#d#eda#..',
            '########################dd#eda#.',
            '...#dddddddddddddddddddddd##eda#',
            '...#aaaaaaaaaaaaaaaaaaaaaa#.####',
            '...########################..##.']

class MyApp(QtGui.QMainWindow):
    
    def __init__(self, parent=None):
        super(MyApp, self).__init__()
        
        self.events = [] # holds the events from the most recent analysis run
        
        self.threadPool = []
        
        self.setWindowTitle('Translocation Event Analysis')
        
        self.create_menu()
        self.create_main_frame()
        self.create_status_bar()
        
        self.__initZooming()
#         self.showMaximized()
        
    def __initZooming(self):
        """Initialize zooming
        """

        self.zoomer = Qwt.QwtPlotZoomer(Qwt.QwtPlot.xBottom,
                                        Qwt.QwtPlot.yLeft,
                                        Qwt.QwtPicker.DragSelection,
                                        Qwt.QwtPicker.AlwaysOff,
                                        self.plot.canvas())
        self.zoomer.setRubberBandPen(Qt.QPen(Qt.Qt.black))
        
        self.picker = Qwt.QwtPlotPicker(
            Qwt.QwtPlot.xBottom,
            Qwt.QwtPlot.yLeft,
            Qwt.QwtPicker.DragSelection,
#             Qwt.QwtPlotPicker.DragSelection,
            Qwt.QwtPlotPicker.CrossRubberBand,
            Qwt.QwtPicker.AlwaysOff,
            self.plot.canvas())
        self.picker.setRubberBandPen(Qt.QPen(QtCore.Qt.darkMagenta))
        self.picker.setTrackerPen(Qt.QPen(QtCore.Qt.cyan))
        self.picker.connect(self.picker, Qt.SIGNAL('selected(const QwtDoublePoint&)'), self.aSlot)
        
        self.zoomer_concatEvents = Qwt.QwtPlotZoomer(Qwt.QwtPlot.xBottom,
                                        Qwt.QwtPlot.yLeft,
                                        Qwt.QwtPicker.DragSelection,
                                        Qwt.QwtPicker.AlwaysOff,
                                        self.plot_concatevents.canvas())
        self.zoomer_concatEvents.setRubberBandPen(Qt.QPen(Qt.Qt.black))
        self.zoomer.setEnabled(False)
        
        self.zoomer_event = Qwt.QwtPlotZoomer(Qwt.QwtPlot.xBottom,
                                        Qwt.QwtPlot.yLeft,
                                        Qwt.QwtPicker.DragSelection,
                                        Qwt.QwtPicker.AlwaysOff,
                                        self.plot_event_zoomed.canvas())
        self.zoomer_event.setRubberBandPen(Qt.QPen(Qt.Qt.black))
        
        self.magnifier = Qwt.QwtPlotMagnifier(self.plot.canvas())
        self.magnifier.setEnabled(False)
    
    def aSlot(self, aQPointF):
        print 'aSlot gets:', aQPointF
        
    def zoom(self, on):
        self.zoomer.setEnabled(on)
        self.zoomer.zoom(0)
        self.magnifier.setEnabled(True)
        
    def open_files(self):
        '''
        Opens file dialog box, adds names of files to open to list
        '''

        fnames = QtGui.QFileDialog.getOpenFileNames(self, 'Open data file', '../data')
        if len(fnames) > 0:
            self.listWidget.clear()
        else:
            return
        areFilesOpened = False
        for w in fnames:
            areFilesOpened = True
            item = FileListItem(w)
            self.listWidget.addItem(item)
            
        if areFilesOpened:
            self.analyze_button.setEnabled(False)
            
    def open_event_database(self):
        '''
        Opens file dialog box, add names of event database files to open list
        '''
        fnames = QtGui.QFileDialog.getOpenFileNames(self, 'Open event database', '../data', '*.mat')
        if len(fnames) > 0:
            self.listEventWidget.clear()
        else:
            return
        areFilesOpened = False
        for w in fnames:
            areFilesOpened = True
            item = FileListItem(w)
            self.listEventWidget.addItem(item)
            
        if areFilesOpened:
            self.btnAddFilter.setEnabled(False)
            
    def _on_event_file_selection_changed(self):
        self.btnAddFilter.setEnabled(True)
            
    def _on_file_item_selection_changed(self):
        self.analyze_button.setEnabled(True)
        
    def _on_file_item_doubleclick(self, item):
        '''
        Called when filter_parameter file list item is double clicked.
        Starts the plotting thread, which opens the file, parses data, then passes to plotData
        '''
        # adding by emitting signal in different thread
        self.status_text.setText('Plotting...')
        self.threadPool.append(PlotThread(self.plot, filename=str(item.getFileName())))
        self.connect(self.threadPool[len(self.threadPool) - 1], QtCore.SIGNAL('plotData(PyQt_PyObject)'), self._on_file_item_doubleclick_callback)
        self.threadPool[len(self.threadPool) - 1].start()
        
    def _on_file_item_doubleclick_callback(self, results):
        if 'plot_options' in results:
            self.plotData(results['plot_options'])
        if 'status_text' in results:
            self.status_text.setText(results['status_text'])
            
    def _create_event_finding_options(self):
        scrollArea = QtGui.QScrollArea()
        scrollArea.setWidgetResizable(True)
        
        # Create filter_parameter list for files want to analyze
        self.listWidget = QtGui.QListWidget()
        self.listWidget.itemSelectionChanged.connect(self._on_file_item_selection_changed)
        self.listWidget.itemDoubleClicked.connect(self._on_file_item_doubleclick)
        self.listWidget.setMaximumHeight(100)
        
        # Other GUI controls
        # 
        self.analyze_button = QtGui.QPushButton("&Find Events")
        self.connect(self.analyze_button, QtCore.SIGNAL('clicked()'), self.on_analyze)
        self.analyze_button.setEnabled(False)
        
        self.stop_analyze_button = QtGui.QPushButton("&Stop")
        self.connect(self.stop_analyze_button, QtCore.SIGNAL('clicked()'), self.on_analyze_stop)
        self.stop_analyze_button.setEnabled(False)
        
        # Analysis options
        self.min_event_length_edit = QtGui.QLineEdit()
        self.min_event_length_edit.setText('10.0')
        self.min_event_length_edit.setValidator(QtGui.QDoubleValidator(0, 1e12, 5))
        self.max_event_length_edit = QtGui.QLineEdit()
        self.max_event_length_edit.setText('1000.0')
        self.max_event_length_edit.setValidator(QtGui.QDoubleValidator(0, 1e12, 5))
        fixed_analysis_options = QtGui.QFormLayout()
        fixed_analysis_options.addRow('Data Files:', self.listWidget)
        fixed_analysis_options.addRow('Min Event Length [us]:', self.min_event_length_edit)
        fixed_analysis_options.addRow('Max Event Length [us]:', self.max_event_length_edit)
        
        # Baseline options
        baseline_options = QtGui.QStackedLayout()
        self.baseline_type_combo = QtGui.QComboBox()
        self.baseline_type_combo.addItems(('Adaptive', 'Fixed'))
        self.baseline_type_combo.activated.connect(baseline_options.setCurrentIndex)
        
        adaptive_options_layout = QtGui.QFormLayout()
        self.filter_parameter_edit = QtGui.QLineEdit()
        self.filter_parameter_edit.setValidator(QtGui.QDoubleValidator(0, 10, 5))
        self.filter_parameter_edit.setText('0.93') 
        adaptive_options_layout.addRow('Filter Parameter \'a\':', self.filter_parameter_edit)
        # need to cast to widget to add to QStackedLayout
        adaptive_options_widget = QtGui.QWidget()
        adaptive_options_widget.setLayout(adaptive_options_layout)
        
        fixed_options_layout = QtGui.QFormLayout()
        self.baseline_current_edit = QtGui.QLineEdit()
        self.baseline_current_edit.setValidator(QtGui.QDoubleValidator(-9999, 9999, 9))
        self.baseline_current_edit.setText('0.0')
        fixed_options_layout.addRow('Baseline Current:', self.baseline_current_edit)
        fixed_options_widget = QtGui.QWidget()
        fixed_options_widget.setLayout(fixed_options_layout)
        
        baseline_options.addWidget(adaptive_options_widget)
        baseline_options.addWidget(fixed_options_widget)
        
        
        baseline_form = QtGui.QFormLayout()
        baseline_form.addRow('Baseline Type:', self.baseline_type_combo)
        
        # Threshold options
        threshold_options = QtGui.QStackedLayout()
        self.threshold_type_combo = QtGui.QComboBox()
        self.threshold_type_combo.addItem('Noise Based')
        self.threshold_type_combo.addItem('Absolute Change')
        self.threshold_type_combo.addItem('Percent Change')
        self.threshold_type_combo.activated.connect(threshold_options.setCurrentIndex)
        
        threshold_form = QtGui.QFormLayout()
        self.threshold_direction_combo = QtGui.QComboBox()
        self.threshold_direction_combo.addItems(('Both', 'Positive', 'Negative'))
        threshold_form.addRow('Threshold Direction:', self.threshold_direction_combo)
        threshold_form.addRow('Threshold Type:', self.threshold_type_combo)
        
        noise_based_options_layout = QtGui.QFormLayout()
        self.threshold_stdev_start = QtGui.QLineEdit()
        self.threshold_stdev_start.setValidator(QtGui.QDoubleValidator(-9999, 9999, 4))
        self.threshold_stdev_start.setText('5.0')
        noise_based_options_layout.addRow('Start StdDev:', self.threshold_stdev_start)
        self.threshold_stdev_end = QtGui.QLineEdit()
        self.threshold_stdev_end.setValidator(QtGui.QDoubleValidator(-9999, 9999, 4))
        self.threshold_stdev_end.setText('1.0')
        noise_based_options_layout.addRow('End StdDev:', self.threshold_stdev_end)
        
        absolute_drop_options_layout = QtGui.QFormLayout()
        self.absolute_change_start_edit = QtGui.QLineEdit()
        self.absolute_change_start_edit.setValidator(QtGui.QDoubleValidator(-9999, 9999, 9))
        self.absolute_change_start_edit.setText('0.1')
        absolute_drop_options_layout.addRow('Absolute Change Start [uA]:', self.absolute_change_start_edit)
        self.absolute_change_end_edit = QtGui.QLineEdit()
        self.absolute_change_end_edit.setValidator(QtGui.QDoubleValidator(-9999, 9999, 9))
        self.absolute_change_end_edit.setText('0.0')
        absolute_drop_options_layout.addRow('Absolute Change End [uA]:', self.absolute_change_end_edit)
        
        percentage_change_options_layout = QtGui.QFormLayout()
        self.percentage_change_start_edit = QtGui.QLineEdit()
        self.percentage_change_start_edit.setValidator(QtGui.QDoubleValidator(0, 9999, 5))
        self.percentage_change_start_edit.setText('10.0')
        percentage_change_options_layout.addRow('Percent Change Start:', self.percentage_change_start_edit)
        self.percentage_change_end_edit = QtGui.QLineEdit()
        self.percentage_change_end_edit.setValidator(QtGui.QDoubleValidator(0, 9999, 5))
        self.percentage_change_end_edit.setText('0.0')
        percentage_change_options_layout.addRow('Percent Change End:', self.percentage_change_end_edit)
        
        noise_based_options = QtGui.QWidget()
        noise_based_options.setLayout(noise_based_options_layout)
        
        absolute_drop_options = QtGui.QWidget()
        absolute_drop_options.setLayout(absolute_drop_options_layout)
        
        percentage_change_options_widget = QtGui.QWidget()
        percentage_change_options_widget.setLayout(percentage_change_options_layout)
        
        threshold_options.addWidget(noise_based_options)
        threshold_options.addWidget(absolute_drop_options)
        threshold_options.addWidget(percentage_change_options_widget)
        
        hbox = QtGui.QHBoxLayout()
        
        for w in [  self.analyze_button, self.stop_analyze_button]:
            hbox.addWidget(w)
            hbox.setAlignment(w, QtCore.Qt.AlignVCenter)
        
        
        # Left vertical layout with settings
        vbox_left = QtGui.QVBoxLayout()
        vbox_left.addLayout(fixed_analysis_options)
        vbox_left.addLayout(baseline_form)
        vbox_left.addLayout(baseline_options)
        vbox_left.addLayout(threshold_form)
        vbox_left.addLayout(threshold_options)
        vbox_left.addLayout(hbox)
        
        vbox_left_widget = QtGui.QWidget()
        vbox_left_widget.setLayout(vbox_left)
        
        scrollArea.setWidget(vbox_left_widget)
        
        return scrollArea
    
    def _create_event_analysis_options(self):
        scrollArea = QtGui.QScrollArea()
        scrollArea.setWidgetResizable(True)
        
        # Create filter_parameter list for files want to analyze
        self.listEventWidget = QtGui.QListWidget()
#         self.listEventWidget.itemSelectionChanged.connect(self._on_file_item_selection_changed)
#         self.listEventWidget.itemDoubleClicked.connect(self._on_file_item_doubleclick)
        self.listEventWidget.setMaximumHeight(100)
        self.listEventWidget.itemSelectionChanged.connect(self._on_event_file_selection_changed)
        self.listEventWidget.setSelectionMode(Qt.QAbstractItemView.ExtendedSelection)
        
        files_options = QtGui.QFormLayout()
        files_options.addRow('Event Databases:', self.listEventWidget)
        
        ## Color Picker
        self.event_color = QtGui.QColor('blue')
        pickColorBtn = QtGui.QPushButton()
        pickColorBtn.setText('Choose a Color')
        pickColorBtn.clicked.connect(self.colorPickerBtnClicked)
        
        self.frm = QtGui.QFrame()
        self.frm.setStyleSheet("QWidget { background-color: %s }" 
            % self.event_color.name())
        self.frm.setMinimumSize(15, 15)
        self.frm.setMaximumSize(30, 30)
        
        files_options.addRow(pickColorBtn, self.frm)
        
        ## List of filters created
        self.btnAddFilter = QtGui.QPushButton('Add selections as filter')
        self.btnAddFilter.clicked.connect(self.addFilterClicked)
        self.btnAddFilter.setEnabled(False)
        formFilter = QtGui.QFormLayout()
        formFilter.addRow('Filters:', self.btnAddFilter)
        self.listFilterWidget = QtGui.QListWidget()
        vbox = QtGui.QVBoxLayout()
        vbox.addLayout(formFilter)
        vbox.addWidget(self.listFilterWidget)
        btnRemoveFilter = QtGui.QPushButton('Remove selected filter')
        vbox.addWidget(btnRemoveFilter)
        
        vbox_left = QtGui.QVBoxLayout()
        vbox_left.addLayout(files_options)
        vbox_left.addLayout(vbox)
        
        vbox_left_widget = QtGui.QWidget()
        vbox_left_widget.setLayout(vbox_left)
        
        scrollArea.setWidget(vbox_left_widget)
        
        return scrollArea
    
    def addFilterClicked(self):
        items = self.listEventWidget.selectedItems()
        if items == None or len(items) < 1:
            return
        
        params = self._getCurrentEventAnalysisParams()
        
        filenames = []
        
        for item in items:
            filenames.append(item.getFileName())
        
        item = FilterListItem(filenames, params)
        self.listFilterWidget.addItem(item)
        
        self.plotEventDatabaseAnalyses(filenames, params)
        
    def _getCurrentEventAnalysisParams(self):
        params = {}
        params['color'] = self.event_color
        return params
    
    def colorPickerBtnClicked(self):
        col = QtGui.QColorDialog.getColor(initial=self.event_color)
        
        if col.isValid():
            self.event_color = col
            self.frm.setStyleSheet("QWidget { background-color: %s }"
                % col.name())
        
    def _create_left_side(self):
        event_finding_options = self._create_event_finding_options()
        event_analysis_options = self._create_event_analysis_options()
        
        tab_widget = QtGui.QTabWidget()
        tab_widget.addTab(event_finding_options, "Event Finding")
        tab_widget.addTab(event_analysis_options, "Event Analysis")
        
        return tab_widget
        
    def _create_eventfinder_plots_widget(self):
        # Create Qwt plot
        self.plot = Qwt.QwtPlot(self)
        self.plot.setCanvasBackground(QtCore.Qt.white)
        self.plot.setMinimumSize(400, 200)
        self.plot.setAxisTitle(Qwt.QwtPlot.xBottom, 'Time')
        self.plot.setAxisTitle(Qwt.QwtPlot.yLeft, 'Current')
        self.plot.setTitle('Current Trace')
        
        # Zoom button for plot
        toolBar = QtGui.QToolBar(self)
        self.addToolBar(toolBar)
        
        btnZoom = QtGui.QToolButton(toolBar)
        btnZoom.setText("Zoom")
        btnZoom.setIcon(QtGui.QIcon(QtGui.QPixmap(zoom_xpm)))
        btnZoom.setCheckable(True)
        btnZoom.setToolButtonStyle(QtCore.Qt.ToolButtonTextUnderIcon)
        toolBar.addWidget(btnZoom)
        self.connect(btnZoom,
                     QtCore.SIGNAL('toggled(bool)'),
                     self.zoom)
        
        # Create Qwt plot for concatenated events
        self.plot_concatevents = Qwt.QwtPlot(self)
        self.plot_concatevents.setCanvasBackground(QtCore.Qt.white)
        self.plot_concatevents.setMinimumSize(400, 200)
        self.plot_concatevents.setAxisTitle(Qwt.QwtPlot.xBottom, 'Time')
        self.plot_concatevents.setAxisTitle(Qwt.QwtPlot.yLeft, 'Current')
        self.plot_concatevents.setTitle('Concatenated Events')
        
        # Qwt plot for each event found
        self.plot_event_zoomed = Qwt.QwtPlot(self)
        self.plot_event_zoomed.setCanvasBackground(QtCore.Qt.white)
        self.plot_event_zoomed.setAxisTitle(Qwt.QwtPlot.xBottom, 'Time')
        self.plot_event_zoomed.setAxisTitle(Qwt.QwtPlot.yLeft, 'Current')
        self.plot_event_zoomed.setMinimumSize(400, 200)
        self.plot_event_zoomed.setTitle('Single Event')
        
        eventSelectToolbar = QtGui.QToolBar(self)
        self.addToolBar(eventSelectToolbar)
        
        btnPrevious = QtGui.QPushButton(eventSelectToolbar)
        btnPrevious.setText("Previous")
        btnPrevious.clicked.connect(self.previousClicked)
        eventSelectToolbar.addWidget(btnPrevious)
        
        self.eventDisplayedEdit = QtGui.QLineEdit()
        self.eventDisplayedEdit.setText('0')
        self.eventDisplayedEdit.setMaxLength(int(len(self.events)/10)+1)
        self.eventDisplayedEdit.setValidator(QtGui.QIntValidator(0,len(self.events)))
        self.eventDisplayedEdit.textChanged.connect(self._eventDisplayEditOnChange)
        eventSelectToolbar.addWidget(self.eventDisplayedEdit)
        
        self.eventCountText = QtGui.QLabel()
        self.eventCountText.setText('/' + str(len(self.events)))
        eventSelectToolbar.addWidget(self.eventCountText)
        
        btnNext = QtGui.QPushButton(eventSelectToolbar)
        btnNext.setText("Next")
        btnNext.clicked.connect(self.nextClicked)
        eventSelectToolbar.addWidget(btnNext)
        
        singleEventDisplayLayout = QtGui.QVBoxLayout()
        singleEventDisplayLayout.addWidget(self.plot_event_zoomed)
        singleEventDisplayLayout.addWidget(eventSelectToolbar)
        
        singleEventDisplayWidet = QtGui.QWidget() # widget container for layout
        singleEventDisplayWidet.setLayout(singleEventDisplayLayout)
        
        eventfinderplots_layout = QtGui.QVBoxLayout()
        eventfinderplots_layout.addWidget(self.plot)
        eventfinderplots_layout.addWidget(toolBar)
        eventfinderplots_layout.addWidget(self.plot_concatevents)
        eventfinderplots_layout.addWidget(singleEventDisplayWidet)
        
        eventfinderplots_widget = QtGui.QWidget()
        eventfinderplots_widget.setLayout(eventfinderplots_layout)
        
        return eventfinderplots_widget
    
    def _create_eventanalysis_plot_widget(self):
        # Tab widget for event stuff
        
#         self.tab_widget = QtGui.QTabWidget()
#         self.tab_widget.setMinimumSize(450, 250)
        
        # Filter and Histogram tab.  Use matplotlib cuz can't figure out pyqwt histogram
        self.fig = Figure()
        self.canvas = FigureCanvas(self.fig)
#         self.canvas.setParent(self.tab_widget)
        self.axes = self.fig.add_subplot(221)
        self.axes2 = self.fig.add_subplot(222)
        self.axes3 = self.fig.add_subplot(223)
        self.axes4 = self.fig.add_subplot(224)
        
        self.canvas.setMinimumSize(500, 400)
        
        return self.canvas
        
    
    def _create_right_side(self):
        '''
        Returns a widget holding all of the plots, stuff on right side
        of gui.
        '''
        # Put everything in filter_parameter scroll area
        scrollArea = QtGui.QScrollArea()
        scrollArea.setWidgetResizable(True)
        
        event_finding_widget = self._create_eventfinder_plots_widget()
        
        event_analysis_widget = self._create_eventanalysis_plot_widget()
        
        
        # Right vertical layout with plots and stuff
        vbox_right = QtGui.QVBoxLayout()
        vbox_right.addWidget(event_finding_widget)
        vbox_right.addWidget(event_analysis_widget)
        
        vbox_right_widget = QtGui.QWidget()
        vbox_right_widget.setLayout(vbox_right)
        
        scrollArea.setWidget(vbox_right_widget)
        
        return scrollArea
        
    def create_main_frame(self):
        '''
        Initializes the main gui frame.
        '''
        left_side = self._create_left_side()
        right_side = self._create_right_side()
        

        # Layout holding everything        
        main_frame = QtGui.QSplitter() # Splitter allows for drag to resize between children
        main_frame.addWidget(left_side)
        main_frame.addWidget(right_side)
        
        self.setCentralWidget(main_frame)
        
    def _eventDisplayEditOnChange(self, text):
        if len(text) < 1:
            return
        eventCount = int(self.eventDisplayedEdit.text())
        self.plotEvent(self.events[eventCount-1])
        return
        
    def previousClicked(self):
        self.moveEventDisplayBy(-1)
        
    def nextClicked(self):
        self.moveEventDisplayBy(1)
                
    def moveEventDisplayBy(self, count):
        '''
        Changes the event displayed on the event display plot to
        current value + count
        '''
        try:
            eventCount = int(self.eventDisplayedEdit.text())
            if eventCount + count > 0 and eventCount + count <= len(self.events):
                self.eventDisplayedEdit.setText(str(eventCount + count))
        except ValueError:
            # if we can't parse the event display text but there are events,
            # just set to zero
            if len(self.events) > 0:
                self.eventDisplayedEdit.setText('1')
        
    def create_status_bar(self):
        '''
        Creates filter_parameter status bar with filter_parameter text widget.
        '''
        self.status_text = QtGui.QLabel("")
        self.statusBar().addWidget(self.status_text, 1)
    
    def create_menu(self):
        '''
        Creates File menu with Open
        '''
        self.file_menu = self.menuBar().addMenu("&File")
        
        load_data_file_action = self.create_action("&Open Data File",
            shortcut="Ctrl+O", slot=self.open_files,
            tip="Open data Files")
        load_events_database_action = self.create_action("&Open Events Database",
            shortcut="Ctrl+E", slot=self.open_event_database, 
            tip="Open Events Database")
        quit_action = self.create_action("&Quit", slot=self.close,
            shortcut="Ctrl+Q", tip="Close the application")
        
        self.add_actions(self.file_menu,
            (load_data_file_action, load_events_database_action, None, quit_action))
        
#         self.help_menu = self.menuBar().addMenu("&Help")
#         about_action = self.create_action("&About", 
#             shortcut='F1', slot=self.on_about, 
#             tip='About the demo')
#         
#         self.add_actions(self.help_menu, (about_action,))

    def add_actions(self, target, actions):
        for action in actions:
            if action is None:
                target.addSeparator()
            else:
                target.addAction(action)

    def create_action(self, text, slot=None, shortcut=None,
                        icon=None, tip=None, checkable=False,
                        signal="triggered()"):
        action = QtGui.QAction(text, self)
        if icon is not None:
            action.setIcon(QtGui.QIcon(":/%s.png" % icon))
        if shortcut is not None:
            action.setShortcut(shortcut)
        if tip is not None:
            action.setToolTip(tip)
            action.setStatusTip(tip)
        if slot is not None:
            self.connect(action, QtCore.SIGNAL(signal), slot)
        if checkable:
            action.setCheckable(True)
        return action
    
    def plotEventDatabaseAnalyses(self, filenames, params):
        '''
        Plots event statistics.  
        '''
        currentBlockade = []
        for filename in filenames:
            database = sio.loadmat(str(filename))
            events = database['Events']
            for i in range(0, len(events)):
                event = events[i][0][0] # extra zeroes come from way scipy.io saves .mat
                baseline = event['baseline'][0][0][0]
                levels = event['cusum_values'][0][0]
                for level in levels:
                    currentBlockade.append(level - baseline)
                 
        self.axes.hist(currentBlockade,5)
        self.canvas.draw()
        return
    
    def plotData(self, plot_options):
        '''
        Plots waveform in datadict
        Pass in plot_options, filter_parameter dictionary with 'plot_range', 'axes', and 'datadict'
        pass in Data dictionary, with data at 'data' and sample rate at 'SETUP_ADCSAMPLERATE'
        Can pass in range as [start,stop], or 'all' for 0:n
        '''
        axes = plot_options['axes']
        if axes is None:
            axes = self.plot
        # Read the first file, store data in dictionary
        data = plot_options['datadict']['data']
        sample_rate = plot_options['datadict']['SETUP_ADCSAMPLERATE'][0][0]
        plot_range = plot_options['plot_range']
    
        n = len(data)
#         # If problem with input, just plot all the data
        if plot_range == 'all' or len(plot_range) != 2 or plot_range[1] <= plot_range[0]:
            plot_range = [0, n]
        else:  # no problems!
            n = plot_range[1] - plot_range[0] + 1
    
        axes.clear()
        Ts = 1 / sample_rate
        
        times = arange(Ts * plot_range[0], Ts * (plot_range[1]+1), Ts)
        
        curve = Qwt.QwtPlotCurve("Current Trace")
        curve.setData(times, data[plot_range[0]:(plot_range[1]+1)])
        curve.attach(axes)
        axes.replot()
        # Set the top of the zoom stack to current plot, if wanted.  False means no replot (we just plotted it!)
        if 'set_zoom_base' in plot_options:
            if plot_options['set_zoom_base'] == True:
                self.zoomer.setZoomBase(False)
        else:
            self.zoomer.setZoomBase(False)
        
    def addEventToConcatEventPlot(self, event):
        '''
        Adds an event to the concatenated events plot.
        '''
        items = self.plot_concatevents.itemList()
        data = event['raw_data']
        curve = Qwt.QwtPlotCurve('Concat Event ' + str(len(items)+1))
        sample_rate = event['sample_rate']
        baseline = event['baseline']
        #  move the baseline to zero
        data = data - baseline
        times = arange(0, len(data))/sample_rate
        if len(items) > 0:
            # Get the most recent curve added
            prev_curve = items[len(items)-1]
            # Get the time of the last data point in the previous curve
            last_time = prev_curve.x(prev_curve.dataSize()-1)
            times = times + last_time + 1/sample_rate
        curve.setData(times, data)
        if len(items) % 2 == 0 :
            curve.setPen(Qt.QPen(QtCore.Qt.green))
        else:
            curve.setPen(Qt.QPen(QtCore.Qt.blue))
        curve.attach(self.plot_concatevents)
        self.plot_concatevents.replot()
        self.zoomer_concatEvents.setZoomBase(False)
        
    def plotEvent(self, event):
        '''
        Plots the event on the plot with 
        '''
        
        # If I zoom on a plot, then plot a different curve, it doesn't
        # auto scale...  Need to fix!
        
        self.plot_event_zoomed.clear()
        self._plotEventToPlot(event, self.plot_event_zoomed)
        self.zoomer_event.setZoomBase(False)
        
    def _plotEventToPlot(self, event, plot):
        data = event['raw_data']
        levels_index = event['cusum_indexes']
        levels_values = event['cusum_values']
        sample_rate = event['sample_rate']
        event_start = event['event_start']
        event_end = event['event_end']
        baseline = event['baseline']
        raw_points_per_side = event['raw_points_per_side']
        
        Ts = 1 / sample_rate
        
        times = arange(Ts * (event_start - raw_points_per_side), Ts * (event_start - raw_points_per_side + len(data) - 1), Ts)
        times2 = [(event_start - raw_points_per_side) * Ts, (event_start-1)*Ts, event_start*Ts]
        levels2 = [baseline, baseline, levels_values[0]]
        for i in range(1, len(levels_values)):
            times2.append(levels_index[i - 1] * Ts)
            levels2.append(levels_values[i - 1])
            times2.append((levels_index[i - 1]+1) * Ts)
            levels2.append(levels_values[i])
        times2.append(event_end * Ts)
        levels2.append(levels_values[len(levels_values) - 1])
        times2.append((event_end + 1)* Ts)
        levels2.append(baseline)
        times2.append((event_end + raw_points_per_side)* Ts)
        levels2.append(baseline)
        curve = Qwt.QwtPlotCurve('Event')
        curve.setPen(Qt.QPen(QtCore.Qt.green))
        curve.setData(times, data)
        curve.attach(plot)
        curve2 = Qwt.QwtPlotCurve('Levels')
        curve2.setPen(Qt.QPen(QtCore.Qt.blue))
        curve2.setData(times2, levels2)
        curve2.attach(plot)
        
        plot.replot()
            
    def plotEventOnMainPlot(self, event):
        '''
        Adds an event to the main current trace plot.  
        Pass in filter_parameter dictionary with 'event_data', 'sample_rate', 'event_start'
        '''
        if not 'raw_data' in event or not 'sample_rate' in event or not 'event_start' in event or not 'raw_points_per_side' or not 'cusum_indexes' in event or not 'cusum_values' in event:
            print 'incorrectly called plotEventOnMainPlot.  Need \'raw_data\', \'sample_rate\', \'cusum_indexes\', \'cusum_values\', and \'event_start\'' 
            return
        self._plotEventToPlot(event, self.plot)
        
    def on_analyze_stop(self):
        for w in self.threadPool:
            print w
            if isinstance(w, AnalyzeDataThread):
                w.terminate()
        self.stop_analyze_button.setEnabled(False)
        self.status_text.setText('Analyze aborted.')
            
    def on_analyze(self):
        '''
        Searches for events in the file that is currently highlighted in the files list.
        '''
        currItem = self.listWidget.currentItem()
        if currItem == None:
            return
        
        parameters = self.get_current_analysis_parameters()
        if 'error' in parameters:
            self.status_text.setText(parameters['error'])
            return
        
        # Clear the current events
        self.events = []
        
        # Add axes and the filename to the parameters
        parameters['axes'] = self.plot_event_zoomed
        parameters['filename'] = str(currItem.getFileName())
        
        self.status_text.setText('Event Count: 0 Percent Done: 0')
        
        # Start analyzing data in new thread.
        thread = AnalyzeDataThread(parameters)
        self.threadPool.append(thread)
        self.connect(self.threadPool[len(self.threadPool) - 1], QtCore.SIGNAL('_analyze_data_thread_callback(PyQt_PyObject)'), self._analyze_data_thread_callback)
        self.threadPool[len(self.threadPool) - 1].start()
        
        self.stop_analyze_button.setEnabled(True)
        
        # Clear the concatenated_events plot and the single event plot
        self.plot_concatevents.clear()
        self.plot_event_zoomed.clear()
        
    def get_current_analysis_parameters(self):
        '''
        Returns filter_parameter dictionary holding the current analysis parameters set by the user.  Returns an entry 'error' if there were
        invalid inputs.
        '''
        parameters = {}
        # Get Min_event length in microseconds
        try:
            parameters['min_event_length'] = float(self.min_event_length_edit.text())
        except ValueError:
            parameters['error'] = 'Could not read float from Min Event Length text box.  Please fix.'
            return parameters
        # Get Max Event Length in microseconds
        try:
            parameters['max_event_length'] = float(self.max_event_length_edit.text())
        except ValueError:
            parameters['error'] = 'Could not read float from Max Event Length text box.  Please fix.'
            return parameters
        if parameters['min_event_length'] >= parameters['max_event_length']:
            parameters['max_event_length'] = 'Min Event Length is greater than Max Event Length.  Please fix.'
            return parameters
        
        parameters['baseline_type'] = str(self.baseline_type_combo.currentText())
        if parameters['baseline_type'] == 'Adaptive':
            try:
                parameters['filter_parameter'] = float(self.filter_parameter_edit.text())
            except ValueError:
                parameters['error'] = 'Could not read float from Filter Parameter text box.  Please fix.'
                return
        elif parameters['baseline_type'] == 'Fixed':
            try:
                parameters['baseline_current'] = float(self.baseline_current_edit.text())
            except ValueError:
                parameters['error'] = 'Could not read float from Baseline Current text box.  Please fix.'
               
        parameters['threshold_direction'] = str(self.threshold_direction_combo.currentText()) 
        parameters['threshold_type'] = str(self.threshold_type_combo.currentText())
        if parameters['threshold_type'] == 'Noise Based':
            try:
                parameters['start_stddev'] = float(self.threshold_stdev_start.text())
            except ValueError:
                parameters['error'] = 'Could not read float from Start StdDev text box.  Please fix.'
            try:
                parameters['end_stddev'] = float(self.threshold_stdev_end.text())
            except ValueError:
                parameters['error'] = 'Could not read float from End StdDev text box.  Please fix.'
        elif parameters['threshold_type'] == 'Absolute Change':
            try:
                parameters['absolute_change_start'] = float(self.absolute_change_start_edit.text())
            except ValueError:
                parameters['error'] = 'Could not read float from Absolute Change Start.  Please fix.'
            try:
                parameters['absolute_change_end'] = float(self.absolute_change_end_edit.text())
            except ValueError:
                parameters['error'] = 'Could not read float from Absolute Change End.  Please fix.'
        elif parameters['threshold_type'] == 'Percent Change':
            try:
                parameters['percent_change_start'] = float(self.percentage_change_start_edit.text())
            except ValueError:
                parameters['error'] = 'Could not read float from Percent Change Start text box.  Please fix.'
            try:
                parameters['percent_change_end'] = float(self.percentage_change_end_edit.text())
            except ValueError:
                parameters['error'] = 'Could not read float from Percent Change End text box.  Please fix.'
        
        return parameters
        
    def _analyze_data_thread_callback(self, results):
        if 'status_text' in results:
            self.status_text.setText(results['status_text'])
        if 'event' in results:
            event = results['event']
            self.plotEventOnMainPlot(event)
            self.addEventToConcatEventPlot(event)
            self.events.append(event)
            self.eventDisplayedEdit.setMaxLength(int(len(self.events)/10)+1)
            self.eventDisplayedEdit.setValidator(QtGui.QIntValidator(1,len(self.events)))
            self.eventCountText.setText('/' + str(len(self.events)))
            if len(self.events) < 2:
                self.eventDisplayedEdit.setText('1')
        if 'done' in results:
            if results['done']:
                self.stop_analyze_button.setEnabled(False)
        
# def plotSpectrum(data, rate):
#     n = len(data)
#     k = np.arange(n)
#     T = n / rate
#     frq = k / T  # Two sides frequency range
#     frq = frq[range(n / 2)]  # one side frequency range
#     
#     Y = fft(data) / n  # fft and normalization
#     Y = Y[range(n / 2)]
#     
#     decimated = frq
#     if len(frq) > 1000000:
#         decimated = signal.decimate(Y, int(len(data) / 1000000))
#     t = arange(frq[0], frq[len(frq) - 1], (frq[len(frq) - 1] - frq[0]) / len(decimated))
#     
#     plt.plot(t, decimated, 'r')
#     plt.xlim([frq[0], frq[n / 2 - 1]])
#     plt.xlabel('Freq (Hz)')
#     plt.ylabel('|Y(freq)|')


def main():
    
    app = QtGui.QApplication(sys.argv)
    ex = MyApp()
    ex.show()
    app.exec_()
    sys.exit()


if __name__ == '__main__':
    main()

