# main.py
# English comments included.
# Application entry point — hosts a QStackedWidget (router) and wires up pages.

import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QStackedWidget
from PySide6.QtCore import Qt

# Pages and global stylesheet
from code.ui.pages.home import HomePage
from code.ui.pages.new_sample import NewSamplePage
from code.ui.pages.sample_types import SampleTypesPage
from code.ui.pages.label_editor import LabelEditorPage
from code.ui.styles import app_qss


class MainWindow(QMainWindow):
    """Main window that owns the router (QStackedWidget) and handles navigation."""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Audio Labeler")
        # A compact default size that fits all toolbars without needing fullscreen
        self.resize(1200, 740)
        self.setMinimumSize(980, 600)

        # --- Central router ---
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        # --- Instantiate pages ---
        self.page_home = HomePage()          # Home (4 cards)
        self.page_new = NewSamplePage()      # Step 1: metadata
        self.page_specs = SampleTypesPage()  # Sample Types & Specs (CSV editable)
        self.page_labels = LabelEditorPage() # Step 2: attach & label

        # --- Add pages to router ---
        self.stack.addWidget(self.page_home)
        self.stack.addWidget(self.page_new)
        self.stack.addWidget(self.page_specs)
        self.stack.addWidget(self.page_labels)

        # --- Navigation wiring ---

        # Home -> Step 1
        self.page_home.sig_new_sample.connect(
            lambda: self.stack.setCurrentWidget(self.page_new)
        )

        # Home -> Sample Types & Specs
        self.page_home.sig_sample_types.connect(
            lambda: self.stack.setCurrentWidget(self.page_specs)
        )

        # (Optional placeholders for future routes)
        self.page_home.sig_edit_sample.connect(self._todo_edit_sample)
        self.page_home.sig_csv_reports.connect(self._todo_csv_reports)

        # Step 1 -> Home
        self.page_new.sig_go_home.connect(
            lambda: self.stack.setCurrentWidget(self.page_home)
        )

        # Step 1 finished -> open Step 2 for that sample_id
        self.page_new.sig_go_step2.connect(self._go_step2)

        # Specs -> Home
        self.page_specs.sig_go_home.connect(
            lambda: self.stack.setCurrentWidget(self.page_home)
        )

        # ✅ Step 2 (Label Editor) -> Home  (Back button)
        self.page_labels.sig_go_home.connect(
            lambda: self.stack.setCurrentWidget(self.page_home)
        )

        # --- Global stylesheet ---
        self.setStyleSheet(app_qss)

    # -------- Handlers --------
    def _go_step2(self, sample_id: str):
        """Prepare and navigate to label editor for the given sample_id."""
        self.page_labels.open_for(sample_id)
        self.stack.setCurrentWidget(self.page_labels)

    def _todo_edit_sample(self):
        """Placeholder for a future page (e.g., batch editor)."""
        self.stack.setCurrentWidget(self.page_home)

    def _todo_csv_reports(self):
        """Placeholder for a future reports/export page."""
        self.stack.setCurrentWidget(self.page_home)


def main():
    """Bootstraps the Qt application and shows the MainWindow."""
    app = QApplication(sys.argv)
    app.setLayoutDirection(Qt.LeftToRight)  # change to RightToLeft if desired
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()