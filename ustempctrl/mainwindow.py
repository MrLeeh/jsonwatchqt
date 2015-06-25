#! python3

"""
    GUI for Ultrasonic Temperature Controller
    Copyright © 2015 by Stefan Lehmann

"""
import datetime
import sys
import json
import queue
import threading

import serial
from PyQt5.QtWidgets import QApplication, QAction, QDialog, QMainWindow, QMessageBox, \
    QDockWidget, QLabel
from PyQt5.QtCore import QTimer, QSettings, QCoreApplication, Qt, QThread

from serial.serialutil import SerialException

from jsonwatch.jsonobject import JsonObject
from ustempctrl.plotsettings import PlotSettingsWidget
from ustempctrl.settingswidget import CtrlSettingsWidget
from ustempctrl.jsontreeview import JsonTreeView
from ustempctrl.plotwidget import PlotWidget
from ustempctrl.serialdialog import SerialDialog
from ustempctrl.utilities import critical


def read_serial(ser: serial.Serial, q: queue, stop_event: threading.Event):
    utf8decode = lambda s: s.decode('utf-8')
    strip = lambda s: s.strip()

    while not stop_event.is_set():
        if ser.inWaiting():
            q.put(strip(utf8decode(ser.readline())))


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
        self.objectexplorerDockWidget = QDockWidget(
            self.tr("object explorer"), self
        )
        self.objectexplorerDockWidget.setObjectName("objectexplorer_dockwidget")
        self.objectexplorerDockWidget.setWidget(self.objectexplorer)

        # plot settings
        self.plotsettings = PlotSettingsWidget(self)
        self.plotsettingsDockWidget = QDockWidget(
            self.tr("plot settings"), self
        )
        self.plotsettingsDockWidget.setObjectName("plotsettings_dockwidget")
        self.plotsettingsDockWidget.setWidget(self.plotsettings)

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

        # StatusBar
        statusbar = self.statusBar()
        statusbar.setVisible(True)
        self.connectionstateLabel = QLabel(self.tr("Not connected"))
        statusbar.addPermanentWidget(self.connectionstateLabel)
        statusbar.showMessage(self.tr("Ready"))

        # Layout
        self.setCentralWidget(self.plot)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.objectexplorerDockWidget)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.plotsettingsDockWidget)

    def closeEvent(self, event):
        self.stop_event.set()
        self.timer.stop()
        try:
            self.serial.close()
        except (SerialException, AttributeError):
            pass

    def send_reset(self):
        jsonstring = json.dumps({"resetpid": 1})
        self.serial.write(bytearray(jsonstring, 'utf-8'))

    def receive_serialdata(self):
        while not self.queue.empty():
            node = JsonObject('root', self.queue.get())
            self.rootnode.update(node)

            # refresh widgets
            self.objectexplorer.refresh()
            self.plot.refresh(datetime.datetime.now())

            if self.settingsDialog is not None:
                if node.child_with_key('settings') is not None:
                    self.settingsDialog.refresh()

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
            self.queue = queue.Queue()
            self.stop_event = threading.Event()
            self.worker = threading.Thread(
                target=read_serial, args=(self.serial, self.queue,
                                          self.stop_event)
            )
            self.worker.start()

            self.connectAction.setText(self.tr("Disconnect"))
            self.serialdlgAction.setEnabled(False)
            self.connectionstateLabel.setText(self.tr("Connected to %s") % port)

    def disconnect(self):
        self.stop_event.set()
        self.timer.stop()
        self.serial.close()
        self.serial = None
        self.connectAction.setText(self.tr("Connect"))
        self.serialdlgAction.setEnabled(True)
        self.connectionstateLabel.setText(self.tr("Not connected"))


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

