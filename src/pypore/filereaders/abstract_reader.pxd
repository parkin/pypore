from cpython cimport bool

cdef class AbstractReader:
    """
    This is an abstract class showing the methods that subclasses must override.

        -Subclasses should implement opening full data files.
        -Subclasses should implement lazy loading with\
            :py:func:`pypore.filereaders.abstract_converter.get_next_blocks`

    """

    cdef long block_size
    cdef public double sample_rate
    cdef public long points_per_channel_total
    cdef object filename

    cpdef _prepare_file(self, filename)

    cpdef close(self)
    cdef void close_c(self)

    cpdef object get_all_data(self, bool decimate=?)
    cdef object get_all_data_c(self, bool decimate=?)

    cpdef object get_next_blocks(self, long n_blocks=?)
    cdef object get_next_blocks_c(self, long n_blocks=?)

    cpdef double get_sample_rate(self)
    cdef double get_sample_rate_c(self)

    cpdef long get_points_per_channel_total(self)
    cdef long get_points_per_channel_total_c(self)

    cpdef object get_filename(self)
    cdef object get_filename_c(self)
