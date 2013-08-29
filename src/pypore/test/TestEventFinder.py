'''
Created on Aug 27, 2013

@author: parkin
'''
import unittest
from src.pypore.EventFinder import findEvents


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