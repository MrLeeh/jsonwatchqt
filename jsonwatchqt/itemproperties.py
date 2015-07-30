"""
    Copyright (c) 2015 by Stefan Lehmann

"""
from qtpy.QtCore import QSignalMapper, Qt
from qtpy.QtWidgets import QDialog, QLabel, QLineEdit, QGridLayout, QComboBox, \
    QSpinBox, QDoubleSpinBox, QDialogButtonBox, QApplication, QCheckBox
import sys
from jsonwatch.abstractjsonitem import VALUETYPES
from jsonwatch.jsonitem import JsonItem
from jsonwatchqt.utilities import critical


class NoZerosDoubleSpinBox(QDoubleSpinBox):
    def textFromValue(self, value: float):
        s = super().textFromValue(value)
        return s.rstrip("0").rstrip(".,")


class ItemPropertyDialog(QDialog):
    def __init__(self, jsonitem: JsonItem, parent=None):
        super().__init__(parent)

        assert jsonitem is not None
        self.item = jsonitem

        # name
        self.nameLabel = QLabel(self.tr("name:"))
        self.nameLineEdit = QLineEdit(self.item.name or "")
        self.nameLabel.setBuddy(self.nameLineEdit)

        # unit
        self.unitLabel = QLabel(self.tr("unit:"))
        self.unitLineEdit = QLineEdit(self.item.unit or "")
        self.unitLabel.setBuddy(self.unitLineEdit)

        # type
        self.typeLabel = QLabel(self.tr("type:"))
        self.typeComboBox = QComboBox()
        self.typeComboBox.addItems([k for k, t in VALUETYPES])
        self.typeComboBox.setCurrentIndex(
            self.typeComboBox.findText(self.item.type))
        self.typeComboBox.currentIndexChanged.connect(self.data_changed)
        self.typeLabel.setBuddy(self.typeComboBox)

        # decimals
        self.decimalsLabel = QLabel(self.tr("decimals:"))
        self.decimalsSpinBox = QSpinBox()
        self.decimalsSpinBox.setRange(0, 10)
        self.decimalsSpinBox.setValue(self.item.decimals or 0)
        self.decimalsLabel.setBuddy(self.decimalsSpinBox)
        self.decimalsSpinBox.valueChanged.connect(self.data_changed)
        self.last_decimals = self.decimalsSpinBox.value()

        # min
        self.minLabel = QLabel(self.tr("minimum:"))
        self.minSpinBox =QDoubleSpinBox()
        self.minSpinBox.setRange(-sys.maxsize, sys.maxsize)
        self.minLabel.setBuddy(self.minSpinBox)
        self.minSpinBox.setValue(self.item.min or 0.0)

        # max
        self.maxLabel = QLabel(self.tr("maximum:"))
        self.maxSpinBox = QDoubleSpinBox()
        self.maxSpinBox.setRange(-sys.maxsize, sys.maxsize)
        self.maxSpinBox.setValue(self.item.max or 100.0)

        # numerator
        self.scalefactorLabel = QLabel(self.tr("scalefactor:"))
        self.scalefactorSpinBox = NoZerosDoubleSpinBox()
        self.scalefactorSpinBox.setRange(-sys.maxsize, sys.maxsize)
        self.scalefactorSpinBox.setButtonSymbols(QSpinBox.NoButtons)
        self.scalefactorSpinBox.setDecimals(10)
        self.scalefactorSpinBox.setValue(self.item.scalefactor or 1)
        self.scalefactorLabel.setBuddy(self.scalefactorSpinBox)

        # readonly
        self.readonlyCheckBox = QCheckBox(self.tr("readonly"))
        self.readonlyCheckBox.setChecked(Qt.Checked if self.item.readonly
                                         else Qt.Unchecked)
        self.readonlyCheckBox.stateChanged.connect(self.data_changed)

        # buttons
        self.buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal
        )
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

        # layout
        layout = QGridLayout()
        layout.addWidget(self.nameLabel, 0, 0)
        layout.addWidget(self.nameLineEdit, 0, 1)
        layout.addWidget(self.unitLabel, 1, 0)
        layout.addWidget(self.unitLineEdit, 1, 1)
        layout.addWidget(self.typeLabel, 2, 0)
        layout.addWidget(self.typeComboBox, 2, 1)
        layout.addWidget(self.decimalsLabel, 3, 0)
        layout.addWidget(self.decimalsSpinBox, 3, 1)
        layout.addWidget(self.minLabel, 4, 0)
        layout.addWidget(self.minSpinBox, 4, 1)
        layout.addWidget(self.maxLabel, 5, 0)
        layout.addWidget(self.maxSpinBox, 5, 1)
        layout.addWidget(self.scalefactorLabel, 6, 0)
        layout.addWidget(self.scalefactorSpinBox, 6, 1)
        layout.addWidget(self.readonlyCheckBox, 7, 0, 1, 2)
        layout.addWidget(self.buttons, 8, 0, 1, 2)
        self.setLayout(layout)

        # misc
        self.setWindowTitle("Edit JsonItem '%s'" % self.item.key)
        self.data_changed()

    def accept(self):
        self.item.name = self.nameLineEdit.text()
        self.item.unit = self.unitLineEdit.text()
        self.item.decimals = self.decimalsSpinBox.value()
        self.item.min = self.minSpinBox.value()
        self.item.max = self.maxSpinBox.value()
        self.item.scalefactor = self.scalefactorSpinBox.value()
        self.item.readonly = self.readonlyCheckBox.checkState() == Qt.Checked
        self.item.type = self.typeComboBox.currentText()
        return super().accept()

    def data_changed(self):
        type_numeric = self.typeComboBox.currentText() not in ('bool', 'str')
        type_int = self.typeComboBox.currentText() == 'int'
        readonly  = self.readonlyCheckBox.checkState() == Qt.Checked

        # not used properties invisible
        self.decimalsSpinBox.setVisible(type_numeric)
        self.decimalsLabel.setVisible(type_numeric)

        self.scalefactorSpinBox.setVisible(type_numeric)
        self.scalefactorLabel.setVisible(type_numeric)

        self.minSpinBox.setVisible(type_numeric and not readonly)
        self.minLabel.setVisible(type_numeric and not readonly)

        self.maxSpinBox.setVisible(type_numeric and not readonly)
        self.maxLabel.setVisible(type_numeric and not readonly)

        self.unitLineEdit.setVisible(type_numeric)
        self.unitLabel.setVisible(type_numeric)

        # no decimals for int
        self.minSpinBox.setDecimals(self.decimalsSpinBox.value())
        self.maxSpinBox.setDecimals(self.decimalsSpinBox.value())

        if type_int:
            delta = self.decimalsSpinBox.value() - self.last_decimals
            self.scalefactorSpinBox.setValue(
                self.scalefactorSpinBox.value() / 10**delta
            )

        self.last_decimals = self.decimalsSpinBox.value()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    item = JsonItem('me', name="my property", type='float', scalefactor=1)
    dlg = ItemPropertyDialog(item)
    dlg.exec_()
