from __future__ import annotations
import hashlib
_original_md5 = hashlib.md5
def _md5_compat(*args, **kwargs):
    kwargs.pop("usedforsecurity", None)
    return _original_md5(*args, **kwargs)
hashlib.md5 = _md5_compat
import sys
from PySide2.QtWidgets import QApplication
from app.database.connection import init_db
from app.utils.logger import setup_logger
from app.utils.theme_manager import ThemeManager
from app.utils.font_manager import FontManager
from app.services.auth_service import AuthService
from app.services.backup_service import BackupService


def main():
    setup_logger()
    init_db()

    # ── Setup all backup triggers ──
    BackupService.setup()

    app = QApplication(sys.argv)
    app.setApplicationName("Dindigul School Point")

    # Load the bundled Poppins font BEFORE any window is created, so
    # every widget picks it up as the application default font instead
    # of relying on Poppins being installed system-wide.
    FontManager.load()

    # Stop backup thread cleanly when app quits
    app.aboutToQuit.connect(BackupService.stop)

    ThemeManager.apply("dark")

    cached = AuthService.auto_login()
    if cached:
        _open_dashboard(cached)
    else:
        _open_login()

    sys.exit(app.exec_())


def _open_login():
    from ui.windows.login_window import LoginWindow
    login = LoginWindow()
    login.login_success.connect(_on_login_success)
    login.show()
    main._login = login


def _on_login_success(user_data: dict):
    if hasattr(main, "_login") and main._login:
        main._login.close()
        main._login = None
    _open_dashboard(user_data)


def _open_dashboard(user_data: dict):
    from ui.windows.dashboard_window import DashboardWindow
    dashboard = DashboardWindow(user_data)
    dashboard.showMaximized()
    main._dashboard = dashboard


if __name__ == "__main__":
    main()


