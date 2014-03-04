from PySide import QtGui, QtCore
from numpy import linspace
import pyqtgraph as pg
from pyqtgraph.widgets.LayoutWidget import LayoutWidget

from pypore.dataFileOpener import prepareDataFile

from pyporegui._ThreadManager import _ThreadManager
from pyporegui.MyThreads import AnalyzeDataThread, PlotThread
from pyporegui.graphicsItems.MyPlotItem import MyPlotItem
from pyporegui.views import DataFileListItem
from pyporegui.widgets.PlotToolBar import PlotToolBar

__all__ = ['EventFindingTab']


# Note _ThreadManager must go first, otherwise its __init__ is never called
class EventFindingTab(_ThreadManager, QtGui.QSplitter):
    """
    A QtGui.QSplitter that contains event finding options on the left and a plot on the right.
    """

    def __init__(self, parent=None):
        """
        :param PySide.QtGui.QMainWindow parent: Parent main window (optional).
        """
        super(EventFindingTab, self).__init__(parent)

        # Define the instance elements
        self.events = []  # holds the events from the most recent analysis run

        self.on_status_update_callback = None
        self.process_events_callback = None
        self.plot_widget = None
        self.p1 = None
        self.plot_tool_bar = None

        # Set up the widgets

        options = self._create_event_finding_options()
        plots = self._create_event_finder_plots_widget(parent)

        # Put everything in filter_parameter scroll area
        scroll_options = QtGui.QScrollArea()
        scroll_plots = QtGui.QScrollArea()
        scroll_options.setWidgetResizable(True)
        scroll_plots.setWidgetResizable(True)

        scroll_options.setWidget(options)
        scroll_plots.setWidget(plots)

        self.addWidget(scroll_options)
        self.addWidget(scroll_plots)

    def get_current_analysis_parameters(self):
        """
        Reads the current analysis parameters from the gui and returns the results in a dictionary. Returns
        dictionary entry 'error' with text of the error if one exists.

        :returns: DictType -- the event analysis parameters. These include:
                -- 'error' - Text if there was an error
                OR
                -- 'min_event_length'
                -- 'max_event_length'
                -- 'baseline_type'
                -- 'filter_parameter'
                -- 'baseline_current'
                etc...
        """
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

    def open_files(self, file_names=None):
        """
        Analyzes the files for correctness, then adds them to the list widget.

        :param ListType<StringType> file_names: The file names to be included in the list widget. If not included,
                                                this function will use a QtGui.QFileDialog.getOpenFileNames to open
                                                files.
        """
        if file_names is None:
            file_names = QtGui.QFileDialog.getOpenFileNames(self,
                                                            'Open data file',
                                                            '.',
                                                            "All types(*.h5 *.hkd *.log *.mat);;"
                                                            "Pypore data files *.h5(*.h5);;"
                                                            "Heka files *.hkd(*.hkd);;"
                                                            "Chimera files *.log(*.log);;Gabys files *.mat(*.mat)")[0]
        if len(file_names) > 0:
            self.list_widget.clear()
        else:
            return
        are_files_opened = False
        open_dir = None
        for w in file_names:
            f, params = prepareDataFile(w)
            if 'error' in params:
                self.status_text.setText(params['error'])
            else:
                are_files_opened = True
                f.close()
                item = DataFileListItem(w, params)
                open_dir = item.getDirectory()
                self.list_widget.addItem(item)

        if are_files_opened:
            self.analyze_button.setEnabled(False)

    def plot_data(self, plot_options):
        """
        Plots waveform in datadict
        :param DictType plot_options: Dictionary of plot options. Must contain:
                            - Data at plot_options['datadict']['data'][0]
                            - sample_rate at plot_options['datadict']['sample_rate']
                            - plot_range at plot_options['datadict']['plot_range']. This can be [start,stop], or
                                'all' for 0:n.
        """
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

        ts = 1 / sample_rate

        times = linspace(ts * plot_range[0], ts * plot_range[1], n)
        y_data = data[plot_range[0]:(plot_range[1] + 1)]

        self.plot_widget.clear_event_items()
        self.p1.setData(x=times, y=y_data)
        self.plot_widget.autoRange()
        if self.process_events_callback is not None:
            self.process_events_callback()

    def set_process_events_callback(self, callback):
        """
        Sets a callback for when the EventFindingTab requests app.processEvents

        :param MethodType callback:
        """
        self.process_events_callback = callback

    def set_on_status_update_callback(self, callback):
        """
        Sets a callback for when the EventFinderTab's status is updated. The status is a String of information
        about the current state of the EventFinderTab.

        :param MethodType callback: Callback method for when the EventFinderTab's status is updated.
                                    This callback must accept one string parameter.
        """
        self.on_status_update_callback = callback

    def _dispatch_status_update(self, text):
        """
        Dispatches text to the on_status_update_callback if the on_status_update_callback is not None.
        """
        if self.on_status_update_callback is not None:
            self.on_status_update_callback(text)

    def _analyze_data_thread_callback(self, results):
        """
        Callback for updates from the AnalyzeDataThread.
        """
        if 'status_text' in results:
            self._dispatch_status_update(results['status_text'])
        if 'Events' in results:
            single_plot = False
            events = results['Events']
            if len(events) < 1:
                return
            elif len(self.events) < 1:
                # if this is our first time plotting events, include the single event plot!
                single_plot = True
            self.events += events
            self.event_display_edit.setMaxLength(int(len(self.events) / 10) + 1)
            self.event_display_edit.setValidator(QtGui.QIntValidator(1, len(self.events), self.event_display_edit))
            self.eventCountText.setText('/' + str(len(self.events)))
            if self.plot_tool_bar.is_plot_during_checked():
                self.plotEventsOnMainPlot(events)
                self.addEventsToConcatEventPlot(events)
            if single_plot:
                self.event_display_edit.setText('1')
            self.app.processEvents()
            self.analyzethread.readyForEvents = True
        if 'done' in results:
            if results['done']:
                self.stop_analyze_button.setEnabled(False)

    def _on_analyze(self):
        """
        Searches for events in the file that is currently highlighted in the files list.
        """
        selected_items = self.list_widget.selectedItems()
        if len(selected_items) > 0:
            curr_item = selected_items[0]
        else:
            return

        parameters = self.get_current_analysis_parameters()
        if 'error' in parameters:
            self.status_text.setText(parameters['error'])
            return

        # Clear the current events
        del self.events[:]
        # self.prev_concat_time = 0.

        file_names = [str(curr_item.getFileName())]

        if self.on_status_update_callback is not None:
            self.on_status_update_callback("Event Count: 0 Percent Done: 0")

        # Start analyzing data in new analyzethread.
        self.analyzethread = AnalyzeDataThread(file_names, parameters)
        self.analyzethread.dataReady.connect(self._analyze_data_thread_callback)
        self.add_thread(self.analyzethread)
        self.analyzethread.start()

        self.stop_analyze_button.setEnabled(True)

    def _on_analyze_stop(self):
        """
        Called when the user clicks the Stop button.
        """
        self.clean_threads()
        self.stop_analyze_button.setEnabled(False)
        self._dispatch_status_update("Analyze aborted.")

    def _on_file_item_doubleclick(self, item):
        """
        Called when filter_parameter file list item is double clicked.
        Starts the plotting thread, which opens the file, parses data, then passes to plotData
        """
        # adding by emitting signal in different thread
        if self.on_status_update_callback is not None:
            self.on_status_update_callback('Plotting...')
        decimates = self.plot_tool_bar.is_decimate_checked()
        thread = PlotThread(self.p1, filename=str(item.getFileName()), decimate=decimates)
        thread.dataReady.connect(self._on_file_item_doubleclick_callback)
        self.add_thread(thread)
        thread.start()

    def _on_file_item_doubleclick_callback(self, results):
        if 'plot_options' in results:
            self.plot_data(results['plot_options'])
        if 'status_text' in results and self.on_status_update_callback is not None:
            self.on_status_update_callback(results['status_text'])
        if 'thread' in results:
            self.remove_thread(results['thread'])

    def _on_file_item_selection_changed(self):
        self.analyze_button.setEnabled(True)

    def _create_event_finder_plots_widget(self, parent=None):
        wig = pg.GraphicsLayoutWidget()

        # Main plot
        self.plot_widget = MyPlotItem(title='Current Trace', name='Plot')
        wig.addItem(self.plot_widget)
        self.plot_widget.enableAutoRange('xy', False)
        self.p1 = self.plot_widget.plot()  # create an empty plot curve to be filled later

        # Tool bar for main plot.  Contains zoom button and different checkboxes
        self.plot_tool_bar = PlotToolBar(self)
        if not parent is None:
            parent.addToolBar(self.plot_tool_bar)

        event_finder_plots_layout = LayoutWidget()
        event_finder_plots_layout.addWidget(self.plot_tool_bar, row=1, col=0, colspan=3)
        event_finder_plots_layout.addWidget(wig, row=2, col=0, colspan=3)

        return event_finder_plots_layout

    def _create_event_finding_options(self):
        """
        Initializes everything in the options pane on the left side of the splitter.
        """
        scroll_area = QtGui.QScrollArea()
        scroll_area.setWidgetResizable(True)

        # Create filter_parameter list for files want to analyze
        self.list_widget = QtGui.QListWidget()
        self.list_widget.itemSelectionChanged.connect(self._on_file_item_selection_changed)
        self.list_widget.itemDoubleClicked.connect(self._on_file_item_doubleclick)
        self.list_widget.setMaximumHeight(100)

        # Other GUI controls
        #
        self.analyze_button = QtGui.QPushButton("&Find Events")
        self.connect(self.analyze_button, QtCore.SIGNAL('clicked()'), self._on_analyze)
        self.analyze_button.setEnabled(False)

        self.stop_analyze_button = QtGui.QPushButton("&Stop")
        self.connect(self.stop_analyze_button, QtCore.SIGNAL('clicked()'), self._on_analyze_stop)
        self.stop_analyze_button.setEnabled(False)

        # Analysis options
        self.min_event_length_edit = QtGui.QLineEdit()
        self.min_event_length_edit.setText('10.0')
        self.min_event_length_edit.setValidator(QtGui.QDoubleValidator(0, 1e12, 5, self.min_event_length_edit))
        self.max_event_length_edit = QtGui.QLineEdit()
        self.max_event_length_edit.setText('1000.0')
        self.max_event_length_edit.setValidator(QtGui.QDoubleValidator(0, 1e12, 5, self.max_event_length_edit))
        fixed_analysis_options = QtGui.QFormLayout()
        fixed_analysis_options.addRow('Data Files:', self.list_widget)
        fixed_analysis_options.addRow('Min Event Length [us]:', self.min_event_length_edit)
        fixed_analysis_options.addRow('Max Event Length [us]:', self.max_event_length_edit)

        # Baseline options
        baseline_options = QtGui.QStackedLayout()
        self.baseline_type_combo = QtGui.QComboBox()
        self.baseline_type_combo.addItems(('Adaptive', 'Fixed'))
        self.baseline_type_combo.activated.connect(baseline_options.setCurrentIndex)

        adaptive_options_layout = QtGui.QFormLayout()
        self.filter_parameter_edit = QtGui.QLineEdit()
        self.filter_parameter_edit.setValidator(QtGui.QDoubleValidator(0, 10, 5, self.filter_parameter_edit))
        self.filter_parameter_edit.setText('0.93')
        adaptive_options_layout.addRow('Filter Parameter \'a\':', self.filter_parameter_edit)
        # need to cast to widget to add to QStackedLayout
        adaptive_options_widget = QtGui.QWidget()
        adaptive_options_widget.setLayout(adaptive_options_layout)

        choose_baseline_btn = QtGui.QPushButton('Baseline:')
        choose_baseline_btn.setToolTip('Click to choose the baseline from the plot.')

        fixed_options_layout = QtGui.QFormLayout()
        self.baseline_current_edit = QtGui.QLineEdit()
        self.baseline_current_edit.setValidator(QtGui.QDoubleValidator(-9999, 9999, 9, self.baseline_current_edit))
        self.baseline_current_edit.setText('0.0')
        fixed_options_layout.addRow(choose_baseline_btn, self.baseline_current_edit)
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
        self.threshold_stdev_start.setValidator(QtGui.QDoubleValidator(-9999, 9999, 4, self.threshold_stdev_start))
        self.threshold_stdev_start.setText('5.0')
        noise_based_options_layout.addRow('Start StdDev:', self.threshold_stdev_start)
        self.threshold_stdev_end = QtGui.QLineEdit()
        self.threshold_stdev_end.setValidator(QtGui.QDoubleValidator(-9999, 9999, 4, self.threshold_stdev_end))
        self.threshold_stdev_end.setText('1.0')
        noise_based_options_layout.addRow('End StdDev:', self.threshold_stdev_end)

        absolute_drop_options_layout = QtGui.QFormLayout()
        self.absolute_change_start_edit = QtGui.QLineEdit()
        self.absolute_change_start_edit.setValidator(
            QtGui.QDoubleValidator(-9999, 9999, 9, self.absolute_change_start_edit))
        self.absolute_change_start_edit.setText('0.1')
        absolute_drop_options_layout.addRow('Absolute Change Start [uA]:', self.absolute_change_start_edit)
        self.absolute_change_end_edit = QtGui.QLineEdit()
        self.absolute_change_end_edit.setValidator(
            QtGui.QDoubleValidator(-9999, 9999, 9, self.absolute_change_end_edit))
        self.absolute_change_end_edit.setText('0.0')
        absolute_drop_options_layout.addRow('Absolute Change End [uA]:', self.absolute_change_end_edit)

        percentage_change_options_layout = QtGui.QFormLayout()
        self.percentage_change_start_edit = QtGui.QLineEdit()
        self.percentage_change_start_edit.setValidator(
            QtGui.QDoubleValidator(0, 9999, 5, self.percentage_change_start_edit))
        self.percentage_change_start_edit.setText('10.0')
        percentage_change_options_layout.addRow('Percent Change Start:', self.percentage_change_start_edit)
        self.percentage_change_end_edit = QtGui.QLineEdit()
        self.percentage_change_end_edit.setValidator(
            QtGui.QDoubleValidator(0, 9999, 5, self.percentage_change_end_edit))
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

        for w in [self.analyze_button, self.stop_analyze_button]:
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

        scroll_area.setWidget(vbox_left_widget)

        return scroll_area