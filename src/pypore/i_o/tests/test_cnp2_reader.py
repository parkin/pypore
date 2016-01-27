import unittest
import numpy as np
import os
import csv

from pypore.i_o.cnp2_reader import CNP2Reader
from pypore.i_o.tests.reader_tests import ReaderTests
import pypore.sampledata.testing_files as tf


class TestChimeraReader(unittest.TestCase, ReaderTests):
    reader_class = CNP2Reader

    default_test_data_files = [tf.get_abs_path('cnp_test.hex')]

    def test_constructor_no_mat_spec(self):
        """
        Tests that an IOError is raised when no .cfg config file is next to the .hex file.
        """
        test_no_cfg_file = tf.get_abs_path('cnp_empty.hex')
        for filename in test_no_cfg_file:
            self.assertRaises(IOError, CNP2Reader, filename)

    def test_get_all_data(self):
        # Make sure path to file is correct.
        filename = tf.get_abs_path('cnp_test.hex')
        cnp_reader = CNP2Reader(filename)
        data = cnp_reader.get_all_data(False)[0]

        csv_filename = filename[:-4] + '.csv'
        csv_data = self._get_test_csv_data(csv_filename)

        ratio = np.abs((csv_data-data) / csv_data)

        np.testing.assert_array_almost_equal(ratio, np.zeros_like(data))

        cnp_reader.close()

    def _get_test_csv_data(self, csv_filename):
        data = []
        with open(csv_filename, 'rb') as csvfile:
            csvreader = csv.reader(csvfile, delimiter=',')
            # skip first row
            csvreader.next()
            for row in csvreader:
                data.append(float(row[1]))
        return np.array(data) * 1.e9 # scale the data to nA

    def help_scaling(self):
        filename = tf.get_abs_path('cnp_test.hex')
        mean_should_be = 10.363  # Value gotten from the exported CSV file
        std_should_be = 4.6866  # Value gotten from the exported CSV file
        return [filename], [mean_should_be], [std_should_be]

    def help_scaling_decimated(self):
        filename = tf.get_abs_path('cnp_test.hex')
        return [filename]


if __name__ == "__main__":
    unittest.main()
