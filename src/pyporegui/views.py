'''
Created on Aug 6, 2013

@author: parkin
'''
from PySide import QtGui
import os.path

import numpy as np

import pypore.eventDatabase as ed

from pyqtgraph.graphicsItems.PlotItem.PlotItem import PlotItem
from pyqtgraph.graphicsItems.ScatterPlotItem import ScatterPlotItem, SpotItem
from pyqtgraph.widgets.GraphicsLayoutWidget import GraphicsLayoutWidget
from pyqtgraph.graphicsItems.PlotCurveItem import PlotCurveItem
from pyqtgraph.functions import mkPen


class MyHistogramItem(PlotItem):
    
    def __init__(self, *args, **kargs):
        self.rotate = False
        if 'rotate' in kargs:
            self.rotate = kargs['rotate']
            del kargs['rotate']  # if you dont delete, MyHistogramItem will start with
                                # a PlotDataItem for some reason
        
        super(MyHistogramItem, self).__init__(*args, **kargs)
            
        self.dataArray = []
        self.bins = np.zeros(1)
        self.nbins = 0
        self.minimum = 0.
        self.maximum = 0.
        
        self.minimumArray = []
        self.maximumArray = []
        self.nbinsArray = []
            
    def addHistogram(self, data, nbins=None, color=None):
        """
        Adds a histogram to the plot.
        
        data should be 1D numpy array
        
        nbins = number of bins for numpy.histogram()
               default is nbins = sqrt(data.size)
        """
        if nbins == None:
            nbins = data.size ** 0.5
            
        minimum = data.min()
        maximum = data.max()
        
        self.minimumArray.append(minimum)
        self.maximumArray.append(maximum)
        self.nbinsArray.append(nbins)
        
        # if this is the first histogram plotted,
        # initialize settings
        if len(self.dataArray) < 1:
            self.minimum = minimum
            self.maximum = maximum
            self.nbins = nbins
            self.bins = np.linspace(self.minimum, self.maximum, self.nbins + 1)
        
        # replot the other histograms with this new
        # binning if needed
        rehist = False
        if minimum < self.minimum:
            self.minimum = minimum
            rehist = True
        if maximum > self.maximum:
            self.maximum = maximum
            rehist = True
        if nbins > self.nbins:
            self.nbins = nbins
            rehist = True
            
        if rehist:
            self.reHistogram()
            
        self.plotHistogram(data, color)
        
    def plotHistogram(self, data, color=None):
        if color == None:
            color = QtGui.QColor(0, 0, 255, 128)
            
        y, x = np.histogram(data, bins=self.bins)
        
        if self.rotate:
            x = -1. * x
        curve = PlotCurveItem(x, y, stepMode=True, fillLevel=0, brush=color)
        if self.rotate:
            curve.rotate(-90)
        self.addItem(curve)
        
        self.dataArray.append(data)
        
    def reHistogram(self):
        self.bins = np.linspace(self.minimum, self.maximum, self.nbins + 1)
        items = self.listDataItems()
        for i, item in enumerate(items):
            y, x = np.histogram(self.dataArray[i], bins=self.bins)
            if self.rotate:
                x = -1. * x
            item.setData(x, y)
            
    def removeItemAt(self, index):
        if len(self.dataArray) < 1:
            return
        
        self.removeItem(self.listDataItems()[index])
        del self.dataArray[index]
        del self.minimumArray[index]
        del self.maximumArray[index]
        del self.nbinsArray[index]
        
        # return if no more histograms to display
        if len(self.dataArray) < 1:
            return
        
        reHist = False
        # do we need to replot?
        maxi = max(self.maximumArray)
        if maxi < self.maximum:
            reHist = True
            self.maximum = maxi
        mini = min(self.minimumArray)
        if mini > self.minimum:
            reHist = True
            self.minimum = mini
        nb = max(self.nbinsArray)
        if nb < self.nbins:
            reHist = True
            self.nbins = nb
            
        if reHist:
            self.reHistogram()

