from cpython cimport bool

cdef class AbstractReader:
    """
    This is an abstract class showing the methods that subclasses must override.

        -Subclasses should implement opening full data files.
        -Subclasses should implement lazy loading with\
            :py:func:`pypore.filereaders.abstract_reader.get_next_blocks`

    """

    def __init__(self, filename):
        """
        Opens a data file, reads relevant parameters, and returns then open file and parameters.

        :param StringType filename: Filename to open and read parameters.

        If there was an error opening the files, params will have 'error' key with string description.
        """
        self.block_size = 5000
        self.filename = filename
        self._prepare_file_c(filename)

    cpdef _prepare_file(self, filename):
        """_prepare_file(filename)

        (Note this is a cpdef wrapper around the cdef method :py:func:`_prepare_file_c`. This cpdef version
        is **never** called. If overriding, make sure to override the :py:func:`_prepare_file_c` version.)

        Opens a data file, reads relevant parameters, and returns then open file and parameters.

        :param StringType filename: Filename to open and read parameters.

        If there was an error opening the files, params will have 'error' key with string description.

        _prepare_file should set the sample_rate and points_per_channel_total.
        """
        self._prepare_file_c(filename)

    cdef void _prepare_file_c(self, filename):
        raise NotImplementedError

    cpdef close(self):
        """close()

        (Note this is a cpdef wrapper around the cdef method :py:func:`close_c`.
        If using Cython, you can directly call the cdef version.)

        Closes the file and the reader.
        """
        self.close_c()

    cdef void close_c(self):
        """
        See docs for :py:func:`close`.
        """
        raise NotImplementedError

    cpdef object get_all_data(self, bool decimate=False):
        """get_all_data(bool decimate=False)

        (Note this is a cpdef wrapper around the cdef method :py:func:`get_all_data_c`.
        If using Cython, you can call the cdef version directly.)

        Reads and returns all of the data in the file.

        :param BooleanType decimate: Whether or not to decimate the data. Default is False.
        :returns: List of numpy arrays, one for each channel of the data.
        """
        return self.get_all_data_c(decimate)

    cdef object get_all_data_c(self, bool decimate=False):
        """
        See docs for :py:func:`get_all_data`.
        """
        raise NotImplementedError

    cpdef object get_next_blocks(self, long n_blocks=1):
        """get_next_blocks(long n_blocks=1)

        (Note this is a cpdef wrapper around the cdef method :py:func:`get_next_blocks_c`.
        If using Cython, you can call the cdef version directly.)

        Gets the next n_blocks (~5000 data points per block) of data from filename.

        :param IntType n_blocks: Number of blocks to read and return.
        :returns: ListType<np.array> -- List of numpy arrays, one for each channel of the data.
        """
        return self.get_next_blocks_c(n_blocks)

    cdef object get_next_blocks_c(self, long n_blocks=1):
        raise NotImplementedError

    cpdef double get_sample_rate(self):
        """get_sample_rate()

        (Note this is a cpdef wrapper around the cdef method :py:func:`get_next_blocks_c`.
        If using Cython, you can call the cdef version directly.)

        :returns: sample rate of the file.
        """
        return self.get_sample_rate_c()

    cdef double get_sample_rate_c(self):
        return self.sample_rate

    cpdef object get_filename(self):
        """get_filename()

        (Note this is a cpdef wrapper around the cdef method :py:func:`get_next_blocks_c`.
        If using Cython, you can call the cdef version directly.)
        :returns: the filename being read.
        """
        return self.get_filename_c()

    cdef object get_filename_c(self):
        return self.filename

    cpdef long get_points_per_channel_total(self):
        """get_points_per_channel_total()

        (Note this is a cpdef wrapper around the cdef method :py:func:`get_next_blocks_c`.
        If using Cython, you can call the cdef version directly.)

        :returns: the total number of points in each channel of data.
        """
        return self.get_points_per_channel_total_c()

    cdef long get_points_per_channel_total_c(self):
        return self.points_per_channel_total

