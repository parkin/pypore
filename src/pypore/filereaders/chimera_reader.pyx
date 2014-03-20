
import scipy.io as sio
import numpy as np
cimport numpy as np
import os
from cpython cimport bool
import pypore.cythonsetup
cimport pypore.filereaders.abstract_reader
from pypore.filereaders.abstract_reader cimport AbstractReader

DTYPE = np.float
ctypedef np.float_t DTYPE_t

CHIMERA_DATA_TYPE = np.dtype('<u2')

cdef class ChimeraReader(AbstractReader):

    # Note that these need to be public in order for the calling of
    # _prepare_file from AbstractReader to work.

    cpdef get_next_blocks(self, long n_blocks):
        """
        Get the next n blocks of data.

        :param int n_blocks: Number of blocks to grab.
        :returns: List of numpy arrays, one for each channel. Chimera data only has one channel,\
            so this returns [np array].
        """

        cdef np.ndarray raw_values = np.fromfile(self.datafile, CHIMERA_DATA_TYPE, n_blocks * self.block_size)
        raw_values &= self.bit_mask
        cdef np.ndarray[DTYPE_t] log_data = -self.adc_v_ref + (2 * self.adc_v_ref) * raw_values / (2 ** 16)

        return [log_data]

    cpdef _prepare_file(self, filename):
        """
        Implementation of :py:func:`prepare_data_file` for Chimera ".log" files with the associated ".mat" file.
        """
        # remove 'log' append 'mat'
        s = list(filename)
        s.pop()
        s.pop()
        s.pop()
        s.append('mat')
        # load the matlab file with parameters for the runs
        try:
            self.specs_file = sio.loadmat("".join(s))
        except IOError:
            raise IOError("Error opening " + filename + ", Chimera .mat specs file of same name must be located in same folder.")

        self.datafile = open(filename, 'rb')

        # Calculate number of points per channel
        cdef int filesize = os.path.getsize(filename)
        self.points_per_channel_total = filesize / CHIMERA_DATA_TYPE.itemsize

        self.adc_bits = self.specs_file['SETUP_ADCBITS'][0][0]
        self.adc_v_ref = self.specs_file['SETUP_ADCVREF'][0][0]

        self.bit_mask = (2 ** 16) - 1 - (2 ** (16 - self.adc_bits) - 1)

        self.sample_rate = 1.0 * self.specs_file['SETUP_ADCSAMPLERATE'][0][0]
        # Change the decimate sample rate
        self.decimate_sample_rate = self.sample_rate * 2.0 / self.block_size

    cpdef close(self):
        self.datafile.close()

    cpdef get_all_data(self, bool decimate):
        """
        Reads files created by the Chimera acquisition software.  It requires a
        filename.log file with the data, and a filename.mat file containing the
        parameters of the run.

        :returns: a dictionary with the keys / values in the filename.mat file\
            as well as 'data', a numpy array of the current values
        """
        cdef long decimated_size = 0
        cdef long i = 0
        cdef np.ndarray[DTYPE_t] log_data, read_values
        cdef np.ndarray raw_values
        if decimate:
            # use 5000 for plot decimation
            decimated_size = int(2 * self.points_per_channel_total / self.block_size)
            # will there be a block at the end with < block_size datapoints?
            if self.points_per_channel_total % self.block_size> 0:
                decimated_size += 2
            log_data = np.empty(decimated_size)
            i = 0
            while True:
                raw_values = np.fromfile(self.datafile, CHIMERA_DATA_TYPE, self.block_size)
                if raw_values.size < 1:
                    break
                read_values = -self.adc_v_ref + (2 * self.adc_v_ref) * (raw_values & self.bit_mask) / (2 ** 16)
                log_data[i] = np.max(read_values)
                log_data[i + 1] = np.min(read_values)
                i += 2

        else:
            raw_values = np.fromfile(self.datafile, CHIMERA_DATA_TYPE)
            raw_values &= self.bit_mask
            log_data = -self.adc_v_ref + (2 * self.adc_v_ref) * raw_values / (2 ** 16);

        return [log_data]
