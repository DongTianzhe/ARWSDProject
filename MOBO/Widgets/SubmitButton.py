from PySide6.QtWidgets import QPushButton
from PySide6.QtCore import QSize

class SubmitButton(QPushButton):
    def __init__(self):
        super().__init__()

        self.setText('Submit')
        self.setStyleSheet("QPushButton {background-color: #66ccff; color: white}")
