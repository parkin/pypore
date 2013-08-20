'''
Created on Aug 19, 2013

@author: parkin
'''
import unittest
from pypore.DataFileOpener import openData, prepareDataFile, prepareChimeraFile,\
    openChimeraFile

class TestDataFileOpener(unittest.TestCase):


    def setUp(self):
        self.allowedFileExtensions = ['.hkd', '.log']
        self.randomUnallowedExtensions = ['.fsd', '.kdf', '', '+']

    def tearDown(self):
        pass


    def testBadFileExtensionOpenData(self):
        for extension in self.randomUnallowedExtensions:
            x = openData(extension)
            self.assertIn('error', x, 'Error not returned when extension bad. Extension: ' + str(extension))
            self.assertTrue('File not specified' in x['error'], 'Wrong error message for bad filetype: ' + str(extension))
    
    def testBadFileExtensionPrepareFile(self):
        for extension in self.randomUnallowedExtensions:
            y, x = prepareDataFile(extension)
            self.assertIn('error', x, 'Error not returned when extension bad. Extension: ' + str(extension))
            self.assertTrue('File not specified' in x['error'], 'Wrong error message for bad filetype: ' + str(extension))
            self.assertEqual(y, 0, 'prepareChimera did not return 0 when error raised')
            
    def testNoChimeraMatSpec(self):
        testNoMatChimeraFiles = ['testDataFiles/empty.log']
        for filename in testNoMatChimeraFiles:
            x = openData(filename)
            self.assertIn('error', x, 'Error not returned when opening chimera file without .mat spec file.')
            self.assertTrue('.mat' in x['error'], 'Incorrect error returned for chimera file without .mat spec file')
            
            y,x = prepareChimeraFile(filename) 
            self.assertIn('error', x, 'Error not returned when opening chimera file without .mat spec file.')
            self.assertTrue('.mat' in x['error'], 'Incorrect error returned for chimera file without .mat spec file')
            self.assertEqual(y, 0, 'prepareChimera did not return 0 when error raised')
            
    def testOpenDataWithChimeraFiles(self):
        filename = 'testDataFiles/smallChimera.log'
        specs = openData(filename, False)
        self._testSmallChimeraFileHelp(specs)
        
    def _testSmallChimeraFileHelp(self, specs):
        self.assertIn('data', specs, 'No data returned from openData.')
        datas = specs['data']
        self.assertEqual(len(datas), 1, 'Too many data channels returned.')
        data = datas[0]
        self.assertEqual(data.size, 10, 'Wrong data size returned.')
        self.assertAlmostEqual(data[0], 1.07818604, 7)
        self.assertAlmostEqual(data[9], 1.11694336, 7)

    def testOpenChimeraData(self):
        filename = 'testDataFiles/smallChimera.log'
        specs = openChimeraFile(filename, False)
        self._testSmallChimeraFileHelp(specs)
        

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()