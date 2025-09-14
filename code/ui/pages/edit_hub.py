# code/ui/pages/edit_hub.py
# Edit hub: search by id/name (press Enter), open edit pages, and delete metadata + related CSVs.

from pathlib import Path
from typing import List

import pandas as pd

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableView, QMessageBox, QFrame
)

from code.ui.widgets.pandas_model import PandasModel

# Project paths
DATA_DIR = Path.cwd() / "data"
META_CSV = DATA_DIR / "samples_meta.csv"
LABELS_DIR = DATA_DIR / "labels"


class EditHubPage(QWidget):
    """Lists samples from samples_meta.csv, supports search, open, and delete."""

    # Navigation signals
    sig_go_home = Signal()
    sig_edit_metadata = Signal(str)   # emits sample_id
    sig_edit_labels = Signal(str)     # emits sample_id

    def __init__(self):
        super().__init__()

        # ---- top bar ----
        top = QHBoxLayout()
        self.btn_back = QPushButton("← Home")
        self.btn_back.setProperty("class", "back")
        self.btn_back.clicked.connect(self.sig_go_home.emit)

        title = QLabel("Edit — Pick a Sample")
        title.setProperty("class", "h1")

        top.addWidget(self.btn_back, alignment=Qt.AlignLeft)
        top.addWidget(title, alignment=Qt.AlignLeft)
        top.addStretch()

        # ---- toolbar (search + actions) ----
        tool_card = QFrame()
        tool_card.setObjectName("toolCard")
        tool = QHBoxLayout(tool_card)
        tool.setContentsMargins(12, 10, 12, 10)
        tool.setSpacing(8)

        self.search = QLineEdit()
        self.search.setPlaceholderText("Search by id or name…")
        self.search.setClearButtonEnabled(True)
        self.search.returnPressed.connect(self._do_search)  # Enter triggers search

        self.btn_reload = QPushButton("↻ Reload")
        self.btn_reload.setProperty("variant", "soft")
        self.btn_reload.clicked.connect(self._reload_all)

        self.btn_edit_meta = QPushButton("📝 Edit Metadata")
        self.btn_edit_meta.setProperty("variant", "primary")
        self.btn_edit_meta.clicked.connect(self._open_edit_meta)

        self.btn_edit_labels = QPushButton("🎛 Edit Labels")
        self.btn_edit_labels.setProperty("variant", "accent")
        self.btn_edit_labels.clicked.connect(self._open_edit_labels)

        self.btn_delete = QPushButton("🗑 Delete")
        self.btn_delete.setProperty("variant", "danger")
        self.btn_delete.clicked.connect(self._delete_selected)

        tool.addWidget(self.search, 1)
        tool.addWidget(self.btn_reload)
        tool.addWidget(self.btn_edit_meta)
        tool.addWidget(self.btn_edit_labels)
        tool.addWidget(self.btn_delete)

        # ---- table ----
        self.table = QTableView()
        self.table.setSelectionBehavior(QTableView.SelectRows)
        self.table.setSelectionMode(QTableView.ExtendedSelection)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setDefaultSectionSize(32)

        # ---- root ----
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(12)
        root.addLayout(top)
        root.addWidget(tool_card)
        root.addWidget(self.table)

        # state
        self._df_full = pd.DataFrame()
        self._model: PandasModel | None = None

        # initial load
        self._reload_all()

    # ---------- data load / filter ----------
    def _reload_all(self):
        """Load full metadata CSV into the table."""
        if META_CSV.exists():
            try:
                self._df_full = pd.read_csv(META_CSV, dtype=str, encoding="utf-8")
            except Exception:
                self._df_full = pd.DataFrame()
        else:
            self._df_full = pd.DataFrame()

        # Ensure useful columns exist and order them
        cols_order = ["sample_id", "sample_name", "date", "time", "labels_csv", "created_at"]
        for c in cols_order:
            if c not in self._df_full.columns:
                self._df_full[c] = ""
        self._df_full = self._df_full[cols_order]

        self._apply_df_to_table(self._df_full)

    def _do_search(self):
        """Filter by id or name using the search text; empty => show all."""
        q = (self.search.text() or "").strip().lower()
        if not q:
            self._apply_df_to_table(self._df_full)
            return

        df = self._df_full.copy()
        mask = (
            df["sample_id"].astype(str).str.lower().str.contains(q, na=False)
            | df["sample_name"].astype(str).str.lower().str.contains(q, na=False)
        )
        self._apply_df_to_table(df[mask].reset_index(drop=True))

    def _apply_df_to_table(self, df: pd.DataFrame):
        """Bind a dataframe to the table via PandasModel."""
        self._model = PandasModel(df.reset_index(drop=True))
        self.table.setModel(self._model)
        self.table.resizeColumnsToContents()

    # ---------- selection helpers ----------
    def _selected_sample_ids(self) -> List[str]:
        if not self._model:
            return []
        rows = [ix.row() for ix in self.table.selectionModel().selectedRows()]
        if not rows:
            return []
        df = self._model.dataframe()
        return [str(df.loc[r, "sample_id"]) for r in rows]

    def _safe_path_from_value(self, val):
        """Return a valid Path if val looks like a non-empty path string; otherwise None."""
        if val is None:
            return None
        # pandas missing values often come as float('nan')
        if isinstance(val, float):
            return None
        s = str(val).strip()
        if not s or s.lower() == "nan":
            return None
        return Path(s)

    def open(self, query: str = "") -> None:
        """Refresh table and optionally pre-fill the search box.
        Called by MainWindow when navigating to this page."""
        self._reload_all()          # reload full meta csv
        self.search.setText(query)  # optional preset query
        self._do_search()           # apply current search (or show all if empty)
        self.search.setFocus()      # UX: focus search box
        # Optionally select the first row for quick actions
        if self.table.model() and self.table.model().rowCount() > 0:
            self.table.selectRow(0)

    # ---------- open actions ----------
    def _open_edit_meta(self):
        ids = self._selected_sample_ids()
        if not ids:
            QMessageBox.information(self, "Select", "Please select a row.")
            return
        self.sig_edit_metadata.emit(ids[0])

    def _open_edit_labels(self):
        ids = self._selected_sample_ids()
        if not ids:
            QMessageBox.information(self, "Select", "Please select a row.")
            return
        self.sig_edit_labels.emit(ids[0])

    # ---------- delete ----------
    def _delete_selected(self):
        """Delete selected rows from meta and remove all related CSVs on disk."""
        if not self._model:
            return

        rows = sorted([ix.row() for ix in self.table.selectionModel().selectedRows()], reverse=True)
        if not rows:
            QMessageBox.information(self, "Delete", "Please select one or more rows to delete.")
            return

        df_view = self._model.dataframe()
        ids = [str(df_view.loc[r, "sample_id"]) for r in rows]

        # Gather CSV files to delete (labels_csv column + canonical data/labels/{sample_id}.csv)
        files_to_delete = []
        if "labels_csv" in df_view.columns:
            for r in rows:
                p = self._safe_path_from_value(df_view.loc[r, "labels_csv"])
                if p:
                    files_to_delete.append(p)

        for sid in ids:
            files_to_delete.append((LABELS_DIR / f"{sid}.csv"))

        # Deduplicate and keep only existing files
        files_to_delete = [Path(s) for s in dict.fromkeys(map(str, files_to_delete))]
        existing = [p for p in files_to_delete if p.exists()]

        msg = (
            f"You are about to delete:\n"
            f"• {len(ids)} metadata row(s)\n"
            f"• {len(existing)} CSV file(s) on disk\n\n"
            "This cannot be undone. Continue?"
        )
        if QMessageBox.question(self, "Confirm Delete", msg, QMessageBox.Yes | QMessageBox.No) != QMessageBox.Yes:
            return

        # Delete files (ignore errors)
        for f in existing:
            try:
                f.unlink(missing_ok=True)
            except Exception:
                pass

        # Remove from META_CSV by sample_id and save
        if META_CSV.exists():
            try:
                df_all = pd.read_csv(META_CSV, dtype=str, encoding="utf-8")
            except Exception:
                df_all = pd.DataFrame()
        else:
            df_all = pd.DataFrame()

        if not df_all.empty and "sample_id" in df_all.columns:
            df_all = df_all[~df_all["sample_id"].astype(str).isin(ids)]
            df_all.to_csv(META_CSV, index=False, encoding="utf-8")

        # Refresh view (preserve current search)
        self._reload_all()
        self._do_search()
        QMessageBox.information(self, "Deleted", "Selected items were removed.")