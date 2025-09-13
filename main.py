# main.py
# Entry point — MainWindow manages navigation between pages.
# English comments are included.

import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QStackedWidget
from PySide6.QtCore import Qt

from code.ui.pages.home import HomePage
from code.ui.pages.sample_types import SampleTypesPage
from code.ui.pages.new_sample import NewSamplePage
from code.ui.styles import app_qss


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Audio Labeler")
        self.resize(1100, 700)

        # ✅ central router
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        # ✅ instantiate pages
        self.home = HomePage()
        self.page_new = NewSamplePage()
        self.page_specs = SampleTypesPage()

        # ✅ add pages to stack
        self.stack.addWidget(self.home)
        self.stack.addWidget(self.page_new)
        self.stack.addWidget(self.page_specs)

        # ✅ navigation wiring
        self.home.sig_new_sample.connect(lambda: self.stack.setCurrentWidget(self.page_new))
        self.page_new.sig_go_home.connect(lambda: self.stack.setCurrentWidget(self.home))
        self.page_new.sig_go_step2.connect(self._go_step2)

        self.home.sig_sample_types.connect(lambda: self.stack.setCurrentWidget(self.page_specs))
        self.page_specs.sig_go_home.connect(lambda: self.stack.setCurrentWidget(self.home))

        # ✅ global stylesheet
        self.setStyleSheet(app_qss)

    def _go_step2(self, sample_id: str):
        # TODO: navigate to Step 2 page when implemented.
        print("[DEBUG] Go to Step 2 for:", sample_id)
        self.stack.setCurrentWidget(self.home)


def main():
    app = QApplication(sys.argv)
    app.setLayoutDirection(Qt.LeftToRight)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()