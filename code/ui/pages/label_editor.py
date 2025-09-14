# code/ui/pages/label_editor.py
# Dark-mode Label Editor with waveform + spectrogram, CSV table,
# play/pause with spacebar, and sample classes loaded from sample_list.csv.

from pathlib import Path
from datetime import datetime

import numpy as np
import pandas as pd
import pyqtgraph as pg
import soundfile as sf
from scipy.signal import spectrogram

from PySide6.QtCore import Qt, Signal, QUrl
from PySide6.QtGui import QShortcut, QKeySequence
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSlider,
    QSplitter,
    QStyledItemDelegate,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from code.ui.widgets.pandas_model import PandasModel


# --- project dirs ---
DATA_DIR = Path.cwd() / "data"
LABELS_DIR = DATA_DIR / "labels"
META_CSV = DATA_DIR / "samples_meta.csv"
SAMPLE_LIST_CSV = DATA_DIR / "sample_list.csv"

LABEL_COLUMNS = ["sample_id", "audio_path", "start_s", "end_s", "label_class", "notes", "created_at"]


# ---------- UI helpers ----------
class SeekSlider(QSlider):
    """Horizontal slider with click-to-seek and dragging."""
    def __init__(self, orientation=Qt.Horizontal, parent=None):
        super().__init__(orientation, parent)
        self.setRange(0, 0)
        self.setSingleStep(1000)
        self.setPageStep(5000)

    def _value_from_event(self, pos) -> int:
        x = max(0, min(int(pos.x()), self.width()))
        ratio = x / max(1, self.width())
        return int(self.minimum() + ratio * (self.maximum() - self.minimum()))

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton and self.maximum() > self.minimum():
            self.setValue(self._value_from_event(e.position()))
            self.sliderPressed.emit()
            self.sliderMoved.emit(self.value())
            self.sliderReleased.emit()
        super().mousePressEvent(e)

    def mouseMoveEvent(self, e):
        if e.buttons() & Qt.LeftButton and self.maximum() > self.minimum():
            self.setValue(self._value_from_event(e.position()))
            self.sliderMoved.emit(self.value())
        super().mouseMoveEvent(e)


class ComboBoxDelegate(QStyledItemDelegate):
    """Forces combobox editor with options loaded from sample_list.csv."""
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


