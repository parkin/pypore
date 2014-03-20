
cdef class ThresholdStrategy:
    """
    Abstract base class defining the behavior that a ThresholdType should implement. These methods
    will be called by :py:func:`find_events`.
    """

    cdef double compute_starting_threshold(self, double baseline, double variance):
        raise NotImplementedError

    cdef double compute_ending_threshold(self, double baseline, double variance):
        raise NotImplementedError
