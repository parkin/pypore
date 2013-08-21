#!/usr/bin/env python

'''
Created on Jul 23, 2013

@author: parkin
'''

from PySide import QtCore
import scipy.io as sio
import numpy as np
import datetime
import time
from pypore.DataFileOpener import openData, prepareDataFile, getNextBlocks

class PlotThread(QtCore.QThread):
    dataReady = QtCore.Signal(object)
    
    cancelled = False
    
    def __init__(self, axes, datadict='', plot_range='all', filename='',
                 threshold_type='adaptive', a=0.93,
                 threshold_direction='negative', min_event_length=10., max_event_length=1000., decimate=False):
        QtCore.QThread.__init__(self)
        self.plot_options = {'axes': axes, 'datadict': datadict, 'plot_range': plot_range}
        self.filename = filename
        self.threshold_type = threshold_type
        self.filter_parameter = a
        self.threshold_direction = threshold_direction
        self.min_event_length = min_event_length
        self.max_event_length = max_event_length
        self.decimate = decimate
    
    def __del__(self):
        '''
        If the object instantiating this thread gets deleted, the thread will be deleted, causing
        filter_parameter segfault, unless we implement this destructor.
        '''
        self.wait()
    
    def run(self):
        if not self.filename == '' or self.plot_options['datadict'] == '':
            self.plot_options['datadict'] = openData(self.filename, self.decimate)
#         self.emit(QtCore.SIGNAL('plotData(PyQt_PyObject)'), {'plot_options': self.plot_options, 'status_text': ''})
        if self.cancelled:
            return
        self.dataReady.emit({'plot_options': self.plot_options, 'status_text': ''})

class AnalyzeDataThread(QtCore.QThread):
    '''
    Class for searching for events in filter_parameter separate thread.  
    '''
    # Threshold types
    THRESHOLD_NOISE_BASED = 0
    THRESHOLD_ABSOLUTE_CHANGE = 1
    THRESHOLD_PERCENTAGE_CHANGE = 2
    
    # Baseline types
    BASELINE_ADAPTIVE = 3
    BASELINE_FIXED = 4
    
    dataReady = QtCore.Signal(object)
    
    cancelled = False
    
    readyForEvents = True
    
    def __init__(self, parameters):
#     def __init__(self, axes, filename='', threshold_type='adaptive', filter_parameter=0.93,
#                  threshold_direction='negative', min_event_length=10., max_event_length=1000.):
        QtCore.QThread.__init__(self)
        self.parameters = parameters
        
        self.event_count = 0
        self.save_file = {}
        self.save_file['Events'] = []
        self.placeInData = 1
        self.points_per_channel_total = 1
        self.prevI = 0
        self.recent_time = 1
        self.total_time = 1
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.periodicCall)
        self.timer.setSingleShot(True)
        
        self.nextEventToSend = 0
        
        self.periodicCall()
        
    
    def __del__(self):
        '''
        If the object instantiating this thread gets deleted, the thread will be deleted, causing
        filter_parameter segfault, unless we implement this destructor.
        '''
        self.wait()
        
    def periodicCall(self):
        self.updateGui()
        if self.cancelled:
            return
        self.timer.start(500)
        
    def updateGui(self):
