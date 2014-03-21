"""
Created on Sep 13, 2013

@author: `@parkin1`_
"""

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
    """
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
    >>> database = ed.open_file('tests.h5',mode='w')
    >>> database.close()
    >>> os.remove('tests.h5')
    """

    DEFAULT_MAX_EVENT_LENGTH = 100
    max_event_length = DEFAULT_MAX_EVENT_LENGTH
    event_row = None

    def append_event(self, arrayRow, eventStart, eventLength, nLevels, rawPointsPerSide, baseline, currentBlockage, area,
                    rawData=None, levels=None, levelLengths=None):
        """
        Appends an event with the specified values to the eventsTable.  If rawData, levels, or levelLengths
        are included, they are added to the corresponding matrices.
        
        :param Int arrayRow: The row in the rawData, levels, and levelLengths array that corresponds
                             to this event.
        :param eventStart: The starting index of this event in the data.
        :param eventLength: Number of data points in the event.
        :param nLevels: Number of levels in the event.
        :param rawPointsPerSide: Number of extra points kept on either side of the event in rawData.
        :param baseline: Open-pore current at the time of the event.
        :param currentBlockage: The mean current blockage of the event.
        :param area: The area of the event.
        :param rawData: Numpy array of the raw data.
        :param levels: Numpy array of the levels.
        :param levelLengths: Numpy array of the level lengths.
        """
        row = self.get_event_table_row()
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
            self.append_raw_data(rawData)
        if levels is not None:
            self.append_levels(levels)
        if levelLengths is not None:
            self.append_level_lengths(levelLengths)

    def append_level_lengths(self, levelLengths):
        """
        Appends a numpy matrix levelLengths to root.events.levelLengths
        """
        if levelLengths is not None:
            self.root.events.levelLengths.append(levelLengths)

    def append_levels(self, levels):
        """
        Appends a numpy matrix levels to root.events.levels
        """
        if levels is not None:
            self.root.events.levels.append(levels)

    def append_raw_data(self, rawData):
        """
        Appends a numpy matrix rawData to root.events.rawData
        """
        if rawData is not None:
            self.root.events.rawData.append(rawData)

    def clean_database(self):
        """
        Removes /events and then re-initializes the /events group. Note
        that any references to any table/matrix in this group will
        be broken and need to be refreshed.
        
        >>> h5 = open_file('tests.h5',mode='a')
        >>> table = h5.get_event_table()
        >>> h5.clean_database() // table is now refers to deleted table
        >>> table = h5.get_event_table() // table now refers to live table
        """
        # remove the events group
        self.root.events._f_remove(recursive=True)

        self.initialize_database()

    @classmethod
    def _convert_to_event_database(cls, tables_object):
        """
        Converts a PyTables object's __class__ field to EventDatabase so
        you can use the object as an EventDatabase object.
        """
        tables_object.__class__ = EventDatabase

    def get_event_count(self):
        """
        Returns the number of rows in the /events/eventTable table.
        Note this will flush the table so the data is correct.
        """
        self.get_event_table().flush()
        return self.get_event_table().nrows

    def get_event_data_at(self, i):
        """
        Returns the event data portion of rawData[i], ie excluding the
        raw buffer points kept on each side of an event.
        """
        row = self.get_event_row(i)
        array_row = row['arrayRow']
        event_length = row['eventLength']
        raw_points_per_side = row['rawPointsPerSide']
        return self.root.events.rawData[array_row][raw_points_per_side:event_length + raw_points_per_side]

    def get_event_row(self, i):
        """
        Returns the ith row in /events/eventTable. Throws IndexOutOfBounds
        or similar error if i out of bounds. Note this flushes the
        eventTable before returning.
        """
        self.root.events.eventTable.flush()
        return self.root.events.eventTable[i]

    def get_events_group(self):
        """
        Returns the events group in the PyTables HDF5 file.
        """
        return self.root.events

    def get_event_table(self):
        """
        returns /events/eventTable
        """
        return self.root.events.eventTable

    def get_event_table_row(self):
        """
        Gets the PyTables Row object of the eventTable.
        root.events.eventTable.row
        
        If you need a specific row in eventTable, use getEventRow(i)
        """
        if self.event_row is None:
            self.event_row = self.root.events.eventTable.row
        return self.event_row

    def get_level_lengths_at(self, i):
        """
        Returns a numpy array of the levelLengths corresponding to the event
        in row 'i' of eventTable.
        """
        row = self.get_event_row(i)
        array_row = row['arrayRow']
        n_levels = row['nLevels']
        return self.root.events.levelLengths[array_row][:n_levels]

    def get_levels_at(self, i):
        """
        Returns a numpy array of the levels corresponding to the event
        in row 'i' of eventTable.
        """
        row = self.get_event_row(i)
        array_row = row['arrayRow']
        n_levels = row['nLevels']
        return self.root.events.levels[array_row][:n_levels]

    def get_raw_data_at(self, i):
        """
        Returns the rawData numpy matrix associated with event 'i'.
        """
        row = self.get_event_row(i)
        array_row = row['arrayRow']
        event_length = row['eventLength']
        raw_points_per_side = row['rawPointsPerSide']
        return self.root.events.rawData[array_row][:event_length + 2 * raw_points_per_side]

    def get_sample_rate(self):
        """
        Gets the sample rate at root.events.eventTable.attrs.sampleRate
        """
        return self.root.events.eventTable.attrs.sampleRate

    def initialize_database(self, **kargs):
        """
        Initializes the EventDatabase.  Adds a group 'events' with
        table 'eventsTable' and matrices 'rawData', 'levels', and 'levelLengths'.

        :param kargs: Dictionary - includes:
                        -maxEventLength: Maximum number of datapoints for an event to be added.
        """
        if 'maxEventLength' in kargs:
            if kargs['maxEventLength'] > self.max_event_length:
                self.max_event_length = kargs['maxEventLength']
        if 'events' not in self.root:
            self.createGroup(self.root, 'events', 'Events')

        if not 'eventTable' in self.root.events:
            self.createTable(self.root.events, 'eventTable', _Event, 'Event parameters')
            self.event_row = None

        filters = tb.Filters(complib='blosc', complevel=4)
        shape = (0, self.max_event_length)
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

    def remove_event(self, i):
        """
        Deletes event i from /events/eventTable. Does nothing if
        i < 0 or i >= eventCount. Note the table will be flushed.
        Note that deleting a row in a table of length 1 is not
        currently supported.
        """
        self.remove_events(i, i + 1)

    def remove_events(self, i, j):
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
        event_count = self.get_event_count()

        if 0 <= i < event_count and i < j <= event_count:
            # Currently cannot delete EVERY row in a table.
            if j - i < event_count:
                self.get_event_table().removeRows(i, j)
            else:
                print "removeEvents FAILED: Removing all rows in table not currently supported."
        self.get_event_table().flush()


def open_file(*args, **kargs):
    """
    Opens an EventDatabase by calling tables.openFile and then
    copying the __dict__ to a new EventDatabase instance.
    
    Args:
        maxEventLength: Maximum length of an event for the table. Default is 100.
    """
    f = tb.openFile(*args, **kargs)
    EventDatabase._convert_to_event_database(f)
    if 'mode' in kargs:
        mode = kargs['mode']
        if 'w' in mode or 'a' in mode:
            f.initialize_database(**kargs)
    return f
