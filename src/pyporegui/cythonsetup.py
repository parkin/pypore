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

dirname = os.path.dirname(os.path.realpath(__file__))
    
pyximport.install(setup_args=mingw_setup_args,
                      build_dir= os.path.join(dirname, '.pyxbld'))

packagepath = os.path.dirname(dirname)

sys.path.append(packagepath)

