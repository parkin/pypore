'''
Created on May 23, 2013

@author: parkin
'''

import scipy.io as sio
import numpy as np
cimport numpy as np
import os

DTYPE = np.double
ctypedef np.double_t DTYPE_t

# Data types list, in order specified by the HEKA file header v2.0.
# Using big-endian.
# Code 0=uint8,1=uint16,2=uint32,3=int8,4=int16,5=int32,
#    6=single,7=double,8=string64,9=string512
encodings = [np.dtype('>u1'), np.dtype('>u2'), np.dtype('>u4'), 
             np.dtype('>i1'), np.dtype('>i2'), np.dtype('>i4'), 
             np.dtype('>f4'), np.dtype('>f8'), np.dtype('>S64'), 
             np.dtype('>S512'), np.dtype('<u2')]

cpdef openData(filename, decimate=False):
    '''
    Opens a datafile and returns a dictionary with the data in 'data'.
    If unable to return, will return an error message.
    
    Assumes '.log' extension is Chimera data.  Chimera data requires a '.mat'
     file with the same name to be in the same folder.
     
    Assumes '.hkd' extension is Heka data.
    '''
    if '.log' in filename:
        return openChimeraFile(filename, decimate)
    if '.hkd' in filename:
        return openHekaFile(filename, decimate)
        
    return {'error': 'File not specified with correct extension. Possibilities are: \'.log\', \'.hkd\''}
    
cpdef prepareDataFile(filename):
    '''
    Opens a data file, reads relevant parameters, and 
    
    Assumes '.log' extension is Chimera data.  Chimera data requires a '.mat'
     file with the same name to be in the same folder. - not yet implemented
     
    Assumes '.hkd' extension is Heka data.
    
    Returns
    datafile, params
    
    If there was an error opening the files, params will have 'error' key
    with string description
    '''
    if '.log' in filename:
        return prepareChimeraFile(filename)
    if '.hkd' in filename:
        return prepareHekaFile(filename)
        
    return 0,{'error': 'File not specified with correct extension. Possibilities are: \'.log\', \'.hkd\''}

cpdef getNextBlocks(datafile, params, int n=1):
    '''
    Gets the next n blocks (~5000 datapoints) of data from filename
    
    Pass in an open datafile,
    params - 
    n - number of blocks to read and return.
    
    Assumes '.log' extension is Chimera data.  Chimera data requires a '.mat'
     file with the same name to be in the same folder. - not yet implemented
     
    Assumes '.hkd' extension is Heka data.
    '''
    if '.log' in params['filename']:
        return getNextChimeraBlocks(datafile, params, n)
    if '.hkd' in params['filename']:
        return getNextHekaBlocks(datafile, params, n)
        
    return 'File not specified with correct extension. Possibilities are: \'.log\', \'.hkd\''

cdef openChimeraFile(filename, decimate=False):
    '''
    Reads files created by the Chimera acquisition software.  It requires a
    filename.log file with the data, and a filename.mat file containing the
    parameters of the run.
    
    Returns a dictionary with the keys/values in the filename.mat file
    as well as 'data', a numpy array of the current values
    '''
    # remove 'log' append 'mat'
    datafile, p = prepareChimeraFile(filename)
    
    if 'error' in p:
        return p
    
    cdef long ADCBITS = p['ADCBITS']
    cdef double ADCvref = p['ADCvref']
    datatype = p['datatype']
