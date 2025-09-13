# code/ui/pages/sample_types.py
# English comments are included.
# "Sample Types & Specs" page:
# - Shows an editable table backed by sample_list.csv
# - On first open, creates the CSV with default schema if missing
# - Supports Add Row / Delete Selected / Save CSV / Reload CSV

from PySide6.QtWidgets import (
    QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QTableView, QFileDialog, QMessageBox
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QAction
from pathlib import Path
import pandas as pd

from code.ui.widgets.pandas_model import PandasModel

# Where to keep CSV (project local ./data/sample_list.csv)
DATA_DIR = Path.cwd() / "data"
CSV_PATH = DATA_DIR / "sample_list.csv"

# Default schema / initial rows
DEFAULT_COLUMNS = ["ID", "Type", "Factor", "Value", "Count"]
DEFAULT_ROWS = [
    {"ID": 1, "Type": "Acoustic", "Factor": "SNR", "Value": 20, "Count": 3},
    {"ID": 2, "Type": "Acoustic", "Factor": "SNR", "Value": 21, "Count": 4},
]


from PySide6.QtWidgets import QFrame  # add this import

class SampleTypesPage(QWidget):
    sig_go_home = Signal()

    def __init__(self):
        super().__init__()

        # ----- Top bar (Back + Title) -----
        top = QHBoxLayout()
        self.btn_back = QPushButton("← Home")
        self.btn_back.setProperty("class", "back")
        title = QLabel("Sample Types & Specs")
        title.setProperty("class", "h1")
        top.addWidget(self.btn_back, alignment=Qt.AlignLeft)
        top.addWidget(title, alignment=Qt.AlignLeft)
        top.addStretch()

        # ===== New: toolbar inside a white card frame =====
        tool_card = QFrame()
        tool_card.setObjectName("toolCard")
        tool_card.setStyleSheet("""
            QFrame#toolCard {
                background: #ffffff;
                border: 1px solid #dbe3ee;
                border-radius: 14px;
            }
        """)
        tool_wrap = QHBoxLayout(tool_card)
        tool_wrap.setContentsMargins(12, 10, 12, 10)
        tool_wrap.setSpacing(10)

        # Buttons with theme variants
        self.btn_add    = QPushButton("➕ Add Row");          self.btn_add.setProperty("variant", "success")
        self.btn_del    = QPushButton("🗑️ Delete Selected");  self.btn_del.setProperty("variant", "danger")
        self.btn_save   = QPushButton("💾 Save CSV");         self.btn_save.setProperty("variant", "primary")
        self.btn_reload = QPushButton("↻ Reload");            self.btn_reload.setProperty("variant", "soft")
        self.btn_import = QPushButton("📥 Import CSV…");      self.btn_import.setProperty("variant", "accent")
        self.btn_export = QPushButton("📤 Export CSV As…");   self.btn_export.setProperty("variant", "warn")

        for b in (self.btn_add, self.btn_del, self.btn_save, self.btn_reload, self.btn_import, self.btn_export):
            b.setMinimumHeight(34)

        tool_wrap.addWidget(self.btn_add)
        tool_wrap.addWidget(self.btn_del)
        tool_wrap.addSpacing(8)
        tool_wrap.addWidget(self.btn_save)
        tool_wrap.addWidget(self.btn_reload)
        tool_wrap.addStretch()
        tool_wrap.addWidget(self.btn_import)
        tool_wrap.addWidget(self.btn_export)

        # ----- Table -----
        self.table = QTableView()
        self.table.setAlternatingRowColors(False)
        self.table.setSelectionBehavior(QTableView.SelectRows)
        self.table.setSelectionMode(QTableView.ExtendedSelection)
        self.table.horizontalHeader().setStretchLastSection(True)

        # ----- Root layout -----
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(12)
        root.addLayout(top)
        root.addWidget(tool_card)   # ← card-styled toolbar
        root.addWidget(self.table)

        # connections + rest of logic remain the same ...
        self.btn_back.clicked.connect(self.sig_go_home.emit)
        self.btn_add.clicked.connect(self.add_row)
        self.btn_del.clicked.connect(self.delete_selected_rows)
        self.btn_save.clicked.connect(self.save_csv)
        self.btn_reload.clicked.connect(self.load_csv)
        self.btn_import.clicked.connect(self.import_csv_dialog)
        self.btn_export.clicked.connect(self.export_csv_dialog)

        self.model = None
        self.ensure_csv_exists()
        self.load_csv()
        self._make_shortcuts()
    # ----- CSV handling -----
    def ensure_csv_exists(self):
        """Create data folder and default CSV if not present."""
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        if not CSV_PATH.exists():
            df = pd.DataFrame(DEFAULT_ROWS, columns=DEFAULT_COLUMNS)
            df.to_csv(CSV_PATH, index=False, encoding="utf-8")

    def load_csv(self):
        """Load CSV into the table model."""
        try:
            df = pd.read_csv(CSV_PATH, dtype=str, encoding="utf-8")
        except Exception:
            # If file invalid, recreate with default schema
            df = pd.DataFrame(columns=DEFAULT_COLUMNS)

        # Ensure required columns exist
        for col in DEFAULT_COLUMNS:
            if col not in df.columns:
                df[col] = ""

        # Reorder columns to default order
        df = df[DEFAULT_COLUMNS]

        # Convert numeric columns if possible
        for col in ("ID", "Value", "Count"):
            try:
                df[col] = pd.to_numeric(df[col], errors="ignore", downcast="integer")
            except Exception:
                pass

        self.model = PandasModel(df)
        self.table.setModel(self.model)
        self.table.resizeColumnsToContents()

    def save_csv(self):
        """Validate/coerce numeric columns and save to CSV."""
        if not self.model:
            return
        df = self.model.dataframe().copy()

        # Coerce numerics on save
        for col in ("ID", "Value", "Count"):
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna("").astype("Int64")

        # Fill missing strings
        for col in ("Type", "Factor"):
            df[col] = df[col].fillna("")

        try:
            df.to_csv(CSV_PATH, index=False, encoding="utf-8")
            QMessageBox.information(self, "Saved", f"Saved to:\n{CSV_PATH}")
        except Exception as e:
            QMessageBox.critical(self, "Save error", str(e))

    # ----- Table actions -----
    def add_row(self):
        """Append a new row with auto-increment ID."""
        if not self.model:
            return
        df = self.model.dataframe()
        # Compute next ID
        try:
            next_id = int(pd.to_numeric(df["ID"], errors="coerce").dropna().max()) + 1
        except Exception:
            next_id = 1
        self.model.insert_empty_row(
            {"ID": next_id, "Type": "", "Factor": "", "Value": "", "Count": ""}
        )
        # Scroll to the new row
        last = self.model.index(self.model.rowCount() - 1, 0)
        self.table.scrollTo(last)

    def delete_selected_rows(self):
        """Delete selected rows from the table/model."""
        if not self.model:
            return
        sel = self.table.selectionModel().selectedRows()
        if not sel:
            return
        rows = [ix.row() for ix in sel]
        self.model.remove_rows(rows)

    # ----- Import/Export dialogs -----
    def import_csv_dialog(self):
        """Allow user to pick a CSV file and replace current table."""
        path, _ = QFileDialog.getOpenFileName(self, "Import CSV", str(Path.cwd()), "CSV Files (*.csv)")
        if not path:
            return
        try:
            df = pd.read_csv(path, dtype=str, encoding="utf-8")
            # Ensure required columns
            for col in DEFAULT_COLUMNS:
                if col not in df.columns:
                    df[col] = ""
            df = df[DEFAULT_COLUMNS]
            self.model = PandasModel(df)
            self.table.setModel(self.model)
            self.table.resizeColumnsToContents()
        except Exception as e:
            QMessageBox.critical(self, "Import error", str(e))

    def export_csv_dialog(self):
        """Export current table to another CSV file."""
        if not self.model:
            return
        out, _ = QFileDialog.getSaveFileName(self, "Export CSV As", str(Path.cwd() / "export.csv"), "CSV Files (*.csv)")
        if not out:
            return
        try:
            self.model.dataframe().to_csv(out, index=False, encoding="utf-8")
            QMessageBox.information(self, "Exported", f"Exported to:\n{out}")
        except Exception as e:
            QMessageBox.critical(self, "Export error", str(e))

    # ----- UX helpers -----
    def _make_shortcuts(self):
        """Optional keyboard shortcuts: Ctrl+S save, Del delete rows, Ctrl+N new row."""
        act_save = QAction(self)
        act_save.setShortcut("Ctrl+S")
        act_save.triggered.connect(self.save_csv)
        self.addAction(act_save)

        act_new = QAction(self)
        act_new.setShortcut("Ctrl+N")
        act_new.triggered.connect(self.add_row)
        self.addAction(act_new)

        act_del = QAction(self)
        act_del.setShortcut(Qt.Key.Key_Delete)
        act_del.triggered.connect(self.delete_selected_rows)
        self.addAction(act_del)