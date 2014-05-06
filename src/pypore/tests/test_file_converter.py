"""

"""

import unittest
import os

import numpy as np

from pypore.i_o import get_reader_from_filename
from pypore.file_converter import convert_file
from pypore.i_o.data_file_reader import DataFileReader
from pypore.tests.util import _test_file_manager
import pypore.sampledata.testing_files as tf


DIRECTORY = os.path.dirname(os.path.abspath(__file__))


class TestFileConverter(unittest.TestCase):
    @_test_file_manager(DIRECTORY)
    def test_convert_file_set_output_filename(self, filename):
        """
        Tests that the output filename can be set correctly.
        """
        data_filename = tf.get_abs_path('chimera_1event.log')

        output_filename = convert_file(data_filename, output_filename=filename)

        # Test that we can set the output filename
        self.assertEqual(output_filename, filename, "output_filename not correct")

    @_test_file_manager(DIRECTORY)
    def test_convert_chimera_file_equality(self, filename):
        """
        Test that the original/converted matrices and sample rates are the same for one-channel data.
        """
        data_filename = tf.get_abs_path('chimera_1event.log')

        output_filename = convert_file(data_filename, output_filename=filename)

        orig_reader = get_reader_from_filename(data_filename)
        orig_data_all = orig_reader.get_all_data()
        orig_sample_rate = orig_reader.get_sample_rate()

        self.assertEqual(len(orig_data_all), 1)

        out_reader = DataFileReader(output_filename)
        out_data_all = out_reader.get_all_data()
        out_sample_rate = out_reader.get_sample_rate()

        self.assertEqual(len(out_data_all), 1)

        orig_data = orig_data_all[0]
        out_data = out_data_all[0]

        # assert sample rates are equal
        self.assertAlmostEqual(1.0 * orig_sample_rate / out_sample_rate, 1, 4)

        # assert the two arrays are equal
        np.testing.assert_array_equal(orig_data, out_data)

        orig_reader.close()
        out_reader.close()


from pypore.file_converter import concat_files
from pypore.file_converter import SamplingRatesMismatchError


class TestConcatFiles(unittest.TestCase):
    def test_default_output_filename(self):
        """
        Tests that the default output filename is correctly generated from the input file names.
        """
        file_names = [tf.get_abs_path('chimera_1event_2levels.log'), tf.get_abs_path('chimera_1event.log')]

        output_filename = concat_files(file_names)

        self.assertTrue(os.path.exists(output_filename))

        # Check that it's saved in the current directory
        self.assertEqual(output_filename[0:len('chimera_1event')], 'chimera_1event')

        # Check the correct file extension
        self.assertEqual(output_filename[-len('.h5'):], '.h5')

        self.assertIn('_concatenated_', output_filename,
                      "Default output filename ''{0}'' should contain ''_concatenated_''")

        os.remove(output_filename)

    @_test_file_manager(DIRECTORY)
    def test_set_output_filename(self, filename):
        file_names = [tf.get_abs_path('chimera_1event_2levels.log'), tf.get_abs_path('chimera_1event.log')]

        output_filename = concat_files(file_names, output_filename=filename)

        self.assertEqual(output_filename, filename)
        self.assertTrue(os.path.exists(output_filename))

    @_test_file_manager(DIRECTORY)
    def test_different_sample_rate_no_resample(self, filename):
        """
        Tests that an error is thrown if the files have different sample rates and we do not want to resample.
        """

        file_names = [tf.get_abs_path('heka_1.5s_mean5.32p_std2.76p.hkd'), tf.get_abs_path('chimera_1event.log')]

        self.assertRaises(SamplingRatesMismatchError, concat_files, file_names, output_filename=filename)

    def test_single_file_fail(self):
        """
        Tests that an exception is thrown if less than 2 file names are passed in the list.
        """
        file_names = ['hi.txt']

        self.assertRaises(ValueError, concat_files, file_names)
        self.assertRaises(ValueError, concat_files, [])

    @_test_file_manager(DIRECTORY)
    def test_original_files_unmodified(self, filename):
        file1 = tf.get_abs_path('chimera_1event_2levels.log')
        file2 = tf.get_abs_path('chimera_1event.log')

        reader1 = get_reader_from_filename(file1)
        reader2 = get_reader_from_filename(file2)

        sample_rate1_orig = reader1.get_sample_rate()
        sample_rate2_orig = reader2.get_sample_rate()

        data1_orig = reader1.get_all_data()[0]
        data2_orig = reader2.get_all_data()[0]

        reader1.close()
        reader2.close()

        concat_files([file1, file2], output_filename=filename)

        reader1 = get_reader_from_filename(file1)
        reader2 = get_reader_from_filename(file2)

        reader_out = get_reader_from_filename(filename)

        sample_rate1_final = reader1.get_sample_rate()
        sample_rate2_final = reader2.get_sample_rate()

        self.assertEqual(sample_rate1_final, sample_rate1_orig,
                         "Sample rate changed. Was {0}, now {1}.".format(sample_rate1_orig, sample_rate1_final))
        self.assertEqual(sample_rate2_final, sample_rate2_orig,
                         "Sample rate changed. Was {0}, now {1}.".format(sample_rate2_orig, sample_rate2_final))

        data1 = reader1.get_all_data()[0]
        data2 = reader2.get_all_data()[0]

        np.testing.assert_array_equal(data1, data1_orig)
        np.testing.assert_array_equal(data2, data2_orig)

        reader1.close()
        reader2.close()
        reader_out.close()

    @_test_file_manager(DIRECTORY)
    def test_correct_data(self, filename):
        file1 = tf.get_abs_path('chimera_1event_2levels.log')
        file2 = tf.get_abs_path('chimera_1event.log')

        concat_files([file1, file2], output_filename=filename)

        reader1 = get_reader_from_filename(file1)
        reader2 = get_reader_from_filename(file2)

        reader_out = get_reader_from_filename(filename)

        sample_rate1 = reader1.get_sample_rate()
        sample_rate2 = reader2.get_sample_rate()
        sample_rate_out = reader_out.get_sample_rate()

        self.assertEqual(sample_rate_out, sample_rate1,
                         "Unexpected sample rate. Should be {0}, was {1}.".format(sample_rate1, sample_rate_out))
        self.assertEqual(sample_rate_out, sample_rate2,
                         "Unexpected sample rate. Should be {0}, was {1}.".format(sample_rate2, sample_rate_out))

        data1 = reader1.get_all_data()[0]
        data2 = reader2.get_all_data()[0]

        data_out_should_be = np.zeros(data1.size + data2.size)
        data_out_should_be[:data1.size] = data1[:]
        data_out_should_be[data1.size:] = data2[:]

        data_out = reader_out.get_all_data()[0]

        np.testing.assert_array_equal(data_out, data_out_should_be)

        reader1.close()
        reader2.close()
        reader_out.close()


if __name__ == "__main__":
    unittest.main()

