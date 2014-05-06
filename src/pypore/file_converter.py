"""
Created on Jan 28, 2014

@author: `@parkin`_
"""
import os
import datetime

from filetypes import data_file
from pypore.i_o import get_reader_from_filename
import pypore.filetypes.data_file as df
from pypore.i_o.abstract_reader import AbstractReader


def convert_file(filename, output_filename=None):
    """
    Convert a file to the pypore .h5 file format. Returns the new file's name.
    """
    reader = get_reader_from_filename(filename)

    sample_rate = reader.get_sample_rate()
    n_points = reader.get_points_per_channel_total()

    if output_filename is None:
        output_filename = filename.split('.')[0] + '.h5'

    save_file = data_file.open_file(output_filename, mode='w', sample_rate=sample_rate, n_points=n_points)
    blocks_to_get = 1
    data = reader.get_next_blocks(blocks_to_get)[0]

    n = data.size
    i = 0
    while n > 0:
        save_file.root.data[i:n + i] = data[:]
        i += n
        data = reader.get_next_blocks(blocks_to_get)[0]
        n = data.size

    reader.close()

    save_file.flush()
    save_file.close()
    return output_filename


class SamplingRatesMismatchError(Exception):
    pass


def concat_files(files, output_filename=None):
    """
    This function concatenates multiple files into one data file. All of the sampling rates of the original files
    must be the same.

    :param list files: List of string file names OR
        :py:class:`Readers <pypore.i_o.abstract_reader.AbstractReader>`.
    :param output_filename: Optional file name for the resulting file.
    :raises: :py:exc:`ValueError` -- if the length of the files list is < 2.
    :raises: :py:exc:`SamplingRatesMismatchError <pypore.file_converter.SamplingRatesMismatchError>` -- if the sampling
        rates do not match in all of the files.

    >>> from pypore.i_o.data_file_reader import DataFileReader
    >>> concat_files(['file1.log', DataFileReader('dataFile.h5')], output_filename='concatenated.h5') # can pass strings or Readers
    """
    if len(files) < 2:
        raise ValueError("Minimum length of files list is 2.")

    # Get the first sample rate
    should_close_reader = False
    reader = files[0]
    if not isinstance(reader, AbstractReader):
        reader = get_reader_from_filename(reader)
        should_close_reader = True

    sample_rate = reader.get_sample_rate()

    if output_filename is None:
        basename = os.path.basename(reader.get_filename())
        output_filename = basename.split('.')[0] + '_concatenated_' + datetime.datetime.now().strftime(
            "%Y%m%d_%H%M%S") + '.h5'

    if should_close_reader:
        reader.close()

    n = 0

    # Get the total number of data points, and check that the sampling rates are equal.
    for i, reader in enumerate(files):
        should_close_reader = False

        # If it's not already a reader
        if not isinstance(reader, AbstractReader):
            reader = get_reader_from_filename(reader)
            should_close_reader = True

        curr_sample_rate = reader.get_sample_rate()

        if curr_sample_rate != sample_rate:
            raise SamplingRatesMismatchError(
                "Sampling rates differ in files. Found {0} and {1}.".format(curr_sample_rate, sample_rate))

        n += reader.get_all_data()[0].size

        if should_close_reader:
            reader.close()

    # Open a new data file.
    new_data_file = df.open_file(output_filename, mode='w', n_points=n, sample_rate=sample_rate)

    curr_i = 0

    for i, reader in enumerate(files):
        should_close_reader = False

        # If it's not already a reader
        if not isinstance(reader, AbstractReader):
            reader = get_reader_from_filename(reader)
            should_close_reader = True

        n_i = reader.get_points_per_channel_total()

        new_data_file.root.data[curr_i:curr_i + n_i] = reader.get_all_data()[0]

        curr_i += n_i

        if should_close_reader:
            reader.close()

    new_data_file.close()

    return output_filename

