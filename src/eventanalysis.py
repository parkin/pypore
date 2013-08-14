#!/usr/bin/env python
# -*- coding: utf8 -*-

'''

This program is for finding events in files and displaying the results.
'''
import sys

import PySide # here to force pyqtgraph to use pyside
import pyqtgraph as pg
from pyqtgraph import QtGui, QtCore, PlotData
from pyqtgraph.widgets.LayoutWidget import LayoutWidget

import time

from scipy import arange, linspace
import scipy.io as sio

import numpy as np

# My stuff
from pypore import AnalyzeDataThread, PlotThread
from views import FileListItem, FilterListItem, PlotToolBar

class MyApp(QtGui.QMainWindow):
    
    def __init__(self, app, parent=None):
        super(MyApp, self).__init__()
        
        self.events = [] # holds the events from the most recent analysis run
        self.app = app
        
        pg.setConfigOption('leftButtonPan', False)
        
        self.threadPool = []
        
        self.setWindowTitle('Translocation Event Analysis')
        
        self.create_menu()
        self.create_main_frame()
        self.create_status_bar()
        
    
    def open_files(self):
        '''
        Opens file dialog box, adds names of files to open to list
        '''

        fnames = QtGui.QFileDialog.getOpenFileNames(self, 'Open data file', '../data')[0]
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
        fnames = QtGui.QFileDialog.getOpenFileNames(self, 'Open event database', '../data', '*.mat')[0]
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
        decimates = self.plotToolBar.isDecimateChecked()
        thread = PlotThread(self.p1, filename=str(item.getFileName()), decimate = decimates)
        thread.dataReady.connect(self._on_file_item_doubleclick_callback)
        self.threadPool.append(thread)
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
        
        chooseBaselineBtn = QtGui.QPushButton('Baseline:')
        chooseBaselineBtn.setToolTip('Click to choose the baseline from the plot.')
        
        fixed_options_layout = QtGui.QFormLayout()
        self.baseline_current_edit = QtGui.QLineEdit()
        self.baseline_current_edit.setValidator(QtGui.QDoubleValidator(-9999, 9999, 9))
        self.baseline_current_edit.setText('0.0')
        fixed_options_layout.addRow(chooseBaselineBtn, self.baseline_current_edit)
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
        self.listEventWidget.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        
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
        # Main plot
        self.plotwid = pg.PlotWidget(title = 'Current Trace', name='Plot')
        self.plotwid.setMinimumSize(400, 200)
        self.p1 = self.plotwid.plot() # create an empty plot curve to be filled later
        
        # Create Qwt plot for concatenated events
        
        self.plot_concatevents = pg.PlotWidget(title = 'Concatenated Events', name='Concat')
        self.plot_concatevents.setMinimumSize(400, 200)
        self.plot_concatevents.show()
        
        # Qwt plot for each event found
        self.plot_event_zoomed = pg.PlotWidget(title = 'Single Event', name='Single')
        self.plot_event_zoomed.setMinimumSize(400, 200)
        
        # Tool bar for main plot.  Contains zoom button and different checkboxes
        self.plotToolBar = PlotToolBar(self)
        self.addToolBar(self.plotToolBar)
        
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
        
        eventfinderplots_layout = LayoutWidget()
        eventfinderplots_layout.addWidget(self.plotToolBar, row=1, col=0, colspan=3)
        eventfinderplots_layout.addWidget(self.plotwid, row=2, col=0, colspan=3)
        eventfinderplots_layout.addWidget(self.plot_concatevents, row=3, col=0, colspan=3)
        eventfinderplots_layout.addWidget(self.plot_event_zoomed, row=4, col=0, colspan=3)
        eventfinderplots_layout.addWidget(eventSelectToolbar, row=5, col=0, colspan=3)
        
        return eventfinderplots_layout
    
    def _create_eventanalysis_plot_widget(self):
        # Tab widget for event stuff
        
        vwig = pg.GraphicsLayoutWidget()
        self.plot_eventdepth = vwig.addPlot(title='Event Depth')
        self.plot_eventdur_eventdepth = vwig.addPlot(title='Duration vs. Depth')
        
        vwig.nextRow()
        
        self.plot_scatterselect = vwig.addPlot(title='Single Event')
        self.plot_eventdur = vwig.addPlot(title='Event Duration')
        
        return vwig
        
    
    def _create_right_side(self):
        '''
        Returns a widget holding all of the plots, stuff on right side
        of gui.
        '''
        tabWidget = QtGui.QTabWidget()
        
        # Put everything in filter_parameter scroll area
        scrollArea = QtGui.QScrollArea()
        scrollAreaAnalysis = QtGui.QScrollArea()
        scrollArea.setWidgetResizable(True)
        scrollAreaAnalysis.setWidgetResizable(True)
        
        event_finding_widget = self._create_eventfinder_plots_widget()
        
        event_analysis_widget = self._create_eventanalysis_plot_widget()
        
        scrollArea.setWidget(event_finding_widget)
        scrollAreaAnalysis.setWidget(event_analysis_widget)
        
        tabWidget.addTab(scrollArea, 'Event Finding')
        tabWidget.addTab(scrollAreaAnalysis, 'Event Analysis')
        
        return tabWidget
        
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
        self.plotSingleEvent(self.events[eventCount-1])
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
        dwellTimes = []
        for filename in filenames:
            database = sio.loadmat(str(filename))
            events = database['Events']
            sample_rate = database['sample_rate'][0][0]
            for i in range(0, len(events)):
                event = events[i][0][0] # extra zeroes come from way scipy.io saves .mat
                baseline = event['baseline'][0][0][0]
                levels = event['cusum_values'][0][0]
                for level in levels:
                    currentBlockade.append(level - baseline)
                dwellTime = (event['event_end'][0][0][0]-event['event_start'][0][0][0])/sample_rate
                dwellTimes.append(dwellTime)
                
        color = params['color']
        newcolor = QtGui.QColor(color.red(),color.green(),color.blue(),128)
                 
        y_dt,x_dt = np.histogram(dwellTimes, bins=40)        
        curve_dt = pg.PlotCurveItem(x_dt, y_dt, stepMode=True, fillLevel=0, brush=newcolor)
        self.plot_eventdur.addItem(curve_dt)
        
        y_cb,x_cb = np.histogram(currentBlockade, bins=40)        
        curve_cb = pg.PlotCurveItem(x_cb, y_cb, stepMode=True, fillLevel=0, brush=newcolor)
        self.plot_eventdepth.addItem(curve_cb)
        
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
        data = plot_options['datadict']['data'][0]
        sample_rate = plot_options['datadict']['SETUP_ADCSAMPLERATE'][0][0]
        plot_range = plot_options['plot_range']
    
        n = len(data)
