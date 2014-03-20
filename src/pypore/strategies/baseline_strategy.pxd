
import numpy as np
cimport numpy as np

DTYPE = np.float
ctypedef np.float_t DTYPE_t

cdef class BaselineStrategy:

    cdef public double baseline
    cdef public double variance

    cpdef double compute_baseline(self, double data_point)
    cdef double compute_baseline_c(self, double data_point)

    cpdef double compute_variance(self, double data_point)
    cdef double compute_variance_c(self, double data_point)

    cpdef initialize(self, np.ndarray[DTYPE_t] initialization_points)
    cdef void initialize_c(self, np.ndarray[DTYPE_t] initialization_points)

    cpdef double get_baseline(self)
    cdef double get_baseline_c(self)

    cpdef double get_variance(self)
    cdef double get_variance_c(self)
