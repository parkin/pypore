'''
Created on Aug 6, 2013

@author: parkin
'''
from PySide import QtGui
import os.path

import tables as tb
import numpy as np

from pyqtgraph.graphicsItems.PlotItem.PlotItem import PlotItem
from pyqtgraph.graphicsItems.ScatterPlotItem import ScatterPlotItem, SpotItem
from pyqtgraph.widgets.GraphicsLayoutWidget import GraphicsLayoutWidget
from pyqtgraph.graphicsItems.PlotCurveItem import PlotCurveItem
from pyqtgraph.functions import mkPen

class EventAnalysisWidget(GraphicsLayoutWidget):
    pass

    def __init__(self):
        super(EventAnalysisWidget, self).__init__()
        
        self.plot_eventdepth = self.addPlot(title='Event Depth')
        self.plot_eventdepth.setMouseEnabled(x=False, y=True)
        self.plot_eventdur_eventdepth = self.addPlot(name='Depth vs. Duration', title='Depth vs. Duration')
        self.plot_eventdepth.setYLink('Depth vs. Duration')
        
        self.nextRow()
        
        self.plot_scatterselect = self.addPlot(title='Single Event')
        self.plot_eventdur = self.addPlot(title='Event Duration')
        self.plot_eventdur.setXLink('Depth vs. Duration')
        self.plot_eventdur.setMouseEnabled(x=True, y=False)
        
        self.lastScatterClicked = []
        
    def addSelections(self, filenames, params):
        '''
        Plots event statistics.  
        '''
        files = []
        counts = []
        eventCount = 0
        for filename in filenames:
            h5file = tb.openFile(filename, mode='r')
            files.append(h5file)
            count = h5file.root.events.eventTable.attrs.eventCount
            eventCount += count
            counts.append(count)
        
        currentBlockade = np.empty(eventCount)
        dwellTimes = np.empty(eventCount)
        count = 0
        for j, filex in enumerate(files):
            eventTable = filex.root.events.eventTable
            sample_rate = filex.root.events.eventTable.attrs.sampleRate
            for i, row in enumerate(eventTable):
                currentBlockade[count+i] = row['currentBlockage']
                dwellTimes[count+i] = row['eventLength'] / sample_rate
            count += counts[j]
                
        color = params['color']
        newcolor = QtGui.QColor(color.red(), color.green(), color.blue(), 128)
                 
        bins = eventCount ** 0.5
        y_dt, x_dt = np.histogram(dwellTimes, bins=bins)        
        curve_dt = PlotCurveItem(x_dt, y_dt, stepMode=True, fillLevel=0, brush=newcolor)
        self.plot_eventdur.addItem(curve_dt)
        
        y_cb, x_cb = np.histogram(currentBlockade, bins=bins)        
        curve_cb = PlotCurveItem(-1.*x_cb, y_cb, stepMode=True, fillLevel=0, brush=newcolor)
        curve_cb.rotate(-90)
        self.plot_eventdepth.addItem(curve_cb)
        scatterItem = MyScatterPlotItem(size=10, pen=mkPen(None), brush=newcolor, files=filenames, counts=counts)
        scatterItem.setData(dwellTimes, currentBlockade)
        self.plot_eventdur_eventdepth.addItem(scatterItem)
        scatterItem.sigClicked.connect(self.onScatterPointsClicked)
        
        for filex in files:
            filex.close()
        
        return
    
    def removeFilter(self, index):
        self.plot_eventdur.removeItem(self.plot_eventdur.listDataItems()[index])
        self.plot_eventdepth.removeItem(self.plot_eventdepth.listDataItems()[index])
        self.plot_eventdur_eventdepth.removeItem(self.plot_eventdur_eventdepth.listDataItems()[index])
    
    def onScatterPointsClicked(self, plot, points):
        """
        Callback for when a scatter plot points are clicked.
        Highlights the points and unhighlights previously selected points.
        
        plot should be a MyScatterPlotItem
        points should be a MySpotItem
        """
        for p in self.lastScatterClicked:
            p.resetPen()
            # remove point we've already selected so we
            # can select points behind it.
            if p in points and len(points) > 1:
                points.remove(p)
