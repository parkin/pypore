#!/usr/bin/env python
# -*- coding: utf8 -*-

"""

This program is for finding events in files and displaying the results.
"""
import sys
import os

from PySide import QtCore, QtGui  # Must import PySide stuff before pyqtgraph so pyqtgraph knows
                                # to use PySide instead of PyQt
             
                                
# The rest of the imports can be found below in _longImports
def _long_imports(**kwargs):
    """
    Loads imports and updates the splash screen with information.
    """
    # append the src directory to the PYTHONPATH, i.e. '../../' = 'src/'
    src_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    if not src_dir in sys.path:
        sys.path.append(src_dir)
    
    global AnalyzeDataThread, PlotThread, FileListItem, FilterListItem, \
            PlotToolBar, DataFileListItem, MyPlotItem, prepareDataFile, pg, pgc, \
            LayoutWidget, PlotCurveItem, linspace, np, \
            MySpotItem, MyScatterPlotItem, EventAnalysisWidget, ed, tabs
        
    update_splash = False
    if 'splash' in kwargs and 'app' in kwargs:
        update_splash = True
        splash = kwargs['splash']
        app = kwargs['app']
       
    if update_splash:
        splash.showMessage("Importing PyQtGraph...", alignment=QtCore.Qt.AlignBottom)
        app.processEvents()
    import pyqtgraph as pg
    import pyqtgraph.console as pgc
    from pyqtgraph.widgets.LayoutWidget import LayoutWidget
    from pyqtgraph.graphicsItems.PlotCurveItem import PlotCurveItem
    
    if update_splash:
        splash.showMessage("Importing SciPy...", alignment=QtCore.Qt.AlignBottom)
        app.processEvents()
    from scipy import linspace
    
    if update_splash:
        splash.showMessage("Importing NumPy...", alignment=QtCore.Qt.AlignBottom)
        app.processEvents()
    import numpy as np
            
    # My stuff
    if update_splash:
        splash.showMessage("Setting up Cython imports...", alignment=QtCore.Qt.AlignBottom)
        app.processEvents()
    from pypore import cythonsetup
    
    if update_splash:
        splash.showMessage("Compiling Cython imports... DataFileOpener", alignment=QtCore.Qt.AlignBottom)
        app.processEvents()
    from pypore.dataFileOpener import prepareDataFile
    import tabs

    if update_splash:
        splash.showMessage("Compiling Cython imports... EventFinder", alignment=QtCore.Qt.AlignBottom)
        app.processEvents()
    from MyThreads import AnalyzeDataThread, PlotThread
    from views import FileListItem, FilterListItem, PlotToolBar, DataFileListItem, MyPlotItem
    from views import MySpotItem, MyScatterPlotItem, EventAnalysisWidget
    
    if update_splash:
        splash.showMessage("Importing EventDatabase", alignment=QtCore.Qt.AlignBottom)
        app.processEvents()
    import pypore.eventDatabase as ed
    
# If we are running from a test, name != main, and we'll need to import the above on our own
if not __name__ == '__main__':
    _long_imports()


class PathItem(QtGui.QGraphicsPathItem):
        def __init__(self, x, y, conn='all'):
            xr = x.min(), x.max()
            yr = y.min(), y.max()
            self._bounds = QtCore.QRectF(xr[0], yr[0], xr[1] - xr[0], yr[1] - yr[0])
            self.path = pg.arrayToQPath(x, y, conn)
            QtGui.QGraphicsPathItem.__init__(self, self.path)
            
        def boundingRect(self):
            return self._bounds


