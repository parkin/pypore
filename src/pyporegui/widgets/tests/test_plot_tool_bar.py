import unittest
from PySide import QtGui
from PySide.QtGui import QCheckBox
from pyporegui.widgets.plot_tool_bar import PlotToolBar

# This class needs a QApplication instance
if QtGui.qApp is None:
    QtGui.QApplication([])


class TestPlotToolBar(unittest.TestCase):

    def test_plot_tool_bar_initial_state(self):
        toolbar = PlotToolBar()
        self.assertTrue(toolbar.is_decimate_checked())
        self.assertTrue(toolbar.is_plot_during_checked())
        widget_list = toolbar.get_widget_list()
        self.assertEqual(len(widget_list), 3)

    def test_plot_tool_bar_widget_list(self):
        toolbar = PlotToolBar()
        widget_list = toolbar.get_widget_list()
        self.assertEqual(len(widget_list), 3)

        # tests for immutability
        widget_list.append(QCheckBox())
        self.assertEqual(len(toolbar.get_widget_list()), 3)

        # tests adding widget
        checkbox = QCheckBox()
        toolbar.addWidget(checkbox)
        self.assertEqual(len(toolbar.get_widget_list()), 4)