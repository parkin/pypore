"""
Created on Aug 19, 2013

@author: `@parkin1`_
"""
import unittest
import os.path
from pypore import cythonsetup
from pypore.data_file_opener import open_data, prepare_data_file


class TestDataFileOpener(unittest.TestCase):
    def setUp(self):
        self.allowed_file_extensions = ['.hkd', '.log']
        self.random_disallowed_extensions = ['.fsd', '.kdf', '', '+']

    def tearDown(self):
        pass

    def test_bad_file_extension_open_data(self):
        for extension in self.random_disallowed_extensions:
            x = open_data(extension)
            self.assertIn('error', x, 'Error not returned when extension bad. Extension: ' + str(extension))
            self.assertTrue('File not specified' in x['error'],
                            'Wrong error message for bad filetype: ' + str(extension))

    def test_bad_file_extension_prepare_file(self):
        for extension in self.random_disallowed_extensions:
            y, x = prepare_data_file(extension)
            self.assertIn('error', x, 'Error not returned when extension bad. Extension: ' + str(extension))
            self.assertTrue('File not specified' in x['error'],
                            'Wrong error message for bad filetype: ' + str(extension))
            self.assertEqual(y, 0, 'prepareChimera did not return 0 when error raised')

    def test_no_chimera_mat_spec(self):
        test_no_mat_chimera_files = ['testDataFiles/empty.log']
        for filename in test_no_mat_chimera_files:
            x = open_data(filename)
            self.assertIn('error', x, 'Error not returned when opening chimera file without .mat spec file.')
            self.assertTrue('.mat' in x['error'], 'Incorrect error returned for chimera file without .mat spec file')

            y, x = prepare_data_file(filename)
            self.assertIn('error', x, 'Error not returned when opening chimera file without .mat spec file.')
            self.assertTrue('.mat' in x['error'], 'Incorrect error returned for chimera file without .mat spec file')
            self.assertEqual(y, 0, 'prepareChimera did not return 0 when error raised')

    def test_open_data_with_chimera_files(self):
        # Make sure path to chimera file is correct.
        directory = os.path.dirname(os.path.abspath(__file__))
        filename = os.path.join(os.path.join(directory, 'testDataFiles'), 'smallChimera.log')
        specs = open_data(filename, False)
        self._test_small_chimera_file_help(specs)

    def _test_small_chimera_file_help(self, specs):
        self.assertIn('data', specs, 'No data returned from open_data.')
        data_all = specs['data']
        self.assertEqual(len(data_all), 1, 'Too many data channels returned.')
        data = data_all[0]
        self.assertEqual(data.size, 10, 'Wrong data size returned.')
        self.assertAlmostEqual(data[0], 1.07818604, 7)
        self.assertAlmostEqual(data[9], 1.11694336, 7)

    def test_open_chimera_data(self):
        # Make sure path to chimera file is correct.
        directory = os.path.dirname(os.path.abspath(__file__))
        filename = os.path.join(os.path.join(directory, 'testDataFiles'), 'smallChimera.log')
        specs = open_data(filename, False)
        self._test_small_chimera_file_help(specs)


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()