#         self.dataReady.emit({'event': event})
        send = {'status_text': 'Event Count: ' + str(self.event_count) + ' Percent Done: ' + str(100.*self.placeInData / self.points_per_channel_total) + ' Rate: ' + str((self.placeInData-self.prevI)/self.recent_time) + ' samples/s' + ' Total Rate:' + str(self.placeInData/self.total_time) + ' samples/s'}
        if self.readyForEvents:
            events = self.save_file['Events']
            if self.event_count > self.nextEventToSend:
                send['Events'] = events[self.nextEventToSend:self.event_count]
                self.nextEventToSend = self.event_count
                self.readyForEvents = False
        self.dataReady.emit(send)
        
    def lazyLoading(self):
        '''
        Lazily loads large data files.
        '''
        # I did some quick calculation of the rate (with plotting and everything), and
        # nonLazy - ~96k samples/sec
        # lazy 10 blocks (50,000 samples) - ~100k samples/sec
        # lazy 3 blocks ( 15,000 samples) - ~105k samples/sec
        # lazy 1 block (5,000 samples) - ~108k samples/sec
        get_blocks = 1
        
        raw_points_per_side = 50
        
        # IMPLEMENT ME pleasE
        self.plot_options = {}
        self.plot_options['axes'] = self.parameters['axes']
        f, params = prepareDataFile(self.parameters['filename'])
        
        sample_rate = params['sample_rate']
        self.points_per_channel_total = params['points_per_channel_total']
        timestep = 1. / sample_rate
        # Min and Max number of points in an event
        min_event_steps = int(self.parameters['min_event_length'] * 1e-6 / timestep)
        max_event_steps = int(self.parameters['max_event_length'] * 1e-6 / timestep)
        
        # Threshold direction.  -1 for negative, 0 for both, +1 for positive
        directionPositive = False
        directionNegative = False
        if self.parameters['threshold_direction'] == 'Positive':
            directionPositive = True
        elif self.parameters['threshold_direction'] == 'Negative':
            directionNegative = True
        elif self.parameters['threshold_direction'] == 'Both':
            directionNegative = True
            directionPositive = True
            
        # allocate memory for data
        data, doneWithData = getNextBlocks(f, params, get_blocks)
        data = data[0]  # only get channel 1
        
        if data.size < 100:
            print 'Not enough datapoints in file.'
            return 'Not enough datapoints in file.'
        
        local_mean = data[0]
        local_variance = 0.
        
        i = 0
        filter_parameter = self.parameters['filter_parameter']  # filter parameter 'a'
        if self.parameters['threshold_type'] == 'Absolute Change':
            threshold_start = self.parameters['absolute_change_start']
            threshold_end = self.parameters['absolute_change_end']
            threshold_type = self.THRESHOLD_ABSOLUTE_CHANGE
        elif self.parameters['threshold_type'] == 'Percent Change':
            
            threshold_type = self.THRESHOLD_PERCENTAGE_CHANGE
        else:  # noise based
            start_stddev = self.parameters['start_stddev']  # Starting threshold_start parameter
            end_stddev = self.parameters['end_stddev']  # Ending threshold_start parameter
            
            i = 100
            # initialize mean/variance with first i datapoints
            for k in range(0, i):
                local_mean = filter_parameter * local_mean + (1 - filter_parameter) * data[k]
                local_variance = filter_parameter * local_variance + (1 - filter_parameter) * (data[k] - local_mean) ** 2
    
            # distance from mean to define an event.  noise based unless otherwise chosen.
            threshold_start = start_stddev * local_variance ** .5
            threshold_end = data[0]
            threshold_type = self.THRESHOLD_NOISE_BASED
        
        dataCache = []
        rawPointsCache = np.zeros(raw_points_per_side)
        
        n = data.size
        i = 0
        self.prevI = 0
        time2 = self.time1
        isEvent = False
        wasEventPositive = False  # Was the event an up spike?
        self.placeInData = 0
        # search for events.  Keep track of filter_parameter filtered local (adapting!) mean and variance,
        # and use them to decide filter_parameter threshold_start for events.  See
        # http://pubs.rsc.org/en/content/articlehtml/2012/nr/c2nr30951c for more details.
        while i < n and not doneWithData:
            time.sleep(0)# way to yield to other threads. Allows the gui
                                    # to remain responsive. Note this obviously 
                                    # lowers the samples/s rate.
            # could this be an event?
            event_start = 0
            event_end = 0
            if threshold_type == self.THRESHOLD_PERCENTAGE_CHANGE:
                threshold_start = local_mean * self.parameters['percent_change_start'] / 100.
            # Detecting a negative event
            if (directionNegative and data[i] < local_mean - threshold_start):
                isEvent = True
                wasEventPositive = False
            # Detecting a positive event
            elif (directionPositive and data[i] > local_mean + threshold_start):
                isEvent = True
                wasEventPositive = True
            if isEvent:
                isEvent = False
                # Set ending threshold_end
                if threshold_type == self.THRESHOLD_NOISE_BASED:
                    threshold_end = end_stddev * local_variance ** .5 
                elif threshold_type == self.THRESHOLD_PERCENTAGE_CHANGE:
                    threshold_end = local_mean * self.parameters['percent_change_end'] / 100.
                event_start = i
                event_end = i + 1
                done = False
                event_i = i
                # CUSUM stuff
                mean_estimate = data[i]
                level_indexes = [event_start]  # The indexes in data[] where each
                                                # level starts.
                sn = sp = Sn = Sp = Gn = Gp = var_estimate = 0
                n_levels = 1  # We're already starting with one level
                delta = 0.1
                h = delta / (local_variance) ** .5
                min_index_p = min_index_n = i
                min_Sp = min_Sn = 99999
                ko = i
                event_area = data[event_i] - local_mean  # integrate the area
                
                # loop until event ends
                while not done and event_i - event_start < max_event_steps:
                    time.sleep(0) # way to yield to other threads. Allows the gui
                                    # to remain responsive. Note this obviously 
                                    # lowers the samples/s rate.
                    event_i = event_i + 1
                    #  If we need to load another block, but are still looking at an event,
                    # just cache the current data
                    if event_i % n == 0:
                        datas, doneWithData = getNextBlocks(f, params, get_blocks)
                        dataCache.append(datas[0])
                        datas = 0 # free
                        if doneWithData:
                            break
                    if (not wasEventPositive and self.getDataAt(data, dataCache, rawPointsCache, event_i) > local_mean - threshold_end) or (wasEventPositive and self.getDataAt(data, dataCache, rawPointsCache, event_i) < local_mean + threshold_end):
                        event_end = event_i - 1
                        done = True
                        break
                    event_area = event_area + self.getDataAt(data, dataCache, rawPointsCache, event_i) - local_mean
                    # new mean = old_mean + (new_sample - old_mean)/(N)
                    new_mean = mean_estimate + (self.getDataAt(data, dataCache, rawPointsCache, event_i) - mean_estimate) / (1 + event_i - ko)
                    # New variance recursion relation 
                    var_estimate = ((event_i - ko) * var_estimate + (self.getDataAt(data, dataCache, rawPointsCache, event_i) - mean_estimate) * (self.getDataAt(data, dataCache, rawPointsCache, event_i) - new_mean)) / (1 + event_i - ko)
                    mean_estimate = new_mean
                    sp = (delta / var_estimate) * (self.getDataAt(data, dataCache, rawPointsCache, event_i) - mean_estimate - delta / 2)
                    sn = -(delta / var_estimate) * (self.getDataAt(data, dataCache, rawPointsCache, event_i) - mean_estimate + delta / 2)
                    Sp = Sp + sp
                    Sn = Sn + sn
                    Gp = max(0, Gp + sp)
                    Gn = max(0, Gn + sn)
                    if Sp < min_Sp:
                        min_Sp = Sp
                        min_index_p = event_i
                    if Sn < min_Sn:
                        min_Sn = Sn
                        min_index_n = event_i
                    # Did we detect a change?
                    if Gp > h or Gn > h:
                        minindex = min_index_n
                        level_indexes.append(min_index_n)
                        if Gp > h:
                            minindex = min_index_p
                            level_indexes[n_levels - 1] = min_index_p
                        n_levels = n_levels + 1
                        # reset stuff
                        mean_estimate = data[i]
                        sn = sp = Sn = Sp = Gn = Gp = var_estimate = 0
                        min_index_p = min_index_n = event_i
                        min_Sp = min_Sn = 99999
                        # Go back to 1 after the level change found
                        ko = event_i = minindex + 1
                        
                i = event_end
                # is the event long enough?
                if done and event_end - event_start > min_event_steps:
                    # CUSUM stuff
                    level_values = np.zeros(n_levels)  # Holds the current values of the level_values
                    for q in range(0, n_levels):
                        start_index = event_start
                        if q > 0:
                            start_index = level_indexes[q - 1]
                        end_index = event_end + 1
                        if q < n_levels - 1:
                            end_index = level_indexes[q] + 1
                        level_values[q] = np.mean(self.getDataRange(data, dataCache, rawPointsCache, start_index, end_index))
                    for j in range(0, len(level_indexes)):
                        level_indexes[j] = level_indexes[j] + self.placeInData
                    # end CUSUM
                    self.plot_options['plot_range'] = [event_start - raw_points_per_side, event_end + raw_points_per_side]
                    self.plot_options['show_event'] = True
                    event = {}
                    event['event_data'] = self.getDataRange(data, dataCache, rawPointsCache, event_start, event_end)
                    event['raw_data'] = self.getDataRange(data, dataCache, rawPointsCache, event_start-raw_points_per_side, event_end+raw_points_per_side)
                    event['baseline'] = local_mean
                    event['current_blockage'] = np.mean(event['event_data']) - local_mean
                    event['event_start'] = event_start + self.placeInData
                    event['event_end'] = event_end + self.placeInData
                    event['raw_points_per_side'] = raw_points_per_side
                    event['sample_rate'] = sample_rate
                    event['cusum_indexes'] = level_indexes
                    event['cusum_values'] = level_values
                    event['area'] = event_area