#     ctypedef datatype datatype_t
    specsfile = p['specsfile']
    

    cdef long bitmask = (2**16) - 1 - (2**(16-ADCBITS) - 1)
    cdef long num_points = 0
    cdef int block_size = 0
    cdef long decimated_size = 0
    cdef long i = 0
    cdef np.ndarray[DTYPE_t] logdata, readvalues
    cdef np.ndarray rawvalues
    if decimate:
        # Calculate number of points in the dataset
        filesize = os.path.getsize(filename)
        num_points = filesize/datatype.itemsize
        # use 5000 for plot decimation
        block_size = 5000
        decimated_size = int(2*num_points/block_size)
        if num_points%block_size > 0: # will there be a block at the end with < block_size datapoints?
            decimated_size = decimated_size + 2
        logdata = np.empty(decimated_size)
        i = 0
        while True:
            rawvalues = np.fromfile(datafile,datatype,block_size)
            if rawvalues.size < 1:
                break
            readvalues = -ADCvref + (2*ADCvref)*(rawvalues & bitmask)/(2**16)
            logdata[i] = np.max(readvalues)
            logdata[i+1] = np.min(readvalues)
            i += 2
            
        # Change the sample rate
        specsfile['SETUP_ADCSAMPLERATE'][0][0] = specsfile['SETUP_ADCSAMPLERATE'][0][0]*2/block_size
    else:
        rawvalues = np.fromfile(datafile,datatype)
        rawvalues = rawvalues & bitmask
        logdata = -ADCvref + (2*ADCvref) * rawvalues / (2**16);

    specsfile['data'] = [logdata]
    datafile.close()
    return specsfile

cdef prepareChimeraFile(filename):
    # remove 'log' append 'mat'
    s = list(filename)
    s.pop()
    s.pop()
    s.pop()
    s.append('mat')
    # load the matlab file with parameters for the runs
    try:
        specsfile = sio.loadmat("".join(s))
    except IOError:
        return 0, {'error': 'Error opening ' + filename + ', Chimera .mat specs file of same name must be located in same folder.'}
    
    # Calculate number of points per channel
    filesize = os.path.getsize(filename)
    datatype = np.dtype('<u2')
    cdef int points_per_channel_per_block = 10000
    cdef long points_per_channel_total = filesize/datatype.itemsize

    cdef long ADCBITS = specsfile['SETUP_ADCBITS'][0][0]
    cdef double ADCvref = specsfile['SETUP_ADCVREF'][0][0]
    
    datafile = open(filename, 'rb')
    
    cdef long bitmaskk = (2**16) - 1 - (2**(16-ADCBITS) - 1)
    
    p = {'filetype': 'chimera',
         'ADCBITS': ADCBITS, 'ADCvref': ADCvref, 'datafile': datafile,
         'datatype': datatype, 'specsfile': specsfile, 
         'bitmask': bitmaskk, 'filename': filename,
         'sample_rate': specsfile['SETUP_ADCSAMPLERATE'][0][0],
         'points_per_channel_per_block': points_per_channel_per_block,
         'points_per_channel_total': points_per_channel_total}
    
    return datafile, p

cdef getNextChimeraBlocks(datafile, params, int n):
    '''
    '''
    cdef int block_size = params['points_per_channel_per_block']
    
    datatype = params['datatype']
    cdef long bitmask = params['bitmask']
    cdef double ADCvref = params['ADCvref']
    
    cdef np.ndarray rawvalues = np.fromfile(datafile,datatype, n*block_size)
    rawvalues = rawvalues & bitmask
    cdef np.ndarray[DTYPE_t] logdata = -ADCvref + (2*ADCvref) * rawvalues / (2**16)

    return [logdata]
        
