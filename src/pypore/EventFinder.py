'''
Created on Aug 19, 2013

@author: parkin
'''

import time, datetime
import numpy as np
import scipy.io as sio
from pypore.DataFileOpener import prepareDataFile, getNextBlocks
from itertools import chain

# Threshold types
THRESHOLD_NOISE_BASED = 0
THRESHOLD_ABSOLUTE_CHANGE = 1
THRESHOLD_PERCENTAGE_CHANGE = 2

# Baseline types
BASELINE_ADAPTIVE = 3
BASELINE_FIXED = 4

def _getDataRange(dataCache, i, n):
    '''
    returns [i,n)
    '''
    res = np.zeros(n-i)
    
    resspot = 0
    # do we need to include points from the old data
    # (eg. for raw event points)
    if i < 0:
        l = len(dataCache[0])
        # Is the range totally within the old data
        if n <= 0:
            res = dataCache[0][l+i:l+n]
            return res
        res[0:-i] = dataCache[0][l+i:l]
        resspot -= i
        i=0
    spot = 0
    for q in xrange(len(dataCache)-1):
        cache = dataCache[q+1]
        nn = cache.size
        # if all the rest of the data is in this cache
        # add it to the end of the result and return
        if i >= spot and n <= spot+nn:
            res[resspot:] = cache[i-spot:n-spot]
            break
        # else we must need to visit more caches
        elif i < spot+nn:
            res[resspot:resspot+nn-i] = cache[i-spot:]
            resspot += nn-i
            i = spot + nn
        spot += nn
    return res
        
        

def _lazyLoadFindEvents(**parameters):
    event_count = 0
    
    get_blocks = 1
    
    raw_points_per_side = 50
    
    save_file = {}
    save_file['Events'] = []
    
    # IMPLEMENT ME pleasE
    f, params = prepareDataFile(parameters['filename'])
    
    sample_rate = params['sample_rate']
    timestep = 1. / sample_rate
    # Min and Max number of points in an event
    min_event_steps = int(parameters['min_event_length'] * 1e-6 / timestep)
    max_event_steps = int(parameters['max_event_length'] * 1e-6 / timestep)
    
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
    data, _ = getNextBlocks(f, params, get_blocks)
    data = data[0]  # only get channel 1
    
    n = data.size
    
    if n < 100:
        print 'Not enough datapoints in file.'
        return 'Not enough datapoints in file.'
    
    datapoint = data[0]
    
    local_mean = datapoint
    local_variance = 0.
    
    filter_parameter = parameters['filter_parameter']  # filter parameter 'a'
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
        threshold_start = start_stddev * local_variance ** .5
        threshold_end = datapoint
        threshold_type = THRESHOLD_NOISE_BASED
    
    dataCache = [np.zeros(n)+datapoint, data]
    
    i = 0
    prevI = 0
    time1 = time.time()
    time2 = time1
    event_start = 0
    event_end = 0
    isEvent = False
    wasEventPositive = False  # Was the event an up spike?
    placeInData = 0
    # search for events.  Keep track of filter_parameter filtered local (adapting!) mean and variance,
    # and use them to decide filter_parameter threshold_start for events.  See
    # http://pubs.rsc.org/en/content/articlehtml/2012/nr/c2nr30951c for more details.
    while i < n:
#         time.sleep(0)# way to yield to other threads. Allows the gui
#                                 # to remain responsive. Note this obviously 
#                                 # lowers the samples/s rate.
        datapoint = dataCache[1][i]
        if threshold_type == THRESHOLD_NOISE_BASED:
            threshold_start = start_stddev * local_variance ** .5 
        
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
                threshold_end = end_stddev * local_variance ** .5 
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
            delta = np.absolute(mean_estimate-local_mean)/10.
            min_index_p = min_index_n = i
            min_Sp = min_Sn = 999999
            ko = i
            event_area = datapoint - local_mean  # integrate the area
            
            # loop until event ends
            while not done and event_i - event_start < max_event_steps:
#                 time.sleep(0) # way to yield to other threads. Allows the gui
#                                 # to remain responsive. Note this obviously 
#                                 # lowers the samples/s rate.
                event_i = event_i + 1
                if event_i % n == 0: # We may need new data
                    size = 0
                    cache_index = 1 # which index in the cache is event_i
                                    # trying to grab data from?
                    for qq in xrange(len(dataCache)-1):
                        size += dataCache[qq+1].size
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
                datapoint = dataCache[int(1.*event_i/n)+1][event_i%n]
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
                elif delta ==0:
                    sp = sn = 0
                else:
                    sp = sn = float('inf')
                Sp = Sp + sp
                Sn = Sn + sn
                Gp = max(0, Gp + sp)
                Gn = max(0, Gn + sn)
                if Sp <= min_Sp:
                    min_Sp = Sp
                    min_index_p = event_i
                if Sn <= min_Sn:
                    min_Sn = Sn
                    min_index_n = event_i
                h = delta / (var_estimate) ** .5
                # Did we detect a change?
                if Gp > h or Gn > h:
                    minindex = min_index_n
                    level_indexes.append(min_index_n)
                    if Gp > h:
                        minindex = min_index_p
                        level_indexes[n_levels - 1] = min_index_p
                    n_levels = n_levels + 1
                    # reset stuff
                    mean_estimate = dataCache[int(1.*minindex/n)+1][minindex%n]
                    sn = sp = Sn = Sp = Gn = Gp = 0
                    min_index_p = min_index_n = event_i
                    min_Sp = min_Sn = 9999999
                    # Go back to 1 after the level change found
                    ko = event_i = minindex + 1
                  
            i = event_end
            level_indexes.append(event_end)
            # is the event long enough?
            if done and event_end - event_start > min_event_steps:
                # CUSUM stuff
                level_values = np.zeros(n_levels)  # Holds the current values of the level_values
                for q in xrange(0, n_levels):
                    start_index = level_indexes[q]
                    end_index = level_indexes[q+1]
                    level_values[q] = np.mean(_getDataRange(dataCache, start_index, end_index))
                for j, level_index in enumerate(level_indexes):
                    level_indexes[j] = level_index + placeInData
                # end CUSUM
                event = {}
                event['event_data'] = _getDataRange(dataCache, event_start, event_end)
                event['raw_data'] = _getDataRange(dataCache, event_start-raw_points_per_side, event_end+raw_points_per_side)
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
        local_variance = filter_parameter * local_variance + (1 - filter_parameter) * (datapoint - local_mean) ** 2
        i += 1
        # remove any arrays in the cache that we dont need anymore
        while i >= n and n > 0:
            del dataCache[0]
            i -= n
            placeInData += n
            # If we're just left with dataCache[0], which is reserved
            # for old data, then we need new data.
            if len(dataCache) < 2:
                datanext, _ = getNextBlocks(f, params, get_blocks)
                datanext = datanext[0]
                dataCache.append(datanext)
            if len(dataCache) > 1:
                n = dataCache[1].size
#             if placeInData % 50000 == 0:
#                 recent_time = time.time() - time2
#                 total_time = time.time() - time1
# #                     dataReady.emit({'status_text': 'Event Count: ' + str(event_count) + ' Percent Done: ' + str(100.*placeInData / points_per_channel_total) + ' Rate: ' + str((placeInData-prevI)/recent_time) + ' samples/s' + ' Total Rate:' + str(placeInData/total_time) + ' samples/s'})
#                 time2 = time.time()
#                 prevI = placeInData
            
            
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
    
def findEvents(**parameters):
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
    return _lazyLoadFindEvents(**params)
