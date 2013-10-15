'''
Created on Aug 6, 2013

@author: parkin
'''
from PySide import QtGui
import os.path
from pyqtgraph.graphicsItems.PlotItem.PlotItem import PlotItem
from pyqtgraph.graphicsItems.ScatterPlotItem import ScatterPlotItem, SpotItem

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
