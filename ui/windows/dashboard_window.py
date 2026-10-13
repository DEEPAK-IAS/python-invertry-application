from __future__ import annotations
from PySide2.QtWidgets import (QMainWindow, QWidget, QHBoxLayout,
                                QVBoxLayout, QLabel, QStatusBar,
                                QStackedWidget, QMessageBox)
from PySide2.QtCore import Qt, QTimer
from datetime import datetime
from ui.widgets.sidebar import Sidebar
from ui.widgets.theme_toggle import ThemeToggleButton
from ui.windows.product_window import ProductWindow
from ui.windows.sales_window import SalesWindow
from ui.windows.pending_bills_window import PendingBillsWindow
from ui.windows.customer_window import CustomerWindow
from ui.windows.supplier_window import SupplierWindow
from ui.windows.reports_window import ReportsWindow
from ui.windows.home_page import HomePage
from ui.windows.settings_window import SettingsWindow
from app.services.auth_service import AuthService

class DashboardWindow(QMainWindow):
    def __init__(self, user_data: dict):
        super().__init__()
        self.user_data = user_data
        # Dynamic: reads the company name the user actually registered,
        # instead of a fixed business name baked into the app.
        company_name = self.user_data.get("company_name") or "Stock Manager"
        self.setWindowTitle(company_name)
        self.setMinimumSize(1280, 720)
        self._setup_ui()
        self._setup_statusbar()
        self._setup_clock()

    def _setup_ui(self):
        central = QWidget()
        root_layout = QHBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        self.sidebar = Sidebar(self.user_data)
        self.sidebar.page_changed.connect(self._switch_page)
        self.sidebar.logout_requested.connect(self._logout)
        root_layout.addWidget(self.sidebar)

        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        # Top bar
        top_bar = QWidget()
        top_bar.setObjectName("TopBar")
        top_bar.setFixedHeight(78)
        top_bar_layout = QHBoxLayout(top_bar)
        top_bar_layout.setContentsMargins(24, 0, 24, 0)

        self.page_title = QLabel("Dashboard")
        self.page_title.setObjectName("TitleLabel")
        self.clock_label = QLabel()
        self.clock_label.setObjectName("SubtitleLabel")
        self.theme_btn = ThemeToggleButton()

        top_bar_layout.addWidget(self.page_title)
        top_bar_layout.addStretch()
        top_bar_layout.addWidget(self.clock_label)
        top_bar_layout.addSpacing(16)
        top_bar_layout.addWidget(self.theme_btn)

        # Initialize Windows
        self.home_page = HomePage(self.user_data)
        self.product_window = ProductWindow()
        self.reports_window = ReportsWindow(self.user_data)
        
        company_name = self.user_data.get("company_name", "DINDIGUL SCHOOL POINT")
        
        self.sales_window = SalesWindow(company_name=company_name, user_data=self.user_data)
        self.pending_bills_window = PendingBillsWindow(self.user_data)

        self.home_page.navigate_requested.connect(self._switch_page)

        self.stack = QStackedWidget()
        self.stack.addWidget(self.home_page)            # 0
        self.stack.addWidget(self.product_window)        # 1
        self.stack.addWidget(self.sales_window)          # 2
        self.stack.addWidget(self.pending_bills_window)  # 3
        self.stack.addWidget(CustomerWindow())           # 4
        self.stack.addWidget(SupplierWindow())           # 5
        self.stack.addWidget(self.reports_window)        # 6
        self.stack.addWidget(SettingsWindow(self.user_data))  # 7
        
        self.product_window.product_saved.connect(self.reports_window.refresh)

        right_layout.addWidget(top_bar)
        right_layout.addWidget(self.stack)
        root_layout.addWidget(right)
        self.setCentralWidget(central)

    def closeEvent(self, event):
        """Intercepts the close action when clicking the 'X' icon to prompt user confirmation."""
        reply = QMessageBox.question(
            self, 
            "Confirm Exit", 
            "Are you sure you want to close the application?",
            QMessageBox.Yes | QMessageBox.No, 
            QMessageBox.No  # Default choice is 'No' for safety
        )
        
        if reply == QMessageBox.Yes:
            event.accept()  # Allows the app to close and triggers exit backups
        else:
            event.ignore()  # Keeps the window open and active

    def _switch_page(self, index: int, title: str):
        self.stack.setCurrentIndex(index)
        self.page_title.setText(title)
        
        current_widget = self.stack.widget(index)
        
        if hasattr(current_widget, "refresh"):
            current_widget.refresh()
        elif hasattr(current_widget, "load_products"):
            current_widget.load_products()
        elif hasattr(current_widget, "_load_products"):
            current_widget._load_products()

    def _setup_clock(self):
        timer = QTimer(self)
        timer.timeout.connect(self._tick)
        timer.start(1000)
        self._tick()

    def _tick(self):
        now = datetime.now().strftime("%A, %d %b %Y   %H:%M:%S")
        self.clock_label.setText(now)

    def _logout(self):
        if QMessageBox.question(self, "Logout", "Are you sure you want to logout?") == QMessageBox.Yes:
            AuthService.logout()
            self.close()
            import main as m
            m._open_login()

    def _setup_statusbar(self):
        bar = QStatusBar()
        user = self.user_data.get("username", "")
        company_name = self.user_data.get("company_name") or "Stock Manager"
        bar.showMessage(f"Logged in as: @{user}  |  {company_name} v1.0.0")
        self.setStatusBar(bar)