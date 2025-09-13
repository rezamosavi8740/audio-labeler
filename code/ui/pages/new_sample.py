# code/ui/pages/new_sample.py
# English comments included.
# New Sample — Step 1 (Metadata) with "create" and "edit" modes.

from pathlib import Path
from datetime import datetime
import uuid
import pandas as pd

from PySide6.QtWidgets import (
    QWidget, QLabel, QLineEdit, QDateEdit, QTimeEdit, QPushButton,
    QGridLayout, QVBoxLayout, QHBoxLayout, QMessageBox, QFrame
)
from PySide6.QtCore import Signal, Qt, QDate, QTime
from PySide6.QtGui import QDoubleValidator, QIntValidator


# Data locations
DATA_DIR = Path.cwd() / "data"
META_CSV = DATA_DIR / "samples_meta.csv"

# Column order for metadata CSV
META_COLUMNS = [
    "sample_id", "date", "time",
    "temperature_c", "pressure_kpa",
    "latitude", "longitude",
    "count", "sample_name",
    "labels_csv", "created_at",
]


class NewSamplePage(QWidget):
    sig_go_home = Signal()
    sig_go_step2 = Signal(str)  # emits sample_id

    def __init__(self):
        super().__init__()

        # --- Top bar ---
        top = QHBoxLayout()
        btn_back = QPushButton("← Home")
        btn_back.setProperty("class", "back")

        self.title = QLabel("New Sample — Step 1 (Metadata)")
        self.title.setProperty("class", "h1")

        top.addWidget(btn_back, alignment=Qt.AlignLeft)
        top.addWidget(self.title, alignment=Qt.AlignLeft)
        top.addStretch()

        # --- Form card ---
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

        # Two-column grid
        grid = QGridLayout()
        grid.setHorizontalSpacing(20)
        grid.setVerticalSpacing(14)

        def add_row(r, c_label, text, widget):
            lbl = QLabel(text); lbl.setProperty("class", "formLabel")
            grid.addWidget(lbl, r, c_label); grid.addWidget(widget, r, c_label + 1)

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

        grid.setColumnStretch(0, 0); grid.setColumnStretch(1, 1)
        grid.setColumnStretch(2, 0); grid.setColumnStretch(3, 1)

        form_wrap.addLayout(grid)

        # Bottom bar
        action_bar = QHBoxLayout()
        action_bar.addStretch()
        self.btn_submit = QPushButton("Next →")
        self.btn_submit.setProperty("class", "ctaPrimary")
        action_bar.addWidget(self.btn_submit)
        form_wrap.addLayout(action_bar)

        # Root layout
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(14)
        root.addLayout(top)
        root.addWidget(form_card)

        # Connections
        btn_back.clicked.connect(self.sig_go_home.emit)
        self.btn_submit.clicked.connect(self._handle_submit)

        # CSV ensure
        self._ensure_csv()

        # Edit mode state
        self._edit_mode = False
        self._edit_sample_id: str | None = None

    # ---------- Public API ----------
    def open_for_edit(self, sample_id: str):
        """
        Load an existing sample into the form and switch to edit mode.
        """
        self._ensure_csv()
        try:
            df = pd.read_csv(META_CSV, dtype=str, encoding="utf-8")
        except Exception:
            QMessageBox.warning(self, "Load error", "Could not read samples_meta.csv")
            return

        if "sample_id" not in df.columns:
            QMessageBox.information(self, "Not found", "No 'sample_id' column.")
            return

        row = df.loc[df["sample_id"].astype(str) == str(sample_id)]
        if row.empty:
            QMessageBox.information(self, "Not found", f"Sample {sample_id} not found.")
            return

        r = row.iloc[0]

        # Fill widgets (defensive conversions)
        # date
        try:
            d = QDate.fromString(str(r.get("date", "")), "yyyy-MM-dd")
            if d.isValid(): self.in_date.setDate(d)
        except Exception:
            pass
        # time
        try:
            tparts = str(r.get("time", "00:00:00")).split(":")
            h, m, s = (int(tparts[0]), int(tparts[1]), int(tparts[2])) if len(tparts) == 3 else (0, 0, 0)
            self.in_time.setTime(QTime(h, m, s))
        except Exception:
            pass

        self.in_temp.setText(str(r.get("temperature_c", "")))
        self.in_press.setText(str(r.get("pressure_kpa", "")))
        self.in_lat.setText(str(r.get("latitude", "")))
        self.in_lon.setText(str(r.get("longitude", "")))
        self.in_count.setText(str(r.get("count", "")))
        self.in_name.setText(str(r.get("sample_name", "")))

        # Switch to edit mode
        self._edit_mode = True
        self._edit_sample_id = str(sample_id)
        self.title.setText(f"Edit Sample — Step 1 (Metadata) • {sample_id}")
        self.btn_submit.setText("Save & Continue →")

    # ---------- CSV helpers ----------
    def _ensure_csv(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        if not META_CSV.exists():
            pd.DataFrame(columns=META_COLUMNS).to_csv(META_CSV, index=False, encoding="utf-8")

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

    def _update_row(self, sample_id: str, row: dict):
        self._ensure_csv()
        try:
            df = pd.read_csv(META_CSV, dtype=str, encoding="utf-8")
        except Exception:
            df = pd.DataFrame(columns=META_COLUMNS)

        if "sample_id" not in df.columns:
            df["sample_id"] = ""

        # ensure missing columns exist
        for col in META_COLUMNS:
            if col not in df.columns:
                df[col] = ""

        mask = df["sample_id"].astype(str) == str(sample_id)
        if mask.any():
            for k, v in row.items():
                if k in df.columns:
                    df.loc[mask, k] = v
        else:
            # if not found, append as new
            df.loc[len(df)] = {**{c: "" for c in META_COLUMNS}, **row}

        df.to_csv(META_CSV, index=False, encoding="utf-8")

    # ---------- Submit ----------
    def _handle_submit(self):
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

        # In edit mode we keep the same ID; otherwise generate new.
        if self._edit_mode and self._edit_sample_id:
            sample_id = self._edit_sample_id
        else:
            sample_id = datetime.now().strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:6]

        created_at = datetime.now().isoformat(timespec="seconds")

        row = {
            "sample_id": sample_id,
            "date": date_str, "time": time_str,
            "temperature_c": temp, "pressure_kpa": press,
            "latitude": lat, "longitude": lon,
            "count": count, "sample_name": name,
            "labels_csv": "",  # will be set by Step 2 when labels CSV is created/saved
            "created_at": created_at,
        }

        try:
            if self._edit_mode and self._edit_sample_id:
                # update existing
                self._update_row(self._edit_sample_id, row)
            else:
                # create new
                self._append_row(row)
        except Exception as e:
            QMessageBox.critical(self, "Save error", f"Could not save metadata:\n{e}")
            return

        QMessageBox.information(self, "Saved", f"Sample ID:\n{sample_id}")
        self.sig_go_step2.emit(sample_id)

        # Reset edit mode for next time
        self._edit_mode = False
        self._edit_sample_id = None
        self.title.setText("New Sample — Step 1 (Metadata)")
        self.btn_submit.setText("Next →")