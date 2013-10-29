'''
Created on Aug 19, 2013

@author: parkin
'''

import os
import time, datetime
import numpy as np
cimport numpy as np
from pypore.eventDatabase import initializeEventsDatabase
from pypore.DataFileOpener import prepareDataFile, getNextBlocks
from pypore.eventDatabase import initializeEventsDatabase
from itertools import chain
import sys
from libc.math cimport sqrt, pow, fmax, fmin, abs
import tables as tb

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

cdef np.ndarray[DTYPE_t] _getDataRange(dataCache, long i, long n):
    '''
    returns [i,n)
    '''
    cdef np.ndarray[DTYPE_t,
                    negative_indices = False,
                    mode = 'c'] res = np.zeros(n - i, dtype=DTYPE)
    cdef long resspot = 0, l, nn
    # do we need to include points from the old data
    # (eg. for raw event points)
    if i < 0:
        l = dataCache[0].size
        # Is the range totally within the old data
        if n <= 0:
            res = dataCache[0][l + i:l + n]
            return res
        res[0:-i] = dataCache[0][l + i:l]
        resspot -= i
        i = 0
    cdef long spot = 0
    cdef np.ndarray[DTYPE_t] cache
    cdef int q = 0
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
            resspot += nn - (i - spot)
            i = spot + nn
        spot += nn
    return res

cpdef np.ndarray[DTYPE_t] _getDataRangeTestWrapper(dataCache, long i, long n):
    '''
    Just a wrapper so the python unittests can call _getDataRange
    '''
    return _getDataRange(dataCache, i, n)
        
cdef _lazyLoadFindEvents(filename, parameters, pipe=None, h5file=None):
    cdef unsigned int event_count = 0
    
    cdef unsigned int get_blocks = 1
    
    cdef unsigned int raw_points_per_side = 50
    
    # IMPLEMENT ME pleasE
    f, params = prepareDataFile(filename)
    
    cdef double sample_rate = params['sample_rate']
    cdef double timestep = 1. / sample_rate
    # Min and Max number of points in an event
    cdef unsigned int min_event_steps = np.ceil(parameters['min_event_length'] * 1e-6 / timestep)
    cdef unsigned int max_event_steps = np.ceil(parameters['max_event_length'] * 1e-6 / timestep)
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
    datax = getNextBlocks(f, params, get_blocks)
    cdef np.ndarray[DTYPE_t] data = datax[0]  # only get channel 1
    del datax
    
    cdef unsigned long n = data.size
    
    if n < 100:
        print 'Not enough datapoints in file.'
        if pipe is not None:
            pipe.close()
        return 'Not enough datapoints in file.'
    
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
    
    cdef unsigned long maxPoints = max_event_steps + 2 * raw_points_per_side
    
    # Open the event datbase
    if h5file == None:
        h5file = initializeEventsDatabase(save_file_name, maxPoints)
    rawData = h5file.root.events.rawData
    eventEntry = h5file.root.events.eventTable.row
    levelsMatrix = h5file.root.events.levels
    lengthsMatrix = h5file.root.events.levelLengths
    
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
    
    dataCache = [np.zeros(n, dtype=DTYPE) + datapoint, data]
    
    isEvent = False
    wasEventPositive = False  # Was the event an up spike?
    
    # Figure out how many rows will it take to have a cache of 10MB (1048576 bytes = 1MB)
    cdef numRowsInEventCache = int(10 * 1048576 / (maxPoints * (np.dtype(DTYPE).itemsize)))
    # Make an array to hold events in memory before writing to disk.
    cdef np.ndarray[DTYPE_t, ndim = 2] eventCache = np.zeros((numRowsInEventCache, maxPoints), dtype=DTYPE)
    cdef np.ndarray[DTYPE_t, ndim = 2] levelsCache = np.zeros((numRowsInEventCache, maxPoints), dtype=DTYPE)
    cdef np.ndarray[DTYPE_UINT32_t, ndim = 2] levelLengthCache = np.zeros((numRowsInEventCache, maxPoints), dtype=DTYPE_UINT32)
    
    cdef eventCacheIndex = 0
    
    cdef:
    
        unsigned long i = 0
        unsigned long event_i = 0
        unsigned long minindex = 0
        unsigned long prevI = 0
        double time1 = time.time()
        double time2 = time1
        double timetemp = 0
        unsigned long event_start = 0
        unsigned long event_end = 0
        unsigned long start_index = 0
        unsigned long end_index = 0
        unsigned long placeInData = 0
        
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
        double min_Sp = float("inf")
        double min_Sn = float("inf")
        long ko = i
        double event_area = datapoint - local_mean  # integrate the area
        double currentBlockage = 0
        int cache_index = 0
        unsigned int size = 0
        double h = 0
        double percent_done = 0
        double rate = 0
        double total_rate = 0
        int time_left = 0
        int qq = 0
        int cacheSize = 0
        long cache_refreshes = 0  # number of times we get new data at the
                                        # end of the loop
        double percent_change_start = 0
        double percent_change_end = 0
        double temp = 0
        long tempLong = 0
        
