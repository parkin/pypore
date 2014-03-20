import numpy as np
cimport numpy as np

from pypore.strategies.baseline_strategy cimport BaselineStrategy

DTYPE = np.float
ctypedef np.float_t DTYPE_t

cdef class FixedBaselineStrategy(BaselineStrategy):
    cdef double compute_baseline_c(self, double data_point):
        # fixed baseline
        return self.baseline

    cdef double compute_variance_c(self, double data_point):
        # fixed variance
        return self.variance

    cdef void initialize_c(self, np.ndarray[DTYPE_t] initialization_points):
        pass

    cdef double get_baseline_c(self):
        return BaselineStrategy.get_baseline_c(self)

    cdef double get_variance_c(self):
        return BaselineStrategy.get_variance_c(self)