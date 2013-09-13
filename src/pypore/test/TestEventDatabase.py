'''
Created on Sep 13, 2013

@author: parkin
'''
import unittest, os
import pypore.cythonsetup
import pypore.eventDatabase as ed


class TestEventDatabase(unittest.TestCase):


    def setUp(self):
        pass


    def tearDown(self):
        pass


    def testInitializeEventsDatabase(self):
        filename = 'testInitializeDatabase.h5'
        
        # Get an open file descriptor
        fileh = ed.initializeEventsDatabase(filename)
        
        # Check that only the root group and event group exist
        names = []
        for group in fileh.walkGroups():
            names.append(group._v_name)
        self.assertEqual(len(names), 2, "Incorrect number of initial groups in event database.")
        self.assertIn('/', names, 'file missing root group')
        self.assertIn('events', names, "file missing event group.")
        
        # Check the events group has the correct nodes
        # Should be events, eventTable, eventData, rawData
        names = []
        for node in fileh.walkNodes(fileh.root.events):
            names.append(node._v_name)
        namesShouldBe = ['events', 'eventTable', 'rawData', 'levels', 'levelIndices']
        self.assertEqual(len(names), len(namesShouldBe))
        self.assertEqual(sorted(names), sorted(namesShouldBe)) # i don't care what order these lists are
        
        # Assert table, vlarrays are empty
        self.assertEqual(fileh.root.events.eventTable.nrows, 0)
        self.assertEqual(fileh.root.events.rawData.nrows, 0)
        self.assertEqual(fileh.root.events.levels.nrows, 0)
        self.assertEqual(fileh.root.events.levelIndices.nrows, 0)
        
        # Check the eventTable columns are correct and in correct order
        columnNames = ['arrayRow', 'eventStart', 'eventLength', 'rawPointsPerSide', 'baseline', 'currentBlockage', 'Area', 'Filename']
        self.assertEqual(fileh.root.events.eventTable.colnames, columnNames)
        
        os.remove(filename)
        

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()