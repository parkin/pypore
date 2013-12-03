'''
Created on Sep 13, 2013

@author: parkin
'''
import unittest, os
import numpy as np
import numpy.testing as npt
# import pypore.cythonsetup
import pypore.eventDatabase as ed

class TestEventDatabase(unittest.TestCase):

    def setUp(self):
        self.filename = 'testEventDatabase_938247283278128.h5'
        self.maxEventLength = 100
        self.database = ed.openFile(self.filename, mode='w', maxEventLength = self.maxEventLength)

    def tearDown(self):
        self.database.close()
        os.remove(self.filename)
        
    def _testInitialRoot(self, fileh = None):
        """
        Check that only the root group and event group exist
        """
        if fileh == None:
            fileh = self.database
        
        names = []
        for group in fileh.walkGroups():
            names.append(group._v_name)
        self.assertEqual(len(names), 2, "Incorrect number of initial groups in event database.")
        self.assertIn('/', names, 'file missing root group')
        self.assertIn('events', names, "file missing event group.")
        
    def _testEmptyEventsGroup(self, eventsGroup = None):
        """
        Checks that the events group has the correct (and empty) tables/arrays
        """
        if eventsGroup == None:
            eventsGroup = self.database.root.events
        
        # Check the events group has the correct nodes
        # Should be events, eventTable, eventData, rawData
        names = []
        for node in self.database.walkNodes(eventsGroup):
            names.append(node._v_name)
        namesShouldBe = ['events', 'eventTable', 'rawData', 'levels', 'levelLengths']
        self.assertEqual(len(names), len(namesShouldBe))
        self.assertEqual(sorted(names), sorted(namesShouldBe)) # i don't care what order these lists are
        
        # Assert table, vlarrays are empty
        self.assertEqual(eventsGroup.eventTable.nrows, 0)
        self.assertEqual(eventsGroup.rawData.nrows, 0)
        self.assertEqual(eventsGroup.levels.nrows, 0)
        self.assertEqual(eventsGroup.levelLengths.nrows, 0)
        
        # Check the eventTable columns are correct and in correct order
        columnNames = ['arrayRow', 'eventStart', 'eventLength', 'nLevels', 'rawPointsPerSide', 'baseline', 'currentBlockage', 'area']
        self.assertEqual(eventsGroup.eventTable.colnames, columnNames)
        
    def testCleanDatabase(self):
        """
        Tests that cleanDatabase removing eventsTable, rawData, levels, and levelData
        and initializing with empty table/matrices.
        """
        # put stuff in rawData
        rawData = np.ones((1,self.database.maxEventLength))
        self.database.appendEvent(1,2,3,4,5,6,7,8, rawData, rawData, rawData)
        
        # clean the database
        self.database.cleanDatabase()
        
        # check that the database has all the empty table/matrices
        self._testEmptyEventsGroup(self.database.root.events)

    def testAppendEvent(self):
        """
        Tests appendEvent
        
        arrayRow, eventStart, eventLength, nLevels, rawPointsPerSide,\
                    baseline, currentBlockage, area, rawData = None, levels = None, levelLengths = None
        """
        table = self.database.getEventTable()
        
        # add an event
        self.database.appendEvent(1,2,3,4,5,6,7,8)
        self.database.flush()
        
        # Check eventTable for one correct row.
        self.assertEqual(self.database.getEventTable().nrows, 1)
        self.assertEqual(table[0]['arrayRow'], 1)
        self.assertEqual(table[0]['eventStart'], 2)
        self.assertEqual(table[0]['eventLength'], 3)
        self.assertEqual(table[0]['nLevels'], 4)
        self.assertEqual(table[0]['rawPointsPerSide'], 5)
        self.assertEqual(table[0]['baseline'], 6)
        self.assertEqual(table[0]['currentBlockage'], 7)
        self.assertEqual(table[0]['area'], 8)
        
        # Check for nothing in rawData, levels, levelLengths
        self.assertEqual(self.database.root.events.rawData.nrows, 0)
        self.assertEqual(self.database.root.events.levels.nrows, 0)
        self.assertEqual(self.database.root.events.levelLengths.nrows, 0)
        
        # add another event, this time with rawData
        rawData = np.ones((1,self.database.maxEventLength))
        self.database.appendEvent(10,20,30,40,50,60,70,80, rawData)
        self.database.flush()
        
        # Check eventTable for two correct rows.
        self.assertEqual(self.database.getEventTable().nrows, 2)
        self.assertEqual(table[1]['arrayRow'], 10)
        self.assertEqual(table[1]['eventStart'], 20)
        self.assertEqual(table[1]['eventLength'], 30)
        self.assertEqual(table[1]['nLevels'], 40)
        self.assertEqual(table[1]['rawPointsPerSide'], 50)
        self.assertEqual(table[1]['baseline'], 60)
        self.assertEqual(table[1]['currentBlockage'], 70)
        self.assertEqual(table[1]['area'], 80)
        
        # Check for 1 row in rawData and nothing in levels, levelLengths
        self.assertEqual(self.database.root.events.rawData.nrows, 1)
        self.assertEqual(self.database.root.events.levels.nrows, 0)
        self.assertEqual(self.database.root.events.levelLengths.nrows, 0)
        npt.assert_array_equal(self.database.root.events.rawData[:], rawData)
        
    def testDeleteEvent(self):
        """
        Tests deleting single events from eventTable.
        """
        table = self.database.getEventTable()
        
        # Test deleting all events in database does nothing
        self.database.appendEvent(1,2,3,4,5,6,7,8)
        self.database.removeEvent(0)
        self.assertEqual(self.database.getEventCount(), 1)
        
        # Test deleting out of range does nothing
        self.database.removeEvent(-1)
        self.assertEqual(self.database.getEventCount(), 1)
        self.database.removeEvent(1)
        self.assertEqual(self.database.getEventCount(), 1)
        self.database.removeEvent(10)
        self.assertEqual(self.database.getEventCount(), 1)
        
        # Test deleting first event in database
        for i in xrange(1,10):
            self.database.appendEvent(i+1,i+2,i+3,i+4,i+5,i+6,i+7,i+8)
        self.assertEqual(self.database.getEventCount(), 10)
        self.assertEqual(table[0]['arrayRow'], 1)
        self.database.removeEvent(0)
        self.assertEqual(self.database.getEventCount(), 9)
        self.assertEqual(table[0]['arrayRow'], 2)
        
        # Test deleting last event in database
        self.assertEqual(table[8]['arrayRow'], 10)
        self.database.removeEvent(8)
        self.assertEqual(self.database.getEventCount(), 8)
        self.assertEqual(table[7]['arrayRow'], 9)
        
        # Test deleting second to last row
        self.assertEqual(table[6]['arrayRow'], 8)
        self.database.removeEvent(6)
        self.assertEqual(self.database.getEventCount(), 7)
        self.assertEqual(table[6]['arrayRow'], 9)
        self.assertEqual(table[5]['arrayRow'], 7)
        
    def testDeleteEvents(self):
        """
        Test removing ranges of events from event table.
        """
        table = self.database.getEventTable()
        
        # Test deleting all events in database does nothing
        self.database.appendEvent(1,2,3,4,5,6,7,8)
        self.database.removeEvents(0,1)
        self.assertEqual(self.database.getEventCount(), 1)
        
        # Add to total of 10 events
        for i in xrange(1,10):
            self.database.appendEvent(i+1,i+2,i+3,i+4,i+5,i+6,i+7,i+8)
            
        # Test deleting all events does nothing
        self.database.removeEvents(0,10)
        self.assertEqual(self.database.getEventCount(), 10)
        
        # Test for i out of range
        self.database.removeEvents(-1,5)
        self.assertEqual(self.database.getEventCount(), 10)
        self.database.removeEvents(-9999,5)
        self.assertEqual(self.database.getEventCount(), 10)
        self.database.removeEvents(5,5)
        self.assertEqual(self.database.getEventCount(), 10)
        self.database.removeEvents(6,5)
        self.assertEqual(self.database.getEventCount(), 10)
        self.database.removeEvents(50,5)
        self.assertEqual(self.database.getEventCount(), 10)
        self.database.removeEvents(50,51)
        self.assertEqual(self.database.getEventCount(), 10)
        
        # Test for j out of range
        self.database.removeEvents(5,5)
        self.assertEqual(self.database.getEventCount(), 10)
        self.database.removeEvents(5,4)
        self.assertEqual(self.database.getEventCount(), 10)
        self.database.removeEvents(5,-1)
        self.assertEqual(self.database.getEventCount(), 10)
        self.database.removeEvents(5,-100)
        self.assertEqual(self.database.getEventCount(), 10)
        self.database.removeEvents(5,11)
        self.assertEqual(self.database.getEventCount(), 10)
        self.database.removeEvents(5,100)
        self.assertEqual(self.database.getEventCount(), 10)
        
        # Test removing first event
        self.database.removeEvents(0,1)
        self.assertEqual(self.database.getEventCount(), 9)
        self.assertEqual(table[0]['arrayRow'], 2)
        
        # Test removing final event
        self.database.removeEvents(8,9)
        self.assertEqual(self.database.getEventCount(), 8)
        self.assertEqual(table[7]['arrayRow'], 9)
        
        # Test removing range
        self.database.removeEvents(1,7)
        self.assertEqual(self.database.getEventCount(), 2)
        self.assertEqual(table[0]['arrayRow'], 2)
        self.assertEqual(table[1]['arrayRow'], 9)
    
    def testInitializeEventsDatabase(self):
        self._testInitialRoot(self.database)
        
        self._testEmptyEventsGroup()
        
        # Check is in write mode
        self.database.root.events.rawData.append(np.zeros((1,100)))
        self.database.flush()
        
    def testOpenExistingEmptyDatabase(self):
        """
        Tests opening an existing h5 file with an empty 
        EventsDatabase structure.
        """
        self.database.close()
        
        self.database = ed.openFile(self.filename)
        
        self._testInitialRoot(self.database)
        
        self._testEmptyEventsGroup()
        
    def testOpenExistingFullDatabase(self):
        """
        Tests opening an existing h5 file with events in
        the EventDatabase structure.
        """
        # Add to the rawData matrix
        rawData = np.zeros((2,self.maxEventLength))
        rawData[1][:] += 1
        self.database.appendRawData(rawData)
        
        # Add to the levels matrix
        levels = rawData + 1
        self.database.appendLevels(levels)
        
        # Add to the levelLengths matrix
        levelLengths = rawData + 2
        self.database.appendLevelLengths(levelLengths)
        
        # Add to the event table
        eventRow = self.database.getEventTableRow()
        eventRow['arrayRow'] = 1
        eventRow['eventStart'] = 2
        eventRow['eventLength'] = 3
        eventRow['nLevels'] = 4
        eventRow['rawPointsPerSide'] = 5
        eventRow['baseline'] = 6
        eventRow['currentBlockage'] = 7
        eventRow['area'] = 8
        eventRow.append()
        
        # Close the file
        self.database.flush()
        self.database.close()
        
        # Open the existing file
        self.database = ed.openFile(self.filename, mode='r')
        
        # Check the rawData matrix
        npt.assert_array_equal(rawData, self.database.root.events.rawData[:])
        
        # Check the levels matrix
        npt.assert_array_equal(levels, self.database.root.events.levels[:])
        
        # Check the levelLengths matrix
        npt.assert_array_equal(levelLengths, self.database.root.events.levelLengths[:])
        
        # Check the eventTable
        row = self.database.root.events.eventTable[0]
        self.assertEqual(row['arrayRow'], 1)
        self.assertEqual(row['area'], 8)
        
    def testInitializeDatabaseWithExistingNodes(self):
        """
        Test that calling initialize database with existing nodes does not
        throw an error (ie existing nodes ignored).
        """
        self.assertIn('eventTable', self.database.root.events)
        self.assertIn('rawData', self.database.root.events)
        
        raw = np.ones((1,self.maxEventLength))
        self.database.appendRawData(raw)
        
        # test to see if error thrown
        self.database.initializeDatabase()
        
        # check that rawData is still the same
        npt.assert_array_equal(raw, self.database.root.events.rawData[:])
        
    def testGetEventsGroup(self):
        """
        Test the getter for /events
        """
        eventsGroup = self.database.getEventsGroup()
        self._testEmptyEventsGroup(eventsGroup)
        
        self.assertIn('rawData', eventsGroup)
        self.assertIn('levels', eventsGroup)
        self.assertIn('levelLengths', eventsGroup)

    def testGetEventCount(self):
        """
        Tests that getEventCount returns the correct value, even
        after events are added/deleted.
        """
        self.assertEqual(self.database.getEventCount(), 0)
        
        for i in xrange(100):
            self.database.appendEvent(i+1,i+2,i+3,i+4,i+5,i+6,i+7,i+8)
            self.assertEqual(self.database.getEventCount(), i+1)
            
        for i in xrange(50):
            self.database.removeEvent(0)
            self.assertEqual(self.database.getEventCount(), 99-i)
            
    def testGetEventDataAt(self):
        """
        Tests getting only the event points from rawData
        """
        raw = np.linspace(0.0, 100.0, self.maxEventLength).reshape((1,100))
        
        self.database.appendEvent(0,2,3,4,5,6,7,8,raw) # eventLength=3, rawPointsPerSide=5
        
        row = self.database.getEventRow(0)
        eventLength = row['eventLength']
        rawPointsPerSide = row['rawPointsPerSide']
        
        self.assertEqual(eventLength, 3)
        self.assertEqual(rawPointsPerSide, 5)
        npt.assert_array_equal(self.database.getEventDataAt(0), raw[0][rawPointsPerSide:eventLength+rawPointsPerSide])
        
    def testGetEventRow(self):
        """
        Test that getEventRow returns correct row.
        """
        for i in xrange(10):
            self.database.appendEvent(i+1,i+2,i+3,i+4,i+5,i+6,i+7,i+8)
            
        row = self.database.getEventRow(1)
        self.assertEqual(row['arrayRow'], 2)
        
    def testGetLevelLengthsAt(self):
        """
        Tests that getLevelLengthsAt returns a numpy matrix of the 
        levelLengths corresponding to the event
        in row 'i' of eventTable.
        """
        levelLengths = np.array(range(self.maxEventLength)).reshape((1,self.maxEventLength))
        
        self.database.appendEvent(0,2,3,4,5,6,7,8,levelLengths=levelLengths) # eventLength=3, rawPointsPerSide=5
        
        row = self.database.getEventRow(0)
        nLevels = row['nLevels']
        
        self.assertEqual(nLevels, 4)
        npt.assert_array_equal(self.database.getLevelLengthsAt(0), levelLengths[0][:nLevels])
        
    def testGetLevelsAt(self):
        """
        Tests that getLevelsAt returns a numpy matrix of the levels corresponding to the event
        in row 'i' of eventTable.
        """
        levels = np.linspace(0.0, 100.0, self.maxEventLength).reshape((1,self.maxEventLength))
        
        self.database.appendEvent(0,2,3,4,5,6,7,8,levels=levels) # eventLength=3, rawPointsPerSide=5
        
        row = self.database.getEventRow(0)
        nLevels = row['nLevels']
        
        self.assertEqual(nLevels, 4)
        npt.assert_array_equal(self.database.getLevelsAt(0), levels[0][:nLevels])
        
    def testGetRawDataAt(self):
        """
        Tests that getRawDataAt returns correctly sized(eventLength + 2*rawPointsPerSide)
        numpy array with correct data.
        """
        raw = np.linspace(0.0, 100.0, self.maxEventLength).reshape((1,self.maxEventLength))
        
        self.database.appendEvent(0,2,3,4,5,6,7,8,raw) # eventLength=3, rawPointsPerSide=5
        
        row = self.database.getEventRow(0)
        eventLength = row['eventLength']
        rawPointsPerSide = row['rawPointsPerSide']
        
        self.assertEqual(eventLength, 3)
        self.assertEqual(rawPointsPerSide, 5)
        npt.assert_array_equal(self.database.getRawDataAt(0), raw[0][:eventLength+2*rawPointsPerSide])
        
    def testGetSampleRate(self):
        """
        Test that getSampleRate returns root.events.eventTable.attrs.sampleRate
        """
        rate = 13928.99
        self.database.root.events.eventTable.attrs.sampleRate = rate
        
        self.assertEqual(self.database.getSampleRate(), rate)
        
if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()