cdef prepareHekaFile(filename):
    f = open(filename, 'rb')
    # Check that the first line is as expected
    line = f.readline()
    if not 'Nanopore Experiment Data File V2.0' in line:
        f.close()
        return 0, {'error': 'Heka data file format not recognized.'}
    # Just skip over the file header text, should be always the same.
    while True:
        line = f.readline()
        if 'End of file format' in line:
            break
    
    # So now f should be at the binary data.
    
    ## Read binary header parameter lists
    per_file_param_list = _readHekaHeaderParamList(f, np.dtype('>S64'), encodings)
    per_block_param_list = _readHekaHeaderParamList(f, np.dtype('>S64'), encodings)
    per_channel_param_list = _readHekaHeaderParamList(f, np.dtype('>S64'), encodings)
    channel_list = _readHekaHeaderParamList(f, np.dtype('>S512'), encodings)
    
    ## Read per_file parameters
    per_file_params = _readHekaHeaderParams(f, per_file_param_list)
    
    ## Calculate sizes of blocks, channels, etc
    cdef long per_file_header_length = f.tell()
    
    # Calculate the block lengths
    cdef long per_channel_per_block_length = _getParamListByteLength(per_channel_param_list)
    cdef long per_block_length = _getParamListByteLength(per_block_param_list)
    
    cdef int channel_list_number = len(channel_list)
    
    cdef long header_bytes_per_block = per_channel_per_block_length*channel_list_number
    cdef long data_bytes_per_block = per_file_params['Points per block'] * 2 * channel_list_number
    cdef long total_bytes_per_block = header_bytes_per_block + data_bytes_per_block + per_block_length
    
    # Calculate number of points per channel
    cdef long filesize = os.path.getsize(filename)
    cdef long num_blocks_in_file = int((filesize - per_file_header_length)/total_bytes_per_block)
    cdef long remainder = (filesize - per_file_header_length)%total_bytes_per_block
    if not remainder == 0:
        f.close()
        return 0, {'error': 'Error, data file ends with incomplete block'}
    cdef long points_per_channel_total = per_file_params['Points per block'] * num_blocks_in_file
    cdef long points_per_channel_per_block = per_file_params['Points per block']
    
    p = {'filetype': 'heka',
         'per_file_param_list': per_file_param_list, 'per_block_param_list': per_block_param_list,
         'per_channel_param_list': per_channel_param_list, 'channel_list': channel_list,
         'per_file_params': per_file_params, 'per_file_header_length': per_file_header_length,
         'per_channel_per_block_length': per_channel_per_block_length,
         'per_block_length': per_block_length, 'channel_list_number': channel_list_number,
         'header_bytes_per_block': header_bytes_per_block, 
         'data_bytes_per_block': data_bytes_per_block,
         'total_bytes_per_block': total_bytes_per_block,  'filesize': filesize,
         'num_blocks_in_file': num_blocks_in_file,
         'points_per_channel_total': points_per_channel_total,
         'points_per_channel_per_block': points_per_channel_per_block,
         'sample_rate': 1.0/per_file_params['Sampling interval'],
         'filename': filename}
    
    return f, p


cdef openHekaFile(filename, decimate=False):
    '''
    Gets data from a file generated by Ken's LabView code v2.0 for HEKA acquisition.
    Visit https://drndiclab-bkup.physics.upenn.edu/wiki/index.php/HKD_File_I/O_SubVIs
        for a description of the heka file format.
        
    Returns a dictionary with entries:
        -'data', a numpy array of the current values
        -'SETUP_ADCSAMPLERATE'
        
    Currently only works with one channel measurements
    '''
    # Open the file and read all of the header parameters
    f, p = prepareHekaFile(filename)
    
    per_file_params = p['per_file_params']
    channel_list = p['channel_list']
    cdef long num_blocks_in_file = p['num_blocks_in_file']
    cdef long points_per_channel_total = p['points_per_channel_total']
    per_block_param_list = p['per_block_param_list']
    per_channel_param_list = p['per_channel_param_list']
    cdef long points_per_channel_per_block = p['points_per_channel_per_block']
    
    data = []
    cdef double sample_rate = 1.0/per_file_params['Sampling interval']
    for _ in channel_list:
        if decimate: # If decimating, just keep max and min value from each block
            data.append(np.empty(num_blocks_in_file*2))
        else:
            data.append(np.empty(points_per_channel_total))  # initialize array
        
    for i in xrange(0,num_blocks_in_file):
        block = _readHekaNextBlock(f, per_file_params, per_block_param_list, per_channel_param_list, channel_list, points_per_channel_per_block)
        for j in xrange(len(block)):
            if decimate: # if decimating data, only keep max and min of each block
                data[j][2*i] = np.max(block[j])
                data[j][2*i+1] = np.min(block[j])
            else:
                data[j][i*points_per_channel_per_block:(i+1)*points_per_channel_per_block] = block[j]
            
    if decimate:
        sample_rate = sample_rate*2/per_file_params['Points per block'] # we are downsampling
        
    # return dictionary
    # samplerate is i [[]] because of how chimera data is returned.
    specsfile = {'data': data, 'SETUP_ADCSAMPLERATE': [[sample_rate]]}
    
    return specsfile

