import os

import numpy as np

from pypore.i_o.abstract_reader import AbstractReader
from pypore.util import slice_combine, get_slice_length

# Data types list, in order specified by the HEKA file header v2.0.
# Using big-endian.
# Code 0=uint8,1=uint16,2=uint32,3=int8,4=int16,5=int32,
# 6=single,7=double,8=string64,9=string512

HEKA_ENCODINGS = [np.dtype('>u1'), np.dtype('>u2'), np.dtype('>u4'),
                  np.dtype('>i1'), np.dtype('>i2'), np.dtype('>i4'),
                  np.dtype('>f4'), np.dtype('>f8'), np.dtype('>S64'),
                  np.dtype('>S512'), np.dtype('<u2')]

HEKA_DATATYPE = dt = np.dtype('>i2')  # int16

# Stupid python 3, dropping xrange....
try:
    xrange
except NameError:
    xrange = range


def _get_param_list_byte_length(param_list):
    """
    Returns the length in bytes of the sum of all the parameters in the list.
    Here, list[i][0] = param, list[i][1] = np.dtype
    """
    size = 0
    for i in param_list:
        size = size + i[1].itemsize
    return size


class HekaReader(AbstractReader):
    _channel_selected = None

    def __array__(self):
        return self.get_data_from_selection(self._slice)

    def _get_total_dimension_length(self):
        if self._channel_selected is None:
            return self.channel_list_number
        return self.points_per_channel_total

    def __getitem__(self, item):
        sample_rate = self.sample_rate

        if isinstance(item, int):
            if self._channel_selected is not None:
                if item == -1:
                    stop = None
                else:
                    stop = item + 1
                return self.get_data_from_selection(slice(item, stop, 1))
            else:
                new_slice = slice(0, 0, 1)
                channel_selected = item
        else:
            channel_selected = self._channel_selected

            if isinstance(item, slice) and item.step is not None and item.step > 1:
                sample_rate /= item.step
            new_slice = slice_combine(self._get_total_dimension_length(), self._slice, item)

        return HekaReader(self.filename, _slice=new_slice, _sample_rate=sample_rate, _channel_selected=channel_selected)

    def get_data_from_selection(self, s):
        """
        Returns the requested data.
        :param starts:
        :param stops:
        :param steps:
        :param shape:
        :return:
        """
        indices = s.indices(self._get_total_dimension_length())

        n_points = get_slice_length(self._get_total_dimension_length(), s)
        # if no points are requested, return an empty array
        if n_points == 0:
            return np.zeros(0, dtype=HEKA_DATATYPE)

        start = indices[0]
        stop = indices[1]
        step = indices[2]
        # if the step size is < 0, we need to figure out what the first point actually is
        if step > 0:
            negative_step = False
        else:
            start = xrange(start, stop, step)[-1]
            negative_step = True
        step_size = abs(step)

        # find the block number that contains the start of the selection
        start_block_number = start // self._chunk_size

        # skip to that block, from the start of the binary data
        self.datafile.seek(self.per_file_header_length + start_block_number * self.total_bytes_per_block)

        # how far into the block is the first data point
        remainder = start % self._chunk_size

        # if we are dealing with a single integer, just return it
        if n_points == 1:
            chunk = self._read_heka_next_block()[0]
            values = chunk[remainder]
        else:
            count = 0
            # only read channel 1 for now
            # TODO fix for multichannel
            values = np.empty(shape=(n_points,))
            while count < n_points:
                # only read channel 1 for now
                # TODO fix for multichannel
                chunk = self._read_heka_next_block()[0]

                chunk = chunk[remainder::step_size]
                chunk_size = chunk.size
                if (n_points - count) < chunk_size:
                    chunk = chunk[:n_points - count]
                    chunk_size = chunk.size
                values[count:count + chunk_size] = chunk[:]
                remainder = (remainder + step_size - self._chunk_size) % step_size
                count += chunk_size

        if negative_step:
            values = values[::-1]

        return values

    def __iter__(self):
        """
        Makes the HekaReader iterable.
        """
        # TODO this is a slow implementation ~9s to run on lab pc. Make it faster.
        # get the number of elements to return
        indices = self._slice.indices(self._get_total_dimension_length())
        n_elements = get_slice_length(self._get_total_dimension_length(), self._slice)

        # setup the starts/stops/steps
        start = indices[0]
        step = indices[2]

        for i in xrange(n_elements):
            # get the chunk of data
            chunk = self.get_data_from_selection(slice(start + i * step, start + i * step + 1, step))
            yield chunk

    def __init__(self, filename, *args, **kwargs):
        """
        Implementation of :py:func:`prepare_data_file` for Heka ".hkd" files.
        """
        self.filename = filename
        self.datafile = open(filename, 'rb')

        try:
            # Check that the first line is as expected
            line = self.datafile.readline().decode()
            if not 'Nanopore Experiment Data File V2.0' in line:
                self.datafile.close()
                raise IOError('Heka data file format not recognized.')

            # Just skip over the file header text, should be always the same.
            while True:
                line = self.datafile.readline().decode()
                if 'End of file format' in line:
                    break
        except UnicodeDecodeError:
            # If we can't decode the first line, then it's definitely not a heka file.
            self.datafile.close()
            raise IOError('Data file not recognized as a Heka file.')

        # So now datafile should be at the binary data.

        # # Read binary header parameter lists
        self.per_file_param_list = self._read_heka_header_param_list(np.dtype('>S64'))
        self.per_block_param_list = self._read_heka_header_param_list(np.dtype('>S64'))
        self.per_channel_param_list = self._read_heka_header_param_list(np.dtype('>S64'))
        self.channel_list = self._read_heka_header_param_list(np.dtype('>S512'))

        # # Read per_file parameters
        self.per_file_params = self._read_heka_header_params(self.per_file_param_list)

        # # Calculate sizes of blocks, channels, etc
        self.per_file_header_length = self.datafile.tell()

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
        remainder = (self.file_size - self.per_file_header_length) % self.total_bytes_per_block
        if not remainder == 0:
            self.datafile.close()
            raise IOError('Heka file ends with incomplete block')
        self._chunk_size = self.per_file_params['Points per block']
        self.points_per_channel_total = self._chunk_size * self.num_blocks_in_file

        if not '_sample_rate' in kwargs:
            self.sample_rate = 1.0 / self.per_file_params['Sampling interval']
        else:
            self.sample_rate = kwargs['_sample_rate']

        if not '_slice' in kwargs:
            self._slice = slice(0, None, 1)
        else:
            self._slice = kwargs['_slice']

        if not '_channel_selected' in kwargs:
            if self.channel_list_number > 1:
                self._channel_selected = None
            else:
                self._channel_selected = 0
        else:
            self._channel_selected = kwargs['_channel_selected']

        # Create a memmap of the remaining data
        # self.datafile.seek(self.per_file_header_length + start_block_number * self.total_bytes_per_block)

    def _read_heka_next_block(self):
        """
        Reads the next block of heka data.
        Returns a dictionary with 'data', 'per_block_params', and 'per_channel_params'.
        """
        # Read block header
        per_block_params = self._read_heka_header_params(self.per_block_param_list)
        if per_block_params is None:
            return [np.empty(0)]

        # Read per channel header
        per_channel_block_params = []
        for _ in self.channel_list:  # underscore used for discarded parameters
            channel_params = {}
            # i[0] = name, i[1] = datatype
            for i in self.per_channel_param_list:
                channel_params[i[0]] = np.fromfile(self.datafile, i[1], 1)[0]
            per_channel_block_params.append(channel_params)

        # Read data
        data = []
        for i in xrange(0, len(self.channel_list)):
            values = np.fromfile(self.datafile, dt, count=self._chunk_size) * \
                     per_channel_block_params[i][
                         'Scale']
            # get rid of nan's
            # values[np.isnan(values)] = 0
            data.append(values)

        return data

    def _read_heka_header_param_list(self, datatype):
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
        self.datafile.read(3)  # read null characters?
        dt = np.dtype('>u1')
        num_params = np.fromfile(self.datafile, dt, 1)[0]
        for _ in xrange(0, num_params):
            type_code = np.fromfile(self.datafile, dt, 1)[0]
            # read the name this way, because numpy and python 3 together
            # don't naturally decode strings.
            name = self.datafile.read(datatype.itemsize).decode('utf-8').strip()
            param_list.append([name, HEKA_ENCODINGS[type_code]])
        return param_list

    def _read_heka_header_params(self, param_list):
        params = {}
        # pair[0] = name, pair[1] = np.datatype
        for pair in param_list:
            array = np.fromfile(self.datafile, pair[1], 1)
            if array.size > 0:
                params[pair[0]] = array[0]
            else:
                return None
        return params

    def close(self):
        self.datafile.close()

    @property
    def ndim(self):
        if self._ndim is None:
            self._ndim = len(self.shape)
        return self._ndim

    @property
    def shape(self):
        if self._shape is None:
            # TODO fix for multidimensional
            x = get_slice_length(self._get_total_dimension_length(), self._slice)
            self._shape = (x,)
        return self._shape

    @property
    def size(self):
        if self._size is None:
            self._size = 1
            for i in self.shape:
                self._size *= i
        return self._size

    def max(self):
        if self._max is None:
            # Loop through the data without affecting the position
            self._max = self.__array__().max()
        return self._max

    def mean(self):
        if self._mean is None:
            self._mean = self.__array__().mean()
        return self._mean

    def min(self):
        if self._min is None:
            self._min = self.__array__().min()
        return self._min

    def std(self):
        if self._std is None:
            self._std = self.__array__().std()
        return self._std
