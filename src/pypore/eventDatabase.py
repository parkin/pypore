'''
Created on Sep 13, 2013

@author: parkin
'''

import tables as tb

# Description of events table
class _Event(tb.IsDescription):
    """
    Description of the table /events/eventTable.
    """
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
    
    >>> import pypore.eventDatabase as ed
    >>> database = ed.openFile('test.h5',mode='w')
    >>> database.close()
    >>> os.remove('test.h5')
    '''
    
    DEFAULT_MAX_EVENT_LENGTH = 100
    maxEventLength = DEFAULT_MAX_EVENT_LENGTH
    eventRow = None
    
    def appendEvent(self, arrayRow, eventStart, eventLength, nLevels, rawPointsPerSide, \
                    baseline, currentBlockage, area, rawData=None, levels=None, levelLengths=None):
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
        row = self.getEventTableRow()
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
        Removes /events and then reinitializes the /events group. Note
        that any references to any table/matrix in this group will
        be broken and need to be refreshed.
        
        >>> h5 = openFile('test.h5',mode='a')
        >>> table = h5.getEventTable()
        >>> h5.cleanDatabase() // table is now refers to deleted table
        >>> table = h5.getEventTable() // table now refers to live table
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
        
    def getEventCount(self):
        """
        Returns the number of rows in the /events/eventTable table.
        Note this will flush the table so the data is correct.
        """
        self.getEventTable().flush()
        return self.getEventTable().nrows
    
    def getEventDataAt(self, i):
        """
        Returns the event data portion of rawData[i], ie excluding the
        raw buffer points kept on each side of an event.
        """
        row = self.getEventRow(i)
        arrayRow = row['arrayRow']
        eventLength = row['eventLength']
        rawPointsPerSide = row['rawPointsPerSide']
        return self.root.events.rawData[arrayRow][rawPointsPerSide:eventLength+rawPointsPerSide]
    
    def getEventRow(self, i):
        """
        Returns the i'th row in /events/eventTable. Throws IndexOutOfBounds
        or similar error if i out of bounds. Note this flushes the
        eventTable before returning.
        """
        self.root.events.eventTable.flush()
        return self.root.events.eventTable[i]
        
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
    
    def getEventTableRow(self):
        """
        Gets the PyTables Row object of the eventTable.
        root.events.eventTable.row
        
        If you need a specific row in eventTable, use getEventRow(i)
        """
        if self.eventRow == None:
            self.eventRow = self.root.events.eventTable.row
        return self.eventRow
    
    def getLevelLengthsAt(self, i):
        """
        Returns a numpy array of the levelLengths corresponding to the event
        in row 'i' of eventTable.
        """
        row = self.getEventRow(i)
        arrayRow = row['arrayRow']
        nLevels = row['nLevels']
        return self.root.events.levelLengths[arrayRow][:nLevels]
    
    def getLevelsAt(self, i):
        """
        Returns a numpy array of the levels corresponding to the event
        in row 'i' of eventTable.
        """
        row = self.getEventRow(i)
        arrayRow = row['arrayRow']
        nLevels = row['nLevels']
        return self.root.events.levels[arrayRow][:nLevels]
    
    def getRawDataAt(self, i):
        """
        Returns the rawData numpy matrix associated with event 'i'.
        """
        row = self.getEventRow(i)
        arrayRow = row['arrayRow']
        eventLength = row['eventLength']
        rawPointsPerSide = row['rawPointsPerSide']
        return self.root.events.rawData[arrayRow][:eventLength+2*rawPointsPerSide]
    
    def getSampleRate(self):
        """
        Gets the sample rate at root.events.eventTable.attrs.sampleRate
        """
        return self.root.events.eventTable.attrs.sampleRate
    
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
            self.eventRow = None
            
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
            
    def removeEvent(self, i):
        """
        Deletes event i from /events/eventTable. Does nothing if
        i < 0 or i >= eventCount. Note the table will be flushed.
        Note that deleting a row in a table of length 1 is not
        currently supported.
        """
        self.removeEvents(i, i + 1)
            
    def removeEvents(self, i, j):
        """
        Deletes events [i,j) from /events/eventTable. Does nothing
        if deleting out of range events is requested. Note the table
        will be flushed. Note that deleting all the rows in a 
        table is not currently supported. Refer to cleanDatabase for
        deleting everything.
        
        Args:
            i - First entry to delete.  Must be within range
                0 < i < eventCount
            j - 1 past last entry to delete.  Must be within range
                i < j <= eventCount
        """
        eventCount = self.getEventCount()
        
        if i >= 0 and i < eventCount and j > i and j <= eventCount:
            # Currently cannot delete EVERY row in a table.
            if j - i < eventCount:
                self.getEventTable().removeRows(i, j)
            else:
                print "removeEvents FAILED: Removing all rows in table not currently supported."
        self.getEventTable().flush()
        
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
        mode = kargs['mode']
        if 'w' in mode or 'a' in mode:
            f.initializeDatabase(*args, **kargs)
    return f
