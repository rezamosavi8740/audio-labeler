# main.py
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
from code.ui.pages.csv_reports import CsvReportsPage
from code.ui.pages.labels_picker import LabelsPickerPage
from code.ui.styles import app_qss


class MainWindow(QMainWindow):
    """Main window that owns the router (QStackedWidget) and handles navigation."""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Audio Labeler")
        self.resize(1200, 740)
        self.setMinimumSize(980, 600)

        # --- Central router ---
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        # --- Instantiate pages ---
        self.page_home    = HomePage()          # Home (4 cards)
        self.page_new     = NewSamplePage()     # Step 1: metadata (create/edit)
        self.page_specs   = SampleTypesPage()   # Sample Types & Specs
        self.page_labels  = LabelEditorPage()   # Step 2: attach & label
        self.page_edit    = EditHubPage()       # Hub for editing existing samples
        self.page_reports = CsvReportsPage()    # CSV Reports (export)
        self.page_pick    = LabelsPickerPage()  # Picker for per-sample label CSVs

        # --- Add pages to router ---
        for p in (
            self.page_home,
            self.page_new,
            self.page_specs,
            self.page_labels,
            self.page_edit,
            self.page_reports,
            self.page_pick,
        ):
            self.stack.addWidget(p)

        # --- Navigation wiring ---

        # Home
        self.page_home.sig_new_sample.connect(lambda: self.stack.setCurrentWidget(self.page_new))
        self.page_home.sig_sample_types.connect(lambda: self.stack.setCurrentWidget(self.page_specs))
        self.page_home.sig_edit_sample.connect(self._open_edit_hub)
        self.page_home.sig_csv_reports.connect(self._open_csv_reports)

        # Step 1 (NewSamplePage)
        self.page_new.sig_go_home.connect(lambda: self.stack.setCurrentWidget(self.page_home))
        self.page_new.sig_go_step2.connect(self._go_step2)  # open label editor for created sample_id

        # Sample Types
        self.page_specs.sig_go_home.connect(lambda: self.stack.setCurrentWidget(self.page_home))

        # Label Editor
        self.page_labels.sig_go_home.connect(lambda: self.stack.setCurrentWidget(self.page_home))

        # Edit Hub
        self.page_edit.sig_go_home.connect(lambda: self.stack.setCurrentWidget(self.page_home))
        self.page_edit.sig_edit_metadata.connect(self._open_edit_metadata)
        self.page_edit.sig_edit_labels.connect(self._open_edit_labels)  # opens picker
        # optional: add sample to metadata (jump to editor and immediately attach WAV)
        if hasattr(self.page_edit, "sig_add_sample_to_metadata"):
            self.page_edit.sig_add_sample_to_metadata.connect(self._open_labels_and_attach)

        # Labels Picker
        self.page_pick.sig_go_back.connect(lambda: self.stack.setCurrentWidget(self.page_edit))
        self.page_pick.sig_open_labels.connect(self._open_labels_existing)

        # Reports
        self.page_reports.sig_go_home.connect(lambda: self.stack.setCurrentWidget(self.page_home))

        # --- Global stylesheet ---
        self.setStyleSheet(app_qss)

    # -------- Handlers --------
    def _go_step2(self, sample_id: str):
        """Prepare and navigate to label editor for the given sample_id (fresh session)."""
        self.page_labels.open_for(sample_id)
        self.stack.setCurrentWidget(self.page_labels)

    def _open_edit_hub(self):
        """Open EditHub and refresh its view."""
        if hasattr(self.page_edit, "open"):
            self.page_edit.open()
        self.stack.setCurrentWidget(self.page_edit)

    def _open_edit_metadata(self, sample_id: str):
        """Open Step 1 in edit mode for the chosen sample_id."""
        self.page_new.open_for_edit(sample_id)
        self.stack.setCurrentWidget(self.page_new)

    def _open_edit_labels(self, sample_id: str):
        """Open labels picker for this metadata (choose one of {sample_id}__*.csv)."""
        self.page_pick.open_for(sample_id)
        self.stack.setCurrentWidget(self.page_pick)

    def _open_labels_existing(self, sample_id: str, csv_path: str):
        """Open editor with an existing labels CSV path."""
        self.page_labels.open_existing(sample_id, csv_path)
        self.stack.setCurrentWidget(self.page_labels)

    def _open_labels_and_attach(self, sample_id: str):
        """Open editor for metadata and immediately prompt to attach WAV(s)."""
        self.page_labels.open_for(sample_id)
        self.stack.setCurrentWidget(self.page_labels)
        if hasattr(self.page_labels, "attach_new_wav_dialog"):
            self.page_labels.attach_new_wav_dialog()

    def _open_csv_reports(self):
        """Open CSV Reports page and refresh both tabs."""
        if hasattr(self.page_reports, "open"):
            self.page_reports.open()
        self.stack.setCurrentWidget(self.page_reports)


def main():
    """Bootstraps the Qt application and shows the MainWindow."""
    app = QApplication(sys.argv)
    app.setLayoutDirection(Qt.LeftToRight)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()