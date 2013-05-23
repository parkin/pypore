'''
Created on May 21, 2013

@author: parkin
'''
import scipy.io as sio
import matplotlib.pyplot as plt
import numpy as np
from Tkinter import Tk
from tkFileDialog import askopenfilenames

Tk().withdraw() # we don't want a full GUI, so keep the root window from appearing
filenames = askopenfilenames(title='Open Data Files') # Show an Open Files dialog and return the filenames choesen
print(filenames)


specsfile = sio.loadmat('/home/parkin/Documents/DrndicLab/data/sample/events.mat')

'''
Do everything for the first dataset
'''
# load the matlab file with parameters for the runs
specsfile = sio.loadmat('/home/parkin/Documents/DrndicLab/data/sample/all.mat')

struct = specsfile['All']

print struct.shape
first = struct[0,10]
event = first['event_data'][0][0]
time = np.linspace(first['start_time'][0][0][0][0], first['end_time'][0][0][0][0], len(event))

print len(time),len(event)

plt.plot(time,event)
plt.show()
