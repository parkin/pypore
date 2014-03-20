
cdef class ThresholdStrategy:
    """
    Abstract base class defining the behavior that a `ThresholdStrategy` should implement. These methods
    will be called by :py:func:`find_events`.

    A threshold is defined as a absolute value distance away from the baseline that the current must
    pass in order to trigger an event.

    Example implementations--

    * :py:class:`pypore.strategies.noise_based_threshold_strategy.NoiseBasedThresholdStrategy` -- Use the \
        noise level to define event start and end thresholds.

    """

    cpdef double compute_starting_threshold(self, double baseline, double variance):
        """compute_starting_threshold(double baseline, double variance)

        (Note: this is a cpdef wrapper for the cdef method :py:func:`compute_starting_threshold_c`.
        This method is accessible from Python, while :py:func:`compute_starting_threshold_c` is
        only accessible from Cython. However, to subclass this class, you must implement the
        :py:func:`compute_starting_threshold_c` version.)

        Compute the starting threshold for the event.

        :param double baseline: The current baseline.
        :param double variance: The variance of the baseline.
        :returns: The threshold (magnitude of the change) to trigger the start an event.

        """
        return self.compute_starting_threshold_c(baseline, variance)

    cdef double compute_starting_threshold_c(self, double baseline, double variance):
        """
        See docs for :py:func:`compute_starting_threshold`.
        """
        raise NotImplementedError

    cpdef double compute_ending_threshold(self, double baseline, double variance):
        """compute_ending_threshold(double baseline, double variance)

        (Note: this is a cpdef wrapper for the cdef method :py:func:`compute_ending_threshold_c`.
        This method is accessible from Python, while :py:func:`compute_ending_threshold_c` is
        only accessible from Cython. However, to subclass this class, you must implement the
        :py:func:`compute_ending_threshold_c` version.)

        Compute the starting threshold for the event.

        :param double baseline: The current baseline.
        :param double variance: The variance of the baseline.
        :returns: The threshold (magnitude of the change) to trigger the end of an event.

        """
        return self.compute_ending_threshold_c(baseline, variance)

    cdef double compute_ending_threshold_c(self, double baseline, double variance):
        raise NotImplementedError
