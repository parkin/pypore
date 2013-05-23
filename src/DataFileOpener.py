'''
Created on May 23, 2013

@author: parkin
'''
import scipy.io as sio
import numpy as np

def openData(filename):
    '''
    Opens a datafile and returns a dictionary with the data in 'data'.
    If unable to return, will return an error message.
    
    Assumes '.log' extension is Chimera data.  Chimera data requires a '.mat'
     file with the same name to be in the same folder.
    '''
    if '.log' in filename:
        return _openChimera(filename)
        
    else:
        return 'File not specified with correct extension. Possibilities are: \'.log\''
        
def _openChimera(filename):
    # remove 'log' append 'mat'
    s = list(filename)
    s.pop()
    s.pop()
    s.pop()
    s.append('mat')
    # load the matlab file with parameters for the runs
    specsfile = sio.loadmat("".join(s))

    ADCBITS = specsfile['SETUP_ADCBITS'][0][0]
    ADCvref = specsfile['SETUP_ADCVREF'][0][0]

    datafile = open(filename)
    datatype = 'uint16'

    bitmask = (2**16) - 1 - (2**(16-ADCBITS) - 1);
    rawvalues = np.fromfile(datafile,datatype)
    readvalues = rawvalues & bitmask

    logdata = -ADCvref + (2*ADCvref) * readvalues / (2**16);
    specsfile['data'] = logdata
    return specsfile
    