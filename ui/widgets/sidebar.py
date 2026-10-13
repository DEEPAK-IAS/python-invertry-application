from __future__ import annotations
from PySide2.QtWidgets import (QWidget, QVBoxLayout, QPushButton,
                                QLabel, QFrame)
from PySide2.QtCore import Qt, Signal, QSize

from app.design.icons import icon, register_icon_refresh
from app.design.tokens import ButtonSize

# (index, label, icon_name) -- icon is now a themed vector glyph instead
# of an emoji character baked into the label text.
PAGES = [
    (0, "Dashboard", "dashboard"),
    (1, "Products", "products"),
    (2, "Sales", "sales"),
    (3, "Pending Bills", "pending"),
    (4, "Customers", "customers"),
    (5, "Suppliers", "suppliers"),
    (6, "Reports", "reports"),
    (7, "Settings", "settings"),
]


class Sidebar(QWidget):
    page_changed = Signal(int, str)
    logout_requested = Signal()

    def __init__(self, user_data: dict = None):
        super().__init__()

        self.setObjectName("Sidebar")
        # Width now comes from the theme QSS (SIDEBAR_WIDTH token) via
        # #Sidebar { min-width / max-width }, not a hardcoded value here.

        self._buttons = []
        self.user_data = user_data or {}
        self._setup_ui()
        register_icon_refresh(self)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 20, 14, 20)
        layout.setSpacing(6)

        # 1. Company Name Header
        company_name = self.user_data.get("company_name", "Stock Manager PRO")
        title = QLabel(company_name.upper())
        title.setObjectName("SidebarTitle")
        title.setWordWrap(True)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        layout.addSpacing(10)

        # 2. User Info Card
        if self.user_data:
            user_frame = QFrame()
            user_frame.setObjectName("UserCard")

            user_layout = QVBoxLayout(user_frame)
            user_layout.setContentsMargins(12, 10, 12, 10)
            user_layout.setSpacing(2)

            name_lbl = QLabel(self.user_data.get("full_name", "User"))
            name_lbl.setObjectName("UserName")

            uname_lbl = QLabel(f"@{self.user_data.get('username', '')}")
            uname_lbl.setObjectName("UserHandle")

            user_layout.addWidget(name_lbl)
            user_layout.addWidget(uname_lbl)

            layout.addWidget(user_frame)
            layout.addSpacing(6)

        # 3. Navigation Buttons -- one consistent variant (#SidebarButton),
        # sizing/padding/icon-size all come from the theme QSS token
        # (ButtonSize.NAV), not per-button Python overrides.
        nav_icon_size = ButtonSize.NAV["icon"]
        for index, label, icon_name in PAGES:
            btn = QPushButton(f"  {label}")
            btn.setObjectName("SidebarButton")
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setIcon(icon(icon_name))
            btn.setIconSize(QSize(nav_icon_size, nav_icon_size))
            btn._icon_name = icon_name  # used by refresh_icons()

            btn.clicked.connect(
                lambda checked=False, i=index, l=label:
                self._on_click(i, l)
            )

            layout.addWidget(btn)
            self._buttons.append(btn)

        layout.addStretch()

        # 4. Logout Button
        logout_btn = QPushButton("  Logout")
        logout_btn.setObjectName("DangerButton")
        logout_btn.setIcon(icon("logout"))
        logout_btn.setIconSize(QSize(nav_icon_size, nav_icon_size))
        logout_btn.setCursor(Qt.PointingHandCursor)
        logout_btn._icon_name = "logout"
        logout_btn.clicked.connect(lambda checked=False: self.logout_requested.emit())
        layout.addWidget(logout_btn)
        self._logout_btn = logout_btn

        if self._buttons:
            self._buttons[0].setChecked(True)

    def _on_click(self, index, label):
        self.page_changed.emit(index, label)
        for btn in self._buttons:
            is_active = btn.text().strip() == label.strip()
            btn.setChecked(is_active)

    def refresh_icons(self):
        """Called automatically by the icon registry after a theme
        switch, so nav icons keep the correct tint."""
        for btn in self._buttons + [getattr(self, "_logout_btn", None)]:
            if btn is not None and hasattr(btn, "_icon_name"):
                btn.setIcon(icon(btn._icon_name))
