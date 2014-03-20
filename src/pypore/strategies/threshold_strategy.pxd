
cdef class ThresholdStrategy:

    cdef double compute_starting_threshold(self, double baseline, double variance)
    cdef double compute_ending_threshold(self, double baseline, double variance)
