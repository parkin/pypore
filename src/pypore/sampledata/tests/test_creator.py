import unittest
import os

import scipy.stats as stats
import numpy as np
from pypore.io import get_reader_from_filename

from pypore.sampledata.creator import create_specified_data
from pypore.sampledata.creator import create_random_data
from pypore.event_finder import find_events
from pypore.filetypes.event_database import EventDatabase

import inspect
from functools import wraps

DIRECTORY = os.path.dirname(os.path.abspath(__file__))


def _test_file_manager(directory):
    """
    Decorator.

    Creates a test filename based on the decorated function's name. Makes sure this file is removed before and after
    the decorated function is called. Calls the decorated function with an extra named parameter filename.

    :param directory: Directory in which to save the file.
    """

    def real_dec(function):
        @wraps(function)
        def wrap(*args, **kwargs):
            arg_spec = inspect.getargspec(function)
            filename = ""
            if 'self' in arg_spec.args:
                filename += args[0].__class__.__name__ + "_"
            filename += function.__name__ + '.h5'

            filename = os.path.join(directory, filename)

            if os.path.exists(filename):
                os.remove(filename)

            function(*args, filename=filename, **kwargs)

            os.remove(filename)

        return wrap

    return real_dec


def _test_params_equality(self, filename, data_should_be, sample_rate):
    """
    Tests that the data and sample_rate in filename equal data_should_be and sample_rate, respectively.
    """
    reader = get_reader_from_filename(filename)
    data_all = reader.get_all_data()
    out_data = data_all[0]
    out_sample_rate = reader.get_sample_rate()
    reader.close()

    self.assertEqual(sample_rate, out_sample_rate,
                     "Sample rates not equal. Wanted {0}, got {1}.".format(sample_rate, out_sample_rate))

    np.testing.assert_array_equal(out_data, data_should_be)


class TestCreateRandomData(unittest.TestCase):
    @_test_file_manager('.')
    def test_output_filename_correct(self, filename):
        """
        Tests that the output filename is correct.
        """
        create_random_data(filename, seconds=1., sample_rate=10.)

        self.assertTrue(os.path.exists(filename))

    @_test_file_manager(DIRECTORY)
    def test_opening_existing_filename_raises(self, filename):
        """
        Tests that trying to open an existing filename without setting overwrite=True will raise an IOError.
        """
        # create a blank file
        f = open(filename, mode='w')
        f.close()

        self.assertRaises(IOError, create_random_data, filename, seconds=1., sample_rate=10.)

    @_test_file_manager(DIRECTORY)
    def test_opening_existing_with_overwrite(self, filename):
        """
        Tests that we can overwrite an existing file with overwrite=True
        """
        # create a blank file
        f = open(filename, mode='w')
        f.close()

        seconds = 1.
        sample_rate = 1.
        baseline = 1.

        create_random_data(filename, seconds=seconds, sample_rate=sample_rate, baseline=baseline, overwrite=True)

        self.assertTrue(os.path.exists(filename))

    @_test_file_manager(DIRECTORY)
    def test_baseline_no_noise_no_events(self, filename):
        """
        Tests that with only the baseline, we create the right data.
        """
        seconds = 1.
        sample_rate = 1.e6
        baseline = 1.

        event_rate = 0

        event_duration = stats.norm(loc=100.e-6, scale=10.e-6)
        event_depth = stats.norm(loc=.5, scale=.05)

        data_should_be = np.zeros(int(seconds * sample_rate)) + baseline

        create_random_data(filename=filename, seconds=seconds, sample_rate=sample_rate, baseline=baseline,
                           event_rate=event_rate, event_duration=event_duration, event_depth=event_depth)

        _test_params_equality(self, filename, data_should_be, sample_rate)

    @_test_file_manager(DIRECTORY)
    def test_number_of_events(self, filename):
        """
        Tests that the number of events is roughly correct. The number of events should be random, which is why
        only roughly.
        """
        seconds = 1.
        sample_rate = 1.e6
        baseline = 1.
        event_rate = 10.
        event_duration = stats.norm(loc=100.e-6, scale=5.e-6)
        event_depth = stats.norm(loc=-1., scale=.05)
        noise = stats.norm(scale=0.02)

        n_events_returned = create_random_data(filename=filename, seconds=seconds, sample_rate=sample_rate,
                                               baseline=baseline, noise=noise,
                                               event_rate=event_rate, event_duration=event_duration,
                                               event_depth=event_depth)

        save_file_name = filename[:-len('.h5')] + 'Events.h5'
        if os.path.exists(save_file_name):
            os.remove(save_file_name)
        event_database = find_events([filename], save_file_names=[save_file_name])[0]

        ed = EventDatabase(event_database)

        n_events = ed.get_event_count()

        n_events_should_be = event_rate * seconds

        difference = abs(n_events - n_events_should_be)
        self.assertLessEqual(difference, 3,
                             "Unexpected number of events. Should be {0}, was {1}.".format(n_events_should_be,
                                                                                           n_events))
        self.assertEqual(n_events, n_events_returned,
                         "Number of events returned from function different than actual value. "
                         "Should be {0}, got {1}".format(n_events, n_events_returned))

        ed.close()
        os.remove(event_database)

    @_test_file_manager(DIRECTORY)
    def test_noise(self, filename):
        """
        Tests that the noise is added correctly(its mean and std_dev are correct).
        """
        seconds = 1.
        sample_rate = 1.e6
        baseline = 1.
        noise_loc = 1.
        noise_scale = 0.6
        noise = stats.norm(loc=noise_loc, scale=noise_scale)

        create_random_data(filename, seconds=seconds, sample_rate=sample_rate, baseline=baseline,
                           noise=noise)

        reader = get_reader_from_filename(filename)
        data_all = reader.get_all_data()
        data = data_all[0]

        mean = np.mean(data)
        mean_should_be = baseline + noise_loc
        self.assertAlmostEqual(mean, mean_should_be, 1,
                               "Unexpected mean. Wanted {0}, got {1}.".format(mean_should_be, mean))

        std_dev = np.std(data)
        self.assertAlmostEqual(noise_scale, std_dev, 1, "Unexpected standard deviation.  "
                                                        "Wanted {0}, got {1}".format(noise_scale, std_dev))

    @_test_file_manager(DIRECTORY)
    def test_event_params(self, filename):
        """
        Tests that setting the event depth and duration give correct values.
        """
        seconds = 5.
        sample_rate = 1.e6
        baseline = 10.
        event_rate = 100.
        event_duration_loc = 1.e-4
        event_duration_scale = 5.e-6
        event_duration = stats.norm(loc=event_duration_loc, scale=event_duration_scale)
        event_depth_loc = -1.
        event_depth_scale = .05
        event_depth = stats.norm(loc=-1., scale=.05)
        noise = stats.norm(scale=0.01)

        n_events_returned = create_random_data(filename, seconds=seconds, sample_rate=sample_rate,
                                               baseline=baseline, event_rate=event_rate,
                                               event_duration=event_duration, event_depth=event_depth,
                                               noise=noise)

        save_file_name = filename[:-len('.h5')] + 'Events.h5'
        if os.path.exists(save_file_name):
            os.remove(save_file_name)
        event_database = find_events([filename], save_file_names=[save_file_name])[0]

        ed = EventDatabase(event_database)

        count = ed.get_event_count()
        count_should_be = event_rate * seconds
        diff = abs(count - count_should_be)
        self.assertLessEqual(diff, 100, "Unexpected number of events. "
                                        "Expected {0}, was {1}.".format(count_should_be, count))

        table_sample_rate = ed.get_sample_rate()
        durations = [x['event_length'] / table_sample_rate for x in ed.get_event_table().iterrows()]
        depths = [x['current_blockage'] for x in ed.get_event_table().iterrows()]

        mean_duration = np.mean(durations)
        self.assertAlmostEqual(event_duration_loc, mean_duration, 5, "Unexpected mean event duration.  "
                                                                     "Wanted {0}, got {1}.".format(event_duration_loc,
                                                                                                   mean_duration))

        mean_depth = np.mean(depths)
        self.assertAlmostEqual(event_depth_loc, mean_depth, 1, "Unexpected mean event depth. "
                                                               "Wanted {0}, got {1}.".format(event_depth_loc,
                                                                                             mean_depth))

        ed.close()
        os.remove(event_database)


