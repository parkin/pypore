"""
Created on Sep 13, 2013

@author: `@parkin`_
"""

import tables as tb
import csv


# Description of events table
class _Event(tb.IsDescription):
    """
    Description of the table /events/eventTable.
    """
    # UIntAtom = uint32
    array_row = tb.UIntCol(pos=0)  # indicates the corresponding row in the
    event_start = tb.UIntCol(itemsize=8, pos=1)  # start index of the event in the data
    event_length = tb.UIntCol(pos=2)
    n_levels = tb.UIntCol(pos=3)
    raw_points_per_side = tb.UIntCol(pos=4)
    baseline = tb.FloatCol(pos=5)
    current_blockage = tb.FloatCol(pos=6)
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
    /events/raw_data, /event/levels, and /event/levelLength
    
    Must be instantiated by calling eventDatabase's
    
    >>> import pypore.eventDatabase as ed
    >>> database = ed.open_file('tests.h5',mode='w')
    >>> database.close()
    >>> os.remove('tests.h5')
    """

    DEFAULT_MAX_EVENT_LENGTH = 100
    max_event_length = DEFAULT_MAX_EVENT_LENGTH
    event_row = None

    def append_event(self, array_row, event_start, event_length, n_levels, raw_points_per_side, baseline, current_blockage, area,
                    raw_data=None, levels=None, level_lengths=None):
        """
        Appends an event with the specified values to the eventsTable.  If raw_data, levels, or level_lengths
        are included, they are added to the corresponding matrices.
        
        :param Int array_row: The row in the raw_data, levels, and level_lengths array that corresponds
                             to this event.
        :param event_start: The starting index of this event in the data.
        :param event_length: Number of data points in the event.
        :param n_levels: Number of levels in the event.
        :param raw_points_per_side: Number of extra points kept on either side of the event in raw_data.
        :param baseline: Open-pore current at the time of the event.
        :param current_blockage: The mean current blockage of the event.
        :param area: The area of the event.
        :param raw_data: Numpy array of the raw data.
        :param levels: Numpy array of the levels.
        :param level_lengths: Numpy array of the level lengths.
        """
        row = self.get_event_table_row()
        row['array_row'] = array_row
        row['event_start'] = event_start
        row['event_length'] = event_length
        row['n_levels'] = n_levels
        row['raw_points_per_side'] = raw_points_per_side
        row['baseline'] = baseline
        row['current_blockage'] = current_blockage
        row['area'] = area
        row.append()

        if raw_data is not None:
            self.append_raw_data(raw_data)
        if levels is not None:
            self.append_levels(levels)
        if level_lengths is not None:
            self.append_level_lengths(level_lengths)

    def append_level_lengths(self, level_lengths):
        """
        Appends a numpy matrix level_lengths to root.events.level_lengths
        """
        if level_lengths is not None:
            self.root.events.level_lengths.append(level_lengths)

    def append_levels(self, levels):
        """
        Appends a numpy matrix levels to root.events.levels
        """
        if levels is not None:
            self.root.events.levels.append(levels)

    def append_raw_data(self, raw_data):
        """
        Appends a numpy matrix raw_data to root.events.raw_data
        """
        if raw_data is not None:
            self.root.events.raw_data.append(raw_data)

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
        Returns the event data portion of raw_data[i], ie excluding the
        raw buffer points kept on each side of an event.
        """
        row = self.get_event_row(i)
        array_row = row['array_row']
        event_length = row['event_length']
        raw_points_per_side = row['raw_points_per_side']
        return self.root.events.raw_data[array_row][raw_points_per_side:event_length + raw_points_per_side]

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
        Returns a numpy array of the level_lengths corresponding to the event
        in row 'i' of eventTable.
        """
        row = self.get_event_row(i)
        array_row = row['array_row']
        n_levels = row['n_levels']
        return self.root.events.level_lengths[array_row][:n_levels]

    def get_levels_at(self, i):
        """
        Returns a numpy array of the levels corresponding to the event
        in row 'i' of eventTable.
        """
        row = self.get_event_row(i)
        array_row = row['array_row']
        n_levels = row['n_levels']
        return self.root.events.levels[array_row][:n_levels]

    def get_raw_data_at(self, i):
        """
        Returns the raw_data numpy matrix associated with event 'i'.
        """
        row = self.get_event_row(i)
        array_row = row['array_row']
        event_length = row['event_length']
        raw_points_per_side = row['raw_points_per_side']
        return self.root.events.raw_data[array_row][:event_length + 2 * raw_points_per_side]

    def get_sample_rate(self):
        """
        Gets the sample rate at root.events.eventTable.attrs.sample_rate
        """
        return self.root.events.eventTable.attrs.sample_rate

    def initialize_database(self, **kargs):
        """
        Initializes the EventDatabase.  Adds a group 'events' with
        table 'eventsTable' and matrices 'raw_data', 'levels', and 'level_lengths'.

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

        filters = tb.Filters(complib='zlib', complevel=3)
        shape = (0, self.max_event_length)
        a = tb.FloatAtom()
        b = tb.IntAtom()

        if not 'raw_data' in self.root.events:
            self.createEArray(self.root.events, 'raw_data',
                              a, shape=shape,
                              title="Raw data points",
                              filters=filters)

        if not 'levels' in self.root.events:
            self.createEArray(self.root.events, 'levels',
                              a, shape=shape,
                              title="Cusum levels",
                              filters=filters)

        if not 'level_lengths' in self.root.events:
            self.createEArray(self.root.events, 'level_lengths',
                              b, shape=shape,
                              title="Lengths of the cusum levels",
                              filters=filters)

        # Create/init the debug group if needed.
        if 'debug' in kargs and kargs['debug']:
            if not 'debug' in self.root:
                self.createGroup(self.root, 'debug', 'Debug')
            debug_shape = (kargs['n_channels'], kargs['n_points'])
            if not 'data' in self.root.debug:
                self.createCArray(self.root.debug, 'data',
                                  a, shape=debug_shape,
                                  title="Raw data",
                                  filters=filters)

            if not 'baseline' in self.root.debug:
                self.createCArray(self.root.debug, 'baseline',
                                  a, shape=debug_shape,
                                  title="Baseline data",
                                  filters=filters)

            if not 'threshold_positive' in self.root.debug:
                self.createCArray(self.root.debug, 'threshold_positive',
                                  a, shape=debug_shape,
                                  title="Raw data",
                                  filters=filters)

            if not 'threshold_negative' in self.root.debug:
                self.createCArray(self.root.debug, 'threshold_negative',
                                  a, shape=debug_shape,
                                  title="Raw data",
                                  filters=filters)

    def is_debug(self):
        """
        :returns: True if the event was created with the debug keyword.
        """
        return 'debug' in self.root

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

    def to_csv(self, filename):
        ofile = open(filename, 'wb')

        writer = csv.writer(ofile, quoting=csv.QUOTE_NONNUMERIC)

        # Write header
        header = ['Start Time', 'Dwell Time', 'Blockage', 'Baseline', 'Inter Event Time', 'Number of Levels']
        writer.writerow(header)

        table = self.get_event_table()

        sample_rate = self.get_sample_rate()

        prev_event_start = 0.
        for row in table.iterrows():
            r = [row['event_start'] / sample_rate, row['event_length'] / sample_rate, row['current_blockage'],
                 row['baseline'], (row['event_start'] - prev_event_start) / sample_rate, row['n_levels']]
            writer.writerow(r)
            prev_event_start = row['event_start']


def open_file(*args, **kargs):
    """
    Opens an EventDatabase by calling tables.openFile and then
    copying the __dict__ to a new EventDatabase instance.
    
    :param kargs: Pass in the following named parameters.

        - maxEventLength: Maximum length of an event for the table. Default is 100.
        - debug: boolean -- If debug, an extra root.debug group will be created. If passing debug=True, then\
            you need to also pass the following parameters. This mode is used by\
            :py:func:`pypore.event_finder.find_events`, and only does anything if you are opening a new databse.

            - n_points: number of points in the original data.
            - n_channels: number of channels in the original data.

            And optional parameters

            - threshold_positive: boolean -- True if you need an array allocated for positive threshold.
            - threshold_negative: boolean -- True if you need an array allocated to keep negative threshold data.

    """
    f = tb.openFile(*args, **kargs)
    EventDatabase._convert_to_event_database(f)
    if 'mode' in kargs:
        mode = kargs['mode']
        if 'w' in mode or 'a' in mode:
            f.initialize_database(**kargs)
    return f
