'''
Created on Aug 19, 2013

@author: parkin
'''

import time, datetime
import numpy as np
cimport numpy as np
from pypore.DataFileOpener import prepareDataFile, getNextBlocks
from itertools import chain
import sys
from libc.math cimport sqrt, pow, fmax, fmin

# Threshold types
cdef int THRESHOLD_NOISE_BASED = 0
cdef int THRESHOLD_ABSOLUTE_CHANGE = 1
cdef int THRESHOLD_PERCENTAGE_CHANGE = 2

# Baseline types
cdef int BASELINE_ADAPTIVE = 3
cdef int BASELINE_FIXED = 4

DTYPE = np.double
ctypedef np.double_t DTYPE_t

cdef _getDataRange(dataCache, long i, long n):
    '''
    returns [i,n)
    '''
    cdef np.ndarray[DTYPE_t] res = np.zeros(n - i, dtype = DTYPE)
    cdef long resspot =0, l, nn
    # do we need to include points from the old data
    # (eg. for raw event points)
    if i < 0:
        l = len(dataCache[0])
        # Is the range totally within the old data
        if n <= 0:
            res = dataCache[0][l + i:l + n]
            return res
        res[0:-i] = dataCache[0][l + i:l]
        resspot -= i
        i = 0
    cdef long spot = 0
    cdef np.ndarray[DTYPE_t] cache
    for q in xrange(len(dataCache) - 1):
        cache = dataCache[q + 1]
        nn = cache.size
        # if all the rest of the data is in this cache
        # add it to the end of the result and return
        if i >= spot and n <= spot + nn:
            res[resspot:] = cache[i - spot:n - spot]
            break
        # else we must need to visit more caches
        elif i < spot + nn:
            res[resspot:resspot + nn - (i - spot)] = cache[i - spot:]
            resspot += nn - (i-spot)
            i = spot + nn
        spot += nn
    return res
        
        
