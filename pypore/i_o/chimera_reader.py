import os

import scipy.io as sio
import numpy as np

from pypore.i_o.abstract_reader import AbstractReader


# ctypedef np.float_t DTYPE_t

CHIMERA_DATA_TYPE = np.dtype('<u2')
# mantissa is 23 bits for np.float32, well above 16 bit from raw
CHIMERA_OUTPUT_DATA_TYPE = np.float32

# Stupid python 3, dropping xrange....
try:
    xrange
except NameError:
    xrange = range


class ChimeraReader(AbstractReader):
    """
    Reader class that reads .log files (with corresponding .mat files) produced by the Chimera acquisition software
    at UPenn.
    """
    specs_file = None

    # parameters from the specsfile
    scale_multiplication = None
    scale_addition = None
    adc_bits = None
    adc_v_ref = None
    current_offset = None
    tia_gain = None
    pre_adc_gain = None
    bit_mask = None

    def __array__(self):
        return self._scale_raw_chimera(np.array(self._data[:]))

    def __getitem__(self, item):
        """
        Examples
        --------

        ::

            array1 = reader[0]          # simple selection
            array2 = reader[4:1400:3]   # slice selection
            array3 = reader[1, :]     # general slice selection, although chimera is only 1 channel, so this will fail

        :param item:
        :return:
        """
        if isinstance(item, int):
            return self._scale_raw_chimera(self._data[item])
        else:
            # reduce sample rate if the slice has steps
            sample_rate = self.sample_rate
            if isinstance(item, slice) and item.step is not None and item.step > 1:
                sample_rate /= item.step

            return ChimeraReader(self._data[item], self.filename, sample_rate, self.bit_mask,
                                 self.scale_multiplication, self.scale_addition)

    def __iter__(self):
        for point in self._data:
            yield self._scale_raw_chimera(point)

    def _scale_raw_chimera(self, values):
        """
        Scales the raw chimera data to correct scaling.

        :param values: numpy array of Chimera values. (raw <u2 datatype)
        :returns: Array of scaled Chimera values (np.float datatype)
        """
        values = values & self.bit_mask
        if hasattr(values, '__iter__'):
            values = values.astype(CHIMERA_OUTPUT_DATA_TYPE, copy=False)
        else:
            values = values.astype(CHIMERA_OUTPUT_DATA_TYPE)
        values *= self.scale_multiplication
        values += self.scale_addition

        return values

    def __init__(self, data, *args):
        """
        Implementation of :py:func:`prepare_data_file` for Chimera ".log" files with the associated ".mat" file.
        """

        if not isinstance(data, str):
            # Then we must copy the data to the new object
            self._data = data
            self.filename = args[0]
            self.sample_rate = args[1]
            self.bit_mask = args[2]
            self.scale_multiplication = args[3]
            self.scale_addition = args[4]
            return

        # remove 'log' append 'mat'
        specs_filename = data[:-len('log')] + 'mat'
        # load the matlab file with parameters for the runs
        try:
            self.specs_file = sio.loadmat(specs_filename)
        except IOError:
            raise IOError(
                "Error opening " + data + ", Chimera .mat specs file of same name must be located in same folder.")

        # Calculate number of points per channel
        file_size = os.path.getsize(data)
        points_per_channel_total = file_size // CHIMERA_DATA_TYPE.itemsize
        shape = (points_per_channel_total,)

        self.adc_bits = self.specs_file['SETUP_ADCBITS'][0][0]
        self.adc_v_ref = self.specs_file['SETUP_ADCVREF'][0][0]
        self.current_offset = self.specs_file['SETUP_pAoffset'][0][0]
        self.tia_gain = self.specs_file['SETUP_TIAgain'][0][0]
        self.pre_adc_gain = self.specs_file['SETUP_preADCgain'][0][0]

        self.bit_mask = np.array((2 ** 16) - 1 - (2 ** (16 - self.adc_bits) - 1), dtype=CHIMERA_DATA_TYPE)

        self.sample_rate = 1.0 * self.specs_file['SETUP_ADCSAMPLERATE'][0][0]

        # calculate the scaling factor from raw data
        self.scale_multiplication = np.array(
            (2 * self.adc_v_ref / 2 ** 16) / (self.pre_adc_gain * self.tia_gain), dtype=CHIMERA_OUTPUT_DATA_TYPE)
        self.scale_addition = np.array(self.current_offset - self.adc_v_ref / (self.pre_adc_gain * self.tia_gain),
                                       dtype=CHIMERA_OUTPUT_DATA_TYPE)

        # Use numpy _data. Note this will fail for files > 4GB on 32 bit systems.
        # If you run into this, a more extreme lazy loading solution will be needed.
        self._data = np.memmap(data, dtype=CHIMERA_DATA_TYPE, mode='r', shape=shape)

    def max(self):
        if self._max is None:
            self._max = np.array(self, copy=False).max()
        return self._max

    def mean(self):
        if self._mean is None:
            self._mean = np.array(self, copy=False).mean()
        return self._mean

    def min(self):
        if self._min is None:
            self._min = np.array(self, copy=False).min()
        return self._min

    def std(self):
        if self._std is None:
            self._std = np.array(self, copy=False).std()
        return self._std

    def close(self):
        del self._data