#         print 'Points clicked:', points, plot
        for point in points:
            point.setPen('w', width=2)
            self.lastScatterClicked = [point]
            break # only take first point
        
        # Plot the new point clicked on the single event display
        filename, position = plot.getFileNameFromPosition(self.lastScatterClicked[0].eventPosition)
        
        h5file = tb.openFile(filename, mode='r')
        
        table = h5file.root.events.eventTable
        row = table[position]
        arrayRow = row['arrayRow']
        sampleRate = table.attrs.sampleRate
        eventLength = row['eventLength']
        rawPointsPerSide = row['rawPointsPerSide']
        n = eventLength+2*rawPointsPerSide
        
        rawData = h5file.root.events.rawData[arrayRow][:n]
        
        times = np.linspace(0.0, 1.0*n/sampleRate, n)
        
        self.plot_scatterselect.clear()
        self.plot_scatterselect.plot(times, rawData)
        # plot the event points in yellow
        self.plot_scatterselect.plot(times[rawPointsPerSide:rawPointsPerSide+eventLength],\
                                     rawData[rawPointsPerSide:rawPointsPerSide+eventLength], pen='y')
        
        # Plot the cusum levels
        nLevels = row['nLevels']
        baseline = row['baseline']
        eventStart = row['eventStart']
        # left, start-1, start, 
        levels = h5file.root.events.levels[arrayRow][:nLevels]
        indices = h5file.root.events.levelIndices[arrayRow][:nLevels+1]
        indices -= eventStart
        
        levelTimes = np.zeros(2*nLevels+4)
        levelValues = np.zeros(2*nLevels+4)
        
        levelTimes[1] = 1.0*(rawPointsPerSide-1)/sampleRate
        levelValues[0] = levelValues[1] = baseline
        i = 0
        for i in xrange(nLevels):
            levelTimes[2*i+2] = times[rawPointsPerSide] + 1.0*(indices[i])/sampleRate
            levelValues[2*i+2] = levels[i]
            if i < nLevels:
                levelTimes[2*i+3] = times[rawPointsPerSide] + 1.0*(indices[i+1])/sampleRate
                levelValues[2*i+3] = levels[i]
        i += 1        
        levelTimes[2*i+2] = times[rawPointsPerSide+eventLength]
        levelTimes[2*i+3] = times[n-1]
        levelValues[2*i+2] = levelValues[2*i+3] = baseline
        
        self.plot_scatterselect.plot(levelTimes, levelValues, pen='g')
        
        h5file.close()

class MySpotItem(SpotItem):
    
    eventPosition = 0
    
    def __init__(self, data, plot, position):
        super(MySpotItem, self).__init__(data, plot)
        self.eventPosition = position
        
class MyScatterPlotItem(ScatterPlotItem):
    
    def __init__(self, *args, **kargs):
        super(MyScatterPlotItem, self).__init__(*args, **kargs)
        self.files = kargs['files']
        self.counts = kargs['counts'] # number of events in each file
        
    def points(self):
        for i, rec in enumerate(self.data):
            if rec['item'] is None:
                rec['item'] = MySpotItem(rec, self, i)
        return self.data['item']
    
    def getFileNameFromPosition(self, position):
        """
        Returns filename, eventNumber for the 
        SpotItem position.
        """
        for i, j in enumerate(self.counts):
            if position < j:
                return self.files[i], position
            position -= j
        return None

class MyPlotItem(PlotItem):
    def __init__(self, parent = None, title = None, name = None):
        super(MyPlotItem, self).__init__(parent=parent, title=title, name=name)
        self._myItemList = []
        self._myEventItemList = []
         
    def addItem(self, item, *args, **kwargs):
        super(MyPlotItem, self).addItem(item, *args, **kwargs)
        self._myItemList.append(item)
        
    def addEventItem(self, item, *args, **kwargs):
        super(MyPlotItem, self).addItem(item, *args, **kwargs)
        self._myEventItemList.append(item)
        
    def clearEventItems(self):
        for item in self._myEventItemList:
            self.removeItem(item)
        del self._myEventItemList[:]
        
    def clear(self):
        super(MyPlotItem, self).clear()
        del self._myEventItemList[:]
        del self._myItemList[:]
        
