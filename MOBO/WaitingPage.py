from PySide6.QtWidgets import QMainWindow, QVBoxLayout, QPushButton, QLabel, QWidget

class WaitingWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        label = QLabel('Submit success. Please continue experiment')
        button = QPushButton('Start Evaluation')

        layout = QVBoxLayout()
        layout.addWidget(label)
        layout.addWidget(button)

        self.setLayout(layout)
    
    def buttonClickEvent(self):
        self.close()