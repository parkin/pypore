"""
Created on Aug 20, 2013

@author: `@parkin`_
"""
from PySide import QtGui
import unittest
import os

from PySide.QtGui import QColor

# This class needs a QApplication instance
if QtGui.qApp is None:
    QtGui.QApplication([])

# from PySide.QtTest import QTest
from pyporegui.file_items import FilterListItem, FileListItem, DataFileListItem


class TestFileListItem(unittest.TestCase):
    
    def setUp(self):
        self.filename = os.path.abspath('hi.txt')
        self._set_item()
        
    def _set_item(self):
        self.item = FileListItem(self.filename)
    
    def tearDown(self):
        pass
    
    def test_file_list_item_simple_name(self):
        simple_name = self.item.get_simple_name()
        self.assertEqual(simple_name, 'hi.txt')
        
    def test_file_list_item_directory(self):
        directory = self.item.get_directory()
        self.assertEqual(directory, os.path.dirname(self.filename))
        
    def test_file_list_item_filename(self):
        check = self.item.get_file_name()
        self.assertEqual(check, self.filename)
        
        
class TestDataFileListItem(TestFileListItem):
    """
    Subclassing TestFileListItem will also run those tests too.
    """
     
    def setUp(self):
        self.params = {'hi': 9, 'bye': 19}
        TestFileListItem.setUp(self)
        
    def _set_item(self):
        self.item = DataFileListItem(self.filename, self.params)
        
    def test_data_file_list_item_params(self):
        params = self.item.get_params()
        self.assertEqual(params, self.params)
        
        # Test immutable
        params['qwertyuiop'] = 1
        self.assertNotIn('qwertyuiop', self.item.get_params())
        
    def test_data_file_list_item_get_param(self):
        self.assertEqual(self.item.get_param('hi'), 9)
        self.assertEqual(self.item.get_param('bye'), 19)
        self.assertIsNone(self.item.get_param('sdafkfasfweoaifeawfksfd'))
        
_instance = None
    
    
class TestFilterListItem(unittest.TestCase):
    
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_filter_list_item_simple_name(self):
        file_names = [os.path.abspath('hi.txt')]
        item = FilterListItem(file_names)
        simple_names = item.get_simple_names()
        self.assertEqual(len(simple_names), len(file_names))
        self.assertEqual(simple_names[0], 'hi.txt')
        self.assertEqual(item.get_simple_name_at(0), 'hi.txt')
        self.assertIsNone(item.get_simple_name_at(100))
        self.assertIsNone(item.get_simple_name_at(-12))
        
        # Test immutability
        simple_names.append('blahblahblahblahblah')
        self.assertEqual(len(item.get_simple_names()), len(file_names))
        
    def test_filter_list_item_file_names(self):
        file_names = [os.path.abspath(__file__), os.path.abspath('x.hi')]
        item = FilterListItem(file_names)
        names = item.get_file_names()
        self.assertEqual(names, file_names)
        self.assertEqual(item.get_file_name_at(1), file_names[1])
        self.assertIsNone(item.get_file_name_at(-1))
        
        # Test immutability
        names.append('blahblahblahblah')
        self.assertEqual(len(item.get_file_names()), len(file_names))
        
    def test_filter_list_item_default_color(self):
        file_names = [os.path.abspath('hi.txt')]
        item = FilterListItem(file_names)
        color = item.get_params()['color']
        self.assertTrue(type(color) is QColor)
        
    def test_filter_list_item_color(self):
        file_names = [os.path.abspath('hi.txt')]
        color = QColor.fromRgbF(1., 1., 1., 1.)
        item = FilterListItem(file_names, color=color)
        color_check = item.get_params()['color']
        self.assertEqual(color, color_check)
        
    def test_filter_list_item_params(self):
        file_names = [os.path.abspath('hi.txt')]
        item = FilterListItem(file_names)
        params = item.get_params()
        self.assertEqual(len(params.keys()), 1)
        self.assertIn('color', params)
        
        item = FilterListItem(file_names, x=12, y={'hi': 'bye'})
        params = item.get_params()
        self.assertEqual(len(params.keys()), 3)
        self.assertIn('color', params)
        self.assertIn('x', params)
        self.assertIn('hi', params['y'])
        
        # tests immutability
        params['qwertyuiop'] = 1
        self.assertNotIn('qwertyuiop', item.get_params())
        
    def test_filter_list_item_text(self):
        file_names = [os.path.abspath('hi.txt'), os.path.abspath('bye.py'), os.path.abspath('q')]
        item = FilterListItem(file_names)
        text = item.text()
        self.assertEqual(text, 'hi.txt, bye.py, q')
        
        file_names = []
        item = FilterListItem(file_names)
        text = item.text()
        self.assertEqual(text, 'item')
    
    def test_filter_list_item_has_icon(self):
        file_names = [os.path.abspath('hi.txt')]
        color = QColor.fromRgbF(.5, .6, .4, .34)
        item = FilterListItem(file_names, color=color)
        icon = item.icon()
        self.assertIsNotNone(icon)
        self.assertFalse(icon.isNull())

if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
