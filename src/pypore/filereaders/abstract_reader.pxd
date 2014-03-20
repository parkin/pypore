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
    cpdef get_all_data(self, bool decimate=?)
    cpdef get_next_blocks(self, long n_blocks)
    cpdef set_block_size(self, long block_size)
    cpdef double get_sample_rate(self)
    cpdef long get_points_per_channel_total(self)
    cpdef get_filename(self)
