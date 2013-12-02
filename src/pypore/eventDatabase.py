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
    PyTables HDF5 database storing events and corresponding data.
    Inherits from tables.file.File, so you can interact with this
    just as you would a PyTables File object. However, this contains
    some extra convenience methods for storing/reading events
    and event data.
    
    Automatically adds a group
    /events
    With table
    /events/eventTable
    and matrices
    /events/rawData, /event/levels, and /event/levelLength
    
    Must be instantiated by calling eventDatabase's
    
    >>> eventDatabase = openFile('test.h5',mode='w')
    >>> os.remove('test.h5')
    '''
    
    maxEventLength = 100
    
    def __init__(self, pytablesFile, *args, **kargs):
        """
        Constructor for a new EventDatabase.  Must be called with
        an open tables.file.File object.
        
        Args:
            pytablesFile: Open tables.file.File object to be converted
                        to an EventDatabase object
        Kargs:
            mode: pytables mode used to open the pytablesFile.
        """
        self.__dict__ = pytablesFile.__dict__
        if 'mode' in kargs:
            if 'w' in kargs['mode']:
                self.initializeDatabase(*args, **kargs)
    
    def appendLevelLengths(self, levelLengths):
        """
        Appends a numpy matrix levelLengths to root.events.levelLengths
        """
        self.root.events.levelLengths.append(levelLengths)
    
    def appendLevels(self, levels):
        """
        Appends a numpy matrix levels to root.events.levels
        """
        self.root.events.levels.append(levels)
    
    def appendRawData(self, data):
        """
        Appends a numpy matrix data to root.events.rawData
        """
        self.root.events.rawData.append(data)
        
    def getEventRow(self):
        """
        Gets the PyTables Row object of the eventTable.
        """
        return self.root.events.eventTable.row
    
    def getEventsGroup(self):
        """
        Returns the events group in the PyTables HDF5 file.
        """
        return self.root.events
    
    def initializeDatabase(self, *args, **kargs):
        """
        Initializes the EventDatabase.  Adds a group 'events' with
        table 'eventsTable' and matrices 'rawData', 'levels', and 'levelLengths'.
        
        Args:
        Kargs:
            -maxEventLength: Maximum number of datapoints for an event to be added.
        """
        if 'maxEventLength' in kargs:
            self.maxEventLength = kargs['maxEventLength']
        if 'events' not in self.root:
            self.createGroup(self.root, 'events', 'Events')
            
        if not 'eventTable' in self.root.events:
            self.createTable(self.root.events, 'eventTable', _Event, 'Event parameters')
            
        filters = tb.Filters(complib='blosc', complevel=4)
        shape = (0, self.maxEventLength)
        a = tb.FloatAtom()
        b = tb.IntAtom()
        
        if not 'rawData' in self.root.events:
            self.createEArray(self.root.events, 'rawData',
                                 a, shape=shape,
                                 title="Raw data points",
                                 filters=filters)
        
        if not 'levels' in self.root.events:
            self.createEArray(self.root.events, 'levels',
                                 a, shape=shape,
                                 title="Cusum levels",
                                 filters=filters)
        
        if not 'levelLengths' in self.root.events:
            self.createEArray(self.root.events, 'levelLengths',
                                 b, shape=shape,
                                 title="Lengths of the cusum levels",
                                 filters=filters)
        
def openFile(*args, **kargs):
    """
    Opens an EventDatabase by calling tables.openFile and then
    copying the __dict__ to a new EventDatabase instance.
    
    Args:
        maxEventLength: Maximum length of an event for the table. Default is 100.
    """
    f = tb.openFile(*args, **kargs)
    e = EventDatabase(f, *args, **kargs)
    return e
