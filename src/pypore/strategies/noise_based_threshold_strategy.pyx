from libc.math cimport sqrt
from pypore.strategies.threshold_strategy cimport ThresholdStrategy

cdef class NoiseBasedThresholdStrategy(ThresholdStrategy):
    cdef public double start_std_dev
    cdef public double end_std_dev

    def __init__(self, double start_std_dev=5.0, double end_std_dev=1.0):
        super(NoiseBasedThresholdStrategy, self).__init__()
        self.start_std_dev = start_std_dev
        self.end_std_dev = end_std_dev

    cdef double compute_ending_threshold_c(self, double baseline, double variance):
        return self.end_std_dev * sqrt(variance)

    cdef double compute_starting_threshold_c(self, double baseline, double variance):
        return self.start_std_dev * sqrt(variance)