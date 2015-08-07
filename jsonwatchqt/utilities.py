"""
    Copyright © 2015 by Stefan Lehmann

"""
import sys
from os.path import dirname, join
from qtpy.QtCore import QCoreApplication
from qtpy.QtWidgets import QMessageBox


image_path = join(dirname(sys.argv[0]), 'img')

def critical(parent, msg):
    QMessageBox.critical(parent, QCoreApplication.applicationName(), msg)