class PlotToolBar(QtGui.QToolBar):
    '''
    A toolbar for plots, with a zoom button, check boxes for options.
    '''
    def __init__(self, parent = None):
        super(PlotToolBar, self).__init__(parent)
        
        self.widgetList = []
        
        self.decimateCheckBox = QtGui.QCheckBox()
        self.decimateCheckBox.setChecked(True)
        self.decimateCheckBox.setText('Decimate')
        self.addWidget(self.decimateCheckBox)
        
        self.plotDuringCheckBox = QtGui.QCheckBox()
        self.plotDuringCheckBox.setChecked(True)
        self.plotDuringCheckBox.setText('Plot Events')
        self.plotDuringCheckBox.setToolTip('Select to have events plotted during event finding.')
        self.addWidget(self.plotDuringCheckBox)
        
    def isDecimateChecked(self):
        '''
        Returns true if the toolbar's decimate checkbox is checked, false
        otherwise.
        '''
        return self.decimateCheckBox.isChecked()
    
    def isPlotDuringChecked(self):
        '''
        Returns true if the toolbar's plot during checkbox is checked, false
        otherwise.
        '''
        return self.plotDuringCheckBox.isChecked()

    
    def getWidgetList(self):
        return list(self.widgetList)
    
    def addWidget(self, widget, *args, **kwargs):
        self.widgetList.append(widget)
        return super(PlotToolBar, self).addWidget(widget, *args, **kwargs)
    
    

class FileListItem(QtGui.QListWidgetItem):
    '''
    Subclass of QListWidgetItem to handle filenames with long file paths.
    '''
    
    def __init__(self, filename):
        words = os.path.split(filename)
        self.simplename = words[1]
        super(FileListItem, self).__init__(self.simplename)
        self.filenames = filename
        self.directory = words[0]
        
    def getFileName(self):
        '''
        Return the filenames with the file path included.
        ex /home/user/.../filenames
        '''
        return self.filenames
    
    def getSimpleName(self):
        '''
        Return the filenames without the file path included.
        '''
        return self.simplename
    
    def getDirectory(self):
        return self.directory
    
class DataFileListItem(FileListItem):
    '''
    Is a FileListItem with a parameter.
    '''
    
    def __init__(self, filename, params):
        FileListItem.__init__(self, filename)
        self.params = params
        
    def getParams(self):
        return dict(self.params)
    
    def getParam(self, param):
        if param in self.params:
            return self.params[param]
        else:
            return None

class FilterListItem(QtGui.QListWidgetItem):
    '''
    Subclass of QListWidgetItem to handle filter list items.
    
    self.params contain the filter parameters specified by the user.
    '''
    def __init__(self, filenames, **params):
        '''
        Pass in a list of filenames
        '''
        self.filenames = filenames
        self.simplenames = []
        item_text = 'item'
        if len(filenames) > 0:
            item_text = ''
        index = 0
        for filename in filenames:
            words = os.path.split(filename)
            simplename = words[1]
            item_text = item_text + simplename
            self.simplenames.append(simplename)
            index += 1
            # don't append ', ' to last item
            if index < len(filenames):
                item_text += ', '
        super(FilterListItem, self).__init__(item_text)
        self.params = params
        if not 'color' in params:
            # give the item a default color
            self.params['color'] = QtGui.QColor.fromRgbF(0., 0., 1.)
        # set the icon color
#         self.setForeground(params['color'])
        pixmap = QtGui.QPixmap(20,20)
        pixmap.fill(self.params['color'])
        self.setIcon(QtGui.QIcon(pixmap))
        
    def getParams(self):
        return dict(self.params)
    
    def getFileNames(self):
        return list(self.filenames)
    
    def getFileNameAt(self, index):
        if 0 <= index < len(self.filenames):
            return self.filenames[index]
        else:
            return None
    
    def getSimpleNames(self):
        return list(self.simplenames)
    
    def getSimpleNameAt(self, index):
        if 0 <= index < len(self.filenames):
            return self.simplenames[index]
        else:
            return None
