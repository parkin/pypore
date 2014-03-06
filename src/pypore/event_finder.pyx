"""
Created on Aug 19, 2013

@author: parkin1
"""
#cython: embedsignature=True

import os
import time, datetime
import numpy as np
cimport numpy as np
import filetypes.event_database as ed
from pypore.data_file_opener import prepare_data_file, get_next_blocks
from itertools import chain
import sys
from libc.math cimport sqrt, pow, fmax, fmin, abs

# Threshold types
cdef int THRESHOLD_NOISE_BASED = 0
cdef int THRESHOLD_ABSOLUTE_CHANGE = 1
cdef int THRESHOLD_PERCENTAGE_CHANGE = 2

# Baseline types
cdef int BASELINE_ADAPTIVE = 3
cdef int BASELINE_FIXED = 4

DTYPE = np.float
ctypedef np.float_t DTYPE_t

DTYPE_UINT32 = np.uint32
ctypedef np.uint32_t DTYPE_UINT32_t

cpdef np.ndarray[DTYPE_t] _get_data_range(data_cache, long i, long n):
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
    Just a wrapper so the python unittests can call _getDataRange
    """
    return _get_data_range(data_cache, i, n)
        
cpdef _lazy_load_find_events(filename, parameters, pipe=None, h5file=None, save_file_name=None):
    cdef unsigned int event_count = 0
    
    cdef unsigned int get_blocks = 1
    
    cdef unsigned int raw_points_per_side = 50
    
    # IMPLEMENT ME pleasE
    f, params = prepare_data_file(filename)

    cdef double sample_rate = params['sample_rate']
    cdef double time_step = 1. / sample_rate
    # Min and Max number of points in an event
    cdef unsigned int min_event_steps = np.ceil(parameters['min_event_length'] * 1e-6 / time_step)
    cdef unsigned int max_event_steps = np.ceil(parameters['max_event_length'] * 1e-6 / time_step)
    cdef long points_per_channel_total = params['points_per_channel_total']
    
    # Threshold direction.  -1 for negative, 0 for both, +1 for positive
    direction_positive = False
    direction_negative = False
    if parameters['threshold_direction'] == 'Positive':
        direction_positive = True
    elif parameters['threshold_direction'] == 'Negative':
        direction_negative = True
    elif parameters['threshold_direction'] == 'Both':
        direction_negative = True
        direction_positive = True
        
    # allocate memory for data
    data_x = get_next_blocks(f, params, get_blocks)
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
        save_file_name = list(filename)
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
        h5file = ed.open_file(save_file_name, maxEventLength = max_points, mode='w')
    raw_data = h5file.root.events.rawData
    levels_matrix = h5file.root.events.levels
    lengths_matrix = h5file.root.events.levelLengths
    
    cdef double data_point = data[0]
    
    cdef double local_mean = data_point
    cdef double local_variance = 0.
    
    cdef double filter_parameter = parameters['filter_parameter']  # filter parameter 'a'
    
    cdef double threshold_start = 0.0
    cdef double threshold_end = 0.0
    cdef int threshold_type = THRESHOLD_ABSOLUTE_CHANGE
    cdef double start_stddev = 0.0
    cdef double end_stddev = 0.0
    if parameters['threshold_type'] == 'Absolute Change':
        threshold_start = parameters['absolute_change_start']
        threshold_end = parameters['absolute_change_end']
        threshold_type = THRESHOLD_ABSOLUTE_CHANGE
    elif parameters['threshold_type'] == 'Percent Change':
        
        threshold_type = THRESHOLD_PERCENTAGE_CHANGE
    else:  # noise based
        start_stddev = parameters['start_stddev']  # Starting threshold_start parameter
        end_stddev = parameters['end_stddev']  # Ending threshold_start parameter
        
        initialization_index = 100
            
        local_mean = np.mean(data[0:initialization_index])
        local_variance = np.var(data[0:initialization_index])

        # distance from mean to define an event.  noise based unless otherwise chosen.
        threshold_start = start_stddev * sqrt(local_variance)
        threshold_end = data_point
        threshold_type = THRESHOLD_NOISE_BASED
    
    data_cache = [np.zeros(n, dtype=DTYPE) + data_point, data]
    
    is_event = False
    was_event_positive = False  # Was the event an up spike?
    
    # Figure out how many rows will it take to have a cache of 10MB (1048576 bytes = 1MB)
    cdef num_rows_in_event_cache = int(10 * 1048576 / (max_points * (np.dtype(DTYPE).itemsize)))
    # Make an array to hold events in memory before writing to disk.
    cdef np.ndarray[DTYPE_t, ndim = 2] event_cache = np.zeros((num_rows_in_event_cache, max_points), dtype=DTYPE)
    cdef np.ndarray[DTYPE_t, ndim = 2] levels_cache = np.zeros((num_rows_in_event_cache, max_points), dtype=DTYPE)
    cdef np.ndarray[DTYPE_UINT32_t, ndim = 2] level_length_cache = np.zeros((num_rows_in_event_cache, max_points), dtype=DTYPE_UINT32)
    
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
        double event_area = data_point - local_mean  # integrate the area
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
        double percent_change_start = 0
        double percent_change_end = 0
        double temp = 0
        long temp_long = 0
        
#         np.ndarray[DTYPE_t] level_values
        np.ndarray[DTYPE_t] curr_data = data_cache[1]  # data in dataCache[1]
        
        np.ndarray[DTYPE_t] m_levels = np.zeros(max_points, dtype=DTYPE)
        np.ndarray[DTYPE_UINT32_t] m_levels_length = np.zeros(max_points, dtype=DTYPE_UINT32)
        
        double level_sum = 0
        long prev_level_start = 0
        
        int last_event_sent = 0
        
    if 'percent_change_start' in parameters:
        percent_change_start = parameters['percent_change_start']
    if 'percent_change_end' in parameters:
        percent_change_end = parameters['percent_change_end']
    
    # search for events.  Keep track of filter_parameter filtered local (adapting!) mean and variance,
    # and use them to decide filter_parameter threshold_start for events.  See
    # http://pubs.rsc.org/en/content/articlehtml/2012/nr/c2nr30951c for more details.
    while i < n:
        data_point = curr_data[i]
        if threshold_type == THRESHOLD_NOISE_BASED:
            threshold_start = start_stddev * sqrt(local_variance) 
        elif threshold_type == THRESHOLD_PERCENTAGE_CHANGE:
            threshold_start = local_mean * percent_change_start / 100.
            
        # Detecting a negative event
        if direction_negative and data_point < local_mean - threshold_start:
            is_event = True
            was_event_positive = False
        # Detecting a positive event
        elif direction_positive and data_point > local_mean + threshold_start:
            is_event = True
            was_event_positive = True
        if is_event:
            is_event = False
            # Set ending threshold_end
            if threshold_type == THRESHOLD_NOISE_BASED:
                threshold_end = end_stddev * sqrt(local_variance) 
            elif threshold_type == THRESHOLD_PERCENTAGE_CHANGE:
                threshold_end = local_mean * percent_change_end / 100.
            event_start = i
            event_end = i + 1
            done = False
            event_i = i
            # CUSUM stuff
            mean_estimate = data_point
            n_levels = 0
            sn = sp = Sn = Sp = Gn = Gp = 0
            var_estimate = local_variance
#             n_levels = 1  # We're already starting with one level
            delta = abs(mean_estimate - local_mean) / 2.
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
                    datas = get_next_blocks(f, params, get_blocks)
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
                if (not was_event_positive and data_point >= local_mean - threshold_end) or (was_event_positive and data_point <= local_mean + threshold_end):
                    event_end = event_i
                    done = True
                    break
                # new mean = old_mean + (new_sample - old_mean)/(N)
                new_mean = mean_estimate + (data_point - mean_estimate) / (1 + event_i - ko)
                # New variance recursion relation 
                var_estimate = ((event_i - ko) * var_estimate + (data_point - mean_estimate) * (data_point - new_mean)) / (1 + event_i - ko)
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
                    m_levels[n_levels] = level_sum / m_levels_length[n_levels] ##
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
                        current_blockage -= local_mean
                    else:
                        current_blockage = np.min(_get_data_range(data_cache, event_start, event_end))
                        m_levels[0] = current_blockage
                        current_blockage -= local_mean
                    m_levels_length[0] = event_end - event_start
                else:
                    current_blockage = 0
                    # calculate the weighted average of the levels
                    for qq in xrange(n_levels):
                        current_blockage += m_levels[qq] * m_levels_length[qq]
                    current_blockage = current_blockage / (event_end - event_start) - local_mean
                    
                # end CUSUM, save events to file/cache
                h5file.append_event(event_count, event_start + place_in_data, event_end - event_start,\
                                   n_levels, raw_points_per_side, local_mean, current_blockage,\
                                   event_area - local_mean)
                
                event_cache[event_cache_index][:event_end - event_start + 2 * raw_points_per_side] = _get_data_range(data_cache, event_start - raw_points_per_side, event_end + raw_points_per_side)
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
        
        
        local_mean = filter_parameter * local_mean + (1 - filter_parameter) * data_point
        local_variance = filter_parameter * local_variance + (1 - filter_parameter) * pow(data_point - local_mean, 2)
        i += 1
        # remove any arrays in the cache that we dont need anymore
        while 0 < n <= i:
            del data_cache[0]
            i -= n
            place_in_data += n
            # If we're just left with dataCache[0], which is reserved
            # for old data, then we need new data.
            if len(data_cache) < 2:
                cache_refreshes += 1
                data_next = get_next_blocks(f, params, get_blocks)
                data_cache.append(data_next[0])
            if len(data_cache) > 1:
                curr_data = data_cache[1]
                n = curr_data.size
            if cache_refreshes % 100 == 0 and len(data_cache) == 2:
                time_temp = time.time()
                recent_time = time_temp - time2
                if recent_time > 0:
                    total_time = time_temp - time1
                    percent_done = 100.*(place_in_data + i) / points_per_channel_total
                    rate = (place_in_data + i - prev_i) / recent_time
                    total_rate = (place_in_data + i) / total_time
                    time_left = int((points_per_channel_total - (place_in_data + i)) / rate)
                    status_text = "Event Count: %d Percent Done: %.2f Rate: %.2e pt/s Total Rate: %.2e pt/s Time Left: %s" % (event_count, percent_done, rate, total_rate, datetime.timedelta(seconds=time_left))
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
    percent_done = 100.*(place_in_data + i) / points_per_channel_total
    rate = (place_in_data + i - prev_i) / recent_time
    total_rate = (place_in_data + i) / total_time
    time_left = int((points_per_channel_total - (place_in_data + i)) / rate)
    status_text = "Event Count: %d Percent Done: %.2f Rate: %.2e pt/s Total Rate: %.2e pt/s Time Left: %s" % (event_count, percent_done, rate, total_rate, datetime.timedelta(seconds=time_left))
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
        h5file.root.events.eventTable.attrs.sampleRate = sample_rate
        h5file.root.events.eventTable.attrs.eventCount = event_count
        h5file.root.events.eventTable.attrs.dataFilename = filename
        h5file.flush()
        h5file.close()
        return save_file_name
    else:
        # if no events, just delete the file.
        h5file.flush()
        h5file.close()
        os.remove(save_file_name)
        
    return None
    
def find_events(file_names, pipe=None, h5file=None, save_file_names = None, **parameters):
    default_params = { 'min_event_length': 10.,
                                   'max_event_length': 10000.,
                                   'threshold_direction': 'Negative',
                                   'filter_parameter': 0.93,
                                   'threshold_type': 'Noise Based',
                                   'start_stddev': 5.,
                                   'end_stddev': 1.}
    # do a union of defaultParams and parameters, keeping the
    # parameters entries on conflict.
    params = dict(chain(default_params.iteritems(), parameters.iteritems()))
    event_databases = []
    save_file_name = None
    for i, filename in enumerate(file_names):
        if save_file_names is not None:
            save_file_name = save_file_names[i]
        database_filename = _lazy_load_find_events(filename, params, pipe, h5file, save_file_name)
        print database_filename
        if database_filename is not None:
            event_databases.append(database_filename)
    return event_databases
