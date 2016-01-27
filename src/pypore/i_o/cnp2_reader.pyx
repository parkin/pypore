from pypore.i_o.abstract_reader cimport AbstractReader

import numpy as np
cimport numpy as np

import os

import json

SAMPLE_RATE = 40.e6


cdef class CNP2Reader(AbstractReader):

    cpdef _prepare_file(self, filename):
        self.block_size = 6000
        self.ADCBITS = 12

        config_filename = filename[:-4] + '.cfg'

        config_data = None

        with open(config_filename) as config_file:
            config_data = json.load(config_file)

        self.bias_enable = config_data['biasEnable']
        self.amplifier_gain_select = config_data['amplifierGainSelect']
        self.integrator_reset = config_data['integratorReset']
        self.idc_offset = config_data['IDCOffset']
        self.connect_isrcext = config_data['connectISRCEXT']
        self.column_select = config_data['columnSelect']
        self.rdcfb = config_data['RDCFB']
        self.row_select = config_data['rowSelect']
        self.connect_electrode = config_data['connectElectrode']

        self.AAFILTERGAIN = (51+620)/620.0*1.8*.51

        self.datafile = open(filename, 'rb')

        self.sample_rate = SAMPLE_RATE

        cdef int filesize = os.path.getsize(filename)

        if self.column_select in [0, 1]:
            self.raw_dtype = np.dtype('uint32')
            self.points_per_chunk = 1
            self.points_per_channel_total = filesize / 4 # 4 byte chunks
        elif self.column_select in [2, 3, 4]:
            self.raw_dtype = np.dtype('uint64')
            self.points_per_chunk = 3
            self.points_per_channel_total = filesize / 16 # 16 byte chunks


    cdef void close_c(self):
        self.datafile.close()

    cdef np.ndarray _unpack_raw(self, np.ndarray raw):
        cdef np.ndarray ADCData
        # Implement the Master FPGAType
        if self.column_select == 0:
            ADCData = np.bitwise_and(raw, 0xfff)
        elif self.column_select == 1:
            ADCData = np.bitwise_and(raw, 0xfff000) >> 12

        # TODO implement Slave FPGAType

        return ADCData


    cdef np.ndarray _get_next_n_values(self, long n):
        """
        Returns the next n values in the file.
        """
        cdef np.ndarray raw_values = np.fromfile(self.datafile, self.raw_dtype, n)

        cdef np.ndarray adc_data = self._unpack_raw(raw_values)

        cdef np.ndarray fnal = 1.0*adc_data

        # Scale the data correctly
        fnal[fnal >= 2**(self.ADCBITS-1)] -= 2**(self.ADCBITS)
        fnal /= (2**(self.ADCBITS - 1) * self.rdcfb * self.AAFILTERGAIN)
        fnal -= self.idc_offset

        # scale to nA
        fnal *= 1.e9

        return fnal

    cdef object get_next_blocks_c(self, long n_blocks=1):
        """
        Get the next n blocks of data.

        :param int n_blocks: Number of blocks to grab.
        :returns: List of numpy arrays, one for each channel. Chimera data only has one channel,\
            so this returns [np array].
        """
        cdef np.ndarray adc_data = self._get_next_n_values(n_blocks * self.block_size)

        return [adc_data]

    cdef object get_all_data_c(self, bool decimate=False):

        # Go to the beginning of the file
        self.datafile.seek(0)

        cdef np.ndarray adc_data
        cdef np.ndarray values

        cdef long decimated_size

        cdef i

        if decimate:
            # use 5000 for plot decimation
            decimated_size = 2 * int(self.points_per_channel_total / self.block_size)
            # will there be a block at the end with < block_size datapoints?
            if self.points_per_channel_total % self.block_size > 0:
                decimated_size += 2
            adc_data = np.zeros(decimated_size)
            i = 0
            while True:
                values = self._get_next_n_values(self.block_size)
                if values.size < 1:
                    break
                adc_data[i] = np.max(values)
                adc_data[i + 1] = np.min(values)
                i += 2
        else:
            adc_data = self._get_next_n_values(self.points_per_channel_total)

        return [adc_data]
