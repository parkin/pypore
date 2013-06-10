'''
Created on May 21, 2013

@author: parkin
'''
import scipy.io as sio
import matplotlib.pyplot as plt
import numpy as np

# specsfile = sio.loadmat('/home/parkin/Documents/DrndicLab/data/sample/events.mat')

'''
Do everything for the first dataset
'''
# load the matlab file with parameters for the runs
# specsfile = sio.loadmat('/home/parkin/Documents/DrndicLab/data/sample/all.mat')
# specsfile = sio.loadmat('/home/parkin/Eclipse/drndiclabworkspace/com.parkin.python.drniclab/data/polyA_20121221_142654_Events.mat')
specsfile = sio.loadmat('/home/will/python/translocationcode-python/data/polyA_20121221_142654_Events.mat')

print specsfile.keys()

events = specsfile['Events']

print events.shape
print specsfile['sample_rate']
print events[0]
first = events[2,0]
event = first['event_data'][0][0]
raw = first['raw_data'][0][0]
# time = np.linspace(first['start_time'][0][0][0][0], first['end_time'][0][0][0][0], len(event))
raw_time = np.linspace(0, len(raw)/float(specsfile['sample_rate']), len(raw))
time = np.linspace((len(raw) - len(event))/(2.*float(specsfile['sample_rate'])), (len(event)+(len(raw)-len(event))/2.)/float(specsfile['sample_rate']), len(event))
print time

print len(time),len(event)

plt.plot(raw_time,raw)
plt.plot(time,event)
plt.show()
