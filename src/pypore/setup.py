'''
Created on Aug 30, 2013

@author: parkin
'''
from distutils.core import setup
from distutils.extension import Extension
from Cython.Distutils import build_ext

ext_modules = [Extension("EventFinder", ["EventFinder.pyx"], libraries=["math"]),
               Extension("DataFileOpener", ["DataFileOpener.pyx"])]

setup(
  name = 'Event Finder',
  cmdclass = {'build_ext': build_ext},
  ext_modules = ext_modules
)
