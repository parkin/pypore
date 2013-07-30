#!/usr/bin/env python
'''
Created on Jul 29, 2013

@author: parkin
'''

import numpy as np

encodings = [np.dtype(np.uint8), np.dtype(np.uint16), np.dtype(np.uint32), np.dtype(np.int8), np.dtype(np.int16), np.dtype(np.int32), np.dtype(np.single), np.dtype(np.double)]

print np.dtype(np.uint8).byteorder
dt = np.dtype(np.uint32)
dt = dt.newbyteorder()
print dt.itemsize

# Starts out little endian for some reason.  Need big-endian.
for i in range(0, len(encodings)):
    encodings[i] = encodings[i].newbyteorder()

def getEncoding(integer):
    return encodings[integer]

f = open('/home/parkin/Eclipse/drndiclabworkspace/com.parkin.python.drniclab/data/kim.hkd')

while True:
    line = f.readline()
    if 'End of file format' in line:
        print line
        break
    
per_file_param_list = []
    
# Read per-file params
print 'Per-file params: --------------------------------'
f.read(3)  # read null characters?
byte = f.read(1)
for i in range(0, np.frombuffer(byte, np.uint8)[0]):
    byte1 = f.read(1)
    bytes2 = f.read(64)
    per_file_param_list.append([bytes2.strip(), np.frombuffer(byte1, np.uint8)[0]])
    
print per_file_param_list
    
# read per-block params
print 'Per-block params: --------------------------------'
per_block_param_list = []
f.read(3)
byte = f.read(1)
for i in range(0, np.frombuffer(byte, np.uint8)[0]):
    byte1 = f.read(1)
    bytes2 = f.read(64)
    per_block_param_list.append([bytes2.strip(), np.frombuffer(byte1, np.uint8)[0]])

print per_block_param_list

# read per-channel per-block params
print 'Per-channel per block params: -----------------'
per_channel_block_param_list = []
f.read(3)
byte = f.read(1)
for i in range(0, np.frombuffer(byte, np.uint8)[0]):
    byte1 = f.read(1)
    bytes2 = f.read(64)
    per_channel_block_param_list.append([bytes2.strip(), np.frombuffer(byte1, np.uint8)[0]])

print per_channel_block_param_list    

# read channel list
print 'Channel list: ---------------'
channel_list = []
f.read(3)
byte = f.read(1)
for i in range(0, np.frombuffer(byte, np.uint8)[0]):
    byte1 = f.read(1)
    bytes2 = f.read(512)
    channel_list.append([bytes2.strip(), np.frombuffer(byte1, np.uint8)[0]])

print channel_list

# Read per-file parameters
per_file_params = []
for pair in per_file_param_list:
    encoding = getEncoding(pair[1])
    byte = f.read(encoding.itemsize)
    per_file_params.append([pair[0], np.frombuffer(byte, encoding)[0]])
    
print per_file_params


