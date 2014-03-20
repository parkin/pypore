
from pypore.strategies.threshold_strategy cimport ThresholdStrategy

cdef class AbsoluteChangeThresholdStrategy(ThresholdStrategy):
    cdef public double change_start
    cdef public double change_end

    def __init__(self, double change_start=3.e-9, double change_end=5.e-10):
        self.change_start = change_start
        self.change_end = change_end

    cdef double compute_starting_threshold(self, double baseline, double variance):
        # TODO figure out how to handle both positive and negative changes...
        raise NotImplementedError

    cdef double compute_ending_threshold(self, double baseline, double variance):
        raise NotImplementedError