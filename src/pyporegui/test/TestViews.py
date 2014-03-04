'''
Created on Aug 20, 2013

@author: parkin
'''
import unittest
from helper import UsesQApplication
import os
from PySide.QtGui import QColor, QCheckBox
# from PySide.QtTest import QTest
from pyporegui.graphicsItems.MyPlotItem import MyPlotItem
from pyporegui.FileItems import FilterListItem, FileListItem, DataFileListItem
from pyqtgraph.graphicsItems.PlotCurveItem import PlotCurveItem
from pyporegui.eventanalysis import PathItem
import numpy as np
from pyporegui.widgets.PlotToolBar import PlotToolBar


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
        plotitem.add_event_item(plot)
        
        self.assertEqual(len(plotitem._myEventItemList), 1)
        
        x=y=np.zeros(2)
        plot2 = PathItem(x,y)
        plotitem.add_event_item(plot2)
        self.assertEqual(len(plotitem._myEventItemList), 2)
        
    def testClearEventItems(self):
        plotitem = MyPlotItem()
        x = [1]
        y = [1]
        plot = PlotCurveItem(x,y)
        plotitem.addItem(plot)
        
        plot2 = PlotCurveItem(y,x)
        plotitem.add_event_item(plot2)
        
        self.assertEqual(len(plotitem._myEventItemList), 1)
        self.assertEqual(len(plotitem.listDataItems()), 2)
        
        plotitem.clear_event_items()
        self.assertEqual(len(plotitem._myEventItemList), 0)
        
        self.assertEqual(len(plotitem.listDataItems()), 1)
        
    def testClear(self):
        plotitem = MyPlotItem()
        x = [1]
        y = [1]
        plot = PlotCurveItem(x,y)
        plotitem.addItem(plot)
        
        plot2 = PlotCurveItem(y,x)
        plotitem.add_event_item(plot2)
        
        x=y=np.zeros(2)
        plot3 = PathItem(x,y)
        plotitem.add_event_item(plot3)
        
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
        plotitem.add_event_item(plot2)
        
        plot5 = PlotCurveItem(y,x)
        plotitem.addItem(plot5)
        
        x=y=np.zeros(2)
        plot3 = PathItem(x,y)
        plotitem.add_event_item(plot3)
        
        plot4 = plotitem.plot(clear=True)
        
        # Test that all of the plots have been cleared,
        # and that plot4 was added succesfully
        self.assertEqual(len(plotitem.listDataItems()), 1)
        self.assertEqual(len(plotitem._myEventItemList), 0)
        self.assertEqual(len(plotitem._myItemList), 1)
        self.assertEqual(plotitem.listDataItems()[0], plot4)
        self.assertEqual(plotitem._myItemList[0], plot4)
        
        
class TestPlotToolBar(unittest.TestCase):
    
    def testPlotToolBarInitialState(self):
        toolbar = PlotToolBar()
        self.assertTrue(toolbar.is_decimate_checked())
        self.assertTrue(toolbar.is_plot_during_checked())
        wiglist = toolbar.get_widget_list()
        self.assertEqual(len(wiglist), 3)
        
    def testPlotToolBarWidgetList(self):
        toolbar = PlotToolBar()
        wiglist = toolbar.get_widget_list()
        self.assertEqual(len(wiglist), 3)
        
        # test for immutability
        wiglist.append(QCheckBox())
        self.assertEqual(len(toolbar.get_widget_list()), 3)
        
        # test adding widget
        checkbox = QCheckBox()
        toolbar.addWidget(checkbox)
        self.assertEqual(len(toolbar.get_widget_list()), 4)
        
class TestFileListItem(unittest.TestCase):
    
    def setUp(self):
        self.filename = os.path.abspath('hi.txt')
        self._setItem()
        
    def _setItem(self):
        self.item = FileListItem(self.filename)
    
    def tearDown(self):
        pass
    
    def testFileListItemSimpleName(self):
        simplename = self.item.get_simple_name()
        self.assertEqual(simplename, 'hi.txt')
        
    def testFileListItemDirectory(self):
        directory = self.item.get_directory()
        self.assertEqual(directory, os.path.dirname(self.filename))
        
    def testFileListItemFilename(self):
        check = self.item.get_file_name()
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
        params = self.item.get_params()
        self.assertEqual(params, self.params)
        
        # Test immutable
        params['qwertyuiop'] = 1
        self.assertNotIn('qwertyuiop', self.item.get_params())
        
    def testDataFileListItemGetParam(self):
        self.assertEqual(self.item.get_param('hi'), 9)
        self.assertEqual(self.item.get_param('bye'), 19)
        self.assertIsNone(self.item.get_param('sdafkfasfweoaifeawfksfd'))
        
_instance = None
    
class TestFilterListItem(UsesQApplication):
    
    def setUp(self):
        super(TestFilterListItem, self).setUp()

    def tearDown(self):
        super(TestFilterListItem, self).tearDown()
    
    def testFilterListItemSimpleName(self):
        filenames = [os.path.abspath('hi.txt')]
        item = FilterListItem(filenames)
        simplenames = item.get_simple_names()
        self.assertEqual(len(simplenames), len(filenames))
        self.assertEqual(simplenames[0], 'hi.txt')
        self.assertEqual(item.get_simple_name_at(0), 'hi.txt')
        self.assertIsNone(item.get_simple_name_at(100))
        self.assertIsNone(item.get_simple_name_at(-12))
        
        # Test immutability
        simplenames.append('blahblahblahblahblah')
        self.assertEqual(len(item.get_simple_names()), len(filenames))
        
    def testFilterListItemFileNames(self):
        filenames = [os.path.abspath(__file__), os.path.abspath('x.hi')]
        item = FilterListItem(filenames)
        names = item.get_file_names()
        self.assertEqual(names, filenames)
        self.assertEqual(item.get_file_name_at(1), filenames[1])
        self.assertIsNone(item.get_file_name_at(-1))
        
        # Test immutability
        names.append('blahblahblahblah')
        self.assertEqual(len(item.get_file_names()), len(filenames))
        
    def testFilterListItemDefaultColor(self):
        filenames = [os.path.abspath('hi.txt')]
        item = FilterListItem(filenames)
        color = item.get_params()['color']
        self.assertTrue(type(color) is QColor)
        
    def testFilterListItemColor(self):
        filenames = [os.path.abspath('hi.txt')]
        color = QColor.fromRgbF(1.,1.,1.,1.)
        item = FilterListItem(filenames, color=color)
        colorCheck = item.get_params()['color']
        self.assertEqual(color, colorCheck)
        
    def testFilterListItemParams(self):
        filenames = [os.path.abspath('hi.txt')]
        item = FilterListItem(filenames)
        params = item.get_params()
        self.assertEqual(len(params.keys()), 1)
        self.assertIn('color', params)
        
        item = FilterListItem(filenames, x=12, y={'hi': 'bye'})
        params = item.get_params()
        self.assertEqual(len(params.keys()), 3)
        self.assertIn('color', params)
        self.assertIn('x', params)
        self.assertIn('hi', params['y'])
        
        # test immutability
        params['qwertyuiop'] = 1
        self.assertNotIn('qwertyuiop', item.get_params())
        
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
