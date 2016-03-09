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

        cdef long decimated_size = 0
        cdef np.ndarray log_data, read_values
        cdef int i = 0
        if decimate:
            decimated_size = 2 * int(self.points_per_channel_total / self.block_size)
            if self.points_per_channel_total % self.block_size > 0:
                decimated_size += 2
            log_data = np.empty(decimated_size)
            # loop through each block and get its max an min value
            i = 0
            while True:
                if self.next_to_send >= self.points_per_channel_total:
                    break
                up_bound = self.next_to_send + self.block_size
                if up_bound > self.points_per_channel_total:
                    up_bound = self.points_per_channel_total
                read_values = self.datafile.root.data[self.next_to_send:up_bound]
                log_data[i] = np.max(read_values)
                log_data[i + 1] = np.min(read_values)
                i += 2
                self.next_to_send += self.block_size

            return [log_data]
        return [self.datafile.root.data[:].astype(DTYPE)]

    cdef void close_c(self):
        self.datafile.close()
