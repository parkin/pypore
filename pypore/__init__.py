def open_file(filename, reader_class=None):
    """
    Opens a read only, raw current data file of one of the following formats:

        #. Chimera files. See implementations in :py:mod:`pypore.i_o.chimera_reader`
        #. Heka files. See implementations in :py:mod:`pypore.i_o.heka_reader`

    To implement your own reader, extend :py:class:`pypore.i_o.abstract_reader.AbstractReader`.

    To test your own reader, override unittest and :py:class:`pypore.i_o.tests.reader_tests.ReaderTests`. See
    :py:mod:`pypore.i_o.tests.test_chimera_reader` as an example.

    :param filename: Filename to open.
    :param reader_class: (Optional) A reader class to be used to read the filename. If None, a reader class will be
    chosen based on the file extension.
    :return: An open reader.
    """
    # make sure the filename is a string
    filename = str(filename)

    if reader_class is not None:
        return reader_class(filename)

    if filename[-len('.log'):] == '.log':
        from pypore.i_o.chimera_reader import ChimeraReader
        reader_class = ChimeraReader
    elif filename[-len('.hkd'):] == '.hkd':
        from pypore.i_o.heka_reader import HekaReader
        reader_class = HekaReader

    if reader_class is None:
        import os
        raise ValueError("No reader was found for the file extension '{0}'.".format(os.path.splitext(filename)[1]))

    return reader_class(filename)
