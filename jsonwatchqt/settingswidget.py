import sys
import json

from qtpy.QtCore import Qt
from qtpy.QtWidgets import QWidget, QLabel, QGridLayout, QApplication, \
    QPushButton, QDialog, QCheckBox
from serial.serialutil import SerialException
from jsonwatch.jsonnode import JsonNode
from jsonwatch.jsonitem import JsonItem
from jsonwatchqt.jsonmapper import JsonMapper
from jsonwatchqt.miscwidgets import MySpinBox
from jsonwatchqt.utilities import critical


class CtrlSettingsWidget(QDialog):
    def __init__(self, serial, rootnode: JsonNode, parent=None):
        super().__init__(parent)
        self.serial = serial
        self.rootnode = rootnode
        self.mapper = JsonMapper(self.rootnode)

        # P-part
        self.pLabel = QLabel("P:")
        self.pSpinBox = MySpinBox()
        self.pLabel.setBuddy(self.pSpinBox)
        self.mapper.map("kp", self.pSpinBox)

        # I-part
        self.iLabel = QLabel("I:")
        self.iSpinBox = MySpinBox()
        self.iLabel.setBuddy(self.iSpinBox)
        self.mapper.map("ki", self.iSpinBox)

        # D-part
        self.dLabel = QLabel("D:")
        self.dSpinBox = MySpinBox()
        self.dLabel.setBuddy(self.dSpinBox)
        self.mapper.map("kd", self.dSpinBox)

        # PWM frequency
        self.pwmLabel = QLabel("PWM Frequenz:")
        self.pwmSpinBox = MySpinBox()
        self.pwmLabel.setBuddy(self.pwmSpinBox)
        self.mapper.map("fq", self.pwmSpinBox)

        # Seek interval
        self.seekLabel = QLabel("Seek Intervall:")
        self.seekSpinBox = MySpinBox()
        self.seekLabel.setBuddy(self.seekSpinBox)
        self.mapper.map("seekinterval", self.seekSpinBox)

        # Seek time
        self.seektimeLabel = QLabel("Seek Time:")
        self.seektimeSpinBox = MySpinBox()
        self.seektimeLabel.setBuddy(self.seektimeSpinBox)
        self.mapper.map("seektime", self.seektimeSpinBox)

        # Anti windup
        self.antiwindupCheckBox = QCheckBox(self.tr("anti-windup"))
        self.mapper.map("antiwindup", self.antiwindupCheckBox,
                        getter='isChecked', setter='setChecked')

        # Send Button
        self.sendButton = QPushButton("Send")
        self.sendButton.pressed.connect(self.send_settings)

        # Layout
        layout = QGridLayout()
        layout.addWidget(self.pLabel, 0, 0)
        layout.addWidget(self.pSpinBox, 0, 1)
        layout.addWidget(self.iLabel, 1, 0)
        layout.addWidget(self.iSpinBox, 1, 1)
        layout.addWidget(self.dLabel, 2, 0)
        layout.addWidget(self.dSpinBox, 2, 1)
        layout.addWidget(self.pwmLabel, 3, 0)
        layout.addWidget(self.pwmSpinBox, 3, 1)
        layout.addWidget(self.seekLabel, 4, 0)
        layout.addWidget(self.seekSpinBox, 4, 1)
        layout.addWidget(self.seektimeLabel, 5, 0)
        layout.addWidget(self.seektimeSpinBox, 5, 1)
        layout.addWidget(self.antiwindupCheckBox, 6, 1)
        layout.addWidget(self.sendButton, 7, 1)
        self.setLayout(layout)

        self.request_settings()

    def closeEvent(self, QCloseEvent):
        self.parent().settingsWidget = None

    def request_settings(self):
        # send request for setting data
        node = JsonNode('root')
        node.add_child(JsonItem('send_settings', 1))
        try:
            self.serial.write(bytearray(node.to_json(), 'utf-8'))
        except AttributeError as e:
            critical(self.parent(), self.tr("Serial Port is not open."))

    def refresh(self):
        self.mapper.map_from_node()

    def send_settings(self, *argv):
        self.mapper.map_to_node()
        try:
            self.serial.write(bytearray(self.rootnode.to_json(), 'utf-8'))
        except (AttributeError, SerialException) as e:
            critical(self.parent(), self.tr("Serial Port is not open."))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = CtrlSettingsWidget()
    w.show()
    app.exec_()
