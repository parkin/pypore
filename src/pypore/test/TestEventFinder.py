'''
Created on Aug 27, 2013

@author: parkin
'''
import unittest
from src.pypore.EventFinder import findEvents
import numpy as np
from pypore.EventFinder import _getDataRangeNew

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
    
    def test_getDataRangeAtNew(self):
        n = 100
        first = np.zeros(n)
        first[n-1] += 1.
        first[0] += 1.
        dataCache = [first, np.zeros(n)+100., np.zeros(n)+100.+60.]
        
        res = _getDataRangeNew(dataCache, 0, n)
        self.assertEqual(res.size, n)
        np.testing.assert_array_equal(res, np.zeros(n)+100.)
         
        # Test negative i to 0
        x = np.zeros(10)
        x[9] += 1.
        res = _getDataRangeNew(dataCache, -10, 0)
        np.testing.assert_array_equal(res, x)
         
        # Test negative i,n
        x = np.zeros(10)
        x[0] += 1.
        res = _getDataRangeNew(dataCache, -100, -90)
        np.testing.assert_array_equal(res, x)
         
        # Test negative i, pos n in first spot
        x = np.zeros(10)
        x[4] += 1.
        x[5:10] += 100.
        res = _getDataRangeNew(dataCache, -5, 5)
        np.testing.assert_array_equal(res, x)
         
        # Test pos i,n both in first spot
        x = np.zeros(10) + 100.
        res = _getDataRangeNew(dataCache, 60, 70)
        np.testing.assert_array_equal(res, x)
         
        # Test first and second cache overlap
        x = np.zeros(10) + 100.
        x[5:] += 60.
        res = _getDataRangeNew(dataCache, 95, 105)
        np.testing.assert_array_equal(res, x)
         
        # Test fist cache bumping up on second
        x = np.zeros(10) + 100.
        res = _getDataRangeNew(dataCache, 90, 100)
        np.testing.assert_array_equal(res, x)
         
        # Test second cache
        x = np.zeros(10) + 160.
        res = _getDataRangeNew(dataCache, 155, 165)
        np.testing.assert_array_equal(res, x)
        
        # Test neg overlap with 2 pos caches
        x = np.zeros(120)
        x[9] += 1.
        x[10:] += 100.
        x[110:] += 60. 
        res = _getDataRangeNew(dataCache, -10, 110)

    def testChimera_nonoise_1Event(self):
        eventDatabase = findEvents(filename = 'testDataFiles/chimera_nonoise_1event.log',
                                   **self.defaultParams)
        self.assertIn('Events', eventDatabase)
        events = eventDatabase['Events']
        
        self.assertEqual(len(events), 1)
        event = events[0]
        levels = event['cusum_values']
        self.assertEqual(len(levels), 1)
        level = levels[0]
        self.assertAlmostEqual(level, 0.9332, 4)
        
    def testChimera_nonoise_1Event_2Levels(self):
        eventDatabase = findEvents(filename = 'testDataFiles/chimera_nonoise_1event_2levels.log',
                                   **self.defaultParams)
        self.assertIn('Events', eventDatabase)
        events = eventDatabase['Events']
        
        self.assertEqual(len(events), 1)
        event = events[0]
        levels = event['cusum_values']
        self.assertEqual(len(levels), 2)
        level = levels[0]
        self.assertAlmostEqual(level, 0.9332, 4)
        
        level = levels[1]
        self.assertAlmostEqual(level, 0.78064, 4)
        
if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()