#         # If problem with input, just plot all the data
        if plot_range == 'all' or len(plot_range) != 2 or plot_range[1] <= plot_range[0]:
            plot_range = [0, n]
        else:  # no problems!
            n = plot_range[1] - plot_range[0] + 1
    
        Ts = 1 / sample_rate
        
        times = arange(Ts * plot_range[0], Ts * (plot_range[1]), Ts)
        yData = data[plot_range[0]:(plot_range[1]+1)]
        
        self.p1.setData(x=times,y=yData)
        
    def addEventToConcatEventPlot(self, event):
        '''
        Adds an event to the concatenated events plot.
        '''
        # get the most recent event in concatplot to append to
        times, data, _, _ = self.getEventAndLevelsData(event)
        dataItems = self.plot_concatevents.listDataItems()
        if len(dataItems) > 0:
            prevX = dataItems[len(dataItems)-1].dataBounds(0)[1] 
        else:
            prevX = 2*times[0]
        times = times + (prevX - times[0])
        data = data - event['baseline']
        time1 = time.time()
#         path = pg.arrayToQPath(times.flatten(), data.flatten())
#         item = QtGui.QGraphicsPathItem(path)
#         item.setPen(pg.mkPen('w'))
#         self.plot_concatevents.addItem(item)
        self.plot_concatevents.plot(x=times,y=data)
        print 'Plot time:', time.time() - time1
        
    def plotSingleEvent(self, event):
        '''
        Plots the event on the plot with 
        '''
        
        times, data, times2, levels2 = self.getEventAndLevelsData(event)
        
        self.plot_event_zoomed.clear()
        self.plot_event_zoomed.plot(x=times,y=data)
        self.plot_event_zoomed.plot(x=times2,y=levels2, pen=pg.mkPen('g'))
