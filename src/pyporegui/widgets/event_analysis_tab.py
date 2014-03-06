from PySide import QtGui
from pyporegui._thread_manager import _ThreadManager
from pyporegui.file_items import FilterListItem, FileListItem
from pyporegui.widgets.event_analysis_plot_widget import EventAnalysisPlotWidget

__all__ = ['EventAnalysisTab']


class EventAnalysisTab(_ThreadManager, QtGui.QSplitter):
    """
    """

    def __init__(self, parent=None):
        """
        :param PySide.QtGui.QMainWindow parent: Parent window of this tab (optional).
        """
        super(EventAnalysisTab, self).__init__(parent)
        self._parent = parent

        options = self._create_event_analysis_options()
        self.eventAnalysisWidget = EventAnalysisPlotWidget()

        # Put everything in filter_parameter scroll area
        scroll_options = QtGui.QScrollArea()
        scroll_plots = QtGui.QScrollArea()
        scroll_options.setWidgetResizable(True)
        scroll_plots.setWidgetResizable(True)

        scroll_options.setWidget(options)
        scroll_plots.setWidget(self.eventAnalysisWidget)

        self.addWidget(scroll_options)
        self.addWidget(scroll_plots)

    def color_picker_btn_clicked(self):
        col = QtGui.QColorDialog.getColor(initial=self.event_color)

        if col.isValid():
            self.event_color = col
            self.frm.setStyleSheet("QWidget { background-color: %s }"
                                   % col.name())

    def add_filter_clicked(self):
        items = self.list_event_widget.selectedItems()
        if items is None or len(items) < 1:
            return

        params = self._get_current_event_analysis_params()

        file_names = []

        for item in items:
            file_names.append(item.get_file_name())

        item = FilterListItem(file_names, **params)
        self.listFilterWidget.addItem(item)

        self.eventAnalysisWidget.add_selections(file_names, params)

    def _get_current_event_analysis_params(self):
        params = {'color': self.event_color}
        return params

    def open_event_database(self, file_names=None):
        """
        Adds the files to the list widget.

        :param ListType<StringType> file_names: (Optional) List of file names to be added to the list widget. If not
                                                included, then a QtGui.QFileDialog will be opened to select files.
        """
        if file_names is None:
            file_names = QtGui.QFileDialog.getOpenFileNames(self, 'Open event database', '.', '*.h5')[0]

        if len(file_names) > 0:
            self.list_event_widget.clear()
        else:
            return
        for w in file_names:
            item = FileListItem(w)
            self.list_event_widget.addItem(item)

    def remove_filter_clicked(self):
        items = self.listFilterWidget.selectedItems()
        for item in items:
            index = self.listFilterWidget.indexFromItem(item).row()
            self.eventAnalysisWidget.removeFilter(index)
            self.listFilterWidget.takeItem(index)

    def _on_event_file_selection_changed(self):
        """
        Called when the user clicks a new file in the file list.
        """
        self.btnAddFilter.setEnabled(True)

    def _create_event_analysis_options(self):
        """
        Initializes the analysis options on the left side of the tab.
        """
        scroll_area = QtGui.QScrollArea()
        scroll_area.setWidgetResizable(True)

        # Create filter_parameter list for files want to analyze
        self.list_event_widget = QtGui.QListWidget()
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