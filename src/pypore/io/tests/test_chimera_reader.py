"""
Created on Aug 19, 2013

@author: `@parkin`_
"""
import unittest
import os.path
import numpy as np
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
        chimera_reader.close()

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
        chimera_reader.close()

    def test_scaling(self):
        """
        Tests that the chimera data is scaled correctly, from a known test file.
        """
        directory = os.path.dirname(os.path.abspath(__file__))
        filename = os.path.join(directory, 'testDataFiles', 'spheres_20140114_154938_beginning.log')

        reader = ChimeraReader(filename)

        data = reader.get_all_data()[0]
        reader.close()

        baseline = np.mean(data)
        baseline_should_be = 7.57604  # Value gotten from original MATLAB script

        self.assertAlmostEqual(baseline, baseline_should_be, 2,
                               "Baseline scaled wrong. Should be {0}, got {1}.".format(baseline_should_be, baseline))

        std = np.std(data)
        std_should_be = 1.15445  # Value gotten from original MATLAB script

        self.assertAlmostEqual(std, std_should_be, 2,
                               "Baseline scaled wrong. Should be {0}, got {1}.".format(std_should_be, std))

    def test_decimate_scaling(self):
        """
        Tests that the scaling of the decimated data is the same as the undecimated data.
        """
        directory = os.path.dirname(os.path.abspath(__file__))
        filename = os.path.join(directory, 'testDataFiles', 'spheres_20140114_154938_beginning.log')

        reader = ChimeraReader(filename)

        data = reader.get_all_data()[0]
        data_decimated = reader.get_all_data(decimate=True)[0]
        reader.close()

        baseline = np.mean(data)
        baseline_decimate = np.mean(data_decimated)

        self.assertAlmostEqual(baseline, baseline_decimate, 2,
                               "Decimated baseline scaled wrong. Should be {0}, got {1}.".format(baseline,
                                                                                                 baseline_decimate))


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()

