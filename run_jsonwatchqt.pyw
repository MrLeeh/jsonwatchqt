#!/usr/bin/env python


import os
import sys
import logging
import argparse
from jsonwatchqt.mainwindow import MainWindow
from jsonwatch._version import get_versions

os.environ['QT_API'] = 'PySide'  # 'PySide', 'PyQt5'

# for PyQt5 integration
pythonpath = os.path.join(os.path.split(sys.executable)[0], os.pardir)
os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = \
    os.path.join(pythonpath, "Lib\site-packages\PyQt5\plugins\platforms")

from qtpy.QtCore import QCoreApplication, QSettings
from qtpy.QtWidgets import QApplication


# argparser
parser = argparse.ArgumentParser(description="run jsonwatchqt")
parser.add_argument('--clear',
                    help="clear settings",
                    action='store_true')
args = parser.parse_args()

# logger
logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s: %(message)s')

# Application
app = QApplication(sys.argv)
QCoreApplication.setOrganizationName("Stefan Lehmann")
QCoreApplication.setApplicationName("JsonWatchQt")
QCoreApplication.setApplicationVersion(get_versions()['version'])

# clear settings
if args.clear:
    QSettings().clear()

# open Mainwindow
w = MainWindow()
w.show()
app.exec_()
