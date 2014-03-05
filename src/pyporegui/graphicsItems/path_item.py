from PySide import QtGui, QtCore
import pyqtgraph as pg


class PathItem(QtGui.QGraphicsPathItem):
    def __init__(self, x, y, conn='all'):
        xr = x.min(), x.max()
        yr = y.min(), y.max()
        self._bounds = QtCore.QRectF(xr[0], yr[0], xr[1] - xr[0], yr[1] - yr[0])
        self.path = pg.arrayToQPath(x, y, conn)
        QtGui.QGraphicsPathItem.__init__(self, self.path)

    def boundingRect(self):
        return self._bounds