class EventAnalysisWidget(GraphicsLayoutWidget):

    def __init__(self):
        super(EventAnalysisWidget, self).__init__()
        
        self.plot_eventdepth = MyHistogramItem(title='Event Depth', rotate=True)
        self.addItem(self.plot_eventdepth)
        self.plot_eventdepth.setMouseEnabled(x=False, y=True)
        self.plot_eventdur_eventdepth = self.addPlot(name='Depth vs. Duration', title='Depth vs. Duration')
        self.plot_eventdepth.setYLink('Depth vs. Duration')
        
        self.nextRow()
        
        self.plot_scatterselect = self.addPlot(title='Single Event')
        
        self.plot_eventdur = MyHistogramItem(title='Event Duration')
        self.addItem(self.plot_eventdur)
        self.plot_eventdur.setXLink('Depth vs. Duration')
        self.plot_eventdur.setMouseEnabled(x=True, y=False)
        
        self.lastScatterClicked = []
        
        self.nbins = 0
        self.bins = np.zeros(0)
        
    def addSelections(self, filenames, params):
        '''
        Plots event statistics.  
        '''
        files = []
        counts = []
        eventCount = 0
        for filename in filenames:
            h5file = ed.openFile(filename, mode='r')
            files.append(h5file)
            count = h5file.getEventCount()
            eventCount += count
            counts.append(count)
        
        currentBlockade = np.empty(eventCount)
        dwellTimes = np.empty(eventCount)
        count = 0
        for j, filex in enumerate(files):
            eventTable = filex.getEventTable()
            sample_rate = filex.getSampleRate()
            for i, row in enumerate(eventTable):
                currentBlockade[count + i] = row['currentBlockage']
                dwellTimes[count + i] = row['eventLength'] / sample_rate
            count += counts[j]
                
        color = params['color']
        newcolor = QtGui.QColor(color.red(), color.green(), color.blue(), 128)
                 
        self.plot_eventdur.addHistogram(dwellTimes, color=newcolor)
        
        self.plot_eventdepth.addHistogram(currentBlockade, color=newcolor)
        
        scatterItem = MyScatterPlotItem(size=10, pen=mkPen(None), brush=newcolor, files=filenames, counts=counts)
        scatterItem.setData(dwellTimes, currentBlockade)
        self.plot_eventdur_eventdepth.addItem(scatterItem)
        scatterItem.sigClicked.connect(self.onScatterPointsClicked)
        
        for filex in files:
            filex.close()
        
        return
    
    def removeFilter(self, index):
        self.plot_eventdur.removeItemAt(index)
        self.plot_eventdepth.removeItemAt(index)
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
            break  # only take first point
        
        # Plot the new point clicked on the single event display
        filename, position = plot.getFileNameFromPosition(self.lastScatterClicked[0].eventPosition)
        
        h5file = ed.openFile(filename, mode='r')
        
        table = h5file.root.events.eventTable
        row = h5file.getEventRow(position)
        arrayRow = row['arrayRow']
        sampleRate = h5file.getSampleRate()
        eventLength = row['eventLength']
        rawPointsPerSide = row['rawPointsPerSide']
        
        rawData = h5file.getRawDataAt(arrayRow)
        
        n = len(rawData)
        
        times = np.linspace(0.0, 1.0 * n / sampleRate, n)
        
        self.plot_scatterselect.clear()
        self.plot_scatterselect.plot(times, rawData)
        # plot the event points in yellow
        self.plot_scatterselect.plot(times[rawPointsPerSide:rawPointsPerSide + eventLength], \
                                     rawData[rawPointsPerSide:rawPointsPerSide + eventLength], pen='y')
        
        # Plot the cusum levels
        nLevels = row['nLevels']
        baseline = row['baseline']
        # left, start-1, start, 
        levels = h5file.getLevelsAt(arrayRow)
        indices = h5file.getLevelLengthsAt(arrayRow)
        
        levelTimes = np.zeros(2 * nLevels + 4)
        levelValues = np.zeros(2 * nLevels + 4)
        
        levelTimes[1] = 1.0 * (rawPointsPerSide - 1) / sampleRate
        levelValues[0] = levelValues[1] = baseline
        i = 0
        length = 0
        for i in xrange(nLevels):
            levelTimes[2 * i + 2] = times[rawPointsPerSide] + 1.0 * (length) / sampleRate
            levelValues[2 * i + 2] = levels[i]
            levelTimes[2 * i + 3] = times[rawPointsPerSide] + 1.0 * (length + indices[i]) / sampleRate
            levelValues[2 * i + 3] = levels[i]
            length += indices[i]
        i += 1        
        levelTimes[2 * i + 2] = times[rawPointsPerSide + eventLength]
        levelTimes[2 * i + 3] = times[n - 1]
        levelValues[2 * i + 2] = levelValues[2 * i + 3] = baseline
        
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
        self.counts = kargs['counts']  # number of events in each file
        
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
    def __init__(self, parent=None, title=None, name=None):
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
    def __init__(self, parent=None):
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
        
        self.filterData = QtGui.QCheckBox()
        self.filterData.setChecked(True)
        self.filterData.setText('Show filtered')
        self.filterData.setToolTip('Select to have events plotted during event finding.')
        self.addWidget(self.filterData)
        
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
        pixmap = QtGui.QPixmap(20, 20)
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
