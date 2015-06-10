"""
    Copyright © 2015 by Stefan Lehmann

"""
from PyQt5.QtCore import QCoreApplication
from PyQt5.QtWidgets import QMessageBox


def critical(parent, msg):
    QMessageBox.critical(parent, QCoreApplication.applicationName(), msg)