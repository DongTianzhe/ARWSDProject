from PySide6.QtWidgets import QMainWindow, QVBoxLayout, QHBoxLayout, QScrollArea, QWidget, QMessageBox, QLabel
from PySide6.QtCore import Qt
from Widgets.QuestionWidget import QuestionWidget
from Widgets.SubmitButton import SubmitButton
from Widgets.LoadingDialog import LoadingDialog
from WaitingPage import WaitingWindow
import json
import socket

socketClient = socket.socket()
socketOpened = False
recvBuffer = ''

def recvJSON():
    global recvBuffer
    while True:
        idx = recvBuffer.find('\n')
        if idx != -1:
            line = recvBuffer[:idx]
            recvBuffer = recvBuffer[idx+1:]
            if line.strip():
                return json.loads(line)
        recvBuffer += socketClient.recv(4096).decode('utf-8')

def recvType(expectedType):
    while True:
        msg = recvJSON()
        msgType = msg.get('type')
        print('Receive: ', msgType)
        if msgType == expectedType:
            return msg
        print('Ignore: ', msg)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.iterationType = 'Sampling'
        self.iteration = 1

        self.questionnaireData = {}

        self.loadingDialog = LoadingDialog()
        self.waitingWindow = WaitingWindow()

        with open('InitialisationConfiguration.json', encoding='utf-8') as f:
            self.initConfig = json.load(f)
        
        with open('Questions.json', encoding='utf-8') as f:
            self.questions = json.load(f)
        
        questionData = []
        for i in range(len(self.questions)):
            questionData.append(self.questions[i]['title'])
        self.questionnaireData['questions'] = questionData
        print(self.questionnaireData)
        
        self.iterations = {'Sampling': int(self.initConfig['config']['numSamplingIterations']), 'Optimization': int(self.initConfig['config']['numOptimizationIterations'])}
        if self.iterations['Sampling'] == 0:
            self.iterationType = 'optimization'
        
        if socketOpened:
            socketClient.connect(('localhost', 56001))
            print('Socket client opened')
            socketClient.send(json.dumps(self.initConfig).encode('utf-8'))
            socketClient.send('\n'.encode('utf-8'))

            if self.iterations['Sampling'] != 0:
                # Receive sampling parameters
                print('Receving Initial Sampling Parameters')
                msg = recvType('parameters')
                print(msg)
        
        self.initialisation()
    
    def initialisation(self):
        scrollArea = QScrollArea()
        scrollArea.setWidgetResizable(True)

        container = QWidget()
        layout = QVBoxLayout(container)

        self.questionWidgets = []

        for questionData in self.questions:
            question = QuestionWidget(questionData)

            layout.addWidget(question)
            self.questionWidgets.append(question)

        submitButton = SubmitButton()
        submitButton.clicked.connect(self.buttonClickEvent)
        
        objectives = self.initConfig["objectives"]
        self.submitDict = {}
        for i in objectives:
            self.submitDict[i['key']] = 0

        iterationLabel = QLabel(text=f'{self.iterationType} Iteration: {str(self.iteration)}')

        infoLayout = QHBoxLayout()
        infoLayout.addWidget(submitButton)
        infoLayout.addWidget(iterationLabel)
        
        layout.addStretch()
        
        scrollArea.setWidget(container)

        outer = QVBoxLayout()
        outer.addWidget(scrollArea)
        outer.addLayout(infoLayout)
        widget = QWidget()
        widget.setLayout(outer)
        self.setCentralWidget(widget)
    
    def buttonClickEvent(self):
        #Initialise self.submitDict
        for key in self.submitDict.keys():
            self.submitDict[key] = 0
        
        currentQuestionnaireData = []
        
        for widget in self.questionWidgets:
            ans = widget.getAnswer()
            # Prevent unanswered questions
            if ans == None:
                QMessageBox.information(self, "info", "Please answer all the question.")
                return
            currentQuestionnaireData.append(int(ans))
            if widget.type == 'checkbox':
                if widget.smallIsBetter:
                    self.submitDict[widget.questionGroup] -= int(ans)
                else:
                    self.submitDict[widget.questionGroup] += int(ans)
            elif widget.type == 'slider':
                self.submitDict[widget.questionGroup] = int(ans)
        
        self.questionnaireData[f'{self.iterationType} {self.iteration}'] = currentQuestionnaireData
        # print(self.questionnaireData)
        submitDictNew = {'type': 'objectives', 'values': self.submitDict}
        print(submitDictNew)
        self.loadingDialog.show()
        if socketOpened:
            # Send score of questionnaire
            socketClient.send(json.dumps(submitDictNew).encode('utf-8'))
            socketClient.send('\n'.encode('utf-8'))

        # QMessageBox.information(self, "Success", "Submittion succuss. Please continue experiment.")

        if self.iterationType == 'Sampling':
            if self.iteration == self.iterations['Sampling']:
                self.iterationType = 'Optimization'
                self.iteration = 1
                if socketOpened:
                    print('Receiving Coverage')
                    msg = recvType('coverage')
                    print('Converage: ', msg)
                    print(f'Receiving parameters in {self.iterationType} Iteration {self.iteration}')
                    msg = recvType('parameters')
                    print('Parameters: ', msg)
                print('Sampling Finshed')
                print(self.iterationType)
            else:
                self.iteration += 1
                if socketOpened:
                    print(f'Receiving parameters in {self.iterationType} Iteration {self.iteration}')
                    msg = recvType('parameters')
                    print('Parameters: ', msg)
        else:
            if socketOpened:
                    print('Receiving Coverage')
                    msg = recvType('coverage')
                    print('Coverage: ', msg)
            if self.iteration == self.iterations['Optimization']:
                with open ('questionData.json', 'w', encoding='utf-8') as f:
                        json.dump(self.questionnaireData, f)
                if socketOpened:
                    # Receive Optimisation Finished notice
                    msg = recvType('optimization_finished')
                    print('Optimization Finished')  
                QMessageBox.information(self, "Information", "Optimisation Finished")
            else:
                self.iteration += 1
                if socketOpened:
                    print(f'Receiving parameters in {self.iterationType} Iteration {self.iteration}')
                    msg = recvType('parameters')
                    print('Parameters: ', msg)
        
        
        #Initialisation for next iteration
        self.loadingDialog.hide()
        self.initialisation()

    def closeEvent(self, event):
        if socketOpened:
            if socketClient:
                socketClient.close()
                print('Close Client Socket')

