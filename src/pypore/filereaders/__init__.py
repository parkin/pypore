
def get_reader_from_filename(filename):
    import pypore.cythonsetup

    # TODO implement for other file types

    # if '.h5' in filename:
    #     return open_pypore_file(filename, decimate)
    if '.log' in filename:
        from chimera_reader import ChimeraReader
        try:
            reader = ChimeraReader(filename)
            return reader
        except Exception, e:
            print e

    # elif '.hkd' in filename:
    #     return open_heka_file(filename, decimate)
    # elif '.mat' in filename:
    #     return open_gabys_file(filename, decimate)
    #
    # return {'error': 'File not specified with correct extension. Possibilities are: \'.log\', \'.hkd\''}