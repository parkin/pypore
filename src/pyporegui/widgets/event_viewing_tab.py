from PySide import QtGui, QtCore
import numpy as np
import pyqtgraph as pg
from pyqtgraph.widgets.LayoutWidget import LayoutWidget
from pypore.filetypes import event_database as eD
from pyporegui._thread_manager import _ThreadManager
from pyporegui.graphicsItems.my_plot_item import MyPlotItem
from pyporegui.file_items import FileListItem
from pyporegui.graphicsItems.path_item import PathItem

__all__ = ['EventViewingTab']


class EventViewingTab(_ThreadManager, QtGui.QSplitter):
    """
    A QtGui.Splitter that contains a file opener list on the left and plots on the right.
    """

    def __init__(self, parent=None):
        """
        :param PySide.QtGui.QMainWindow parent: Parent main window (optional).
        """
        super(EventViewingTab, self).__init__(parent)

        self._parent = parent

        self.open_directory_changed_callback = None

        options = self._create_event_viewer_options()
        plots = self._create_event_viewer_plot_widget()

        # Put everything in baseline_filter_parameter scroll area
        scroll_plots = QtGui.QScrollArea()
        scroll_plots.setWidgetResizable(True)

        scroll_plots.setWidget(plots)

        self.addWidget(options)
        self.addWidget(scroll_plots)

    def open_event_databases(self, file_names=None):
        """
        Adds the files to the list widget.

        :param ListType<StringType> file_names: (Optional) List of file names to be added to the list widget. If not
                                                included, then a QtGui.QFileDialog will be opened to select files.
        """
        if file_names is None:
            file_names = QtGui.QFileDialog.getOpenFileNames(self, 'Open event database', '.', '*.h5')[0]

        if len(file_names) > 0:
            self.eventview_list_widget.clear()
        else:
            return
        for w in file_names:
            item = FileListItem(w)
            self.eventview_list_widget.addItem(item)

    def _create_event_viewer_options(self):
        scroll_area = QtGui.QScrollArea()
        scroll_area.setWidgetResizable(True)

        # Create baseline_filter_parameter list for files want to analyze
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

        h5file = eD.open_file(item.get_file_name())

        event_count = h5file.get_event_count()

        if h5file.is_debug():
            self.plot_debug(h5file)

        h5file.close()

        self.event_display_edit.setMaxLength(int(event_count / 10) + 1)
        self.event_display_edit.setValidator(QtGui.QIntValidator(1, event_count, self.event_display_edit))
        self.event_count_text.setText('/' + str(event_count))
        self.event_display_edit.setText('')
        self.event_display_edit.setText('1')

    def plot_debug(self, event_database):
        """
        Plots the data, baseline, and thresholds of the debug group in the event_database, if they exist,
        in the main plot.

        :param event_database: An already open\
                :class:`EventDatabase <pypore.filetypes.event_database.EventDatabase>`.
        """
        if not event_database.is_debug():
            return

        self.eventview_plotwid.clear()

        sample_rate = event_database.get_sample_rate()

        # TODO remove the step_size.
        step_size = 1000

        data = event_database.root.debug.data[0][::step_size]

        data_size = data.size
        times = np.linspace(0, data_size *1.0/sample_rate, data_size)
        item = PathItem(times, data)
        item.setPen(pg.mkPen('w'))
        self.eventview_plotwid.addItem(item)

        baseline = event_database.root.debug.baseline[0][::step_size]
        item = PathItem(times, baseline)
        item.setPen(pg.mkPen('y'))
        self.eventview_plotwid.addItem(item)

        threshold_p = event_database.root.debug.threshold_positive[0][::step_size]
        item = PathItem(times, threshold_p)
        item.setPen(pg.mkPen('g'))
        self.eventview_plotwid.addItem(item)

        threshold_n = event_database.root.debug.threshold_negative[0][::step_size]
        item = PathItem(times, threshold_n)
        item.setPen(pg.mkPen('g'))
        self.eventview_plotwid.addItem(item)

    def plot_single_events(self, event):
        """
        Plots the event on the plot with
        """
        h5file = eD.open_file(self.event_view_item.get_file_name(), mode='r')

        event_count = h5file.get_event_count()

        for i in xrange(3):
            for j in xrange(3):
                pos = 3 * i + j
                if pos + event >= event_count or pos + event < 0:
                    self.eventviewer_plots[pos].clear()
                    self.eventviewer_plots[pos].setTitle('')
                else:
                    self.plot_single_event(h5file, event + pos, self.eventviewer_plots[pos])
                    self.eventviewer_plots[pos].setTitle('Event ' + str(event + pos + 1))

        h5file.close()

    def plot_single_event(self, h5file, position, plot):
        sample_rate = h5file.get_sample_rate()
        row = h5file.get_event_row(position)
        event_length = row['event_length']
        raw_points_per_side = row['raw_points_per_side']

        raw_data = h5file.get_raw_data_at(position)

        n = len(raw_data)

        times = np.linspace(0.0, 1.0 * n / sample_rate, n)

        plot.clear()
        plot.plot(times, raw_data)
        # plot the event points in yellow
        plot.plot(times[raw_points_per_side:raw_points_per_side + event_length],
                  raw_data[raw_points_per_side:raw_points_per_side + event_length], pen='y')

        # Plot the cusum levels
        n_levels = row['n_levels']
        baseline = row['baseline']
        # left, start-1, start,
        levels = h5file.get_levels_at(position)
        indices = h5file.get_level_lengths_at(position)

        level_times = np.zeros(2 * n_levels + 4)
        level_values = np.zeros(2 * n_levels + 4)

        level_times[1] = 1.0 * (raw_points_per_side - 1) / sample_rate
        level_values[0] = level_values[1] = baseline
        i = 0
        length = 0
        for i in xrange(n_levels):
            level_times[2 * i + 2] = times[raw_points_per_side] + 1.0 * length / sample_rate
            level_values[2 * i + 2] = levels[i]
            level_times[2 * i + 3] = times[raw_points_per_side] + 1.0 * (length + indices[i]) / sample_rate
            level_values[2 * i + 3] = levels[i]
            length += indices[i]
        i += 1
        level_times[2 * i + 2] = times[raw_points_per_side + event_length]
        level_times[2 * i + 3] = times[n - 1]
        level_values[2 * i + 2] = level_values[2 * i + 3] = baseline

        plot.plot(level_times, level_values, pen='g')

    def previous_clicked(self):
        self.move_event_display_by(-1 * len(self.eventviewer_plots))

    def next_clicked(self):
        self.move_event_display_by(len(self.eventviewer_plots))

    def move_event_display_by(self, count):
        """
        Changes the event displayed on the event display plot to
        current value + count
        """
        h5_event_count = 0
        try:
            h5file = eD.open_file(self.event_view_item.get_file_name())
            h5_event_count = h5file.get_event_count()
            h5file.close()
        except:
            return
        try:
            event_count = int(self.event_display_edit.text())
            if 0 < event_count + count <= h5_event_count:
                self.event_display_edit.setText(str(event_count + count))
        except ValueError:
            # if we can't parse the event display text but there are events,
            # just set to zero
            if h5_event_count > 0:
                self.event_display_edit.setText('1')

    def _event_display_edit_on_change(self, text):
        if len(text) < 1:
            return
        position = int(self.event_display_edit.text())
        self.plot_single_events(position - 1)
        return

    def _create_event_viewer_plot_widget(self):
        wig = pg.GraphicsLayoutWidget()
        wig2 = pg.GraphicsLayoutWidget()

        # Main plot
        self.eventview_plotwid = MyPlotItem(title='Current Trace', name='Plot')
        wig.addItem(self.eventview_plotwid)
        self.eventview_plotwid.enableAutoRange('xy', False)

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

        event_select_toolbar = QtGui.QToolBar(self)
        if self._parent is not None:
            self._parent.addToolBar(event_select_toolbar)

        button_previous = QtGui.QPushButton(event_select_toolbar)
        button_previous.setText("Previous")
        button_previous.clicked.connect(self.previous_clicked)
        event_select_toolbar.addWidget(button_previous)

        self.event_display_edit = QtGui.QLineEdit()
        self.event_display_edit.setText('0')
        self.event_display_edit.setMaxLength(1)
        self.event_display_edit.setValidator(QtGui.QIntValidator(0, 0, self.event_display_edit))
        self.event_display_edit.textChanged.connect(self._event_display_edit_on_change)
        event_select_toolbar.addWidget(self.event_display_edit)

        self.event_count_text = QtGui.QLabel()
        self.event_count_text.setText('/' + str(0))
        event_select_toolbar.addWidget(self.event_count_text)

        button_previous = QtGui.QPushButton(event_select_toolbar)
        button_previous.setText("Next")
        button_previous.clicked.connect(self.next_clicked)
        event_select_toolbar.addWidget(button_previous)

        frame = QtGui.QSplitter()
        frame.setOrientation(QtCore.Qt.Vertical)
        frame.addWidget(wig)
        frame.addWidget(wig2)

        event_finder_plots_layout = LayoutWidget()
        # event_finder_plots_layout.addWidget(self.plotToolBar, row=1, col=0, colspan=3)
        event_finder_plots_layout.addWidget(frame, row=2, col=0, colspan=3)
        event_finder_plots_layout.addWidget(event_select_toolbar, row=5, col=0, colspan=3)

        return event_finder_plots_layout


