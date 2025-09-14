# code/ui/pages/labels_picker.py
from __future__ import annotations
from pathlib import Path
from datetime import datetime

import pandas as pd

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QTableView, QLabel, QFrame, QFileDialog, QMessageBox
)

from code.ui.widgets.pandas_model import PandasModel

DATA_DIR   = Path.cwd() / "data"
LABELS_DIR = DATA_DIR / "labels"

class LabelsPickerPage(QWidget):
    """Shows all label CSVs linked to a given sample_id and lets the user pick one to edit."""
    sig_go_back = Signal()                              # back to EditHub
    sig_open_labels = Signal(str, str)                  # (sample_id, csv_path)

    def __init__(self):
        super().__init__()
        self.sample_id: str | None = None
        self._df: pd.DataFrame | None = None

        # Top bar
        top = QHBoxLayout()
        self.btn_back = QPushButton("← Back")
        self.btn_back.setProperty("class", "back")
        self.btn_back.clicked.connect(self.sig_go_back.emit)

        self.title = QLabel("Pick a Labels CSV")
        self.title.setProperty("class", "h1")
        top.addWidget(self.btn_back, alignment=Qt.AlignLeft)
        top.addWidget(self.title, alignment=Qt.AlignLeft)
        top.addStretch()

        # Toolbar
        tool_card = QFrame(); tool_card.setObjectName("toolCard")
        tool = QHBoxLayout(tool_card); tool.setContentsMargins(12,10,12,10); tool.setSpacing(8)
        self.search = QLineEdit(); self.search.setPlaceholderText("Filter by file name or path...")
        self.btn_reload = QPushButton("↻ Reload"); self.btn_reload.setProperty("variant", "soft")
        self.btn_open   = QPushButton("✳ Open Selected"); self.btn_open.setProperty("variant", "primary")

        tool.addWidget(self.search, 1)
        tool.addWidget(self.btn_reload)
        tool.addWidget(self.btn_open)

        # Table
        self.table = QTableView()
        self.table.setSelectionBehavior(QTableView.SelectRows)
        self.table.setSelectionMode(QTableView.SingleSelection)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setDefaultSectionSize(30)

        # Root
        root = QVBoxLayout(self)
        root.setContentsMargins(24,24,24,24)
        root.setSpacing(12)
        root.addLayout(top)
        root.addWidget(tool_card)
        root.addWidget(self.table)

        # Wire
        self.btn_reload.clicked.connect(self._reload)
        self.btn_open.clicked.connect(self._open_selected)
        self.search.returnPressed.connect(self._apply_filter)

    # -------- API --------
    def open_for(self, sample_id: str):
        self.sample_id = sample_id
        self.title.setText(f"Pick a Labels CSV • {sample_id}")
        self.search.clear()
        self._reload()

    # -------- Internals --------
    def _scan_csvs(self) -> pd.DataFrame:
        """Find {sample_id}__*.csv files in data/labels."""
        rows = []
        if LABELS_DIR.exists():
            for p in sorted(LABELS_DIR.glob(f"{self.sample_id}__*.csv")):
                try:
                    stat = p.stat()
                    rows.append({
                        "csv_name": p.name,
                        "csv_path": str(p),
                        "size_kb": f"{stat.st_size/1024:.1f}",
                        "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                    })
                except Exception:
                    rows.append({"csv_name": p.name, "csv_path": str(p), "size_kb": "", "modified": ""})
        df = pd.DataFrame(rows, columns=["csv_name", "csv_path", "size_kb", "modified"])
        return df

    def _reload(self):
        df = self._scan_csvs()
        self._df = df
        self._set_model(df)

    def _set_model(self, df: pd.DataFrame):
        model = PandasModel(df)
        self.table.setModel(model)
        self.table.resizeColumnsToContents()

    def _apply_filter(self):
        if self._df is None:
            return
        q = self.search.text().strip().lower()
        if not q:
            self._set_model(self._df)
            return
        mask = self._df["csv_name"].str.lower().str.contains(q) | self._df["csv_path"].str.lower().str.contains(q)
        self._set_model(self._df[mask].reset_index(drop=True))

    def _open_selected(self):
        model = self.table.model()
        if model is None or model.rowCount() == 0:
            QMessageBox.information(self, "Open", "No CSV selected.")
            return
        sel = self.table.selectionModel().selectedRows()
        if not sel:
            QMessageBox.information(self, "Open", "Please select a row.")
            return
        r = sel[0].row()
        csv_path = model.index(r, model.columnCount()-3).sibling(r, 1).data()  # column 1 == csv_path
        self.sig_open_labels.emit(self.sample_id, csv_path)