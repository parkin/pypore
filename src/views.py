'''
Created on Aug 6, 2013

@author: parkin
'''
from PyQt4.QtGui import QListWidgetItem

class FileListItem(QListWidgetItem):
    '''
    Subclass of QListWidgetItem to handle filenames with long file paths.
    '''
    
    def __init__(self, filename):
        words = filename.split('/')
        name_without_path = words[len(words)-1]
        QListWidgetItem.__init__(self, name_without_path)
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

class FilterListItem(QListWidgetItem):
    '''
    Subclass of QListWidgetItem to handle filter list items.
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
        QListWidgetItem.__init__(self, item_text)
        self.params = params
        if 'color' in params:
            self.setTextColor(params['color'])
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
