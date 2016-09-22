# coding=utf-8
"""
    jsonwatchqt.plotsettings.py,

    copyright (c) 2015 by Stefan Lehmann,
    licensed under the MIT license

"""
import sys
from qtpy.QtCore import QCoreApplication, Signal
from qtpy.QtWidgets import QWidget, QApplication, QGridLayout, \
    QLabel, QDoubleSpinBox, QRadioButton, QButtonGroup, QGroupBox, QVBoxLayout


S_XMIN = "plot/xmin"
S_XMAX = "plot/xmax"
S_YMIN = "plot/ymin"
S_YMAX = "plot/ymax"
S_AUTOSCALE = "plot/autoscaleoption"

AUTOSCALE_COMPLETE = 0
AUTOSCALE_AUTOSCROLL = 1
AUTOSCALE_NONE = 2


class CoordSpinBox(QDoubleSpinBox):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setRange(-1E9, 1E9)
        self.setDecimals(1)
        self.setSingleStep(1.0)


class PlotSettingsWidget(QWidget):

    def __init__(self, settings, plotWidget, parent=None):
        super().__init__(parent)
        self.mainwindow = parent
        self.plotWidget = plotWidget

        # xmin
        self.xminLabel = QLabel(self.tr('xmin:'))
        self.xminSpinBox = CoordSpinBox()
        self.xminLabel.setBuddy(self.xminSpinBox)
        self.xminSpinBox.editingFinished.connect(self.change_limits)

        # xmax
        self.xmaxLabel = QLabel(self.tr('xmax:'))
        self.xmaxSpinBox = CoordSpinBox()
        self.xmaxLabel.setBuddy(self.xmaxSpinBox)
        self.xmaxSpinBox.editingFinished.connect(self.change_limits)

        # ymin
        self.yminLabel = QLabel(self.tr('ymin:'))
        self.yminSpinBox = CoordSpinBox()
        self.yminLabel.setBuddy(self.yminSpinBox)
        self.yminSpinBox.editingFinished.connect(self.change_limits)

        # ymax
        self.ymaxLabel = QLabel(self.tr('ymax:'))
        self.ymaxSpinBox = CoordSpinBox()
        self.ymaxLabel.setBuddy(self.ymaxSpinBox)
        self.ymaxSpinBox.editingFinished.connect(self.change_limits)

        # Autoscale Radio Group
        self.autoscaleButtonGroup = QButtonGroup()

        # Autoscale Group Box
        self.autoscaleGroupBox = QGroupBox()

        # autoscale
        self.autoscaleRadioButton = QRadioButton(self.tr("autoscale"))
        self.autoscaleButtonGroup.addButton(self.autoscaleRadioButton)

        # autotrack
        self.autoscrollRadioButton = QRadioButton(self.tr("autoscroll"))
        self.autoscaleButtonGroup.addButton(self.autoscrollRadioButton)

        # no autoscale
        self.manualscaleRadioButton = QRadioButton(self.tr("manual"))
        self.autoscaleButtonGroup.addButton(self.manualscaleRadioButton)

        layout = QVBoxLayout()
        layout.addWidget(self.autoscaleRadioButton)
        layout.addWidget(self.autoscrollRadioButton)
        layout.addWidget(self.manualscaleRadioButton)
        self.autoscaleGroupBox.setLayout(layout)

        # Layout
        layout = QGridLayout()
        layout.addWidget(self.xminLabel, 1, 0)
        layout.addWidget(self.xminSpinBox, 1, 1)
        layout.addWidget(self.xmaxLabel, 2, 0)
        layout.addWidget(self.xmaxSpinBox, 2, 1)
        layout.addWidget(self.yminLabel, 3, 0)
        layout.addWidget(self.yminSpinBox, 3, 1)
        layout.addWidget(self.ymaxLabel, 4, 0)
        layout.addWidget(self.ymaxSpinBox, 4, 1)
        layout.addWidget(self.autoscaleGroupBox, 5, 0, 1, 2)
        layout.setRowStretch(6, 1)
        self.setLayout(layout)

        # settings
        self.settings = settings
        self.settings.add_handler(S_XMIN, self.xminSpinBox)
        self.settings.add_handler(S_XMAX, self.xmaxSpinBox)
        self.settings.add_handler(S_YMIN, self.yminSpinBox)
        self.settings.add_handler(S_YMAX, self.ymaxSpinBox)
        self.settings.add_handler(S_AUTOSCALE, self.autoscaleButtonGroup)

    def refresh(self, state):
        pass

    def change_limits(self):
        if self.autoscale != AUTOSCALE_COMPLETE:
            self.plotWidget.xmin = self.xmin
            self.plotWidget.xmax = self.xmax
            self.plotWidget.ymin = self.ymin
            self.plotWidget.ymax = self.ymax
            self.plotWidget.draw()

    @property
    def xmin(self):
        return self.xminSpinBox.value()

    @property
    def xmax(self):
        return self.xmaxSpinBox.value()

    @property
    def ymin(self):
        return self.yminSpinBox.value()

    @property
    def ymax(self):
        return self.ymaxSpinBox.value()

    @property
    def autoscale(self):
        return self.autoscaleButtonGroup.checkedId()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    QCoreApplication.setApplicationName("USTempCtrl")
    QCoreApplication.setOrganizationName("KUZ")
    w = PlotSettingsWidget()
    w.show()
    app.exec_()
