"""
Created on Aug 19, 2013

@author: `@parkin`_
"""
#cython: embedsignature=True


import os
import time
import datetime

import numpy as np
cimport numpy as np

import filetypes.event_database as ed
import sys

from libc.math cimport sqrt
from libc.math cimport fmax
from libc.math cimport fabs

from cpython cimport bool

from pypore.io import get_reader_from_filename
from pypore.io.abstract_reader cimport AbstractReader
from pypore.strategies.baseline_strategy cimport BaselineStrategy
from pypore.strategies.adaptive_baseline_strategy import AdaptiveBaselineStrategy
from pypore.strategies.threshold_strategy cimport ThresholdStrategy
from pypore.strategies.noise_based_threshold_strategy import NoiseBasedThresholdStrategy

DTYPE = np.float
ctypedef np.float_t DTYPE_t

DTYPE_UINT32 = np.uint32
ctypedef np.uint32_t DTYPE_UINT32_t

cdef np.ndarray[DTYPE_t] _get_data_range(data_cache, long i, long n):
    """
    returns [i,n)
    """
    cdef np.ndarray[DTYPE_t,
                    negative_indices = False,
                    mode = 'c'] res = np.zeros(n - i, dtype=DTYPE)
    cdef long res_spot = 0, l, nn
    # do we need to include points from the old data
    # (eg. for raw event points)
    if i < 0:
        l = data_cache[0].size
        # Is the range totally within the old data
        if n <= 0:
            res = data_cache[0][l + i:l + n]
            return res
        res[0:-i] = data_cache[0][l + i:l]
        res_spot -= i
        i = 0
    cdef long spot = 0
    cdef np.ndarray[DTYPE_t] cache
    cdef int q = 0
    for q in xrange(len(data_cache) - 1):
        cache = data_cache[q + 1]
        nn = cache.size
        # if all the rest of the data is in this cache
        # add it to the end of the result and return
        if i >= spot and n <= spot + nn:
            res[res_spot:] = cache[i - spot:n - spot]
            break
        # else we must need to visit more caches
        elif i < spot + nn:
            res[res_spot:res_spot + nn - (i - spot)] = cache[i - spot:]
            res_spot += nn - (i - spot)
            i = spot + nn
        spot += nn
    return res

cpdef np.ndarray[DTYPE_t] _get_data_range_test_wrapper(data_cache, long i, long n):
    """
    Just a wrapper so the python unittests can call :py:func:`_get_data_range`.
    """
    return _get_data_range(data_cache, i, n)

