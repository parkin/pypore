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
        self.filename = filename
        self.simplename = name_without_path
        
        
    def getFilename(self):
        '''
        Return the filename with the file path included.
        ex /home/user/.../filename
        '''
        return self.filename
    
    def getSimpleName(self):
        '''
        Return the filename without the file path included.
        '''
        return self.simplename
