
cdef class ThresholdStrategy:


    cpdef double compute_starting_threshold(self, double baseline, double variance)
    cdef double compute_starting_threshold_c(self, double baseline, double variance)

    cpdef double compute_ending_threshold(self, double baseline, double variance)
    cdef double compute_ending_threshold_c(self, double baseline, double variance)