#                     self.dataReady.emit({'plot_options': self.plot_options, 'event': event})
                    self.save_file['Events'].append(event)
                    self.event_count = self.event_count + 1
                if len(dataCache) > 0:
#                     print 'cache len:', len(dataCache)
                    if i >= n:
                        i = i % n
                        self.placeInData = self.placeInData + n
                        for cache in dataCache:
                            if i >= cache.size:
                                i = i % cache.size
                                self.placeInData = self.placeInData + cache.size
                                rawPointsCache = cache[cache.size-raw_points_per_side:]
                            else:
                                data = cache
                                n = data.size
                                break
                    dataCache = []
                                
            local_mean = filter_parameter * local_mean + (1 - filter_parameter) * data[i]
            local_variance = filter_parameter * local_variance + (1 - filter_parameter) * (data[i] - local_mean) ** 2
            if threshold_type == self.THRESHOLD_NOISE_BASED:
                threshold_start = start_stddev * local_variance ** .5 
            i = i + 1
            if i >= n:
                self.placeInData = self.placeInData + n
                i = i % n
                rawPointsCache = data[data.size - raw_points_per_side:]
                data, doneWithData = getNextBlocks(f, params, get_blocks)
                data = data[0]
                n = data.size
                if self.placeInData % 50000 == 0:
                    self.recent_time = time.time() - time2
                    self.total_time = time.time() - self.time1
