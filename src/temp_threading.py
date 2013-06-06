'''
Created on Jun 5, 2013

@author: parkin
'''

import sys, time
from PyQt4 import QtCore, QtGui

class WorkThread(QtCore.QThread):
    def __init__(self):
        QtCore.QThread.__init__(self)
    
    def __del__(self):
        '''
        If the object instantiating this thread gets deleted, the thread will be deleted, causing
        a segfault, unless we implement this destructor.
        '''
        self.wait()
    
    def run(self):
        for i in range(6):
            time.sleep(0.3) # artificial time delay
            self.emit( QtCore.SIGNAL('update(QString)'), "from work thread " + str(i) )
        return
 
class MyApp(QtGui.QWidget):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
 
        self.setGeometry(300, 300, 280, 600)
        self.setWindowTitle('threads')
        
        self.layout = QtGui.QVBoxLayout(self)
        
        self.testButton = QtGui.QPushButton("test")
        self.connect(self.testButton, QtCore.SIGNAL("released()"), self.test)
        self.listwidget = QtGui.QListWidget(self)
        
        self.layout.addWidget(self.testButton)
        self.layout.addWidget(self.listwidget)
        
        self.threadPool = []

    def add(self, text):
        """ Add item to list widget """
        print "Add: " + text
        self.listwidget.addItem(text)
        self.listwidget.sortItems()
 
    def addBatch(self,text="test",iters=6,delay=0.3):
        """ Add several items to list widget """
        for i in range(iters):
            time.sleep(delay) # artificial time delay
            self.add(text+" "+str(i))
 
    def test(self):
        self.listwidget.clear()
        # adding entries just from main application: locks ui
        self.addBatch("_non_thread",iters=6,delay=0.3)
        
        # adding by emitting signal in different thread
        self.threadPool.append( WorkThread() )
        self.connect( self.threadPool[len(self.threadPool)-1], QtCore.SIGNAL("update(QString)"), self.add )
        self.threadPool[len(self.threadPool)-1].start()

if __name__ == '__main__':
    # run
    app = QtGui.QApplication(sys.argv)
    test = MyApp()
    test.show()
    app.exec_()