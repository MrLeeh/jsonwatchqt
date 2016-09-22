"""
    jsonwatchqt.plotwidget.py,

    copyright (c) 2015 by Stefan Lehmann,
    licensed under the MIT license

"""
import datetime
import os
import sys
from qtpy.QtCore import QByteArray, QIODevice, QDataStream
from qtpy.QtGui import QDragEnterEvent, QDropEvent
from qtpy.QtWidgets import QWidget, QVBoxLayout, QApplication
from jsonwatch.jsonnode import JsonNode
from jsonwatchqt.plotsettings import AUTOSCALE_COMPLETE, AUTOSCALE_AUTOSCROLL, \
    AUTOSCALE_NONE

import matplotlib

if os.environ['QT_API'].lower() in ('pyside', 'pyqt4'):
    matplotlib.use("Qt4agg")
    from matplotlib.backends.backend_qt4agg import \
        FigureCanvasQTAgg as FigureCanvas, \
        NavigationToolbar2QT as NavigationToolbar
else:
    matplotlib.use("Qt5agg")
    from matplotlib.backends.backend_qt5agg import \
        FigureCanvasQTAgg as FigureCanvas, \
        NavigationToolbar2QT as NavigationToolbar

import pylab


class PlotItem:

    def __init__(self, dataitem, line):
        self.dataitem = dataitem
        self.line = line
        self.xdata = []
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

    def __init__(self, rootnode: JsonNode, settings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.rootnode = rootnode
        self.plotitems = []
        self.starttime = datetime.datetime.now()
        self.dirty = False

        # matplotlib figure
        self.fig = pylab.figure()
        self.canvas = MyCanvas(self.fig, self)
        self.canvas.setParent(self)
        self.ax1 = self.fig.add_subplot(111)
        self.ax1.grid()
        self.ax1.callbacks.connect('xlim_changed', self.plotlim_changed)
        self.ax1.callbacks.connect('ylim_changed', self.plotlim_changed)

        # navigation toolbar
        self.toolbar = NavigationToolbar(self.canvas, self)

        # layout
        layout = QVBoxLayout()
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
        self.setLayout(layout)

        self.setAcceptDrops(True)

    def add_plot(self, path):
        item = self.rootnode.item_from_path(path.split('/'))
        if item is None or item in (pi.dataitem for pi in self.plotitems):
            return

        # append plotlist, plot data
        line = self.ax1.plot([], [], label=item.key)[0]
        self.plotitems.append(PlotItem(item, line))

        # draw legend
        handles, labels = self.ax1.get_legend_handles_labels()
        self.ax1.legend(handles, labels)

        # refresh
        self.canvas.draw()

    def refresh(self, date):

        autoscale = dict(self.settings.get('plot/autoscaleoption'))
        timedelta = (date - self.starttime).total_seconds()

        for plotitem in self.plotitems:
            plotitem.add_data(timedelta, plotitem.dataitem.value)

        # complete autoscale
        if autoscale[0]:
            self.ax1.relim()
            self.ax1.autoscale()
            self.ax1.autoscale_view()

        # autoscroll x axis
        elif autoscale[1]:
            xmin, xmax = self.ax1.get_xlim()
            delta = xmax - xmin
            xmax = timedelta + 0.1 * delta
            xmin = xmax - delta
            self.ax1.set_xlim(xmin, xmax)

        self.canvas.draw()

    def plotlim_changed(self, *args, **kwargs):
        xmin, xmax = self.ax1.get_xlim()
        ymin, ymax = self.ax1.get_ylim()
        self.settings.set('plot/xmin', float(xmin))
        self.settings.set('plot/xmax', float(xmax))
        self.settings.set('plot/ymin', float(ymin))
        self.settings.set('plot/ymax', float(ymax))

    def draw(self):
        self.canvas.draw()

    # xmin property
    @property
    def xmin(self):
        return self.ax1.get_xlim()[0]

    @xmin.setter
    def xmin(self, value):
        xmax = self.ax1.get_xlim()[1]
        self.ax1.set_xlim(value, xmax)

    # xmax property
    @property
    def xmax(self):
        return self.ax1.get_xlim()[1]

    @xmax.setter
    def xmax(self, value):
        xmin = self.ax1.get_xlim()[0]
        self.ax1.set_xlim(xmin, value)

    # ymin property
    @property
    def ymin(self):
        return self.ax1.get_ylim()[0]

    @ymin.setter
    def ymin(self, value):
        ymax = self.ax1.get_ylim()[1]
        self.ax1.set_ylim(value, ymax)

    # ymax property
    @property
    def ymax(self):
        return self.ax1.get_ylim()[1]

    @ymax.setter
    def ymax(self, value):
        ymin = self.ax1.get_ylim()[0]
        self.ax1.set_ylim(ymin, value)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = PlotWidget()
    w.show()
    app.exec_()
