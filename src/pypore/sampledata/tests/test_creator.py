import unittest
import os

import numpy as np
from pypore.io import get_reader_from_filename

from pypore.sampledata.creator import create_specified_data


DIRECTORY = os.path.dirname(os.path.abspath(__file__))


class TestCreateSpecifiedData(unittest.TestCase):
    def test_output_filename_correct(self):
        filename = TestCreateSpecifiedData.__name__ + "_test_output_filename_correct.h5"

        if os.path.exists(filename):
            os.remove(filename)

        create_specified_data(filename, n=100, sample_rate=10)

        self.assertTrue(os.path.exists(filename))

        os.remove(filename)

    def test_opening_existing_filename_raises(self):
        """
        Tests that trying to open an existing filename raises an exception.
        """
        filename = os.path.join(DIRECTORY, TestCreateSpecifiedData.__name__ + "_test_opening_existing_filename.h5")

        if os.path.exists(filename):
            os.remove(filename)

        # create a blank file
        f = open(filename, mode='w')
        f.close()

        # try to create a data set on the same file
        self.assertRaises(IOError, create_specified_data, filename, 100, 100.)

        os.remove(filename)

    def test_opening_existing_filename_overwrite(self):
        """
        Tests that we can overwrite an existing filename if we use the overwrite parameter.
        """
        filename = os.path.join(DIRECTORY, TestCreateSpecifiedData.__name__ + "_test_opening_existing_filename.h5")

        if os.path.exists(filename):
            os.remove(filename)

        # create a blank file
        f = open(filename, mode='w')
        f.close()

        sample_rate = 1.e6
        baseline = 0.2
        n = 5000

        data_should_be = np.zeros(n) + baseline

        create_specified_data(filename=filename, n=n, sample_rate=sample_rate, baseline=baseline, noise_scale=0.0,
                              events=[], overwrite=True)

        self._test_params_equality(filename=filename, data_should_be=data_should_be, sample_rate=sample_rate)

        os.remove(filename)

    def _test_params_equality(self, filename, data_should_be, sample_rate):
        reader = get_reader_from_filename(filename)
        data_all = reader.get_all_data()
        out_data = data_all[0]
        out_sample_rate = reader.get_sample_rate()
        reader.close()

        self.assertEqual(sample_rate, out_sample_rate,
                         "Sample rates not equal. Wanted {0}, got {1}.".format(sample_rate, out_sample_rate))

        np.testing.assert_array_equal(out_data, data_should_be)

    def test_simple_baseline(self):
        """
        Tests that a no noise, no event returns just a baseline.
        """
        filename = os.path.join(DIRECTORY, TestCreateSpecifiedData.__name__ + "_test_simple_baseline.h5")

        if os.path.exists(filename):
            os.remove(filename)

        sample_rate = 1.e6
        baseline = 0.2
        n = 5000

        data_should_be = np.zeros(n) + baseline

        create_specified_data(filename=filename, n=n, sample_rate=sample_rate, baseline=baseline, noise_scale=0.0,
                              events=[])

        self._test_params_equality(filename=filename, data_should_be=data_should_be, sample_rate=sample_rate)

        os.remove(filename)

    def test_no_noise_specified_events(self):
        """
        Tests that with no noise and specified events we get the right matrix
        """
        filename = os.path.join(DIRECTORY, TestCreateSpecifiedData.__name__ + "_test_no_noise.h5")

        if os.path.exists(filename):
            os.remove(filename)

        sample_rate = 1.e6
        baseline = 1.0
        n = 5000

        events = [[100, 200., -.5], [1000, 500, -1.0], [3000, 1000, .2]]

        data_should_be = np.zeros(n) + baseline

        # add in the events to the data_should_be
        for event in events:
            data_should_be[event[0]:event[0] + event[1]] += event[2]

        create_specified_data(filename=filename, n=n, sample_rate=sample_rate, baseline=baseline, noise_scale=0.0,
                              events=events)

        self._test_params_equality(filename=filename, data_should_be=data_should_be, sample_rate=sample_rate)

        os.remove(filename)

    def test_noise_no_events(self):
        """
        Tests that noise is added correctly.
        """
        filename = os.path.join(DIRECTORY, TestCreateSpecifiedData.__name__ + "_test_no_noise.h5")

        if os.path.exists(filename):
            os.remove(filename)

        sample_rate = 1.e5
        baseline = 1.0
        n = 10000
        noise_scale = 1.

        create_specified_data(filename=filename, n=n, sample_rate=sample_rate, baseline=baseline,
                              noise_scale=noise_scale, events=[])

        reader = get_reader_from_filename(filename)
        data_all = reader.get_all_data()
        data = data_all[0]
        reader.close()

        self.assertEqual(n, data.size, "Unexpected array size. Wanted {0}, got {1}.".format(n, data.size))
        decimal = 1
        mean = np.mean(data)
        self.assertAlmostEqual(baseline, mean, decimal,
                               "Unexpected baseline. Wanted {0}, got {1}. Tested to {2} decimals.".format(baseline,
                                                                                                          mean,
                                                                                                          decimal))
        decimal = 1
        std_dev = np.std(data)
        self.assertAlmostEqual(noise_scale, std_dev, decimal,
                               msg="Unexpected stddev. Wanted{0}, got {1}. Tested to {2} decimals.".format(noise_scale,
                                                                                                           std_dev,
                                                                                                           decimal))

        os.remove(filename)
