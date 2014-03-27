Installation
============

Basic Installation Steps
--------------------------

The dependencies of :py:mod:`pypore` are:

#. `Python v2.7.+ <http://www.python.org/>`_
#. `Cython <http://cython.org/>`_
#. `SciPy <http://www.scipy.org/>`_
#. `NumPy <http://www.numpy.org/>`_
#. `PyTables <http://www.pytables.org/>`_
#. `C Compiler`_

:py:mod:`pyporegui` depends on all of :py:mod:`pypore`'s above dependencies, along with the following:

#. `PySide <http://qt-project.org/wiki/PySide>`_
#. `PyQtGraph <http://www.pyqtgraph.org/>`_

These packages can be installed individually, but it is **strongly** recommended that you use a complete scientific
Python distribution, especially on Windows and Mac OS X.

Recommended distributions are:

#. `Anaconda <https://store.continuum.io/cshop/anaconda>`_
#. `EPD <http://www.enthought.com/products/epd.php>`_
#. `Python(x,y) <http://code.google.com/p/pythonxy/>`_
#. `WinPython <http://code.google.com/p/winpython/>`_

These distributions ship with a bunch of widely-used python libraries. When installing one of these distributions,
ensure that the above libraries are installed.
`PyQtGraph <http://www.pyqtgraph.org/>`_ is the least likely library to ship with one of the distributions,
so after installing a distribution, go to
`PyQtGraph <http://www.pyqtgraph.org/>`_, which has binary installers.

C Compiler
-----------
In order to compile and use the modules written in `Cython <http://cython.org/>`_, you will need a C compiler.
The :py:mod:`pypore.cythonsetup` module sets up the compiler based on the detected OS.

For Linux and Mac, ``gcc`` is used.

Fow Windows, `MinGW <http://www.mingw.org/>`_ is used.

    - MinGW is packaged and can be installed during the `Python(x,y) <http://code.google.com/p/pythonxy/>`_\
        installation process. Make sure to check it during installation.
    - Hopefully this is true of the other distributions.

Get the Code
-----------------
`Fork me on GitHub! <https://github.com/parkin/pypore>`_.

`Download .zip file <https://github.com/parkin/pypore/zipball/master>`_.

`Download .tar.gz file <https://github.com/parkin/pypore/tarball/master>`_.