class MyMainWindow(QtGui.QMainWindow):

    def __init__(self, app, parent=None):
        super(MyMainWindow, self).__init__()
        
        self.events = []  # holds the events from the most recent analysis run
        self.app = app
        
        pg.setConfigOption('leftButtonPan', False)
        
        self.open_dir = '../../data'
        
        self.thread_pool = []
        
        self.setWindowTitle('Translocation Event Analysis')
        
        self.create_menu()
        self._create_main_frame()
        self.create_status_bar()
        
    def open_files(self):
        """
        Opens file dialog box, adds names of files to open to list
        """
        self.event_finding_tab.open_files(self.open_dir)

    def _on_files_opened(self, open_dir=None):
        """
        Callback for when files are opened.

        :param str open_dir: Directory where files were opened from.
        """
        self.main_tabwig.setCurrentIndex(0)
        if not open_dir is None:
            self.open_dir = open_dir

    def open_event_database(self):
        """
        Opens file dialog box, add names of event database files to open list
        """
        fnames = QtGui.QFileDialog.getOpenFileNames(self, 'Open event database', self.open_dir, '*.h5')[0]
        if len(fnames) > 0:
            self.list_event_widget.clear()
            self.eventview_list_widget.clear()
        else:
            return
        are_files_opened = False
        for w in fnames:
            are_files_opened = True
            item = FileListItem(w)
            self.open_dir = item.getDirectory()  # save the directory info for later
            self.list_event_widget.addItem(item)
            
            item = FileListItem(w)
            self.eventview_list_widget.addItem(item)
            
        if are_files_opened:
            self.btnAddFilter.setEnabled(False)
            if self.main_tabwig.currentIndex() < 1:
                self.main_tabwig.setCurrentIndex(2)

    def set_status(self, text):
        """
        Sets the status text.

        :param StringType text: Text to display in the status bar.
        """
        self.status_text.setText(text)

    def _on_event_file_selection_changed(self):
        self.btnAddFilter.setEnabled(True)
            
    def _create_event_viewer_options(self):
        scroll_area = QtGui.QScrollArea()
        scroll_area.setWidgetResizable(True)
        
        # Create filter_parameter list for files want to analyze
        self.eventview_list_widget = QtGui.QListWidget()
        self.eventview_list_widget.itemDoubleClicked.connect(self._on_eventview_file_item_doubleclick)
        self.eventview_list_widget.setMaximumHeight(100)
        
        fixed_analysis_options = QtGui.QFormLayout()
        fixed_analysis_options.addRow('Event Databases:', self.eventview_list_widget)
        
        vbox_left = QtGui.QVBoxLayout()
        vbox_left.addLayout(fixed_analysis_options)
        
        vbox_left_widget = QtGui.QWidget()
        vbox_left_widget.setLayout(vbox_left)
        
        scroll_area.setWidget(vbox_left_widget)
        
        return scroll_area
        
    def _on_eventview_file_item_doubleclick(self, item):
        """
        """
        self.event_view_item = item
        
        h5file = ed.openFile(item.getFileName())
        
        event_count = h5file.getEventCount()
        
        h5file.close()
        
        self.eventDisplayedEdit.setMaxLength(int(event_count / 10) + 1)
        self.eventDisplayedEdit.setValidator(QtGui.QIntValidator(1, event_count, self.eventDisplayedEdit))
        self.eventCountText.setText('/' + str(event_count))
        self.eventDisplayedEdit.setText('')
        self.eventDisplayedEdit.setText('1')
    
    def _create_event_analysis_options(self):
        scroll_area = QtGui.QScrollArea()
        scroll_area.setWidgetResizable(True)
        
        # Create filter_parameter list for files want to analyze
        self.list_event_widget = QtGui.QListWidget()
