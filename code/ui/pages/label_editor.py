from pathlib import Path
from datetime import datetime
import pandas as pd

from PySide6.QtCore import Qt, Signal, QUrl, QPoint
from PySide6.QtWidgets import (
    QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QFileDialog,
    QTableView, QMessageBox, QFrame, QLineEdit, QComboBox, QSlider, QStyledItemDelegate
)
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput

from code.ui.widgets.pandas_model import PandasModel

# Data directories
DATA_DIR = Path.cwd() / "data"
LABELS_DIR = DATA_DIR / "labels"
META_CSV = DATA_DIR / "samples_meta.csv"
SAMPLE_LIST_CSV = DATA_DIR / "sample_list.csv"  # must have a column 'type'

# Labels CSV columns
LABEL_COLUMNS = [
    "sample_id", "audio_path", "start_s", "end_s",
    "label_class", "notes", "created_at",
]


class SeekSlider(QSlider):
    """Horizontal slider with click-to-seek and smooth dragging."""
    def __init__(self, orientation=Qt.Horizontal, parent=None):
        super().__init__(orientation, parent)
        self.setRange(0, 0)
        self.setSingleStep(1000)
        self.setPageStep(5000)

    def _value_from_event(self, ev_pos: QPoint) -> int:
        x = max(0, min(ev_pos.x(), self.width()))
        ratio = x / max(1, self.width())
        return int(self.minimum() + ratio * (self.maximum() - self.minimum()))

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton and self.maximum() > self.minimum():
            self.setValue(self._value_from_event(e.position().toPoint()))
            self.sliderPressed.emit()
            self.sliderMoved.emit(self.value())
            self.sliderReleased.emit()
        super().mousePressEvent(e)

    def mouseMoveEvent(self, e):
        if e.buttons() & Qt.LeftButton and self.maximum() > self.minimum():
            self.setValue(self._value_from_event(e.position().toPoint()))
            self.sliderMoved.emit(self.value())
        super().mouseMoveEvent(e)


class ComboBoxDelegate(QStyledItemDelegate):
    """Delegate that forces a QComboBox editor with fixed options."""
    def __init__(self, options: list[str], parent=None):
        super().__init__(parent)
        self._options = options

    def createEditor(self, parent, option, index):
        cb = QComboBox(parent)
        cb.addItems(self._options)
        return cb

    def setEditorData(self, editor, index):
        val = str(index.data() or "")
        i = editor.findText(val)
        if i >= 0:
            editor.setCurrentIndex(i)

    def setModelData(self, editor, model, index):
        model.setData(index, editor.currentText(), Qt.EditRole)


