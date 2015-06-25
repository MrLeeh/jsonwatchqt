# coding=utf-8
"""
    Copyright © 2015 by Stefan Lehmann

"""
import sys
from PyQt5.QtCore import QCoreApplication, QSettings
from PyQt5.QtWidgets import QWidget, QCheckBox, QApplication, QGridLayout, \
    QLabel, QDoubleSpinBox
from pyqtconfig.config import QSettingsManager


class CoordSpinBox(QDoubleSpinBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setRange(-1E9, 1E9)
        self.setDecimals(1)
        self.setSingleStep(1.0)


class PlotSettingsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.settings = QSettingsManager()

        # autoscale
        self.autoscaleCheckbox = QCheckBox(self.tr("autoscale"))
        self.autoscaleCheckbox.stateChanged.connect(self.refresh)
        self.settings.add_handler('plot/autoscale', self.autoscaleCheckbox,
                                  default=True)

        # xmin
        self.xminLabel = QLabel(self.tr('xmin:'))
        self.xminSpinBox = CoordSpinBox()
        self.xminLabel.setBuddy(self.xminSpinBox)
        self.settings.set_default('plot/xmin', 0.0)
        self.settings.add_handler('plot/xmin', self.xminSpinBox)

        # xmax
        self.xmaxLabel = QLabel(self.tr('xmax:'))
        self.xmaxSpinBox = CoordSpinBox()
        self.xmaxLabel.setBuddy(self.xmaxSpinBox)
        self.settings.set_default('plot/xmax', 10.0)
        self.settings.add_handler('plot/xmax', self.xmaxSpinBox)

        # ymin
        self.yminLabel = QLabel(self.tr('ymin:'))
        self.yminSpinBox = CoordSpinBox()
        self.yminLabel.setBuddy(self.yminSpinBox)
        self.settings.set_default('plot/ymin', -10.0)
        self.settings.add_handler('plot/ymin', self.yminSpinBox)

        #ymax
        self.ymaxLabel = QLabel(self.tr('ymax:'))
        self.ymaxSpinBox = CoordSpinBox()
        self.ymaxLabel.setBuddy(self.ymaxSpinBox)
        self.settings.set_default('plot/ymax', 10.0)
        self.settings.add_handler('plot/ymax', self.ymaxSpinBox)

        # Layout
        layout = QGridLayout()
        layout.addWidget(self.autoscaleCheckbox, 0, 0, 1, 2)
        layout.addWidget(self.xminLabel, 1, 0)
        layout.addWidget(self.xminSpinBox, 1, 1)
        layout.addWidget(self.xmaxLabel, 2, 0)
        layout.addWidget(self.xmaxSpinBox, 2, 1)
        layout.addWidget(self.yminLabel, 3, 0)
        layout.addWidget(self.yminSpinBox, 3, 1)
        layout.addWidget(self.ymaxLabel, 4, 0)
        layout.addWidget(self.ymaxSpinBox, 4, 1)
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