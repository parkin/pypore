
def get_reader_from_filename(filename):

    # TODO implement for other file types

    # if '.h5' in filename:
    #     return open_pypore_file(filename, decimate)
    if '.h5' in filename:
        from data_file_reader import DataFileReader as ReaderClass
    elif '.log' in filename:
        from chimera_reader import ChimeraReader as ReaderClass
    else:
        print "error"
        return "No default reader available for file extension of {0}".format(filename)

    try:
        reader = ReaderClass(filename)
        return reader
    except Exception, e:
        print e
        return e.message



    # elif '.hkd' in filename:
    #     return open_heka_file(filename, decimate)
    # elif '.mat' in filename:
    #     return open_gabys_file(filename, decimate)
    #
    # return {'error': 'File not specified with correct extension. Possibilities are: \'.log\', \'.hkd\''}