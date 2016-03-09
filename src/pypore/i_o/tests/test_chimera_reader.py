"""
@author: `@parkin`_
"""
import unittest

from pypore.i_o.chimera_reader import ChimeraReader
from pypore.i_o.tests.reader_tests import ReaderTests
import pypore.sampledata.testing_files as tf


class TestChimeraReader(unittest.TestCase, ReaderTests):
    reader_class = ChimeraReader

    default_test_data_files = [tf.get_abs_path('chimera_small.log'),
                               tf.get_abs_path('spheres_20140114_154938_beginning.log')]

    def test_constructor_no_mat_spec(self):
        """
        Tests that an IOError is raised when no .mat spec file is next to the .log file.
        """
        test_no_mat_chimera_files = tf.get_abs_path('chimera_empty.log')
        for filename in test_no_mat_chimera_files:
            self.assertRaises(IOError, ChimeraReader, filename)

    def test_get_all_data(self):
        # Make sure path to chimera file is correct.
        filename = tf.get_abs_path('chimera_small.log')
        chimera_reader = ChimeraReader(filename)
        data = chimera_reader.get_all_data(False)
        self._test_small_chimera_file_help(data)
        chimera_reader.close()

    def _test_small_chimera_file_help(self, data_all):
        self.assertEqual(len(data_all), 1, 'Too many data channels returned.')
        data = data_all[0]
        self.assertEqual(data.size, 10, 'Wrong data size returned.')
        self.assertAlmostEqual(data[0], 17.45518, 3)
        self.assertAlmostEqual(data[9], 18.0743, 3)

    def help_scaling(self):
        filename = tf.get_abs_path('spheres_20140114_154938_beginning.log')
        mean_should_be = 7.57604  # Value gotten from original MATLAB script
        std_should_be = 1.15445  # Value gotten from original MATLAB script
        return [filename], [mean_should_be], [std_should_be]

    def help_scaling_decimated(self):
        filename = tf.get_abs_path('spheres_20140114_154938_beginning.log')
        return [filename]


if __name__ == "__main__":
    unittest.main()
