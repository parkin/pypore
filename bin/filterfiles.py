#!/usr/bin/env python
import argparse
import fnmatch
from multiprocessing import Pool
import os
from pypore.filter_files import filter_file


def _filter_wrap(tup):
    # returns the output filename
    print "Starting file:", tup[0]
    output_filename = filter_file(tup[0], tup[1], tup[2])
    print "Done filtering input {0} into output {1}.".format(tup[0], output_filename)
    return output_filename


def main():
    """
    File filtering is included as a script available from the command line when pypore is installed.

    usage:

    .. code-block:: bash

        filterfiles [-h] [-d DIRECTORY] [-ff FILTER_FREQ]
                    [-osr OUT_SAMPLE_RATE] [-g GLOB] [-r]

    Filters files in a directory based on a file extension.

    optional arguments:

    * -h, --help            show this help message and exit
    * -d DIRECTORY, --directory DIRECTORY
        directory of files to filter. Default is the current directory.
    * -ff FILTER_FREQ, --filter-freq FILTER_FREQ
        low-pass filter frequency cutoff. Default is 10000.0 Hz
    * -osr OUT_SAMPLE_RATE, --out-sample-rate OUT_SAMPLE_RATE
        output sample rate. Default is 100000.0 Hz
    * -g GLOB, --glob GLOB  Unix pattern to search for files in the directory.
        Default is '\*.log', which finds all files with a '.log' extension.
    * -r, --recursive       search for files recursively.

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
                        help="Unix pattern to search for files in the directory. Default is \'*.log\', which finds all"
                             " files with a '.log' extension. Must surround with quotes.")
    parser.add_argument('-r', '--recursive', action='store_true',
                        help="search for files recursively.")
    args = parser.parse_args()

    directory = '.'
    # Use the command line arguments to set our variables, if necessary.
    if args.directory is not None:
        directory = args.directory[0]

    if args.filter_freq is not None:
        filter_freq = args.filter_freq[0]

    if args.out_sample_rate is not None:
        re_sample_freq = args.out_sample_rate[0]

    if args.glob is not None:
        glob_search = args.glob[0]
    print glob_search

    # find all of the files in the current directory with .log extension.
    files = []
    for root, dirname, filenames in os.walk(directory):
        for filename in fnmatch.filter(filenames, glob_search):
            files.append(os.path.join(root, filename))
        # Only do top level directory, unless recursive is specified.
        if not args.recursive:
            break

    print "Filter frequency: {0} Hz".format(filter_freq)
    print "Output sample frequency: {0} Hz".format(re_sample_freq)
    print "Glob search: {0}".format(glob_search)
    print "Recursive: {0}".format(args.recursive)
    print "Filtering these files:", files
    print "\n----------------------------\n"

    p = Pool()

    # add the file names and filter frequency and output sample rate to a tuple to pass in multiprocessing
    pool_args = []
    for filename in files:
        tup = (filename, filter_freq, re_sample_freq)
        pool_args.append(tup)

    # filter each file
    output_file_names = p.map(_filter_wrap, pool_args)

    print "\n----------------------------\n"
    print "Output files:", output_file_names

if __name__ == '__main__':
    main()
