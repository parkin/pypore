"""
Tests for eventFinder.pyx

@author: `@parkin1`_
"""
import unittest
from pypore import cythonsetup
from pypore.eventFinder import findEvents
from pypore.eventFinder import _getDataRangeTestWrapper
import numpy as np
import os
import pypore.eventDatabase as eD


class TestEventFinder(unittest.TestCase):
    
    def setUp(self):
        self.default_params = {'min_event_length': 10.,
                                   'max_event_length': 10000.,
                                   'threshold_direction': 'Negative',
                                   'filter_parameter': 0.93,
                                   'threshold_type': 'Noise Based',
                                   'start_stddev': 5.,
                                   'end_stddev': 1.}

    def tearDown(self):
        pass
    
    def test_get_data_range_test_wrapper_at_new(self):
        n = 100
        first = np.zeros(n)
        first[n - 1] += 1.
        first[0] += 1.
        data_cache = [first, np.zeros(n) + 100., np.zeros(n) + 100. + 60., np.zeros(n) + 200.]
        
        res = _getDataRangeTestWrapper(data_cache, 0, n)
        self.assertEqual(res.size, n)
        np.testing.assert_array_equal(res, np.zeros(n) + 100.)
         
        # Test negative i to 0
        x = np.zeros(10)
        x[9] += 1.
        res = _getDataRangeTestWrapper(data_cache, -10, 0)
        np.testing.assert_array_equal(res, x)
         
        # Test negative i,n
        x = np.zeros(10)
        x[0] += 1.
        res = _getDataRangeTestWrapper(data_cache, -100, -90)
        np.testing.assert_array_equal(res, x)
         
        # Test negative i, pos n in first spot
        x = np.zeros(10)
        x[4] += 1.
        x[5:10] += 100.
        res = _getDataRangeTestWrapper(data_cache, -5, 5)
        np.testing.assert_array_equal(res, x)
         
        # Test pos i,n both in first spot
        x = np.zeros(10) + 100.
        res = _getDataRangeTestWrapper(data_cache, 60, 70)
        np.testing.assert_array_equal(res, x)
         
        # Test first and second cache overlap
        x = np.zeros(10) + 100.
        x[5:] += 60.
        res = _getDataRangeTestWrapper(data_cache, 95, 105)
        np.testing.assert_array_equal(res, x)
         
        # Test fist cache bumping up on second
        x = np.zeros(10) + 100.
        res = _getDataRangeTestWrapper(data_cache, 90, 100)
        np.testing.assert_array_equal(res, x)
         
        # Test second cache
        x = np.zeros(10) + 160.
        res = _getDataRangeTestWrapper(data_cache, 155, 165)
        np.testing.assert_array_equal(res, x)
        
        # Test neg overlap with 2 pos caches
        x = np.zeros(120)
        x[9] += 1.
        x[10:] += 100.
        x[110:] += 60. 
        res = _getDataRangeTestWrapper(data_cache, -10, 110)
        
        # Test neg overlap with 3 pos caches
        x = np.zeros(220)
        x[9] += 1.
        x[10:] += 100.
        x[110:] += 60.
        x[210:] += 40.
        res = _getDataRangeTestWrapper(data_cache, -10, 210)
        
    def test_saving_files(self):
        filename = os.path.dirname(os.path.realpath(__file__))
        filename = os.path.join(filename, 'testDataFiles', 'chimera_1event.log')
        
        event_database = findEvents([filename], save_file_name = ['_testSavingFiles_9238.h5'])[0]
        
        self.assertTrue(os.path.isfile(event_database))
        
        h5file = eD.open_file(event_database, mode='r')
        
        self.assertTrue(h5file.isopen)
        
        h5file.close()
        
        # delete the newly created event file
        os.remove(event_database)

    def test_chimera_no_noise_1event(self):
        filename = os.path.dirname(os.path.realpath(__file__))
        filename = os.path.join(filename, 'testDataFiles', 'chimera_nonoise_1event.log')
        event_database = findEvents([filename], save_file_name = ['_testChimera_nonoise_1Event_9238.h5'],
                                   **self.default_params)[0]
        
        h5file = eD.open_file(event_database, mode='r')
        
        events = h5file.root.events

        # check event table correct length        
        eventTable = events.eventTable
        self.assertTrue(eventTable.nrows, 1)
        
        # check raw data array correct length
        rawDataMatrix = events.rawData
        self.assertEqual(rawDataMatrix.nrows, 1)
        eventLength = eventTable[0]['eventLength']
        self.assertEqual(eventLength, 1000)
        
        # Make sure only 1 event with 1 level
        levelsMatrix = events.levels
        self.assertEqual(levelsMatrix.nrows, 1)
        nLevels = eventTable[0]['nLevels']
        self.assertEqual(nLevels, 1)
        levels = levelsMatrix[0]
        self.assertAlmostEqual(levels[0], 0.9332, 4)
        
        # Check 1 event with 1 levelLength
        lengthsMatrix = events.levelLengths
        self.assertEqual(lengthsMatrix.nrows, 1)
        lengths = lengthsMatrix[0]
        self.assertEqual(lengths[0], 1000)
        
        h5file.close()
        
        # delete the newly created event file
        os.remove(event_database)
        
    def _testChimera_nonoise_1Event_2Levels_helper(self, h5file):
        events = h5file.root.events
        
        eventTable = events.eventTable
        self.assertTrue(eventTable.nrows, 1)
        
        # check raw data array correct length
        rawDataMatrix = events.rawData
        self.assertEqual(rawDataMatrix.nrows, 1)
        eventLength = eventTable[0]['eventLength']
        self.assertEqual(eventLength, 1500)
        
        levelsMatrix = events.levels
        self.assertEqual(levelsMatrix.nrows, 1)
        levels = levelsMatrix[0]
        nLevels = eventTable[0]['nLevels']
        self.assertEqual(nLevels, 2)
        self.assertAlmostEqual(levels[0], 0.9332, 4)
        self.assertAlmostEqual(levels[1], 0.78064, 4)
        
        levelsMatrix = events.levelLengths
        self.assertEqual(levelsMatrix.nrows, 1)
        levels = h5file.get_level_lengths_at(0)
        self.assertEqual(len(levels), 2)
        self.assertEqual(levels[0], 750)
        self.assertEqual(levels[1], 750)
        
    def testChimera_nonoise_1Event_2Levels(self):
        filename = os.path.dirname(os.path.realpath(__file__))
        filename = os.path.join(filename, 'testDataFiles', 'chimera_nonoise_1event_2levels.log')
        eventDatabase = findEvents([filename], save_file_name = ['_testChimera_nonoise_1Event_2Levels_9238.h5'],
                                   **self.default_params)[0]
        
        h5file = eD.open_file(eventDatabase, mode='r')
        self._testChimera_nonoise_1Event_2Levels_helper(h5file)
        h5file.close()
        
        # delete the newly created event file
        os.remove(eventDatabase)
        
    def _testChimera_nonoise_2events_1levels_wrapper(self, h5file):
        events = h5file.root.events

        # check event table correct length        
        eventTable = events.eventTable
        self.assertTrue(eventTable.nrows, 2)
        
        # check raw data array correct length
        rawDataMatrix = events.rawData
        self.assertEqual(rawDataMatrix.nrows, 2)
        eventLength = eventTable[0]['eventLength']
        self.assertEqual(eventLength, 1000)
        # second event
        eventLength = eventTable[1]['eventLength']
        self.assertEqual(eventLength, 1000)
        
        # Make sure only 2 events with 1 level each
        levelsMatrix = events.levels
        self.assertEqual(levelsMatrix.nrows, 2)
        levels = levelsMatrix[0]
        nLevels = eventTable[0]['nLevels']
        self.assertEqual(nLevels, 1)
        self.assertAlmostEqual(levels[0], 0.9332, 4)
        # event 2
        levels = levelsMatrix[1]
        nLevels1 = eventTable[1]['nLevels']
        self.assertEqual(nLevels1, 1)
        self.assertAlmostEqual(levels[0], 0.9332, 4)
        
        # Check 2 events with 1 level -> 1 lengths
        lengthsMatrix = events.levelLengths
        self.assertEqual(lengthsMatrix.nrows, 2)
        lengths1 = h5file.get_level_lengths_at(0)
        self.assertEqual(len(lengths1), 1)
        self.assertEqual(lengths1[0], 1000)
        # event
        lengths2 = h5file.get_level_lengths_at(1)
        self.assertEqual(len(lengths2), 1)
        self.assertEqual(lengths2[0], 1000)
        
    def test_chimera_no_noise_2events_1levels(self):
        filename = os.path.dirname(os.path.realpath(__file__))
        filename = os.path.join(filename, 'testDataFiles', 'chimera_nonoise_2events_1levels.log')
        event_databases = findEvents([filename], save_file_name=['_testChimera_nonoise_2events_1levels_9238.h5'],
                                     **self.default_params)

        self.assertEqual(len(event_databases), 1)

        event_database = event_databases[0]
        
        h5file = eD.open_file(event_database, mode='r')
        self._testChimera_nonoise_2events_1levels_wrapper(h5file)
        h5file.close()
        
        # delete the newly created event file
        os.remove(event_database)
        
    def test_multiple_files(self):
        filename1 = os.path.dirname(os.path.realpath(__file__))
        filename1 = os.path.join(filename1, 'testDataFiles', 'chimera_nonoise_2events_1levels.log')
        filename2 = os.path.dirname(os.path.realpath(__file__))
        filename2 = os.path.join(filename2, 'testDataFiles', 'chimera_nonoise_1event_2levels.log')
        file_names = [filename1, filename2]
        event_databases = findEvents(file_names,
                                     save_file_names=['_testMultipleFiles_1_9238.h5', '_testMultipleFiles_2_9238.h5'],
                                     **self.default_params)
        
        self.assertEqual(len(event_databases), 2)
        
        h5file = eD.open_file(event_databases[0], mode='r')
        self._testChimera_nonoise_2events_1levels_wrapper(h5file)
        h5file.close()
        os.remove(event_databases[0])
        
        h5file = eD.open_file(event_databases[1], mode='r')
        self._testChimera_nonoise_1Event_2Levels_helper(h5file)
        h5file.close()
        os.remove(event_databases[1])
        
if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
