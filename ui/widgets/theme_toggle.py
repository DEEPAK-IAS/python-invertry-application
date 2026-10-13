from __future__ import annotations
from PySide2.QtWidgets import QPushButton
from PySide2.QtCore import Qt, QSize
from app.utils.theme_manager import ThemeManager
from app.design.icons import icon, register_icon_refresh
from app.design.tokens import ButtonSize


class ThemeToggleButton(QPushButton):
    """A button that toggles between dark and light theme.

    Sizing/icon now come from design tokens (ButtonSize.SMALL) instead
    of a hardcoded setFixedSize(), and the sun/moon glyph is a themed
    vector icon instead of an emoji character (emoji glyphs render
    inconsistently across Windows font/DPI settings).
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("SmallButton")
        self.setCursor(Qt.PointingHandCursor)
        size = ButtonSize.SMALL
        self.setIconSize(QSize(size["icon"], size["icon"]))
        self.setToolTip("Toggle Dark / Light theme")
        self.clicked.connect(self._toggle)
        register_icon_refresh(self)
        self._update_label()

    def _toggle(self):
        ThemeManager.toggle()
        self._update_label()

    def refresh_icon(self):
        self._update_label()

    def _update_label(self):
        if ThemeManager.is_dark():
            self.setIcon(icon("sun"))
            self.setText(" Light")
        else:
            self.setIcon(icon("moon"))
            self.setText(" Dark")
