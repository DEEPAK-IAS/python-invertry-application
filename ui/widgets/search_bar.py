from __future__ import annotations
from PySide2.QtWidgets import QLineEdit
from PySide2.QtGui import QIcon

class SearchBar(QLineEdit):
    def __init__(self):
        super().__init__()
        self.setPlaceholderText("Search products...")
        self.setMinimumWidth(300)
        self.setMinimumHeight(44)


