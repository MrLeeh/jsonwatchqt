"""
    Copyright © 2015 by Stefan Lehmann

"""
import datetime
import os
import sys
from PyQt5.QtCore import QByteArray, QIODevice, QDataStream, QSettings
from PyQt5.QtGui import QDragEnterEvent, QDropEvent
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QApplication
from pyqtconfig.config import QSettingsManager
from jsonwatch.jsonobject import JsonObject

os.environ['QT_API'] = 'pyqt5'

import matplotlib

matplotlib.use("Qt5agg")

from matplotlib.backends.backend_qt5agg import \
    FigureCanvasQTAgg as FigureCanvas, \
    NavigationToolbar2QT as NavigationToolbar
import pylab


class PlotItem:
    def __init__(self, dataitem, line):
        self.dataitem = dataitem
        self.line = line
        self.xdata =[]
        self.ydata = []

    def add_data(self, x, y):
        self.xdata.append(x)
        self.ydata.append(y)
        self.line.set_data(self.xdata, self.ydata)


class MyCanvas(FigureCanvas):
    def __init__(self, figure, parent=None):
        super().__init__(figure)
        self.setParent(parent)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasFormat("application/x_nodepath.list"):
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        mimedata = event.mimeData()
        data = QByteArray(mimedata.data("application/x_nodepath.list"))
        stream = QDataStream(data, QIODevice.ReadOnly)
        while not stream.atEnd():
            path = stream.readQString()
            self.parent().add_plot(path)
        event.acceptProposedAction()


class PlotWidget(QWidget):
    def __init__(self, rootnode: JsonObject, parent=None):
        super().__init__(parent)
        self.settings = QSettings()
        self.rootnode = rootnode
        self.plotitems = []
        self.starttime = datetime.datetime.now()
        self.dirty = False

        # matplotlib figure
        self.fig = pylab.figure()
        self.canvas = MyCanvas(self.fig, self)
        self.canvas.setParent(self)
        self.ax1 = self.fig.add_subplot(111)

        # navigation toolbar
        self.toolbar = NavigationToolbar(self.canvas, self)

        # layout
        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        layout.addWidget(self.toolbar)
        self.setLayout(layout)

        self.setAcceptDrops(True)

    def add_plot(self, path):
        item = self.rootnode.child_from_path(path)
        if item is None or item in (pi.dataitem for pi in self.plotitems):
            return

        # append plotlist, plot data
        line = self.ax1.plot([],[], label=item.key)[0]
        self.plotitems.append(PlotItem(item, line))

        # draw legend
        handles, labels = self.ax1.get_legend_handles_labels()
        self.ax1.legend(handles, labels)

        # refresh
        self.canvas.draw()

    def refresh(self, date):
        autoscale = self.settings.value('plot/autoscale', type=bool)
        xmin = self.settings.value('plot/xmin', type=float)
        xmax = self.settings.value('plot/xmax', type=float)
        ymin = self.settings.value('plot/ymin', type=float)
        ymax = self.settings.value('plot/ymax', type=float)
        timedelta = (date - self.starttime).total_seconds()

        for plotitem in self.plotitems:
            plotitem.add_data(timedelta, plotitem.dataitem.value)
        if autoscale:
            self.ax1.relim()
            self.ax1.autoscale()
            self.ax1.autoscale_view()
            xmin, xmax = self.ax1.get_xlim()
            self.settings.setValue('plot/xmin', float(xmin))
            self.settings.setValue('plot/xmax', float(xmax))
        else:
            if not self.dirty:
                self.ax1.set_xlim(xmin, xmax)
                # self.ax1.set_ylim(ymin, ymax)
                pass
        self.canvas.draw()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = PlotWidget()
    w.show()
    app.exec_()
