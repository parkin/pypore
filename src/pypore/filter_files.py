import glob
import argparse

from multiprocessing import Pool
import numpy as np
from scipy import signal as sig, signal

from pypore.filetypes import data_file
from pypore.i_o import get_reader_from_filename


def filter_file(filename, filter_frequency, out_sample_rate, output_filename=None):
    """
    Reads data from the filename file and uses a Butterworth low-pass filter with cutoff at filter_frequency. Outputs
    the filtered waveform to a new :py:class:`pypore.filetypes.data_file.DataFile`.

    :param StringType filename: Filename containing data to be filtered.
    :param DoubleType filter_frequency: Cutoff frequency for the low-pass Butterworth filter.
    :param DoubleType out_sample_rate: After the data is filtered, it can be resampled to roughly out_sample_rate. If \
            out_sample_rate <= 0, the data will not be resampled.
    :param StringType output_filename: (Optional) Filename for the filtered data. If not specified,
        for an example filename='test.mat', the default output_filename would be 'test_filtered.h5'
    :returns: StringType -- The output filename of the filtered data.

    Usage:

    >>> import pypore.file_converter as fC
    >>> fC.filter_file("filename", 1.e4, 1.e5, "output.h5") // filter at 10kHz, resample at 100kHz
    """
    reader = get_reader_from_filename(filename)

    data = reader.get_all_data()[0]

    sample_rate = reader.get_sample_rate()
    final_sample_rate = sample_rate
    n_points = len(data)

    if output_filename is None:
        output_filename = filename.split('.')[0] + '_filtered.h5'

    # wn is a fraction of the Nyquist frequency (half the sampling frequency).
    wn = filter_frequency / (0.5 * sample_rate)

    b, a = sig.butter(6, wn)

    filtered = sig.filtfilt(b, a, data)[:]

    # resample the data, if requested.
    if 0 < out_sample_rate < sample_rate:
        n_out = int(np.ceil(n_points * out_sample_rate / sample_rate))
        filtered = sig.resample(filtered, num=n_out)
        final_sample_rate = sample_rate * (1.0 * n_out / n_points)

    save_file = data_file.open_file(output_filename, mode='w', sample_rate=final_sample_rate, n_points=filtered.size)
    save_file.root.data[:] = filtered[:]

    save_file.flush()
    save_file.close()
    return output_filename


def filter_wrap(tup):
    # returns the output filename
    print "Starting file:", tup[0]
    output_filename = filter_file(tup[0], tup[1], tup[2])
    print "Done filtering input {0} into output {1}.".format(tup[0], output_filename)
    return output_filename


def main():
    """
    File filtering is included as a script available from the command line when pypore is installed.

    usage: filterfiles [-h] [-d DIRECTORY] [-ff FILTER_FREQ]
                   [-osr OUT_SAMPLE_RATE] [-g GLOB]

    Filters files in a directory based on a file extension.

    optional arguments:
      -h, --help            show this help message and exit
      -d DIRECTORY, --directory DIRECTORY
                            directory of files to filter. Default is the current
                            directory.
      -ff FILTER_FREQ, --filter-freq FILTER_FREQ
                            low-pass filter frequency cutoff. Default is 10000.0
                            Hz
      -osr OUT_SAMPLE_RATE, --out-sample-rate OUT_SAMPLE_RATE
                            output sample rate. Default is 100000.0 Hz
      -g GLOB, --glob GLOB  Unix pattern to search for files in the directory.
                            Default is *.log, which finds all files with a '.log'
                            extension.

    """
    filter_freq = 1.e4
    re_sample_freq = 1.e5
    glob_search = '*.log'

    # parse the command line arguments
    parser = argparse.ArgumentParser(description="Filters files in a directory based on a file extension.")
    parser.add_argument('-d', '--directory', type=str, nargs=1,
                        help="directory of files to filter. Default is the current directory.")
    parser.add_argument('-ff', '--filter-freq', type=float, nargs=1,
                        help="low-pass filter frequency cutoff. Default is {0} Hz".format(filter_freq))
    parser.add_argument('-osr', '--out-sample-rate', type=float, nargs=1,
                        help="output sample rate. Default is {0} Hz".format(re_sample_freq))
    parser.add_argument('-g', '--glob', type=str, nargs=1,
                        help="Unix pattern to search for files in the directory. Default is *.log, which finds all"
                             " files with a '.log' extension.")
    args = parser.parse_args()

    # Use the command line arguments to set our variables, if necessary.
    if args.directory is not None:
        directory = args.directory[0]
        print "Changing to directory:", directory
        import os

        os.chdir(directory)

    if args.filter_freq is not None:
        filter_freq = args.filter_freq[0]

    if args.out_sample_rate is not None:
        re_sample_freq = args.out_sample_rate[0]

    if args.glob is not None:
        glob_search = args.glob

    # find all of the files in the current directory with .log extension.
    files = glob.glob(glob_search)
    print "Filter frequency: {0} Hz".format(filter_freq)
    print "Output sample frequency: {0} Hz".format(re_sample_freq)
    print "Glob search: {0}".format(glob_search)
    print "Filtering these files:", files
    print "\n----------------------------\n"

    p = Pool(len(files))

    # add the file names and filter frequency and output sample rate to a tuple to pass in multiprocessing
    pool_args = []
    for filename in files:
        tup = (filename, filter_freq, re_sample_freq)
        pool_args.append(tup)

    # filter each file
    output_file_names = p.map(filter_wrap, pool_args)

    print "\n----------------------------\n"
    print "Output files:", output_file_names


if __name__ == "__main__":
    main()


