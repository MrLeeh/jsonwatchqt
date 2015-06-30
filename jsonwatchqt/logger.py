"""
    Copyright (c) 2015 by Stefan Lehmann

"""
from PyQt5.QtWidgets import QPlainTextEdit
from datetime import datetime

class LoggingWidget(QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)

    def log_input(self, message):
        self.appendPlainText(datetime.now().strftime("[In] %H:%M:%S.%f") + ": "
                             + message)

    def log_output(self, message):
        self.appendPlainText(datetime.now().strftime("[Out] %H:%M:%S.%f") + ": "
                             + message)