cdef _lazy_load_find_events(AbstractReader reader, Parameters parameters, object pipe=None, h5file=None,
                            save_file_name=None):
    cdef unsigned int event_count = 0

    cdef unsigned int get_blocks = 1

    cdef unsigned int raw_points_per_side = 50

    cdef double sample_rate = reader.get_sample_rate_c()
    cdef double time_step = 1. / sample_rate
    # Min and Max number of points in an event
    cdef unsigned int min_event_steps = np.ceil(parameters.min_event_length * 1e-6 / time_step)
    cdef unsigned int max_event_steps = np.ceil(parameters.max_event_length * 1e-6 / time_step)
    cdef long points_per_channel_total = reader.get_points_per_channel_total_c()

    cdef BaselineStrategy baseline_type = parameters.baseline_strategy

    # Threshold direction.  -1 for negative, 0 for both, +1 for positive
    direction_positive = False
    direction_negative = False
    if parameters.detect_positive_events:
        direction_positive = True
    if parameters.detect_negative_events:
        direction_negative = True

    # allocate memory for data
    data_x = reader.get_next_blocks_c(get_blocks)
    cdef np.ndarray[DTYPE_t] data = data_x[0]  # only get channel 1
    del data_x

    cdef unsigned long n = data.size

    if n < 100:
        print 'Not enough data points in file.'
        if pipe is not None:
            pipe.close()
        return 'Not enough data points in file.'

    if save_file_name is None:
        # Get the name of the database file we want to save
        # if we have input.hkd, then save database to
        # input_Events_YYmmdd_HHMMSS.h5
        save_file_name = list(reader.get_filename_c())
        # Remove the .mat off the end
        for _ in xrange(0, 4):
            save_file_name.pop()
        # Get a string with the current year/month/day/hour/minute to label the file
        day_time = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        save_file_name.append('_Events_' + day_time + '.h5')
        save_file_name = "".join(save_file_name)

    cdef unsigned long max_points = max_event_steps + 2 * raw_points_per_side

    # Open the event database
    if h5file is None:
        h5file = ed.open_file(save_file_name, maxEventLength=max_points, mode='w')
    raw_data = h5file.root.events.raw_data
    levels_matrix = h5file.root.events.levels
    lengths_matrix = h5file.root.events.level_lengths

    cdef double data_point = data[0]

    baseline_type.baseline = data_point

    cdef ThresholdStrategy threshold_type = parameters.threshold_strategy

    cdef double threshold_start = 0.0
    cdef double threshold_end = 0.0

    initialization_index = 100

    baseline_type.initialize_c(data[0:initialization_index])

    data_cache = [np.zeros(n, dtype=DTYPE) + data_point, data]

    is_event = False
    was_event_positive = False  # Was the event an up spike?

    # Figure out how many rows will it take to have a cache of 10MB (1048576 bytes = 1MB)
    cdef num_rows_in_event_cache = int(10 * 1048576 / (max_points * (np.dtype(DTYPE).itemsize)))
    # Make an array to hold events in memory before writing to disk.
    cdef np.ndarray[DTYPE_t, ndim = 2] event_cache = np.zeros((num_rows_in_event_cache, max_points), dtype=DTYPE)
    cdef np.ndarray[DTYPE_t, ndim = 2] levels_cache = np.zeros((num_rows_in_event_cache, max_points), dtype=DTYPE)
    cdef np.ndarray[DTYPE_UINT32_t, ndim = 2] level_length_cache = np.zeros((num_rows_in_event_cache, max_points),
                                                                            dtype=DTYPE_UINT32)

    cdef event_cache_index = 0

    cdef:

        unsigned long i = 0
        unsigned long event_i = 0
        unsigned long min_index = 0
        unsigned long prev_i = 0
        double time1 = time.time()
        double time2 = time1
        double time_temp = 0
        unsigned long event_start = 0
        unsigned long event_end = 0
        unsigned long start_index = 0
        unsigned long end_index = 0
        unsigned long place_in_data = 0

        double mean_estimate = 0.0
        double sn = 0
        double sp = 0
        double Sn = 0
        double Sp = 0
        double Gn = 0
        double Gp = 0
        double new_mean = 0
        double var_estimate = 0
        unsigned int n_levels = 0
        double delta = 0
        unsigned long min_index_p = 0
        unsigned long min_index_n = 0
        double float_inf = np.finfo('d').max
        double min_Sp = float_inf
        double min_Sn = float_inf
        long ko = i
        double event_area = data_point - baseline_type.get_baseline_c()  # integrate the area
        double current_blockage = 0
        int cache_index = 0
        unsigned int size = 0
        double h = 0
        double percent_done = 0
        double rate = 0
        double total_rate = 0
        int time_left = 0
        int qq = 0
        int cache_size = 0
        long cache_refreshes = 0  # number of times we get new data at the
        # end of the loop
        double temp = 0
        long temp_long = 0
        double baseline = baseline_type.get_baseline_c()
        double variance = baseline_type.get_variance_c()

        #         np.ndarray[DTYPE_t] level_values
        np.ndarray[DTYPE_t] curr_data = data_cache[1]  # data in dataCache[1]

        np.ndarray[DTYPE_t] m_levels = np.zeros(max_points, dtype=DTYPE)
        np.ndarray[DTYPE_UINT32_t] m_levels_length = np.zeros(max_points, dtype=DTYPE_UINT32)

        double level_sum = 0
        long prev_level_start = 0

        int last_event_sent = 0

    # search for events.  Keep track of filter_parameter filtered local (adapting!) mean and variance,
    # and use them to decide filter_parameter threshold_start for events.  See
    # http://pubs.rsc.org/en/content/articlehtml/2012/nr/c2nr30951c for more details.
    while i < n:
        data_point = curr_data[i]
        threshold_start = threshold_type.compute_starting_threshold_c(baseline, variance)

        # Detecting a negative event
        if direction_negative and data_point < baseline - threshold_start:
            is_event = True
            was_event_positive = False
        # Detecting a positive event
        elif direction_positive and data_point > baseline + threshold_start:
            is_event = True
            was_event_positive = True
        if is_event:
            is_event = False
            # Set ending threshold_end
            threshold_end = threshold_type.compute_ending_threshold_c(baseline, variance)
            event_start = i
            event_end = i + 1
            done = False
            event_i = i
            # CUSUM stuff
            mean_estimate = data_point
            n_levels = 0
            sn = sp = Sn = Sp = Gn = Gp = 0
            var_estimate = variance
            #             n_levels = 1  # We're already starting with one level
            delta = fabs(mean_estimate - baseline) / 2.
            min_index_p = min_index_n = i
            min_Sp = min_Sn = float_inf
            ko = i
            event_area = data_point  # integrate the area
            cache_index = 1  # which index in the cache is event_i
            # trying to grab data from?

            level_sum = data_point
            level_sum_minp = data_point
            level_sum_minn = data_point
            prev_level_start = event_i
            cache_size = n

            # loop until event ends
            while not done and event_i - event_start < max_event_steps:
                event_i += 1
                if event_i >= cache_size:  # We may need new data
                    # we need new data if we've run out
                    cache_index += 1
                    datas = reader.get_next_blocks_c(get_blocks)
                    datas = datas[0]
                    n = datas.size
                    cache_size += n
                    if n < 1:
                        i = n
                        print "Done"
                        break
                    data_cache.append(datas)
                if cache_index == 1:
                    data_point = curr_data[event_i]
                else:
                    data_point = data_cache[cache_index][event_i % n]
                if (not was_event_positive and data_point >= baseline - threshold_end) or (
                            was_event_positive and data_point <= baseline + threshold_end):
                    event_end = event_i
                    done = True
                    break
                # new mean = old_mean + (new_sample - old_mean)/(N)
                new_mean = mean_estimate + (data_point - mean_estimate) / (1 + event_i - ko)
                # New variance recursion relation 
                var_estimate = ((event_i - ko) * var_estimate + (data_point - mean_estimate) * (
                    data_point - new_mean)) / (1 + event_i - ko)
                mean_estimate = new_mean
                if var_estimate > 0:
                    sp = (delta / var_estimate) * (data_point - mean_estimate - delta / 2.)
                    sn = -(delta / var_estimate) * (data_point - mean_estimate + delta / 2.)
                elif delta == 0:
                    sp = sn = 0
                else:
                    sp = sn = float_inf
                Sp = Sp + sp
                Sn = Sn + sn
                Gp = fmax(0.0, Gp + sp)
                Gn = fmax(0.0, Gn + sn)
                level_sum += data_point
                if Sp <= 0:
                    Sp = 0
                    min_Sp = Sp
                    min_index_p = event_i
                    level_sum_minp = level_sum
                if Sn <= 0:
                    Sn = 0
                    min_Sn = Sn
                    min_index_n = event_i
                    level_sum_minn = level_sum
                h = delta / sqrt(var_estimate)
                # Did we detect a change?
                if Gp > h or Gn > h:
                    if Gp > h:
                        min_index = min_index_p
                        level_sum = level_sum_minp
                    else:
                        min_index = min_index_n
                        level_sum = level_sum_minn
                    m_levels_length[n_levels] = min_index + 1 - ko
                    m_levels[n_levels] = level_sum / m_levels_length[n_levels]  ##
                    n_levels += 1
                    # reset stuff
                    sn = sp = Sn = Sp = Gn = Gp = 0
                    min_Sp = min_Sn = float_inf
                    # Go back to 1 after the level change found
                    ko = event_i = min_index + 1
                    min_index_p = min_index_n = event_i
                    prev_level_start = event_i
                    if cache_index == 1:
                        mean_estimate = curr_data[event_i]
                    else:
                        mean_estimate = data_cache[cache_index][event_i % n]
                    level_sum = level_sum_minp = level_sum_minn = mean_estimate

            i = event_end
            if event_end > prev_level_start:
                m_levels_length[n_levels] = event_end - prev_level_start
                m_levels[n_levels] = level_sum / (event_end - prev_level_start)
                n_levels += 1
            # is the event long enough?
            if done and event_end - event_start > min_event_steps:
                # CUSUM stuff
                # otherwise just say 1 level and use the maximum change as the value
                if event_end - event_start < 10:
                    n_levels = 1
                    if was_event_positive:
                        current_blockage = np.max(_get_data_range(data_cache, event_start, event_end))
                        m_levels[0] = current_blockage
                        current_blockage -= baseline
                    else:
                        current_blockage = np.min(_get_data_range(data_cache, event_start, event_end))
                        m_levels[0] = current_blockage
                        current_blockage -= baseline
                    m_levels_length[0] = event_end - event_start
                else:
                    current_blockage = 0
                    # calculate the weighted average of the levels
                    for qq in xrange(n_levels):
                        current_blockage += m_levels[qq] * m_levels_length[qq]
                    current_blockage = current_blockage / (event_end - event_start) - baseline

                # end CUSUM, save events to file/cache
                h5file.append_event(event_count, event_start + place_in_data, event_end - event_start, \
                                    n_levels, raw_points_per_side, baseline, current_blockage, \
                                    event_area - baseline)

                event_cache[event_cache_index][:event_end - event_start + 2 * raw_points_per_side] = _get_data_range(
                    data_cache, event_start - raw_points_per_side, event_end + raw_points_per_side)
                levels_cache[event_cache_index][:n_levels] = m_levels[:n_levels]
                level_length_cache[event_cache_index][:n_levels] = m_levels_length[:n_levels]

                event_count += 1
                event_cache_index += 1

                if event_cache_index >= num_rows_in_event_cache:
                    raw_data.append(event_cache)
                    lengths_matrix.append(level_length_cache)
                    levels_matrix.append(levels_cache)
                    h5file.root.events.eventTable.flush()
                    event_cache_index = 0

                if event_count % 1000 == 0:
                    h5file.root.events.eventTable.flush()
                    h5file.flush()

        baseline = baseline_type.compute_baseline_c(data_point)
        variance = baseline_type.compute_variance_c(data_point)
        i += 1
        # remove any arrays in the cache that we don't need anymore
        while 0 < n <= i:
            del data_cache[0]
            i -= n
            place_in_data += n
            # If we're just left with dataCache[0], which is reserved
            # for old data, then we need new data.
            if len(data_cache) < 2:
                cache_refreshes += 1
                data_next = reader.get_next_blocks_c(get_blocks)
                data_cache.append(data_next[0])
            if len(data_cache) > 1:
                curr_data = data_cache[1]
                n = curr_data.size
            if cache_refreshes % 100 == 0 and len(data_cache) == 2:
                time_temp = time.time()
                recent_time = time_temp - time2
                if recent_time > 0:
                    total_time = time_temp - time1
                    percent_done = 100. * (place_in_data + i) / points_per_channel_total
                    rate = (place_in_data + i - prev_i) / recent_time
                    total_rate = (place_in_data + i) / total_time
                    time_left = int((points_per_channel_total - (place_in_data + i)) / rate)
                    status_text = "Event Count: %d Percent Done: %.2f Rate: %.2e pt/s Total Rate: %.2e pt/s Time Left: %s" % (
                        event_count, percent_done, rate, total_rate, datetime.timedelta(seconds=time_left))
                    if pipe is not None:
                        #                     if event_count > last_event_sent:
                        #                         pipe.send({'status_text': status_text, 'Events': save_file['Events'][last_event_sent:]})
                        pipe.send({'status_text': status_text})
                        #                         last_event_sent = event_count
                    else:
                        sys.stdout.write("\r" + status_text)
                        sys.stdout.flush()
                    time2 = time_temp
                    prev_i = place_in_data + i

    # clean up the caches, make sure everything is saved
    if event_cache_index > 0:
        h5file.root.events.eventTable.flush()
        raw_data.append(event_cache[:event_cache_index])
        lengths_matrix.append(level_length_cache[:event_cache_index])
        levels_matrix.append(levels_cache[:event_cache_index])
        event_cache_index = 0

    # Update the status_text one last time
    recent_time = time.time() - time2
    total_time = time.time() - time1
    percent_done = 100. * (place_in_data + i) / points_per_channel_total
    rate = (place_in_data + i - prev_i) / recent_time
    total_rate = (place_in_data + i) / total_time
    time_left = int((points_per_channel_total - (place_in_data + i)) / rate)
    status_text = "Event Count: %d Percent Done: %.2f Rate: %.2e pt/s Total Rate: %.2e pt/s Time Left: %s" % (
        event_count, percent_done, rate, total_rate, datetime.timedelta(seconds=time_left))
    if pipe is not None:
        #                     if event_count > last_event_sent:
        #                         pipe.send({'status_text': status_text, 'Events': save_file['Events'][last_event_sent:]})
        pipe.send({'status_text': status_text})
    #                         last_event_sent = event_count
    else:
        sys.stdout.write("\r" + status_text)
        sys.stdout.flush()

    if event_count > 0:
        # Save the file
        # add attributes
        h5file.root.events.eventTable.flush()  # if you don't flush before adding attributes,
        # PyTables might print a warning
        h5file.root.events.eventTable.attrs.sample_rate = sample_rate
        h5file.root.events.eventTable.attrs.eventCount = event_count
        h5file.root.events.eventTable.attrs.dataFilename = reader.get_filename_c()
        h5file.flush()
        h5file.close()
        return save_file_name
    else:
        # if no events, just delete the file.
        h5file.flush()
        h5file.close()
        os.remove(save_file_name)

    return None

