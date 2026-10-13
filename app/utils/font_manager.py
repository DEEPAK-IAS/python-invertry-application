"""
Loads the bundled Poppins font files into the Qt font database at
startup, and sets it as the application-wide default font.

Why this instead of just `font-family: Poppins` in QSS:
QSS font-family only works if the font is already installed on the
customer's Windows machine, which we can't assume for a fresh install.
QFontDatabase.addApplicationFont() registers the font at the process
level regardless of what's installed system-wide, and PyInstaller will
bundle the .ttf files as long as they're included as data files (see
stock_manager.spec).

Call FontManager.load() once, right after QApplication() is created,
before any window is shown. Nothing else in the app should call
QFontDatabase or set fonts per-widget — that's what makes typography
consistent instead of ad hoc.
"""
from __future__ import annotations
import os
from PySide2.QtGui import QFontDatabase, QFont
from PySide2.QtWidgets import QApplication
from app.utils.logger import logger

FONTS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "assets", "fonts"
)

_FONT_FILES = [
    "Poppins-Light.ttf",
    "Poppins-Regular.ttf",
    "Poppins-Medium.ttf",
    "Poppins-SemiBold.ttf",
    "Poppins-Bold.ttf",
    "Poppins-Italic.ttf",
]

FAMILY_NAME = "Poppins"


class FontManager:
    _loaded = False

    @classmethod
    def load(cls) -> str:
        """
        Registers all bundled Poppins weights and sets the app default
        font. Returns the family name actually applied (falls back to
        Segoe UI if the font files are missing so the app never crashes
        over a missing asset).
        """
        if cls._loaded:
            return FAMILY_NAME

        app = QApplication.instance()
        if app is None:
            logger.warning("FontManager.load() called before QApplication exists")
            return "Segoe UI"

        any_loaded = False
        for filename in _FONT_FILES:
            path = os.path.join(FONTS_DIR, filename)
            if not os.path.exists(path):
                logger.warning(f"Font file missing, skipped: {path}")
                continue
            font_id = QFontDatabase.addApplicationFont(path)
            if font_id == -1:
                logger.warning(f"Failed to register font: {path}")
                continue
            any_loaded = True

        cls._loaded = True

        family = FAMILY_NAME if any_loaded else "Segoe UI"
        if not any_loaded:
            logger.warning(
                "No Poppins font files loaded — falling back to Segoe UI. "
                f"Expected files under: {FONTS_DIR}"
            )
        else:
            logger.info(f"Poppins font family registered from {FONTS_DIR}")

        default_font = QFont(family, 10)
        app.setFont(default_font)
        return family
