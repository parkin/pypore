from pyqtgraph import PlotItem


class MyPlotItem(PlotItem):
    """
    A subclass of PlotItem that keeps track of regular items and event items separately.
    """
    def __init__(self, parent=None, title=None, name=None):
        super(MyPlotItem, self).__init__(parent=parent, title=title, name=name)
        self._myItemList = []
        self._myEventItemList = []

    def addItem(self, item, *args, **kwargs):
        super(MyPlotItem, self).addItem(item, *args, **kwargs)
        self._myItemList.append(item)

    def add_event_item(self, item, *args, **kwargs):
        super(MyPlotItem, self).addItem(item, *args, **kwargs)
        self._myEventItemList.append(item)

    def clear_event_items(self):
        for item in self._myEventItemList:
            self.removeItem(item)
        del self._myEventItemList[:]

    def clear(self):
        super(MyPlotItem, self).clear()
        del self._myEventItemList[:]
        del self._myItemList[:]