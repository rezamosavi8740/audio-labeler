# code/ui/pages/edit_hub.py
# Edit hub: pick a sample and choose to edit metadata or labels.

from pathlib import Path
import pandas as pd

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QFrame,
    QTableView, QLineEdit, QMessageBox
)

from code.ui.widgets.pandas_model import PandasModel

DATA_DIR = Path.cwd() / "data"
META_CSV = DATA_DIR / "samples_meta.csv"


class EditHubPage(QWidget):
    """List samples and route to Metadata Editor or Label Editor for the selected sample."""
    sig_go_home = Signal()
    sig_edit_metadata = Signal(str)  # sample_id
    sig_edit_labels = Signal(str)    # sample_id

    def __init__(self):
        super().__init__()

        # Top bar
        top = QHBoxLayout()
        self.btn_back = QPushButton("← Home")
        self.btn_back.setProperty("class", "back")
        self.btn_back.clicked.connect(lambda: self.sig_go_home.emit())

        self.title = QLabel("Edit — Pick a Sample")
        self.title.setProperty("class", "h1")

        top.addWidget(self.btn_back, alignment=Qt.AlignLeft)
        top.addWidget(self.title, alignment=Qt.AlignLeft)
        top.addStretch()

        # Toolbar
        tool = QFrame(); tool.setObjectName("toolCard")
        tl = QHBoxLayout(tool); tl.setContentsMargins(12, 10, 12, 10); tl.setSpacing(8)

        self.search = QLineEdit(); self.search.setPlaceholderText("Search by id or name…")
        self.btn_reload = QPushButton("↻ Reload"); self.btn_reload.setProperty("variant", "soft")
        self.btn_meta   = QPushButton("✏️ Edit Metadata"); self.btn_meta.setProperty("variant", "primary")
        self.btn_labels = QPushButton("🎧 Edit Labels");   self.btn_labels.setProperty("variant", "accent")

        for w in (self.btn_reload, self.btn_meta, self.btn_labels):
            w.setMinimumHeight(32)

        tl.addWidget(self.search, 1)
        tl.addStretch()
        tl.addWidget(self.btn_reload)
        tl.addWidget(self.btn_meta)
        tl.addWidget(self.btn_labels)

        # Table
        self.table = QTableView()
        self.table.setSelectionBehavior(QTableView.SelectRows)
        self.table.setSelectionMode(QTableView.SingleSelection)
        self.table.horizontalHeader().setStretchLastSection(True)

        # Root
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(12)
        root.addLayout(top)
        root.addWidget(tool)
        root.addWidget(self.table)

        # State
        self._model: PandasModel | None = None
        self._df: pd.DataFrame | None = None

        # Signals
        self.btn_reload.clicked.connect(self.reload)
        self.search.textChanged.connect(self._apply_filter)
        self.btn_meta.clicked.connect(self._go_meta)
        self.btn_labels.clicked.connect(self._go_labels)

    # --- API ---
    def open(self):
        self.reload()

    # --- Data helpers ---
    def reload(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        if not META_CSV.exists():
            pd.DataFrame(columns=[
                "sample_id","date","time","temperature_c","pressure_kpa",
                "latitude","longitude","count","sample_name","labels_csv","created_at"
            ]).to_csv(META_CSV, index=False, encoding="utf-8")

        try:
            df = pd.read_csv(META_CSV, dtype=str, encoding="utf-8")
        except Exception as e:
            QMessageBox.critical(self, "Load error", str(e))
            df = pd.DataFrame()

        # keep useful columns first
        cols = [c for c in ["sample_id","sample_name","date","time","labels_csv","created_at"] if c in df.columns]
        df = df[cols] if cols else df
        self._df = df.fillna("")

        self._model = PandasModel(self._df.copy())
        self.table.setModel(self._model)
        self.table.resizeColumnsToContents()

    def _apply_filter(self, text: str):
        if self._df is None or self._model is None:
            return
        t = (text or "").strip().lower()
        if not t:
            self._model.set_dataframe(self._df.copy())
            return
        mask = False
        for col in self._df.columns:
            mask = mask | self._df[col].str.lower().str.contains(t, na=False)
        self._model.set_dataframe(self._df[mask].copy())

    def _selected_sample_id(self) -> str | None:
        sm = self.table.selectionModel()
        if not sm: return None
        rows = sm.selectedRows()
        if not rows: return None
        r = rows[0].row()
        df = self._model.dataframe()
        if "sample_id" not in df.columns: return None
        return str(df.iloc[r]["sample_id"])

    # --- Routes ---
    def _go_meta(self):
        sid = self._selected_sample_id()
        if not sid:
            QMessageBox.information(self, "Pick a row", "Please select a sample first.")
            return
        self.sig_edit_metadata.emit(sid)

    def _go_labels(self):
        sid = self._selected_sample_id()
        if not sid:
            QMessageBox.information(self, "Pick a row", "Please select a sample first.")
            return
        self.sig_edit_labels.emit(sid)