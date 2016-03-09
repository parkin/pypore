import unittest
import numpy as np
import os
import csv

from pypore.i_o.data_file_reader import DataFileReader
from pypore.i_o.tests.reader_tests import ReaderTests
import pypore.sampledata.testing_files as tf


class TestDataFileReader(unittest.TestCase, ReaderTests):
    reader_class = DataFileReader

    default_test_data_files = [tf.get_abs_path('chimera_small.h5'),
                               tf.get_abs_path('spheres_20140114_154938_beginning.h5')]

    def _test_small_chimera_file_help(self, data_all):
        self.assertEqual(len(data_all), 1, 'Too many data channels returned.')
        data = data_all[0]
        self.assertEqual(data.size, 10, 'Wrong data size returned.')
        self.assertAlmostEqual(data[0], 17.45518, 3)
        self.assertAlmostEqual(data[9], 18.0743, 3)

    def test_get_all_data(self):
        # Make sure path to file is correct.
        filename = tf.get_abs_path('chimera_small.h5')
        reader = self.reader_class(filename)
        data = reader.get_all_data(False)

        self._test_small_chimera_file_help(data)
        reader.close()

    def help_scaling(self):
        filename = tf.get_abs_path('spheres_20140114_154938_beginning.h5')
        mean_should_be = 7.57604  # Value gotten from original MATLAB script
        std_should_be = 1.15445  # Value gotten from original MATLAB script
        return [filename], [mean_should_be], [std_should_be]

    def help_scaling_decimated(self):
        filename = tf.get_abs_path('spheres_20140114_154938_beginning.h5')
        return [filename]


if __name__ == "__main__":
    unittest.main()