class TestCreateSpecifiedData(unittest.TestCase):
    @_test_file_manager('.')
    def test_output_filename_correct(self, filename):
        create_specified_data(filename, n=100, sample_rate=10)

        self.assertTrue(os.path.exists(filename))

    @_test_file_manager(DIRECTORY)
    def test_opening_existing_filename_raises(self, filename):
        """
        Tests that trying to open an existing filename raises an exception.
        """
        # create a blank file
        f = open(filename, mode='w')
        f.close()

        # try to create a data set on the same file
        self.assertRaises(IOError, create_specified_data, filename, 100, 100.)

    @_test_file_manager(DIRECTORY)
    def test_opening_existing_filename_overwrite(self, filename):
        """
        Tests that we can overwrite an existing filename if we use the overwrite parameter.
        """
        # create a blank file
        f = open(filename, mode='w')
        f.close()

        sample_rate = 1.e6
        baseline = 0.2
        n = 5000

        data_should_be = np.zeros(n) + baseline

        create_specified_data(filename=filename, n=n, sample_rate=sample_rate, baseline=baseline, noise_scale=0.0,
                              events=[], overwrite=True)

        _test_params_equality(self, filename=filename, data_should_be=data_should_be, sample_rate=sample_rate)

    @_test_file_manager(DIRECTORY)
    def test_simple_baseline(self, filename):
        """
        Tests that a no noise, no event returns just a baseline.
        """
        sample_rate = 1.e6
        baseline = 0.2
        n = 5000

        data_should_be = np.zeros(n) + baseline

        create_specified_data(filename=filename, n=n, sample_rate=sample_rate, baseline=baseline, noise_scale=0.0,
                              events=[])

        _test_params_equality(self, filename=filename, data_should_be=data_should_be, sample_rate=sample_rate)

    @_test_file_manager(DIRECTORY)
    def test_no_noise_specified_events(self, filename):
        """
        Tests that with no noise and specified events we get the right matrix
        """
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

        _test_params_equality(self, filename=filename, data_should_be=data_should_be, sample_rate=sample_rate)

    @_test_file_manager(DIRECTORY)
    def test_noise_no_events(self, filename):
        """
        Tests that noise is added correctly.
        """
        sample_rate = 1.e5
        baseline = 1.0
        n = 100000
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
