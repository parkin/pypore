'''
Created on Aug 20, 2013

@author: parkin
'''
import unittest
from src.helper import UsesQApplication
import os
from PySide.QtGui import QColor, QCheckBox
# from PySide.QtTest import QTest
from src.pyporegui.views import FilterListItem, FileListItem, DataFileListItem,\
    PlotToolBar, MyPlotItem
from pyqtgraph.graphicsItems.PlotCurveItem import PlotCurveItem
from src.pyporegui.eventanalysis import PathItem
import numpy as np
    
    
class TestMyPlotItem(unittest.TestCase):
    
    def testMyPlotItemAddItem(self):
        plotitem = MyPlotItem()
        x = [1]
        y = [1]
        plot = PlotCurveItem(x,y)
        plotitem.addItem(plot)
        
        self.assertEqual(len(plotitem._myItemList), 1)
        
        x=y=np.zeros(2)
        plot2 = PathItem(x,y)
        plotitem.addItem(plot2)
        self.assertEqual(len(plotitem._myItemList), 2)
        
    def testAddEventItem(self):
        plotitem = MyPlotItem()
        x = [1]
        y = [1]
        plot = PlotCurveItem(x,y)
        plotitem.addEventItem(plot)
        
        self.assertEqual(len(plotitem._myEventItemList), 1)
        
        x=y=np.zeros(2)
        plot2 = PathItem(x,y)
        plotitem.addEventItem(plot2)
        self.assertEqual(len(plotitem._myEventItemList), 2)
        
    def testClearEventItems(self):
        plotitem = MyPlotItem()
        x = [1]
        y = [1]
        plot = PlotCurveItem(x,y)
        plotitem.addItem(plot)
        
        plot2 = PlotCurveItem(y,x)
        plotitem.addEventItem(plot2)
        
        self.assertEqual(len(plotitem._myEventItemList), 1)
        self.assertEqual(len(plotitem.listDataItems()), 2)
        
        plotitem.clearEventItems()
        self.assertEqual(len(plotitem._myEventItemList), 0)
        
        self.assertEqual(len(plotitem.listDataItems()), 1)
        
    def testClear(self):
        plotitem = MyPlotItem()
        x = [1]
        y = [1]
        plot = PlotCurveItem(x,y)
        plotitem.addItem(plot)
        
        plot2 = PlotCurveItem(y,x)
        plotitem.addEventItem(plot2)
        
        x=y=np.zeros(2)
        plot3 = PathItem(x,y)
        plotitem.addEventItem(plot3)
        
        plotitem.clear()
        self.assertEqual(len(plotitem.listDataItems()), 0)
        self.assertEqual(len(plotitem._myEventItemList), 0)
        self.assertEqual(len(plotitem._myItemList), 0)
        
    def testPlotClear(self):
        # test to make sure that when the clear flag is passed
        # to plots, that clear works as expected
        plotitem = MyPlotItem()
        x = [1]
        y = [1]
        plot = PlotCurveItem(x,y)
        plotitem.addItem(plot)
        
        plot2 = PlotCurveItem(y,x)
        plotitem.addEventItem(plot2)
        
        x=y=np.zeros(2)
        plot3 = PathItem(x,y)
        plotitem.addEventItem(plot3)
        
        plot4 = plotitem.plot(clear=True)
        
        self.assertEqual(len(plotitem.listDataItems()), 1)
        self.assertEqual(len(plotitem._myEventItemList), 0)
        self.assertEqual(len(plotitem._myItemList), 1)
        
        
class TestPlotToolBar(unittest.TestCase):
    
    def testPlotToolBarInitialState(self):
        toolbar = PlotToolBar()
        self.assertTrue(toolbar.isDecimateChecked())
        self.assertTrue(toolbar.isPlotDuringChecked())
        wiglist = toolbar.getWidgetList()
        self.assertEqual(len(wiglist), 2)
        
    def testPlotToolBarWidgetList(self):
        toolbar = PlotToolBar()
        wiglist = toolbar.getWidgetList()
        self.assertEqual(len(wiglist), 2)
        
        # test for immutability
        wiglist.append(QCheckBox())
        self.assertEqual(len(toolbar.getWidgetList()), 2)
        
        # test adding widget
        checkbox = QCheckBox()
        toolbar.addWidget(checkbox)
        self.assertEqual(len(toolbar.getWidgetList()), 3)
        
