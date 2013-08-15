'''
Created on Aug 6, 2013

@author: parkin
'''
import PySide
from pyqtgraph import QtGui, PlotItem

# zoom picture? copied from BodeDemo
zoom_xpm = ['32 32 8 1',
            '# c #000000',
            'b c #c0c0c0',
            'a c #ffffff',
            'e c #585858',
            'd c #a0a0a4',
            'c c #0000ff',
            'f c #00ffff',
            '. c None',
            '..######################........',
            '.#a#baaaaaaaaaaaaaaaaaa#........',
            '#aa#baaaaaaaaaaaaaccaca#........',
            '####baaaaaaaaaaaaaaaaca####.....',
            '#bbbbaaaaaaaaaaaacccaaa#da#.....',
            '#aaaaaaaaaaaaaaaacccaca#da#.....',
            '#aaaaaaaaaaaaaaaaaccaca#da#.....',
            '#aaaaaaaaaabe###ebaaaaa#da#.....',
            '#aaaaaaaaa#########aaaa#da#.....',
            '#aaaaaaaa###dbbbb###aaa#da#.....',
            '#aaaaaaa###aaaaffb###aa#da#.....',
            '#aaaaaab##aaccaaafb##ba#da#.....',
            '#aaaaaae#daaccaccaad#ea#da#.....',
            '#aaaaaa##aaaaaaccaab##a#da#.....',
            '#aaaaaa##aacccaaaaab##a#da#.....',
            '#aaaaaa##aaccccaccab##a#da#.....',
            '#aaaaaae#daccccaccad#ea#da#.....',
            '#aaaaaab##aacccaaaa##da#da#.....',
            '#aaccacd###aaaaaaa###da#da#.....',
            '#aaaaacad###daaad#####a#da#.....',
            '#acccaaaad##########da##da#.....',
            '#acccacaaadde###edd#eda#da#.....',
            '#aaccacaaaabdddddbdd#eda#a#.....',
            '#aaaaaaaaaaaaaaaaaadd#eda##.....',
            '#aaaaaaaaaaaaaaaaaaadd#eda#.....',
            '#aaaaaaaccacaaaaaaaaadd#eda#....',
            '#aaaaaaaaaacaaaaaaaaaad##eda#...',
            '#aaaaaacccaaaaaaaaaaaaa#d#eda#..',
            '########################dd#eda#.',
            '...#dddddddddddddddddddddd##eda#',
            '...#aaaaaaaaaaaaaaaaaaaaaa#.####',
            '...########################..##.']

# class MyPlotWidget(PlotWidget):
#     
#     def __init__(self, parent = None, title = None, name = None):
#         PlotWidget.__init__(self, parent, title=title, name=name)
#         self.itemList = []
#         
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
        QtGui.QToolBar.__init__(self, parent)
        
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

class FileListItem(QtGui.QListWidgetItem):
    '''
    Subclass of QListWidgetItem to handle filenames with long file paths.
    '''
    
    def __init__(self, filename):
        words = filename.split('/')
        name_without_path = words[len(words)-1]
        QtGui.QListWidgetItem.__init__(self, name_without_path)
        self.filenames = filename
        self.simplename = name_without_path
        
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
    
class DataFileListItem(FileListItem):
    '''
    Is a FileListItem with a parameter.
    '''
    
    def __init__(self, filename, params):
        FileListItem.__init__(self, filename)
        self.params = params
        
    def getParams(self):
        return self.params
    
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
    def __init__(self, filenames, params):
        '''
        Pass in a list of filenames
        '''
        self.filenames = filenames
        self.simplenames = []
        item_text = ''
        for filename in filenames:
            words = filename.split('/')
            simplename = words[len(words)-1]
            item_text = item_text + str(simplename) + ', '
            self.simplenames.append(simplename)
        QtGui.QListWidgetItem.__init__(self, item_text)
        self.params = params
        if 'color' in params:
            self.setForeground(params['color'])
        else:
            print 'FilterListItem should be passed params with a \'color\' key'
        
    def getParams(self):
        return self.params
    
    def getFileNames(self):
        return self.filenames
    
    def getFileNameAt(self, index):
        if index < len(self.filenames):
            return self.filenames[index]
        else:
            return None
    
    def getSimpleNames(self):
        return self.simplenames
    
    def getSimpleNameAt(self, index):
        if index < len(self.filenames):
            return self.simplenames[index]
        else:
            return None
