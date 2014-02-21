"""
Created on Jan 28, 2014

@author: `@parkin1 <https://github.com/parkin1>`_
"""

import tables as tb


class DataFile(tb.file.File):
    """
    PyTables HDF5 database storing raw data.
    Inherits from tables.file.File, so you can interact with this
    just as you would a PyTables File object. However, this contains
    some extra convenience methods for storing/reading data. Note that 
    DataFile allows you to interact
    with this PyTables file in the usual PyTables file manner, so you
    can potentially mangle the data from the original DataFile
    format.
    
    Automatically adds matrix
    /data
    
    Must be instantiated by calling dataFile's
    
    >>> import pypore.dataFile as dF
    >>> database = dF.openFile('test.h5',mode='w')
    >>> database.close()
    >>> os.remove('test.h5')
    """

    def clean_database(self):
        """
        Removes /events and then reinitializes the /events group. Note
        that any references to any table/matrix in this group will
        be broken and need to be refreshed.
        
        >>> h5 = openFile('test.h5',mode='a')
        >>> table = h5.getEventTable()
        >>> h5.clean_database() // table is now refers to deleted table
        >>> table = h5.getEventTable() // table now refers to live table
        """
        # remove the events group
        self.root._f_remove(recursive=True)

        self.initializeDatabase()

    @classmethod
    def convertToEventDatabase(cls, tables_object):
        """
        Converts a PyTables object's __class__ field to DataFile so
        you can use the object as an DataFile object.
        """
        tables_object.__class__ = DataFile

    def getDataLength(self):
        """
        Returns the number of rows in the data matrix.
        Note this will flush the table so the data is correct.
        """
        self.root.data.flush()
        return self.root.data.nrows

    def getSampleRate(self):
        """
        Gets the sample rate at root.events.eventTable.attrs.sampleRate
        """
        return self.root.attrs.sampleRate

    def initializeDatabase(self, *args, **kargs):
        """
        Initializes the EventDatabase.  Adds a group 'events' with
        table 'eventsTable' and matrices 'rawData', 'levels', and 'levelLengths'.
        
        Args:
        Kargs:
            -maxEventLength: Maximum number of datapoints for an event to be added.
        """

        filters = tb.Filters(complib='blosc', complevel=4)
        shape = (kargs['nPoints'],)
        a = tb.FloatAtom()
        if not 'data' in self.root:
            self.createCArray(self.root, 'data', a, shape=shape, title='Data', filters=filters)

        # set the attributes
        self.root.data.attrs.sampleRate = kargs['sampleRate']


def openFile(*args, **kargs):
    """
    Opens an EventDatabase by calling tables.openFile and then
    copying the __dict__ to a new EventDatabase instance.
    
    Kargs:
        nPoints: Number of points that should be in the array.
        sampleRate: sample rate of the data.
    """
    f = tb.openFile(*args, **kargs)
    DataFile.convertToEventDatabase(f)
    if 'mode' in kargs:
        mode = kargs['mode']
        if 'w' in mode or 'a' in mode:
            f.initializeDatabase(*args, **kargs)
    return f
