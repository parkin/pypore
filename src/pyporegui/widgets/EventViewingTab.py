from PySide import QtGui, QtCore
import numpy as np
import pyqtgraph as pg
from pyqtgraph.widgets.LayoutWidget import LayoutWidget
from pypore import eventDatabase as eD
from pyporegui._ThreadManager import _ThreadManager
from pyporegui.graphicsItems.MyPlotItem import MyPlotItem
from pyporegui.FileItems import FileListItem

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

        # Put everything in filter_parameter scroll area
        scroll_options = QtGui.QScrollArea()
        scroll_plots = QtGui.QScrollArea()
        scroll_options.setWidgetResizable(True)
        scroll_plots.setWidgetResizable(True)

        scroll_options.setWidget(options)
        scroll_plots.setWidget(plots)

        self.addWidget(scroll_options)
        self.addWidget(scroll_plots)

    def open_event_database(self, file_names=None):
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

        h5file = eD.openFile(item.get_file_name())

        event_count = h5file.getEventCount()

        h5file.close()

        self.event_display_edit.setMaxLength(int(event_count / 10) + 1)
        self.event_display_edit.setValidator(QtGui.QIntValidator(1, event_count, self.event_display_edit))
        self.event_count_text.setText('/' + str(event_count))
        self.event_display_edit.setText('')
        self.event_display_edit.setText('1')

    def plotSingleEvents(self, event):
        '''
        Plots the event on the plot with
        '''
        h5file = eD.openFile(self.event_view_item.get_file_name(), mode='r')

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

    def previous_clicked(self):
        self.moveEventDisplayBy(-1 * len(self.eventviewer_plots))

    def next_clicked(self):
        self.moveEventDisplayBy(len(self.eventviewer_plots))

    def moveEventDisplayBy(self, count):
        '''
        Changes the event displayed on the event display plot to
        current value + count
        '''
        h5eventCount = 0
        try:
            h5file = eD.openFile(self.event_view_item.get_file_name())
            h5eventCount = h5file.getEventCount()
            h5file.close()
        except:
            return
        try:
            eventCount = int(self.event_display_edit.text())
            if 0 < eventCount + count <= h5eventCount:
                self.event_display_edit.setText(str(eventCount + count))
        except ValueError:
            # if we can't parse the event display text but there are events,
            # just set to zero
            if h5eventCount > 0:
                self.event_display_edit.setText('1')

    def _eventDisplayEditOnChange(self, text):
        if len(text) < 1:
            return
        position = int(self.event_display_edit.text())
        self.plotSingleEvents(position - 1)
        return

    def _create_event_viewer_plot_widget(self):
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
        self.event_display_edit.textChanged.connect(self._eventDisplayEditOnChange)
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


