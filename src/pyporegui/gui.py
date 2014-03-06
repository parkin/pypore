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

    global AnalyzeDataThread, PlotThread, pg, pgc, LayoutWidget, linspace, np, \
        EventAnalysisWidget, ed, EventFindingTab, EventViewingTab, EventAnalysisTab

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
    from widgets.event_viewing_tab import EventViewingTab
    from widgets.event_analysis_tab import EventAnalysisTab
    from widgets.event_finding_tab import EventFindingTab

    if update_splash:
        splash.showMessage("Compiling Cython imports... EventFinder", alignment=QtCore.Qt.AlignBottom)
        app.processEvents()
    from my_threads import AnalyzeDataThread, PlotThread

    if update_splash:
        splash.showMessage("Importing Event Database", alignment=QtCore.Qt.AlignBottom)
        app.processEvents()
    import pypore.filetypes.event_database as ed


class MyMainWindow(QtGui.QMainWindow):
    def __init__(self, app, parent=None):
        super(MyMainWindow, self).__init__()

        self.events = []  # holds the events from the most recent analysis run
        self.app = app

        pg.setConfigOption('leftButtonPan', False)

        self.open_dir = '../../data'

        self.thread_pool = []

        self.setWindowTitle('Translocation Event Analysis')

        self._create_menu()
        self._create_main_frame()
        self._create_status_bar()

    def open_files(self):
        """
        Opens file dialog box, adds names of files to open to list
        """
        file_names = QtGui.QFileDialog.getOpenFileNames(self,
                                                        'Open data file',
                                                        self.open_dir,
                                                        "All types(*.h5 *.hkd *.log *.mat);;"
                                                        "Pypore data files *.h5(*.h5);;"
                                                        "Heka files *.hkd(*.hkd);;"
                                                        "Chimera files *.log(*.log);;"
                                                        "Gabys files *.mat(*.mat)")[0]
        if len(file_names) > 0:
            self.event_finding_tab.open_files(file_names)

    def open_event_database(self):
        """
        Opens file dialog box, add names of event database files to open list
        """
        file_names = QtGui.QFileDialog.getOpenFileNames(self, 'Open event database', self.open_dir, '*.h5')[0]

        if len(file_names) > 0:
            self.event_viewer_tab.open_event_database(file_names)
            self.event_analysis_tab.open_event_database(file_names)

    def set_status(self, text):
        """
        Sets the status text.

        :param StringType text: Text to display in the status bar.
        """
        self.status_text.setText(text)

    def _process_events(self):
        self.app.processEvents()

    def _create_main_frame(self):
        """
        Helper to initialize the main gui frame.
        """
        self.event_finding_tab = EventFindingTab(self)
        self.event_finding_tab.set_on_status_update_callback(self.set_status)
        self.event_finding_tab.set_process_events_callback(self._process_events)

        self.event_viewer_tab = EventViewingTab(self)

        self.event_analysis_tab = EventAnalysisTab(self)

        # Layout holding everything        
        self.main_tabwig = QtGui.QTabWidget()
        self.main_tabwig.addTab(self.event_finding_tab, 'Event Finding')
        self.main_tabwig.addTab(self.event_viewer_tab, 'Event View')
        self.main_tabwig.addTab(self.event_analysis_tab, 'Event Analysis')
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

        namespace = {'np': np, 'pg': pg, 'ed': ed, 'currentPlot': self.event_finding_tab.plot_widget}
        self.console = pgc.ConsoleWidget(namespace=namespace, text=text)

        frame = QtGui.QSplitter()
        frame.setOrientation(QtCore.Qt.Vertical)
        frame.addWidget(self.main_tabwig)
        frame.addWidget(self.console)

        self.setCentralWidget(frame)

    def _create_status_bar(self):
        """
        Creates filter_parameter status bar with filter_parameter text widget.
        """
        self.status_text = QtGui.QLabel("")
        self.statusBar().addWidget(self.status_text, 1)

    def _create_menu(self):
        """
        Creates File menu with Open
        """
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

    @classmethod
    def add_actions(cls, target, actions):
        for action in actions:
            if action is None:
                target.addSeparator()
            else:
                target.addAction(action)

    def create_action(self, text, slot=None, shortcut=None,
                      icon=None, tip=None, checkable=False,
                      signal="triggered()"):
        """
        Create a :py:class:`QtGui.QAction`.
        :param text: Text to show in the file menu
        """
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

    def clean_threads(self):
        for w in self.thread_pool:
            w.cancel()
            #             w.wait()
            self.thread_pool.remove(w)


def main():
    app = QtGui.QApplication(sys.argv)
    pix_map = QtGui.QPixmap('splash.png')
    splash = QtGui.QSplashScreen(pix_map, QtCore.Qt.WindowStaysOnTopHint)
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
else:
    # If we are running from a tests, name != main, and we'll need to import the long imports now.
    _long_imports()
