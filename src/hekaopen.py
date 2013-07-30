#!/usr/bin/env python
'''
Created on Jul 29, 2013

@author: parkin
'''

import numpy as np
import os

def getByteLength(list):
    '''
    Returns the length in bytes of the sum of all the parameters in the list.
    Here, list[i][0] = param, list[i][1] = np.dtype
    '''
    size = 0
    for i in list:
        size = size + i[1].itemsize
    return size

# Data types list, in order specified by the HEKA file header v2.0.
# Using big-endian.
# Code 0=uint8,1=uint16,2=uint32,3=int8,4=int16,5=int32,
#    6=single,7=double,8=string64,9=string512
encodings = [np.dtype('>u1'), np.dtype('>u2'), np.dtype('>u4'), np.dtype('>i1'), np.dtype('>i2'), np.dtype('>i4'), np.dtype('>f4'), np.dtype('>f8'), np.dtype('>S64'), np.dtype('>S512')]

filename = '/home/parkin/Eclipse/drndiclabworkspace/com.parkin.python.drniclab/data/kim.hkd'

f = open(filename)

# Skip the header text in the file.
while True:
    line = f.readline()
    if 'End of file format' in line:
        print line
        break
    
per_file_param_list = []
    
# Read per-file params
print 'Per-file param list: --------------------------------'
f.read(3)  # read null characters?
byte = f.read(1)
for i in range(0, np.frombuffer(byte, np.uint8)[0]):
    byte1 = f.read(1)
    bytes2 = f.read(64)
    per_file_param_list.append([bytes2.strip(), encodings[np.frombuffer(byte1, np.uint8)[0]]])
    
print per_file_param_list
    
# read per-block params
print 'Per-block params: --------------------------------'
per_block_param_list = []
f.read(3)
byte = f.read(1)
for i in range(0, np.frombuffer(byte, np.uint8)[0]):
    byte1 = f.read(1)
    bytes2 = f.read(64)
    per_block_param_list.append([bytes2.strip(), encodings[np.frombuffer(byte1, np.uint8)[0]]])

print per_block_param_list

# read per-channel per-block params
print 'Per-channel per block params: -----------------'
per_channel_block_param_list = []
f.read(3)
byte = f.read(1)
for i in range(0, np.frombuffer(byte, np.uint8)[0]):
    byte1 = f.read(1)
    bytes2 = f.read(64)
    per_channel_block_param_list.append([bytes2.strip(), encodings[np.frombuffer(byte1, np.uint8)[0]]])

print per_channel_block_param_list    

# read channel list
print 'Channel list: ---------------'
channel_list = []
f.read(3)
byte = f.read(1)
for i in range(0, np.frombuffer(byte, np.uint8)[0]):
    byte1 = f.read(1)
    bytes2 = f.read(512)
    channel_list.append([bytes2.strip(), encodings[np.frombuffer(byte1, np.uint8)[0]]])

print channel_list

# Read per-file parameters
per_file_params = {}
for pair in per_file_param_list:
    byte = f.read(pair[1].itemsize)
    dt = pair[1]
    per_file_params[pair[0]] = np.frombuffer(byte,dt)[0]

print 'Per-file params: -----------------'   
print per_file_params

# Get per-file header length. Given by position in file
per_file_header_length = f.tell()
print 'per file header length:', per_file_header_length

# Calculate the block lengths
print 'Block lengths: ------------------'
per_channel_per_block_length = getByteLength(per_channel_block_param_list)
per_block_length = getByteLength(per_block_param_list)

channel_list_number = len(channel_list)

header_bytes_per_block = per_channel_per_block_length*channel_list_number
data_bytes_per_block = per_file_params['Points per block'] * 2 * channel_list_number
total_bytes_per_block = header_bytes_per_block + data_bytes_per_block + per_block_length

print 'header bytes per block:', header_bytes_per_block
print 'total bytes per block:', total_bytes_per_block
print 'data bytes per block:', data_bytes_per_block

# Calculate number of points per channel
print 'Points per channel: ------------------'
filesize = os.path.getsize(filename)
num_blocks_in_file = int((filesize - per_file_header_length)/total_bytes_per_block)
remainder = (filesize - per_file_header_length)%total_bytes_per_block
if not remainder == 0:
    print 'Error, data file ends with incomplete block'
points_per_channel = per_file_params['Points per block'] * num_blocks_in_file
print 'Number of points per channel:', points_per_channel
