import os
import numpy
import pyximport

if os.name == 'nt':
    if os.environ.has_key('CPATH'):
        os.environ['CPATH'] = os.environ['CPATH'] + numpy.get_include()
    else:
        os.environ['CPATH'] = numpy.get_include()

    # XXX: we're assuming that MinGW is installed in C:\MinGW (default)
    if os.environ.has_key('PATH'):
        os.environ['PATH'] = os.environ['PATH'] + ';C:\MinGW\bin'
    else:
        os.environ['PATH'] = 'C:\MinGW\bin'

    mingw_setup_args = {'options': {'build_ext': {'cimpiler': 'mingw32'}}}
    pyximport.install(setup_args=mingw_setup_args)

elif os.name == 'posix':
    if os.environ.has_key('CFLAGS'):
        os.environ['CFLAGS'] = os.environ['CFLAGS'] + ' -I' + numpy.get_include()
    else:
        os.environ['CFLAGS'] = ' -I' + numpy.get_include()

    pyximport.install()


if os.environ.has_key('PYTHONPATH'):
    os.environ['PYTHONPATH'] = os.environ['PYTHONPATH'] + 
else:
    os.environ['CFLAGS'] = ' -I' + numpy.get_include()

