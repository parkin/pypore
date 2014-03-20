import numpy as np
cimport numpy as np

cdef class BaselineStrategy:
    """
    This is an abstract class defining how :py:func:`find_events` handles computing the baseline.

    Example implementations--

    * :py:class:`FixedBaselineStrategy` -- baseline is fixed.
    * :py:class:`AdaptiveBaselineStrategy` -- applies a first-order recursive filter to adapt the\
        baseline as the data changes.

    When a :py:class:`BaselineStrategy` is passed to :py:func:`find_events`,
    :py:func:`find_events` will call the following methods, so Subclasses must override
    these methods.
    """

    def __init__(self, double baseline=0.0, double variance=0.0):
        """(double baseline=0.0, double variance=0.0)

        :param double baseline: baseline
        :param double variance: variance
        """
        self.baseline = baseline
        self.variance = variance

    cpdef double compute_baseline(self, double data_point):
        """compute_baseline(double data_point)

        (Note: this is a cpdef wrapper around the cdef function :py:func:`compute_baseline_c`.
        This function can be called directly from Python. If calling from Cython,
        you can call the cdef version :py:func:`compute_baseline_c`)

        When a :py:class:`BaselineType` or subclass is passed in a :py:class:`Parameters` object to \
        :py:func:`find_events`, it will call this method with each new data_point as it linearly \
        loops through its data.

        This method will raise a NotImplementedError, so it should be overridden.
        Subclasses can use this data_point to compute/modify the baseline.

        :param double data_point: When called from :py:func:`find_events`, data_point is the most \
            recent data point.
        :returns: the new baseline. Subclasses should return \
            `BaselineStrategy.compute_baseline_c(self, data_point)`.
        """
        return self.compute_baseline_c(data_point)

    cdef double compute_baseline_c(self, double data_point):
        """
        See docs for :py:func:`compute_baseline`.
        """
        raise NotImplementedError

    cpdef double compute_variance(self, double data_point):
        """compute_variance(double data_point)

        (Note: this is a cpdef wrapper around the cdef function :py:func:`compute_variance_c`.
        This function can be called directly from Python. If calling from Cython,
        you can call the cdef version :py:func:`compute_variance_c`)

        When a :py:class:`BaselineType` or subclass is passed in a :py:class:`Parameters` object to \
        :py:func:`find_events`, it will call this method with each new data_point as it linearly \
        loops through its data.

        This method will raise a NotImplementedError, so it should be overridden.
        Subclasses can use this data_point to compute/modify the variance.

        :param double data_point: When called from :py:func:`find_events`, data_point is the most \
            recent data point.
        :returns: the new variance. Subclasses should return \
            `BaselineStrategy.compute_variance_c(self, data_point)`.
        """
        return self.compute_variance_c(data_point)

    cdef double compute_variance_c(self, double data_point):
        """
        See docs for :py:func:`compute_variance`.
        """
        raise NotImplementedError

    cdef void initialize(self, np.ndarray[DTYPE_t] initialization_points):
        """initialize(double baseline)

        (Note: this is a cpdef wrapper around the cdef function :py:func:`initialize_c`.
        This function can be called directly from Python. If calling from Cython,
        you can call the cdef version :py:func:`initialize_c`)

        When a :py:class:`BaselineType` or subclass is passed in a :py:class:`Parameters` object to \
        :py:func:`find_events`, it will call this method with the first 100 data points or so.

        This method will raise a NotImplementedError, so it should be overridden.
        Subclasses can use the initialization_points initialize_c the baseline and the variance.

        :param numpy.ndarray[numpy.float] initialization_points: When called from \
            :py:func:`find_events`, this is the first 100 data points or so.
        """
        self.initialize_c(initialization_points)

    cdef void initialize_c(self, np.ndarray[DTYPE_t] initialization_points):
        """
        See the docs for :py:func:`initialize`.
        """
        raise NotImplementedError

    cpdef double get_baseline(self):
        """get_baseline()

        (Note: this is a cpdef wrapper around the cdef function :py:func:`get_baseline_c`.
        This function can be called directly from Python. If calling from Cython,
        you can call the cdef version :py:func:`get_baseline_c`)

        :returns: the current baseline.
        """
        return self.get_baseline_c()

    cdef double get_baseline_c(self):
        """
        See docs for :py:func:`get_baseline`.
        """
        return self.baseline

    cdef double get_variance(self):
        """get_variance()

        (Note: this is a cpdef wrapper around the cdef function :py:func:`get_variance_c`.
        This function can be called directly from Python. If calling from Cython,
        you can call the cdef version :py:func:`get_variance_c`)

        :returns: the current variance.
        """
        return self.get_variance_c()

    cdef double get_variance_c(self):
        """
        See docs for :py:func:`get_variance`
        """
        return self.variance