"""

"""

import unittest
import os
from pypore.io import get_reader_from_filename
from pypore.io.pypore_reader import PyporeReader
from pypore.file_converter import convert_file

import numpy as np


class TestFileConverter(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_convert_file_set_output_filename(self):
        """
        Tests that the output filename can be set correctly.
        """
        filename = os.path.dirname(os.path.realpath(__file__))
        filename = os.path.join(filename, 'testDataFiles', 'chimera_1event.log')

        output_filename_set = "out.h5"

        output_filename = convert_file(filename, output_filename=output_filename_set)

        # Test that we can set the output filename
        self.assertEqual(output_filename, output_filename_set, "output_filename not correct")

        os.remove(output_filename)

    def test_convert_chimera_file_equality(self):
        """
        Test that the original/converted matrices and sample rates are the same for one-channel data.
        """
        # TODO add tests for multichannel data.
        filename = os.path.dirname(os.path.realpath(__file__))
        filename = os.path.join(filename, 'testDataFiles', 'chimera_1event.log')

        output_filename_set = "out.h5"

        output_filename = convert_file(filename, output_filename=output_filename_set)

        orig_reader = get_reader_from_filename(filename)
        orig_data_all = orig_reader.get_all_data()
        orig_sample_rate = orig_reader.get_sample_rate()

        self.assertEqual(len(orig_data_all), 1)

        out_reader = PyporeReader(filename)
        out_data_all = out_reader.get_all_data()
        out_sample_rate = out_reader.get_sample_rate()

        self.assertEqual(len(out_data_all), 1)

        orig_data = orig_data_all[0]
        out_data = out_data_all[0]

        # assert sample rates are equal
        self.assertAlmostEqual(1.0*orig_sample_rate/out_sample_rate, 1, 4)

        # assert the two arrays are equal
        np.testing.assert_array_equal(orig_data, out_data)

        orig_reader.close()

        os.remove(output_filename)


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()

