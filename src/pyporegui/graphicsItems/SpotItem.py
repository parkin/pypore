from pyqtgraph.graphicsItems.ScatterPlotItem import SpotItem


class SpotItem(SpotItem):
    """
    A pyqtgraph.graphicsItems.ScatterPlotItem.SpotItem with an extra field for the event_position.
    """

    event_position = 0

    def __init__(self, data, plot, position):
        super(SpotItem, self).__init__(data, plot)
        self.event_position = position