#         self.listEventWidget.itemSelectionChanged.connect(self._on_file_item_selection_changed)
#         self.listEventWidget.itemDoubleClicked.connect(self._on_file_item_doubleclick)
        self.list_event_widget.setMaximumHeight(100)
        self.list_event_widget.itemSelectionChanged.connect(self._on_event_file_selection_changed)
        self.list_event_widget.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        
        files_options = QtGui.QFormLayout()
        files_options.addRow('Event Databases:', self.list_event_widget)
        
        # # Color Picker
        self.event_color = QtGui.QColor('blue')
        pick_color_btn = QtGui.QPushButton()
        pick_color_btn.setText('Choose a Color')
        pick_color_btn.clicked.connect(self.color_picker_btn_clicked)
        
        self.frm = QtGui.QFrame()
        self.frm.setStyleSheet("QWidget { background-color: %s }" 
            % self.event_color.name())
        self.frm.setMinimumSize(15, 15)
        self.frm.setMaximumSize(30, 30)
        
        files_options.addRow(pick_color_btn, self.frm)
        
        # # List of filters created
        self.btnAddFilter = QtGui.QPushButton('Add selections as filter')
        self.btnAddFilter.clicked.connect(self.add_filter_clicked)
        self.btnAddFilter.setEnabled(False)
        formFilter = QtGui.QFormLayout()
        formFilter.addRow('Filters:', self.btnAddFilter)
        self.listFilterWidget = QtGui.QListWidget()
        vbox = QtGui.QVBoxLayout()
        vbox.addLayout(formFilter)
        vbox.addWidget(self.listFilterWidget)
        btn_remove_filter = QtGui.QPushButton('Remove selected filters')
        btn_remove_filter.clicked.connect(self.remove_filter_clicked)
        vbox.addWidget(btn_remove_filter)
        
        vbox_left = QtGui.QVBoxLayout()
        vbox_left.addLayout(files_options)
        vbox_left.addLayout(vbox)
        
        vbox_left_widget = QtGui.QWidget()
        vbox_left_widget.setLayout(vbox_left)
        
        scroll_area.setWidget(vbox_left_widget)
        
        return scroll_area
    
    def add_filter_clicked(self):
        items = self.list_event_widget.selectedItems()
        if items is None or len(items) < 1:
            return
        
        params = self._get_current_event_analysis_params()
        
        filenames = []
        
        for item in items:
            filenames.append(item.getFileName())
        
        item = FilterListItem(filenames, **params)
        self.listFilterWidget.addItem(item)
        
        self.eventAnalysisWidget.addSelections(filenames, params)
        
    def remove_filter_clicked(self):
        items = self.listFilterWidget.selectedItems()
        for item in items:
            index = self.listFilterWidget.indexFromItem(item).row()
            self.eventAnalysisWidget.removeFilter(index)
            self.listFilterWidget.takeItem(index)
        
    def _get_current_event_analysis_params(self):
        params = {}
        params['color'] = self.event_color
        return params
    
    def color_picker_btn_clicked(self):
        col = QtGui.QColorDialog.getColor(initial=self.event_color)
        
        if col.isValid():
            self.event_color = col
            self.frm.setStyleSheet("QWidget { background-color: %s }"
                % col.name())
        
    def _create_eventviewer_plot_widget(self):
        wig = pg.GraphicsLayoutWidget()
        wig2 = pg.GraphicsLayoutWidget()

        # Main plot        
        self.eventview_plotwid = MyPlotItem(title='Current Trace', name='Plot')
        wig.addItem(self.eventview_plotwid)
        self.eventview_plotwid.enableAutoRange('xy', False)
        self.eventview_p1 = self.eventview_plotwid.plot()  # create an empty plot curve to be filled later
        
        wig.nextRow()
        # Create Qwt plot for concatenated events
        self.plot_concatevents = wig.addPlot(title='Concatenated Events', name='Concat')
        
        self.eventviewer_plots = []
        
        # Now add 9 plots to view events in
        for i in xrange(3):
            wig2.nextRow()
            for j in xrange(3):
                plot = wig2.addPlot(title='Event ' + str(i * 3 + j), name='Single' + str(i * 3 + j))
                self.eventviewer_plots.append(plot)
                
        # Tool bar for main plot.  Contains zoom button and different checkboxes
