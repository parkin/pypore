"""
Created on Sep 13, 2013

@author: `@parkin`_
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

        names = [x._v_name for x in file_h.walkGroups()]
        self.assertIn('/', names, 'file missing root group')
        self.assertIn('events', names, "file missing event group.")

    def _test_empty_events_group(self, database=None, events_group=None):
        """
        Checks that the events group has the correct (and empty) tables/arrays
        """
        if database is None:
            database = self.database
        if events_group is None:
            events_group = database.root.events

        # Check the events group has the correct nodes
        # Should be events, eventTable, eventData, raw_data
        names = []
        for node in database.walkNodes(events_group):
            names.append(node._v_name)
        names = [x._v_name for x in database.walkNodes(events_group)]
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
        self._test_empty_events_group(events_group=self.database.root.events)

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

    def test_initialize_events_database_with_debug(self):
        filename = 'test_initialize_events_database_with_debug.h5'
        if os.path.exists(filename):
            os.remove(filename)
        n_points = 100
        n_channels = 2
        database = eD.open_file(filename, mode='w', debug=True, n_points=n_points, n_channels=n_channels)

        self._test_initial_root(database)

        self._test_empty_events_group(events_group=database.root.events)

        # Make sure is debug
        self.assertTrue(database.is_debug())

        # Make sure the debug group is there.
        names = [x._v_name for x in database.walkGroups()]
        self.assertIn('debug', names, 'No debug group.')

        debug_group = database.root.debug

        # Make sure the debug group
        debug_group_names = [x._v_name for x in database.walkNodes(debug_group)]
        print debug_group_names
        self.assertIn('data', debug_group_names, 'No data matrix.')
        self.assertIn('baseline', debug_group_names, 'No baseline matrix.')
        self.assertIn('threshold_positive', debug_group_names, 'No positive threshold matrix.')
        self.assertIn('threshold_negative', debug_group_names, 'No negative threshold matrix.')

        # Make sure arrays are correct dimensions
        self.assertEqual(debug_group.data.shape, (n_channels, n_points))
        self.assertEqual(debug_group.baseline.shape, (n_channels, n_points))
        self.assertEqual(debug_group.threshold_positive.shape, (n_channels, n_points))
        self.assertEqual(debug_group.threshold_negative.shape, (n_channels, n_points))

        # Check is in write mode
        database.root.events.raw_data.append(np.zeros((1, 100)))
        database.flush()

        database.close()
        os.remove(filename)

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
        self._test_empty_events_group(events_group=events_group)

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
        Test that get_sample_rate returns root.events.eventTable.attrs.sample_rate
        """
        rate = 13928.99
        self.database.root.events.eventTable.attrs.sample_rate = rate

        self.assertEqual(self.database.get_sample_rate(), rate)

    def test_to_csv_default_columns(self):
        import csv

        event_start = 2
        event_length = 3
        n_levels = 4
        baseline = 10.0
        current_blockage = 9.0

        event_start_2 = 19
        event_length_2 = 20
        n_levels_2 = 8
        baseline_2 = -12.
        current_blockage_2 = 99.

        self.database.append_event(array_row=0, event_start=event_start, event_length=event_length, n_levels=n_levels,
                                   raw_points_per_side=5,
                                   baseline=baseline,
                                   current_blockage=current_blockage, area=8)
        self.database.append_event(array_row=1, event_start=event_start_2, event_length=event_length_2,
                                   n_levels=n_levels_2,
                                   raw_points_per_side=5,
                                   baseline=baseline_2,
                                   current_blockage=current_blockage_2, area=16)
        # raw_points_per_side=5
        # def append_event(self, array_row, event_start, event_length, n_levels, raw_points_per_side, baseline,
        # current_blockage, area, raw_data=None, levels=None, level_lengths=None):

        sample_rate = 10.e4
        self.database.get_event_table().attrs.sample_rate = sample_rate
        self.database.flush()

        output_filename = "blahblah.csv"
        if os.path.exists(output_filename):
            os.remove(output_filename)

        self.database.to_csv(output_filename)

        self.assertTrue(os.path.exists(output_filename))

        ifile = open(output_filename, 'rb')
        reader = csv.reader(ifile)

        # get header
        headers = next(reader, None)
        headers_should_be = ['Start Time', 'Dwell Time', 'Blockage', 'Baseline', 'Inter Event Time', 'Number of Levels']

        for i, header in enumerate(headers):
            self.assertEqual(header, headers_should_be[i])

        row_count = 0
        row_should_be = [event_start / sample_rate, event_length / sample_rate, current_blockage, baseline,
                         event_start / sample_rate,
                         n_levels]
        row_should_be_2 = [event_start_2 / sample_rate, event_length_2 / sample_rate, current_blockage_2, baseline_2,
                           (event_start_2 - event_start) / sample_rate,
                           n_levels_2]
        row = next(reader, None)
        self.assertEqual(len(row), len(row_should_be))
        for i, el in enumerate(row):
            self.assertAlmostEqual(float(el), row_should_be[i])
        row_count += 1

        row_2 = next(reader, None)
        self.assertEqual(len(row_2), len(row_should_be_2))
        for i, el in enumerate(row_2):
            self.assertAlmostEqual(float(el), row_should_be_2[i])
        row_count += 1

        for row_i in reader:
            row_count += 1

        self.assertEqual(row_count, 2)

        os.remove(output_filename)


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()