import sys
import QuestionnairePage as QuestionnairePage
from PySide6.QtWidgets import QApplication


if __name__ == '__main__':
    app = QApplication(sys.argv)

    window = QuestionnairePage.MainWindow()

    window.show()
    app.exec()
