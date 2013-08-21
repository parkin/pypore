'''
Created on Aug 20, 2013

@author: parkin
'''
import unittest
from src.helper import UsesQApplication
import os
from PySide.QtGui import QColor
# from PySide.QtTest import QTest
from src.pyporegui.views import FilterListItem, FileListItem, DataFileListItem,\
    PlotToolBar

class TestPlotToolBar(unittest.TestCase):
    
    def setUp(self):
        pass
    
    def tearDown(self):
        pass
    
    def TestPlotToolBar(self):
        toolbar = PlotToolBar
        self.assertTrue(toolbar.isDecimateChecked())
        self.assertTrue(toolbar.isPlotDuringChecked())

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
