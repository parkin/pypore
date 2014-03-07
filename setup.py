
# NOTE THIS IS THE INITIAL COMMIT. THIS WILL NOT WORK.

import sys, getopt
from distutils.core import setup, Extension

# get command line arguments
argv = sys.argv[1:]

USE_CYTHON = False

# Check to see if we want to build using Cython. If not, we'll assume there are .c files we can compile.
opts = args = []
try:
    opts, args = getopt.getopt(argv, '', ['use-cython'])
    for opt, arg in opts:
        if opt in ('--use-cython'):
            USE_CYTHON = True
except getopt.GetoptError:
    pass

# Set up the .c or .pyx (Cython) extensions
ext = '.pyx' if USE_CYTHON else '.c'

extensions = [Extension('*', '*' + ext)]

# Cythonize .pyx extensions if needed
if USE_CYTHON:
    from Cython.Build import cythonize
    extensions = cythonize(extensions)

setup(
    name='pypore',
    description='Pythonic/Cythonic Nanopore Translocation Analysis',
    author='Will Parkin',
    author_email='wmparkin@gmail.com',
    url='http://parkin1.github.io/pypore/',
    package_dir={'': 'src'},
    requires=['numpy', 'scipy', 'tables', 'PySide', 'pyqtgraph'],
    #ext_modules = cythonize(extensions), requires=['PySide']

)