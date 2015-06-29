# coding=utf-8
"""
    Copyright © 2015 by Stefan Lehmann

"""
import sys
from PyQt5.QtCore import QCoreApplication, QSettings
from PyQt5.QtWidgets import QWidget, QCheckBox, QApplication, QGridLayout, \
    QLabel, QDoubleSpinBox, QRadioButton, QButtonGroup, QGroupBox, QVBoxLayout
from pyqtconfig.config import QSettingsManager


class CoordSpinBox(QDoubleSpinBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setRange(-1E9, 1E9)
        self.setDecimals(1)
        self.setSingleStep(1.0)


class PlotSettingsWidget(QWidget):
    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.settings = settings
        # xmin
        self.xminLabel = QLabel(self.tr('xmin:'))
        self.xminSpinBox = CoordSpinBox()
        self.xminLabel.setBuddy(self.xminSpinBox)
        self.settings.add_handler('plot/xmin', self.xminSpinBox, default=0.0)

        # xmax
        self.xmaxLabel = QLabel(self.tr('xmax:'))
        self.xmaxSpinBox = CoordSpinBox()
        self.xmaxLabel.setBuddy(self.xmaxSpinBox)
        self.settings.add_handler('plot/xmax', self.xmaxSpinBox, default=10.0)

        # ymin
        self.yminLabel = QLabel(self.tr('ymin:'))
        self.yminSpinBox = CoordSpinBox()
        self.yminLabel.setBuddy(self.yminSpinBox)
        self.settings.add_handler('plot/ymin', self.yminSpinBox, default=-10.0)

        #ymax
        self.ymaxLabel = QLabel(self.tr('ymax:'))
        self.ymaxSpinBox = CoordSpinBox()
        self.ymaxLabel.setBuddy(self.ymaxSpinBox)
        self.settings.add_handler('plot/ymax', self.ymaxSpinBox, default=10.0)

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

        self.settings.add_handler('plot/autoscaleoption',
                                  self.autoscaleButtonGroup, default=[(0, True)])

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

    def refresh(self, state):
        pass


if __name__ == "__main__":
    app = QApplication(sys.argv)
    QCoreApplication.setApplicationName("USTempCtrl")
    QCoreApplication.setOrganizationName("KUZ")
    w = PlotSettingsWidget()
    w.show()
    app.exec_()