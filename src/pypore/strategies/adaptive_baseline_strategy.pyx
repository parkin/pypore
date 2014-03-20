
import numpy as np
cimport numpy as np

from libc.math cimport pow
from pypore.strategies.baseline_strategy cimport BaselineStrategy

DTYPE = np.float
ctypedef np.float_t DTYPE_t

cdef class AdaptiveBaselineStrategy(BaselineStrategy):
    cdef public double filter_parameter

    def __init__(self, double baseline=0.0, double variance=0.0, double filter_parameter=0.93):
        super(AdaptiveBaselineStrategy, self).__init__(baseline, variance)
        self.filter_parameter = filter_parameter
        self.variance = variance

    cdef double compute_baseline_c(self, double data_point):
        self.baseline = self.filter_parameter * self.baseline + (1 - self.filter_parameter) * data_point
        return self.baseline

    cdef double compute_variance_c(self, double data_point):
        self.variance = self.filter_parameter * self.variance + (1 - self.filter_parameter) * pow(
            data_point - self.baseline, 2)
        return self.variance

    cdef double get_baseline_c(self):
        return BaselineStrategy.get_baseline_c(self)

    cdef double get_variance_c(self):
        return BaselineStrategy.get_variance_c(self)

    cdef void initialize_c(self, np.ndarray[DTYPE_t] initialization_points):
        self.baseline = np.mean(initialization_points)
        self.variance = np.var(initialization_points)