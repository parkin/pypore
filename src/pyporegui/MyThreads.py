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
from pypore.EventFinder import findEvents

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
        if self.cancelled:
            self.save_file['cancelled'] = True
            return
        self.updateGui()
        self.timer.start(500)
        
    def updateGui(self):
#         self.dataReady.emit({'event': event})
        send = {'status_text': 'Event Count: ' + str(self.event_count) + ' Percent Done: ' + str(100.*self.placeInData / self.points_per_channel_total) + ' Rate: ' + str((self.placeInData-self.prevI)/self.recent_time) + ' samples/s' + ' Total Rate:' + str(self.placeInData/self.total_time) + ' samples/s'}
        events = self.save_file['Events']
        count = len(events)
        if self.readyForEvents:
            if count > self.nextEventToSend:
                send['Events'] = events[self.nextEventToSend:count]
                self.nextEventToSend = count
                self.readyForEvents = False
        self.dataReady.emit(send)
        
    
    def run(self):
        self.time1 = time.time()
#         self.nonLazyLoading()
        findEvents(self.dataReady, self.save_file, **self.parameters)
        self.cancelled = True
