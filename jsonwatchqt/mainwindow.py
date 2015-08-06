#! python3

"""
    GUI for Ultrasonic Temperature Controller
    Copyright (c) 2015 by Stefan Lehmann

"""

import datetime
import logging
import json
import os

import serial
from qtpy.QtWidgets import QAction, QDialog, QMainWindow, QMessageBox, \
    QDockWidget, QLabel, QFileDialog, QApplication
from qtpy.QtCore import QSettings, QCoreApplication, Qt, QThread, \
    Signal

from serial.serialutil import SerialException
from jsonwatch.jsonitem import JsonItem

from jsonwatch.jsonnode import JsonNode
from jsonwatchqt.logger import LoggingWidget
from jsonwatchqt.utilities import critical
from pyqtconfig.config import QSettingsManager
from jsonwatchqt.plotsettings import PlotSettingsWidget
from jsonwatchqt.objectexplorer import ObjectExplorer
from jsonwatchqt.plotwidget import PlotWidget
from jsonwatchqt.serialdialog import SerialDialog


logger = logging.getLogger("jsonwatchqt.mainwindow")
WINDOWSTATE_SETTING = "mainwindow/windowstate"
GEOMETRY_SETTING = "mainwindow/geometry"
FILENAME_SETTING = "mainwindow/filename"


def strip(s):
    return s.strip()


def utf8_to_bytearray(x):
    return bytearray(x, 'utf-8')


def bytearray_to_utf8(x):
    return x.decode('utf-8')


class SerialWorker(QThread):
    data_received = Signal(str)

    def __init__(self, ser: serial.Serial, parent=None):
        super().__init__(parent)
        self.serial = ser
        self._quit = False

    def run(self):
        while not self._quit:
            try:
                if self.serial.isOpen() and self.serial.inWaiting():
                    self.data_received.emit(
                        strip(bytearray_to_utf8(self.serial.readline()))
                    )
            except SerialException as e:
                pass

    def quit(self):
        self._quit = True