#                     self.dataReady.emit({'status_text': 'Event Count: ' + str(self.event_count) + ' Percent Done: ' + str(100.*self.placeInData / self.points_per_channel_total) + ' Rate: ' + str((self.placeInData-self.prevI)/self.recent_time) + ' samples/s' + ' Total Rate:' + str(self.placeInData/self.total_time) + ' samples/s'})
                    time2 = time.time()
                    self.prevI = self.placeInData
            if self.cancelled:
                return
            
            
        if self.event_count > 0:
            self.save_file_name = list(self.parameters['filename'])
            # Remove the .mat off the end
            for i in range(0, 4):
                self.save_file_name.pop()
                
            # Get a string with the current year/month/day/hour/minute to label the file
            day_time = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            self.save_file_name.append('_Events_' + day_time + '.mat')
            self.save_file['filename'] = "".join(self.save_file_name)
            self.save_file['sample_rate'] = sample_rate
            self.save_file['event_count'] = self.event_count
            # save the user's analysis parameters
            self.parameters.pop('axes', None)  # remove the axes before saving.
            self.save_file['parameters'] = self.parameters
            sio.savemat(self.save_file['filename'], self.save_file)
            
#         self.dataReady.emit({'status_text': 'Done. Found ' + str(self.event_count) + ' events.  Saved database to ' + str(self.save_file['filename']), 'done': True})
        self.cancelled = True
        
        return
    
    def getDataAt(self, data, dataCache, rawPointsCache, i):
        '''
        Returns data from either data, or dataCache
        '''
        if i < 0:
            return rawPointsCache[rawPointsCache.size + i]
        elif i < data.size:
            return data[i]
        else:
            i = i%data.size
            for cache in dataCache:
                if i < cache.size:
                    return cache[i]
                else:
                    i = i%cache.size
