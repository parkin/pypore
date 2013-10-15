#!/usr/bin/env python
# -*- coding: utf8 -*-

'''

This program is for finding events in files and displaying the results.
'''
import sys, os

from PySide import QtCore, QtGui  # Must import PySide stuff before pyqtgraph so pyqtgraph knows
                                # to use PySide instead of PyQt
             
                                
# The rest of the imports can be found below in _longImports
def _longImports(**kwargs):
    '''
    Loads imports and updates the splash screen with information.
    '''
    # append the src directory to the PYTHONPATH, i.e. '../../' = 'src/'
    srcdir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    if not srcdir in sys.path:
        sys.path.append(srcdir)
    
    global AnalyzeDataThread, PlotThread, FileListItem, FilterListItem, \
            PlotToolBar, DataFileListItem, MyPlotItem, prepareDataFile, pg, pgc, \
            LayoutWidget, PlotCurveItem, linspace, np, tb, \
            MySpotItem, MyScatterPlotItem
        
    updateSplash = False    
    if 'splash' in kwargs and 'app' in kwargs:
        updateSplash = True
        splash = kwargs['splash']
        app = kwargs['app']
       
    if updateSplash: 
        splash.showMessage("Importing PyQtGraph...", alignment=QtCore.Qt.AlignBottom)
        app.processEvents()
    import pyqtgraph as pg
    import pyqtgraph.console as pgc
    from pyqtgraph.widgets.LayoutWidget import LayoutWidget
    from pyqtgraph.graphicsItems.PlotCurveItem import PlotCurveItem
    
    if updateSplash: 
        splash.showMessage("Importing SciPy...", alignment=QtCore.Qt.AlignBottom)
        app.processEvents()
    from scipy import linspace
    
    if updateSplash: 
        splash.showMessage("Importing NumPy...", alignment=QtCore.Qt.AlignBottom)
        app.processEvents()
    import numpy as np
            
    # My stuff
    if updateSplash: 
        splash.showMessage("Setting up Cython imports...", alignment=QtCore.Qt.AlignBottom)
        app.processEvents()
    from pypore import cythonsetup
    
    if updateSplash: 
        splash.showMessage("Compiling Cython imports... DataFileOpener", alignment=QtCore.Qt.AlignBottom)
        app.processEvents()
    from pypore.DataFileOpener import prepareDataFile
    
    if updateSplash: 
        splash.showMessage("Compiling Cython imports... EventFinder", alignment=QtCore.Qt.AlignBottom)
        app.processEvents()
    from MyThreads import AnalyzeDataThread, PlotThread
    from views import FileListItem, FilterListItem, PlotToolBar, DataFileListItem, MyPlotItem
    from views import MySpotItem, MyScatterPlotItem
    
    if updateSplash: 
        splash.showMessage("Importing PyTables", alignment=QtCore.Qt.AlignBottom)
        app.processEvents()
    import tables as tb
    
