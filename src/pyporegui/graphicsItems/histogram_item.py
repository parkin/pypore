from PySide import QtGui
import numpy as np
from pyqtgraph import PlotItem
from pyqtgraph.graphicsItems.PlotCurveItem import PlotCurveItem


class HistogramItem(PlotItem):
    def __init__(self, *args, **kwargs):
        self.rotate = False
        if 'rotate' in kwargs:
            self.rotate = kwargs['rotate']
            del kwargs['rotate']  # if you don't delete, MyHistogramItem will start with
            # a PlotDataItem for some reason

        super(HistogramItem, self).__init__(*args, **kwargs)

        self.data_array = []
        self.bins = np.zeros(1)
        self.n_bins = 0
        self.minimum = 0.
        self.maximum = 0.

        self.minimum_array = []
        self.maximum_array = []
        self.n_bins_array = []

    def add_histogram(self, data, n_bins=None, color=None):
        """
        Adds a histogram to the plot.

        :param numpyArray data: Data for histogram.
        :param IntType n_bins: Number of bins for the histogram. Default value is sqrt(data.size).
        :param QtGui.QColor color: (Optional) color of the new histogram.
        """
        if n_bins is None:
            n_bins = data.size ** 0.5

        minimum = data.min()
        maximum = data.max()

        self.minimum_array.append(minimum)
        self.maximum_array.append(maximum)
        self.n_bins_array.append(n_bins)

        # if this is the first histogram plotted,
        # initialize_c settings
        if len(self.data_array) < 1:
            self.minimum = minimum
            self.maximum = maximum
            self.n_bins = n_bins
            self.bins = np.linspace(self.minimum, self.maximum, int(self.n_bins + 1))

        # re-plot the other histograms with this new
        # binning if needed
        re_hist = False
        if minimum < self.minimum:
            self.minimum = minimum
            re_hist = True
        if maximum > self.maximum:
            self.maximum = maximum
            re_hist = True
        if n_bins > self.n_bins:
            self.n_bins = n_bins
            re_hist = True

        if re_hist:
            self._re_histogram()

        self._plot_histogram(data, color)

    def _plot_histogram(self, data, color=None):
        if color is None:
            color = QtGui.QColor(0, 0, 255, 128)

        # Copy self.bins, otherwise it is returned as x, which we can accidentally modify
        # by x *= -1, leaving self.bins modified.
        bins = self.bins.copy()
        y, x = np.histogram(data, bins=bins)

        if self.rotate:
            x *= -1.
        curve = PlotCurveItem(x, y, stepMode=True, fillLevel=0, brush=color)
        if self.rotate:
            curve.rotate(-90)
        self.addItem(curve)

        self.data_array.append(data)

    def _re_histogram(self):
        self.bins = np.linspace(self.minimum, self.maximum, self.n_bins + 1)
        items = self.listDataItems()
        for i, item in enumerate(items):
            # Copy self.bins, otherwise it is returned as x, which we can accidentally modify
            # by x *= -1, leaving self.bins modified.
            bins = self.bins.copy()
            y, x = np.histogram(self.data_array[i], bins=bins)
            if self.rotate:
                x *= -1.
            item.setData(x, y)

    def remove_item_at(self, index):
        """
        Removes the histogram item at index.

        :param IntType index: Index of the histogram to remove.
        """
        if len(self.data_array) < 1:
            return

        self.removeItem(self.listDataItems()[index])
        del self.data_array[index]
        del self.minimum_array[index]
        del self.maximum_array[index]
        del self.n_bins_array[index]

        # return if no more histograms to display
        if len(self.data_array) < 1:
            return

        re_hist = False
        # do we need to re-plot?
        maxi = max(self.maximum_array)
        if maxi < self.maximum:
            re_hist = True
            self.maximum = maxi
        mini = min(self.minimum_array)
        if mini > self.minimum:
            re_hist = True
            self.minimum = mini
        nb = max(self.n_bins_array)
        if nb < self.n_bins:
            re_hist = True
            self.n_bins = nb

        if re_hist:
            self._re_histogram()