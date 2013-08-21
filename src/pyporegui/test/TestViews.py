'''
Created on Aug 20, 2013

@author: parkin
'''
import unittest
import os
from src.pyporegui.views import FilterListItem
from PySide.QtGui import QColor

class TestViews(unittest.TestCase):

    def setUp(self):
        pass


    def tearDown(self):
        pass

    def testFilterListItemSimpleName(self):
        filenames = [os.path.abspath(__file__)]
        item = FilterListItem(filenames)
        simplenames = item.getSimpleNames()
        self.assertEqual(len(simplenames), len(filenames))
        self.assertEqual(simplenames[0], 'TestViews.py')
        self.assertEqual(item.getSimpleNameAt(0), 'TestViews.py')
        
    def testFilterListItemDefaultColor(self):
        filenames = ['hi.txt']
        item = FilterListItem(filenames)
        color = item.getParams()['color']
        self.assertTrue(type(color) is QColor)
        
    

if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