cdef getNextHekaBlocks(datafile, params, int n):
    per_file_params = params['per_file_params']
    per_block_param_list = params['per_block_param_list']
    per_channel_param_list = params['per_channel_param_list']
    channel_list = params['channel_list']
    cdef long points_per_channel_per_block = params['points_per_channel_per_block']
    
    blocks = []
    cdef long totalsize = 0
    cdef long size = 0
    done = False
    for i in xrange(0,n):
        block = _readHekaNextBlock(datafile, per_file_params, 
                                   per_block_param_list, per_channel_param_list, 
                                   channel_list, points_per_channel_per_block)
        if block[0].size == 0:
            return block
        blocks.append(block)
        size = block[0].size
        totalsize = totalsize + size
        if size < points_per_channel_per_block: # did we reach the end?
            break
        
    # stitch the data together
    data = []
    index = []
    for _ in xrange(0, len(channel_list)):
        data.append(np.empty(totalsize))
        index.append(0)
    for block in blocks:
        for i in xrange(0, len(channel_list)):
            data[i][index[i]:index[i]+block[i].size] = block[i]
            index[i] = index[i] + block[i].size
            
    return data

cdef _readHekaNextBlock(f, per_file_params, per_block_param_list, per_channel_param_list, channel_list, long points_per_channel_per_block):
    '''
    Reads the next block of heka data.
    Returns a dictionary with 'data', 'per_block_params', and 'per_channel_params'.
    '''
    
    # Read block header
    per_block_params = _readHekaHeaderParams(f, per_block_param_list)
    if per_block_params == None:
        return [np.empty(0)]
    
    # Read per channel header
    per_channel_block_params = []
    for _ in channel_list: # underscore used for discarded parameters
        channel_params = {}
        # i[0] = name, i[1] = datatype
        for i in per_channel_param_list:
            channel_params[i[0]] = np.fromfile(f, i[1], 1)[0]
        per_channel_block_params.append(channel_params)
        
    # Read data
    data = []
    dt = np.dtype('>i2') # int16
    cdef np.ndarray values
    for i in xrange(0,len(channel_list)):
        values = np.fromfile(f, dt, count=points_per_channel_per_block) * per_channel_block_params[i]['Scale']
        # get rid of nan's
#         values[np.isnan(values)] = 0
        data.append(values)
        
    return data
    
cdef long _getParamListByteLength(param_list):
    '''
    Returns the length in bytes of the sum of all the parameters in the list.
    Here, list[i][0] = param, list[i][1] = np.dtype
    '''
    cdef long sizee = 0
    for i in param_list:
        sizee = sizee + i[1].itemsize
    return sizee
    
cdef _readHekaHeaderParams(f, param_list):
    
    params = {}
    # pair[0] = name, pair[1] = np.datatype
    cdef np.ndarray array
    for pair in param_list:
        array = np.fromfile(f, pair[1], 1)
        if array.size > 0:
            params[pair[0]] = array[0]
        else:
            return None
    return params
        
cdef _readHekaHeaderParamList(f, datatype, encodings):
    '''
    Reads the binary parameter list of the following format:
        3 null bytes
        1 byte uint8 - how many params following
        params - 1 byte uint8 - code for datatype (eg encoding[code])
                 datatype.intemsize bytes - name the parameter
    Returns a list of parameters, with
        item[0] = name
        item[1] = numpy datatype
    '''
    param_list = []
    f.read(3)  # read null characters?
    dt = np.dtype('>u1')
    cdef int num_params = np.fromfile(f, dt, 1)[0]
    for _ in xrange(0, num_params):
        type_code = np.fromfile(f, dt,1)[0]
        name = np.fromfile(f, datatype, 1)[0].strip()
        param_list.append([name, encodings[type_code]])
    return param_list


