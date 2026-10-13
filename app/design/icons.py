"""
Centralized icon system.

Why qtawesome: it bundles Font Awesome / Material icon fonts directly
inside the pip package (no per-icon asset files to manage, no missing-
file bugs), renders crisp at any size (vector, not bitmap), and lets us
recolor icons in code to match the active theme — which is what actually
fixes "icons look ugly / inconsistent / wrong size" for a PySide2 app.

Every icon in the app should be requested through `icon()` below so:
  - the same logical name always renders the same glyph
  - size always comes from design tokens (app/design/tokens.py), never
    a magic number typed at the call site
  - color always comes from the active theme automatically

If qtawesome is not installed (e.g. a dev environment that hasn't run
`pip install -r requirements.txt` yet), everything degrades to Qt's
built-in standard icons rather than crashing.
"""
from __future__ import annotations
from typing import Optional
import weakref

try:
    import qtawesome as qta
    _HAS_QTA = True
except Exception:
    _HAS_QTA = False

from PySide2.QtGui import QIcon
from PySide2.QtWidgets import QApplication, QStyle

from app.design.tokens import ButtonSize

# Logical name -> qtawesome glyph name. Centralizing this mapping means a
# rename ("mdi.pencil" -> a different pack) happens in exactly one place.
_GLYPHS = {
    "edit":        "fa5s.pen",
    "delete":      "fa5s.trash-alt",
    "view":        "fa5s.eye",
    "print":       "fa5s.print",
    "reprint":     "fa5s.print",
    "payment":     "fa5s.money-bill-wave",
    "add":         "fa5s.plus",
    "search":      "fa5s.search",
    "refresh":     "fa5s.sync-alt",
    "export":      "fa5s.file-export",
    "download":    "fa5s.download",
    "settings":    "fa5s.cog",
    "logout":      "fa5s.sign-out-alt",
    "dashboard":   "fa5s.th-large",
    "products":    "fa5s.box-open",
    "sales":       "fa5s.cash-register",
    "pending":     "fa5s.file-invoice-dollar",
    "customers":   "fa5s.users",
    "suppliers":   "fa5s.truck",
    "reports":     "fa5s.chart-bar",
    "close":       "fa5s.times",
    "check":       "fa5s.check",
    "warning":     "fa5s.exclamation-triangle",
    "info":        "fa5s.info-circle",
    "history":     "fa5s.history",
    "receipt":     "fa5s.receipt",
    "sun":         "fa5s.sun",
    "moon":        "fa5s.moon",
    "user":        "fa5s.user-circle",
    "building":    "fa5s.building",
    "phone":       "fa5s.phone-alt",
    "backup":      "fa5s.database",
}

# Fallback to Qt's built-in standard icons if qtawesome is unavailable.
_QT_STANDARD_FALLBACK = {
    "edit": QStyle.SP_FileDialogDetailedView,
    "delete": QStyle.SP_TrashIcon,
    "view": QStyle.SP_FileDialogContentsView,
    "print": QStyle.SP_DialogSaveButton,
    "reprint": QStyle.SP_DialogSaveButton,
    "add": QStyle.SP_FileDialogNewFolder,
    "refresh": QStyle.SP_BrowserReload,
    "close": QStyle.SP_DialogCloseButton,
    "settings": QStyle.SP_FileDialogDetailedView,
    "logout": QStyle.SP_DialogCloseButton,
}


def icon(name: str, color: Optional[str] = None, on_accent: bool = False) -> QIcon:
    """
    Return a themed QIcon for a logical icon name (see _GLYPHS).

    color: explicit hex override. If omitted, uses the active theme's
    icon_color token (set by ThemeManager whenever the theme changes).
    on_accent: use the "on accent" tint (for icons drawn on a colored
    button background, e.g. the Primary button) instead of the neutral
    surface tint.
    """
    if color is None:
        color = _current_icon_color(on_accent=on_accent)

    if _HAS_QTA and name in _GLYPHS:
        try:
            return qta.icon(_GLYPHS[name], color=color)
        except Exception:
            pass

    # Fallback path — still returns *something* sensible rather than a
    # blank icon, so the UI never silently loses an icon.
    style = QApplication.instance().style() if QApplication.instance() else None
    if style is not None and name in _QT_STANDARD_FALLBACK:
        return style.standardIcon(_QT_STANDARD_FALLBACK[name])
    return QIcon()


def table_action_icon_size():
    s = ButtonSize.TABLE_ACTION["icon"]
    from PySide2.QtCore import QSize
    return QSize(s, s)


# ── Theme wiring (set by ThemeManager.apply(), read by icon()) ──
_active_icon_color = "#4b4f66"
_active_icon_color_on_accent = "#ffffff"

# Any widget that draws its own themed icon (TableActionButton,
# ThemeToggleButton, Sidebar nav buttons, ...) can register a zero-arg
# callback here so it gets told to redraw its icon whenever the theme
# switches at runtime. Uses weak references so widgets that are closed/
# destroyed are dropped automatically instead of leaking.
_refresh_listeners: "weakref.WeakSet" = weakref.WeakSet()


def register_icon_refresh(obj) -> None:
    """`obj` must implement `refresh_icon()` / `refresh_icons()`. It is
    held weakly, so no need to unregister on widget close."""
    _refresh_listeners.add(obj)


def set_active_icon_colors(icon_color: str, icon_color_on_accent: str = "#ffffff"):
    global _active_icon_color, _active_icon_color_on_accent
    _active_icon_color = icon_color
    _active_icon_color_on_accent = icon_color_on_accent

    for obj in list(_refresh_listeners):
        try:
            if hasattr(obj, "refresh_icon"):
                obj.refresh_icon()
            elif hasattr(obj, "refresh_icons"):
                obj.refresh_icons()
        except RuntimeError:
            # underlying C++ Qt object already deleted
            pass


def _current_icon_color(on_accent: bool = False) -> str:
    return _active_icon_color_on_accent if on_accent else _active_icon_color
