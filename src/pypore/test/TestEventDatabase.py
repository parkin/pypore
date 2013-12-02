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
        self.database.initializeEmptyDatabase()

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
        eventRow = self.database.getEventRow()
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
        
    def testGetEventsGroup(self):
        """
        """
        eventsGroup = self.database.getEventsGroup()
        self._testEmptyEventsGroup(eventsGroup)
        
        
if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()