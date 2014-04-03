"""
Module for creating sample data.

Create a current trace with specified events using
:func:`create_specified_data <pypore.sampledata.creator.create_specified_data>`.
"""

import os
import numpy as np

from pypore.filetypes.data_file import open_file


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
    :raises IOError: If the filename already exists and overwrite=False.

    >>> from pypore.sampledata.creator import create_specified_data as csd
    >>> filename = "test.h5"
    >>> n = 10000
    >>> events = [[100, 200, -.5], [3000, 1000, -.8]] # Creates an event starting at position 100, with length 200 and\
                                                      #  baseline change of -0.5.
    >>> create_specified_data(filename, n, 1.e4, baseline=5.0, noise_scale=1.0, events=events)
    """
    if not overwrite and os.path.exists(filename):
        raise IOError(
            "File already exists. Use a different filename, or call with overwrite=True to over-write existing files.")

    f = open_file(filename, mode='w', n_points=n, sample_rate=sample_rate)

    data = np.zeros(n) + baseline

    if noise_scale > 0:
        data += np.random.normal(scale=noise_scale, size=n)

    for event in events:
        data[event[0]:event[0] + event[1]] += event[2]

    f.root.data[:] = data[:]

    f.close()
