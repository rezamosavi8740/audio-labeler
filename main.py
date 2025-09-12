# main.py
# English comments are included.
# Entry point of the application — loads HomePage inside MainWindow.

import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QStackedWidget
from PySide6.QtCore import Qt

# Import our UI components
from code.ui.pages.home import HomePage
from code.ui.styles import app_qss


class MainWindow(QMainWindow):
    """
    Main window holds a QStackedWidget (router).
    For now it only shows HomePage.
    Later we add NewSample, EditSample, etc.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Audio Labeler")
        self.resize(1100, 700)

        # Central stacked widget
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        # Instantiate Home page
        self.home = HomePage()

        # Add to stack
        self.stack.addWidget(self.home)

        # Apply global stylesheet
        self.setStyleSheet(app_qss)


def main():
    app = QApplication(sys.argv)
    app.setLayoutDirection(Qt.LeftToRight)  # keep UI left-to-right
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()