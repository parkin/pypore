# TODO finish implementing this file
from cpython cimport bool

import numpy as np
cimport numpy as np

import pypore.filetypes.data_file as df

from pypore.io.abstract_reader cimport AbstractReader

DTYPE = np.float

cdef class DataFileReader(AbstractReader):
    cdef long next_to_send
    cdef object datafile

    cpdef _prepare_file(self, filename):
        """
        Implementation of :py:func:`pypore.io.abstract_reader.AbstractReader._prepare_file`
        for Pypore HDF5 files.
        """
        self.datafile = df.open_file(filename, mode='r')

        self.sample_rate = self.datafile.get_sample_rate()

        self.points_per_channel_total = self.datafile.get_data_length()

        self.next_to_send = 0

    cdef object get_next_blocks_c(self, long n_blocks=1):
        data = self.datafile.root.data

        if self.next_to_send >= self.points_per_channel_total:
            return [data[self.next_to_send:].astype(DTYPE)]
        else:
            self.next_to_send += self.block_size
            return [data[self.next_to_send:self.next_to_send + self.block_size].astype(DTYPE)]

    cpdef get_all_data(self, bool decimate=False):
        self.next_to_send = 0

        arr = self.datafile.root.data

        cdef np.ndarray data

        # cdef float sample_rate = p['sample_rate']

        # if decimate:
        #     data = arr[::5000]
        #     sample_rate /= 5000.
        # else:
        #     data = arr[:]
        #
        # specs_file = {'data': [data], 'sample_rate': sample_rate}
        # return specs_file