# ---------- Main page ----------
class LabelEditorPage(QWidget):
    sig_go_home = Signal()

    def __init__(self):
        super().__init__()

        # ---- top bar ----
        top = QHBoxLayout()
        self.btn_back = QPushButton("← Home")
        self.btn_back.setProperty("class", "back")
        self.btn_back.clicked.connect(lambda: self.sig_go_home.emit())
        self.title = QLabel("Label Editor — Step 2")
        self.title.setProperty("class", "h1")
        top.addWidget(self.btn_back, alignment=Qt.AlignLeft)
        top.addWidget(self.title, alignment=Qt.AlignLeft)
        top.addStretch()

        # ---- toolbar ----
        tool_card = QFrame()
        tool_card.setObjectName("toolCard")
        tool = QHBoxLayout(tool_card)
        tool.setContentsMargins(12, 10, 12, 10)
        tool.setSpacing(8)

        self.btn_attach = QPushButton("📎 Attach WAV…")
        self.btn_attach.setProperty("variant", "accent")
        self.btn_play = QPushButton("▶ Play")
        self.btn_play.setProperty("variant", "primary")
        self.btn_pause = QPushButton("⏸ Pause")
        self.btn_pause.setProperty("variant", "soft")
        self.btn_stop = QPushButton("⏹ Stop")
        self.btn_stop.setProperty("variant", "soft")

        self.btn_mark_start = QPushButton("⟲ Mark Start")
        self.btn_mark_start.setProperty("variant", "success")
        self.btn_mark_end = QPushButton("⟶ Mark End")
        self.btn_mark_end.setProperty("variant", "warn")

        self.class_combo = QComboBox()
        self.class_combo.setMinimumWidth(140)

        self.btn_add_row = QPushButton("➕ Add Row")
        self.btn_add_row.setProperty("variant", "success")
        self.btn_delete = QPushButton("🗑 Delete")
        self.btn_delete.setProperty("variant", "danger")
        self.btn_save = QPushButton("💾 Save")
        self.btn_save.setProperty("variant", "primary")
        self.btn_reload = QPushButton("↻ Reload")
        self.btn_reload.setProperty("variant", "soft")
        self.btn_toggle_visuals = QPushButton("▾ Toggle Visuals")
        self.btn_toggle_visuals.setProperty("variant", "soft")

        for w in (
            self.btn_attach,
            self.btn_play,
            self.btn_pause,
            self.btn_stop,
            self.btn_mark_start,
            self.btn_mark_end,
            self.class_combo,
            self.btn_add_row,
            self.btn_delete,
            self.btn_save,
            self.btn_reload,
            self.btn_toggle_visuals,
        ):
            w.setMinimumHeight(32)

        tool.addWidget(self.btn_attach)
        tool.addWidget(self.btn_play)
        tool.addWidget(self.btn_pause)
        tool.addWidget(self.btn_stop)
        tool.addSpacing(6)
        tool.addWidget(self.btn_mark_start)
        tool.addWidget(self.btn_mark_end)
        tool.addWidget(QLabel("Class:"))
        tool.addWidget(self.class_combo)
        tool.addWidget(self.btn_add_row)
        tool.addWidget(self.btn_delete)
        tool.addStretch()
        tool.addWidget(self.btn_save)
        tool.addWidget(self.btn_reload)
        tool.addWidget(self.btn_toggle_visuals)

        # ---- timeline ----
        tl_card = QFrame()
        tl_card.setObjectName("toolCard")
        tl = QHBoxLayout(tl_card)
        tl.setContentsMargins(12, 10, 12, 10)
        tl.setSpacing(10)
        self.slider = SeekSlider(Qt.Horizontal)
        self.lbl_time = QLabel("00:00 / 00:00")
        self.lbl_time.setStyleSheet("color:#a6adc8;")
        tl.addWidget(self.slider, 1)
        tl.addWidget(self.lbl_time)

        # ---- visuals ----
        wf_card = QFrame()
        wf_card.setObjectName("toolCard")
        wf = QVBoxLayout(wf_card)
        wf.setContentsMargins(12, 10, 12, 10)
        wf.setSpacing(8)

        cap = QLabel("Waveform / Spectrogram")
        cap.setProperty("class", "subtle")
        wf.addWidget(cap)

        self.pg_wave = pg.PlotWidget()
        self.pg_wave.setBackground("#12141a")
        self.pg_wave.showGrid(x=True, y=True, alpha=0.2)
        self.pg_wave.setMouseEnabled(x=True, y=False)
        self.pg_wave.setLabel("bottom", "Time", units="s", **{"color": "#cfd3e0"})
        self.pg_wave.setLabel("left", "Amplitude", **{"color": "#cfd3e0"})
        self.pg_wave.setMinimumHeight(110)

        self.pg_spec = pg.PlotWidget()
        self.pg_spec.setBackground("#12141a")
        self.pg_spec.setLabel("bottom", "Time", units="s", **{"color": "#cfd3e0"})
        self.pg_spec.setLabel("left", "Frequency", units="Hz", **{"color": "#cfd3e0"})
        self.pg_spec.setMinimumHeight(140)
        self._img_spec = pg.ImageItem()
        self.pg_spec.addItem(self._img_spec)

        wf.addWidget(self.pg_wave)
        wf.addWidget(self.pg_spec)

        # ---- marks row ----
        marks_card = QFrame()
        marks_card.setObjectName("toolCard")
        marks = QHBoxLayout(marks_card)
        marks.setContentsMargins(12, 10, 12, 10)
        marks.setSpacing(8)

        self.line_pos = QLineEdit("0.000")
        self.line_pos.setReadOnly(True)
        self.line_start = QLineEdit("")
        self.line_start.setPlaceholderText("start_s")
        self.line_start.setReadOnly(True)
        self.line_end = QLineEdit("")
        self.line_end.setPlaceholderText("end_s")
        self.line_end.setReadOnly(True)
        for l in (self.line_pos, self.line_start, self.line_end):
            l.setMinimumWidth(100)

        marks.addWidget(QLabel("Pos (s):"))
        marks.addWidget(self.line_pos, 0)
        marks.addSpacing(8)
        marks.addWidget(QLabel("Start:"))
        marks.addWidget(self.line_start, 1)
        marks.addWidget(QLabel("End:"))
        marks.addWidget(self.line_end, 1)
        marks.addStretch()

        # ---- labels table ----
        self.table = QTableView()
        self.table.setSelectionBehavior(QTableView.SelectRows)
        self.table.setSelectionMode(QTableView.ExtendedSelection)
        theader = self.table.horizontalHeader()
        theader.setStretchLastSection(True)
        self.table.verticalHeader().setDefaultSectionSize(32)

        # ---- splitter ----
        self.splitter = QSplitter(Qt.Vertical)
        self.splitter.addWidget(wf_card)
        self.splitter.addWidget(marks_card)
        self.splitter.addWidget(self.table)
        self.splitter.setSizes([220, 70, 700])

        # ---- root ----
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(12)
        root.addLayout(top)
        root.addWidget(tool_card)
        root.addWidget(tl_card)
        root.addWidget(self.splitter)

        # ---- player ----
        self.player = QMediaPlayer(self)
        self.audio_out = QAudioOutput(self)
        self.player.setAudioOutput(self.audio_out)
        self.audio_out.setVolume(0.9)

        self.player.positionChanged.connect(self._on_position_changed)
        self.player.durationChanged.connect(self._on_duration_changed)
        self.slider.sliderMoved.connect(self._seek_live)
        self.slider.sliderReleased.connect(self._seek_release)

        # buttons wiring
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
        self.btn_toggle_visuals.clicked.connect(self._toggle_visuals)

        # spacebar toggle
        self._space_shortcut = QShortcut(QKeySequence(Qt.Key_Space), self)
        self._space_shortcut.setContext(Qt.ApplicationShortcut)
        self._space_shortcut.activated.connect(self._toggle_play_pause)

        # state
        self.sample_id: str | None = None
        self.labels_csv_path: Path | None = None
        self.audio_path: Path | None = None
        self.model: PandasModel | None = None
        self._class_options: list[str] = [""]

        self._wav_data: np.ndarray | None = None
        self._wav_sr: int | None = None

        self._playhead_wave = pg.InfiniteLine(pos=0, angle=90, movable=False, pen=pg.mkPen("#2aa3ff", width=2))
        self.pg_wave.addItem(self._playhead_wave)
        self._playhead_spec = pg.InfiniteLine(pos=0, angle=90, movable=False, pen=pg.mkPen("#2aa3ff", width=2))
        self.pg_spec.addItem(self._playhead_spec)

        self.pg_wave.scene().sigMouseClicked.connect(self._on_wave_click)
        self.pg_spec.scene().sigMouseClicked.connect(self._on_spec_click)

    # ===== public API =====
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
        self.title.setText(f"Label Editor — Step 2 • {sample_id}")

    # ===== audio =====
    def _attach_audio(self):
        path, _ = QFileDialog.getOpenFileName(self, "Attach WAV", str(Path.cwd()), "WAV Audio (*.wav)")
        if not path:
            return
        self.audio_path = Path(path)
        self.player.setSource(QUrl.fromLocalFile(str(self.audio_path)))
        self.player.play()
        try:
            self._load_wav_array(self.audio_path)
            self._render_waveform()
            self._render_spectrogram()
        except Exception as e:
            QMessageBox.warning(self, "Audio", f"Could not render waveform/spectrogram:\n{e}")

    def _toggle_play_pause(self):
        state = self.player.playbackState()
        if state == QMediaPlayer.PlayingState:
            self.player.pause()
        else:
            if self.player.source().isEmpty():
                return
            self.player.play()

    def _load_wav_array(self, wav_path: Path):
        data, sr = sf.read(str(wav_path), always_2d=False)
        if data.ndim > 1:
            data = data.mean(axis=1)
        if data.dtype.kind in ("i", "u"):
            maxv = np.iinfo(data.dtype).max
            data = data.astype(np.float32) / maxv
        else:
            data = data.astype(np.float32)
        self._wav_data = data
        self._wav_sr = int(sr)

    def _render_waveform(self):
        if self._wav_data is None or self._wav_sr is None:
            return
        n = self._wav_data.shape[0]
        t = np.arange(n, dtype=np.float32) / float(self._wav_sr)
        self.pg_wave.clear()
        self.pg_wave.plot(t, self._wav_data, pen=pg.mkPen("#cdd5e4", width=1))
        self._playhead_wave = pg.InfiniteLine(pos=0, angle=90, movable=False, pen=pg.mkPen("#2aa3ff", width=2))
        self.pg_wave.addItem(self._playhead_wave)

    def _render_spectrogram(self):
        if self._wav_data is None or self._wav_sr is None:
            return
        nperseg, noverlap = 1024, 512
        f, t, Sxx = spectrogram(
            self._wav_data,
            fs=self._wav_sr,
            window="hann",
            nperseg=nperseg,
            noverlap=noverlap,
            detrend=False,
            mode="magnitude",
        )
        Sxx_db = 20 * np.log10(np.maximum(Sxx, 1e-10))
        self._img_spec.setImage(Sxx_db.T, autoLevels=True)
        dt = t[1] - t[0] if len(t) > 1 else 1.0
        df = f[1] - f[0] if len(f) > 1 else 1.0
        self._img_spec.resetTransform()
        self._img_spec.scale(dt, df)
        self._img_spec.setPos(0.0, 0.0)

        self.pg_spec.removeItem(self._playhead_spec)
        self._playhead_spec = pg.InfiniteLine(pos=0, angle=90, movable=False, pen=pg.mkPen("#2aa3ff", width=2))
        self.pg_spec.addItem(self._playhead_spec)

    # ===== player <-> UI sync =====
    def _on_position_changed(self, ms: int):
        self.line_pos.setText(f"{ms/1000.0:.3f}")
        if not self.slider.isSliderDown():
            self.slider.setValue(ms)
        self._update_time_label(ms, self.player.duration())
        sec = ms / 1000.0
        if self._playhead_wave:
            self._playhead_wave.setPos(sec)
        if self._playhead_spec:
            self._playhead_spec.setPos(sec)

    def _on_duration_changed(self, ms: int):
        self.slider.setRange(0, ms)
        self._update_time_label(self.player.position(), ms)

    def _seek_live(self, ms: int):
        self.player.setPosition(ms)

    def _seek_release(self):
        self.player.setPosition(self.slider.value())

    def _update_time_label(self, pos_ms: int, dur_ms: int):
        def fmt(m):
            s = int(m / 1000)
            return f"{s//60:02d}:{s%60:02d}"
        self.lbl_time.setText(f"{fmt(pos_ms)} / {fmt(dur_ms)}")

    def _on_wave_click(self, ev):
        if self._wav_sr is None:
            return
        vb = self.pg_wave.getPlotItem().vb
        sec = max(0.0, float(vb.mapSceneToView(ev.scenePos()).x()))
        self.player.setPosition(int(sec * 1000))

    def _on_spec_click(self, ev):
        if self._wav_sr is None:
            return
        vb = self.pg_spec.getPlotItem().vb
        sec = max(0.0, float(vb.mapSceneToView(ev.scenePos()).x()))
        self.player.setPosition(int(sec * 1000))

    # ===== marks & rows =====
    def _mark_start(self):
        self.line_start.setText(self.line_pos.text())

    def _mark_end(self):
        self.line_end.setText(self.line_pos.text())

    def _add_row_from_marks(self):
        """Append a new row from marked start/end and current class selection."""
        if not self.model or not self.sample_id:
            return
        s_txt, e_txt = self.line_start.text().strip(), self.line_end.text().strip()
        if not s_txt or not e_txt:
            QMessageBox.warning(self, "Missing marks", "Please mark Start and End first.")
            return
        try:
            s, e = float(s_txt), float(e_txt)
            if e < s:
                s, e = e, s
        except Exception:
            QMessageBox.warning(self, "Invalid marks", "Start/End must be numbers.")
            return

        cls = self.class_combo.currentText().strip()
        row = {
            "sample_id": self.sample_id,
            "audio_path": str(self.audio_path or ""),
            "start_s": f"{s:.3f}",
            "end_s": f"{e:.3f}",
            "label_class": cls,
            "notes": "",
            "created_at": datetime.now().isoformat(timespec="seconds"),
        }
        self.model.insert_empty_row(row)
        self.line_start.clear()
        self.line_end.clear()

    def _delete_rows(self):
        """Delete selected rows from the table/model."""
        if not self.model:
            return
        sel = self.table.selectionModel().selectedRows()
        if not sel:
            return
        self.model.remove_rows([ix.row() for ix in sel])

    # ===== CSV I/O =====
    def _reload_labels(self):
        """Load labels CSV into the table model (ensure required columns)."""
        if not self.labels_csv_path:
            return
        try:
            df = pd.read_csv(self.labels_csv_path, dtype=str, encoding="utf-8")
        except Exception:
            df = pd.DataFrame(columns=LABEL_COLUMNS)

        # Ensure schema and column order
        for c in LABEL_COLUMNS:
            if c not in df.columns:
                df[c] = ""
        df = df[LABEL_COLUMNS]

        self.model = PandasModel(df)
        self.table.setModel(self.model)
        self.table.resizeColumnsToContents()
        self._apply_class_delegate()

    def _save_labels(self):
        """Persist the model dataframe to CSV (with numeric rounding)."""
        if not self.model or not self.labels_csv_path:
            return
        df = self.model.dataframe().copy()

        # Normalize numeric fields
        for col in ("start_s", "end_s"):
            df[col] = pd.to_numeric(df[col], errors="coerce").round(3).astype(str)

        try:
            df.to_csv(self.labels_csv_path, index=False, encoding="utf-8")
            self._sync_meta_link()
            QMessageBox.information(self, "Saved", f"Saved labels:\n{self.labels_csv_path}")
        except Exception as e:
            QMessageBox.critical(self, "Save error", str(e))

    def _sync_meta_link(self):
        """Write labels CSV path back to META_CSV for this sample_id (column: labels_csv)."""
        if not self.sample_id or not self.labels_csv_path:
            return
        if not META_CSV.exists():
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

    # ===== classes from sample_list.csv =====
    def _load_classes(self):
        """Load unique class values from SAMPLE_LIST_CSV column named 'type' (case-insensitive)."""
        opts = [""]
        if SAMPLE_LIST_CSV.exists():
            try:
                df = pd.read_csv(SAMPLE_LIST_CSV)
                col = next((c for c in df.columns if c.strip().lower() == "type"), None)
                if col:
                    vals = [str(x) for x in df[col].dropna().unique().tolist()]
                    vals.sort()
                    opts = [""] + vals
            except Exception as e:
                print("[WARN] Could not load sample_list.csv:", e)

        self._class_options = opts
        self.class_combo.blockSignals(True)
        self.class_combo.clear()
        self.class_combo.addItems(self._class_options)
        self.class_combo.blockSignals(False)

    def _apply_class_delegate(self):
        """Apply ComboBoxDelegate to the 'label_class' column so users select from allowed classes."""
        if not self.model:
            return
        try:
            col_idx = list(self.model.dataframe().columns).index("label_class")
        except ValueError:
            return
        self.table.setItemDelegateForColumn(col_idx, ComboBoxDelegate(self._class_options, self.table))

    # ===== UI helpers =====
    def _toggle_visuals(self):
        """Hide/show waveform+spectrogram area to give more space to the table."""
        vis = self.splitter.widget(0).isVisible()
        self.splitter.widget(0).setVisible(not vis)  # <-- fixed (Python: 'not', not '!')
        # Allocate sizes: when hidden, give almost all space to the table.
        if vis:
            self.splitter.setSizes([0, 60, 1000])
        else:
            self.splitter.setSizes([220, 70, 700])