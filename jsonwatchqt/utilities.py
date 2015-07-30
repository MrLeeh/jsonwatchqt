"""
    Copyright © 2015 by Stefan Lehmann

"""
from qtpy.QtCore import QCoreApplication
from qtpy.QtWidgets import QMessageBox


def critical(parent, msg):
    QMessageBox.critical(parent, QCoreApplication.applicationName(), msg)