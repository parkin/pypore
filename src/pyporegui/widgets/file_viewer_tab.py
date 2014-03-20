from PySide import QtGui
from pyqtgraph.graphicsItems.PlotItem import PlotItem
from pyqtgraph.widgets.LayoutWidget import LayoutWidget
import pyqtgraph as pg
from pyporegui.widgets.plot_tool_bar import PlotToolBar

from base_tabs import BaseQSplitterDataFile

__all__ = ['FileViewerTab']


class FileViewerTab(BaseQSplitterDataFile):
    """

    """

    def __init__(self, parent=None):
        """

        """
        super(FileViewerTab, self).__init__(parent)

    def _on_file_item_selection_changed(self):
        # TODO implement me
        # or choose to do nothing
        pass

    def _on_file_item_doubleclick(self, item):
        # TODO implement me
        pass

    def _create_right_widget(self, parent):
        plot_wig = pg.GraphicsLayoutWidget()

        self.plot_widget = PlotItem(name='FileViewer', title='Current')

        plot_wig.addItem(self.plot_widget)

        self.plot_tool_bar = PlotToolBar(self)
        if parent is not None:
            parent.addToolBar(self.plot_tool_bar)

        layout_wig = LayoutWidget()
        layout_wig.addWidget(self.plot_tool_bar, row=1, col=0, colspan=3)
        layout_wig.addWidget(plot_wig, row=2, col=0, colspan=3)

        return layout_wig

    def _create_left_widget(self, parent=None):
        scroll_area = QtGui.QScrollArea()
        scroll_area.setWidgetResizable(True)

        file_options = super(FileViewerTab, self)._create_left_widget(parent)

        filter_frame = QtGui.QFrame()

        v_box = QtGui.QVBoxLayout()
        v_box.addLayout(file_options)
        v_box.addWidget(filter_frame)

        v_box_widget = QtGui.QWidget()
        v_box_widget.setLayout(v_box)

        scroll_area.setWidget(v_box_widget)

        return scroll_area
