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
        self._prepare_file(filename)

    cpdef _prepare_file(self, filename):
        """
        Opens a data file, reads relevant parameters, and returns then open file and parameters.

        :param StringType filename: Filename to open and read parameters.

        If there was an error opening the files, params will have 'error' key with string description.

        _prepare_file should set the sample_rate and points_per_channel_total.
        """
        raise NotImplementedError

    cpdef close(self):
        """
        Closes the file and the reader.
        """
        raise NotImplementedError

    cpdef get_all_data(self, bool decimate):
        """
        Opens a datafile and returns a dictionary with the data in 'data'.
        If unable to return, will return an error message.

        :param BooleanType decimate: Whether or not to decimate the data. Default is False.
        :returns: DictType -- dictionary with data in the 'data' key. If there is an error, it will return a
            dictionary with 'error' key containing a String error message.
        """
        raise NotImplementedError

    cpdef get_next_blocks(self, long n_blocks):
        """
        Gets the next n blocks (~5000 data points) of data from filename.

        :param IntType n_blocks: Number of blocks to read and return.
        :returns: ListType<np.array> -- List of numpy arrays, one for each channel of the data.
        """
        raise NotImplementedError

    cpdef double get_sample_rate(self):
        return self.sample_rate

    cpdef get_filename(self):
        return self.filename

    cpdef long get_points_per_channel_total(self):
        return self.points_per_channel_total

    cpdef set_block_size(self, long block_size):
        self.block_size = block_size

