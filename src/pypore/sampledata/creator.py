"""
Module for creating sample data.

- Create a current trace with specified events using \
    :func:`create_specified_data <pypore.sampledata.creator.create_specified_data>`.
- Create a current trace with random events using \
    :func:`create_random_data <pypore.sampledata.creator.create_random_data>`.
"""

import os
import numpy as np
from scipy.stats import geom

from pypore.filetypes.data_file import open_file


def create_random_data(filename, seconds, sample_rate, baseline=0.0, noise=None, event_rate=0, event_durations=None,
                       event_depths=None, overwrite=False):
    """
    Creates random sample data. Leaves the first 200 data points free of events.

    :param str filename: Filename for the data. If the file already exists and overwrite=False, an IOError is raised.
    :param float seconds: Number of seconds of data.
    :param float sample_rate: The sampling rate of the data, in Hz.
    :param float baseline: The baseline of the data, in uA.
    :param scipy.stats.distributions.rv_frozen noise: A frozen :mod:`scipy.stats` probability distribution\
            for the noise. An example normal distribution with mean 2 uA and std dev 3 uA is
            ::

                from scipy.stats import norm
                noise = norm(loc=2, scale=3)

            Default is no noise.
    :param float event_rate: Rate of events in Hz.
    :param scipy.stats.distributions.rv_frozen event_durations: A frozen :mod:`scipy.stats` probability distribution\
            for the event duration (in seconds).
    :param scipy.stats.distributions.rv_frozen event_depths: A frozen :mod:`scipy.stats` probability distribution\
            for the event depth, in uA.
    :param bool overwrite: Whether overwriting an existing file at filename is allowed. If false, and filename exists.\
            an IOError will be raised.
    :raises: :py:exc:`IOError` - If the filename already exists and overwrite=False.

    >>> from pypore.sampledata.creator import create_random_data
    >>> from scipy import stats
    >>> seconds = 1. # 1 second of data.
    >>> sample_rate = 1.e6 # 1 MHz sample rate.
    >>> event_rate = 100. # 100 events/sec, on average.
    >>> baseline = 10. # 10 uA baseline.
    >>> noise = stats.norm(scale=.5) # Normal distributed noise with mean of 0 std dev of 0.5 uA.
    >>> event_depths = stats.norm(loc=2., scale=1.) # Normal distributed events with mean of 2 and std dev of 1 uA.
    >>> event_durations = stats.norm(loc=100.e-6, scale=10.e-6) # Normal distributed event durations with mean of 100 us and std dev 10 us.
    >>> n_events = create_random_data('random_trace.h5', seconds, sample_rate, baseline, noise, event_rate, event_durations, event_depths)
    """
    if not overwrite and os.path.exists(filename):
        raise IOError(
            "File already exists. Use a different filename, or call with overwrite=True to over-write existing file.")

    n_points = int(seconds * sample_rate)
    f = open_file(filename, mode='w', n_points=n_points, sample_rate=sample_rate)

    data = np.zeros(n_points) + baseline

    if noise is not None:
        data += noise.rvs(size=n_points)

    event_count = 0
    if event_rate > 0:
        i = 200
        mean_length = event_durations.mean() * sample_rate
        expected_events = seconds * event_rate
        # Available space that is not events or the beginning of the data.
        free_space = n_points - expected_events * mean_length - i
        event_probability = expected_events/free_space
        # Use geometric distribution to find the next starting spot of an event.
        rv = geom(event_probability)
        while i < n_points:
            # get next event start distance
            i += rv.rvs()
            event_count += 1
            event_length = event_durations.rvs() * sample_rate
            event_depth_i = event_depths.rvs()
            if i + event_length > n_points:
                event_length = n_points - i
            data[i:i+event_length] += event_depth_i
            i += event_length

    f.root.data[:] = data[:]

    f.close()

    return event_count


def create_specified_data(filename, n, sample_rate, baseline=0.0, noise_scale=0.0, events=np.zeros(0), overwrite=False):
    """
    Creates a :class:`DataFile <pypore.filetypes.data_file.DataFile>` with sample event data.

    :param filename: The name for the new DataFile.
    :param int n: The number of samples in the data set.
    :param float sample_rate: The sample rate of the data set.
    :param float baseline: The baseline of the data. Default is 0.0.
    :param float noise_scale: Passed to :func:`numpy.random.normal`, it is the standard deviation of the Gaussian\
            noise added to the signal. Default is 0.0.
    :param events: A list of events to add to the baseline. Events are specified as\
            [starting_point, length, current_change]. So for example
            ::

                events = [[100,200,-.1], [560, 100, .6]]

            specifies 2 events:

        #. Starts at data position 100, with length 200, and current change of -.1.
        #. Starts at data position 560, with length of 100, and current change of +.6.

        Default is no events added.

    :param bool overwrite: Whether to overwrite an existing file at **filename**, if it exists. If **False**, and\
            filename already exists, an IOError will be raised. Default **False**.
    :raises: :exc:`IOError` - If the filename already exists and overwrite=False.

    >>> from pypore.sampledata.creator import create_specified_data as csd
    >>> filename = "test.h5"
    >>> n = 10000
    >>> events = [[100, 200, -.5], [3000, 1000, -.8]] # Creates an event starting at position 100, with length 200 and\
                                                      #  baseline change of -0.5.
    >>> create_specified_data(filename, n, 1.e4, baseline=5.0, noise_scale=1.0, events=events)
    """
    if not overwrite and os.path.exists(filename):
        raise IOError(
            "File already exists. Use a different filename, or call with overwrite=True to over-write existing file.")

    f = open_file(filename, mode='w', n_points=n, sample_rate=sample_rate)

    data = np.zeros(n) + baseline

    if noise_scale > 0:
        data += np.random.normal(scale=noise_scale, size=n)

    for event in events:
        data[event[0]:event[0] + event[1]] += event[2]

    f.root.data[:] = data[:]

    f.close()
