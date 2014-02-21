"""
Created on Jan 28, 2014

@author: parkin1
"""
import cythonsetup
from dataFileOpener import prepareDataFile, getNextBlocks, openData
import dataFile as dF
import scipy.signal as sig


def convert_file(filename, output_filename=None):
    """
    Convert a file to the pypore .h5 file format. Returns the new file's name.
    """
    f, params = prepareDataFile(filename)
    
    sample_rate = params['sample_rate']
    n_points = params['points_per_channel_total']
    
    if output_filename is None:
        output_filename = filename.split('.')[0] + '.h5'
    
    save_file = dF.openFile(output_filename, mode='w', sampleRate=sample_rate, nPoints=n_points)
    
    blocks_to_get = 1
    data = getNextBlocks(f, params, blocks_to_get)[0]
    
    n = data.size
    i = 0
    while n > 0:
        save_file.root.data[i:n + i] = data[:]
        i += n
        data = getNextBlocks(f, params, blocks_to_get)[0]
        n = data.size
        
    f.close()
    
    save_file.flush()
    save_file.close()
    return output_filename


def filter_file(filename, filter_frequency, output_file_name=None):
    """
    Filters the data.
    """
    specs = openData(filename)

    data = specs['data'][0]
    
    sample_rate = specs['sample_rate']
    n_points = len(data)
    
    if output_file_name is None:
        output_file_name = filename.split('.')[0] + '.h5'
    
    save_file = dF.openFile(output_file_name, mode='w', sampleRate=sample_rate, nPoints=n_points)

    # wn is a fraction of the Nyquist frequency (half the sampling frequency).
    wn = filter_frequency / (0.5 * sample_rate)
    
    b, a = sig.butter(6, wn)

    save_file.root.data[:] = sig.filtfilt(b, a, data)[:]
    
    save_file.flush()
    save_file.close()
    return output_file_name

filter_file('../data/spheres_20140114_154938.log', 1e5, 'testFilter.h5')