class MainWindow(QMainWindow):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.counter = 0
        self.serial = serial.Serial()
        self.rootnode = JsonNode('')
        self.settings = QSettingsManager()
        self._dirty = False
        self._filename = None

        # Controller Settings
        self.settingsDialog = None

        # object explorer
        self.objectexplorer = ObjectExplorer(self.rootnode, self)
        self.objectexplorer.nodevalue_changed.connect(self.send_serialdata)
        self.objectexplorer.nodeproperty_changed.connect(self.set_dirty)
        self.objectexplorerDockWidget = QDockWidget(
            self.tr("object explorer"), self
        )
        self.objectexplorerDockWidget.setObjectName(
            "objectexplorer_dockwidget")
        self.objectexplorerDockWidget.setWidget(self.objectexplorer)

        # plot settings
        self.plotsettings = PlotSettingsWidget(self.settings, self)
        self.plotsettingsDockWidget = QDockWidget(
            self.tr("plot settings"), self
        )
        self.plotsettingsDockWidget.setObjectName(
            "plotsettings_dockwidget")
        self.plotsettingsDockWidget.setWidget(self.plotsettings)

        # log widget
        self.loggingWidget = LoggingWidget(self)
        self.loggingDockWidget = QDockWidget(
            self.tr("logger"), self
        )
        self.loggingDockWidget.setObjectName("logging_dockwidget")
        self.loggingDockWidget.setWidget(self.loggingWidget)

        # Plot Widget
        self.plot = PlotWidget(self.rootnode, self.settings, self)

        # actions and menus
        self._init_actions()
        self._init_menus()

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
        self.addDockWidget(Qt.BottomDockWidgetArea, self.loggingDockWidget)

        self.load_settings()

    def _init_actions(self):
        # Serial Dialog
        self.serialdlgAction = QAction(self.tr("Serial Settings..."), self)
        self.serialdlgAction.setShortcut("F6")
        self.serialdlgAction.triggered.connect(self.show_serialdlg)
        # Connect
        self.connectAction = QAction(self.tr("Connect"), self)
        self.connectAction.setShortcut("F5")
        self.connectAction.triggered.connect(self.toggle_connect)
        # Quit
        self.quitAction = QAction(self.tr("Quit"), self)
        self.quitAction.setShortcut("Alt+F4")
        self.quitAction.triggered.connect(self.close)
        # Save Config as
        self.savecfgasAction = QAction(self.tr("Save as..."), self)
        self.savecfgasAction.setShortcut("Ctrl+Shift+S")
        self.savecfgasAction.triggered.connect(self.show_savecfg_dlg)
        # Save Config
        self.savecfgAction = QAction(self.tr("Save"), self)
        self.savecfgAction.setShortcut("Ctrl+S")
        self.savecfgAction.triggered.connect(self.save_config)
        # Load Config
        self.loadcfgAction = QAction(self.tr("Open..."), self)
        self.loadcfgAction.setShortcut("Ctrl+O")
        self.loadcfgAction.triggered.connect(self.show_opencfg_dlg)
        # New
        self.newAction = QAction(self.tr("New"), self)
        self.newAction.setShortcut("Ctrl+N")
        self.newAction.triggered.connect(self.new)
        # Info
        self.infoAction = QAction(self.tr("Info"), self)
        self.infoAction.setShortcut("F1")
        self.infoAction.triggered.connect(self.show_info)

    def _init_menus(self):
        # file menu
        self.fileMenu = self.menuBar().addMenu(self.tr("File"))
        self.fileMenu.addAction(self.newAction)
        self.fileMenu.addAction(self.loadcfgAction)
        self.fileMenu.addAction(self.savecfgAction)
        self.fileMenu.addAction(self.savecfgasAction)
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.connectAction)
        self.fileMenu.addAction(self.serialdlgAction)
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.quitAction)

        # view menu
        self.viewMenu = self.menuBar().addMenu(self.tr("View"))
        self.viewMenu.addAction(self.objectexplorerDockWidget.toggleViewAction())
        self.viewMenu.addAction(self.plotsettingsDockWidget.toggleViewAction())
        self.viewMenu.addAction(self.loggingDockWidget.toggleViewAction())

        self.menuBar().addAction(self.infoAction)

    def show_info(self):
        dlg = QMessageBox.about(
            self, QApplication.applicationName(),
            "%s %s\n"
            "Copyright (c) by %s" %
            (
                QCoreApplication.applicationName(),
                QCoreApplication.applicationVersion(),
                QCoreApplication.organizationName(),
            )
        )

    def load_config(self, filename):
        self.filename = filename
        try:
            with open(filename, 'rb') as f:
                try:
                    self.objectexplorer.model().beginResetModel()
                    self.rootnode.load(bytearray_to_utf8(f.read()))
                    self.objectexplorer.model().endResetModel()
                except ValueError as e:
                    critical(self, "File '%s' is not a valid config file."
                             % filename)
                    logger.error(str(e))
                    self.filename = None
        except FileNotFoundError as e:
            logger.error(str(e))
            self.filename = None
        self.objectexplorer.refresh()

    def load_settings(self):
        settings = QSettings()

        # window geometry
        try:
            self.restoreGeometry(settings.value(GEOMETRY_SETTING))
        except:
            logger.debug("error restoring window geometry")

        # window state
        try:
            self.restoreState(settings.value(WINDOWSTATE_SETTING))
        except:
            logger.debug("error restoring window state")

        # filename
        self.filename = settings.value(FILENAME_SETTING)
        if self.filename is not None:
            self.load_config(self.filename)

    def save_settings(self):
        settings = QSettings()
        settings.setValue(WINDOWSTATE_SETTING, self.saveState())
        settings.setValue(GEOMETRY_SETTING, self.saveGeometry())
        settings.setValue(FILENAME_SETTING, self.filename)

    def closeEvent(self, event):
        if self.dirty:
            res = QMessageBox.question(
                self,
                QCoreApplication.applicationName(),
                self.tr("Save changes to file '%s'?" %
                        self.filename
                        if self.filename is not None else "unknown"),
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
            )
            if res == QMessageBox.Cancel:
                event.ignore()
                return
            elif res == QMessageBox.Yes:
                self.save_config()

        self.save_settings()

        try:
            self.worker.quit()
        except AttributeError:
            pass

        try:
            self.serial.close()
        except (SerialException, AttributeError):
            pass

    def new(self):
        self.objectexplorer.model().beginResetModel()
        self.rootnode.clear()
        self.objectexplorer.model().endResetModel()

    def send_reset(self):
        jsonstring = json.dumps({"resetpid": 1})
        self.serial.write(bytearray(jsonstring, 'utf-8'))

    def receive_serialdata(self, data):
        self.loggingWidget.log_input(data)
        try:
            self.rootnode.from_json(data)
        except ValueError as e:
            logger.error(str(e))

        # refresh widgets
        self.objectexplorer.refresh()
        self.plot.refresh(datetime.datetime.now())

    def send_serialdata(self, node):
        if isinstance(node, JsonItem):
            if self.serial.isOpen():
                s = node.to_json()
                self.serial.write(utf8_to_bytearray(s + '\n'))
                self.loggingWidget.log_output(s.strip())

    def show_serialdlg(self):
        settings = QSettings()
        dlg = SerialDialog(self)
        try:
            dlg.port = settings.value("serial/port")
        except ValueError:
            pass

        if dlg.exec_() == QDialog.Accepted:

            settings.setValue("serial/port", dlg.port)

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

    def show_savecfg_dlg(self):
        filename, _ = QFileDialog.getSaveFileName(
            self, self.tr("Save configuration file..."),
            directory=os.path.expanduser("~"),
            filter="Json file (*.json)"
        )

        if filename:
            self.filename = filename
            self.save_config()

    def save_config(self):
        if self.filename is not None:
            config_string = self.rootnode.dump()
            with open(self.filename, 'w') as f:
                f.write(config_string)
            self.dirty = False
        else:
            self.show_savecfg_dlg()

    def show_opencfg_dlg(self):
        # show file dialog
        filename, _ = QFileDialog.getOpenFileName(
            self, self.tr("Open configuration file..."),
            directory=os.path.expanduser("~"),
            filter=self.tr("Json file (*.json);;All files (*.*)")
        )

        # load config file
        if filename:
            self.load_config(filename)

    def refresh_windowTitle(self):
        s = "%s %s" % (QCoreApplication.applicationName(),
                       QCoreApplication.applicationVersion())
        if self.filename is not None:
            s += " - " + self.filename
        if self.dirty:
            s += "*"
        self.setWindowTitle(s)

    # filename property
    @property
    def filename(self):
        return self._filename

    @filename.setter
    def filename(self, value=""):
        self._filename = value
        self.refresh_windowTitle()

    # dirty property
    @property
    def dirty(self):
        return self._dirty

    @dirty.setter
    def dirty(self, value):
        self._dirty = value
        self.refresh_windowTitle()

    def set_dirty(self):
        self.dirty = True