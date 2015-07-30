"""
    USTempCtrl GUI - Serial Dialog
    Copyright © 2015 by Stefan Lehmann

"""
import sys
import glob

from qtpy.QtCore import Qt
from qtpy.QtWidgets import QApplication, QDialog, QLabel, QComboBox, \
    QGridLayout, QDialogButtonBox
import serial.tools.list_ports
import serial


def serial_ports():
    """Lists serial ports

    :raises EnvironmentError:
        On unsupported or unknown platforms
    :returns:
        A list of available serial ports
    """
    if sys.platform.startswith('win'):
        ports = ['COM' + str(i + 1) for i in range(256)]

    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        # this is to exclude your current terminal "/dev/tty"
        ports = glob.glob('/dev/tty[A-Za-z]*')

    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')

    else:
        raise EnvironmentError('Unsupported platform')

    result = []
    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()
            result.append(port)
        except (OSError, serial.SerialException):
            pass
    return result



class COMPort():
    def __init__(self, args):
        self.name = args[0]
        self.decription = args[1]
        self.dev = args[2]

    @property
    def label(self):
        return self.decription

    def __eq__(self, other):
        if isinstance(other, str):
            return self.name == other
        else:
            return self == other

    def __repr__(self):
        return self.name


class SerialDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.serialports = []

        # Choose COMport
        self.portLabel = QLabel(self.tr("COM Port:"))
        self.portComboBox = QComboBox()
        self.portLabel.setBuddy(self.portComboBox)
        self.refresh_comports(self.portComboBox)

        # Buttons
        self.dlgbuttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel, Qt.Horizontal)
        self.dlgbuttons.rejected.connect(self.reject)
        self.dlgbuttons.accepted.connect(self.accept)

        layout = QGridLayout()
        layout.addWidget(self.portLabel, 0, 0)
        layout.addWidget(self.portComboBox, 0, 1)
        layout.addWidget(self.dlgbuttons, 1, 0, 1, 2)
        self.setLayout(layout)
        self.setWindowTitle(self.tr("Serial Settings"))

    def refresh_comports(self, combobox):
        self.serialports = serial_ports()
        for port in self.serialports:
            item = combobox.addItem(port)

    @property
    def port(self):
        return self.portComboBox.currentText()

    @port.setter
    def port(self, value):
        if value in self.serialports:
            self.portComboBox.setCurrentText(value)
        else:
            raise ValueError("serial port '%s' not available" % value)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    dlg = SerialDialog()
    dlg.port = "COM28"
    dlg.exec_()