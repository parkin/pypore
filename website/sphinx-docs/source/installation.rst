Installation
============



Basic Installation Steps
------------------

The main steps to get all of the dependencies are:

#. Install Python v2.7
#. Install NumPy
#. Install SciPy
#. Install PySide
#. Install PyQtGraph


Windows Installation
-----------------

Install Python v2.7
++++++++++++++++++

The Python v2.7.5 Windows installer can be found `here <http://www.python.org/download/releases/2.7.5/>`_.

If you right click on My Computer -> Properties -> General:

* If under 'System:' it says 'x64' then you need the 64 bit version: the x86-64 MSI installer.
* If not, you need the 32 bit version: x86  MSI installer.

Install Cython
++++++++++++++++++
Next, use easy_install to install Cython.  In the command prompt, type:

``c:\Python27\Scripts\easy_install cython``

Install NumPy
++++++++++++++++

Next, use easy_install to install numpy.  Open the command prompt (Start->Run->type 'cmd' hit Enter) and type:

``c:\Python27\Scripts\easy_install install numpy``

Install SciPy
+++++++++++++++

Download and execute the latest SciPy installer from `here <http://sourceforge.net/projects/scipy/>`_.

Install PySide
++++++++++++++

Next, use easy_install to install PySide.  Open the command prompt (Start->Run->type 'cmd' hit Enter) and type:

``c:\Python27\Scripts\easy_install PySide``

You've just installed PySide!

Install PyQtGraph
+++++++++++++++
Use easy_install as before, in a command prompt type:

``c:\Python27\Scripts\easy_install pyqtgraph``

You now have all of the dependencies and are ready to `Get the Code`_.

Get the Code
-----------------

Install Git, see above for instructions.  Sign up for a BitBucket account, see above.  Before cloning the repository, you will need to be added by **wmparkin** with at least read access.

On Linux, open a terminal.  On Windows, open the 'Git Bash' program.  `Navigate <http://linuxcommand.org/lts0020.php>`_ to where you want the files to be downloaded.

Type the command

``git clone https://<user name>@bitbucket.org/wmparkin/translocationcode-python.git``

You now have the code!  To run, navigate to project/src/pyporegui directory, double click eventanalysis.py!
