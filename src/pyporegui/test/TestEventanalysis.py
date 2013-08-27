'''
Created on Aug 27, 2013

@author: parkin
'''
import unittest
from helper import UsesQApplication
from src.pyporegui.eventanalysis import PathItem, MyMainWindow
import numpy as np
import os

class TestPathItem(unittest.TestCase):
    
    def testBoundingRect(self):
        x = np.random.uniform(-10,10,size=10)
        y = np.random.uniform(-10,10,size=10)
        
        xmax = x.max()
        xmin = x.min()
        ymax = y.max()
        ymin = y.min()
        
        item = PathItem(x,y)
        rect = item.boundingRect()
        rectleft = rect.left()
        self.assertAlmostEqual(rectleft, xmin, 7)
        recttop = rect.top()
        self.assertAlmostEqual(recttop, ymin, 7)
        wid = rect.width()
        hei = rect.height()
        self.assertAlmostEqual(wid, xmax-xmin, 7)
        self.assertAlmostEqual(hei, ymax-ymin)
        
    def testBoundingRectSmallVales(self):
        x = np.random.uniform(-1.e-9,1.e-9,size=10)
        y = np.random.uniform(-1.e-9,1.e-9,size=10)
        
        xmax = x.max()
        xmin = x.min()
        ymax = y.max()
        ymin = y.min()
        
        item = PathItem(x,y)
        rect = item.boundingRect()
        rectleft = rect.left()
        self.assertAlmostEqual(rectleft, xmin, 12)
        recttop = rect.top()
        self.assertAlmostEqual(recttop, ymin, 12)
        wid = rect.width()
        hei = rect.height()
        self.assertAlmostEqual(wid, xmax-xmin, 12)
        self.assertAlmostEqual(hei, ymax-ymin)

class TestEventAnalysis(UsesQApplication):

    def setUp(self):
        super(TestEventAnalysis, self).setUp()
        self.window = MyMainWindow(self.qapplication, )
        
    def tearDown(self):
        super(TestEventAnalysis, self).tearDown()
        
    def testName(self):
        pass

if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
