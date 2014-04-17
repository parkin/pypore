"""
Note this is a legacy file and will be deleted.

Created on May 23, 2013

@author: parkin
"""
#cython: embedsignature=True

import numpy as np
cimport numpy as np
import tables as tb

DTYPE = np.float
ctypedef np.float_t DTYPE_t


cpdef open_data(filename, decimate=False):
    """
    Opens a datafile and returns a dictionary with the data in 'data'.
    If unable to return, will return an error message.

    :param StringType filename: Filename to open.

        - Assumes '.h5' extension is Pypore HDF5 format.
        - Assumes '.log' extension is Chimera data.  Chimera data requires a '.mat'\
            file with the same name to be in the same folder.
        - Assumes '.hkd' extension is Heka data.
        - Assumes '.mat' extension is Gaby's format.

    :param BooleanType decimate: Whether or not to decimate the data. Default is False.
    :returns: DictType -- dictionary with data in the 'data' key. If there is an error, it will return a
        dictionary with 'error' key containing a String error message.
    """
    # if '.h5' in filename:
    #     return open_pypore_file(filename, decimate)
    # if '.log' in filename:
    #     return open_chimera_file(filename, decimate)
    # if '.hkd' in filename:
    #     return open_heka_file(filename, decimate)
    if '.mat' in filename:
        return open_gabys_file(filename, decimate)

    return {'error': 'File not specified with correct extension. Possibilities are: \'.log\''}

cpdef prepare_data_file(filename):
    """
    Opens a data file, reads relevant parameters, and returns then open file and parameters.

    :param StringType filename: Filename to open and read parameters.

        - Assumes '.h5' extension is Pypore HDF5 format.
        - Assumes '.log' extension is Chimera data.  Chimera data requires a '.mat'\
            file with the same name to be in the same folder.
        - Assumes '.hkd' extension is Heka data.
        - Assumes '.mat' extension is Gaby's format.
    
    :returns: 2 things:

        #. datafile -- already opened :py:class:`pypore.filetypes.data_file.DataFile`.
        #. params -- parameters read from the file.

        If there was an error opening the files, params will have 'error' key with string description.
    """
    # if '.h5' in filename:
    #     return prepare_pypore_file(filename)
    # if '.log' in filename:
    #     return prepare_chimera_file(filename)
    # if '.hkd' in filename:
    #     return prepare_heka_file(filename)
    if '.mat' in filename:
        return prepare_gabys_file(filename)

    return 0, {'error': 'File not specified with correct extension. Possibilities are: \'.log\''}

cpdef get_next_blocks(datafile, params, int n=1):
    """
    Gets the next n blocks (~5000 data points) of data from filename.
    
    :param DataFile datafile: An already open :py:class:`pypore.filetypes.data_file.DataFile`.
    :param DictType params: Parameters of the file, usually the ones returned from :py:func:`prepare_data_file`.

        - Assumes '.h5' extension is Pypore HDF5 format.
        - Assumes '.log' extension is Chimera data.  Chimera data requires a '.mat'\
            file with the same name to be in the same folder.
        - Assumes '.hkd' extension is Heka data.
        - Assumes '.mat' extension is Gaby's format.

    :param IntType n: Number of blocks to read and return.
    :returns: ListType<np.array> -- List of numpy arrays, one for each channel of the data.
    """
    # if '.h5' in params['filename']:
    #     return get_next_pypore_blocks(datafile, params, n)
    # if '.log' in params['filename']:
    #     return get_next_chimera_blocks(datafile, params, n)
    # if '.hkd' in params['filename']:
    #     return get_next_heka_blocks(datafile, params, n)
    if '.mat' in params['filename']:
        return get_next_gabys_blocks(datafile, params, n)

    return 'File not specified with correct extension. Possibilities are: \'.log\''


cdef prepare_gabys_file(filename):
    """
    Implementation of :py:func:`prepare_data_file` for Gaby's .mat files.
    The file is a Matlab > 7.3 file, which is
    an HDF file and can be opened with pytables.
    """
    datafile = tb.openFile(filename, mode='r')

    group = datafile.getNode('/#refs#').b

    cdef int points_per_channel_per_block = 10000

    p = {'filetype': 'gabys',
         'dataGroup': group,
         'filename': filename, 'nextToSend': 0,  # next point we haven't sent
         'sample_rate': group.samplerate[0][0],
         'points_per_channel_per_block': points_per_channel_per_block,
         'points_per_channel_total': group.Raw[0].size}
    return datafile, p

cdef open_gabys_file(filename, decimate=False):
    f, p = prepare_gabys_file(filename)
    group = p['dataGroup']

    cdef np.ndarray data2

    cdef float sample_rate = p['sample_rate']

    if decimate:
        data2 = group.Raw[0][::5000]
        sample_rate /= 5000.
    else:
        data2 = group.Raw[0]

    specs_file = {'data': [data2], 'sample_rate': sample_rate}
    f.close()
    return specs_file

cdef get_next_gabys_blocks(datafile, params, int n):
    group = datafile.getNode('/#refs#').b

    cdef long next_to_send_2 = params['nextToSend']
    cdef long points_per_block2 = params['points_per_channel_per_block']
    cdef total_points_2 = params['points_per_channel_total']

    if next_to_send_2 >= total_points_2:
        return [group.Raw[0][next_to_send_2:].astype(DTYPE)]
    else:
        params['nextToSend'] += points_per_block2
        return [group.Raw[0][next_to_send_2:next_to_send_2 + points_per_block2].astype(DTYPE)]
