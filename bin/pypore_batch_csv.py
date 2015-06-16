#!/usr/bin/env python
import argparse
import fnmatch
from multiprocessing import Pool
import os
from pypore.filetypes.event_database import open_file

def _filter_wrap(tup):
    # returns the output filename
    filename = tup[0]
    print "Starting file:", filename
    ed = open_file(filename, mode='r')
    output_filename = filename[:-3] + '.csv'
    ed.to_csv(output_filename)
    print "Done converting input {0} into output {1}.".format(tup[0], output_filename)
    return output_filename


def main():
    """

    * -h, --help            show this help message and exit
    * -d DIRECTORY, --directory DIRECTORY
        directory of files to filter. Default is the current directory.
    * -r, --recursive       search for files recursively.

    """
    filter_freq = 1.e4
    re_sample_freq = 1.e5
    glob_search = '*Events*.h5'

    # parse the command line arguments
    parser = argparse.ArgumentParser(description="Filters files in a directory based on a file extension.")
    parser.add_argument('-d', '--directory', type=str, nargs=1,
                        help="directory of files to filter. Default is the current directory.")
    parser.add_argument('-r', '--recursive', action='store_true',
                        help="search for files recursively.")
    args = parser.parse_args()

    directory = '.'
    # Use the command line arguments to set our variables, if necessary.
    if args.directory is not None:
        directory = args.directory[0]

    # find all of the files in the current directory with .h5 extension.
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
        tup = (filename,)
        pool_args.append(tup)

    # filter each file
    output_file_names = p.map(_filter_wrap, pool_args)

    print "\n----------------------------\n"
    print "Output files:", output_file_names

if __name__ == '__main__':
    main()
