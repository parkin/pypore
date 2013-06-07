'''
Created on May 21, 2013

@author: parkin
'''
import scipy.io as sio
import matplotlib.pyplot as plt
import numpy as np

specsfile = sio.loadmat('/home/parkin/Documents/DrndicLab/data/sample/events.mat')

'''
Do everything for the first dataset
'''
# load the matlab file with parameters for the runs
specsfile = sio.loadmat('/home/parkin/Documents/DrndicLab/data/sample/all.mat')

print specsfile.keys()

struct = specsfile['All']

print struct.shape
print struct[0,1]
print struct[0,1]['event_data']
first = struct[0,1]
event = first['event_data'][0][0]
time = np.linspace(first['start_time'][0][0][0][0], first['end_time'][0][0][0][0], len(event))

print len(time),len(event)

plt.plot(time,event)
plt.show()
