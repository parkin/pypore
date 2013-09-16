'''
Created on Sep 13, 2013

@author: parkin
'''

import tables as tb

# Description of events table
class Event(tb.IsDescription):
    # UIntAtom = uint32
    arrayRow = tb.UIntCol(pos=0)      # indicates the corresponding row in the
                                    # eventData and rawData etc VLArrays
    eventStart = tb.UIntCol(itemsize=8, pos=1)    # start index of the event in the data
    eventLength = tb.UIntCol(pos=2)
    nLevels = tb.UIntCol(pos=3)
    rawPointsPerSide = tb.UIntCol(pos=4)
    baseline = tb.FloatCol(pos=5)
    currentBlockage = tb.FloatCol(pos=6)
    area = tb.FloatCol(pos=7)
    
def initializeEventsDatabase(filename, maxEventSteps):
    h5file = tb.openFile(filename, mode='w')
    h5file.createGroup(h5file.root, 'events', 'Events')
    h5file.createTable(h5file.root.events, 'eventTable', Event, 'Event parameters')
    filters = tb.Filters(complib='blosc', complevel=4)
    shape = (0,maxEventSteps)
    a = tb.FloatAtom()
    h5file.createEArray(h5file.root.events, 'rawData',
                         a, shape=shape,
                         title="Raw data points",
                         filters=filters)
    h5file.createEArray(h5file.root.events, 'levels',
                         a, shape=shape,
                         title="Cusum levels",
                         filters=filters)
    h5file.createEArray(h5file.root.events, 'levelIndices',
                         a, shape=shape,
                         title="Indices for cusum levels",
                         filters=filters)
    
    return h5file