# If we are running from a test, name != main, and we'll need to import the above on our own
if not __name__ == '__main__':
    _longImports()

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
        
        self.openDir = '../../data'
        
        self.threadPool = []
        self.lastScatterClicked = []
        
        self.setWindowTitle('Translocation Event Analysis')
        
        self.create_menu()
        self.create_main_frame()
        self.create_status_bar()
        
    def open_files(self):
        '''
        Opens file dialog box, adds names of files to open to list
        '''

        fnames = QtGui.QFileDialog.getOpenFileNames(self, 'Open data file', self.openDir, "All types(*.hkd *.log *.mat);;Heka files *.hkd(*.hkd);;Chimera files *.log(*.log);;Gabys files *.mat(*.mat)")[0]
        if len(fnames) > 0:
            self.listWidget.clear()
        else:
            return
        areFilesOpened = False
        for w in fnames:
            areFilesOpened = True
            f, params = prepareDataFile(w)
            if 'error' in params:
                self.status_text.setText(params['error'])
            else:
                f.close()
                item = DataFileListItem(w, params)
                self.openDir = item.getDirectory()
                self.listWidget.addItem(item)
            
        if areFilesOpened:
            self.analyze_button.setEnabled(False)
            self.main_tabwig.setCurrentIndex(0)
            
    def open_event_database(self):
        '''
        Opens file dialog box, add names of event database files to open list
        '''
        fnames = QtGui.QFileDialog.getOpenFileNames(self, 'Open event database', self.openDir, '*.h5')[0]
        if len(fnames) > 0:
            self.listEventWidget.clear()
        else:
            return
        areFilesOpened = False
        for w in fnames:
            areFilesOpened = True
            item = FileListItem(w)
            self.openDir = item.getDirectory()  # save the directory info for later
            self.listEventWidget.addItem(item)
            
        if areFilesOpened:
            self.btnAddFilter.setEnabled(False)
            self.main_tabwig.setCurrentIndex(1)
            
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
        thread = PlotThread(self.p1, filename=str(item.getFileName()), decimate=decimates)
        thread.dataReady.connect(self._on_file_item_doubleclick_callback)
        self.threadPool.append(thread)
        self.threadPool[len(self.threadPool) - 1].start()
        
    def _on_file_item_doubleclick_callback(self, results):
        if 'plot_options' in results:
            self.plotData(results['plot_options'])
        if 'status_text' in results:
            self.status_text.setText(results['status_text'])
        if 'thread' in results:
            self.threadPool.remove(results['thread'])
            
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
        
        # # Color Picker
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
        
        # # List of filters created
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
        
        item = FilterListItem(filenames, **params)
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
        
    def _create_eventfinder_plots_widget(self):
        wig = pg.GraphicsLayoutWidget()

        # Main plot        
        self.plotwid = MyPlotItem(title='Current Trace', name='Plot')
        wig.addItem(self.plotwid)
        self.plotwid.enableAutoRange('xy', False)
        self.p1 = self.plotwid.plot()  # create an empty plot curve to be filled later
        
        wig.nextRow()
        # Create Qwt plot for concatenated events
        self.plot_concatevents = wig.addPlot(title='Concatenated Events', name='Concat')
        
        wig.nextRow()
        # Qwt plot for each event found
        self.plot_event_zoomed = wig.addPlot(title='Single Event', name='Single')
        
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
        self.eventDisplayedEdit.setMaxLength(int(len(self.events) / 10) + 1)
        self.eventDisplayedEdit.setValidator(QtGui.QIntValidator(0, len(self.events)))
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
        eventfinderplots_layout.addWidget(wig, row=2, col=0, colspan=3)
        eventfinderplots_layout.addWidget(eventSelectToolbar, row=5, col=0, colspan=3)
        
        return eventfinderplots_layout
    
    def _create_eventanalysis_plot_widget(self):
        # Tab widget for event stuff
        
        vwig = pg.GraphicsLayoutWidget()
        self.plot_eventdepth = vwig.addPlot(title='Event Depth')
        self.plot_eventdepth.setMouseEnabled(x=False, y=True)
        self.plot_eventdur_eventdepth = vwig.addPlot(name='Depth vs. Duration', title='Depth vs. Duration')
        self.plot_eventdepth.setYLink('Depth vs. Duration')
        
        vwig.nextRow()
        
        self.plot_scatterselect = vwig.addPlot(title='Single Event')
        self.plot_eventdur = vwig.addPlot(title='Event Duration')
        self.plot_eventdur.setXLink('Depth vs. Duration')
        self.plot_eventdur.setMouseEnabled(x=True, y=False)
        
        return vwig
    
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
    
    def _create_event_finding_tab(self):
        frame = QtGui.QSplitter()
        
        options = self._create_event_finding_options()
        plots = self._create_eventfinder_plots_widget()
        
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
        
    def create_main_frame(self):
        '''
        Initializes the main gui frame.
        '''
        event_finding = self._create_event_finding_tab()
        event_analysis = self._create_event_analysis_tab()
        
        # Layout holding everything        
        self.main_tabwig = QtGui.QTabWidget()  # Splitter allows for drag to resize between children
        self.main_tabwig.addTab(event_finding, 'Event Finding')
        self.main_tabwig.addTab(event_analysis, 'Event Analysis')
        self.main_tabwig.setMinimumSize(1000,550)
        
        text = """*********************
Welcome to pyporegui!

If you are unfamiliar with the python console, feel free to ignore this console.

However, you can use this console to interact with your data and the gui!
Type globals() to see globally defined variabels.
Type locals() to see application-specific variables.

The current namespace should include:
    np        -    numpy
    pg        -    pyqtgraph
    tb        -    PyTables
    currentPlot -  Top plot in the event finding tab.
*********************"""

        namespace = {'np': np, 'pg': pg, 'tb': tb, 'currentPlot': self.plotwid}
        self.console = pgc.ConsoleWidget(namespace=namespace, text=text)
        
        frame = QtGui.QSplitter()
        frame.setOrientation(QtCore.Qt.Vertical)
        frame.addWidget(self.main_tabwig)
        frame.addWidget(self.console)
        
        self.setCentralWidget(frame)
        
    def _eventDisplayEditOnChange(self, text):
        if len(text) < 1:
            return
        eventCount = int(self.eventDisplayedEdit.text())
        self.plotSingleEvent(self.events[eventCount - 1])
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
            if 0 < eventCount + count <= len(self.events):
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
    
    def onScatterPointsClicked(self, plot, points):
        """
        Callback for when a scatter plot points are clicked.
        Highlights the points and unhighlights previously selected points.
        """
        for p in self.lastScatterClicked:
            p.resetPen()
            # remove point we've already selected so we
            # can select points behind it.
            if p in points and len(points) > 1:
                points.remove(p)
