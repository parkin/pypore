#!/usr/bin/env python

'''
Created on Jul 23, 2013

@author: parkin
'''

from PyQt4 import QtCore
from DataFileOpener import openData
import scipy.io as sio
import numpy as np
import datetime

class PlotThread(QtCore.QThread):
    def __init__(self, axes, datadict='', plot_range='all', filename='',
                 threshold_type='adaptive', a=0.93,
                 threshold_direction='negative', min_event_length=10., max_event_length=1000.):
        QtCore.QThread.__init__(self)
        self.plot_options = {'axes': axes, 'datadict': datadict, 'plot_range': plot_range}
        self.filename = filename
        self.threshold_type = threshold_type
        self.filter_parameter = a
        self.threshold_direction = threshold_direction
        self.min_event_length = min_event_length
        self.max_event_length = max_event_length
    
    def __del__(self):
        '''
        If the object instantiating this thread gets deleted, the thread will be deleted, causing
        filter_parameter segfault, unless we implement this destructor.
        '''
        self.wait()
    
    def run(self):
        if not self.filename == '' or self.plot_options['datadict'] == '':
            self.plot_options['datadict'] = openData(self.filename)
        self.emit(QtCore.SIGNAL('plotData(PyQt_PyObject)'), {'plot_options': self.plot_options, 'status_text': ''})

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
    
    def __init__(self, parameters):
