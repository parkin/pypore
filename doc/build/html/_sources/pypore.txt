pypore
============

**pypore** is a package for analyzing translocation data.  It is written in `Cython <http://cython.org/>`_, a superset of `Python <http://www.python.org/>`_ that provides an optimising static compiler.  Cython compiles Python and Cython code to C code, then the C code is compiled with the systems C compiler.  Basically, this allows you to **significantly speed up** computationally intensive Python code.


Using pypore
------------------

If you are trying to use a module with a .pyx extension (ie Cython code) it must be compiled first.  This can be accomplished by importing **cythonsetup**

.. sourcecode:: python
    import cythonsetup
    import EventFinder
        

Install Python v2.7
++++++++++++++++++
