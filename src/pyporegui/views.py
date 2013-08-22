'''
Created on Aug 6, 2013

@author: parkin
'''
from PySide import QtGui
import os.path
from pyqtgraph.graphicsItems.PlotItem.PlotItem import PlotItem

class MyPlotItem(PlotItem):
    def __init__(self, parent = None, title = None, name = None):
        super(MyPlotItem, self).__init__(parent=parent, title=title, name=name)
        self.myItemList = []
        self.myEventItemList = []
         
    def addItem(self, item, params=None):
        super(MyPlotItem, self).addItem(item, params)
        self.myItemList.append(item)
        
    def addEventItem(self, item, params=None):
        super(MyPlotItem, self).addItem(item, params)
        self.myEventItemList.append(item)
        
    def clearEventItems(self):
        for item in self.myEventItemList:
            self.removeItem(item)

class PlotToolBar(QtGui.QToolBar):
    '''
    A toolbar for plots, with a zoom button, check boxes for options.
    '''
    def __init__(self, parent = None):
        super(PlotToolBar, self).__init__(parent)
        
        self.decimateCheckBox = QtGui.QCheckBox()
        self.decimateCheckBox.setChecked(True)
        self.decimateCheckBox.setText('Decimate')
        self.addWidget(self.decimateCheckBox)
        
        self.plotDuringCheckBox = QtGui.QCheckBox()
        self.plotDuringCheckBox.setChecked(True)
        self.plotDuringCheckBox.setText('Plot Events')
        self.plotDuringCheckBox.setToolTip('Select to have events plotted during event finding.')
        self.addWidget(self.plotDuringCheckBox)
        
        self.widgetList = []
        self.callbackList = []
        self.widgetList.append(self.decimateCheckBox)
        self.widgetList.append(self.plotDuringCheckBox)
        
        for _ in self.widgetList:
            self.callbackList.append(None)
        
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