cdef class Parameters:
    """
    Parameter object to pass to :py:func:`find_events`. Defines the following:

    * min_event_length -- Minimum event length to count as an event [us].
    * max_event_length -- Maximum event length to count as an event [us].
    * detect_positive_events -- Whether to detect events where the current increases.
    * detect_negative_events -- Whether to detect events where the current decreases.
    * baseline_strategy -- Strategy for keeping track of the baseline current. See \
      :py:class:`BaselineStrategy` for a definition of methods and \
      :py:class:`AdaptiveBaselineStrategy` as an example implementation of an adaptive baseline.
    * threshold_strategy -- Strategy for the thresholds deciding the start and end of \
      an event. See :py:class:`ThresholdStrategy` for a definition of the methods and \
      :py:class:`NoiseBasedThresholdStrategy` for an example implementation.

    Usage:

    >>> from pypore.strategies.adaptive_baseline_strategy import AdaptiveBaselineStrategy    >>> from pypore.event_finder import Parameters
    >>> from pypore.event_finder import find_events
    >>> params = Parameters(baseline_strategy=AdaptiveBaselineStrategy(filter_parameter=0.93))
    >>> event_database_filenames = find_events(['test.log'], parameters=params)

    """

    cdef public double min_event_length
    cdef public double max_event_length
    cdef public BaselineStrategy baseline_strategy
    cdef public ThresholdStrategy threshold_strategy
    cdef public bool detect_positive_events
    cdef public bool detect_negative_events

    def __init__(self, min_event_length=10., max_event_length=1.e4,
                 detect_positive_events=True, detect_negative_events=True,
                 baseline_strategy=AdaptiveBaselineStrategy(),
                 threshold_strategy=NoiseBasedThresholdStrategy()):
        """
        Initialize the Parameters object.

        :param double min_event_length: Minimum event length in microseconds. Default is 10.0.
        :param double max_event_length: Maximum event length in microseconds. Default is 1.e4.
        :param bool detect_positive_events: Event finder should look for events where the current increases.\
            Default is True.
        :param bool detect_negative_events: Event finder should look for events where the current decreases.\
            Default is True.
        :param baseline_strategy: Type of the baseline. Default is :py:class:`AdaptiveBaselineStrategy`.\
            Note that this needs to be a subclass of :py:class:`BaselineStrategy`.
        :param threshold_strategy: Type of the threshold for beginning and end to an event.\
            Default is :py:class:`NoiseBasedThresholdStrategy`.\
            Note that this must be a subclass of :py:class:`ThresholdStrategy`.
        """
        self.min_event_length = min_event_length
        self.max_event_length = max_event_length
        self.detect_positive_events = detect_positive_events
        self.detect_negative_events = detect_negative_events
        self.baseline_strategy = baseline_strategy
        self.threshold_strategy = threshold_strategy

