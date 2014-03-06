"""
@author: `@parkin1`_
This module sets up pyximport so that any .pyx file is automatically
compiled on import.

This file should be imported before importing any cython modules.
(Unless building cython modules yourself).

This automatically chooses the correct C compiler based on the operating
system, ie MinGW for Windows, gcc for Unix.

To import a Cython module, for example :py:mod:`pypore.eventFinder`, simply do:

>>> import pypore.cythonsetup
>>> import pypore.eventFinder
"""

import os
import sys
import numpy
import pyximport

mingw_setup_args = {}

# If Windows, we want to compile with the windows c compiler, MinGW
if os.name == 'nt':
    if os.environ.has_key('CPATH'):
        os.environ['CPATH'] = os.environ['CPATH'] + numpy.get_include()
    else:
        os.environ['CPATH'] = numpy.get_include()

    # XXX: we're assuming that MinGW is installed in C:\MinGW (default)
    if os.environ.has_key('PATH'):
        os.environ['PATH'] = os.environ['PATH'] + ';' + 'C:\\MinGW\\bin'
    else:
        os.environ['PATH'] = 'C:\\MinGW\\bin'

    mingw_setup_args = {'options': {'build_ext': {'compiler': 'mingw32'}}}

# If Unix
elif os.name == 'posix':
    if os.environ.has_key('CFLAGS'):
        os.environ['CFLAGS'] = os.environ['CFLAGS'] + ' -I' + numpy.get_include()
    else:
        os.environ['CFLAGS'] = ' -I' + numpy.get_include()

dir_name = os.path.dirname(os.path.realpath(__file__))
    
pyximport.install(setup_args=mingw_setup_args,
                      build_dir= os.path.join(dir_name, '.pyxbld'))

package_path = os.path.dirname(dir_name)

# append directory that contains pypore and pyporegui to 
# PYTHONPATH
if not package_path in sys.path:
    sys.path.append(package_path)