#         self.plotToolBar = PlotToolBar(self)
#         self.addToolBar(self.plotToolBar)
        
        eventSelectToolbar = QtGui.QToolBar(self)
        self.addToolBar(eventSelectToolbar)
        
        btnPrevious = QtGui.QPushButton(eventSelectToolbar)
        btnPrevious.setText("Previous")
        btnPrevious.clicked.connect(self.previousClicked)
        eventSelectToolbar.addWidget(btnPrevious)
        
        self.eventDisplayedEdit = QtGui.QLineEdit()
        self.eventDisplayedEdit.setText('0')
        self.eventDisplayedEdit.setMaxLength(int(len(self.events) / 10) + 1)
        self.eventDisplayedEdit.setValidator(QtGui.QIntValidator(0, len(self.events), self.eventDisplayedEdit))
        self.eventDisplayedEdit.textChanged.connect(self._eventDisplayEditOnChange)
        eventSelectToolbar.addWidget(self.eventDisplayedEdit)
        
        self.eventCountText = QtGui.QLabel()
        self.eventCountText.setText('/' + str(len(self.events)))
        eventSelectToolbar.addWidget(self.eventCountText)
        
        btnNext = QtGui.QPushButton(eventSelectToolbar)
        btnNext.setText("Next")
        btnNext.clicked.connect(self.nextClicked)
        eventSelectToolbar.addWidget(btnNext)
        
        frame = QtGui.QSplitter()
        frame.setOrientation(QtCore.Qt.Vertical)
        frame.addWidget(wig)
        frame.addWidget(wig2)
        
        eventfinderplots_layout = LayoutWidget()
