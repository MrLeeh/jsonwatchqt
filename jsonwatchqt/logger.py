"""
    Copyright (c) 2015 by Stefan Lehmann

"""
from qtpy.QtWidgets import QTextEdit
from datetime import datetime


def timestr():
    dt = datetime.now()
    return dt.strftime("%H:%M:%S") + ".{:03d}".format(int(dt.microsecond / 1E3))


class LoggingWidget(QTextEdit):

    def __init__(self, parent=None):
        super().__init__(parent)

    def log_input(self, message):
        self.append(
            "<font color=green>[In {}]</font> {}".format(timestr(), message)
        )

    def log_output(self, message):
        self.append(
            "<font color=red>[Out {}]</font> {}".format(timestr(), message)
        )
