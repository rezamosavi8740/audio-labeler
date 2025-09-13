# Dark theme variant of app_qss
app_qss = """
/* ====== Base ====== */
QMainWindow {
    background-color: #1c1f26;   /* Dark gray background */
    font-family: "Segoe UI", "SF Pro Text", "Vazirmatn", Arial;
    font-size: 14px;
    color: #e8ecf4;              /* Light text */
}

QWidget {
    background-color: transparent;
    color: #e8ecf4;
}

/* Headings */
QLabel.h1 {
    font-size: 26px;
    font-weight: 800;
    color: #ffffff;              /* White titles for visibility */
    margin: 8px 0 12px 0;
}

/* Back button */
QPushButton.back {
    padding: 8px 14px;
    border-radius: 10px;
    border: 1px solid #3a4252;
    background: #2a2f3b;
    color: #ffffff;
    font-weight: 600;
}
QPushButton.back:hover { background: #333a47; }

/* Toolbar Buttons */
QPushButton[variant] {
    border-radius: 10px;
    padding: 8px 14px;
    font-weight: 600;
    border: 1px solid transparent;
}

/* Primary (blue) */
QPushButton[variant="primary"] {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #42a5f5, stop:1 #1e88e5);
    color: #ffffff;
}
/* Success (green) */
QPushButton[variant="success"] {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #66bb6a, stop:1 #388e3c);
    color: #ffffff;
}
/* Warn (amber) */
QPushButton[variant="warn"] {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #ffca28, stop:1 #f57c00);
    color: #222222;
}
/* Accent (purple) */
QPushButton[variant="accent"] {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #ab47bc, stop:1 #6a1b9a);
    color: #ffffff;
}
/* Soft (neutral) */
QPushButton[variant="soft"] {
    background: #2a2f3b;
    color: #e8ecf4;
    border: 1px solid #3a4252;
}
QPushButton[variant="soft"]:hover { background: #333a47; }
/* Danger (red) */
QPushButton[variant="danger"] {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #ef5350, stop:1 #c62828);
    color: #ffffff;
}

/* Disabled state */
QPushButton[variant]:disabled { opacity: 0.5; }

/* ====== Tables ====== */
QTableView {
    background: #2a2f3b;
    border: 1px solid #3a4252;
    border-radius: 12px;
    gridline-color: #3a4252;
    selection-background-color: #3d5afe;
    selection-color: #ffffff;
}
QTableView::item { padding: 6px; }
QHeaderView::section {
    background: #333a47;
    color: #f1f1f1;
    border: 1px solid #3a4252;
    padding: 6px 8px;
    font-weight: 700;
}
QTableCornerButton::section {
    background: #333a47;
    border: 1px solid #3a4252;
}

/* Scrollbars */
QScrollBar:horizontal, QScrollBar:vertical {
    background: transparent;
    border: none;
    margin: 6px;
}
QScrollBar::handle:horizontal, QScrollBar::handle:vertical {
    background: #4a5268;
    border-radius: 8px;
    min-width: 24px;
    min-height: 24px;
}
QScrollBar::handle:hover { background: #5c6580; }
"""