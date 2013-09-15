'''
Created on Aug 27, 2013

@author: parkin
'''
import unittest
from pypore import cythonsetup
from pypore.EventFinder import findEvents
from pypore.EventFinder import _getDataRangeTestWrapper
import numpy as np
import os
import tables as tb

class TestEventFinder(unittest.TestCase):
    
    def setUp(self):
        self.defaultParams = { 'min_event_length': 10.,
                                   'max_event_length': 10000.,
                                   'threshold_direction': 'Negative',
                                   'filter_parameter': 0.93,
                                   'threshold_type': 'Noise Based',
                                   'start_stddev': 5.,
                                   'end_stddev': 1.}

    def tearDown(self):
        pass
    
    def test_getDataRangeTestWrapperAtNew(self):
        n = 100
        first = np.zeros(n)
        first[n-1] += 1.
        first[0] += 1.
        dataCache = [first, np.zeros(n)+100., np.zeros(n)+100.+60., np.zeros(n)+200.]
        
        res = _getDataRangeTestWrapper(dataCache, 0, n)
        self.assertEqual(res.size, n)
        np.testing.assert_array_equal(res, np.zeros(n)+100.)
         
        # Test negative i to 0
        x = np.zeros(10)
        x[9] += 1.
        res = _getDataRangeTestWrapper(dataCache, -10, 0)
        np.testing.assert_array_equal(res, x)
         
        # Test negative i,n
        x = np.zeros(10)
        x[0] += 1.
        res = _getDataRangeTestWrapper(dataCache, -100, -90)
        np.testing.assert_array_equal(res, x)
         
        # Test negative i, pos n in first spot
        x = np.zeros(10)
        x[4] += 1.
        x[5:10] += 100.
        res = _getDataRangeTestWrapper(dataCache, -5, 5)
        np.testing.assert_array_equal(res, x)
         
        # Test pos i,n both in first spot
        x = np.zeros(10) + 100.
        res = _getDataRangeTestWrapper(dataCache, 60, 70)
        np.testing.assert_array_equal(res, x)
         
        # Test first and second cache overlap
        x = np.zeros(10) + 100.
        x[5:] += 60.
        res = _getDataRangeTestWrapper(dataCache, 95, 105)
        np.testing.assert_array_equal(res, x)
         
        # Test fist cache bumping up on second
        x = np.zeros(10) + 100.
        res = _getDataRangeTestWrapper(dataCache, 90, 100)
        np.testing.assert_array_equal(res, x)
         
        # Test second cache
        x = np.zeros(10) + 160.
        res = _getDataRangeTestWrapper(dataCache, 155, 165)
        np.testing.assert_array_equal(res, x)
        
        # Test neg overlap with 2 pos caches
        x = np.zeros(120)
        x[9] += 1.
        x[10:] += 100.
        x[110:] += 60. 
        res = _getDataRangeTestWrapper(dataCache, -10, 110)
        
        # Test neg overlap with 3 pos caches
        x = np.zeros(220)
        x[9] += 1.
        x[10:] += 100.
        x[110:] += 60.
        x[210:] += 40.
        res = _getDataRangeTestWrapper(dataCache, -10, 210)
        
    def testSavingFiles(self):
        filename = os.path.dirname(os.path.realpath(__file__))
        filename = os.path.join(filename, 'testDataFiles','chimera_1event.log')
        eventDatabase = findEvents(filename = filename)
        
        self.assertTrue(os.path.isfile(eventDatabase))
        
        h5file = tb.openFile(eventDatabase, mode='r')
        
        self.assertTrue(h5file.isopen)
        
        h5file.close()
        
        #delete the newly created event file
        os.remove(eventDatabase)

    def testChimera_nonoise_1Event(self):
        filename = os.path.dirname(os.path.realpath(__file__))
        filename = os.path.join(filename, 'testDataFiles','chimera_nonoise_1event.log')
        eventDatabase = findEvents(filename = filename,
                                   **self.defaultParams)
        
        h5file = tb.openFile(eventDatabase, mode='r')
        
        events = h5file.root.events

        # check event table correct length        
        eventTable = events.eventTable
        self.assertTrue(eventTable.nrows, 1)
        
        # check raw data array correct length
        rawDataMatrix = events.rawData
        self.assertEqual(rawDataMatrix.nrows, 1)
        rawData = rawDataMatrix[0]
        rawPointsPerSide = eventTable[0]['rawPointsPerSide']
        eventLength = eventTable[0]['eventLength']
        self.assertEqual(rawData.size, eventLength + 2*rawPointsPerSide)
        
        # Make sure only 1 event with 1 level
        levelsMatrix = events.levels
        self.assertEqual(levelsMatrix.nrows, 1)
        levels = levelsMatrix[0]
        self.assertEqual(levels.size, 1)
        self.assertAlmostEqual(levels[0], 0.9332, 4)
        
        # Check 1 event with 1 level -> 2 indices
        indicesMatrix = events.levelIndices
        self.assertEqual(indicesMatrix.nrows, 1)
        indices = indicesMatrix[0]
        self.assertEqual(indices.size, 2)
        self.assertEqual(indices[0], 2000)
        self.assertEqual(indices[1], 3000)
        
        h5file.close()
        
        #delete the newly created event file
        os.remove(eventDatabase)
        
    def testChimera_nonoise_1Event_2Levels(self):
        filename = os.path.dirname(os.path.realpath(__file__))
        filename = os.path.join(filename, 'testDataFiles','chimera_nonoise_1event_2levels.log')
        eventDatabase = findEvents(filename = filename,
                                   **self.defaultParams)
        
        h5file = tb.openFile(eventDatabase, mode='r')
        
        events = h5file.root.events
        
        eventTable = events.eventTable
        self.assertTrue(eventTable.nrows, 1)
        
        # check raw data array correct length
        rawDataMatrix = events.rawData
        self.assertEqual(rawDataMatrix.nrows, 1)
        rawData = rawDataMatrix[0]
        rawPointsPerSide = eventTable[0]['rawPointsPerSide']
        eventLength = eventTable[0]['eventLength']
        self.assertEqual(rawData.size, eventLength + 2*rawPointsPerSide)
        
        levelsMatrix = events.levels
        self.assertEqual(levelsMatrix.nrows, 1)
        levels = levelsMatrix[0]
        self.assertEqual(levels.size, 2)
        self.assertAlmostEqual(levels[0], 0.9332, 4)
        self.assertAlmostEqual(levels[1], 0.78064, 4)
        
        indicesMatrix = events.levelIndices
        self.assertEqual(indicesMatrix.nrows, 1)
        indices = indicesMatrix[0]
        self.assertEqual(indices.size, 3)
        self.assertEqual(indices[0], 2000)
        self.assertEqual(indices[1], 2750)
        self.assertEqual(indices[2], 3500)
        
        h5file.close()
        
        #delete the newly created event file
        os.remove(eventDatabase)
        
    def testChimera_nonoise_2events_1levels(self):
        filename = os.path.dirname(os.path.realpath(__file__))
        filename = os.path.join(filename, 'testDataFiles','chimera_nonoise_2events_1levels.log')
        eventDatabase = findEvents(filename = filename,
                                   **self.defaultParams)
        
        h5file = tb.openFile(eventDatabase, mode='r')
        
        events = h5file.root.events

        # check event table correct length        
        eventTable = events.eventTable
        self.assertTrue(eventTable.nrows, 2)
        
        # check raw data array correct length
        rawDataMatrix = events.rawData
        self.assertEqual(rawDataMatrix.nrows, 2)
        rawData = rawDataMatrix[0]
        rawPointsPerSide = eventTable[0]['rawPointsPerSide']
        eventLength = eventTable[0]['eventLength']
        self.assertEqual(rawData.size, eventLength + 2*rawPointsPerSide)
        # second event
        rawData = rawDataMatrix[1]
        rawPointsPerSide = eventTable[1]['rawPointsPerSide']
        eventLength = eventTable[1]['eventLength']
        self.assertEqual(rawData.size, eventLength + 2*rawPointsPerSide)
        
        # Make sure only 2 events with 1 level each
        levelsMatrix = events.levels
        self.assertEqual(levelsMatrix.nrows, 2)
        levels = levelsMatrix[0]
        self.assertEqual(levels.size, 1)
        self.assertAlmostEqual(levels[0], 0.9332, 4)
        # event 2
        levels = levelsMatrix[1]
        self.assertEqual(levels.size, 1)
        self.assertAlmostEqual(levels[0], 0.9332, 4)
        
        # Check 1 event with 1 level -> 2 indices
        indicesMatrix = events.levelIndices
        self.assertEqual(indicesMatrix.nrows, 2)
        indices = indicesMatrix[0]
        self.assertEqual(indices.size, 2)
        self.assertEqual(indices[0], 2000)
        self.assertEqual(indices[1], 3000)
        # event
        indices = indicesMatrix[1]
        self.assertEqual(indices.size, 2)
        self.assertEqual(indices[0], 4500)
        self.assertEqual(indices[1], 5500)
        
        h5file.close()
        
        #delete the newly created event file
        os.remove(eventDatabase)
        
if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()