#     def __init__(self, axes, filename='', threshold_type='adaptive', filter_parameter=0.93,
#                  threshold_direction='negative', min_event_length=10., max_event_length=1000.):
        QtCore.QThread.__init__(self)
        self.parameters = parameters
    
    def __del__(self):
        '''
        If the object instantiating this thread gets deleted, the thread will be deleted, causing
        filter_parameter segfault, unless we implement this destructor.
        '''
        self.wait()
    
    def run(self):
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
        data = self.plot_options['datadict']['data']
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
            return 'Not enough datapoints in file.'
        
        
        local_mean = data[0]
        local_variance = 0.
        
        i = 0
        filter_parameter = self.parameters['filter_parameter'] # filter parameter 'a'
        if self.parameters['threshold_type'] == 'Absolute Change':
            threshold_start = self.parameters['absolute_change_start']
            threshold_end = self.parameters['absolute_change_end']
            threshold_type = self.THRESHOLD_ABSOLUTE_CHANGE
        elif self.parameters['threshold_type'] == 'Percentage Change':
            
            threshold_type = self.THRESHOLD_PERCENTAGE_CHANGE
        else: # noise based
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
        isEvent = False
        wasEventPositive = False # Was the event an up spike?
        # search for events.  Keep track of filter_parameter filtered local (adapting!) mean and variance,
        # and use them to decide filter_parameter threshold_start for events.  See
        # http://pubs.rsc.org/en/content/articlehtml/2012/nr/c2nr30951c for more details.
        while i < n:
            # could this be an event?
            event_start = 0
            event_end = 0
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
                # Set ending threshold_start
                if threshold_type == self.THRESHOLD_NOISE_BASED:
                    threshold_end = end_stddev * local_variance ** .5 
                event_start = i
                event_end = i+1
                done = False
                event_i = i
                # CUSUM stuff
                mean_estimate = data[i]
                level_start_times = []
                sn = sp = Sn = Sp = Gn = Gp = var_estimate = 0
                n_levels = 1 # We're already starting with one level
                delta = 0.1
                h = delta/(local_variance)**.5
                min_index_p = min_index_n = i
                min_Sp = min_Sn = 99999
                ko = i
                
                # loop until event ends
                while not done and event_i - event_start < max_event_steps:
                    event_i = event_i + 1
                    if (not wasEventPositive and data[event_i] > local_mean - threshold_end) or (wasEventPositive and data[event_i] < local_mean + threshold_end):
                        event_end = event_i - 1
                        done = True
                        break
                    # new mean = old_mean + (new_sample - old_mean)/(N)
                    new_mean = mean_estimate + (data[event_i]-mean_estimate)/(1+event_i-ko)
                    # New variance recursion relation 
                    var_estimate = ((event_i - ko)*var_estimate + (data[event_i]-mean_estimate)*(data[event_i] - new_mean))/(1+event_i-ko)
                    mean_estimate = new_mean
                    sp = (delta/var_estimate)*(data[event_i] - mean_estimate - delta/2)
                    sn = -(delta/var_estimate)*(data[event_i] - mean_estimate + delta/2)
                    Sp = Sp + sp
                    Sn = Sn + sn
                    Gp = max(0, Gp+sp)
                    Gn = max(0, Gn+sn)
                    if Sp < min_Sp:
                        min_Sp = Sp
                        min_index_p = event_i
                    if Sn < min_Sn:
                        min_Sn = Sn
                        min_index_n = event_i
                    # Did we detect a change?
                    if Gp > h or Gn > h:
                        minindex = min_index_n
                        level_start_times.append(min_index_n)
                        if Gp > h:
                            minindex = min_index_p
                            level_start_times[n_levels-1] = min_index_p
                        n_levels = n_levels + 1
                        # reset stuff
                        mean_estimate = data[i]
                        sn = sp = Sn = Sp = Gn = Gp = var_estimate = 0
                        min_index_p = min_index_n = event_i
                        min_Sp = min_Sn = 99999
                        # Go back to 1 after the level change found
                        ko = event_i = minindex+1
                    
                
                if event_end - event_start < max_event_steps:
                    i = event_end
                # is the event long enough?
                if done and event_end - event_start > min_event_steps:
                    print 'Number of level_values:', n_levels
                    # CUSUM stuff
                    level_values = [] # Holds the current values of the level_values
                    for q in range(0,n_levels):
                        start_index = event_start
                        if q > 0:
                            start_index = level_start_times[q-1]
                        end_index = event_end
                        if q < n_levels-1:
                            end_index = level_start_times[q]
                        level_values.append(np.mean(data[start_index:end_index]))
                    # end CUSUM
                    self.plot_options['plot_range'] = [event_start - 50, event_end + 50]
                    self.plot_options['show_event'] = True
                    event = {}
                    event['event_data'] = data[event_start:event_end]
                    event['raw_data'] = data[event_start - 50 : event_end + 50]
                    event['baseline'] = local_mean
                    event['delta'] = np.mean(event['event_data'])
                    event['event_start'] = event_start
                    event['event_end'] = event_end
                    event['raw_points_per_side'] = 50
                    event['sample_rate'] = sample_rate
                    event['cusum_indexes'] = level_start_times
                    event['cusum_values'] = level_values
                    self.emit(QtCore.SIGNAL('_analyze_data_thread_callback(PyQt_PyObject)'), {'plot_options': self.plot_options, 'event': event})
                    save_file['Events'].append(event)
                    event_count = event_count + 1
            local_mean = filter_parameter * local_mean + (1 - filter_parameter) * data[i]
            local_variance = filter_parameter * local_variance + (1 - filter_parameter) * (data[i] - local_mean) ** 2
            if threshold_type == self.THRESHOLD_NOISE_BASED:
                threshold_start = start_stddev * local_variance ** .5 
            i = i + 1
            if i % 50000 == 0:
                self.emit(QtCore.SIGNAL('_analyze_data_thread_callback(PyQt_PyObject)'), {'status_text': 'Event Count: ' + str(event_count) + ' Percent Done: ' + str(100.*i / n)})
        if event_count > 0:
            save_file_name = list(self.parameters['filename'])
            # Remove the .mat off the end
            for i in range(0, 4):
                save_file_name.pop()
                
            # Get a string with the current year/month/day/hour/minute to label the file
            day_time = datetime.datetime.now().strftime("%Y%m%d_%H%M")
            save_file_name.append('_Events_' + day_time + '.mat')
            save_file['filename'] = "".join(save_file_name)
            save_file['sample_rate'] = sample_rate
            save_file['event_count'] = event_count
            sio.savemat(save_file['filename'], save_file)
            
        self.emit(QtCore.SIGNAL('_analyze_data_thread_callback(PyQt_PyObject)'), {'status_text': 'Done. Found ' + str(event_count) + ' events.  Saved database to ' + str(save_file['filename']), 'done': True})  