class LabelEditorPage(QWidget):
    sig_go_home = Signal()

    def __init__(self):
        super().__init__()

        # --- Top bar ---
        top = QHBoxLayout()
        self.btn_back = QPushButton("← Home")
        self.btn_back.setProperty("class", "back")
        self.btn_back.clicked.connect(lambda: self.sig_go_home.emit())

        self.title = QLabel("New Sample — Step 2 (Attach & Label)")
        self.title.setProperty("class", "h1")
        top.addWidget(self.btn_back, alignment=Qt.AlignLeft)
        top.addWidget(self.title, alignment=Qt.AlignLeft)
        top.addStretch()

        # --- Toolbar (card) ---
        tool_card = QFrame()
        tool_card.setObjectName("toolCard")
        tool_wrap = QVBoxLayout(tool_card)
        tool_wrap.setContentsMargins(12, 10, 12, 10)
        tool_wrap.setSpacing(8)

        # Row 1: compact controls
        row1 = QHBoxLayout()
        row1.setSpacing(8)

        self.btn_attach = QPushButton("📎 Attach WAV…"); self.btn_attach.setProperty("variant", "accent")
        self.btn_play   = QPushButton("▶ Play");         self.btn_play.setProperty("variant", "primary")
        self.btn_pause  = QPushButton("⏸ Pause");        self.btn_pause.setProperty("variant", "soft")
        self.btn_stop   = QPushButton("⏹ Stop");         self.btn_stop.setProperty("variant", "soft")

        self.btn_mark_start = QPushButton("⟲ Mark Start"); self.btn_mark_start.setProperty("variant", "success")
        self.btn_mark_end   = QPushButton("⟶ Mark End");   self.btn_mark_end.setProperty("variant", "warn")

        self.class_combo = QComboBox(); self.class_combo.setEditable(False); self.class_combo.setMinimumWidth(120)

        self.btn_add_row = QPushButton("➕ Add Row");  self.btn_add_row.setProperty("variant", "success")
        self.btn_delete  = QPushButton("🗑 Delete");   self.btn_delete.setProperty("variant", "danger")
        self.btn_save    = QPushButton("💾 Save");     self.btn_save.setProperty("variant", "primary")
        self.btn_reload  = QPushButton("↻ Reload");    self.btn_reload.setProperty("variant", "soft")

        for w in (self.btn_attach, self.btn_play, self.btn_pause, self.btn_stop,
                  self.btn_mark_start, self.btn_mark_end, self.btn_add_row,
                  self.btn_delete, self.btn_save, self.btn_reload, self.class_combo):
            w.setMinimumHeight(32)

        row1.addWidget(self.btn_attach)
        row1.addWidget(self.btn_play)
        row1.addWidget(self.btn_pause)
        row1.addWidget(self.btn_stop)
        row1.addSpacing(6)
        row1.addWidget(self.btn_mark_start)
        row1.addWidget(self.btn_mark_end)
        row1.addWidget(QLabel("Class:"))
        row1.addWidget(self.class_combo)
        row1.addWidget(self.btn_add_row)
        row1.addWidget(self.btn_delete)
        row1.addStretch()
        row1.addWidget(self.btn_save)
        row1.addWidget(self.btn_reload)

        # Row 2: timeline
        row2 = QHBoxLayout()
        row2.setSpacing(10)
        self.slider = SeekSlider(Qt.Horizontal)
        self.lbl_time = QLabel("00:00 / 00:00"); self.lbl_time.setStyleSheet("color:#bbb;")
        row2.addWidget(self.slider, 1)
        row2.addWidget(self.lbl_time)

        tool_wrap.addLayout(row1)
        tool_wrap.addLayout(row2)

        # --- Pos & marks ---
        pos_card = QFrame(); pos_card.setObjectName("toolCard")
        pos_layout = QHBoxLayout(pos_card); pos_layout.setContentsMargins(12, 8, 12, 8); pos_layout.setSpacing(10)
        self.line_pos   = QLineEdit("0.000"); self.line_pos.setReadOnly(True)
        self.line_start = QLineEdit(""); self.line_start.setPlaceholderText("start_s"); self.line_start.setReadOnly(True)
        self.line_end   = QLineEdit(""); self.line_end.setPlaceholderText("end_s");   self.line_end.setReadOnly(True)
        for l in (self.line_pos, self.line_start, self.line_end): l.setMinimumWidth(90)
        pos_layout.addWidget(QLabel("Pos (s):"));  pos_layout.addWidget(self.line_pos)
        pos_layout.addSpacing(10)
        pos_layout.addWidget(QLabel("Start:"));    pos_layout.addWidget(self.line_start, 1)
        pos_layout.addWidget(QLabel("End:"));      pos_layout.addWidget(self.line_end, 1)
        pos_layout.addStretch()

        # --- Table ---
        self.table = QTableView()
        self.table.setSelectionBehavior(QTableView.SelectRows)
        self.table.setSelectionMode(QTableView.ExtendedSelection)
        self.table.horizontalHeader().setStretchLastSection(True)

        # --- Root ---
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(12)
        root.addLayout(top)
        root.addWidget(tool_card)
        root.addWidget(pos_card)
        root.addWidget(self.table)

        # --- Player ---
        self.player = QMediaPlayer(self)
        self.audio_out = QAudioOutput(self)
        self.player.setAudioOutput(self.audio_out)
        self.audio_out.setVolume(0.9)

        self.player.positionChanged.connect(self._on_position_changed)
        self.player.durationChanged.connect(self._on_duration_changed)
        self.slider.sliderMoved.connect(self._seek_live)
        self.slider.sliderReleased.connect(self._seek_release)

        # Buttons
        self.btn_attach.clicked.connect(self._attach_audio)
        self.btn_play.clicked.connect(self.player.play)
        self.btn_pause.clicked.connect(self.player.pause)
        self.btn_stop.clicked.connect(self.player.stop)
        self.btn_mark_start.clicked.connect(self._mark_start)
        self.btn_mark_end.clicked.connect(self._mark_end)
        self.btn_add_row.clicked.connect(self._add_row_from_marks)
        self.btn_delete.clicked.connect(self._delete_rows)
        self.btn_save.clicked.connect(self._save_labels)
        self.btn_reload.clicked.connect(self._reload_labels)

        # State
        self.sample_id: str | None = None
        self.labels_csv_path: Path | None = None
        self.audio_path: Path | None = None
        self.model: PandasModel | None = None
        self._class_options: list[str] = [""]

    # ---------- Public API ----------
    def open_for(self, sample_id: str):
        self.sample_id = sample_id
        LABELS_DIR.mkdir(parents=True, exist_ok=True)
        self.labels_csv_path = LABELS_DIR / f"{sample_id}.csv"
        if not self.labels_csv_path.exists():
            pd.DataFrame(columns=LABEL_COLUMNS).to_csv(self.labels_csv_path, index=False, encoding="utf-8")
            self._sync_meta_link()
        self._reload_labels()
        self._load_classes()
        self._apply_class_delegate()
        self.title.setText(f"New Sample — Step 2 (Attach & Label) • {sample_id}")

    # ---------- Audio ----------
    def _attach_audio(self):
        path, _ = QFileDialog.getOpenFileName(self, "Attach WAV", str(Path.cwd()), "WAV Audio (*.wav)")
        if not path: return
        self.audio_path = Path(path)
        self.player.setSource(QUrl.fromLocalFile(str(self.audio_path)))
        self.player.play()

    def _on_position_changed(self, ms: int):
        self.line_pos.setText(f"{ms/1000.0:.3f}")
        if not self.slider.isSliderDown(): self.slider.setValue(ms)
        self._update_time_label(ms, self.player.duration())

    def _on_duration_changed(self, ms: int):
        self.slider.setRange(0, ms)
        self._update_time_label(self.player.position(), ms)

    def _seek_live(self, ms: int):
        self.player.setPosition(ms)

    def _seek_release(self):
        self.player.setPosition(self.slider.value())

    def _update_time_label(self, pos_ms: int, dur_ms: int):
        def fmt(ms): s = int(ms/1000); return f"{s//60:02d}:{s%60:02d}"
        self.lbl_time.setText(f"{fmt(pos_ms)} / {fmt(dur_ms)}")

    # ---------- Marks ----------
    def _mark_start(self):
        self.line_start.setText(self.line_pos.text())

    def _mark_end(self):
        self.line_end.setText(self.line_pos.text())

    def _add_row_from_marks(self):
        if not self.model or not self.sample_id: return
        start_text, end_text = self.line_start.text(), self.line_end.text()
        if not start_text or not end_text:
            QMessageBox.warning(self, "Missing marks", "Please mark Start and End first.")
            return
        try:
            s, e = float(start_text), float(end_text)
            if e < s: s, e = e, s
        except Exception:
            QMessageBox.warning(self, "Invalid marks", "Start/End must be numbers.")
            return
        cls = self.class_combo.currentText().strip()
        row = {
            "sample_id": self.sample_id,
            "audio_path": str(self.audio_path or ""),
            "start_s": f"{s:.3f}", "end_s": f"{e:.3f}",
            "label_class": cls, "notes": "",
            "created_at": datetime.now().isoformat(timespec="seconds"),
        }
        self.model.insert_empty_row(row)
        self.line_start.clear(); self.line_end.clear()

    def _delete_rows(self):
        if not self.model: return
        sel = self.table.selectionModel().selectedRows()
        if not sel: return
        self.model.remove_rows([ix.row() for ix in sel])

    # ---------- CSV I/O ----------
    def _reload_labels(self):
        if not self.labels_csv_path: return
        try:
            df = pd.read_csv(self.labels_csv_path, dtype=str, encoding="utf-8")
        except Exception:
            df = pd.DataFrame(columns=LABEL_COLUMNS)
        for col in LABEL_COLUMNS:
            if col not in df.columns: df[col] = ""
        df = df[LABEL_COLUMNS]
        self.model = PandasModel(df)
        self.table.setModel(self.model)
        self.table.resizeColumnsToContents()
        self._apply_class_delegate()  # ensure delegate after reload

    def _save_labels(self):
        if not self.model or not self.labels_csv_path: return
        df = self.model.dataframe().copy()
        for col in ("start_s", "end_s"):
            df[col] = pd.to_numeric(df[col], errors="coerce").round(3).astype(str)
        try:
            df.to_csv(self.labels_csv_path, index=False, encoding="utf-8")
            self._sync_meta_link()
            QMessageBox.information(self, "Saved", f"Saved labels:\n{self.labels_csv_path}")
        except Exception as e:
            QMessageBox.critical(self, "Save error", str(e))

    # ---------- Metadata linking ----------
    def _sync_meta_link(self):
        if not self.sample_id or not self.labels_csv_path: return
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        if not META_CSV.exists():
            pd.DataFrame(columns=["sample_id", "labels_csv"]).to_csv(META_CSV, index=False, encoding="utf-8")
            return
        try:
            df = pd.read_csv(META_CSV, dtype=str, encoding="utf-8")
        except Exception:
            return
        if "labels_csv" not in df.columns:
            df["labels_csv"] = ""
        mask = df["sample_id"].astype(str) == str(self.sample_id)
        if mask.any():
            df.loc[mask, "labels_csv"] = str(self.labels_csv_path)
            df.to_csv(META_CSV, index=False, encoding="utf-8")

    # ---------- Classes ----------
    def _load_classes(self):
        # Read distinct values from column 'type' in sample_list.csv
        self._class_options = [""]
        if SAMPLE_LIST_CSV.exists():
            try:
                df = pd.read_csv(SAMPLE_LIST_CSV)
                # robust: accept any case/spaces for 'type'
                col = None
                for c in df.columns:
                    if c.strip().lower() == "type":
                        col = c
                        break
                if col:
                    opts = [str(x) for x in df[col].dropna().unique().tolist()]
                    opts.sort()
                    self._class_options = [""] + opts
            except Exception as e:
                print("[WARN] Could not load sample_list.csv:", e)

        self.class_combo.blockSignals(True)
        self.class_combo.clear()
        self.class_combo.addItems(self._class_options)
        self.class_combo.blockSignals(False)

    def _apply_class_delegate(self):
        # Install delegate so 'label_class' column is combo-only (no free text)
        if not self.model: return
        try:
            col_idx = list(self.model.dataframe().columns).index("label_class")
        except ValueError:
            return
        self.table.setItemDelegateForColumn(col_idx, ComboBoxDelegate(self._class_options, self.table))