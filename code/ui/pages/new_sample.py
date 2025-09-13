# code/ui/pages/new_sample.py
# English comments included.
# New Sample — Step 1 (Metadata), styled with a card and two-column layout.

from PySide6.QtWidgets import (
    QWidget, QLabel, QLineEdit, QDateEdit, QTimeEdit, QPushButton,
    QGridLayout, QVBoxLayout, QHBoxLayout, QMessageBox, QFrame
)
from PySide6.QtCore import Signal, Qt, QDate, QTime
from PySide6.QtGui import QDoubleValidator, QIntValidator
from pathlib import Path
import pandas as pd
import uuid
from datetime import datetime

DATA_DIR = Path.cwd() / "data"
META_CSV = DATA_DIR / "samples_meta.csv"

META_COLUMNS = [
    "sample_id", "date", "time",
    "temperature_c", "pressure_kpa",
    "latitude", "longitude",
    "count", "sample_name",
    "labels_csv", "created_at",
]


class NewSamplePage(QWidget):
    sig_go_home = Signal()
    sig_go_step2 = Signal(str)   # carries sample_id

    def __init__(self):
        super().__init__()

        # ===== Top bar =====
        top = QHBoxLayout()
        btn_back = QPushButton("← Home")
        btn_back.setProperty("class", "back")

        title = QLabel("New Sample — Step 1 (Metadata)")
        title.setProperty("class", "h1")

        top.addWidget(btn_back, alignment=Qt.AlignLeft)
        top.addWidget(title, alignment=Qt.AlignLeft)
        top.addStretch()

        # ===== Form card =====
        form_card = QFrame()
        form_card.setObjectName("formCard")
        form_wrap = QVBoxLayout(form_card)
        form_wrap.setContentsMargins(18, 16, 18, 16)
        form_wrap.setSpacing(10)

        subtitle = QLabel("Daily metadata • Please fill in the fields below")
        subtitle.setProperty("class", "subtle")
        form_wrap.addWidget(subtitle)

        # Inputs
        self.in_temp = QLineEdit();    self.in_temp.setPlaceholderText("e.g., 25")
        self.in_temp.setValidator(QDoubleValidator(-273.15, 1e6, 3))
        self.in_press = QLineEdit();   self.in_press.setPlaceholderText("e.g., 101")
        self.in_press.setValidator(QDoubleValidator(-1e3, 1e7, 3))

        self.in_date = QDateEdit();    self.in_date.setDisplayFormat("yyyy-MM-dd")
        self.in_date.setDate(QDate.currentDate()); self.in_date.setCalendarPopup(True)

        self.in_time = QTimeEdit();    self.in_time.setDisplayFormat("HH:mm:ss")
        self.in_time.setTime(QTime.currentTime())

        self.in_lat = QLineEdit();     self.in_lat.setPlaceholderText("e.g., 35.6892")
        self.in_lat.setValidator(QDoubleValidator(-90.0, 90.0, 6))
        self.in_lon = QLineEdit();     self.in_lon.setPlaceholderText("e.g., 51.3890")
        self.in_lon.setValidator(QDoubleValidator(-180.0, 180.0, 6))

        self.in_count = QLineEdit();   self.in_count.setPlaceholderText("1")
        self.in_count.setValidator(QIntValidator(0, 10**6))

        self.in_name = QLineEdit();    self.in_name.setPlaceholderText("Sample-A")

        # Grid: two columns (label, input) × 4 rows per column
        grid = QGridLayout()
        grid.setHorizontalSpacing(20)
        grid.setVerticalSpacing(14)

        def add_row(r, c_label, text, widget):
            lbl = QLabel(text); lbl.setProperty("class", "formLabel")
            grid.addWidget(lbl, r, c_label)
            grid.addWidget(widget, r, c_label + 1)

        # Left column
        add_row(0, 0, "Temperature (°C):", self.in_temp)
        add_row(1, 0, "Pressure (kPa):",   self.in_press)
        add_row(2, 0, "Date:",             self.in_date)
        add_row(3, 0, "Time:",             self.in_time)

        # Right column
        add_row(0, 2, "Latitude:",         self.in_lat)
        add_row(1, 2, "Longitude:",        self.in_lon)
        add_row(2, 2, "Count:",            self.in_count)
        add_row(3, 2, "Sample Name:",      self.in_name)

        # Set column stretch (label narrow, input wide)
        grid.setColumnStretch(0, 0)
        grid.setColumnStretch(1, 1)
        grid.setColumnStretch(2, 0)
        grid.setColumnStretch(3, 1)

        form_wrap.addLayout(grid)

        # ===== Bottom action bar inside card =====
        action_bar = QHBoxLayout()
        action_bar.addStretch()
        btn_next = QPushButton("Next →")
        btn_next.setProperty("class", "ctaPrimary")
        action_bar.addWidget(btn_next)
        form_wrap.addLayout(action_bar)

        # ===== Root layout =====
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(14)
        root.addLayout(top)
        root.addWidget(form_card)

        # Connections
        btn_back.clicked.connect(self.sig_go_home.emit)
        btn_next.clicked.connect(self._handle_submit)

        # CSV
        self._ensure_csv()

    # ---------- CSV helpers ----------
    def _ensure_csv(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        if not META_CSV.exists():
            df = pd.DataFrame(columns=META_COLUMNS)
            df.to_csv(META_CSV, index=False, encoding="utf-8")

    def _append_row(self, row: dict):
        self._ensure_csv()
        try:
            df = pd.read_csv(META_CSV, dtype=str, encoding="utf-8")
        except Exception:
            df = pd.DataFrame(columns=META_COLUMNS)

        for col in META_COLUMNS:
            if col not in df.columns:
                df[col] = ""
        df = df[META_COLUMNS]

        df.loc[len(df)] = {**{c: "" for c in META_COLUMNS}, **row}
        df.to_csv(META_CSV, index=False, encoding="utf-8")

    # ---------- Submit ----------
    def _handle_submit(self):
        # Collect values
        date_str = self.in_date.date().toString("yyyy-MM-dd")
        time_str = self.in_time.time().toString("HH:mm:ss")

        temp = self.in_temp.text().strip()
        press = self.in_press.text().strip()
        lat = self.in_lat.text().strip()
        lon = self.in_lon.text().strip()
        count = self.in_count.text().strip()
        name = self.in_name.text().strip()

        if not name:
            QMessageBox.warning(self, "Validation", "Sample Name is required.")
            return

        sample_id = datetime.now().strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:6]
        created_at = datetime.now().isoformat(timespec="seconds")

        row = {
            "sample_id": sample_id,
            "date": date_str, "time": time_str,
            "temperature_c": temp, "pressure_kpa": press,
            "latitude": lat, "longitude": lon,
            "count": count, "sample_name": name,
            "labels_csv": "", "created_at": created_at,
        }

        try:
            self._append_row(row)
        except Exception as e:
            QMessageBox.critical(self, "Save error", f"Could not save metadata:\n{e}")
            return

        QMessageBox.information(self, "Saved", f"Sample created with ID:\n{sample_id}")
        self.sig_go_step2.emit(sample_id)