#!/usr/bin/env python

import sys
import logging
import argparse
from jsonwatchqt.mainwindow import MainWindow
from PyQt5.QtCore import QCoreApplication, QSettings
from PyQt5.QtWidgets import QApplication


# argparser
parser = argparse.ArgumentParser(description="Run JsonWatchQt GUI.")
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

if args.clear: QSettings().clear()

# Open Mainwindow
w = MainWindow()
w.show()
app.exec_()
