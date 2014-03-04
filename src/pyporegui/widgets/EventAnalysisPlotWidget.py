from PySide import QtGui
import numpy as np
from pyqtgraph import GraphicsLayoutWidget, mkPen
from pypore import eventDatabase as eD
from pyporegui.graphicsItems.HistogramItem import HistogramItem
from pyporegui.views import MyScatterPlotItem

__all__ = ['EventAnalysisPlotWidget']


class EventAnalysisPlotWidget(GraphicsLayoutWidget):

    def __init__(self):
        super(EventAnalysisPlotWidget, self).__init__()

        self.plot_eventdepth = HistogramItem(title='Event Depth', rotate=True)
        self.addItem(self.plot_eventdepth)
        self.plot_eventdepth.setMouseEnabled(x=False, y=True)
        self.plot_eventdur_eventdepth = self.addPlot(name='Depth vs. Duration', title='Depth vs. Duration')
        self.plot_eventdepth.setYLink('Depth vs. Duration')

        self.nextRow()

        self.plot_scatterselect = self.addPlot(title='Single Event')

        self.plot_eventdur = HistogramItem(title='Event Duration')
        self.addItem(self.plot_eventdur)
        self.plot_eventdur.setXLink('Depth vs. Duration')
        self.plot_eventdur.setMouseEnabled(x=True, y=False)

        self.lastScatterClicked = []

        self.nbins = 0
        self.bins = np.zeros(0)

    def add_selections(self, file_names, params):
        '''
        Plots event statistics.
        '''
        files = []
        counts = []
        eventCount = 0
        for filename in file_names:
            h5file = eD.openFile(filename, mode='r')
            files.append(h5file)
            count = h5file.getEventCount()
            eventCount += count
            counts.append(count)

        currentBlockade = np.empty(eventCount)
        dwellTimes = np.empty(eventCount)
        count = 0
        for j, filex in enumerate(files):
            eventTable = filex.getEventTable()
            sample_rate = filex.getSampleRate()
            for i, row in enumerate(eventTable):
                currentBlockade[count + i] = row['currentBlockage']
                dwellTimes[count + i] = row['eventLength'] / sample_rate
            count += counts[j]

        color = params['color']
        newcolor = QtGui.QColor(color.red(), color.green(), color.blue(), 128)

        self.plot_eventdur.add_histogram(dwellTimes, color=newcolor)

        self.plot_eventdepth.add_histogram(currentBlockade, color=newcolor)

        scatterItem = MyScatterPlotItem(size=10, pen=mkPen(None), brush=newcolor, files=file_names, counts=counts)
        scatterItem.setData(dwellTimes, currentBlockade)
        self.plot_eventdur_eventdepth.addItem(scatterItem)
        scatterItem.sigClicked.connect(self.onScatterPointsClicked)

        for filex in files:
            filex.close()

        return

    def removeFilter(self, index):
        self.plot_eventdur.remove_item_at(index)
        self.plot_eventdepth.remove_item_at(index)
        self.plot_eventdur_eventdepth.removeItem(self.plot_eventdur_eventdepth.listDataItems()[index])

    def onScatterPointsClicked(self, plot, points):
        """
        Callback for when a scatter plot points are clicked.
        Highlights the points and unhighlights previously selected points.

        plot should be a MyScatterPlotItem
        points should be a MySpotItem
        """
        for p in self.lastScatterClicked:
            p.resetPen()
            # remove point we've already selected so we
            # can select points behind it.
            if p in points and len(points) > 1:
                points.remove(p)
#         print 'Points clicked:', points, plot
        for point in points:
            point.setPen('w', width=2)
            self.lastScatterClicked = [point]
            break  # only take first point

        # Plot the new point clicked on the single event display
        filename, position = plot.getFileNameFromPosition(self.lastScatterClicked[0].eventPosition)

        h5file = eD.openFile(filename, mode='r')

        table = h5file.root.events.eventTable
        row = h5file.getEventRow(position)
        arrayRow = row['arrayRow']
        sampleRate = h5file.getSampleRate()
        eventLength = row['eventLength']
        rawPointsPerSide = row['rawPointsPerSide']

        rawData = h5file.getRawDataAt(arrayRow)

        n = len(rawData)

        times = np.linspace(0.0, 1.0 * n / sampleRate, n)

        self.plot_scatterselect.clear()
        self.plot_scatterselect.plot(times, rawData)
        # plot the event points in yellow
        self.plot_scatterselect.plot(times[rawPointsPerSide:rawPointsPerSide + eventLength], \
                                     rawData[rawPointsPerSide:rawPointsPerSide + eventLength], pen='y')

        # Plot the cusum levels
        nLevels = row['nLevels']
        baseline = row['baseline']
        # left, start-1, start,
        levels = h5file.getLevelsAt(arrayRow)
        indices = h5file.getLevelLengthsAt(arrayRow)

        levelTimes = np.zeros(2 * nLevels + 4)
        levelValues = np.zeros(2 * nLevels + 4)

        levelTimes[1] = 1.0 * (rawPointsPerSide - 1) / sampleRate
        levelValues[0] = levelValues[1] = baseline
        i = 0
        length = 0
        for i in xrange(nLevels):
            levelTimes[2 * i + 2] = times[rawPointsPerSide] + 1.0 * (length) / sampleRate
            levelValues[2 * i + 2] = levels[i]
            levelTimes[2 * i + 3] = times[rawPointsPerSide] + 1.0 * (length + indices[i]) / sampleRate
            levelValues[2 * i + 3] = levels[i]
            length += indices[i]
        i += 1
        levelTimes[2 * i + 2] = times[rawPointsPerSide + eventLength]
        levelTimes[2 * i + 3] = times[n - 1]
        levelValues[2 * i + 2] = levelValues[2 * i + 3] = baseline

        self.plot_scatterselect.plot(levelTimes, levelValues, pen='g')

        h5file.close()