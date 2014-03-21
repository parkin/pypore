
from pypore.strategies.threshold_strategy cimport ThresholdStrategy

cdef class PercentChangeThresholdStrategy(ThresholdStrategy):
    cdef public double percent_change_start
    cdef public double percent_change_end

    def __init__(self, double percent_change_start=30., double percent_change_end=10.):
        self.percent_change_start = percent_change_start
        self.percent_change_end = percent_change_end

    cdef double compute_starting_threshold_c(self, double baseline, double variance):
        return baseline * self.percent_change_start / 100.0

    cdef double compute_ending_threshold_c(self, double baseline, double variance):
        return baseline * self.percent_change_end / 100.0