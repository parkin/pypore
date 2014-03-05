"""

"""

import unittest
import os
from pypore.dataFile import DataFile
from pypore.dataFileOpener import open_data

from pypore.fileConverter import convert_file

import numpy as np


class TestFileConverter(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_convert_file_set_output_filename(self):
        filename = os.path.dirname(os.path.realpath(__file__))
        filename = os.path.join(filename, 'testDataFiles', 'chimera_1event.log')

        output_filename_set = "out.h5"

        output_filename = convert_file(filename, output_filename=output_filename_set)

        # Test that we can set the output filename
        self.assertEqual(output_filename, output_filename_set, "output_filename not correct")

        os.remove(output_filename)

    def test_convert_file_matrix_equality(self):
        filename = os.path.dirname(os.path.realpath(__file__))
        filename = os.path.join(filename, 'testDataFiles', 'chimera_1event.log')

        output_filename_set = "out.h5"

        output_filename = convert_file(filename, output_filename=output_filename_set)

        orig = open_data(filename)
        orig_datas = orig['data']
        orig_sample_rate = orig['sample_rate']

        self.assertEqual(len(orig_datas), 1)

        out = open_data(output_filename)
        out_datas = out['data']
        out_sample_rate = out['sample_rate']

        self.assertEqual(len(out_datas), 1)

        orig_data = orig_datas[0]
        out_data = out_datas[0]

        # assert sample rates are equal
        threshold = -1*int(np.log10(orig_sample_rate)) + 4
        print threshold
        self.assertAlmostEqual(orig_sample_rate, out_sample_rate, threshold)

        # assert the two arrays are equal
        np.testing.assert_array_equal(orig_data, out_data)

        os.remove(output_filename)


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()

