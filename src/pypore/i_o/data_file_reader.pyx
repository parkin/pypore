# TODO finish implementing this file
from cpython cimport bool

import numpy as np
cimport numpy as np

import pypore.filetypes.data_file as df

from pypore.i_o.abstract_reader cimport AbstractReader

DTYPE = np.float
ctypedef np.float_t DTYPE_t

cdef class DataFileReader(AbstractReader):
    cdef long next_to_send
    cdef object datafile

    cpdef _prepare_file(self, filename):
        """
        Implementation of :py:func:`pypore.i_o.abstract_reader.AbstractReader._prepare_file`
        for Pypore HDF5 files.
        """
        self.datafile = df.open_file(filename, mode='r')

        self.sample_rate = self.datafile.get_sample_rate()

        self.points_per_channel_total = self.datafile.get_data_length()

        self.next_to_send = 0

    cdef object get_next_blocks_c(self, long n_blocks=1):

        self.next_to_send += self.block_size
        if self.next_to_send > self.points_per_channel_total:
            return [self.datafile.root.data[self.next_to_send - self.block_size:].astype(DTYPE)]
        else:
            return [self.datafile.root.data[self.next_to_send - self.block_size : self.next_to_send].astype(DTYPE)]

    cdef object get_all_data_c(self, bool decimate=False):

        return [self.datafile.root.data[:].astype(DTYPE)]

    cdef void close_c(self):
        self.datafile.close()