#         np.ndarray[DTYPE_t] level_values
        np.ndarray[DTYPE_t] currData = dataCache[1]  # data in dataCache[1]
        
        np.ndarray[DTYPE_t] mlevels = np.zeros(maxPoints, dtype=DTYPE)
        np.ndarray[DTYPE_UINT32_t] mlevelsLength = np.zeros(maxPoints, dtype=DTYPE_UINT32)
        
        double level_sum = 0
        long prevLevelStart = 0
        
        int last_event_sent = 0
        
    if 'percent_change_start' in parameters:
        percent_change_start = parameters['percent_change_start']
    if 'percent_change_end' in parameters:
        percent_change_end = parameters['percent_change_end']
    
    # search for events.  Keep track of filter_parameter filtered local (adapting!) mean and variance,
    # and use them to decide filter_parameter threshold_start for events.  See
    # http://pubs.rsc.org/en/content/articlehtml/2012/nr/c2nr30951c for more details.
    while i < n:
        datapoint = currData[i]
        if threshold_type == THRESHOLD_NOISE_BASED:
            threshold_start = start_stddev * sqrt(local_variance) 
        elif threshold_type == THRESHOLD_PERCENTAGE_CHANGE:
            threshold_start = local_mean * percent_change_start / 100.
            
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
                threshold_end = local_mean * percent_change_end / 100.
            event_start = i
            event_end = i + 1
            done = False
            event_i = i
            # CUSUM stuff
            mean_estimate = datapoint
            n_levels = 0
            sn = sp = Sn = Sp = Gn = Gp = 0
            var_estimate = local_variance
