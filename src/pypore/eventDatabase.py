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
    and event data. Note that EventDatabase allows you to interact
    with this PyTables file in the usual PyTables file manner, so you
    can potentially mangle the data from the original EventDatabase
    format.
    
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
    
    DEFAULT_MAX_EVENT_LENGTH = 100
    maxEventLength = DEFAULT_MAX_EVENT_LENGTH
    eventRow = None
    
    def appendEvent(self, arrayRow, eventStart, eventLength, nLevels, rawPointsPerSide,\
                    baseline, currentBlockage, area, rawData = None, levels = None, levelLengths = None):
        """
        Appends an event with the specified values to the eventsTable.  If rawData, levels, or levelLengths
        are included, they are added to the corresponding matrices.
        
        Args:
            arrayRow: The row in the rawData, levels, and levelLengths array that corresponds
                    to this event.
            eventStart: The starting index of this event in the data.
            eventLength: Number of data points in the event.
            nLevels: Number of levels in the event.
            rawPointsPerSide: Number of extra points kept on either side of the event in rawData.
            baseline: Open-pore current at the time of the event.
            currentBlockage: The mean current blockage of the event.
            area: The area of the event.
            rawData: Numpy array of the raw data.
            levels: Numpy array of the levels.
            levelLengths: Numpy array of the level lengths.
        """
        row = self.getEventRow()
        row['arrayRow'] = arrayRow
        row['eventStart'] = eventStart
        row['eventLength'] = eventLength
        row['nLevels'] = nLevels
        row['rawPointsPerSide'] = rawPointsPerSide
        row['baseline'] = baseline
        row['currentBlockage'] = currentBlockage
        row['area'] = area
        row.append()
        
        if rawData is not None:
            self.appendRawData(rawData)
        if levels is not None:
            self.appendLevels(levels)
        if levelLengths is not None:
            self.appendLevelLengths(levelLengths)
        
    
    def appendLevelLengths(self, levelLengths):
        """
        Appends a numpy matrix levelLengths to root.events.levelLengths
        """
        if levelLengths is not None:
            self.root.events.levelLengths.append(levelLengths)
    
    def appendLevels(self, levels):
        """
        Appends a numpy matrix levels to root.events.levels
        """
        if levels is not None:
            self.root.events.levels.append(levels)
    
    def appendRawData(self, rawData):
        """
        Appends a numpy matrix rawData to root.events.rawData
        """
        if rawData is not None:
            self.root.events.rawData.append(rawData)
            
    def cleanDatabase(self):
        """
        Removes /events and then reinitializes the /events group.
        """
        # remove the events group
        self.root.events._f_remove(recursive=True)
        
        self.initializeDatabase()
        
    @classmethod
    def convertToEventDatabase(cls, tablesObject):
        """
        Converts a PyTables object's __class__ field to EventDatabase so
        you can use the object as an EventDatabase object.
        """
        tablesObject.__class__ = EventDatabase
        
    def getEventRow(self):
        """
        Gets the PyTables Row object of the eventTable.
        """
        if self.eventRow == None:
            self.eventRow = self.root.events.eventTable.row
        return self.eventRow
    
    def getEventsGroup(self):
        """
        Returns the events group in the PyTables HDF5 file.
        """
        return self.root.events
    
    def getEventTable(self):
        """
        returns /events/eventTable
        """
        return self.root.events.eventTable
    
    def initializeDatabase(self, *args, **kargs):
        """
        Initializes the EventDatabase.  Adds a group 'events' with
        table 'eventsTable' and matrices 'rawData', 'levels', and 'levelLengths'.
        
        Args:
        Kargs:
            -maxEventLength: Maximum number of datapoints for an event to be added.
        """
        if 'maxEventLength' in kargs:
            if kargs['maxEventLength'] > self.maxEventLength:
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
    EventDatabase.convertToEventDatabase(f)
    if 'mode' in kargs:
        if 'w' in kargs['mode']:
            f.initializeDatabase(*args, **kargs)
    return f
