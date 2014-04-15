#!/usr/bin/env python

"""
Created on Jul 23, 2013

@author: `@parkin`_
"""
import os

from PySide import QtCore
import time
from multiprocessing import Process, Pipe
from pypore.event_finder import find_events
from pypore.i_o import get_reader_from_filename


class PlotThread(QtCore.QThread):
    dataReady = QtCore.Signal(object)

    cancelled = False

    def __init__(self, axes, data='', plot_range='all', filename='', decimate=False, sample_rate=0.0):
        QtCore.QThread.__init__(self)
        self.plot_options = {'axes': axes, 'data': data, 'plot_range': plot_range}
        self.filename = filename
        self.decimate = decimate
        self.sample_rate = sample_rate

    def __del__(self):
        """
        If the object instantiating this thread gets deleted, the thread will be deleted, causing
        baseline_filter_parameter segfault, unless we implement this destructor.
        """
        self.wait()

    def run(self):
        if not self.filename == '' or self.plot_options['datadict'] == '':
            reader = get_reader_from_filename(self.filename)
            self.plot_options['data'] = reader.get_all_data(self.decimate)
            if self.sample_rate == 0.0:
                self.sample_rate = reader.get_sample_rate()
            reader.close()
        if self.cancelled:
            return
        self.plot_options['sample_rate'] = self.sample_rate
        self.dataReady.emit({'plot_options': self.plot_options, 'status_text': '', 'thread': self})


class AnalyzeDataThread(QtCore.QThread):
    """
    Class for searching for events in baseline_filter_parameter separate thread.
    """
    dataReady = QtCore.Signal(object)

    cancelled = False

    readyForEvents = True

    p = None

    def __init__(self, file_names, parameters, debug, save_file_names=None):
        QtCore.QThread.__init__(self)
        self.parameters = parameters
        self.debug = debug

        self.file_names = file_names
        self.save_file_names = save_file_names

        self.event_count = 0
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.periodic_call)
        self.timer.setSingleShot(True)

        self.next_event_to_send = 0

        self.events = []
        self.status_text = ''

        self.periodic_call()

    def __del__(self):
        """
        If the object instantiating this thread gets deleted, the thread will be deleted, causing
        baseline_filter_parameter segfault, unless we implement this destructor.
        """
        self.wait()

    def periodic_call(self):
        self.update_gui()
        if self.cancelled:
            self.dataReady.emit({'done': True})
            if self.p is not None:
                self.p.terminate()
                self.p.join()
            return
        self.timer.start(500)

    def update_gui(self):
        #         self.dataReady.emit({'event': event})
        do_send = False
        send = {}
        if len(self.status_text) > 0:
            send['status_text'] = self.status_text
            self.status_text = ''
            do_send = True
        if len(self.events) > 0:
            send['Events'] = self.events
            self.events = []
            do_send = True
        if do_send:
            self.dataReady.emit(send)

    def cancel(self):
        self.cancelled = True

    def run(self):
        self.time1 = time.time()
        if os.name == 'posix':
            self._pipe, child_conn = Pipe()
            self.p = Process(target=find_events, args=(self.file_names,),
                             kwargs={'parameters': self.parameters, 'pipe': child_conn, 'debug': self.debug,
                                     'save_file_names': self.save_file_names})
            self.p.start()
            # child_conn needs to be closed in all processes before EOFError is thrown (on Linux)
            # So close it here immediately
            child_conn.close()
            while True:
                time.sleep(0)
                try:
                    data = self._pipe.recv()
                    if 'status_text' in data:
                        self.status_text = data['status_text']
                    if 'Events' in data:
                        self.events += data['Events']
                except:
                    break
        else:
            # TODO add ability to listen for info from find_events on Windows.
            # If we are on windows, we can only fork a process if __name__ == '__main__'. Which
            # is not true here (because AnalyzeDataThread is imported).
            # So on Windows, just use this thread, don't use an additional separate process.
            find_events(self.file_names, parameters=self.parameters, debug=self.debug,
                        save_file_names=self.save_file_names)

        self.cancelled = True