#         eventfinderplots_layout.addWidget(self.plotToolBar, row=1, col=0, colspan=3)
        eventfinderplots_layout.addWidget(frame, row=2, col=0, colspan=3)
        eventfinderplots_layout.addWidget(eventSelectToolbar, row=5, col=0, colspan=3)
        
        return eventfinderplots_layout
    
    def _create_eventanalysis_plot_widget(self):
        # Tab widget for event stuff
        
        self.eventAnalysisWidget = EventAnalysisWidget()
        
        return self.eventAnalysisWidget
    
    def _create_event_analysis_tab(self):
        frame = QtGui.QSplitter()
        
        options = self._create_event_analysis_options()
        plots = self._create_eventanalysis_plot_widget()
        
        # Put everything in filter_parameter scroll area
        scrollOptions = QtGui.QScrollArea()
        scrollPlots = QtGui.QScrollArea()
        scrollOptions.setWidgetResizable(True)
        scrollPlots.setWidgetResizable(True)
        
        scrollOptions.setWidget(options)
        scrollPlots.setWidget(plots)
        
        frame.addWidget(scrollOptions)
        frame.addWidget(scrollPlots)
        
        return frame
    
    def _create_event_viewer_tab(self):
        frame = QtGui.QSplitter()
        
        options = self._create_event_viewer_options()
        plots = self._create_eventviewer_plot_widget()
        
        # Put everything in filter_parameter scroll area
        scrollOptions = QtGui.QScrollArea()
        scrollPlots = QtGui.QScrollArea()
        scrollOptions.setWidgetResizable(True)
        scrollPlots.setWidgetResizable(True)
        
        scrollOptions.setWidget(options)
        scrollPlots.setWidget(plots)
        
        frame.addWidget(scrollOptions)
        frame.addWidget(scrollPlots)
        return frame
    
    def _create_data_modification_tab(self):
        frame = QtGui.QSplitter()

        options = self._create_data_modification_options()

        return frame

    def _process_events(self):
        self.app.processEvents()
        
    def _create_main_frame(self):
        """
        Helper to initialize the main gui frame.
        """
        # data_modification = self._create_data_modification_tab()
        self.event_finding_tab = tabs.EventFindingTab(self)
        self.event_finding_tab.set_on_files_opened_callback(self._on_files_opened)
        self.event_finding_tab.set_on_status_update_callback(self.set_status)
        self.event_finding_tab.set_process_events_callback(self._process_events)

        event_viewer = self._create_event_viewer_tab()
        event_analysis = self._create_event_analysis_tab()
        
        # Layout holding everything        
        self.main_tabwig = QtGui.QTabWidget()
        # self.main_tabwig.addTab(data_modification, 'Data modification')
        self.main_tabwig.addTab(self.event_finding_tab, 'Event Finding')
        self.main_tabwig.addTab(event_viewer, 'Event View')
        self.main_tabwig.addTab(event_analysis, 'Event Analysis')
        self.main_tabwig.setMinimumSize(1000, 550)
        
        text = """*********************
Welcome to pyporegui!

If you are unfamiliar with the python console, feel free to ignore this console.

However, you can use this console to interact with your data and the gui!
Type globals() to see globally defined variabels.
Type locals() to see application-specific variables.

The current namespace should include:
    np        -    numpy
    pg        -    pyqtgraph
    ed        -    pypore.eventDatabase
    currentPlot -  Top plot in the event finding tab.
*********************"""

        namespace = {'np': np, 'pg': pg, 'ed': ed, 'currentPlot': self.event_finding_tab.plotwid}
        self.console = pgc.ConsoleWidget(namespace=namespace, text=text)
        
        frame = QtGui.QSplitter()
        frame.setOrientation(QtCore.Qt.Vertical)
        frame.addWidget(self.main_tabwig)
        frame.addWidget(self.console)
        
        self.setCentralWidget(frame)
        
    def _eventDisplayEditOnChange(self, text):
        if len(text) < 1:
            return
        position = int(self.eventDisplayedEdit.text())
        self.plotSingleEvents(position - 1)
        return
        
    def previousClicked(self):
        self.moveEventDisplayBy(-1 * len(self.eventviewer_plots))
        
    def nextClicked(self):
        self.moveEventDisplayBy(len(self.eventviewer_plots))
                
    def moveEventDisplayBy(self, count):
        '''
        Changes the event displayed on the event display plot to
        current value + count
        '''
        h5eventCount = 0
        try:
            h5file = ed.openFile(self.event_view_item.getFileName())
            h5eventCount = h5file.getEventCount()
            h5file.close()
        except:
            return
        try:
            eventCount = int(self.eventDisplayedEdit.text())
            if 0 < eventCount + count <= h5eventCount:
                self.eventDisplayedEdit.setText(str(eventCount + count))
        except ValueError:
            # if we can't parse the event display text but there are events,
            # just set to zero
            if h5eventCount > 0:
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
        sample_rate = plot_options['datadict']['sample_rate']
        plot_range = plot_options['plot_range']
    
        n = len(data)
        # If problem with input, just plot all the data
        if plot_range == 'all' or len(plot_range) != 2 or plot_range[1] <= plot_range[0]:
            plot_range = [0, n]
        else:  # no problems!
            n = plot_range[1] - plot_range[0] + 1
    
        Ts = 1 / sample_rate
        
        times = linspace(Ts * plot_range[0], Ts * plot_range[1], n)
        yData = data[plot_range[0]:(plot_range[1] + 1)]
        
        self.plotwid.clearEventItems()
        self.p1.setData(x=times, y=yData)
        self.plotwid.autoRange()
        self.app.processEvents()
        
    def addEventsToConcatEventPlot(self, events):
        if len(events) < 1:
            return
        size = 0
        for event in events:
            size += event['raw_data'].size
        data = np.empty(size)
        sample_rate = events[0]['sample_rate']
        ts = 1 / sample_rate
        times = np.linspace(0., (size - 1) * ts, size) + self.prev_concat_time
        self.prev_concat_time += size * ts
        index = 0
        for event in events:
            d = event['raw_data'].size
            baseline = event['baseline']
            data[index:index + d] = (event['raw_data'] - baseline)
            index += d
            
        item = PathItem(times, data)
        item.setPen(pg.mkPen('w'))
        self.plot_concatevents.addItem(item)
        
    def plotSingleEvents(self, event):
        '''
        Plots the event on the plot with 
        '''
        h5file = ed.openFile(self.event_view_item.getFileName(), mode='r')
        
        eventCount = h5file.getEventCount()
        
        for i in xrange(3):
            for j in xrange(3):
                pos = 3 * i + j
                if pos + event >= eventCount or pos + event < 0:
                    self.eventviewer_plots[pos].clear()
                    self.eventviewer_plots[pos].setTitle('')
                else:
                    self.plotSingleEvent(h5file, event + pos, self.eventviewer_plots[pos])
                    self.eventviewer_plots[pos].setTitle('Event ' + str(event + pos + 1))
        
        h5file.close()
        
    def plotSingleEvent(self, h5file, position, plot):
        sampleRate = h5file.getSampleRate()
        row = h5file.getEventRow(position)
        arrayRow = row['arrayRow']
        eventLength = row['eventLength']
        rawPointsPerSide = row['rawPointsPerSide']
        
        rawData = h5file.getRawDataAt(arrayRow)
        
        n = len(rawData)
        
        times = np.linspace(0.0, 1.0 * n / sampleRate, n)
        
        plot.clear()
        plot.plot(times, rawData)
        # plot the event points in yellow
        plot.plot(times[rawPointsPerSide:rawPointsPerSide + eventLength], \
                                     rawData[rawPointsPerSide:rawPointsPerSide + eventLength], pen='y')
        
        # Plot the cusum levels
        nLevels = row['nLevels']
        baseline = row['baseline']
        # left, start-1, start, 
        levels = h5file.getLevelsAt(arrayRow)
        indices = h5file.getLevelLengthsAt(arrayRow)
        
        levelTimes = np.zeros(2 * nLevels + 4)
        levelValues = np.zeros(2 * nLevels + 4)
        
        levelTimes[1] = 1.0 * (rawPointsPerSide - 1) / sampleRate
        levelValues[0] = levelValues[1] = baseline
        i = 0
        length = 0
        for i in xrange(nLevels):
            levelTimes[2 * i + 2] = times[rawPointsPerSide] + 1.0 * (length) / sampleRate
            levelValues[2 * i + 2] = levels[i]
            levelTimes[2 * i + 3] = times[rawPointsPerSide] + 1.0 * (length + indices[i]) / sampleRate
            levelValues[2 * i + 3] = levels[i]
            length += indices[i]
        i += 1        
        levelTimes[2 * i + 2] = times[rawPointsPerSide + eventLength]
        levelTimes[2 * i + 3] = times[n - 1]
        levelValues[2 * i + 2] = levelValues[2 * i + 3] = baseline
        
        plot.plot(levelTimes, levelValues, pen='g')
        
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
        
        n = data.size
        
        times = linspace(Ts * (event_start - raw_points_per_side), Ts * (event_start - raw_points_per_side + n - 1), n)
        times2 = [(event_start - raw_points_per_side) * Ts, (event_start - 1) * Ts]
        levels2 = [baseline, baseline]
        for i, level_value in enumerate(levels_values):
            times2.append(levels_index[i] * Ts)
            levels2.append(level_value)
            if i < len(levels_values) - 1 :
                times2.append((levels_index[i + 1] - 1) * Ts)
                levels2.append(level_value)
        times2.append(event_end * Ts)
        levels2.append(levels_values[len(levels_values) - 1])
        times2.append((event_end + 1) * Ts)
        levels2.append(baseline)
        times2.append((event_end + raw_points_per_side) * Ts)
        levels2.append(baseline)
        return times, data, times2, levels2
        
    def plotEventsOnMainPlot(self, events):
        if len(events) < 1:
            return
        size = 0
        for event in events:
            size += event['raw_data'].size
        data = np.empty(size)
        sample_rate = events[0]['sample_rate']
        raw_points_per_side = events[0]['raw_points_per_side']
        ts = 1 / sample_rate
        times = np.empty(size)
        conn = np.ones(size)
        index = 0
        for event in events:
            event_start = event['event_start']
            event_data = event['raw_data']
            d = event_data.size
            times[index:index + d] = linspace(ts * (event_start - raw_points_per_side), ts * (event_start - raw_points_per_side + d - 1), d)
            data[index:index + d] = event_data
            conn[index - 1] = False  # disconnect separate events
            index += d
            
        item = PathItem(times, data, conn)
        item.setPen(pg.mkPen('y'))
        self.plotwid.addEventItem(item)
        
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
        
    def clean_threads(self):
        for w in self.thread_pool:
            w.cancel()
#             w.wait()
            self.thread_pool.remove(w)


def main():
    
    app = QtGui.QApplication(sys.argv)
    pixmap = QtGui.QPixmap('splash.png')
    splash = QtGui.QSplashScreen(pixmap, QtCore.Qt.WindowStaysOnTopHint)
    splash.show()
    _long_imports(splash=splash, app=app)
    splash.showMessage("Creating main window...", alignment=QtCore.Qt.AlignBottom)
    app.processEvents()
    ex = MyMainWindow(app)
    ex.show()
    splash.finish(ex)
    app.exec_()
    ex.clean_threads()

if __name__ == '__main__':
    main()

