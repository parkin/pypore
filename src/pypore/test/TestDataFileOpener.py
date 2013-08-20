'''
Created on Aug 19, 2013

@author: parkin
'''
import unittest
from pypore.DataFileOpener import openData

class TestDataFileOpener(unittest.TestCase):


    def setUp(self):
        self.allowedFileExtensions = ['.hkd', '.log']
        self.randomUnallowedExtensions = ['.fsd', '.kdf', '', '+']

    def tearDown(self):
        pass


    def testBadFileExtension(self):
        for extension in self.randomUnallowedExtensions:
            x = openData(extension)
            self.assertIn('error', x, 'Error not returned when extension bad.')
            self.assertTrue('File not specified' in x['error'], 'Wrong error message for bad filetype.')


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()