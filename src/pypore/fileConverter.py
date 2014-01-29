'''
Created on Jan 28, 2014

@author: will
'''
import cythonsetup
from DataFileOpener import prepareDataFile, getNextBlocks, openData
import dataFile as df
import scipy.signal as sig

def convertFile(filename, outputFilename=None):
    '''
    Convert a file to the pypore .h5 file format. Returns the new file's name.
    '''
    f, params = prepareDataFile(filename)
    
    sampleRate = params['sample_rate']
    nPoints = params['points_per_channel_total']
    
    if outputFilename is None:
        outputFilename = filename.split('.')[0] + '.h5'
    
    saveFile = df.openFile(outputFilename, mode='w', sampleRate=sampleRate, nPoints=nPoints)
    
    blocksToGet = 1
    data = getNextBlocks(f, params, blocksToGet)[0]
    
    n = data.size
    i = 0
    while n > 0:
        print "n:", n, "i:", i
        saveFile.root.data[i:n + i] = data[:]
        i += n
        data = getNextBlocks(f, params, blocksToGet)[0]
        n = data.size
        
    f.close()
    
    saveFile.flush()
    saveFile.close()
    return outputFilename

def filterFile(filename, filterFrequency, outputFileName=None):
    print "opening data"
    specs = openData(filename)
    print "data open"
    
    data = specs['data'][0]
    
    sampleRate = specs['sample_rate']
    nPoints = len(data)
    
    if outputFileName is None:
        outputFileName = filename.split('.')[0] + '.h5'
    
    saveFile = df.openFile(outputFileName, mode='w', sampleRate=sampleRate, nPoints=nPoints)
    
    Wn = filterFrequency / (0.5 * sampleRate)  # Wn is a fraction of the Nyquist frequency (half the sampling frequency).
    
    print "Wn:", Wn
    b, a = sig.butter(6, Wn)
    print "filter set"
    
    saveFile.root.data[:] = sig.filtfilt(b, a, data)[:]
    
    saveFile.flush()
    saveFile.close()
    return outputFileName

filterFile('../data/spheres_20140114_154938.log', 1e5, 'testFilter.h5')
