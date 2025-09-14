# code/ui/styles.py
# Dark theme, larger titles, consistent variants, and controls styling (Qt QSS).

app_qss = """
/* ====== Base ====== */
QMainWindow {
    background-color: #1c1f26;  /* dark gray */
    color: #e8ecf4;
    font-family: "Segoe UI", "SF Pro Text", "Vazirmatn", Arial;
    font-size: 14px;
}

/* IMPORTANT: keep QWidget dark (NOT transparent) to force dark mode always */
QWidget {
    background-color: #1c1f26;
    color: #e8ecf4;
}

/* ====== Headings ====== */
QLabel[class="h1"] {
    font-size: 28px;
    font-weight: 800;
    color: #ffffff;
    margin: 8px 0 12px 0;
}
QLabel[class="subtle"] {
    color: #9aa5b8;
    font-size: 13px;
    margin-bottom: 6px;
}

/* ====== Cards / Containers ====== */
QFrame#toolCard, QFrame#formCard {
    background: #1f242e;
    border: 1px solid #3a4252;
    border-radius: 16px;
}

/* ====== Back button ====== */
QPushButton[class="back"] {
    padding: 8px 14px;
    border-radius: 10px;
    border: 1px solid #3a4252;
    background: #2a2f3b;
    color: #ffffff;
    font-weight: 600;
}
QPushButton[class="back"]:hover { background: #333a47; }

/* ====== Toolbar Buttons (variants) ====== */
QPushButton[variant] {
    border-radius: 10px;
    padding: 8px 14px;
    font-weight: 600;
    border: 1px solid transparent;
}
QPushButton[variant="primary"] { background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #42a5f5, stop:1 #1e88e5); color:#fff; }
QPushButton[variant="success"] { background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #66bb6a, stop:1 #388e3c); color:#fff; }
QPushButton[variant="warn"]    { background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #ffca28, stop:1 #f57c00); color:#222; }
QPushButton[variant="accent"]  { background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #ab47bc, stop:1 #6a1b9a); color:#fff; }
QPushButton[variant="soft"]    { background:#2a2f3b; color:#e8ecf4; border:1px solid #3a4252; }
QPushButton[variant="soft"]:hover { background:#333a47; }
QPushButton[variant="danger"]  { background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #ef5350, stop:1 #c62828); color:#fff; }
QPushButton[variant]:disabled { opacity: .5; }

/* ====== Inputs ====== */
QLineEdit, QDateEdit, QTimeEdit, QComboBox {
    background: #2a2f3b;
    color: #e8ecf4;
    border: 1px solid #3a4252;
    border-radius: 10px;
    padding: 8px 10px;
    min-height: 32px;
}
QLineEdit:focus, QDateEdit:focus, QTimeEdit:focus, QComboBox:focus {
    border: 1px solid #42a5f5;
    background: #2f3543;
}
QLineEdit::placeholder { color: #8d97ad; }
QComboBox QAbstractItemView { background:#2a2f3b; color:#e8ecf4; selection-background-color:#3d5afe; border:1px solid #3a4252; }

/* ====== Slider (timeline) ====== */
QSlider::groove:horizontal {
    border: 1px solid #3a4252; height: 8px;
    background: #2a2f3b; border-radius: 6px;
}
QSlider::handle:horizontal {
    background: #42a5f5; width: 16px; border: 1px solid #1e88e5;
    margin: -6px 0; border-radius: 8px;
}
QSlider::sub-page:horizontal {
    background: #3d5afe; border: 1px solid #2f47c7; height: 8px; border-radius: 6px;
}

/* ====== Tables ====== */
QTableView {
    background: #2a2f3b;
    border: 1px solid #3a4252;
    border-radius: 12px;
    gridline-color: #3a4252;
    selection-background-color: #33426b;
    selection-color: #ffffff;
    alternate-background-color: #262b36;
}
QTableView::item { padding: 6px; }
QHeaderView::section {
    background: #333a47;
    color: #f1f1f1;
    border: 1px solid #3a4252;
    padding: 6px 8px;
    font-weight: 700;
}
QTableCornerButton::section { background:#333a47; border:1px solid #3a4252; }

/* ====== Scrollbars ====== */
QScrollBar:horizontal, QScrollBar:vertical { background:transparent; border:none; margin:6px; }
QScrollBar::handle:horizontal, QScrollBar::handle:vertical {
    background:#4a5268; border-radius:8px; min-width:24px; min-height:24px;
}
QScrollBar::handle:hover { background:#5c6580; }

/* ====== Primary CTA ====== */
QPushButton[class="ctaPrimary"] {
    border-radius: 10px;
    padding: 10px 18px;
    font-weight: 700;
    background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #42a5f5, stop:1 #1e88e5);
    color: #ffffff;
}

QTabWidget::pane {
    border: none;                 /* remove border */
    background: transparent;       /* no ugly box behind */
    margin-top: -2px;              /* make tabs sit closer to content */
}

QTabBar::tab {
    background: #2a2f3b;
    color: #cfd3e0;
    font-weight: 600;
    padding: 8px 18px;
    border-radius: 10px;
    margin-right: 6px;
    border: 1px solid #3a4252;
}
QTabBar::tab:selected {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #42a5f5, stop:1 #1e88e5);
    color: #ffffff;
    border: none;
}
QTabBar::tab:hover {
    background: #374055;
}

QTabWidget::pane {
    border: none;
    background: #1c1f26;   /* same as main background */
}

/* ==== Tabs (kill the white strip under tabs) ==== */
QTabWidget::pane {
    border: 0;
    background: #1c1f26;        
    margin: 0;
    padding: 0;
}

QWidget#qt_tabwidget_stackedwidget {
    background: #1c1f26;     
    border: 0;
}

QTabBar {
    background: transparent;
    border: 0;
}

/* تب‌ها کارت‌مانند */
QTabBar::tab {
    background: #2a2f3b;
    color: #cfd3e0;
    font-weight: 600;
    padding: 8px 18px;
    border-radius: 10px;
    margin-right: 6px;
    border: 1px solid #3a4252;
    margin-top: 4px;           
}
QTabBar::tab:selected {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #42a5f5, stop:1 #1e88e5);
    color: #ffffff;
    border: none;
}
QTabBar::tab:hover {
    background: #374055;
}
"""


# code/ui/styles.py  (only the Tabs block — paste once, remove duplicates above/below)

app_qss += """
/* ==== Tabs (clean, no white strip) ==== */

/* Pane behind tabs & content */
QTabWidget::pane {
    border: 0;
    background: #1c1f26;   /* same as app bg */
    margin: 0;
    padding: 0;
}

/* Qt internal stacked widget used by QTabWidget — keep it dark */
QWidget#qt_tabwidget_stackedwidget {
    background: #1c1f26;
    border: 0;
}

/* Tab bar itself */
QTabBar { background: transparent; border: 0; }

/* Tabs as rounded pills/cards */
QTabBar::tab {
    background: #2a2f3b;
    color: #cfd3e0;
    font-weight: 600;
    padding: 8px 18px;
    border-radius: 10px;
    margin-right: 6px;
    border: 1px solid #3a4252;
    margin-top: 4px;
}
QTabBar::tab:selected {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #42a5f5, stop:1 #1e88e5);
    color: #ffffff;
    border: none;
}
QTabBar::tab:hover { background: #374055; }
"""