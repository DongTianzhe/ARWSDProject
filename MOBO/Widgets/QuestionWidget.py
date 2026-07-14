from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QButtonGroup, QRadioButton, QHBoxLayout, QSlider
from PySide6.QtCore import Qt

class QuestionWidget(QWidget):
    def __init__(self, questionData):
        """
        ### Structure of questionData:\n
        {
            "title": str
            "options": [str]
        }
        """
        super().__init__()
        
        self.data = questionData

        layout = QVBoxLayout(self)
        title = QLabel(questionData['title'])
        layout.addWidget(title)

        self.questionGroup = questionData['group']
        self.type = questionData['type']
        self.smallIsBetter = questionData['smallIsBetter']

        if self.type == 'checkbox':
            self.group = QButtonGroup(self)
            optionLayout = QHBoxLayout()

            for option in questionData['options']:
                button = QRadioButton(str(option))
                self.group.addButton(button)
                optionLayout.addWidget(button)
            
            layout.addLayout(optionLayout)
        elif self.type == 'slider':
            self.currentValue = 0
            self.numberLabel = QLabel('1')
            self.slider = QSlider()
            self.slider.setOrientation(Qt.Orientation.Horizontal)
            self.slider.setRange(self.data['min'], self.data['max'])
            self.slider.setPageStep = self.data['step']
            self.slider.setValue(1)
            self.slider.valueChanged.connect(self.updateLabel)
            layout.addWidget(self.numberLabel)
            layout.addWidget(self.slider)
    
    def updateLabel(self, value):
        self.currentValue = value
        self.numberLabel.setText(str(value))
    
    def getAnswer(self):
        if self.type == 'checkbox':
            button = self.group.checkedButton()
            if button:
                return button.text()
            return None
        elif self.type == 'slider':
            return self.currentValue
