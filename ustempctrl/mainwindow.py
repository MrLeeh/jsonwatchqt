#! python3

"""
    GUI for Ultrasonic Temperature Controller
    Copyright © 2015 by Stefan Lehmann

"""
import datetime
from io import StringIO
import sys
import json
import functools

import serial
from PyQt5.QtWidgets import QApplication, QWidget, QGridLayout, \
    QAction, QDialog, QMainWindow, QMessageBox, QSplitter
from PyQt5.QtCore import QTimer, QSettings, QCoreApplication, Qt
from serial.serialutil import SerialException
from jsonwatch.jsonobject import JsonObject
from ustempctrl.plotsettings import PlotSettingsWidget

from ustempctrl.settingswidget import CtrlSettingsWidget
from ustempctrl.jsontreeview import JsonTreeView
from ustempctrl.plotwidget import PlotWidget
from ustempctrl.serialdialog import SerialDialog
from ustempctrl.utilities import critical


class CtrlTestGui(QMainWindow):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.counter = 0
        self.serial = None
        self.rootnode = JsonObject('root')
        self.rootnode.add_child(JsonObject('processdata'))
        self.rootnode.add_child(JsonObject('settings'))

        # Timer for periodic status update
        self.timer = QTimer()
        self.timer.setInterval(100)
        self.timer.timeout.connect(self.receive_serialdata)

        # Controller Settings
        self.settingsDialog = None
        # object explorer
        self.objectexplorer = JsonTreeView(self.rootnode['processdata'], self)
        # plot settings
        self.plotsettings = PlotSettingsWidget(self)
        # Plot Widget
        self.plot = PlotWidget(self.rootnode, self)

        # Actions
        # Serial Dialog
        self.serialdlgAction = QAction(self.tr("Serial Settings..."), self)
        self.serialdlgAction.setShortcut("F6")
        self.serialdlgAction.triggered.connect(self.show_serialdlg)
        # Settings Dialog
        self.settingsdlgAction = QAction(self.tr("Settings..."), self)
        self.settingsdlgAction.triggered.connect(self.show_settingsdlg)
        # Connect
        self.connectAction = QAction(self.tr("Connect"), self)
        self.connectAction.setShortcut("F5")
        self.connectAction.triggered.connect(self.toggle_connect)
        # Quit
        self.quitAction = QAction(self.tr("Quit"), self)
        self.quitAction.setShortcut("Alt+F4")
        self.quitAction.triggered.connect(self.close)

        # Menus
        self.fileMenu = self.menuBar().addMenu(self.tr("File"))
        self.fileMenu.addAction(self.connectAction)
        self.fileMenu.addAction(self.serialdlgAction)
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.quitAction)

        self.extrasMenu = self.menuBar().addMenu(self.tr("Extras"))
        self.extrasMenu.addAction(self.settingsdlgAction)

        # Vertical Splitter
        self.vsplitter = QSplitter(Qt.Vertical)
        self.vsplitter.addWidget(self.objectexplorer)
        self.vsplitter.addWidget(self.plotsettings)

        # Horizontal Splitter
        self.hsplitter = QSplitter()
        self.hsplitter.addWidget(self.vsplitter)
        self.hsplitter.addWidget(self.plot)

        # Layout
        layout = QGridLayout()
        layout.addWidget(self.hsplitter, 0, 0)
        self.setCentralWidget(QWidget())
        self.centralWidget().setLayout(layout)

    def closeEvent(self, event):
        self.timer.stop()
        try:
            self.serial.close()
        except (SerialException, AttributeError):
            pass

    def send_reset(self):
        jsonstring = json.dumps({"resetpid": 1})
        self.serial.write(bytearray(jsonstring, 'utf-8'))

    def receive_serialdata(self):
        if self.serial.inWaiting():
            try:
                # get data from serial
                buf = self.serial.readline().decode('utf-8')
                print(buf.strip())
                node = JsonObject('root', buf)
                self.rootnode.update(node)

                # refresh widgets
                self.objectexplorer.refresh()
                self.plot.refresh(datetime.datetime.now())

                if self.settingsDialog is not None:
                    if node.child_with_key('settings') is not None:
                        self.settingsDialog.refresh()

            except SerialException:
                critical(
                    self, self.tr("Error receiving status from Controller.")
                )
                self.disconnect()

    def show_serialdlg(self):
        settings = QSettings()
        dlg = SerialDialog(self)
        dlg.port = settings.value("serial/port")
        if dlg.exec_() == QDialog.Accepted:

            settings.setValue("serial/port", dlg.port)

    def show_settingsdlg(self):
        if self.settingsDialog is None:
            self.settingsDialog = CtrlSettingsWidget(
                self.serial, self.rootnode['settings'], self)
        self.settingsDialog.show()

    def toggle_connect(self):
        if self.serial is not None:
            self.disconnect()
        else:
            self.connect()

    def connect(self):
        # Load port setting
        settings = QSettings()
        port = settings.value("serial/port")

        # If no port has been selected before show serial settings dialog
        if port is None:
            if self.show_serialdlg() == QDialog.Rejected:
                return
            port = settings.value("serial/port")

        # Serial connection
        try:
            self.serial = serial.Serial(port)
            self.serial.baudrate = 9600
        except ValueError:
            QMessageBox.critical(
                self, QCoreApplication.applicationName(),
                self.tr("Serial parameters e.g. baudrate, databits are out "
                        "of range.")
            )
        except SerialException:
            QMessageBox.critical(
                self, QCoreApplication.applicationName(),
                self.tr("The device '%s' can not be found or can not be "
                        "configured." % port)
            )
        else:
            self.timer.start()
            self.connectAction.setText(self.tr("Disconnect"))
            self.serialdlgAction.setEnabled(False)

    def disconnect(self):
        self.timer.stop()
        self.serial.close()
        self.serial = None
        self.connectAction.setText(self.tr("Connect"))
        self.serialdlgAction.setEnabled(True)


if __name__ == "__main__":

    # Config Application
    app = QApplication(sys.argv)
    QCoreApplication.setOrganizationName("KUZ")
    QCoreApplication.setOrganizationDomain("http://www.kuz-leipzig.de")
    QCoreApplication.setApplicationName("USTempCtrl GUI")

    # Open Mainwindow
    w = CtrlTestGui()
    w.show()
    app.exec_()

