**master** branch

.. image:: https://travis-ci.org/parkin/pypore.svg?branch=master 
    :target: https://travis-ci.org/parkin/pypore
    
.. image:: https://coveralls.io/repos/parkin/pypore/badge.png?branch=master
    :target: https://coveralls.io/r/parkin/pypore?branch=master

**develop** branch

.. image:: https://travis-ci.org/parkin/pypore.svg?branch=develop
    :target: https://travis-ci.org/parkin/pypore
    
.. image:: https://coveralls.io/repos/parkin/pypore/badge.png?branch=develop
    :target: https://coveralls.io/r/parkin/pypore?branch=develop
   
Pypore
=======

This project is for nanopore-translocation event finding/analysis.
It's written in Python, with `numpy <http://www.numpy.org/>`_/`scipy <http://www.scipy.org/>`_ as a Matlab replacement.
The gui library is `pyside <http://qt-project.org/wiki/PySide>`_, and `pyqtgraph <http://www.pyqtgraph.org/>`_ is used for plotting.
More information can be found `here <http://parkin.github.io/pypore>`_.

**Note** that Pypore/PyporeGui are pre-release, major changes can happen at any time.

Pull requests are welcome!

Installing
----------

Dependencies
++++++++++++

Pypore has the following dependencies:

* numpy
* scipy
* PyTables

PyporeGui depends on all of the above and:

* PySide
* pyqtgraph

Building from source additionally requires:

* Cython

Running the tests requires:

* nose

Installing with pip
+++++++++++++++++++

Pypore is currently pre-release, so we'll install with the **--pre** tag.

.. code:: shell

    pip install pypore --pre
    
A new dev release is deployed with every push to the **develop** branch, so upgrade often!

.. code:: shell

    pip install pypore --pre --upgrade
    
Installing from source
++++++++++++++++++++++

Clone or download the source. In the directory (with setup.py), run one of the following:

.. code:: shell

    python setup.py install
    
or

.. code:: shell

    pip install .
    
Running the tests:

.. code:: shell

    python setup.py tests
    
PyporeGui
=========

Start PyporeGui with:

.. code:: python

    import pyporegui
    pyporegui.start()


License
=======

    Copyright 2014 Will Parkin
    
    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.
