import unittest
import numpy as np
from pyqtgraph.graphicsItems.PlotCurveItem import PlotCurveItem
from pyporegui.graphicsItems.my_plot_item import MyPlotItem
from pyporegui.graphicsItems.path_item import PathItem


class TestMyPlotItem(unittest.TestCase):

    def test_my_plot_item_add_item(self):
        plot_item = MyPlotItem()
        x = [1]
        y = [1]
        plot = PlotCurveItem(x, y)
        plot_item.addItem(plot)

        self.assertEqual(len(plot_item._myItemList), 1)

        x = y = np.zeros(2)
        plot2 = PathItem(x, y)
        plot_item.addItem(plot2)
        self.assertEqual(len(plot_item._myItemList), 2)

    def test_add_event_item(self):
        plot_item = MyPlotItem()
        x = [1]
        y = [1]
        plot = PlotCurveItem(x, y)
        plot_item.add_event_item(plot)

        self.assertEqual(len(plot_item._myEventItemList), 1)

        x = y = np.zeros(2)
        plot2 = PathItem(x, y)
        plot_item.add_event_item(plot2)
        self.assertEqual(len(plot_item._myEventItemList), 2)

    def test_clear_event_items(self):
        plot_item = MyPlotItem()
        x = [1]
        y = [1]
        plot = PlotCurveItem(x, y)
        plot_item.addItem(plot)

        plot2 = PlotCurveItem(y, x)
        plot_item.add_event_item(plot2)

        self.assertEqual(len(plot_item._myEventItemList), 1)
        self.assertEqual(len(plot_item.listDataItems()), 2)

        plot_item.clear_event_items()
        self.assertEqual(len(plot_item._myEventItemList), 0)

        self.assertEqual(len(plot_item.listDataItems()), 1)

    def test_clear(self):
        plot_item = MyPlotItem()
        x = [1]
        y = [1]
        plot = PlotCurveItem(x, y)
        plot_item.addItem(plot)

        plot2 = PlotCurveItem(y, x)
        plot_item.add_event_item(plot2)

        x = y = np.zeros(2)
        plot3 = PathItem(x, y)
        plot_item.add_event_item(plot3)

        plot_item.clear()
        self.assertEqual(len(plot_item.listDataItems()), 0)
        self.assertEqual(len(plot_item._myEventItemList), 0)
        self.assertEqual(len(plot_item._myItemList), 0)

    def test_plot_clear(self):
        # tests to make sure that when the clear flag is passed
        # to plots, that clear works as expected
        plot_item = MyPlotItem()
        x = [1]
        y = [1]
        plot = PlotCurveItem(x, y)
        plot_item.addItem(plot)

        plot2 = PlotCurveItem(y, x)
        plot_item.add_event_item(plot2)

        plot5 = PlotCurveItem(y, x)
        plot_item.addItem(plot5)

        x = y = np.zeros(2)
        plot3 = PathItem(x, y)
        plot_item.add_event_item(plot3)

        plot4 = plot_item.plot(clear=True)

        # Test that all of the plots have been cleared,
        # and that plot4 was added successfully
        self.assertEqual(len(plot_item.listDataItems()), 1)
        self.assertEqual(len(plot_item._myEventItemList), 0)
        self.assertEqual(len(plot_item._myItemList), 1)
        self.assertEqual(plot_item.listDataItems()[0], plot4)
        self.assertEqual(plot_item._myItemList[0], plot4)