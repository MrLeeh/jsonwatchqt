"""
    Settings Dialog for CSV export.
    Copyright (c) 2015 by Stefan Lehmann

"""

from qtpy.QtCore import QSettings
from qtpy.QtWidgets import QDialog, QLabel, QComboBox, QDialogButtonBox, \
    QGridLayout


DECIMAL_SETTING = "csv/decimal"
SEPARATOR_SETTING = "csv/separator"


class CSVSettingsDialog(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.settings = QSettings()

        # decimal
        self.decimalLabel = QLabel(self.tr("decimal:"))
        self.decimalComboBox = QComboBox()
        self.decimalLabel.setBuddy(self.decimalComboBox)
        self.decimalComboBox.addItems([",", "."])

        # separator
        self.separatorLabel = QLabel(self.tr("separator:"))
        self.separatorComboBox = QComboBox()
        self.separatorLabel.setBuddy(self.separatorComboBox)
        self.separatorComboBox.addItem("Semicolon ';'", ';')
        self.separatorComboBox.addItem("Comma ','", ',')
        self.separatorComboBox.addItem("Tabulator '\\t'", '\t')
        self.separatorComboBox.addItem("Whitespace ' '", ' ')

        # buttons
        self.buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

        # layout
        layout = QGridLayout()
        layout.addWidget(self.decimalLabel, 0, 0)
        layout.addWidget(self.decimalComboBox, 0, 1)
        layout.addWidget(self.separatorLabel, 1, 0)
        layout.addWidget(self.separatorComboBox, 1, 1)
        layout.addWidget(self.buttons, 2, 0, 1, 2)
        self.setLayout(layout)

        # settings
        self.decimalComboBox.setCurrentIndex(
            self.decimalComboBox.findText(
                self.settings.value(DECIMAL_SETTING, ","))
        )
        self.separatorComboBox.setCurrentIndex(
            self.separatorComboBox.findData(
                self.settings.value(SEPARATOR_SETTING, ";"))
        )

        self.setWindowTitle(self.tr("record settings"))

    def accept(self):
        self.settings.setValue(DECIMAL_SETTING, self.decimal)
        self.settings.setValue(SEPARATOR_SETTING, self.separator)
        super().accept()

    # decimal property
    @property
    def decimal(self):
        return self.decimalComboBox.currentText()

    # seperator property
    @property
    def separator(self):
        return self.separatorComboBox.itemData(
            self.separatorComboBox.currentIndex())
