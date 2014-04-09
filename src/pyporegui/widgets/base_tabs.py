from PySide import QtGui
from pypore.data_file_opener import prepare_data_file
from pypore.i_o import get_reader_from_filename
from pyporegui._thread_manager import _ThreadManager
from pyporegui.file_items import DataFileListItem, FileListItem


class BaseQSplitter(_ThreadManager, QtGui.QSplitter):
    def __init__(self, parent):
        super(BaseQSplitter, self).__init__(parent)

        self.on_status_update_callback = None
        self.process_events_callback = None

        left_widget = self._create_left_widget(parent)
        right_widget = self._create_right_widget(parent)

        self.addWidget(left_widget)
        self.addWidget(right_widget)

    def set_process_events_callback(self, callback):
        """
        Sets a callback for when the EventFindingTab requests app.processEvents

        :param MethodType callback:
        """
        self.process_events_callback = callback

    def _dispatch_process_events(self):
        """
        Calls the process_events_callback if it is not None.
        """
        if self.process_events_callback is not None:
            self.process_events_callback()

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


class BaseQSplitterDataFile(BaseQSplitter):
    def __init__(self, parent):
        super(BaseQSplitterDataFile, self).__init__(parent)

    def open_data_files(self, file_names=None):
        """
        Analyzes the files for correctness, then adds them to the list widget.

        :param ListType<StringType> file_names: The file names to be included in the list widget. If not included,
                                                this function will use a QtGui.QFileDialog.getOpenFileNames to open
                                                files.
        :returns: BooleanType -- **True** if files were opened, **False** otherwise.
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
            self.file_list_widget.clear()
        else:
            return
        are_files_opened = False
        open_dir = None
        for w in file_names:
            reader = get_reader_from_filename(w)
            # if 'error' in params:
            # TODO implement error handling in readers
            # pass
            # else:
            reader.close()
            are_files_opened = True
            item = FileListItem(w)
            open_dir = item.get_directory()
            self.file_list_widget.addItem(item)

        return are_files_opened

    def _create_list_form(self):
        self.file_list_widget = QtGui.QListWidget()
        self.file_list_widget.setMaximumHeight(100)

        self.file_list_widget.itemSelectionChanged.connect(self._on_file_item_selection_changed)
        self.file_list_widget.itemDoubleClicked.connect(self._on_file_item_doubleclick)
        self.file_list_widget.setMaximumHeight(100)

        file_options = QtGui.QFormLayout()
        file_options.addRow('Data Files:', self.file_list_widget)

        return file_options

    def _create_left_widget(self, parent=None):
        return self._create_list_form()
