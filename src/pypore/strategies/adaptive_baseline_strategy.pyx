import numpy as np

cimport numpy as np

from libc.math cimport pow
from pypore.strategies.baseline_strategy cimport BaselineStrategy

DTYPE = np.float
ctypedef np.float_t DTYPE_t

cdef class AdaptiveBaselineStrategy(BaselineStrategy):
    cdef public double baseline_filter_parameter
    cdef public double variance_filter_parameter
    # Keep track of baseline separately for the variance calculation.
    cdef public double variance_baseline

    def __init__(self, double baseline=0.0, double variance=0.0, double baseline_filter_parameter=0.93,
                 double variance_filter_parameter=0.99):
        super(AdaptiveBaselineStrategy, self).__init__(baseline, variance)
        self.variance_baseline = baseline
        self.variance = variance
        self.baseline_filter_parameter = baseline_filter_parameter
        self.variance_filter_parameter = variance_filter_parameter

    cdef double compute_baseline_c(self, double data_point):
        self.baseline = self.baseline_filter_parameter * self.baseline + (
        1 - self.baseline_filter_parameter) * data_point
        return self.baseline

    cdef double compute_variance_c(self, double data_point):
        self.variance_baseline = self.variance_filter_parameter * self.variance_baseline + (
            1 - self.variance_filter_parameter) * data_point
        self.variance = self.variance_filter_parameter * self.variance + (1 - self.variance_filter_parameter) * pow(
            data_point - self.variance_baseline, 2)
        return self.variance

    cdef double get_baseline_c(self):
        return BaselineStrategy.get_baseline_c(self)

    cdef double get_variance_c(self):
        return BaselineStrategy.get_variance_c(self)

    cdef void initialize_c(self, np.ndarray[DTYPE_t] initialization_points):
        self.baseline = np.mean(initialization_points)
        self.variance = np.var(initialization_points)
        self.variance_baseline = self.baseline