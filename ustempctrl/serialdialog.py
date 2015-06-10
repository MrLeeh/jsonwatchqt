"""
    USTempCtrl GUI - Serial Dialog
    Copyright © 2015 by Stefan Lehmann

"""
import sys
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QDialog, QLabel, QComboBox, \
    QGridLayout, QDialogButtonBox
import serial.tools.list_ports


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
        def create_comportobjects():
            comports = serial.tools.list_ports.comports()
            for port in sorted(comports):
                portobj = COMPort(port)
                yield portobj

        self.serialports = list(create_comportobjects())
        for port in self.serialports:
            item = combobox.addItem(port.label, port.name)

    @property
    def port(self):
        portname = self.portComboBox.currentData()
        ports = [port for port in self.serialports if port.name == portname]
        if len(ports):
            return ports[0].name

    @port.setter
    def port(self, value):
        ports = [port for port in self.serialports if port.name == value]
        if len(ports):
            self.portComboBox.setCurrentText(ports[0].label)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    dlg = SerialDialog()
    dlg.port = "COM28"
    dlg.exec_()