#!/usr/bin/env python
# NOTE THIS IS THE INITIAL COMMIT. THIS WILL NOT WORK.

import sys
import getopt
from distutils.core import setup
from distutils.extension import Extension
import numpy

CLASSIFIERS = """\
Development Status :: 2 - Pre-Alpha
Intended Audience :: Science/Research
License :: OSI Approved :: Apache Software License
Programming Language :: Python
Programming Language :: Python :: 2.7
Programming Language :: Cython
Topic :: Scientific/Engineering
Operating System :: Microsoft :: Windows
Operating System :: POSIX
Operating System :: Unix
Operating System :: MacOS
"""

with open('README.rst') as file:
    long_description = file.read()

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

extensions = []
if USE_CYTHON:
    extensions += [Extension('pypore.data_file_opener', ['pypore.data_file_opener.pyx']),
                   Extension('pypore.event_finder', ['pypore.event_finder.pyx'])]
else:
    extensions += [Extension('pypore.data_file_opener',
                             ['src/pypore/.pyxbld/temp.linux-x86_64-2.7/pyrex/pypore/data_file_opener.c']),
                   Extension('pypore.event_finder',
                             ['src/pypore/.pyxbld/temp.linux-x86_64-2.7/pyrex/pypore/event_finder.c'])]

# Cythonize .pyx extensions if needed
if USE_CYTHON:
    from Cython.Build import cythonize

    extensions = cythonize(extensions)

packages = ['pypore', 'pypore.filetypes', 'pypore.filetypes.tests', 'pypore.tests', 'pypore.io',
            'pypore.io.tests', 'pypore.filetypes', 'pypore.strategies']
packages += ['pyporegui', 'pyporegui.graphicsItems', 'pyporegui.graphicsItems.tests', 'pyporegui.tests',
             'pyporegui.widgets', 'pyporegui.widgets.tests']

setup(
    name='pypore',
    version='0.0.1-dev-1',
    description='Pythonic/Cythonic Nanopore Translocation Analysis',
    long_description=long_description,
    author='Will Parkin',
    author_email='wmparkin@gmail.com',
    url='http://parkin.github.io/pypore/',
    package_dir={'': 'src'},
    packages=packages,
    requires=['numpy', 'scipy', 'tables', 'PySide', 'pyqtgraph'],
    include_dirs=[numpy.get_include()],
    ext_modules=extensions,
)


def setup_package():
    pass


if __name__ == '__main__':
    setup_package()