def _lazyLoadFindEvents(signal = None, save_file = None, **parameters):
    cdef int event_count = 0
    
    cdef int get_blocks = 1
    
    cdef int raw_points_per_side = 50
    
    if save_file is None:
        save_file = {}
    if not 'Events' in save_file:
        save_file['Events'] = []
    
    # IMPLEMENT ME pleasE
    f, params = prepareDataFile(parameters['filename'])
    
    cdef double sample_rate = params['sample_rate']
    cdef double timestep = 1. / sample_rate
    # Min and Max number of points in an event
    cdef int min_event_steps = np.ceil(parameters['min_event_length'] * 1e-6 / timestep)
    cdef int max_event_steps = np.ceil(parameters['max_event_length'] * 1e-6 / timestep)
    cdef long points_per_channel_total = params['points_per_channel_total']
    
    # Threshold direction.  -1 for negative, 0 for both, +1 for positive
    directionPositive = False
    directionNegative = False
    if parameters['threshold_direction'] == 'Positive':
        directionPositive = True
    elif parameters['threshold_direction'] == 'Negative':
        directionNegative = True
    elif parameters['threshold_direction'] == 'Both':
        directionNegative = True
        directionPositive = True
        
    # allocate memory for data
    datax, _ = getNextBlocks(f, params, get_blocks)
    cdef np.ndarray[DTYPE_t] data = datax[0]  # only get channel 1
    del datax
    
    cdef long n = data.size
    
    if n < 100:
        print 'Not enough datapoints in file.'
        return 'Not enough datapoints in file.'
    
    cdef double datapoint = data[0]
    
    cdef double local_mean = datapoint
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
        threshold_end = datapoint
        threshold_type = THRESHOLD_NOISE_BASED
    
    dataCache = [np.zeros(n, dtype = DTYPE) + datapoint, data]
    
    cdef long i = 0
    cdef long prevI = 0
    cdef double time1 = time.time()
    cdef double time2 = time1
    cdef long event_start = 0
    cdef long event_end = 0
    isEvent = False
    wasEventPositive = False  # Was the event an up spike?
    cdef long placeInData = 0
    
    cdef double mean_estimate = 0.0
    cdef double sn = 0
    cdef double sp = 0
    cdef double Sn = 0
    cdef double Sp = 0
    cdef double Gn = 0
    cdef double Gp = 0
    cdef double new_mean = 0
    cdef double var_estimate = 0
    cdef int n_levels = 0
    cdef double delta = 0
    cdef long min_index_p = 0
    cdef long min_index_n = 0
    cdef double min_Sp = float("inf")
    cdef double min_Sn = float("inf")
    cdef long ko = i
    cdef double event_area = datapoint - local_mean  # integrate the area
    cdef int cache_index = 0
    cdef int size = 0
    cdef double h = 0
    cdef long cache_refreshes = 0 #number of times we get new data at the
                                    # end of the loop
    
    cdef np.ndarray[DTYPE_t] level_values
    
    # search for events.  Keep track of filter_parameter filtered local (adapting!) mean and variance,
    # and use them to decide filter_parameter threshold_start for events.  See
    # http://pubs.rsc.org/en/content/articlehtml/2012/nr/c2nr30951c for more details.
    while i < n:
        if signal is not None and i%1000 == 0:
            time.sleep(0)# way to yield to other threads. Allows the gui
                                # to remain responsive. Note this obviously 
                                # lowers the samples/s rate.
        datapoint = dataCache[1][i]
        if threshold_type == THRESHOLD_NOISE_BASED:
            threshold_start = start_stddev * sqrt(local_variance) 
        
        # could this be an event?
        if threshold_type == THRESHOLD_PERCENTAGE_CHANGE:
            threshold_start = local_mean * parameters['percent_change_start'] / 100.
        # Detecting a negative event
        if (directionNegative and datapoint < local_mean - threshold_start):
            isEvent = True
            wasEventPositive = False
        # Detecting a positive event
        elif (directionPositive and datapoint > local_mean + threshold_start):
            isEvent = True
            wasEventPositive = True
        if isEvent:
            isEvent = False
            # Set ending threshold_end
            if threshold_type == THRESHOLD_NOISE_BASED:
                threshold_end = end_stddev * sqrt(local_variance) 
            elif threshold_type == THRESHOLD_PERCENTAGE_CHANGE:
                threshold_end = local_mean * parameters['percent_change_end'] / 100.
            event_start = i
            event_end = i + 1
            done = False
            event_i = i
            # CUSUM stuff
            mean_estimate = datapoint
            level_indexes = [event_start]  # The indexes in data[] where each
                                            # level starts.
            sn = sp = Sn = Sp = Gn = Gp = 0
            var_estimate = local_variance
            n_levels = 1  # We're already starting with one level
            delta = np.absolute(mean_estimate - local_mean) / 10.
            min_index_p = min_index_n = i
            min_Sp = min_Sn = 999999
            ko = i
            event_area = datapoint - local_mean  # integrate the area
            
            # loop until event ends
            while not done and event_i - event_start < max_event_steps:
                if signal is not None and event_i %1000 == 0:
                    time.sleep(0) # way to yield to other threads. Allows the gui
                                    # to remain responsive. Note this obviously 
                                    # lowers the samples/s rate.
                event_i = event_i + 1
                if event_i % n == 0:  # We may need new data
                    size = 0
                    cache_index = 1  # which index in the cache is event_i
                                    # trying to grab data from?
                    for qq in xrange(len(dataCache) - 1):
                        size += dataCache[qq + 1].size
                        if event_i >= size:
                            cache_index += 1
                    # we need new data if we've run out
                    if event_i >= size:
                        datas, _ = getNextBlocks(f, params, get_blocks)
                        datas = datas[0]
                        n = datas.size
                        if n < 1:
                            i = n
                            print "Done"
                            break
                        dataCache.append(datas)
                    else:
                        n = dataCache[cache_index].size
                datapoint = dataCache[int(1.*event_i / n) + 1][event_i % n]
                if (not wasEventPositive and datapoint >= local_mean - threshold_end) or (wasEventPositive and datapoint <= local_mean + threshold_end):
                    event_end = event_i
                    done = True
                    break
                event_area = event_area + datapoint - local_mean
                # new mean = old_mean + (new_sample - old_mean)/(N)
                new_mean = mean_estimate + (datapoint - mean_estimate) / (1 + event_i - ko)
                # New variance recursion relation 
                var_estimate = ((event_i - ko) * var_estimate + (datapoint - mean_estimate) * (datapoint - new_mean)) / (1 + event_i - ko)
                mean_estimate = new_mean
                if var_estimate > 0:
                    sp = (delta / var_estimate) * (datapoint - mean_estimate - delta / 2)
                    sn = -(delta / var_estimate) * (datapoint - mean_estimate + delta / 2)
                elif delta == 0:
                    sp = sn = 0
                else:
                    sp = sn = float('inf')
                Sp = Sp + sp
                Sn = Sn + sn
                Gp = fmax(0.0, Gp + sp)
                Gn = fmax(0.0, Gn + sn)
                if Sp <= min_Sp:
                    min_Sp = Sp
                    min_index_p = event_i
                if Sn <= min_Sn:
                    min_Sn = Sn
                    min_index_n = event_i
                h = delta / sqrt(var_estimate)
                # Did we detect a change?
                if Gp > h or Gn > h:
                    minindex = min_index_n
                    if Gp > h:
                        minindex = min_index_p
                    level_indexes.append(minindex)
                    n_levels += 1
                    # reset stuff
                    mean_estimate = dataCache[int(1.*minindex / n) + 1][minindex % n]
                    sn = sp = Sn = Sp = Gn = Gp = 0
                    min_Sp = min_Sn = float("inf")
                    # Go back to 1 after the level change found
                    ko = event_i = minindex
                    min_index_p = min_index_n = event_i
                  
            i = event_end
            level_indexes.append(event_end)
            # is the event long enough?
            if done and event_end - event_start > min_event_steps:
                # CUSUM stuff
                # is there enough for multiple levels?
                if event_end - event_start > 10:
                    level_values = np.zeros(n_levels, DTYPE)  # Holds the current values of the level_values
                    for q in xrange(0, n_levels):
                        start_index = level_indexes[q]
                        end_index = level_indexes[q + 1]
                        level_values[q] = np.mean(_getDataRange(dataCache, start_index, end_index))
                # otherwise just say 1 level and use the maximum change as the value
                else:
                    level_values = np.zeros(1, DTYPE)
                    if wasEventPositive:
                        level_values += np.max(_getDataRange(dataCache, event_start, event_end))
                    else:
                        level_values += np.min(_getDataRange(dataCache, event_start, event_end))
                    level_indexes = [event_start, event_end]
                    
                for j, level_index in enumerate(level_indexes):
                        level_indexes[j] = level_index + placeInData
                # end CUSUM
                event = {}
                event['event_data'] = _getDataRange(dataCache, event_start, event_end)
                event['raw_data'] = _getDataRange(dataCache, event_start - raw_points_per_side, event_end + raw_points_per_side)
                event['baseline'] = local_mean
                event['current_blockage'] = np.mean(event['event_data']) - local_mean
                event['event_start'] = event_start + placeInData
                event['event_end'] = event_end + placeInData
                event['raw_points_per_side'] = raw_points_per_side
                event['sample_rate'] = sample_rate
                event['cusum_indexes'] = level_indexes
                event['cusum_values'] = level_values
                event['area'] = event_area
                save_file['Events'].append(event)
                event_count = event_count + 1
        
        
        local_mean = filter_parameter * local_mean + (1 - filter_parameter) * datapoint
        local_variance = filter_parameter * local_variance + (1 - filter_parameter) * pow(datapoint - local_mean, 2)
        i += 1
        # remove any arrays in the cache that we dont need anymore
        while i >= n and n > 0:
            del dataCache[0]
            i -= n
            placeInData += n
            # If we're just left with dataCache[0], which is reserved
            # for old data, then we need new data.
            if len(dataCache) < 2:
                cache_refreshes += 1
                datanext, _ = getNextBlocks(f, params, get_blocks)
                data = datanext[0]
                dataCache.append(data)
            if len(dataCache) > 1:
                n = dataCache[1].size
            if cache_refreshes % 100 == 0:
                recent_time = time.time() - time2
                total_time = time.time() - time1
                if signal is not None:
                    signal.emit({'status_text': 'Event Count: ' + str(event_count) + ' Percent Done: ' + str(100.*placeInData / points_per_channel_total) + ' Rate: ' + str((placeInData-prevI)/recent_time) + ' samples/s' + ' Total Rate:' + str(placeInData/total_time) + ' samples/s'})
                else:
                    sys.stdout.write("\rEvent Count: %d  rate: %f" % (event_count, placeInData / total_time))
                    sys.stdout.flush()
                time2 = time.time()
                prevI = placeInData
        if i == 0:
            if 'cancelled' in save_file:
                print 'cancelled'
                return {'error': 'Cancelled'}
            
    if event_count > 0:
        save_file_name = list(parameters['filename'])
        # Remove the .mat off the end
        for i in xrange(0, 4):
            save_file_name.pop()
            
        # Get a string with the current year/month/day/hour/minute to label the file
        day_time = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        save_file_name.append('_Events_' + day_time + '.npy')
        save_file_name = "".join(save_file_name)
        save_file['filename'] = parameters['filename']
        save_file['database_filename'] = save_file_name
        save_file['sample_rate'] = sample_rate
        save_file['event_count'] = event_count
        # save the user's analysis parameters
        parameters.pop('axes', None)  # remove the axes before saving.
        save_file['parameters'] = parameters
#         sio.savemat(save_file_name, save_file, oned_as='row')
        np.save(save_file_name, save_file)
        
#         dataReady.emit({'status_text': 'Done. Found ' + str(event_count) + ' events.  Saved database to ' + str(save_file['filename']), 'done': True})
    
    return save_file
    
def findEvents(signal = None, save_file = None, **parameters):
    defaultParams = { 'min_event_length': 10.,
                                   'max_event_length': 10000.,
                                   'threshold_direction': 'Negative',
                                   'filter_parameter': 0.93,
                                   'threshold_type': 'Noise Based',
                                   'start_stddev': 5.,
                                   'end_stddev': 1.}
    # do a union of defaultParams and parameters, keeping the
    # parameters entries on conflict.
    params = dict(chain(defaultParams.iteritems(), parameters.iteritems()))
    return _lazyLoadFindEvents(signal, save_file, **params)
