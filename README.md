# TranslocationCode-Python
This project is for translocation event finding/analysis.  The aim is to use only free tools, so it can be used/contributed to by anyone.  It's written in Python, with numpy/scipy as a matlab replacement.  The gui library is pyqt, and pyqwt is used for plotting.

# Running
To run, in shell do './eventanalysis'

# TODO
* Use one file format for data files.  Make a tool for converting other files, like Heka or Chimera or others.
* Allow user to only analyze a section of the graph by highlighting the graph.
* Allow user to calculate the baseline by highlighting a section of the graph.
* Make more interactive tools for the graphs
* Make it possible to choose different algorithms (event finding, etc.) or import your own.
* Put all of the non-gui related things in its own package, so the tools can be used outside of the gui.

