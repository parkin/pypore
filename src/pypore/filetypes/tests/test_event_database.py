"""
Created on Sep 13, 2013

@author: `@parkin1`_
"""
import unittest
import os

import numpy as np
import numpy.testing as npt

import pypore.filetypes.event_database as eD


class TestEventDatabase(unittest.TestCase):
    def setUp(self):
        self.filename = 'testEventDatabase_938247283278128.h5'
        self.max_event_length = 100
        self.database = eD.open_file(self.filename, mode='w', maxEventLength=self.max_event_length)

    def tearDown(self):
        self.database.close()
        os.remove(self.filename)

    def _test_initial_root(self, file_h=None):
        """
        Check that only the root group and event group exist
        """
        if file_h is None:
            file_h = self.database

        names = []
        for group in file_h.walkGroups():
            names.append(group._v_name)
        self.assertEqual(len(names), 2, "Incorrect number of initial groups in event database.")
        self.assertIn('/', names, 'file missing root group')
        self.assertIn('events', names, "file missing event group.")

    def _test_empty_events_group(self, events_group=None):
        """
        Checks that the events group has the correct (and empty) tables/arrays
        """
        if events_group is None:
            events_group = self.database.root.events

        # Check the events group has the correct nodes
        # Should be events, eventTable, eventData, raw_data
        names = []
        for node in self.database.walkNodes(events_group):
            names.append(node._v_name)
        names_should_be = ['events', 'eventTable', 'raw_data', 'levels', 'level_lengths']
        self.assertEqual(len(names), len(names_should_be))
        self.assertEqual(sorted(names), sorted(names_should_be))  # i don't care what order these lists are

        # Assert table, vlarrays are empty
        self.assertEqual(events_group.eventTable.nrows, 0)
        self.assertEqual(events_group.raw_data.nrows, 0)
        self.assertEqual(events_group.levels.nrows, 0)
        self.assertEqual(events_group.level_lengths.nrows, 0)

        # Check the eventTable columns are correct and in correct order
        column_names = ['array_row', 'event_start', 'event_length', 'n_levels', 'raw_points_per_side', 'baseline',
                        'current_blockage', 'area']
        self.assertEqual(events_group.eventTable.colnames, column_names)

    def test_clean_database(self):
        """
        Tests that cleanDatabase removing eventsTable, raw_data, levels, and levelData
        and initializing with empty table/matrices.
        """
        # put stuff in raw_data
        raw_data = np.ones((1, self.database.max_event_length))
        self.database.append_event(1, 2, 3, 4, 5, 6, 7, 8, raw_data, raw_data, raw_data)

        # clean the database
        self.database.clean_database()

        # check that the database has all the empty table/matrices
        self._test_empty_events_group(self.database.root.events)

    def test_append_event(self):
        """
        Tests appendEvent
        
        array_row, event_start, event_length, n_levels, raw_points_per_side,\
                    baseline, current_blockage, area, raw_data = None, levels = None, level_lengths = None
        """
        table = self.database.get_event_table()

        # add an event
        self.database.append_event(1, 2, 3, 4, 5, 6, 7, 8)
        self.database.flush()

        # Check eventTable for one correct row.
        self.assertEqual(self.database.get_event_table().nrows, 1)
        self.assertEqual(table[0]['array_row'], 1)
        self.assertEqual(table[0]['event_start'], 2)
        self.assertEqual(table[0]['event_length'], 3)
        self.assertEqual(table[0]['n_levels'], 4)
        self.assertEqual(table[0]['raw_points_per_side'], 5)
        self.assertEqual(table[0]['baseline'], 6)
        self.assertEqual(table[0]['current_blockage'], 7)
        self.assertEqual(table[0]['area'], 8)

        # Check for nothing in raw_data, levels, level_lengths
        self.assertEqual(self.database.root.events.raw_data.nrows, 0)
        self.assertEqual(self.database.root.events.levels.nrows, 0)
        self.assertEqual(self.database.root.events.level_lengths.nrows, 0)

        # add another event, this time with raw_data
        raw_data = np.ones((1, self.database.max_event_length))
        self.database.append_event(10, 20, 30, 40, 50, 60, 70, 80, raw_data)
        self.database.flush()

        # Check eventTable for two correct rows.
        self.assertEqual(self.database.get_event_table().nrows, 2)
        self.assertEqual(table[1]['array_row'], 10)
        self.assertEqual(table[1]['event_start'], 20)
        self.assertEqual(table[1]['event_length'], 30)
        self.assertEqual(table[1]['n_levels'], 40)
        self.assertEqual(table[1]['raw_points_per_side'], 50)
        self.assertEqual(table[1]['baseline'], 60)
        self.assertEqual(table[1]['current_blockage'], 70)
        self.assertEqual(table[1]['area'], 80)

        # Check for 1 row in raw_data and nothing in levels, level_lengths
        self.assertEqual(self.database.root.events.raw_data.nrows, 1)
        self.assertEqual(self.database.root.events.levels.nrows, 0)
        self.assertEqual(self.database.root.events.level_lengths.nrows, 0)
        npt.assert_array_equal(self.database.root.events.raw_data[:], raw_data)

    def test_delete_event(self):
        """
        Tests deleting single events from eventTable.
        """
        table = self.database.get_event_table()

        # Test deleting all events in database does nothing
        self.database.append_event(1, 2, 3, 4, 5, 6, 7, 8)
        self.database.remove_event(0)
        self.assertEqual(self.database.get_event_count(), 1)

        # Test deleting out of range does nothing
        self.database.remove_event(-1)
        self.assertEqual(self.database.get_event_count(), 1)
        self.database.remove_event(1)
        self.assertEqual(self.database.get_event_count(), 1)
        self.database.remove_event(10)
        self.assertEqual(self.database.get_event_count(), 1)

        # Test deleting first event in database
        for i in xrange(1, 10):
            self.database.append_event(i + 1, i + 2, i + 3, i + 4, i + 5, i + 6, i + 7, i + 8)
        self.assertEqual(self.database.get_event_count(), 10)
        self.assertEqual(table[0]['array_row'], 1)
        self.database.remove_event(0)
        self.assertEqual(self.database.get_event_count(), 9)
        self.assertEqual(table[0]['array_row'], 2)

        # Test deleting last event in database
        self.assertEqual(table[8]['array_row'], 10)
        self.database.remove_event(8)
        self.assertEqual(self.database.get_event_count(), 8)
        self.assertEqual(table[7]['array_row'], 9)

        # Test deleting second to last row
        self.assertEqual(table[6]['array_row'], 8)
        self.database.remove_event(6)
        self.assertEqual(self.database.get_event_count(), 7)
        self.assertEqual(table[6]['array_row'], 9)
        self.assertEqual(table[5]['array_row'], 7)

    def test_delete_events(self):
        """
        Test removing ranges of events from event table.
        """
        table = self.database.get_event_table()

        # Test deleting all events in database does nothing
        self.database.append_event(1, 2, 3, 4, 5, 6, 7, 8)
        self.database.remove_events(0, 1)
        self.assertEqual(self.database.get_event_count(), 1)

        # Add to total of 10 events
        for i in xrange(1, 10):
            self.database.append_event(i + 1, i + 2, i + 3, i + 4, i + 5, i + 6, i + 7, i + 8)

        # Test deleting all events does nothing
        self.database.remove_events(0, 10)
        self.assertEqual(self.database.get_event_count(), 10)

        # Test for i out of range
        self.database.remove_events(-1, 5)
        self.assertEqual(self.database.get_event_count(), 10)
        self.database.remove_events(-9999, 5)
        self.assertEqual(self.database.get_event_count(), 10)
        self.database.remove_events(5, 5)
        self.assertEqual(self.database.get_event_count(), 10)
        self.database.remove_events(6, 5)
        self.assertEqual(self.database.get_event_count(), 10)
        self.database.remove_events(50, 5)
        self.assertEqual(self.database.get_event_count(), 10)
        self.database.remove_events(50, 51)
        self.assertEqual(self.database.get_event_count(), 10)

        # Test for j out of range
        self.database.remove_events(5, 5)
        self.assertEqual(self.database.get_event_count(), 10)
        self.database.remove_events(5, 4)
        self.assertEqual(self.database.get_event_count(), 10)
        self.database.remove_events(5, -1)
        self.assertEqual(self.database.get_event_count(), 10)
        self.database.remove_events(5, -100)
        self.assertEqual(self.database.get_event_count(), 10)
        self.database.remove_events(5, 11)
        self.assertEqual(self.database.get_event_count(), 10)
        self.database.remove_events(5, 100)
        self.assertEqual(self.database.get_event_count(), 10)

        # Test removing first event
        self.database.remove_events(0, 1)
        self.assertEqual(self.database.get_event_count(), 9)
        self.assertEqual(table[0]['array_row'], 2)

        # Test removing final event
        self.database.remove_events(8, 9)
        self.assertEqual(self.database.get_event_count(), 8)
        self.assertEqual(table[7]['array_row'], 9)

        # Test removing range
        self.database.remove_events(1, 7)
        self.assertEqual(self.database.get_event_count(), 2)
        self.assertEqual(table[0]['array_row'], 2)
        self.assertEqual(table[1]['array_row'], 9)

    def test_initialize_events_database(self):
        self._test_initial_root(self.database)

        self._test_empty_events_group()

        # Check is in write mode
        self.database.root.events.raw_data.append(np.zeros((1, 100)))
        self.database.flush()

    def test_open_existing_empty_database(self):
        """
        Tests opening an existing h5 file with an empty 
        EventsDatabase structure.
        """
        self.database.close()

        self.database = eD.open_file(self.filename)

        self._test_initial_root(self.database)

        self._test_empty_events_group()

    def test_open_existing_full_database(self):
        """
        Tests opening an existing h5 file with events in
        the EventDatabase structure.
        """
        # Add to the raw_data matrix
        raw_data = np.zeros((2, self.max_event_length))
        raw_data[1][:] += 1
        self.database.append_raw_data(raw_data)

        # Add to the levels matrix
        levels = raw_data + 1
        self.database.append_levels(levels)

        # Add to the level_lengths matrix
        level_lengths = raw_data + 2
        self.database.append_level_lengths(level_lengths)

        # Add to the event table
        event_row = self.database.get_event_table_row()
        event_row['array_row'] = 1
        event_row['event_start'] = 2
        event_row['event_length'] = 3
        event_row['n_levels'] = 4
        event_row['raw_points_per_side'] = 5
        event_row['baseline'] = 6
        event_row['current_blockage'] = 7
        event_row['area'] = 8
        event_row.append()

        # Close the file
        self.database.flush()
        self.database.close()

        # Open the existing file
        self.database = eD.open_file(self.filename, mode='r')

        # Check the raw_data matrix
        npt.assert_array_equal(raw_data, self.database.root.events.raw_data[:])

        # Check the levels matrix
        npt.assert_array_equal(levels, self.database.root.events.levels[:])

        # Check the level_lengths matrix
        npt.assert_array_equal(level_lengths, self.database.root.events.level_lengths[:])

        # Check the eventTable
        row = self.database.root.events.eventTable[0]
        self.assertEqual(row['array_row'], 1)
        self.assertEqual(row['area'], 8)

    def test_initialize_database_with_existing_nodes(self):
        """
        Test that calling initialize_c database with existing nodes does not
        throw an error (ie existing nodes ignored).
        """
        self.assertIn('eventTable', self.database.root.events)
        self.assertIn('raw_data', self.database.root.events)

        raw = np.ones((1, self.max_event_length))
        self.database.append_raw_data(raw)

        # tests to see if error thrown
        self.database.initialize_database()

        # check that raw_data is still the same
        npt.assert_array_equal(raw, self.database.root.events.raw_data[:])

    def test_get_events_group(self):
        """
        Test the getter for /events
        """
        events_group = self.database.get_events_group()
        self._test_empty_events_group(events_group)

        self.assertIn('raw_data', events_group)
        self.assertIn('levels', events_group)
        self.assertIn('level_lengths', events_group)

    def test_get_event_count(self):
        """
        Tests that getEventCount returns the correct value, even
        after events are added/deleted.
        """
        self.assertEqual(self.database.get_event_count(), 0)

        for i in xrange(100):
            self.database.append_event(i + 1, i + 2, i + 3, i + 4, i + 5, i + 6, i + 7, i + 8)
            self.assertEqual(self.database.get_event_count(), i + 1)

        for i in xrange(50):
            self.database.remove_event(0)
            self.assertEqual(self.database.get_event_count(), 99 - i)

    def test_get_event_data_at(self):
        """
        Tests getting only the event points from raw_data
        """
        raw = np.linspace(0.0, 100.0, self.max_event_length).reshape((1, 100))

        # event_length=3, raw_points_per_side=5
        self.database.append_event(0, 2, 3, 4, 5, 6, 7, 8, raw)

        row = self.database.get_event_row(0)
        event_length = row['event_length']
        raw_points_per_side = row['raw_points_per_side']

        self.assertEqual(event_length, 3)
        self.assertEqual(raw_points_per_side, 5)
        npt.assert_array_equal(self.database.get_event_data_at(0),
                               raw[0][raw_points_per_side:event_length + raw_points_per_side])

    def test_get_event_row(self):
        """
        Test that getEventRow returns correct row.
        """
        for i in xrange(10):
            self.database.append_event(i + 1, i + 2, i + 3, i + 4, i + 5, i + 6, i + 7, i + 8)

        row = self.database.get_event_row(1)
        self.assertEqual(row['array_row'], 2)

    def test_get_level_lengths_at(self):
        """
        Tests that getLevelLengthsAt returns a numpy matrix of the 
        level_lengths corresponding to the event
        in row 'i' of eventTable.
        """
        level_lengths = np.array(range(self.max_event_length)).reshape((1, self.max_event_length))

        self.database.append_event(0, 2, 3, 4, 5, 6, 7, 8,
                                   level_lengths=level_lengths)  # event_length=3, raw_points_per_side=5

        row = self.database.get_event_row(0)
        n_levels = row['n_levels']

        self.assertEqual(n_levels, 4)
        npt.assert_array_equal(self.database.get_level_lengths_at(0), level_lengths[0][:n_levels])

    def test_get_levels_at(self):
        """
        Tests that getLevelsAt returns a numpy matrix of the levels corresponding to the event
        in row 'i' of eventTable.
        """
        levels = np.linspace(0.0, 100.0, self.max_event_length).reshape((1, self.max_event_length))

        self.database.append_event(0, 2, 3, 4, 5, 6, 7, 8, levels=levels)  # event_length=3, raw_points_per_side=5

        row = self.database.get_event_row(0)
        n_levels = row['n_levels']

        self.assertEqual(n_levels, 4)
        npt.assert_array_equal(self.database.get_levels_at(0), levels[0][:n_levels])

    def test_get_raw_data_at(self):
        """
        Tests that get_raw_data_at returns correctly sized(event_length + 2*raw_points_per_side)
        numpy array with correct data.
        """
        raw = np.linspace(0.0, 100.0, self.max_event_length).reshape((1, self.max_event_length))

        self.database.append_event(0, 2, 3, 4, 5, 6, 7, 8, raw)  # event_length=3, raw_points_per_side=5

        row = self.database.get_event_row(0)
        event_length = row['event_length']
        raw_points_per_side = row['raw_points_per_side']

        self.assertEqual(event_length, 3)
        self.assertEqual(raw_points_per_side, 5)
        npt.assert_array_equal(self.database.get_raw_data_at(0), raw[0][:event_length + 2 * raw_points_per_side])

    def test_get_sample_rate(self):
        """
        Test that getSampleRate returns root.events.eventTable.attrs.sample_rate
        """
        rate = 13928.99
        self.database.root.events.eventTable.attrs.sample_rate = rate

        self.assertEqual(self.database.get_sample_rate(), rate)


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()