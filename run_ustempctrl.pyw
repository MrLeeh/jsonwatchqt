#!python3
import sys
from ustempctrl.mainwindow import CtrlTestGui
from PyQt5.QtCore import QCoreApplication, QSettings
from PyQt5.QtWidgets import QApplication

# Config Application

app = QApplication(sys.argv)
QCoreApplication.setOrganizationName("KUZ")
QCoreApplication.setOrganizationDomain("http://www.kuz-leipzig.de")
QCoreApplication.setApplicationName("USTempCtrl GUI")

# Open Mainwindow
w = CtrlTestGui()
w.show()
app.exec_()
