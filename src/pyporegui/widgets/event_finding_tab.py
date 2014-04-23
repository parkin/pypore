from PySide import QtGui, QtCore
from numpy import linspace
import pyqtgraph as pg
from pyqtgraph.widgets.LayoutWidget import LayoutWidget

from pypore.event_finder import Parameters
from pypore.strategies.absolute_change_threshold_strategy import AbsoluteChangeThresholdStrategy
from pypore.strategies.adaptive_baseline_strategy import AdaptiveBaselineStrategy
from pypore.strategies.fixed_baseline_strategy import FixedBaselineStrategy
from pypore.strategies.noise_based_threshold_strategy import NoiseBasedThresholdStrategy
from pypore.strategies.percent_change_threshold_strategy import PercentChangeThresholdStrategy
from pyporegui.my_threads import AnalyzeDataThread, PlotThread
from pyporegui.graphicsItems.my_plot_item import MyPlotItem
from pyporegui.widgets.plot_tool_bar import PlotToolBar
from base_tabs import BaseQSplitterDataFile


__all__ = ['EventFindingTab']


# Note _ThreadManager must go first, otherwise its __init__ is never called
class EventFindingTab(BaseQSplitterDataFile):
    """
    A QtGui.QSplitter that contains event finding options on the left and a plot on the right.
    """

    def __init__(self, parent=None):
        """
        :param PySide.QtGui.QMainWindow parent: Parent main window (optional).
        """
        # Define the instance elements
        self.events = []  # holds the events from the most recent analysis run
        self.plot_widget = None
        self.p1 = None
        self.plot_tool_bar = None
        super(EventFindingTab, self).__init__(parent)

    def get_current_analysis_parameters(self):
        """
        Reads the current analysis parameters from the gui and returns the results in a dictionary. Returns
        dictionary entry 'error' with text of the error if one exists.

        :returns: DictType -- the event analysis parameters. These include:

            - 'error' - Text if there was an error

            OR

            - 'min_event_length'
            - 'max_event_length'
            - 'baseline_strategy'
            - 'baseline_filter_parameter'
            - 'baseline_current'

            etc...
        """

        threshold_type = baseline_type = None
        # Get Min_event length in microseconds
        try:
            min_event_length = float(self.min_event_length_edit.text())
        except ValueError:
            return {'error': 'Could not read float from Min Event Length text box.  Please fix.'}
        # Get Max Event Length in microseconds
        try:
            max_event_length = float(self.max_event_length_edit.text())
        except ValueError:
            return {'error': 'Could not read float from Max Event Length text box.  Please fix.'}
        if min_event_length >= max_event_length:
            return {'error': 'Min Event Length is greater than Max Event Length.  Please fix.'}

        baseline_type_str = str(self.baseline_type_combo.currentText())
        if baseline_type_str == 'Adaptive':
            try:
                baseline_filter_parameter = float(self.baseline_filter_parameter_edit.text())
            except ValueError:
                return {'error': 'Could not read float from Baseline Filter Parameter text box.  Please fix.'}
            try:
                variance_filter_parameter = float(self.variance_filter_parameter_edit.text())
            except ValueError:
                return {'error': 'Could not read float from Variance Filter Parameter text box.  Please fix.'}
            baseline_type = AdaptiveBaselineStrategy(baseline_filter_parameter=baseline_filter_parameter,
                                                     variance_filter_parameter=variance_filter_parameter)
        elif baseline_type_str == 'Fixed':
            try:
                baseline_current = float(self.baseline_current_edit.text())
                baseline_type = FixedBaselineStrategy(baseline=baseline_current)
            except ValueError:
                return {'error': 'Could not read float from Baseline Current text box.  Please fix.'}

        threshold_direction_str = str(self.threshold_direction_combo.currentText())
        detect_positive_events = (threshold_direction_str in ('Positive', 'Both'))
        detect_negative_events = (threshold_direction_str in ('Negative', 'Both'))

        threshold_type_str = str(self.threshold_type_combo.currentText())
        if threshold_type_str == 'Noise Based':
            try:
                start_stddev = float(self.threshold_stdev_start.text())
            except ValueError:
                return {'error': 'Could not read float from Start StdDev text box.  Please fix.'}
            try:
                end_stddev = float(self.threshold_stdev_end.text())
            except ValueError:
                return {'error': 'Could not read float from End StdDev text box.  Please fix.'}
            threshold_type = NoiseBasedThresholdStrategy(start_std_dev=start_stddev, end_std_dev=end_stddev)
        elif threshold_type_str == 'Absolute Change':
            try:
                absolute_change_start = float(self.absolute_change_start_edit.text())
            except ValueError:
                return {'error': 'Could not read float from Absolute Change Start.  Please fix.'}
            try:
                absolute_change_end = float(self.absolute_change_end_edit.text())
            except ValueError:
                return {'error': 'Could not read float from Absolute Change End.  Please fix.'}
            threshold_type = AbsoluteChangeThresholdStrategy(change_start=absolute_change_start,
                                                             change_end=absolute_change_end)
        elif threshold_type_str == 'Percent Change':
            try:
                percent_change_start = float(self.percentage_change_start_edit.text())
            except ValueError:
                return {'error': 'Could not read float from Percent Change Start text box.  Please fix.'}
            try:
                percent_change_end = float(self.percentage_change_end_edit.text())
            except ValueError:
                return {'error': 'Could not read float from Percent Change End text box.  Please fix.'}
            threshold_type = PercentChangeThresholdStrategy(percent_change_start=percent_change_start,
                                                            percent_change_end=percent_change_end)

        parameters = Parameters(min_event_length=min_event_length, max_event_length=max_event_length,
                                detect_positive_events=detect_positive_events,
                                detect_negative_events=detect_negative_events, baseline_strategy=baseline_type,
                                threshold_strategy=threshold_type)
        return parameters

    def plot_data(self, plot_options):
        """
        Plots waveform in datadict.
        :param DictType plot_options: Dictionary of plot options. Must contain:

        * Data at plot_options['data'][0]
        * sample_rate at plot_options['sample_rate']
        * plot_range at plot_options['plot_range']. This can be [start,stop], or
          'all' for 0:n.

        """
        # Read the first file, store data in dictionary
        data = plot_options['data'][0]
        sample_rate = plot_options['sample_rate']
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
        self._dispatch_process_events()

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
            self._dispatch_process_events()
            self.analyzethread.readyForEvents = True
        if 'done' in results:
            if results['done']:
                self.stop_analyze_button.setEnabled(False)

    def _on_analyze(self):
        """
        Searches for events in the file that is currently highlighted in the files list.
        """
        selected_items = self.file_list_widget.selectedItems()
        if len(selected_items) > 0:
            curr_items = selected_items
        else:
            return

        parameters = self.get_current_analysis_parameters()
        if isinstance(parameters, dict) and 'error' in parameters:
            self._dispatch_status_update(parameters['error'])
            return

        debug = self.debug_check_box.isChecked()

        # Clear the current events
        del self.events[:]
        # self.prev_concat_time = 0.

        file_names = [str(x.get_file_name()) for x in curr_items]

        self._dispatch_status_update("Event Count: 0 Percent Done: 0")

        # Start analyzing data in new analyzethread.
        self.analyzethread = AnalyzeDataThread(file_names, parameters, debug)
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
        Called when baseline_filter_parameter file list item is double clicked.
        Starts the plotting thread, which opens the file, parses data, then passes to plotData
        """
        # adding by emitting signal in different thread
        self._dispatch_status_update("Plotting...")
        decimates = self.plot_tool_bar.is_decimate_checked()
        thread = PlotThread(self.p1, filename=str(item.get_file_name()), decimate=decimates)
        thread.dataReady.connect(self._on_file_item_doubleclick_callback)
        self.add_thread(thread)
        thread.start()

    def _on_file_item_doubleclick_callback(self, results):
        if 'plot_options' in results:
            self.plot_data(results['plot_options'])
        if 'status_text' in results:
            self._dispatch_status_update(results['status_text'])
        if 'thread' in results:
            self.remove_thread(results['thread'])

    def _on_file_item_selection_changed(self):
        self.analyze_button.setEnabled(True)

    def _create_right_widget(self, parent=None):
        wig = pg.GraphicsLayoutWidget(parent)

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

    def open_data_files(self, file_names=None):
        are_files_opened = super(EventFindingTab, self).open_data_files(file_names)
        if are_files_opened:
            self.analyze_button.setEnabled(False)

    def _create_left_widget(self, parent=None):
        """
        Initializes everything in the options pane on the left side of the splitter.
        """
        scroll_area = QtGui.QScrollArea()
        scroll_area.setWidgetResizable(True)

        list_form_layout = super(EventFindingTab, self)._create_left_widget(parent)
        self.file_list_widget.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)

        # Other GUI controls
        #
        self.analyze_button = QtGui.QPushButton("&Find Events")
        self.connect(self.analyze_button, QtCore.SIGNAL('clicked()'), self._on_analyze)
        self.analyze_button.setEnabled(False)

        self.stop_analyze_button = QtGui.QPushButton("&Stop")
        self.connect(self.stop_analyze_button, QtCore.SIGNAL('clicked()'), self._on_analyze_stop)
        self.stop_analyze_button.setEnabled(False)

        self.debug_check_box = QtGui.QCheckBox()
        self.debug_check_box.setChecked(False)
        self.debug_check_box.setText('Debug')
        self.debug_check_box.setToolTip("When checked, extra data will be saved to the EventDatabase. This"
                                        " data includes the data, baseline, and thresholds at each datapoint.")

        # Analysis options
        self.min_event_length_edit = QtGui.QLineEdit()
        self.min_event_length_edit.setText('10.0')
        self.min_event_length_edit.setValidator(QtGui.QDoubleValidator(0, 1e12, 5, self.min_event_length_edit))
        self.max_event_length_edit = QtGui.QLineEdit()
        self.max_event_length_edit.setText('1000.0')
        self.max_event_length_edit.setValidator(QtGui.QDoubleValidator(0, 1e12, 5, self.max_event_length_edit))

        fixed_analysis_options = QtGui.QFormLayout()
        fixed_analysis_options.addRow('Min Event Length [us]:', self.min_event_length_edit)
        fixed_analysis_options.addRow('Max Event Length [us]:', self.max_event_length_edit)

        # Baseline options
        baseline_options = QtGui.QStackedLayout()
        self.baseline_type_combo = QtGui.QComboBox()
        self.baseline_type_combo.addItems(('Adaptive', 'Fixed'))
        self.baseline_type_combo.activated.connect(baseline_options.setCurrentIndex)

        adaptive_options_layout = QtGui.QFormLayout()
        self.baseline_filter_parameter_edit = QtGui.QLineEdit()
        self.baseline_filter_parameter_edit.setValidator(QtGui.QDoubleValidator(0, 10, 5, self.baseline_filter_parameter_edit))
        self.baseline_filter_parameter_edit.setText('0.93')
        adaptive_options_layout.addRow('Baseline Filter Parameter:', self.baseline_filter_parameter_edit)
        self.variance_filter_parameter_edit = QtGui.QLineEdit()
        self.variance_filter_parameter_edit.setValidator(QtGui.QDoubleValidator(0, 10, 5, self.variance_filter_parameter_edit))
        self.variance_filter_parameter_edit.setText('0.99')
        adaptive_options_layout.addRow('Variance Filter Parameter:', self.variance_filter_parameter_edit)
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
        vbox_left.addLayout(list_form_layout)
        vbox_left.addLayout(fixed_analysis_options)
        vbox_left.addLayout(baseline_form)
        vbox_left.addLayout(baseline_options)
        vbox_left.addLayout(threshold_form)
        vbox_left.addLayout(threshold_options)
        vbox_left.addWidget(self.debug_check_box)
        vbox_left.addLayout(hbox)

        vbox_left_widget = QtGui.QWidget()
        vbox_left_widget.setLayout(vbox_left)

        scroll_area.setWidget(vbox_left_widget)

        return scroll_area