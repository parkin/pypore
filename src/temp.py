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
specsfile = sio.loadmat('/home/parkin/Eclipse/drndiclabworkspace/com.parkin.python.drniclab/data/polyA_20121221_142654_Events.mat')

print specsfile.keys()

events = specsfile['Events']

print events.shape
print specsfile['sample_rate']
print events[0]
first = events[4,0]
event = first['event_data'][0][0]
# time = np.linspace(first['start_time'][0][0][0][0], first['end_time'][0][0][0][0], len(event))
time = np.linspace(0, len(event)/float(specsfile['sample_rate']), len(event))
print time

print len(time),len(event)

plt.plot(time,event)
plt.show()
