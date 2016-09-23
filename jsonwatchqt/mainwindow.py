#! python3

"""
    GUI for Ultrasonic Temperature Controller
    Copyright (c) 2015 by Stefan Lehmann

"""

import os
import datetime
import logging
import json

import serial
from qtpy.QtWidgets import QAction, QDialog, QMainWindow, QMessageBox, \
    QDockWidget, QLabel, QFileDialog, QApplication
from qtpy.QtGui import QIcon
from qtpy.QtCore import QSettings, QCoreApplication, Qt, QThread, \
    Signal

from serial.serialutil import SerialException
from jsonwatch.jsonitem import JsonItem
from jsonwatch.jsonnode import JsonNode
from jsonwatchqt.logger import LoggingWidget
from pyqtconfig.config import QSettingsManager
from jsonwatchqt.plotsettings import PlotSettingsWidget
from jsonwatchqt.objectexplorer import ObjectExplorer
from jsonwatchqt.plotwidget import PlotWidget
from jsonwatchqt.serialdialog import SerialDialog, PORT_SETTING, \
    BAUDRATE_SETTING
from jsonwatchqt.utilities import critical, pixmap
from jsonwatchqt.recorder import RecordWidget
from jsonwatchqt.csvsettings import CSVSettingsDialog, DECIMAL_SETTING, \
    SEPARATOR_SETTING


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


def set_default_settings(settings: QSettingsManager):
    settings.set_defaults({
        DECIMAL_SETTING: ',',
        SEPARATOR_SETTING: ';'
    })


class SerialWorker(QThread):
    data_received = Signal(datetime.datetime, str)

    def __init__(self, ser: serial.Serial, parent=None):
        super().__init__(parent)
        self.serial = ser
        self._quit = False

    def run(self):
        while not self._quit:
            try:
                if self.serial.isOpen() and self.serial.inWaiting():
                    self.data_received.emit(
                        datetime.datetime.now(),
                        strip(bytearray_to_utf8(self.serial.readline()))
                    )
            except SerialException:
                pass

    def quit(self):
        self._quit = True


