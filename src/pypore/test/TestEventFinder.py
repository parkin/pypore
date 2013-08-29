'''
Created on Aug 27, 2013

@author: parkin
'''
import unittest
from pypore.EventFinder import findEvents
from pypore.EventFinder import _getDataRange
import numpy as np
import os

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
        
        res = _getDataRange(dataCache, 0, n)
        self.assertEqual(res.size, n)
        np.testing.assert_array_equal(res, np.zeros(n)+100.)
         
        # Test negative i to 0
        x = np.zeros(10)
        x[9] += 1.
        res = _getDataRange(dataCache, -10, 0)
        np.testing.assert_array_equal(res, x)
         
        # Test negative i,n
        x = np.zeros(10)
        x[0] += 1.
        res = _getDataRange(dataCache, -100, -90)
        np.testing.assert_array_equal(res, x)
         
        # Test negative i, pos n in first spot
        x = np.zeros(10)
        x[4] += 1.
        x[5:10] += 100.
        res = _getDataRange(dataCache, -5, 5)
        np.testing.assert_array_equal(res, x)
         
        # Test pos i,n both in first spot
        x = np.zeros(10) + 100.
        res = _getDataRange(dataCache, 60, 70)
        np.testing.assert_array_equal(res, x)
         
        # Test first and second cache overlap
        x = np.zeros(10) + 100.
        x[5:] += 60.
        res = _getDataRange(dataCache, 95, 105)
        np.testing.assert_array_equal(res, x)
         
        # Test fist cache bumping up on second
        x = np.zeros(10) + 100.
        res = _getDataRange(dataCache, 90, 100)
        np.testing.assert_array_equal(res, x)
         
        # Test second cache
        x = np.zeros(10) + 160.
        res = _getDataRange(dataCache, 155, 165)
        np.testing.assert_array_equal(res, x)
        
        # Test neg overlap with 2 pos caches
        x = np.zeros(120)
        x[9] += 1.
        x[10:] += 100.
        x[110:] += 60. 
        res = _getDataRange(dataCache, -10, 110)
        
    def testSavingFiles(self):
        filename = os.path.dirname(os.path.realpath(__file__))
        filename = os.path.join(filename, 'testDataFiles','chimera_1event.log')
        eventDatabase = findEvents(filename = filename)
        
        dat_filename = eventDatabase['database_filename']
        self.assertTrue(os.path.isfile(dat_filename))
        
        database = np.load(dat_filename).item()
        
        np.testing.assert_equal(eventDatabase, database)
        
        #delete the newly created event file
        os.remove(eventDatabase['database_filename'])

    def testChimera_nonoise_1Event(self):
        filename = os.path.dirname(os.path.realpath(__file__))
        filename = os.path.join(filename, 'testDataFiles','chimera_nonoise_1event.log')
        eventDatabase = findEvents(filename = filename,
                                   **self.defaultParams)
        self.assertIn('Events', eventDatabase)
        events = eventDatabase['Events']
        
        self.assertEqual(len(events), 1)
        event = events[0]
        levels = event['cusum_values']
        self.assertEqual(len(levels), 1)
        level = levels[0]
        self.assertAlmostEqual(level, 0.9332, 4)
        
        indexes = event['cusum_indexes']
        self.assertEqual(len(indexes), 2)
        self.assertEqual(indexes[0], 2000)
        self.assertEqual(indexes[1], 3000)
        
        #delete the newly created event file
        os.remove(eventDatabase['database_filename'])
        
    def testChimera_nonoise_1Event_2Levels(self):
        filename = os.path.dirname(os.path.realpath(__file__))
        filename = os.path.join(filename, 'testDataFiles','chimera_nonoise_1event_2levels.log')
        eventDatabase = findEvents(filename = filename,
                                   **self.defaultParams)
        self.assertIn('Events', eventDatabase)
        events = eventDatabase['Events']
         
        self.assertEqual(len(events), 1)
        event = events[0]
        levels = event['cusum_values']
        indexes = event['cusum_indexes']
        self.assertEqual(len(levels), 2)
        self.assertEqual(len(indexes), 2+1)
         
        level = levels[0]
        self.assertAlmostEqual(level, 0.9332, 4)
        self.assertEqual(indexes[0], 2000)
         
        self.assertEqual(indexes[1], 2750)
        level = levels[1]
        self.assertAlmostEqual(level, 0.78064, 4)
        self.assertEqual(indexes[2], 3500)
        
        #delete the newly created event file
        os.remove(eventDatabase['database_filename'])
        
    def testChimera_nonoise_2events_1levels(self):
        filename = os.path.dirname(os.path.realpath(__file__))
        filename = os.path.join(filename, 'testDataFiles','chimera_nonoise_2events_1levels.log')
        eventDatabase = findEvents(filename = filename,
                                   **self.defaultParams)
        
        events = eventDatabase['Events']
        self.assertEqual(len(events), 2)

        # First event stuff
        event = events[0]
        levels = event['cusum_values']
        indexes = event['cusum_indexes']
        self.assertEqual(len(levels), 1)
        self.assertEqual(len(indexes), 2)
        level = levels[0]
        self.assertAlmostEqual(level, 0.9332, 4)
        self.assertEqual(indexes[0], 2000)
        self.assertEqual(indexes[1], 3000)
        
        # Second event stuff
        event = events[1]
        levels = event['cusum_values']
        indexes = event['cusum_indexes']
        self.assertEqual(len(levels), 1)
        self.assertEqual(len(indexes), 2)
        level = levels[0]
        self.assertAlmostEqual(level, 0.9332, 4)
        self.assertEqual(indexes[0], 4500)
        self.assertEqual(indexes[1], 5500)
        
        #delete the newly created event file
        os.remove(eventDatabase['database_filename'])
        
if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()