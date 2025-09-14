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
from code.ui.pages.edit_hub import EditHubPage
from code.ui.pages.csv_reports import CsvReportsPage   # ← NEW
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
        self.page_home    = HomePage()          # Home (4 cards)
        self.page_new     = NewSamplePage()     # Step 1: metadata (supports create/edit)
        self.page_specs   = SampleTypesPage()   # Sample Types & Specs (CSV editable)
        self.page_labels  = LabelEditorPage()   # Step 2: attach & label
        self.page_edit    = EditHubPage()       # Hub for editing existing samples
        self.page_reports = CsvReportsPage()    # CSV Reports (export)

        # --- Add pages to router ---
        for p in (
            self.page_home,
            self.page_new,
            self.page_specs,
            self.page_labels,
            self.page_edit,
            self.page_reports,
        ):
            self.stack.addWidget(p)

        # --- Navigation wiring ---

        # Home -> Step 1 (new)
        self.page_home.sig_new_sample.connect(lambda: self.stack.setCurrentWidget(self.page_new))

        # Home -> Sample Types & Specs
        self.page_home.sig_sample_types.connect(lambda: self.stack.setCurrentWidget(self.page_specs))

        # Home -> Edit hub
        self.page_home.sig_edit_sample.connect(self._open_edit_hub)

        # Home -> CSV Reports
        self.page_home.sig_csv_reports.connect(self._open_csv_reports)

        # Step 1 -> Home
        self.page_new.sig_go_home.connect(lambda: self.stack.setCurrentWidget(self.page_home))

        # Step 1 finished -> open Step 2 for that sample_id
        self.page_new.sig_go_step2.connect(self._go_step2)

        # Specs -> Home
        self.page_specs.sig_go_home.connect(lambda: self.stack.setCurrentWidget(self.page_home))

        # Step 2 -> Home (Back button)
        self.page_labels.sig_go_home.connect(lambda: self.stack.setCurrentWidget(self.page_home))

        # Edit hub -> Home
        self.page_edit.sig_go_home.connect(lambda: self.stack.setCurrentWidget(self.page_home))

        # Edit hub -> Metadata (open Step 1 in edit mode)
        self.page_edit.sig_edit_metadata.connect(self._open_edit_metadata)

        # Edit hub -> Labels (open Step 2)
        self.page_edit.sig_edit_labels.connect(self._open_edit_labels)

        # Reports -> Home
        self.page_reports.sig_go_home.connect(lambda: self.stack.setCurrentWidget(self.page_home))

        # --- Global stylesheet ---
        self.setStyleSheet(app_qss)

    # -------- Handlers --------
    def _go_step2(self, sample_id: str):
        """Prepare and navigate to label editor for the given sample_id."""
        self.page_labels.open_for(sample_id)
        self.stack.setCurrentWidget(self.page_labels)

    def _open_edit_hub(self):
        """Open EditHub and refresh its view."""
        # Ensure EditHub has the optional public `open()` to refresh search/table.
        if hasattr(self.page_edit, "open"):
            self.page_edit.open()
        self.stack.setCurrentWidget(self.page_edit)

    def _open_edit_metadata(self, sample_id: str):
        """Open Step 1 in edit mode for the chosen sample_id."""
        # Your NewSamplePage should expose open_for_edit(sample_id: str)
        self.page_new.open_for_edit(sample_id)
        self.stack.setCurrentWidget(self.page_new)

    def _open_edit_labels(self, sample_id: str):
        """Open Step 2 (Label Editor) for the chosen sample_id."""
        self.page_labels.open_for(sample_id)
        self.stack.setCurrentWidget(self.page_labels)

    def _open_csv_reports(self):
        """Open CSV Reports page and refresh both tabs."""
        if hasattr(self.page_reports, "open"):
            self.page_reports.open()
        self.stack.setCurrentWidget(self.page_reports)


def main():
    """Bootstraps the Qt application and shows the MainWindow."""
    app = QApplication(sys.argv)
    app.setLayoutDirection(Qt.LeftToRight)  # change to RightToLeft if needed
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()