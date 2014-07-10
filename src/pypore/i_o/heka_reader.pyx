import scipy.io as sio
import numpy as np

cimport numpy as np
import os

from cpython cimport bool
from pypore.i_o.abstract_reader cimport AbstractReader

ctypedef np.float_t DTYPE_t

# Data types list, in order specified by the HEKA file header v2.0.
# Using big-endian.
# Code 0=uint8,1=uint16,2=uint32,3=int8,4=int16,5=int32,
#    6=single,7=double,8=string64,9=string512
ENCODINGS = [np.dtype('>u1'), np.dtype('>u2'), np.dtype('>u4'),
             np.dtype('>i1'), np.dtype('>i2'), np.dtype('>i4'),
             np.dtype('>f4'), np.dtype('>f8'), np.dtype('>S64'),
             np.dtype('>S512'), np.dtype('<u2')]

cdef long _get_param_list_byte_length(param_list):
    """
    Returns the length in bytes of the sum of all the parameters in the list.
    Here, list[i][0] = param, list[i][1] = np.dtype
    """
    cdef long size = 0
    for i in param_list:
        size = size + i[1].itemsize
    return size

cdef class HekaReader(AbstractReader):
    # Note that these need to be public in order for the calling of
    # _prepare_file from AbstractReader to work.

    cdef object heka_file
    cdef object per_file_param_list
    cdef object per_block_param_list
    cdef object per_channel_param_list
    cdef object channel_list
    cdef object per_file_params

    cdef int per_file_header_length

    cdef long per_channel_per_block_length
    cdef long per_block_length

    cdef int channel_list_number

    cdef long header_bytes_per_block
    cdef long data_bytes_per_block
    cdef long total_bytes_per_block

    # Calculate number of points per channel
    cdef long file_size
    cdef long num_blocks_in_file
    cdef long remainder

    cpdef _prepare_file(self, filename):
        """
        Implementation of :py:func:`prepare_data_file` for Heka ".hkd" files.
        """
        self.heka_file = open(filename, 'rb')
        # Check that the first line is as expected
        line = self.heka_file.readline()
        if not 'Nanopore Experiment Data File V2.0' in line:
            self.heka_file.close()
            raise IOError('Heka data file format not recognized.')
        # Just skip over the file header text, should be always the same.
        while True:
            line = self.heka_file.readline()
            if 'End of file format' in line:
                break

        # So now heka_file should be at the binary data.

        # # Read binary header parameter lists
        self.per_file_param_list = self._read_heka_header_param_list(np.dtype('>S64'))
        self.per_block_param_list = self._read_heka_header_param_list(np.dtype('>S64'))
        self.per_channel_param_list = self._read_heka_header_param_list(np.dtype('>S64'))
        self.channel_list = self._read_heka_header_param_list(np.dtype('>S512'))

        # # Read per_file parameters
        self.per_file_params = self._read_heka_header_params(self.per_file_param_list)

        # # Calculate sizes of blocks, channels, etc
        self.per_file_header_length = self.heka_file.tell()

        # Calculate the block lengths
        self.per_channel_per_block_length = _get_param_list_byte_length(self.per_channel_param_list)
        self.per_block_length = _get_param_list_byte_length(self.per_block_param_list)

        self.channel_list_number = len(self.channel_list)

        self.header_bytes_per_block = self.per_channel_per_block_length * self.channel_list_number
        self.data_bytes_per_block = self.per_file_params['Points per block'] * 2 * self.channel_list_number
        self.total_bytes_per_block = self.header_bytes_per_block + self.data_bytes_per_block + self.per_block_length

        # Calculate number of points per channel
        self.file_size = os.path.getsize(filename)
        self.num_blocks_in_file = int((self.file_size - self.per_file_header_length) / self.total_bytes_per_block)
        cdef long remainder = (self.file_size - self.per_file_header_length) % self.total_bytes_per_block
        if not remainder == 0:
            self.heka_file.close()
            raise IOError('Heka file ends with incomplete block')
        self.block_size = self.per_file_params['Points per block']
        self.points_per_channel_total = self.block_size * self.num_blocks_in_file

        self.sample_rate = 1.0 / self.per_file_params['Sampling interval']

    cdef void close_c(self):
        self.heka_file.close()

    cdef get_all_data_c(self, bool decimate=False):
        """
        Reads files created by the Heka acquisition software and returns the data.

        :returns: List of numpy arrays, one for each channel of data.
        """
        # return to the start of the file
        self.heka_file.seek(self.per_file_header_length)

        data = []
        for _ in self.channel_list:
            if decimate:  # If decimating, just keep max and min value from each block
                data.append(np.empty(self.num_blocks_in_file * 2))
            else:
                data.append(np.empty(self.points_per_channel_total))  # initialize_c array

        for i in xrange(0, self.num_blocks_in_file):
            block = self._read_heka_next_block()
            for j in xrange(len(block)):
                if decimate:  # if decimating data, only keep max and min of each block
                    data[j][2 * i] = np.max(block[j])
                    data[j][2 * i + 1] = np.min(block[j])
                else:
                    data[j][i * self.block_size:(i + 1) * self.block_size] = block[
                        j]

        # if decimate:
        #     self.decimate_sample_rate = self.sample_rate * 2 / self.points_per_channel_per_block  # we are downsampling

        return data

    cdef object get_next_blocks_c(self, long n_blocks=1):
        """
        Get the next n blocks of data.

        :param int n_blocks: Number of blocks to grab.
        :returns: List of numpy arrays, one for each channel.
        """
        blocks = []
        cdef long totalsize = 0
        cdef long size = 0
        cdef bool done = False
        for i in xrange(0, n_blocks):
            block = self._read_heka_next_block()
            if block[0].size == 0:
                return block
            blocks.append(block)
            size = block[0].size
            totalsize = totalsize + size
            if size < self.block_size:  # did we reach the end?
                break

        # stitch the data together
        data = []
        index = []
        for _ in xrange(0, len(self.channel_list)):
            data.append(np.empty(totalsize))
            index.append(0)
        for block in blocks:
            for i in xrange(0, len(self.channel_list)):
                data[i][index[i]:index[i] + block[i].size] = block[i]
                index[i] = index[i] + block[i].size

        return data

    cdef _read_heka_next_block(self):
        """
        Reads the next block of heka data.
        Returns a dictionary with 'data', 'per_block_params', and 'per_channel_params'.
        """  # Read block header
        per_block_params = self._read_heka_header_params(self.per_block_param_list)
        if per_block_params is None:
            return [np.empty(0)]

        # Read per channel header
        per_channel_block_params = []
        for _ in self.channel_list:  # underscore used for discarded parameters
            channel_params = {}
            # i[0] = name, i[1] = datatype
            for i in self.per_channel_param_list:
                channel_params[i[0]] = np.fromfile(self.heka_file, i[1], 1)[0]
            per_channel_block_params.append(channel_params)

        # Read data
        data = []
        dt = np.dtype('>i2')  # int16
        cdef np.ndarray values
        for i in xrange(0, len(self.channel_list)):
            values = np.fromfile(self.heka_file, dt, count=self.block_size) * \
                     per_channel_block_params[i][
                         'Scale']
            # get rid of nan's
            #         values[np.isnan(values)] = 0
            data.append(values)

        return data

    cdef _read_heka_header_params(self, param_list):
        params = {}
        # pair[0] = name, pair[1] = np.datatype
        cdef np.ndarray array
        for pair in param_list:
            array = np.fromfile(self.heka_file, pair[1], 1)
            if array.size > 0:
                params[pair[0]] = array[0]
            else:
                return None
        return params

    cdef _read_heka_header_param_list(self, datatype):
        """
        Reads the binary parameter list of the following format:
            3 null bytes
            1 byte uint8 - how many params following
            params - 1 byte uint8 - code for datatype (eg encoding[code])
                     datatype.intemsize bytes - name the parameter
        Returns a list of parameters, with
            item[0] = name
            item[1] = numpy datatype
        """
        param_list = []
        self.heka_file.read(3)  # read null characters?
        dt = np.dtype('>u1')
        cdef int num_params = np.fromfile(self.heka_file, dt, 1)[0]
        for _ in xrange(0, num_params):
            type_code = np.fromfile(self.heka_file, dt, 1)[0]
            name = np.fromfile(self.heka_file, datatype, 1)[0].strip()
            param_list.append([name, ENCODINGS[type_code]])
        return param_list