#             n_levels = 1  # We're already starting with one level
            delta = abs(mean_estimate - local_mean) / 2.
            min_index_p = min_index_n = i
            min_Sp = min_Sn = 999999
            ko = i
            event_area = datapoint  # integrate the area
            cache_index = 1  # which index in the cache is event_i
                                    # trying to grab data from?
                                    
            level_sum = datapoint
            level_sum_minp = 0.
            level_sum_minn = 0.
            prevLevelStart = event_i
            cacheSize = n
            
            # loop until event ends
            while not done and event_i - event_start < max_event_steps:
                event_i = event_i + 1
                if event_i >= cacheSize:  # We may need new data
                    # we need new data if we've run out
                    cache_index += 1
                    datas = getNextBlocks(f, params, get_blocks)
                    datas = datas[0]
                    n = datas.size
                    cacheSize += n
                    if n < 1:
                        i = n
                        print "Done"
                        break
                    dataCache.append(datas)
                if cache_index == 1:
                    datapoint = currData[event_i]
                else:
                    datapoint = dataCache[cache_index][event_i % n]
                if (not wasEventPositive and datapoint >= local_mean - threshold_end) or (wasEventPositive and datapoint <= local_mean + threshold_end):
                    event_end = event_i
                    done = True
                    break
                # new mean = old_mean + (new_sample - old_mean)/(N)
                new_mean = mean_estimate + (datapoint - mean_estimate) / (1 + event_i - ko)
                # New variance recursion relation 
                var_estimate = ((event_i - ko) * var_estimate + (datapoint - mean_estimate) * (datapoint - new_mean)) / (1 + event_i - ko)
                mean_estimate = new_mean
                if var_estimate > 0:
                    sp = (delta / var_estimate) * (datapoint - mean_estimate - delta / 2.)
                    sn = -(delta / var_estimate) * (datapoint - mean_estimate + delta / 2.)
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
                    level_sum_minp = level_sum
                if Sn <= min_Sn:
                    min_Sn = Sn
                    min_index_n = event_i
                    level_sum_minn = level_sum
                level_sum += datapoint
                h = delta / sqrt(var_estimate)
                # Did we detect a change?
                if Gp > h or Gn > h:
                    if Gp > h:
                        minindex = min_index_p
                        level_sum = level_sum_minp
                    else:
                        minindex = min_index_n
                        level_sum = level_sum_minn
                    mlevelsLength[n_levels] = minindex + 1 - ko
                    mlevels[n_levels] = level_sum / (minindex - prevLevelStart)
                    n_levels += 1
                    # reset stuff
                    if cache_index == 1:
                        mean_estimate = currData[event_i]
                    else:
                        mean_estimate = dataCache[cache_index][event_i % n]
                    sn = sp = Sn = Sp = Gn = Gp = 0
                    level_sum = mean_estimate
                    min_Sp = min_Sn = float("inf")
                    # Go back to 1 after the level change found
                    ko = event_i = minindex + 1
                    min_index_p = min_index_n = event_i
                    prevLevelStart = event_i
                  
            i = event_end
            if event_end > prevLevelStart:
                mlevelsLength[n_levels] = event_end - ko
                mlevels[n_levels] = level_sum / (event_end - prevLevelStart)
                n_levels += 1
            # is the event long enough?
            if done and event_end - event_start > min_event_steps:
                # CUSUM stuff
                # otherwise just say 1 level and use the maximum change as the value
                if event_end - event_start < 10:
                    n_levels = 1
                    if wasEventPositive:
                        currentBlockage = np.max(_getDataRange(dataCache, event_start, event_end))
                        mlevels[0] = currentBlockage
                        currentBlockage -= local_mean
                    else:
                        currentBlockage = np.min(_getDataRange(dataCache, event_start, event_end))
                        mlevels[0] = currentBlockage
                        currentBlockage -= local_mean
                    mlevelsLength[0] = event_end - event_start
                else:
                    currentBlockage = 0
                    # calculate the weighted average of the levels
                    for qq in xrange(n_levels):
                        currentBlockage += mlevels[qq] * mlevelsLength[qq]
                    currentBlockage = currentBlockage / (event_end - event_start) - local_mean
                    
                # end CUSUM, save events to file/cache
                eventEntry['baseline'] = local_mean
                eventEntry['currentBlockage'] = currentBlockage
                eventEntry['nLevels'] = n_levels
                eventEntry['eventStart'] = event_start + placeInData
                eventEntry['eventLength'] = event_end - event_start
                eventEntry['rawPointsPerSide'] = raw_points_per_side
                eventEntry['area'] = event_area - local_mean
                eventEntry['arrayRow'] = event_count
                eventEntry.append()
                
                eventCache[eventCacheIndex][:event_end - event_start + 2 * raw_points_per_side] = _getDataRange(dataCache, event_start - raw_points_per_side, event_end + raw_points_per_side)
                levelsCache[eventCacheIndex][:n_levels] = mlevels[:n_levels]
                levelLengthCache[eventCacheIndex][:n_levels] = mlevelsLength[:n_levels]
                
                event_count += 1
                eventCacheIndex += 1
                
                if eventCacheIndex >= numRowsInEventCache:
                    rawData.append(eventCache)
                    lengthsMatrix.append(levelLengthCache)
                    levelsMatrix.append(levelsCache)
                    eventCacheIndex = 0
                    
                if event_count % 1000 == 0:
                    h5file.root.events.eventTable.flush()
                    h5file.flush()
        
        
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
                datanext = getNextBlocks(f, params, get_blocks)
                dataCache.append(datanext[0])
            if len(dataCache) > 1:
                currData = dataCache[1]
                n = currData.size
            if cache_refreshes % 100 == 0 and len(dataCache) == 2:
                timetemp = time.time()
                recent_time = timetemp - time2
                if recent_time > 0:
                    total_time = timetemp - time1
                    percent_done = 100.*(placeInData + i) / points_per_channel_total
                    rate = (placeInData + i - prevI) / recent_time
                    total_rate = (placeInData + i) / total_time
                    time_left = int((points_per_channel_total - (placeInData + i)) / rate)
                    status_text = "Event Count: %d Percent Done: %.2f Rate: %.2e pt/s Total Rate: %.2e pt/s Time Left: %s" % (event_count, percent_done, rate, total_rate, datetime.timedelta(seconds=time_left))
                    if pipe is not None:
            #                     if event_count > last_event_sent:
            #                         pipe.send({'status_text': status_text, 'Events': save_file['Events'][last_event_sent:]})
                        pipe.send({'status_text': status_text})
            #                         last_event_sent = event_count
                    else:
                        sys.stdout.write("\r" + status_text)
                        sys.stdout.flush()
                    time2 = timetemp
                    prevI = placeInData + i
                    
    # clean up the caches, make sure everything is saved
    if eventCacheIndex > 0:
        rawData.append(eventCache[:eventCacheIndex])
        lengthsMatrix.append(levelLengthCache[:eventCacheIndex])
        levelsMatrix.append(levelsCache[:eventCacheIndex])
        eventCacheIndex = 0
                
    # Update the status_text one last time
    recent_time = time.time() - time2
    total_time = time.time() - time1
    percent_done = 100.*(placeInData + i) / points_per_channel_total
    rate = (placeInData + i - prevI) / recent_time
    total_rate = (placeInData + i) / total_time
    time_left = int((points_per_channel_total - (placeInData + i)) / rate)
    status_text = "Event Count: %d Percent Done: %.2f Rate: %.2e pt/s Total Rate: %.2e pt/s Time Left: %s" % (event_count, percent_done, rate, total_rate, datetime.timedelta(seconds=time_left))
    if pipe is not None:
