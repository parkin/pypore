from PySide import QtGui
import numpy as np
from pyqtgraph import GraphicsLayoutWidget, mkPen
from pypore.filetypes import event_database as ed
from pyporegui.graphicsItems.histogram_item import HistogramItem
from pyporegui.graphicsItems.scatter_plot_item import ScatterPlotItem

__all__ = ['EventAnalysisPlotWidget']


class EventAnalysisPlotWidget(GraphicsLayoutWidget):
    def __init__(self):
        super(EventAnalysisPlotWidget, self).__init__()

        self.plot_event_depth = HistogramItem(title='Event Depth', rotate=True)
        self.addItem(self.plot_event_depth)
        self.plot_event_depth.setMouseEnabled(x=False, y=True)
        self.plot_event_dur_event_depth = self.addPlot(name='Depth vs. Duration', title='Depth vs. Duration')
        self.plot_event_depth.setYLink('Depth vs. Duration')

        self.nextRow()

        self.plot_scatter_select = self.addPlot(title='Single Event')

        self.plot_event_dur = HistogramItem(title='Event Duration')
        self.addItem(self.plot_event_dur)
        self.plot_event_dur.setXLink('Depth vs. Duration')
        self.plot_event_dur.setMouseEnabled(x=True, y=False)

        self.last_scatter_clicked = []

        self.n_bins = 0
        self.bins = np.zeros(0)

    def add_selections(self, file_names, params):
        """
        Plots event statistics.
        """
        files = []
        counts = []
        event_count = 0
        for filename in file_names:
            h5file = ed.open_file(filename, mode='r')
            files.append(h5file)
            count = h5file.get_event_count()
            event_count += count
            counts.append(count)

        current_blockade = np.empty(event_count)
        dwell_times = np.empty(event_count)
        count = 0
        for j, filex in enumerate(files):
            event_table = filex.get_event_table()
            sample_rate = filex.get_sample_rate()
            for i, row in enumerate(event_table):
                current_blockade[count + i] = row['current_blockage']
                dwell_times[count + i] = row['event_length'] / sample_rate
            count += counts[j]

        color = params['color']
        new_color = QtGui.QColor(color.red(), color.green(), color.blue(), 128)

        self.plot_event_dur.add_histogram(dwell_times, color=new_color)

        self.plot_event_depth.add_histogram(current_blockade, color=new_color)

        scatter_item = ScatterPlotItem(size=10, pen=mkPen(None), brush=new_color, files=file_names, counts=counts)
        scatter_item.setData(dwell_times, current_blockade)
        self.plot_event_dur_event_depth.addItem(scatter_item)
        scatter_item.sigClicked.connect(self.on_scatter_points_clicked)

        for filex in files:
            filex.close()

        return

    def remove_filter(self, index):
        self.plot_event_dur.remove_item_at(index)
        self.plot_event_depth.remove_item_at(index)
        self.plot_event_dur_event_depth.removeItem(self.plot_event_dur_event_depth.listDataItems()[index])

    def on_scatter_points_clicked(self, plot, points):
        """
        Callback for when a scatter plot points are clicked.
        Highlights the points and un-highlights previously selected points.

        plot should be a MyScatterPlotItem
        points should be a MySpotItem
        """
        for p in self.last_scatter_clicked:
            p.resetPen()
            # remove point we've already selected so we
            # can select points behind it.
            if p in points and len(points) > 1:
                points.remove(p)
            #         print 'Points clicked:', points, plot
        for point in points:
            point.setPen('w', width=2)
            self.last_scatter_clicked = [point]
            break  # only take first point

        # Plot the new point clicked on the single event display
        filename, position = plot.get_file_name_from_position(self.last_scatter_clicked[0].event_position)

        h5file = ed.open_file(filename, mode='r')

        row = h5file.get_event_row(position)
        array_row = row['array_row']
        sample_rate = h5file.get_sample_rate()
        event_length = row['event_length']
        raw_points_per_side = row['raw_points_per_side']

        raw_data = h5file.get_raw_data_at(array_row)

        n = len(raw_data)

        times = np.linspace(0.0, 1.0 * n / sample_rate, n)

        self.plot_scatter_select.clear()
        self.plot_scatter_select.plot(times, raw_data)
        # plot the event points in yellow
        self.plot_scatter_select.plot(times[raw_points_per_side:raw_points_per_side + event_length],
                                      raw_data[raw_points_per_side:raw_points_per_side + event_length], pen='y')

        # Plot the cusum levels
        n_levels = row['n_levels']
        baseline = row['baseline']
        # left, start-1, start,
        levels = h5file.get_levels_at(array_row)
        indices = h5file.get_level_lengths_at(array_row)

        level_times = np.zeros(2 * n_levels + 4)
        level_values = np.zeros(2 * n_levels + 4)

        level_times[1] = 1.0 * (raw_points_per_side - 1) / sample_rate
        level_values[0] = level_values[1] = baseline
        i = 0
        length = 0
        for i in xrange(n_levels):
            level_times[2 * i + 2] = times[raw_points_per_side] + 1.0 * length / sample_rate
            level_values[2 * i + 2] = levels[i]
            level_times[2 * i + 3] = times[raw_points_per_side] + 1.0 * (length + indices[i]) / sample_rate
            level_values[2 * i + 3] = levels[i]
            length += indices[i]
        i += 1
        level_times[2 * i + 2] = times[raw_points_per_side + event_length]
        level_times[2 * i + 3] = times[n - 1]
        level_values[2 * i + 2] = level_values[2 * i + 3] = baseline

        self.plot_scatter_select.plot(level_times, level_values, pen='g')

        h5file.close()