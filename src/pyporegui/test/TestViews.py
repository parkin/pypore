'''
Created on Aug 20, 2013

@author: parkin
'''
import unittest
from pyporegui.views import *
import os


class TestViews(unittest.TestCase):


    def setUp(self):
        pass


    def tearDown(self):
        pass


    def testFilterListItemSimpleName(self):
        filenames = [os.path.abspath(__file__)]
        params = {}
        item = FilterListItem(filenames, params)
        simplenames = item.getSimpleNames()
        self.assertEqual(len(simplenames), len(filenames))
        self.assertEqual(simplenames[0], 'TestViews.py')
        self.assertEqual(item.getSimpleNameAt(0), 'TestViews.py')

if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
