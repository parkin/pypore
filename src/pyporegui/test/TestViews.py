'''
Created on Aug 20, 2013

@author: parkin
'''
import unittest
import os
from PySide.QtGui import QColor
from src.pyporegui.views import FilterListItem

class TestViews(unittest.TestCase):

    def setUp(self):
        pass


    def tearDown(self):
        pass

    def testFilterListItemSimpleName(self):
        filenames = [os.path.abspath('hi.txt')]
        item = FilterListItem(filenames)
        simplenames = item.getSimpleNames()
        self.assertEqual(len(simplenames), len(filenames))
        self.assertEqual(simplenames[0], 'hi.txt')
        self.assertEqual(item.getSimpleNameAt(0), 'hi.txt')
        self.assertIsNone(item.getSimpleNameAt(100))
        self.assertIsNone(item.getSimpleNameAt(-12))
        
    def testFilterListItemFileNames(self):
        filenames = [os.path.abspath(__file__), os.path.abspath('x.hi')]
        item = FilterListItem(filenames)
        names = item.getFileNames()
        self.assertEqual(names, filenames)
        self.assertEqual(item.getFileNameAt(1), filenames[1])
        self.assertIsNone(item.getFileNameAt(-1))
        
    def testFilterListItemDefaultColor(self):
        filenames = [os.path.abspath('hi.txt')]
        item = FilterListItem(filenames)
        color = item.getParams()['color']
        self.assertTrue(type(color) is QColor)
        
    def testFilterListItemColor(self):
        filenames = [os.path.abspath('hi.txt')]
        color = QColor.fromRgbF(1.,1.,1.,1.)
        item = FilterListItem(filenames, color=color)
        colorCheck = item.getParams()['color']
        self.assertEqual(color, colorCheck)
        
    def testFilterListItemParams(self):
        filenames = [os.path.abspath('hi.txt')]
        item = FilterListItem(filenames)
        params = item.getParams()
        self.assertEqual(len(params.keys()), 1)
        self.assertIn('color', params)
        
        item = FilterListItem(filenames, x=12, y={'hi': 'bye'})
        params = item.getParams()
        self.assertEqual(len(params.keys()), 3)
        self.assertIn('color', params)
        self.assertIn('x', params)
        self.assertIn('hi', params['y'])
        
    def testFilterListItemText(self):
        filenames = [os.path.abspath('hi.txt'), os.path.abspath('bye.py'), os.path.abspath('q')]
        item = FilterListItem(filenames)
        text = item.text()
        self.assertEqual(text, 'hi.txt, bye.py, q')
        
        filenames = []
        item = FilterListItem(filenames)
        text = item.text()
        self.assertEqual(text, 'item')
    
    def testFilterListItemForeground(self):
        filenames = [os.path.abspath('hi.txt')]
        color = QColor.fromRgbF(.5,.6,.4,.34)
        item = FilterListItem(filenames, color=color)
        foregroundcolor = item.foreground().color()
        self.assertEqual(color, foregroundcolor)

if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
