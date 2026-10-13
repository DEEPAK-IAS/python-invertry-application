"""
A single, consistent icon-only button for table row actions
(edit / delete / view / print / payment / etc).

Replaces ad hoc QPushButton(text) or raw emoji buttons placed inside
table cells across the different *_window.py files. Using this widget
everywhere guarantees:
  - fixed square size (icon can never be bigger than the button)
  - consistent hover/pressed states (from the theme QSS, objectName
    "TableActionButton")
  - a tooltip so the icon-only action stays understandable
  - theme-aware icon color, refreshed automatically on theme toggle

Usage (inside a table's cell widget setup):
    from ui.widgets.table_action_button import TableActionButton
    edit_btn = TableActionButton("edit", "Edit", on_click=lambda: self._edit_row(row))
    delete_btn = TableActionButton("delete", "Delete", on_click=lambda: self._delete_row(row))
"""
from __future__ import annotations
from typing import Callable, Optional
from PySide2.QtWidgets import QToolButton
from PySide2.QtCore import Qt

from app.design.icons import icon, table_action_icon_size, register_icon_refresh


class TableActionButton(QToolButton):
    def __init__(
        self,
        icon_name: str,
        tooltip: str,
        on_click: Optional[Callable[[], None]] = None,
        parent=None,
    ):
        super().__init__(parent)
        self._icon_name = icon_name
        self.setObjectName("TableActionButton")
        self.setToolTip(tooltip)
        self.setCursor(Qt.PointingHandCursor)
        self.setIconSize(table_action_icon_size())
        self.setIcon(icon(icon_name))
        if on_click:
            self.clicked.connect(on_click)
        register_icon_refresh(self)

    def refresh_icon(self):
        """Call after a theme switch so the glyph color stays correct."""
        self.setIcon(icon(self._icon_name))