#         print 'Points clicked:', points, plot
        for point in points:
            point.setPen('w', width=2)
            self.lastScatterClicked = [point]
            break # only take first point
        
        # Plot the new point clicked on the single event display
        filename, position = plot.getFileNameFromPosition(self.lastScatterClicked[0].eventPosition)
        
        h5file = tb.openFile(filename, mode='r')
        
        table = h5file.root.events.eventTable
        row = table[position]
        arrayRow = row['arrayRow']
        sampleRate = table.attrs.sampleRate
        eventLength = row['eventLength']
        rawPointsPerSide = row['rawPointsPerSide']
        n = eventLength+2*rawPointsPerSide
        
        arr = h5file.root.events.rawData[arrayRow]
        rawData = arr[:n]
        
        times = np.linspace(0.0, 1.0*n/sampleRate, n)
        
        self.plot_scatterselect.clear()
        self.plot_scatterselect.plot(times, rawData)
        
        h5file.close()
    
    def plotEventDatabaseAnalyses(self, filenames, params):
        '''
        Plots event statistics.  
        '''
        files = []
        counts = []
        eventCount = 0
        for filename in filenames:
            h5file = tb.openFile(filename, mode='r')
            files.append(h5file)
            count = h5file.root.events.eventTable.attrs.eventCount
            eventCount += count
            counts.append(count)
        
        currentBlockade = np.empty(eventCount)
        dwellTimes = np.empty(eventCount)
        for j, filex in enumerate(files):
            eventTable = filex.root.events.eventTable
            sample_rate = filex.root.events.eventTable.attrs.sampleRate
            for i, row in enumerate(eventTable):
                currentBlockade[j+i] = row['currentBlockage']
                dwellTimes[j+i] = row['eventLength'] / sample_rate
                
        color = params['color']
        newcolor = QtGui.QColor(color.red(), color.green(), color.blue(), 128)
                 
        bins = eventCount ** 0.5
        y_dt, x_dt = np.histogram(dwellTimes, bins=bins)        
        curve_dt = PlotCurveItem(x_dt, y_dt, stepMode=True, fillLevel=0, brush=newcolor)
        self.plot_eventdur.addItem(curve_dt)
        
        y_cb, x_cb = np.histogram(currentBlockade, bins=bins)        
        curve_cb = PlotCurveItem(-1.*x_cb, y_cb, stepMode=True, fillLevel=0, brush=newcolor)
        curve_cb.rotate(-90)
        self.plot_eventdepth.addItem(curve_cb)
        
        scatterItem = MyScatterPlotItem(size=10, pen=pg.mkPen(None), brush=newcolor, files=filenames, counts=counts)
        scatterItem.setData(dwellTimes, currentBlockade)
        self.plot_eventdur_eventdepth.addItem(scatterItem)
        scatterItem.sigClicked.connect(self.onScatterPointsClicked)
        
        for filex in files:
            filex.close()
        
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
        sample_rate = plot_options['datadict']['sample_rate']
        plot_range = plot_options['plot_range']
    
        n = len(data)
