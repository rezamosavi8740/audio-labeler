# code/ui/pages/home.py
# Home page with 4 modern styled cards.
# Emits signals only, no routing logic inside here.

from PySide6.QtWidgets import QWidget, QLabel, QGridLayout, QVBoxLayout
from PySide6.QtCore import Signal, Qt
from code.ui.widgets.card_button import CardButton


class HomePage(QWidget):
    # Navigation signals (MainWindow connects these)
    sig_new_sample = Signal()
    sig_edit_sample = Signal()
    sig_sample_types = Signal()
    sig_csv_reports = Signal()

    def __init__(self):
        super().__init__()

        # Root layout
        root = QVBoxLayout(self)
        root.setContentsMargins(40, 40, 40, 40)
        root.setSpacing(24)

        # Title
        title = QLabel("🎧 Audio Labeler — Home")
        title.setProperty("class", "h1")
        root.addWidget(title, alignment=Qt.AlignLeft)

        # Grid layout for 4 cards
        grid = QGridLayout()
        grid.setHorizontalSpacing(30)
        grid.setVerticalSpacing(30)

        # Four cards
        self.btn_new = CardButton("➕ New Sample", color1="#42a5f5", color2="#1e88e5")
        self.btn_edit = CardButton("✏️ Edit Sample", color1="#66bb6a", color2="#388e3c")
        self.btn_specs = CardButton("⚙️ Sample Types & Specs", color1="#ffca28", color2="#f57c00")
        self.btn_csv = CardButton("📊 CSV Reports", color1="#ab47bc", color2="#6a1b9a")

        # Place them in a 2x2 grid
        grid.addWidget(self.btn_new,   0, 0)
        grid.addWidget(self.btn_edit,  0, 1)
        grid.addWidget(self.btn_specs, 1, 0)
        grid.addWidget(self.btn_csv,   1, 1)

        root.addLayout(grid)

        # Connect button clicks to emit signals
        self.btn_new.clicked.connect(self.sig_new_sample.emit)
        self.btn_edit.clicked.connect(self.sig_edit_sample.emit)
        self.btn_specs.clicked.connect(self.sig_sample_types.emit)
        self.btn_csv.clicked.connect(self.sig_csv_reports.emit)