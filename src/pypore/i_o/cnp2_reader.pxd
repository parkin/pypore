from abstract_reader cimport AbstractReader
from cpython cimport bool
import numpy as np
cimport numpy as np

cdef class CNP2Reader(AbstractReader):

    # Note that these need to be public in order for the calling of
    # _prepare_file from AbstractReader to work.

    cdef public object datafile
    cdef public object config_file

    # parameters from the config file
    cdef public bool bias_enable
    cdef public int amplifier_gain_select
    cdef public bool integrator_reset
    cdef public double idc_offset
    cdef public bool connect_isrcext
    cdef public int column_select
    cdef public double rdcfb
    cdef public int row_select
    cdef public bool connect_electrode
    cdef public int ADCBITS

    # Other
    cdef public object raw_dtype
    cdef public int points_per_chunk

    # Helper functions
    cdef np.ndarray _unpack_raw(self, np.ndarray raw)
    cdef np.ndarray _get_next_n_values(self, long n)
