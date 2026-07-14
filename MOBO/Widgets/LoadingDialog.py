from PySide6.QtWidgets import QDialog, QLabel, QVBoxLayout

class LoadingDialog(QDialog):
    def __init__(self):
        super().__init__()

        label = QLabel('Submitting')

        layout = QVBoxLayout()
        layout.addWidget(label)

        self.setLayout(layout)