def find_events(data, parameters=Parameters(), h5file=None, save_file_names=None, pipe=None):
    """

    :param data: List of data to search. Each item in the list can be one of the following:

        #. An already opened reader. A subclass of :py:class:`pypore.io.abstract_reader.AbstractReader`.\
           For example, a :py:class:`pypore.io.chimera_reader.ChimeraReader`.
        #. A string filename to be opened. The appropriate reader will be chosen based on the file extension.

    :param pipe: (Optional) :py:class:`multiprocessing.Pipe` for status updates during the run.\
        If omitted, status updates will just be printed to standard output.
    :param h5file: (Optional) An already opened :py:func:`pypore.filetypes.event_database.EventDatabase`. \
        If left out, a new EventDatabase will be created.
    :param [string] save_file_names: (Optional) List of names for the output data. If omitted, \
        appropriate save file names will be generated.
    :param Parameters parameters: :py:class:`Parameters` for event finding.
    :returns: List of String file names of the created EventDatabases.

    >>> file_names = ['tests/testDataFiles/chimera_1event.log']
    >>> output_files = find_events(file_names)
    >>> # .... ....
    >>> output_files2 = find_events(file_names, parameters=Parameters(min_event_length=15.))
    """
    event_databases = []
    save_file_name = None
    reader = None
    for i, reader in enumerate(data):
        if save_file_names is not None:
            save_file_name = save_file_names[i]
        if not isinstance(reader, AbstractReader):
            # If not already a reader, assume it is a string filename and create a reader.
            reader = get_reader_from_filename(reader)
        database_filename = _lazy_load_find_events(reader, parameters, pipe, h5file, save_file_name)
        print database_filename
        if database_filename is not None:
            event_databases.append(database_filename)
    return event_databases