#         self.plot_event_zoomed.update()
#         self.app.processEvents()
#         self.plot_event_zoomed_event.setData(x=times,y=data)
#         self.plot_event_zoomed_levels.setData(x=times2,y=levels2)
        
    def getEventAndLevelsData(self, event):
        data = event['raw_data']
        levels_index = event['cusum_indexes']
        levels_values = event['cusum_values']
        sample_rate = event['sample_rate']
        event_start = event['event_start']
        event_end = event['event_end']
        baseline = event['baseline']
        raw_points_per_side = event['raw_points_per_side']
        
        Ts = 1 / sample_rate
        
        times = linspace(Ts * (event_start - raw_points_per_side), Ts * (event_start - raw_points_per_side + len(data) - 1), len(data))
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
        return times, data, times2, levels2
        
        
    def plotEventOnMainPlot(self, event):
        '''
        Adds an event to the main current trace plot.  
        Pass in filter_parameter dictionary with 'event_data', 'sample_rate', 'event_start'
        '''
        if not 'raw_data' in event or not 'sample_rate' in event or not 'event_start' in event or not 'raw_points_per_side' or not 'cusum_indexes' in event or not 'cusum_values' in event:
            print 'incorrectly called plotEventOnMainPlot.  Need \'raw_data\', \'sample_rate\', \'cusum_indexes\', \'cusum_values\', and \'event_start\'' 
            return
        times, data, times2, levels2 = self.getEventAndLevelsData(event)
        self.plotwid.plot(x=times,y=data, pen=pg.mkPen('y'))
        self.plotwid.plot(x=times2,y=levels2, pen=pg.mkPen('g'))
#         self.plotwid.update()
        
    def on_analyze_stop(self):
        for w in self.threadPool:
            if isinstance(w, AnalyzeDataThread):
                w.cancelled = True
                w.wait()
        self.stop_analyze_button.setEnabled(False)
        self.status_text.setText('Analyze aborted.')
            
    def on_analyze(self):
        '''
        Searches for events in the file that is currently highlighted in the files list.
        '''
        selectedItems = self.listWidget.selectedItems()
        if len(selectedItems) > 0:
            currItem = selectedItems[0]
        else:
            return
        
        parameters = self.get_current_analysis_parameters()
        if 'error' in parameters:
            self.status_text.setText(parameters['error'])
            return
        
        self.plot_concatevents.clear()
        self.plot_event_zoomed.clear()
        items = self.plotwid.listDataItems()
        # remove events from main plot, keep trace (first entry probably)
        for i in range(0, len(items)):
            if i > 0:
                self.plotwid.removeItem(items[i])
        
        
        # Clear the current events
        del self.events[:]
        
        # Add axes and the filename to the parameters
        parameters['axes'] = self.plot_event_zoomed
        parameters['filename'] = str(currItem.getFileName())
        
        self.status_text.setText('Event Count: 0 Percent Done: 0')
        
        # Start analyzing data in new thread.
        thread = AnalyzeDataThread(parameters)
        thread.dataReady.connect(self._analyze_data_thread_callback)
        self.threadPool.append(thread)
        thread.start()
        
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
            if self.plotToolBar.isPlotDuringChecked():
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
    
#     app = QtGui.QApplication(sys.argv)
    app = pg.mkQApp()
    ex = MyApp(app)
    ex.show()
    app.exec_()
    sys.exit()


if __name__ == '__main__':
    main()