#                     if event_count > last_event_sent:
#                         pipe.send({'status_text': status_text, 'Events': save_file['Events'][last_event_sent:]})
        pipe.send({'status_text': status_text})
#                         last_event_sent = event_count
    else:
        sys.stdout.write("\r" + status_text)
        sys.stdout.flush()
            
#     if event_count > 0:
#         save_file_name = list(parameters['filename'])
#         # Remove the .mat off the end
#         for i in xrange(0, 4):
#             save_file_name.pop()
#             
#         # Get a string with the current year/month/day/hour/minute to label the file
#         day_time = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
#         save_file_name.append('_Events_' + day_time + '.npy')
#         save_file_name = "".join(save_file_name)
#         save_file['filename'] = parameters['filename']
#         save_file['database_filename'] = save_file_name
#         save_file['sample_rate'] = sample_rate
#         save_file['event_count'] = event_count
#         # save the user's analysis parameters
#         parameters.pop('axes', None)  # remove the axes before saving.
#         save_file['parameters'] = parameters
# #         sio.savemat(save_file_name, save_file, oned_as='row')
#         np.save(save_file_name, save_file)

    if event_count > 0:
        # Save the file
        # add attributes
        h5file.root.events.eventTable.flush()  # if you don't flush before adding attributes,
                                                # PyTables might print a warning
        h5file.root.events.eventTable.attrs.sampleRate = sample_rate
        h5file.root.events.eventTable.attrs.eventCount = event_count
        h5file.flush()
        h5file.close()
    else:
        # if no events, just delete the file.
        h5file.flush()
        h5file.close()
        os.remove(save_file_name)
        
    return save_file_name
    
def findEvents(filenames, pipe=None, h5file=None, **parameters):
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
    eventDatabases = []
    for filename in filenames:
        eventDatabases.append(_lazyLoadFindEvents(filename, params, pipe, h5file))
    return eventDatabases
