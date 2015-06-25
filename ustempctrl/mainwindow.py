#! python3

"""
    GUI for Ultrasonic Temperature Controller
    Copyright © 2015 by Stefan Lehmann

"""
import datetime
import sys
import json

import serial
from PyQt5.QtWidgets import QApplication, QAction, QDialog, QMainWindow, QMessageBox, \
    QDockWidget, QLabel
from PyQt5.QtCore import QTimer, QSettings, QCoreApplication, Qt, QThread, \
    pyqtSignal

from serial.serialutil import SerialException

from jsonwatch.jsonobject import JsonObject
from jsonwatch.jsonvalue import JsonValue
from ustempctrl.plotsettings import PlotSettingsWidget
from ustempctrl.settingswidget import CtrlSettingsWidget
from ustempctrl.jsontreeview import JsonTreeView
from ustempctrl.plotwidget import PlotWidget
from ustempctrl.serialdialog import SerialDialog
from ustempctrl.utilities import critical


class SerialWorker(QThread):
    data_received = pyqtSignal(str)

    def __init__(self, ser: serial.Serial, parent=None):
        super().__init__(parent)
        self.serial = ser
        self._quit = False

    def run(self):
        utf8decode = lambda s: s.decode('utf-8')
        strip = lambda s: s.strip()

        while not self._quit:
            try:
                if self.serial.isOpen() and self.serial.inWaiting():
                    self.data_received.emit(
                        strip(utf8decode(self.serial.readline()))
                    )
            except SerialException as e:
                pass

    def quit(self):
        self._quit = True


class CtrlTestGui(QMainWindow):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.counter = 0
        self.serial = serial.Serial()
        self.rootnode = JsonObject('root')
        self.rootnode.add_child(JsonObject('processdata'))
        self.rootnode.add_child(JsonObject('settings'))

        # Controller Settings
        self.settingsDialog = None
        # object explorer
        self.objectexplorer = JsonTreeView(self.rootnode, self.serial, self)
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

        self.init_jsonobjects()

    def closeEvent(self, event):
        try:
            self.serial.close()
        except (SerialException, AttributeError):
            pass

    def init_jsonobjects(self):
        pd_node = self.rootnode['processdata']

        pd_node.add_child(
            JsonValue('in', name="Actual Temperature", unit="°C",
                      numerator=10, decimals=1, readonly=False)
        )

        pd_node.add_child(
            JsonValue('kp', numerator=10, readonly=False, decimals=1)
        )

        pd_node.add_child(
            JsonValue('ki', numerator=10, readonly=False, decimals=1)
        )

        pd_node.add_child(
            JsonValue('y', numerator=10, unit="%", decimals=1)
        )

    def send_reset(self):
        jsonstring = json.dumps({"resetpid": 1})
        self.serial.write(bytearray(jsonstring, 'utf-8'))

    def receive_serialdata(self, data):
        node = JsonObject('root', data)
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
        if self.serial.isOpen():
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
            self.serial.setPort(port)
            self.serial.setBaudrate(9600)
            self.serial.open()
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
            self.worker = SerialWorker(self.serial, self)
            self.worker.data_received.connect(self.receive_serialdata)
            self.worker.start()

            self.connectAction.setText(self.tr("Disconnect"))
            self.serialdlgAction.setEnabled(False)
            self.connectionstateLabel.setText(self.tr("Connected to %s") % port)

    def disconnect(self):
        self.worker.quit()
        self.serial.close()
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

