"""
Created on Aug 19, 2013

@author: `@parkin`_
"""
import unittest
import os.path
from pypore import cythonsetup
from pypore.io.chimera_reader import ChimeraReader


class TestChimeraReader(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_constructor_no_mat_spec(self):
        test_no_mat_chimera_files = ['testDataFiles/empty.log']
        for filename in test_no_mat_chimera_files:
            self.assertRaises(IOError, ChimeraReader, filename)

    def test_get_all_data(self):
        # Make sure path to chimera file is correct.
        directory = os.path.dirname(os.path.abspath(__file__))
        filename = os.path.join(os.path.join(directory, 'testDataFiles'), 'smallChimera.log')
        chimera_reader = ChimeraReader(filename)
        data = chimera_reader.get_all_data(False)
        self._test_small_chimera_file_help(data)

    def _test_small_chimera_file_help(self, data_all):
        self.assertEqual(len(data_all), 1, 'Too many data channels returned.')
        data = data_all[0]
        self.assertEqual(data.size, 10, 'Wrong data size returned.')
        self.assertAlmostEqual(data[0], 1.07818604, 7)
        self.assertAlmostEqual(data[9], 1.11694336, 7)

    def test_open_chimera_data(self):
        # Make sure path to chimera file is correct.
        directory = os.path.dirname(os.path.abspath(__file__))
        filename = os.path.join(os.path.join(directory, 'testDataFiles'), 'smallChimera.log')
        chimera_reader = ChimeraReader(filename)
        data = chimera_reader.get_all_data(False)
        self._test_small_chimera_file_help(data)


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()