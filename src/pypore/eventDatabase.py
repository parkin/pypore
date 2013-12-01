'''
Created on Sep 13, 2013

@author: parkin
'''

import tables as tb

# Description of events table
class _Event(tb.IsDescription):
    # UIntAtom = uint32
    arrayRow = tb.UIntCol(pos=0)  # indicates the corresponding row in the
                                    # eventData and rawData etc VLArrays
    eventStart = tb.UIntCol(itemsize=8, pos=1)  # start index of the event in the data
    eventLength = tb.UIntCol(pos=2)
    nLevels = tb.UIntCol(pos=3)
    rawPointsPerSide = tb.UIntCol(pos=4)
    baseline = tb.FloatCol(pos=5)
    currentBlockage = tb.FloatCol(pos=6)
    area = tb.FloatCol(pos=7)
    
class EventDatabase(tb.file.File):
    '''
    HDF5 database storing events and corresponding data.
    '''
    
    def __init__(self, *args, **kargs):
        pass
    
    def appendRawData(self, data):
        """
        Appends a numpy matrix data to root.events.rawData
        """
        self.root.events.rawData.append(data)
    
    def getEventsGroup(self):
        """
        Returns the events group in the PyTables HDF5 file.
        """
        return self.root.events
    
    def initializeEmptyDatabase(self, *args, **kargs):
        maxEventSteps = 100
        if 'maxEventSteps' in kargs:
            maxEventSteps = kargs['maxEventSteps']
        self.createGroup(self.root, 'events', 'Events')
        self.createTable(self.root.events, 'eventTable', _Event, 'Event parameters')
        filters = tb.Filters(complib='blosc', complevel=4)
        shape = (0, maxEventSteps)
        a = tb.FloatAtom()
        b = tb.IntAtom()
        self.createEArray(self.root.events, 'rawData',
                             a, shape=shape,
                             title="Raw data points",
                             filters=filters)
        self.createEArray(self.root.events, 'levels',
                             a, shape=shape,
                             title="Cusum levels",
                             filters=filters)
        self.createEArray(self.root.events, 'levelLengths',
                             b, shape=shape,
                             title="Lengths of the cusum levels",
                             filters=filters)
        
def openFile(*args, **kargs):
    """
    Opens an EventDatabase by calling tables.openFile and then
    copying the __dict__ to a new EventDatabase instance.
    """
    f = tb.openFile(*args, **kargs)
    e = EventDatabase()
    e.__dict__ = f.__dict__
    if 'mode' in kargs:
        if kargs['mode'] == 'w':
            e.initializeEmptyDatabase(*args, **kargs)
    return e
