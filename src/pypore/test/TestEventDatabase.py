'''
Created on Sep 13, 2013

@author: parkin
'''
import unittest, os
import numpy as np
# import pypore.cythonsetup
import pypore.eventDatabase as ed


class TestEventDatabase(unittest.TestCase):

    def setUp(self):
        self.filename = 'testInitializeDatabase.h5'
        self.maxEventSteps = 100
        self.database = ed.openFile(self.filename, mode='w', maxEventSteps = self.maxEventSteps)

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
        
    def testGetEventsGroup(self):
        """
        """
        eventsGroup = self.database.getEventsGroup()
        self._testEmptyEventsGroup(eventsGroup)
        
        
if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()