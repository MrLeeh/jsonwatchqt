#!python3
import sys
from jsonwatchqt.mainwindow import CtrlTestGui
from PyQt5.QtCore import QCoreApplication, QSettings
from PyQt5.QtWidgets import QApplication

# Config Application

app = QApplication(sys.argv)
QCoreApplication.setOrganizationName("Stefan Lehmann")
QCoreApplication.setApplicationName("JsonWatchQt")

# Open Mainwindow
w = CtrlTestGui()
w.show()
app.exec_()
