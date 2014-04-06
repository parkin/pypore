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
    def _assert_histogram_item_array_lengths(self, item, length):
        """
        Tests that all of the list members of the HistogramItem item have length number of entries.
        """
        self.assertEqual(len(item.listDataItems()), length)
        self.assertEqual(len(item.data_array), length)
        self.assertEqual(len(item.maximum_array), length)
        self.assertEqual(len(item.minimum_array), length)

    @_rotation
    def test_add_histogram(self, rotate):
        """
        Tests adding a histogram.
        """
        item = HistogramItem(rotate=rotate)

        # Assert no data items.
        self._assert_histogram_item_array_lengths(item, 0)

        data = np.random.random(100)

        item.add_histogram(data)

        data_items = item.listDataItems()
        self._assert_histogram_item_array_lengths(item, 1)

    @_rotation
    def test_add_2_histograms_same_data(self, rotate):
        """
        Tests that adding 2 histograms with the same data is ok.
        """
        item = HistogramItem(rotate=rotate)

        data = np.random.random(100)

        item.add_histogram(data)

        item.add_histogram(data)
        self._assert_histogram_item_array_lengths(item, 2)

    @_rotation
    def test_add_2nd_histogram_narrower_range(self, rotate):
        """
        Tests that we can add a 2nd histogram with narrower (max-min) data. This should not
        change the histograms max/min or the number of bins.
        """
        item = HistogramItem(rotate=rotate)

        # -50 < data[i] < 50
        data = np.random.random(100) * 100 - 50

        item.add_histogram(data)

        maximum = item.maximum
        minimum = item.minimum
        n_bins = item.n_bins

        # 0 < data[i] < 1
        data2 = np.random.random(100)
        item.add_histogram(data2)

        self._assert_histogram_item_array_lengths(item, 2)
        self.assertEqual(item.maximum, maximum)
        self.assertEqual(item.minimum, minimum)
        self.assertEqual(item.n_bins, n_bins)

    @_rotation
    def test_add_2nd_histogram_wider_range(self, rotate):
        """
        Tests that we can add a 2nd histogram with wider data. The max should increase, min
        should decrease, n_bins should stay same (default n_bins depends on length of data).
        """
        item = HistogramItem(rotate=rotate)

        # 0 < data[i] < 1
        data = np.random.random(100)
        # -50 < data[i] < 50
        data2 = np.random.random(100) * 100 - 50

        item.add_histogram(data)

        maximum = item.maximum
        minimum = item.minimum
        n_bins = item.n_bins

        item.add_histogram(data2)

        self._assert_histogram_item_array_lengths(item, 2)
        self.assertLess(item.minimum, minimum)
        self.assertGreater(item.maximum, maximum)
        self.assertEqual(item.n_bins, n_bins)

    @_rotation
    def test_add_2nd_histogram_more_points(self, rotate):
        """
        Tests that adding a 2nd histogram with more points increases the number of bins.
        """
        item = HistogramItem(rotate=rotate)

        data = np.random.random(100)

        item.add_histogram(data)
        n_bins = item.n_bins

        data2 = np.random.random(1000)

        item.add_histogram(data2)

        self._assert_histogram_item_array_lengths(item, 2)
        self.assertGreater(item.n_bins, n_bins)

    @_rotation
    def test_add_2nd_histogram_less_points(self, rotate):
        """
        Tests that adding a 2nd histogram with less points doesn't change number of bins.
        """
        item = HistogramItem(rotate=rotate)

        data = np.random.random(1000)

        item.add_histogram(data)
        n_bins = item.n_bins

        data2 = np.random.random(100)

        item.add_histogram(data2)

        self._assert_histogram_item_array_lengths(item, 2)
        self.assertEqual(item.n_bins, n_bins)

    @_rotation
    def test_remove_only_histogram(self, rotate):
        """
        Tests that removing the only item works.
        """
        item = HistogramItem(rotate=rotate)

        data = np.random.random(100)

        item.add_histogram(data)

        self._assert_histogram_item_array_lengths(item, 1)

        item.remove_item_at(0)

        self._assert_histogram_item_array_lengths(item, 0)

    @_rotation
    def test_remove_first_histogram(self, rotate):
        """
        Tests that removing the first histogram works.
        """
        item = HistogramItem(rotate=rotate)

        data = np.random.random(100)

        item.add_histogram(data)

        data2 = np.random.random(200)

        item.add_histogram(data2)

        data_item2 = item.listDataItems()[1]

        item.remove_item_at(0)

        self._assert_histogram_item_array_lengths(item, 1)

        data_item_left = item.listDataItems()[0]

        self.assertEqual(data_item2, data_item_left)
