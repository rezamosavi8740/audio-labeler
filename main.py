# main.py
# Entry point — MainWindow manages navigation between pages.
# English comments are included.

import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QStackedWidget
from PySide6.QtCore import Qt

from code.ui.pages.home import HomePage
from code.ui.pages.sample_types import SampleTypesPage
from code.ui.styles import app_qss


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Audio Labeler")
        self.resize(1100, 700)

        # Central router: QStackedWidget
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        # Instantiate pages
        self.home = HomePage()
        self.page_specs = SampleTypesPage()

        # Add pages to stack
        self.stack.addWidget(self.home)
        self.stack.addWidget(self.page_specs)

        # Navigation: Home -> Sample Types
        self.home.sig_sample_types.connect(lambda: self.stack.setCurrentWidget(self.page_specs))
        # Navigation: Sample Types -> Home
        self.page_specs.sig_go_home.connect(lambda: self.stack.setCurrentWidget(self.home))

        # Apply global stylesheet
        self.setStyleSheet(app_qss)


def main():
    app = QApplication(sys.argv)
    app.setLayoutDirection(Qt.LeftToRight)  # UI direction
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()