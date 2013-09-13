'''
Created on Sep 13, 2013

@author: parkin
'''

import tables as tb

# Description of events table
class Events(tb.IsDescription):
    arrayRow = tb.UInt32Atom()      # indicates the corresponding row in the
                                    # eventData and rawData etc VLArrays
    eventStart = tb.UInt64Atom()    # start index of the event in the data
    