class TestFileListItem(unittest.TestCase):
    
    def setUp(self):
        self.filename = os.path.abspath('hi.txt')
        self._setItem()
        
    def _setItem(self):
        self.item = FileListItem(self.filename)
    
    def tearDown(self):
        pass
    
    def testFileListItemSimpleName(self):
        simplename = self.item.getSimpleName()
        self.assertEqual(simplename, 'hi.txt')
        
    def testFileListItemDirectory(self):
        directory = self.item.getDirectory()
        self.assertEqual(directory, os.path.dirname(self.filename))
        
    def testFileListItemFilename(self):
        check = self.item.getFileName()
        self.assertEqual(check, self.filename)
        
class TestDataFileListItem(TestFileListItem):
    '''
    Subclassing TestFileListItem will also run those tests too.
    '''
     
    def setUp(self):
        self.params = {'hi': 9, 'bye': 19}
        TestFileListItem.setUp(self)
        
    def _setItem(self):
        self.item = DataFileListItem(self.filename, self.params)
        
    def testDataFileListItemParams(self):
        params = self.item.getParams()
        self.assertEqual(params, self.params)
        
        # Test immutable
        params['qwertyuiop'] = 1
        self.assertNotIn('qwertyuiop', self.item.getParams())
        
    def testDataFileListItemGetParam(self):
        self.assertEqual(self.item.getParam('hi'), 9)
        self.assertEqual(self.item.getParam('bye'), 19)
        self.assertIsNone(self.item.getParam('sdafkfasfweoaifeawfksfd'))
        
_instance = None
    
class TestFilterListItem(UsesQApplication):
    
    def setUp(self):
        super(TestFilterListItem, self).setUp()

    def tearDown(self):
        super(TestFilterListItem, self).tearDown()
    
    def testFilterListItemSimpleName(self):
        filenames = [os.path.abspath('hi.txt')]
        item = FilterListItem(filenames)
        simplenames = item.getSimpleNames()
        self.assertEqual(len(simplenames), len(filenames))
        self.assertEqual(simplenames[0], 'hi.txt')
        self.assertEqual(item.getSimpleNameAt(0), 'hi.txt')
        self.assertIsNone(item.getSimpleNameAt(100))
        self.assertIsNone(item.getSimpleNameAt(-12))
        
        # Test immutability
        simplenames.append('blahblahblahblahblah')
        self.assertEqual(len(item.getSimpleNames()), len(filenames))
        
    def testFilterListItemFileNames(self):
        filenames = [os.path.abspath(__file__), os.path.abspath('x.hi')]
        item = FilterListItem(filenames)
        names = item.getFileNames()
        self.assertEqual(names, filenames)
        self.assertEqual(item.getFileNameAt(1), filenames[1])
        self.assertIsNone(item.getFileNameAt(-1))
        
        # Test immutability
        names.append('blahblahblahblah')
        self.assertEqual(len(item.getFileNames()), len(filenames))
        
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
        
        # test immutability
        params['qwertyuiop'] = 1
        self.assertNotIn('qwertyuiop', item.getParams())
        
    def testFilterListItemText(self):
        filenames = [os.path.abspath('hi.txt'), os.path.abspath('bye.py'), os.path.abspath('q')]
        item = FilterListItem(filenames)
        text = item.text()
        self.assertEqual(text, 'hi.txt, bye.py, q')
        
        filenames = []
        item = FilterListItem(filenames)
        text = item.text()
        self.assertEqual(text, 'item')
    
    def testFilterListItemHasIcon(self):
        filenames = [os.path.abspath('hi.txt')]
        color = QColor.fromRgbF(.5,.6,.4,.34)
        item = FilterListItem(filenames, color=color)
        icon = item.icon()
        self.assertIsNotNone(icon)
        self.assertFalse(icon.isNull())

if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
