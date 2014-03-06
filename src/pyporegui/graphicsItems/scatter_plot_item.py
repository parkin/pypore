from pyqtgraph.graphicsItems.ScatterPlotItem import ScatterPlotItem
from pyporegui.graphicsItems.spot_item import SpotItem


class ScatterPlotItem(ScatterPlotItem):

    def __init__(self, *args, **kargs):
        super(ScatterPlotItem, self).__init__(*args, **kargs)
        self.files = kargs['files']
        self.counts = kargs['counts']  # number of events in each file

    def points(self):
        for i, rec in enumerate(self.data):
            if rec['item'] is None:
                rec['item'] = SpotItem(rec, self, i)
        return self.data['item']

    def get_file_name_from_position(self, position):
        """
        Returns filename, eventNumber for the
        SpotItem position.
        """
        for i, j in enumerate(self.counts):
            if position < j:
                return self.files[i], position
            position -= j
        return None