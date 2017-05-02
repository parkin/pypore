"""
Core data types.
"""

import numpy as np


class MetaSegment(object):
    """
    MetaSegment contains the metadata of a :py:class:`Segment`.

    Attributes:

        * sample_rate - The sampling rate of the segment.
        * shape - The shape of the data.
        * size - Number of data points in the Segment.

    Methods:

        * max - Returns the maximum value of the Segment.
        * mean - Returns the mean of the Segment.
        * min - Returns the minimum value in the Segment.
        * std - Returns the standard deviation of the Segment.

    """

    _sample_rate = None
    _shape = None
    _size = None
    _max = None
    _mean = None
    _min = None
    _std = None

    _ndim = None

    def __init__(self, sample_rate=None, shape=None, size=None, maximum=None, mean=None, minimum=None, std=None):
        self._sample_rate = sample_rate
        self._shape = shape
        if shape is not None:
            self._ndim = len(shape)
        self._size = size

        self._max = maximum
        self._mean = mean
        self._min = minimum
        self._std = std

    @classmethod
    def from_segment(cls, segment):
        """
        Creates a MetaSegment with all of the metadata from data.

        :param data: :py:class:`Segment` to be converted to MetaSegment.

        >>> from pypore.core import Segment, MetaSegment
        >>> import numpy as np
        >>> s = Segment(np.random.random(100))
        >>> ms = MetaSegment.from_segment(s)

        """
        return cls(segment.sample_rate, segment.shape, segment.size, segment.max(), segment.mean(), segment.min(),
                   segment.std())

    def max(self):
        """
        Returns the MetaSegment's attribute.
        :return: The maximum value of the MetaSegment.
        """
        return self._max

    def mean(self):
        """
        Returns the mean of the data.
        :return: The mean of the data.
        """
        # Cache the mean
        return self._mean

    def min(self):
        """
        Returns the min of the data.
        :return: The minimum value of the data.
        """
        return self._min

    def std(self):
        """
        :return: The standard deviation of the data.
        """
        return self._std

    @property
    def ndim(self):
        """
        Returns the number of dimensions in the data set.
        """
        return self._ndim

    @property
    def sample_rate(self):
        """
        Returns the sample rate of the MetaSegment.
        :return:
        """
        return self._sample_rate

    @property
    def shape(self):
        """
        Returns the shape of the MetaSegment data.
        :return: The shape of the MetaSegment data.
        """
        return self._shape

    @property
    def size(self):
        """
        :return: The number of data points in the Segment.
        """
        return self._size


class Segment(object):
    """
    Segment is a segment of current data.

    Slicing a Segment returns a Segment object.

    >>> from pypore.core import Segment
    >>> import numpy as np
    >>> s = Segment(np.random.random(100))
    >>> s_first_fifty = s[:50]
    >>> isinstance(s_first_fifty, Segment)
    True

    It contains the same attributes and methods as a :py:class:`MetaSegment`.

    Attributes:

        * sample_rate - The sampling rate of the segment.
        * shape - The shape of the data.
        * size - Number of data points in the Segment.

    Methods:

        * max - Returns the maximum value of the Segment.
        * mean - Returns the mean of the Segment.
        * min - Returns the minimum value in the Segment.
        * std - Returns the standard deviation of the Segment.

    """

    # Cached values
    _max = None
    _mean = None
    _min = None
    _std = None

    # Cached properties
    _ndim = None
    _shape = None
    _size = None

    def __array__(self):
        """
        Returns this object as an array.

        This method allows np.array(segment) to work.
        :return: Returns this object as a numpy array.
        """
        return np.array(self._data)

    def __init__(self, data, sample_rate=0.0):
        """
        Initialize a new Segment object with the passed in data.
        :param data: Data defining the segment. Can pass in any data that is slice-able, like a numpy array, list, etc.
        :param sample_rate: Sampling rate of the data, in Hz. Default is 0.0 Hz.
        """
        self._data = data
        self.sample_rate = sample_rate

    def __getitem__(self, item):
        if isinstance(item, int):
            # Return single number.
            return self._data[item]
        else:
            # reduce sample rate if the slice has steps
            sample_rate = self.sample_rate
            if isinstance(item, slice) and item.step is not None and item.step > 1:
                sample_rate /= item.step

            # Return the slice as another Segment object.
            return Segment(self._data[item], sample_rate)

    def __len__(self):
        return self.shape[0]

    def __iter__(self):
        return iter(self._data)

    def max(self):
        """
        Returns the max of the Segment's data.
        :return: The maximum value of the Segment's data.
        """
        # Cache the max
        if self._max is None:
            self._max = np.max(self._data)
        return self._max

    def mean(self):
        """
        Returns the mean of the data.
        :return: The mean of the data.
        """
        # Cache the mean
        if self._mean is None:
            self._mean = np.mean(self._data)
        return self._mean

    def min(self):
        """
        Returns the min of the data.
        :return: The minimum value of the data.
        """
        # Cache the min
        if self._min is None:
            self._min = np.min(self._data)
        return self._min

    def std(self):
        """
        :return: The standard deviation of the data.
        """
        # Cache the std deviation.
        if self._std is None:
            self._std = np.std(self._data)
        return self._std

    @property
    def ndim(self):
        """
        Returns the number of dimensions in the data set.
        """
        if self._ndim is None:
            try:
                self._ndim = self._data.ndim
            except AttributeError:
                self._ndim = np.ndim(self._data)
        return self._ndim

    @property
    def shape(self):
        """
        Returns the shape of the Segment's data.
        :return: The shape of the Segment's data.
        """
        if self._shape is None:
            try:
                # First try to get the shape of the data as if _data is a numpy array.
                self._shape = self._data.shape
            except AttributeError:
                self._shape = np.shape(self._data)
        return self._shape

    @property
    def size(self):
        """
        :return: The number of data points in the Segment.
        """
        if self._size is None:
            try:
                self._size = self._data.size
            except AttributeError:
                self._size = np.size(self._data)
        return self._size
