# code/ui/pages/edit_hub.py
# Edit hub: pick a metadata row, then jump to edit metadata / edit labels,
# or add new WAV(s) to that metadata (open label editor in attach mode).

from pathlib import Path
from datetime import datetime

import pandas as pd

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTableView, QMessageBox, QFrame
)

from code.ui.widgets.pandas_model import PandasModel

DATA_DIR     = Path.cwd() / "data"
META_CSV     = DATA_DIR / "samples_meta.csv"

class EditHubPage(QWidget):
    sig_go_home = Signal()
    sig_edit_metadata = Signal(str)            # sample_id
    sig_edit_labels   = Signal(str)            # sample_id
    sig_add_sample_to_metadata = Signal(str)   # sample_id  (NEW)

    def __init__(self):
        super().__init__()

        # Top bar
        top = QHBoxLayout()
        self.btn_back = QPushButton("← Home")
        self.btn_back.setProperty("class", "back")
        self.btn_back.clicked.connect(self.sig_go_home.emit)
        title = QLabel("Edit — Pick a Sample")
        title.setProperty("class", "h1")
        top.addWidget(self.btn_back)
        top.addWidget(title)
        top.addStretch()

        # Tool row
        tool_card = QFrame()
        tool_card.setObjectName("toolCard")
        tool = QHBoxLayout(tool_card)
        tool.setContentsMargins(12, 10, 12, 10)
        tool.setSpacing(8)

        self.search = QLineEdit()
        self.search.setPlaceholderText("Search by id or name…")
        self.btn_reload = QPushButton("↻ Reload")
        self.btn_edit_meta = QPushButton("📝 Edit Metadata")
        self.btn_edit_meta.setProperty("variant", "primary")
        self.btn_edit_labels = QPushButton("🎧 Edit Labels")
        self.btn_edit_labels.setProperty("variant", "accent")

        # NEW: add WAV(s) to selected metadata
        self.btn_add_to_meta = QPushButton("➕ Add Sample to Metadata")
        self.btn_add_to_meta.setProperty("variant", "success")

        # Delete metadata(s)
        self.btn_delete = QPushButton("🗑 Delete")
        self.btn_delete.setProperty("variant", "danger")

        for b in (self.btn_reload, self.btn_edit_meta, self.btn_edit_labels, self.btn_add_to_meta, self.btn_delete):
            b.setMinimumHeight(32)

        tool.addWidget(self.search, 1)
        tool.addWidget(self.btn_reload)
        tool.addWidget(self.btn_edit_meta)
        tool.addWidget(self.btn_edit_labels)
        tool.addWidget(self.btn_add_to_meta)   # << NEW
        tool.addWidget(self.btn_delete)

        # Table
        self.table = QTableView()
        self.table.setSelectionBehavior(QTableView.SelectRows)
        self.table.setSelectionMode(QTableView.SingleSelection)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setDefaultSectionSize(32)

        # Root
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(12)
        root.addLayout(top)
        root.addWidget(tool_card)
        root.addWidget(self.table)

        # Wire
        self.btn_reload.clicked.connect(self._reload)
        self.btn_edit_meta.clicked.connect(self._emit_edit_meta)
        self.btn_edit_labels.clicked.connect(self._emit_edit_labels)
        self.btn_add_to_meta.clicked.connect(self._emit_add_to_meta)  # << NEW
        self.btn_delete.clicked.connect(self._delete_selected)

        self.search.returnPressed.connect(self._apply_filter)

        # State
        self._df = pd.DataFrame()

    # ---------- public ----------
    def open(self):
        """Load/refresh on entering this page."""
        self._reload()

    # ---------- helpers ----------
    def _reload(self):
        try:
            df = pd.read_csv(META_CSV, dtype=str, encoding="utf-8")
        except Exception:
            df = pd.DataFrame(columns=["sample_id", "sample_name", "date", "time", "labels_csv", "created_at"])
        # Ensure columns and order
        for c in ["sample_id", "sample_name", "date", "time", "labels_csv", "created_at"]:
            if c not in df.columns:
                df[c] = ""
        self._df = df[["sample_id", "sample_name", "date", "time", "labels_csv", "created_at"]]

        self._apply_filter()  # populates model

    def _apply_filter(self):
        q = (self.search.text() or "").strip().lower()
        if not q:
            dfv = self._df.copy()
        else:
            dfv = self._df[
                self._df["sample_id"].str.lower().str.contains(q, na=False) |
                self._df["sample_name"].str.lower().str.contains(q, na=False)
            ].copy()

        self.model = PandasModel(dfv)
        self.table.setModel(self.model)
        self.table.resizeColumnsToContents()

    def _selected_sample_id(self) -> str | None:
        sel = self.table.selectionModel().selectedRows()
        if not sel:
            QMessageBox.information(self, "Select", "Please select a metadata row first.")
            return None
        r = sel[0].row()
        df_view = self.model.dataframe()
        return str(df_view.loc[r, "sample_id"])

    def _emit_edit_meta(self):
        sid = self._selected_sample_id()
        if sid:
            self.sig_edit_metadata.emit(sid)

    def _emit_edit_labels(self):
        sid = self._selected_sample_id()
        if sid:
            self.sig_edit_labels.emit(sid)

    def _emit_add_to_meta(self):
        """Open label editor for this metadata and immediately ask user to attach WAV(s)."""
        sid = self._selected_sample_id()
        if sid:
            self.sig_add_sample_to_metadata.emit(sid)

    def _delete_selected(self):
        sel = self.table.selectionModel().selectedRows()
        if not sel:
            return
        rows = sorted([ix.row() for ix in sel])
        df_view = self.model.dataframe()
        sids = [str(df_view.loc[r, "sample_id"]) for r in rows]

        ret = QMessageBox.question(
            self, "Confirm delete",
            f"Delete {len(sids)} metadata row(s)?\n"
            f"All linked label CSV files will also be removed.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if ret != QMessageBox.Yes:
            return

        # Remove label CSV paths if present
        for r in rows:
            p = str(df_view.loc[r, "labels_csv"]) if "labels_csv" in df_view.columns else ""
            if isinstance(p, str) and p.strip():
                try:
                    Path(p).unlink(missing_ok=True)
                except Exception:
                    pass

        # Remove from META_CSV
        try:
            df_all = pd.read_csv(META_CSV, dtype=str, encoding="utf-8")
        except Exception:
            return
        df_all = df_all[~df_all["sample_id"].astype(str).isin(sids)]
        df_all.to_csv(META_CSV, index=False, encoding="utf-8")
        self._reload()