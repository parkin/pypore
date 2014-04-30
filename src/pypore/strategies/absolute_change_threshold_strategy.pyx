
from pypore.strategies.threshold_strategy cimport ThresholdStrategy

cdef class AbsoluteChangeThresholdStrategy(ThresholdStrategy):
    cdef public double change_start
    cdef public double change_end

    def __init__(self, double change_start=3.e-9, double change_end=5.e-10):
        self.change_start = change_start
        self.change_end = change_end

    cdef double compute_starting_threshold_c(self, double baseline, double variance):
        """
        :returns: change_start from strategy initialization. 'baseline' and 'variance' parameters have no effect.
        """
        return self.change_start

    cdef double compute_ending_threshold_c(self, double baseline, double variance):
        """
        :returns: change_end from strategy initialization. 'baseline' and 'variance' parameters have no effect.
        """
        return self.change_end