#         print 'getDataAt no data found, i:', i, 'data.size:', data.size, 'num in cache:', len(dataCache)
        return None
    
    def getDataRange(self, data, dataCache, rawPointsCache, i, n):
        '''
        Returns data [0,n)
        '''
        ret = np.zeros(n-i)
        for j in range(i,n):
            ret[j-i] = self.getDataAt(data, dataCache, rawPointsCache, j)
            
        return ret
    
    def nonLazyLoading(self):
        '''
        Finds all the events in 'data'.
        
        Parameters: 
          datadict - must have data in 'data', sample rate in 'SETUP_ADCSAMPLERATE'
          threshold_type - 'adaptive' for adaptive-based threshold_start
                         - 'current' for current based TODO
          filter_parameter - filter parameter for 'noise'. Should be close to 1, less than 1. nA for 'current'
          threshold_direction - 'positive' or 'negative' or 'both'
          min_event_length - in microseconds
          max_event_length - in microseconds
          
        Returns:
          Struct containing all events found events
          
        '''
        self.plot_options = {}
        self.plot_options['axes'] = self.parameters['axes']
        if not self.parameters['filename'] == '' or self.plot_options['datadict'] == '':
            self.plot_options['datadict'] = openData(self.parameters['filename'])
        data = self.plot_options['datadict']['data'][0]
        sample_rate = self.plot_options['datadict']['SETUP_ADCSAMPLERATE'][0][0]
        timestep = 1 / sample_rate
        
        # Min and Max number of points in an event
        min_event_steps = int(self.parameters['min_event_length'] * 1e-6 / timestep)
        max_event_steps = int(self.parameters['max_event_length'] * 1e-6 / timestep)
        
        # Threshold direction.  -1 for negative, 0 for both, +1 for positive
        directionPositive = False
        directionNegative = False
        if self.parameters['threshold_direction'] == 'Positive':
            directionPositive = True
        elif self.parameters['threshold_direction'] == 'Negative':
            directionNegative = True
        elif self.parameters['threshold_direction'] == 'Both':
            directionNegative = True
            directionPositive = True
            
        n = len(data)
        
        if n < 100:
            print 'Not enough datapoints in file.'
            return 'Not enough datapoints in file.'
        
        
        local_mean = data[0]
        local_variance = 0.
        
        i = 0
        filter_parameter = self.parameters['filter_parameter']  # filter parameter 'a'
        if self.parameters['threshold_type'] == 'Absolute Change':
            threshold_start = self.parameters['absolute_change_start']
            threshold_end = self.parameters['absolute_change_end']
            threshold_type = self.THRESHOLD_ABSOLUTE_CHANGE
        elif self.parameters['threshold_type'] == 'Percent Change':
            
            threshold_type = self.THRESHOLD_PERCENTAGE_CHANGE
        else:  # noise based
            start_stddev = self.parameters['start_stddev']  # Starting threshold_start parameter
            end_stddev = self.parameters['end_stddev']  # Ending threshold_start parameter
            
            i = 100
            # initialize mean/variance with first i datapoints
            for k in range(0, i):
                local_mean = filter_parameter * local_mean + (1 - filter_parameter) * data[k]
                local_variance = filter_parameter * local_variance + (1 - filter_parameter) * (data[k] - local_mean) ** 2
    
            # distance from mean to define an event.  noise based unless otherwise chosen.
            threshold_start = start_stddev * local_variance ** .5
            threshold_end = data[0]
            threshold_type = self.THRESHOLD_NOISE_BASED

        
        save_file = {}
        save_file['Events'] = []
        
        n = len(data)
        event_count = 0
        i = 0
        isEvent = False
        wasEventPositive = False  # Was the event an up spike?
        # search for events.  Keep track of filter_parameter filtered local (adapting!) mean and variance,
        # and use them to decide filter_parameter threshold_start for events.  See
        # http://pubs.rsc.org/en/content/articlehtml/2012/nr/c2nr30951c for more details.
        while i < n:
            # could this be an event?
            event_start = 0
            event_end = 0
            if threshold_type == self.THRESHOLD_PERCENTAGE_CHANGE:
                threshold_start = local_mean * self.parameters['percent_change_start'] / 100.
            # Detecting a negative event
            if (directionNegative and data[i] < local_mean - threshold_start):
                isEvent = True
                wasEventPositive = False
            # Detecting a positive event
            elif (directionPositive and data[i] > local_mean + threshold_start):
                isEvent = True
                wasEventPositive = True
            if isEvent:
                isEvent = False
                # Set ending threshold_end
                if threshold_type == self.THRESHOLD_NOISE_BASED:
                    threshold_end = end_stddev * local_variance ** .5 
                elif threshold_type == self.THRESHOLD_PERCENTAGE_CHANGE:
                    threshold_end = local_mean * self.parameters['percent_change_end'] / 100.
                event_start = i
                event_end = i + 1
                done = False
                event_i = i
                # CUSUM stuff
                mean_estimate = data[i]
                level_indexes = [event_start]  # The indexes in data[] where each
                                                # level starts.
                sn = sp = Sn = Sp = Gn = Gp = var_estimate = 0
                n_levels = 1  # We're already starting with one level
                delta = 0.1
                h = delta / (local_variance) ** .5
                min_index_p = min_index_n = i
                min_Sp = min_Sn = 99999
                ko = i
                event_area = data[event_i] - local_mean  # integrate the area
                
                # loop until event ends
                while not done and event_i - event_start < max_event_steps:
                    event_i = event_i + 1
                    if (not wasEventPositive and data[event_i] > local_mean - threshold_end) or (wasEventPositive and data[event_i] < local_mean + threshold_end):
                        event_end = event_i - 1
                        done = True
                        break
                    event_area = event_area + data[event_i] - local_mean
                    # new mean = old_mean + (new_sample - old_mean)/(N)
                    new_mean = mean_estimate + (data[event_i] - mean_estimate) / (1 + event_i - ko)
                    # New variance recursion relation 
                    var_estimate = ((event_i - ko) * var_estimate + (data[event_i] - mean_estimate) * (data[event_i] - new_mean)) / (1 + event_i - ko)
                    mean_estimate = new_mean
                    sp = (delta / var_estimate) * (data[event_i] - mean_estimate - delta / 2)
                    sn = -(delta / var_estimate) * (data[event_i] - mean_estimate + delta / 2)
                    Sp = Sp + sp
                    Sn = Sn + sn
                    Gp = max(0, Gp + sp)
                    Gn = max(0, Gn + sn)
                    if Sp < min_Sp:
                        min_Sp = Sp
                        min_index_p = event_i
                    if Sn < min_Sn:
                        min_Sn = Sn
                        min_index_n = event_i
                    # Did we detect a change?
                    if Gp > h or Gn > h:
                        minindex = min_index_n
                        level_indexes.append(min_index_n)
                        if Gp > h:
                            minindex = min_index_p
                            level_indexes[n_levels - 1] = min_index_p
                        n_levels = n_levels + 1
                        # reset stuff
                        mean_estimate = data[i]
                        sn = sp = Sn = Sp = Gn = Gp = var_estimate = 0
                        min_index_p = min_index_n = event_i
                        min_Sp = min_Sn = 99999
                        # Go back to 1 after the level change found
                        ko = event_i = minindex + 1
                    
                
                i = event_end
                # is the event long enough?
                if done and event_end - event_start > min_event_steps:
                    # CUSUM stuff
                    level_values = np.zeros(n_levels)  # Holds the current values of the level_values
                    for q in range(0, n_levels):
                        start_index = event_start
                        if q > 0:
                            start_index = level_indexes[q - 1]
                        end_index = event_end + 1
                        if q < n_levels - 1:
                            end_index = level_indexes[q] + 1
                        level_values[q] = np.mean(data[start_index:end_index])
                    # end CUSUM
                    self.plot_options['plot_range'] = [event_start - 50, event_end + 50]
                    self.plot_options['show_event'] = True
                    event = {}
                    event['event_data'] = data[event_start:event_end]
                    event['raw_data'] = data[event_start - 50 : event_end + 50]
                    event['baseline'] = local_mean
                    event['current_blockage'] = np.mean(event['event_data']) - local_mean
                    event['event_start'] = event_start
                    event['event_end'] = event_end
                    event['raw_points_per_side'] = 50
                    event['sample_rate'] = sample_rate
                    event['cusum_indexes'] = level_indexes
                    event['cusum_values'] = level_values
                    event['area'] = event_area
                    self.emit(QtCore.SIGNAL('_analyze_data_thread_callback(PyQt_PyObject)'), {'plot_options': self.plot_options, 'event': event})
                    save_file['Events'].append(event)
                    event_count = event_count + 1
            local_mean = filter_parameter * local_mean + (1 - filter_parameter) * data[i]
            local_variance = filter_parameter * local_variance + (1 - filter_parameter) * (data[i] - local_mean) ** 2
            if threshold_type == self.THRESHOLD_NOISE_BASED:
                threshold_start = start_stddev * local_variance ** .5 
            i = i + 1
            if i % 50000 == 0:
                self.total_time = time.time() - self.time1
                self.emit(QtCore.SIGNAL('_analyze_data_thread_callback(PyQt_PyObject)'), 
                          {'status_text': 'Event Count: ' + str(event_count) + ' Percent Done: ' + str(100.*i / n) + ' Rate: ' + str(i/self.total_time) + ' samples/sec'})
        if event_count > 0:
            save_file_name = list(self.parameters['filename'])
            # Remove the .mat off the end
            for i in range(0, 4):
                save_file_name.pop()
                
            # Get a string with the current year/month/day/hour/minute to label the file
            day_time = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            save_file_name.append('_Events_' + day_time + '.mat')
            save_file['filename'] = "".join(save_file_name)
            save_file['sample_rate'] = sample_rate
            save_file['event_count'] = event_count
            # save the user's analysis parameters
            self.parameters.pop('axes', None)  # remove the axes before saving.
            save_file['parameters'] = self.parameters
            sio.savemat(save_file['filename'], save_file)
            
        self.emit(QtCore.SIGNAL('_analyze_data_thread_callback(PyQt_PyObject)'), 
                  {'status_text': 'Done. Found ' + str(event_count) + ' events.  Saved database to ' + str(save_file['filename']), 'done': True})  
    
    def run(self):
        self.time1 = time.time()
#         self.nonLazyLoading()
        self.lazyLoading()
