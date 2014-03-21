from abstract_reader cimport AbstractReader

cdef class ChimeraReader(AbstractReader):

    # Note that these need to be public in order for the calling of
    # _prepare_file from AbstractReader to work.

    cdef public object datafile
    cdef public object specs_file

    # parameters from the specsfile
    cdef public long adc_bits
    cdef public double adc_v_ref
    cdef public long bit_mask
    cdef public double decimate_sample_rate
