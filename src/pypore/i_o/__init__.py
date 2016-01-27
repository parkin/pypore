# TODO implement tests for this!
def get_reader_from_filename(filename):
    """
    Returns an instance of an implementation of :py:class:`pypore.i_o.abstract_reader.AbstractReader` based on the
    extension of filename.

    :param string filename: Filename to get the reader for.
    :returns: An open reader of an implementation of :py:class:`pypore.i_o.abstract_reader.AbstractReader` based on the\
             extension of filename, for the following extensions.

        - '.h5' extension: returns an instance of :py:class:`pypore.i_o.data_file_reader.DataFileReader`.
        - '.log' extension: returns :py:class:`pypore.i_o.chimera_reader.ChimeraReader`.

        If the file extension is not in the above list, None is returned.

    :raise: Exception - this method opens a reader, which could throw an exception.

    >>> reader = get_reader_from_filename('test.h5') # Returns an open DataFileReader
    >>> data = reader.get_all_data()
    """

    # TODO implement for other file types

    if filename[-len('.h5'):] == '.h5':
        from data_file_reader import DataFileReader as ReaderClass
    elif filename[-len('.log'):] == '.log':
        from chimera_reader import ChimeraReader as ReaderClass
    elif filename[-len('.hkd'):] == '.hkd':
        from heka_reader import HekaReader as ReaderClass
    elif filename[-len('.hex'):] == '.hex':
        from cnp2_reader import CNP2Reader as ReaderClass
    else:
        raise ValueError(
            "No default match for the extension of {0}. Default extensions include '.h5', '.log', '.hkd', '.hex'.".format(filename))

    reader = ReaderClass(filename)
    return reader

    # elif '.hkd' in filename:
    #     return open_heka_file(filename, decimate)
    # elif '.mat' in filename:
    #     return open_gabys_file(filename, decimate)
    #
    # return {'error': 'File not specified with correct extension. Possibilities are: \'.log\', \'.hkd\''}
