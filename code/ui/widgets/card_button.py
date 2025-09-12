# ui/widgets/card_button.py
# A modern card-like button with gradient background and shadow.

from PySide6.QtWidgets import QPushButton, QGraphicsDropShadowEffect
from PySide6.QtGui import QColor, QFont
from PySide6.QtCore import Qt


class CardButton(QPushButton):
    def __init__(self, text: str, color1="#42a5f5", color2="#1e88e5", parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumSize(260, 140)  # Bigger card size
        self.setFont(QFont("Segoe UI", 14, QFont.Bold))

        # Gradient style
        style = f"""
        QPushButton {{
            border-radius: 16px;
            color: white;
            padding: 18px;
            text-align: left;
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                        stop:0 {color1},
                                        stop:1 {color2});
        }}
        QPushButton:hover {{
            opacity: 0.9;
        }}
        QPushButton:pressed {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                        stop:0 {color2},
                                        stop:1 {color1});
        }}
        """
        self.setStyleSheet(style)

        # Drop shadow effect
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(30)
        shadow.setOffset(0, 8)
        shadow.setColor(QColor(0, 0, 0, 100))
        self.setGraphicsEffect(shadow)