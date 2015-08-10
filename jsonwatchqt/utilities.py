"""
    Copyright © 2015 by Stefan Lehmann

"""
import sys
import os
from qtpy.QtCore import QCoreApplication
from qtpy.QtWidgets import QMessageBox
from qtpy.QtGui import QPixmap


image_path = os.path.join(os.path.dirname(sys.argv[0]), 'img')

def pixmap(filename):
    return QPixmap(os.path.join(image_path, filename))

def critical(parent, msg):
    QMessageBox.critical(parent, QCoreApplication.applicationName(), msg)
