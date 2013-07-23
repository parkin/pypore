#!/usr/bin/env python

'''
Created on Jul 23, 2013

@author: parkin
'''

from PyQt4 import QtCore
from DataFileOpener import openData
import scipy.io as sio
import numpy as np

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
          threshold_type - 'adaptive' for adaptive-based threshold
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
        start_stddev = self.parameters['start_stddev']  # Starting threshold parameter
        end_stddev = self.parameters['end_stddev']  # Ending threshold parameter
        filter_parameter = self.parameters['filter_parameter'] # filter parameter 'a'
        
        # distance from mean to define an event
        threshold = data[0]
        
        i = 100
        # initialize mean/variance with first i datapoints
        for k in range(0, i):
            local_mean = filter_parameter * local_mean + (1 - filter_parameter) * data[k]
            local_variance = filter_parameter * local_variance + (1 - filter_parameter) * (data[k] - local_mean) ** 2
            threshold = start_stddev * local_variance ** .5
        
        save_file = {}
        save_file['Events'] = []
        
        n = len(data)
        event_count = 0
        isEvent = False
        wasEventPositive = False # Was the event an up spike?
        # search for events.  Keep track of filter_parameter filtered local (adapting!) mean and variance,
        # and use them to decide filter_parameter threshold for events.  See
        # http://pubs.rsc.org/en/content/articlehtml/2012/nr/c2nr30951c for more details.
        while i < n:
            # could this be an event?
            event_start = 0
            event_end = 0
            # Detecting a negative event
            if (directionNegative and data[i] < local_mean - threshold):
                isEvent = True
                wasEventPositive = False
            # Detecting a positive event
            elif (directionPositive and data[i] > local_mean + threshold):
                isEvent = True
                wasEventPositive = True
            if isEvent:
                isEvent = False
                # Set ending threshold
                threshold = end_stddev * local_variance ** .5 
                event_start = i
                done = False
                event_i = i
                # loop until event ends
                while not done and event_i - event_start < max_event_steps:
                    event_i = event_i + 1
                    if (not wasEventPositive and data[event_i] > local_mean - threshold) or (wasEventPositive and data[event_i] < local_mean + threshold):
                        event_end = event_i - 1
                        done = True
                        break
                # is the event long enough?
                if event_end - event_start > min_event_steps:
                    i = event_end
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
                    self.emit(QtCore.SIGNAL('_analyze_data_thread_callback(PyQt_PyObject)'), {'plot_options': self.plot_options, 'event': event})
                    save_file['Events'].append(event)
                    event_count = event_count + 1
            local_mean = filter_parameter * local_mean + (1 - filter_parameter) * data[i]
            local_variance = filter_parameter * local_variance + (1 - filter_parameter) * (data[i] - local_mean) ** 2
            threshold = start_stddev * local_variance ** .5 
            i = i + 1
            if i % 50000 == 0:
                self.emit(QtCore.SIGNAL('_analyze_data_thread_callback(PyQt_PyObject)'), {'status_text': 'Event Count: ' + str(event_count) + ' Percent Done: ' + str(100.*i / n)})
        if event_count > 0:
            save_file_name = list(self.filename)
            # Remove the .mat off the end
            for i in range(0, 4):
                save_file_name.pop()
                
            save_file_name.append('_Events.mat')
            save_file['filename'] = "".join(save_file_name)
            save_file['sample_rate'] = sample_rate
            save_file['event_count'] = event_count
            sio.savemat(save_file['filename'], save_file)
            
        self.emit(QtCore.SIGNAL('_analyze_data_thread_callback(PyQt_PyObject)'), {'status_text': 'Done. Found ' + str(event_count) + ' events.', 'done': True})  