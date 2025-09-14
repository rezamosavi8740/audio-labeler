from __future__ import annotations

from pathlib import Path
from typing import List, Tuple
import shutil
import pandas as pd

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QLineEdit, QPushButton,
    QFrame, QFileDialog, QMessageBox, QTableView
)

from code.ui.widgets.pandas_model import PandasModel

# Project paths
DATA_DIR = Path.cwd() / "data"
LABELS_DIR = DATA_DIR / "labels"
META_CSV = DATA_DIR / "samples_meta.csv"

META_COLUMNS = ["sample_id", "sample_name", "date", "time", "labels_csv", "created_at"]


class CsvReportsPage(QWidget):
    sig_go_home = Signal()

    def __init__(self) -> None:
        super().__init__()

        # --- Top bar ---
        top = QHBoxLayout()
        self.btn_back = QPushButton("← Home")
        self.btn_back.setProperty("class", "back")
        self.btn_back.clicked.connect(self.sig_go_home.emit)

        title = QPushButton("CSV Reports")
        title.setEnabled(False)
        title.setStyleSheet("QPushButton { "
                            "background: transparent; color: #e8ecf4; "
                            "font-weight: 800; font-size: 24px; border: none; }")

        top.addWidget(self.btn_back, 0, Qt.AlignLeft)
        top.addWidget(title, 0, Qt.AlignLeft)
        top.addStretch(1)

        # --- Tabs ---
        self.tabs = QTabWidget()
        # Local style hack to ensure no white strip even if global QSS is overridden
        self.tabs.setStyleSheet(
            "QTabWidget::pane{background:#1c1f26;border:0;margin:0;padding:0;}"
            "QWidget#qt_tabwidget_stackedwidget{background:#1c1f26;border:0;}"
        )

        # --- Tab: Metadata ---
        self.tab_meta = QWidget()
        self._build_meta_tab(self.tab_meta)

        # --- Tab: Label CSVs ---
        self.tab_labels = QWidget()
        self._build_labels_tab(self.tab_labels)

        self.tabs.addTab(self.tab_meta, "Metadata")
        self.tabs.addTab(self.tab_labels, "Label CSVs")

        # --- Root ---
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(12)
        root.addLayout(top)
        root.addWidget(self.tabs)

        # Data state
        self._meta_model: PandasModel | None = None
        self._labels_model: PandasModel | None = None

        self.open()  # initial load

    # ----------------- UI builders -----------------
    def _build_meta_tab(self, tab: QWidget) -> None:
        v = QVBoxLayout(tab)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(10)

        # Toolbar
        bar = QFrame()
        bar.setObjectName("toolCard")
        hb = QHBoxLayout(bar)
        hb.setContentsMargins(12, 10, 12, 10)
        hb.setSpacing(8)

        self.meta_search = QLineEdit()
        self.meta_search.setPlaceholderText("Search metadata by id or name…")
        self.meta_reload = QPushButton("↻ Reload")
        self.meta_reload.setProperty("variant", "soft")
        self.meta_export = QPushButton("⬇ Export Selected…")
        self.meta_export.setProperty("variant", "primary")

        hb.addWidget(self.meta_search, 1)
        hb.addWidget(self.meta_reload)
        hb.addWidget(self.meta_export)

        # Table
        self.meta_table = QTableView()
        self.meta_table.setSelectionBehavior(QTableView.SelectRows)
        self.meta_table.setSelectionMode(QTableView.ExtendedSelection)
        self.meta_table.horizontalHeader().setStretchLastSection(True)
        self.meta_table.verticalHeader().setDefaultSectionSize(32)

        v.addWidget(bar)
        v.addWidget(self.meta_table, 1)

        # Wire
        self.meta_reload.clicked.connect(self._load_meta)
        self.meta_export.clicked.connect(self._export_meta_selected)
        self.meta_search.returnPressed.connect(self._apply_meta_search)

    def _build_labels_tab(self, tab: QWidget) -> None:
        v = QVBoxLayout(tab)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(10)

        bar = QFrame()
        bar.setObjectName("toolCard")
        hb = QHBoxLayout(bar)
        hb.setContentsMargins(12, 10, 12, 10)
        hb.setSpacing(8)

        self.labels_search = QLineEdit()
        self.labels_search.setPlaceholderText("Search label CSVs by file name or sample_id…")
        self.labels_reload = QPushButton("↻ Reload")
        self.labels_reload.setProperty("variant", "soft")
        self.labels_export = QPushButton("⬇ Export Selected…")
        self.labels_export.setProperty("variant", "primary")

        hb.addWidget(self.labels_search, 1)
        hb.addWidget(self.labels_reload)
        hb.addWidget(self.labels_export)

        self.labels_table = QTableView()
        self.labels_table.setSelectionBehavior(QTableView.SelectRows)
        self.labels_table.setSelectionMode(QTableView.ExtendedSelection)
        self.labels_table.horizontalHeader().setStretchLastSection(True)
        self.labels_table.verticalHeader().setDefaultSectionSize(32)

        v.addWidget(bar)
        v.addWidget(self.labels_table, 1)

        # Wire
        self.labels_reload.clicked.connect(self._load_labels)
        self.labels_export.clicked.connect(self._export_labels_selected)
        self.labels_search.returnPressed.connect(self._apply_labels_search)

    # ----------------- Lifecycle -----------------
    def open(self) -> None:
        self._load_meta()
        self._load_labels()

    # ----------------- Loading -----------------
    def _load_meta(self) -> None:
        try:
            df = pd.read_csv(META_CSV, dtype=str, encoding="utf-8")
        except Exception:
            df = pd.DataFrame(columns=META_COLUMNS)

        for c in META_COLUMNS:
            if c not in df.columns:
                df[c] = ""
        df = df[META_COLUMNS]

        self._meta_model = PandasModel(df)
        self.meta_table.setModel(self._meta_model)
        self.meta_table.resizeColumnsToContents()

    def _load_labels(self) -> None:
        # Build a list of label CSVs from LABELS_DIR
        rows: List[dict] = []
        LABELS_DIR.mkdir(parents=True, exist_ok=True)
        for p in sorted(LABELS_DIR.glob("*.csv")):
            sid = p.stem  # sample_id
            rows.append({"sample_id": sid, "csv_path": str(p), "file_name": p.name})

        df = pd.DataFrame(rows, columns=["sample_id", "file_name", "csv_path"])
        self._labels_model = PandasModel(df)
        self.labels_table.setModel(self._labels_model)
        self.labels_table.resizeColumnsToContents()

    # ----------------- Search -----------------
    def _apply_meta_search(self) -> None:
        if not self._meta_model:
            return
        q = (self.meta_search.text() or "").strip().lower()
        df = self._meta_model.dataframe()
        if not q:
            self._load_meta(); return
        mask = df["sample_id"].astype(str).str.lower().str.contains(q) | \
               df["sample_name"].astype(str).str.lower().str.contains(q)
        self._meta_model = PandasModel(df[mask].copy())
        self.meta_table.setModel(self._meta_model)
        self.meta_table.resizeColumnsToContents()

    def _apply_labels_search(self) -> None:
        if not self._labels_model:
            return
        q = (self.labels_search.text() or "").strip().lower()
        df = self._labels_model.dataframe()
        if not q:
            self._load_labels(); return
        mask = df["sample_id"].astype(str).str.lower().str.contains(q) | \
               df["file_name"].astype(str).str.lower().str.contains(q)
        self._labels_model = PandasModel(df[mask].copy())
        self.labels_table.setModel(self._labels_model)
        self.labels_table.resizeColumnsToContents()

    # ----------------- Export helpers -----------------
    def _ask_dir(self, title: str) -> Path | None:
        dst = QFileDialog.getExistingDirectory(self, title, str(Path.cwd()))
        return Path(dst) if dst else None

    def _ensure_dir(self, p: Path) -> None:
        p.mkdir(parents=True, exist_ok=True)

    # ----------------- Export actions -----------------
    def _export_meta_selected(self) -> None:
        if not self._meta_model:
            return
        sel = self.meta_table.selectionModel().selectedRows()
        if not sel:
            QMessageBox.information(self, "Export", "Select at least one metadata row.")
            return

        out_root = self._ask_dir("Choose export directory")
        if not out_root:
            return

        # Prepare folders
        meta_out = out_root / "metadata"
        labels_out = out_root / "label_csvs"
        self._ensure_dir(meta_out)
        self._ensure_dir(labels_out)

        df_view = self._meta_model.dataframe().copy()
        picked = df_view.iloc[[ix.row() for ix in sel]].copy()

        # Save picked metadata as index.csv inside metadata folder
        picked.to_csv(meta_out / "index.csv", index=False, encoding="utf-8")

        # Copy each row's labels_csv (if present)
        copied: List[Tuple[str, str]] = []
        for _, row in picked.iterrows():
            p = str(row.get("labels_csv", "") or "").strip()
            if not p:
                continue
            src = Path(p)
            if src.exists() and src.suffix.lower() == ".csv":
                dst = labels_out / src.name
                shutil.copy2(src, dst)
                copied.append((row.get("sample_id", ""), str(dst)))

        # Write a simple mapping file for convenience
        if copied:
            pd.DataFrame(copied, columns=["sample_id", "csv_path"]).to_csv(
                out_root / "labels_index.csv", index=False, encoding="utf-8"
            )

        QMessageBox.information(self, "Export", f"Exported to:\n{out_root}")

    def _export_labels_selected(self) -> None:
        """Export selected label CSVs and the corresponding metadata, mirroring metadata tab layout."""
        if not self._labels_model:
            return
        sel = self.labels_table.selectionModel().selectedRows()
        if not sel:
            QMessageBox.information(self, "Export", "Select at least one label CSV.")
            return

        out_root = self._ask_dir("Choose export directory")
        if not out_root:
            return

        # Prepare folders just like metadata export
        meta_out = out_root / "metadata"
        labels_out = out_root / "label_csvs"
        self._ensure_dir(meta_out)
        self._ensure_dir(labels_out)

        df_view = self._labels_model.dataframe()
        picked = df_view.iloc[[ix.row() for ix in sel]].copy()

        # 1) Copy selected label CSVs
        copies = []
        picked_sample_ids = set()
        picked_csv_paths = set()

        for _, row in picked.iterrows():
            sid = str(row.get("sample_id", "") or "").strip()
            p = str(row.get("csv_path", "") or "").strip()
            if not p:
                continue
            src = Path(p)
            if src.exists() and src.suffix.lower() == ".csv":
                dst = labels_out / src.name
                shutil.copy2(src, dst)
                copies.append((sid, str(dst)))
                if sid:
                    picked_sample_ids.add(sid)
                picked_csv_paths.add(str(src))

        # Write labels_index.csv (like metadata export does)
        if copies:
            pd.DataFrame(copies, columns=["sample_id", "csv_path"]).to_csv(
                out_root / "labels_index.csv", index=False, encoding="utf-8"
            )

        # 2) Export corresponding metadata into metadata/index.csv
        #    Match by sample_id OR by labels_csv path.
        try:
            meta_df = pd.read_csv(META_CSV, dtype=str, encoding="utf-8")
        except Exception:
            meta_df = pd.DataFrame(columns=META_COLUMNS)

        for c in META_COLUMNS:
            if c not in meta_df.columns:
                meta_df[c] = ""

        mask_sid = meta_df["sample_id"].astype(str).isin(picked_sample_ids) if "sample_id" in meta_df.columns else False
        mask_path = meta_df["labels_csv"].astype(str).isin(
            picked_csv_paths) if "labels_csv" in meta_df.columns else False
        meta_picked = meta_df[mask_sid | mask_path].copy()

        # Save metadata subset (even if empty we still create an index.csv for consistency)
        meta_picked.to_csv(meta_out / "index.csv", index=False, encoding="utf-8")

        QMessageBox.information(self, "Export", f"Exported:\n- {labels_out}\n- {meta_out}")