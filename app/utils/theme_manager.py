from __future__ import annotations
from PySide2.QtWidgets import QApplication  # type: ignore
from app.utils.logger import logger
from app.design.tokens import PALETTES
from app.design.qss_builder import build_stylesheet
from app.design import icons as icon_module


class ThemeManager:
    """
    Public API is unchanged from before this refactor (apply/toggle/
    current/is_dark), so no caller elsewhere in the app needs to change.
    Internally, the stylesheet is now generated from app/design/tokens.py
    via app/design/qss_builder.py instead of reading a hand-maintained
    .qss file -- this is what guarantees dark/light never drift out of
    structural sync and removes the duplicate/contradictory selectors
    that were causing the button-size and table-contrast bugs.
    """

    _current_theme: str = "dark"

    @classmethod
    def apply(cls, theme: str):
        """Apply 'dark' or 'light' theme to the app."""
        if theme not in PALETTES:
            logger.warning(f"Unknown theme '{theme}', defaulting to 'dark'")
            theme = "dark"

        palette = PALETTES[theme]
        stylesheet = build_stylesheet(palette)

        app = QApplication.instance()
        if app is not None:
            app.setStyleSheet(stylesheet)

        # Icons (qtawesome glyphs) are recolored in Python, not QSS, so
        # they need to be told the active theme's icon tint explicitly.
        icon_module.set_active_icon_colors(
            icon_color=palette.icon_color,
            icon_color_on_accent=palette.icon_color_on_accent,
        )

        cls._current_theme = theme
        logger.info(f"Theme switched to: {theme}")

    @classmethod
    def toggle(cls):
        """Toggle between dark and light."""
        new_theme = "light" if cls._current_theme == "dark" else "dark"
        cls.apply(new_theme)

    @classmethod
    def current(cls) -> str:
        return cls._current_theme

    @classmethod
    def is_dark(cls) -> bool:
        return cls._current_theme == "dark"

    @classmethod
    def palette(cls):
        """Return the active Palette object (colors) for code that needs
        a raw color value outside of QSS, e.g. drawing a chart."""
        return PALETTES[cls._current_theme]
