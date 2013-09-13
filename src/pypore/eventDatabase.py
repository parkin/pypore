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
    rawPointsPerSide = tb.UIntCol(pos=3)
    baseline = tb.FloatCol(pos=4)
    currentBlockage = tb.FloatCol(pos=5)
    area = tb.FloatCol(pos=6)
    
def initializeEventsDatabase(filename):
    h5file = tb.openFile(filename, mode='w')
    h5file.createGroup(h5file.root, 'events', 'Events')
    h5file.createTable(h5file.root.events, 'eventTable', Event, 'Event parameters')
    h5file.createVLArray(h5file.root.events, 'rawData',
                         tb.FloatAtom(shape=()),
                        "Raw data with raw points buffer.")
    h5file.createVLArray(h5file.root.events, 'levels',
                         tb.FloatAtom(shape=()),
                        "Cusum levels")
    h5file.createVLArray(h5file.root.events, 'levelIndices',
                         tb.FloatAtom(shape=()),
                        "Indices for cusum levels")
    
    return h5file