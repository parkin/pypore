from PySide import QtGui


class PlotToolBar(QtGui.QToolBar):
    """
    A toolbar for plots, with a zoom button, check boxes for options.
    """

    def __init__(self, parent=None):
        super(PlotToolBar, self).__init__(parent)

        self.widget_list = []

        self.decimate_check_box = QtGui.QCheckBox()
        self.decimate_check_box.setChecked(True)
        self.decimate_check_box.setText('Decimate')
        self.addWidget(self.decimate_check_box)

        self.plot_during_check_box = QtGui.QCheckBox()
        self.plot_during_check_box.setChecked(True)
        self.plot_during_check_box.setText('Plot Events')
        self.plot_during_check_box.setToolTip('Select to have events plotted during event finding.')
        self.addWidget(self.plot_during_check_box)

        self.filter_data = QtGui.QCheckBox()
        self.filter_data.setChecked(True)
        self.filter_data.setText('Show filtered')
        self.filter_data.setToolTip('Select to have events plotted during event finding.')
        self.addWidget(self.filter_data)

    def is_decimate_checked(self):
        """
        :returns: boolean -- true if the toolbar's decimate checkbox is checked, false
                    otherwise.
        """
        return self.decimate_check_box.isChecked()

    def is_plot_during_checked(self):
        """
        :returns: boolean -- true if the toolbar's plot during checkbox is checked, false otherwise.
        """
        return self.plot_during_check_box.isChecked()

    def get_widget_list(self):
        """
        :returns: ListType<QtGui.QWidget> -- Returns a list of the widgets contained in the PlotToolBar.
        """
        return list(self.widget_list)

    def addWidget(self, widget, *args, **kwargs):
        self.widget_list.append(widget)
        return super(PlotToolBar, self).addWidget(widget, *args, **kwargs)