#         # If problem with input, just plot all the data
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
        
    def plotSingleEvent(self, event):
        '''
        Plots the event on the plot with 
        '''
        
        times, data, times2, levels2 = self.getEventAndLevelsData(event)
        
        self.plot_event_zoomed.clear()
        self.plot_event_zoomed.plot(x=times, y=data)
        self.plot_event_zoomed.plot(x=times2, y=levels2, pen=pg.mkPen('g'))
        
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
        
    def on_analyze_stop(self):
        self.cleanThreads()
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
        self.plotwid.clearEventItems()
        
        # Clear the current events
        del self.events[:]
        self.prev_concat_time = 0.
        
        filenames = [str(currItem.getFileName())]
        
        self.status_text.setText('Event Count: 0 Percent Done: 0')
        
        # Start analyzing data in new analyzethread.
        self.analyzethread = AnalyzeDataThread(filenames, parameters)
        self.analyzethread.dataReady.connect(self._analyze_data_thread_callback)
        self.threadPool.append(self.analyzethread)
        self.analyzethread.start()
        
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
        if 'Events' in results:
            singlePlot = False
            events = results['Events']
            if len(events) < 1:
                return
            elif len(self.events) < 1:
                # if this is our first time plotting events, include the single event plot!
                singlePlot = True
            self.events += events
            self.eventDisplayedEdit.setMaxLength(int(len(self.events) / 10) + 1)
            self.eventDisplayedEdit.setValidator(QtGui.QIntValidator(1, len(self.events)))
            self.eventCountText.setText('/' + str(len(self.events)))
            if self.plotToolBar.isPlotDuringChecked():
                self.plotEventsOnMainPlot(events)
                self.addEventsToConcatEventPlot(events)
            if singlePlot:
                self.eventDisplayedEdit.setText('1')
            self.app.processEvents()  
            self.analyzethread.readyForEvents = True
        if 'done' in results:
            if results['done']:
                self.stop_analyze_button.setEnabled(False)
                
    def cleanThreads(self):
        for w in self.threadPool:
            w.cancel()
#             w.wait()
            self.threadPool.remove(w)
        
def main():
    
    app = QtGui.QApplication(sys.argv)
    pixmap = QtGui.QPixmap('splash.png')
    splash = QtGui.QSplashScreen(pixmap, QtCore.Qt.WindowStaysOnTopHint)
    splash.show()
    _longImports(splash=splash, app=app)
    splash.showMessage("Creating main window...", alignment=QtCore.Qt.AlignBottom)
    app.processEvents()
    ex = MyMainWindow(app)
    ex.show()
    splash.finish(ex)
    app.exec_()
    ex.cleanThreads()

if __name__ == '__main__':
    main()