class MainWindow(QMainWindow):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.recording_enabled = False
        self.serial = serial.Serial()
        self.rootnode = JsonNode('')
        self._connected = False
        self._dirty = False
        self._filename = None

        # settings
        self.settings = QSettingsManager()
        set_default_settings(self.settings)

        # Controller Settings
        self.settingsDialog = None

        # object explorer
        self.objectexplorer = ObjectExplorer(self.rootnode, self)
        self.objectexplorer.nodevalue_changed.connect(self.send_serialdata)
        self.objectexplorer.nodeproperty_changed.connect(self.set_dirty)
        self.objectexplorerDockWidget = QDockWidget(self.tr("object explorer"),
                                                    self)
        self.objectexplorerDockWidget.setObjectName(
            "objectexplorer_dockwidget")
        self.objectexplorerDockWidget.setWidget(self.objectexplorer)

        # plot widget
        self.plot = PlotWidget(self.rootnode, self.settings, self)

        # plot settings
        self.plotsettings = PlotSettingsWidget(self.settings, self.plot, self)
        self.plotsettingsDockWidget = QDockWidget(self.tr("plot settings"),
                                                  self)
        self.plotsettingsDockWidget.setObjectName("plotsettings_dockwidget")
        self.plotsettingsDockWidget.setWidget(self.plotsettings)

        # log widget
        self.loggingWidget = LoggingWidget(self)
        self.loggingDockWidget = QDockWidget(self.tr("logger"), self)
        self.loggingDockWidget.setObjectName("logging_dockwidget")
        self.loggingDockWidget.setWidget(self.loggingWidget)

        # record widget
        self.recordWidget = RecordWidget(self.rootnode, self)
        self.recordDockWidget = QDockWidget(self.tr("data recording"), self)
        self.recordDockWidget.setObjectName("record_dockwidget")
        self.recordDockWidget.setWidget(self.recordWidget)

        # actions and menus
        self._init_actions()
        self._init_menus()

        # statusbar
        statusbar = self.statusBar()
        statusbar.setVisible(True)
        self.connectionstateLabel = QLabel(self.tr("Not connected"))
        statusbar.addPermanentWidget(self.connectionstateLabel)
        statusbar.showMessage(self.tr("Ready"))

        # layout
        self.setCentralWidget(self.plot)
        self.addDockWidget(Qt.LeftDockWidgetArea,
                           self.objectexplorerDockWidget)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.plotsettingsDockWidget)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.loggingDockWidget)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.recordDockWidget)

        self.load_settings()

    def _init_actions(self):
        # Serial Dialog
        self.serialdlgAction = QAction(self.tr("Serial Settings..."), self)
        self.serialdlgAction.setShortcut("F6")
        self.serialdlgAction.setIcon(QIcon(pixmap("configure.png")))
        self.serialdlgAction.triggered.connect(self.show_serialdlg)

        # Connect
        self.connectAction = QAction(self.tr("Connect"), self)
        self.connectAction.setShortcut("F5")
        self.connectAction.setIcon(QIcon(pixmap("network-connect-3.png")))
        self.connectAction.triggered.connect(self.toggle_connect)

        # Quit
        self.quitAction = QAction(self.tr("Quit"), self)
        self.quitAction.setShortcut("Alt+F4")
        self.quitAction.setIcon(QIcon(pixmap("window-close-3.png")))
        self.quitAction.triggered.connect(self.close)

        # Save Config as
        self.saveasAction = QAction(self.tr("Save as..."), self)
        self.saveasAction.setShortcut("Ctrl+Shift+S")
        self.saveasAction.setIcon(QIcon(pixmap("document-save-as-5.png")))
        self.saveasAction.triggered.connect(self.show_savecfg_dlg)

        # Save file
        self.saveAction = QAction(self.tr("Save"), self)
        self.saveAction.setShortcut("Ctrl+S")
        self.saveAction.setIcon(QIcon(pixmap("document-save-5.png")))
        self.saveAction.triggered.connect(self.save_file)

        # Load file
        self.loadAction = QAction(self.tr("Open..."), self)
        self.loadAction.setShortcut("Ctrl+O")
        self.loadAction.setIcon(QIcon(pixmap("document-open-7.png")))
        self.loadAction.triggered.connect(self.show_opencfg_dlg)

        # New
        self.newAction = QAction(self.tr("New"), self)
        self.newAction.setShortcut("Ctrl+N")
        self.newAction.setIcon(QIcon(pixmap("document-new-6.png")))
        self.newAction.triggered.connect(self.new)

        # start recording
        self.startrecordingAction = QAction(self.tr("Start recording"), self)
        self.startrecordingAction.setShortcut("F9")
        self.startrecordingAction.setIcon(QIcon(pixmap("media-record-6.png")))
        self.startrecordingAction.triggered.connect(self.start_recording)

        # stop recording
        self.stoprecordingAction = QAction(self.tr("Stop recording"), self)
        self.stoprecordingAction.setShortcut("F10")
        self.stoprecordingAction.setIcon(QIcon(pixmap("media-playback-stop-8.png")))
        self.stoprecordingAction.setEnabled(False)
        self.stoprecordingAction.triggered.connect(self.stop_recording)

        # clear record
        self.clearrecordAction = QAction(self.tr("Clear"), self)
        self.clearrecordAction.setIcon(QIcon(pixmap("editclear.png")))
        self.clearrecordAction.triggered.connect(self.clear_record)

        # export record
        self.exportcsvAction = QAction(self.tr("Export to csv..."), self)
        self.exportcsvAction.setIcon(QIcon(pixmap("text_csv.png")))
        self.exportcsvAction.triggered.connect(self.export_csv)

        # show record settings
        self.recordsettingsAction = QAction(self.tr("Settings..."), self)
        self.recordsettingsAction.setIcon(QIcon(pixmap("configure.png")))
        self.recordsettingsAction.triggered.connect(self.show_recordsettings)

        # Info
        self.infoAction = QAction(self.tr("Info"), self)
        self.infoAction.setShortcut("F1")
        self.infoAction.triggered.connect(self.show_info)

    def _init_menus(self):
        # file menu
        self.fileMenu = self.menuBar().addMenu(self.tr("File"))
        self.fileMenu.addAction(self.newAction)
        self.fileMenu.addAction(self.loadAction)
        self.fileMenu.addAction(self.saveAction)
        self.fileMenu.addAction(self.saveasAction)
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.connectAction)
        self.fileMenu.addAction(self.serialdlgAction)
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.quitAction)

        # view menu
        self.viewMenu = self.menuBar().addMenu(self.tr("View"))
        self.viewMenu.addAction(
            self.objectexplorerDockWidget.toggleViewAction())
        self.viewMenu.addAction(self.plotsettingsDockWidget.toggleViewAction())
        self.viewMenu.addAction(self.loggingDockWidget.toggleViewAction())
        self.viewMenu.addAction(self.recordDockWidget.toggleViewAction())

        # record menu
        self.recordMenu = self.menuBar().addMenu(self.tr("Record"))
        self.recordMenu.addAction(self.startrecordingAction)
        self.recordMenu.addAction(self.stoprecordingAction)
        self.recordMenu.addAction(self.exportcsvAction)
        self.recordMenu.addSeparator()
        self.recordMenu.addAction(self.clearrecordAction)
        self.recordMenu.addSeparator()
        self.recordMenu.addAction(self.recordsettingsAction)

        # info menu
        self.menuBar().addAction(self.infoAction)

    def show_info(self):
        QMessageBox.about(
            self, QApplication.applicationName(),
            "%s %s\n"
            "Copyright (c) by %s" %
            (
                QCoreApplication.applicationName(),
                QCoreApplication.applicationVersion(),
                QCoreApplication.organizationName(),
            )
        )

    def load_file(self, filename):
        old_filename = self.filename if self.filename != filename else None
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
                    if old_filename is not None:
                        self.load_file(old_filename)
                    else:
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
            self.load_file(self.filename)

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
                self.save_file()

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

    def receive_serialdata(self, time, data):
        self.loggingWidget.log_input(data)

        try:
            self.rootnode.from_json(data)
        except ValueError as e:
            logger.error(str(e))

        # refresh widgets
        self.objectexplorer.refresh()
        self.plot.refresh(time)
        if self.recording_enabled:
            self.recordWidget.add_data(time, self.rootnode)

    def send_serialdata(self, node):
        if isinstance(node, JsonItem):
            if self.serial.isOpen():
                s = node.to_json()
                self.serial.write(utf8_to_bytearray(s + '\n'))
                self.loggingWidget.log_output(s.strip())

    def show_serialdlg(self):
        dlg = SerialDialog(self.settings, self)
        dlg.exec_()

    def toggle_connect(self):
        if self.serial.isOpen():
            self.disconnect()
        else:
            self.connect()

    def connect(self):
        # Load port setting
        port = self.settings.get(PORT_SETTING)
        baudrate = self.settings.get(BAUDRATE_SETTING)

        # If no port has been selected before show serial settings dialog
        if port is None:
            if self.show_serialdlg() == QDialog.Rejected:
                return
            port = self.settings.get(PORT_SETTING)
            baudrate = self.settings.get(BAUDRATE_SETTING)

        # Serial connection
        try:
            self.serial.port = port
            self.serial.baudrate = baudrate
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
            self.connectAction.setIcon(QIcon(pixmap("network-disconnect-3.png")))
            self.serialdlgAction.setEnabled(False)
            self.connectionstateLabel.setText(
                self.tr("Connected to %s") % port)
            self._connected = True
            self.objectexplorer.refresh()

    def disconnect(self):
        self.worker.quit()
        self.serial.close()
        self.connectAction.setText(self.tr("Connect"))
        self.connectAction.setIcon(QIcon(pixmap("network-connect-3.png")))
        self.serialdlgAction.setEnabled(True)
        self.connectionstateLabel.setText(self.tr("Not connected"))
        self._connected = False
        self.objectexplorer.refresh()

    def show_savecfg_dlg(self):
        filename, _ = QFileDialog.getSaveFileName(
            self, self.tr("Save configuration file..."),
            directory=os.path.expanduser("~"),
            filter="Json file (*.json)"
        )

        if filename:
            self.filename = filename
            self.save_file()

    def save_file(self):
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
            self.load_file(filename)

    def refresh_window_title(self):
        s = "%s %s" % (QCoreApplication.applicationName(),
                       QCoreApplication.applicationVersion())
        if self.filename is not None:
            s += " - " + self.filename
        if self.dirty:
            s += "*"
        self.setWindowTitle(s)

    def start_recording(self):
        self.recording_enabled = True
        self.startrecordingAction.setEnabled(False)
        self.stoprecordingAction.setEnabled(True)

    def stop_recording(self):
        self.recording_enabled = False
        self.startrecordingAction.setEnabled(True)
        self.stoprecordingAction.setEnabled(False)

    def export_csv(self):
        filename, _ = QFileDialog.getSaveFileName(
            self, QCoreApplication.applicationName(),
            filter="CSV files(*.csv);;All files (*.*)"
        )

        if filename == "":
            return

        # get current dataframe and export to csv
        df = self.recordWidget.dataframe
        decimal = self.settings.get(DECIMAL_SETTING)
        df = df.applymap(lambda x: str(x).replace(".", decimal))
        df.to_csv(
            filename, index_label="time",
            sep=self.settings.get(SEPARATOR_SETTING)
        )

    def clear_record(self):
        self.recordWidget.clear()

    def show_recordsettings(self):
        dlg = CSVSettingsDialog(self)
        dlg.exec_()

    # filename property
    @property
    def filename(self):
        return self._filename

    @filename.setter
    def filename(self, value=""):
        self._filename = value
        self.refresh_window_title()

    # dirty property
    @property
    def dirty(self):
        return self._dirty

    @dirty.setter
    def dirty(self, value):
        self._dirty = value
        self.refresh_window_title()

    def set_dirty(self):
        self.dirty = True

    # connected property
    @property
    def connected(self):
        return self._connected
