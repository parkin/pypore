import unittest
from functools import wraps
import numpy as np

from PySide import QtGui

from pyporegui.graphicsItems.histogram_item import HistogramItem

# This test class needs a QApplication instance
if QtGui.qApp is None:
    QtGui.QApplication([])


def _rotation(func):
    """
    Decorator.

    Decorates a test function, calls the test twice, once with rotate=True, second time with rotate=False.
    """
    @wraps(func)
    def wrap(self):
        print "rotate: True"
        func(self, rotate=True)
        print "rotate: False"
        func(self, rotate=False)

    return wrap


class TestHistogramItem(unittest.TestCase):
    @_rotation
    def test_add_histogram(self, rotate):
        """
        Tests adding a histogram.
        """
        item = HistogramItem(rotate=rotate)

        # Assert no data items.
        self.assertEqual(len(item.listDataItems()), 0)

        data = np.random.random(100)

        item.add_histogram(data)

        data_items = item.listDataItems()
        self.assertEqual(len(data_items), 1)

    @_rotation
    def test_add_2_histograms_same_data(self, rotate):
        """
        Tests that adding 2 histograms with the same data is ok.
        """
        item = HistogramItem(rotate=rotate)

        data = np.random.random(100)

        item.add_histogram(data)

        item.add_histogram(data)
        self.assertEqual(len(item.listDataItems()), 2)
