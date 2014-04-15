"""
Created on Aug 27, 2013

@author: `@parkin`_
"""
import unittest
from pyporegui.graphicsItems.path_item import PathItem
import numpy as np
from PySide import QtGui

# This test class needs a QApplication instance
if QtGui.qApp is None:
    QtGui.QApplication([])


class TestPathItem(unittest.TestCase):
    def test_bounding_rect(self):
        x = np.random.uniform(-10, 10, size=10)
        y = np.random.uniform(-10, 10, size=10)

        x_max = x.max()
        x_min = x.min()
        y_max = y.max()
        y_min = y.min()

        item = PathItem(x, y)
        rect = item.boundingRect()
        rect_left = rect.left()
        self.assertAlmostEqual(rect_left, x_min, 7)
        rect_top = rect.top()
        self.assertAlmostEqual(rect_top, y_min, 7)
        wid = rect.width()
        hei = rect.height()
        self.assertAlmostEqual(wid, x_max - x_min, 7)
        self.assertAlmostEqual(hei, y_max - y_min)

    def test_bounding_rect_small_values(self):
        x = np.random.uniform(-1.e-9, 1.e-9, size=10)
        y = np.random.uniform(-1.e-9, 1.e-9, size=10)

        x_max = x.max()
        x_min = x.min()
        y_max = y.max()
        y_min = y.min()

        item = PathItem(x, y)
        rect = item.boundingRect()
        rect_left = rect.left()
        self.assertAlmostEqual(rect_left, x_min, 12)
        rect_top = rect.top()
        self.assertAlmostEqual(rect_top, y_min, 12)
        wid = rect.width()
        hei = rect.height()
        self.assertAlmostEqual(wid, x_max - x_min, 12)
        self.assertAlmostEqual(hei, y_max - y_min)


if __name__ == "__main__":
    unittest.main()
