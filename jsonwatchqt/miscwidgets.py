from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QSpinBox


class MySpinBox(QSpinBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setRange(-100000, 100000)
        self.setAlignment(Qt.AlignRight)