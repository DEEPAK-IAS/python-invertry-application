from __future__ import annotations
from PySide2.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QMessageBox,
    QFileDialog, QLabel, QDialog, QFormLayout,
    QLineEdit, QDialogButtonBox, QInputDialog, QComboBox,
    QHBoxLayout,
)
from app.services.backup_service import BackupService
from app.config.settings import BACKUP_DIR
from app.database.connection import get_session
from app.models.user import User
from app.design.icons import icon


class CompanyUpdateDialog(QDialog):
    def __init__(self, current_data):
        super().__init__()
        self.setWindowTitle("Update Company Details")
        layout = QFormLayout(self)
        self.name_input = QLineEdit(current_data.get("company_name", ""))
        self.addr_input = QLineEdit(current_data.get("company_address", ""))
        self.gst_input = QLineEdit(current_data.get("company_gst", ""))   # ← NEW
        self.gst_input.setPlaceholderText("e.g. 29ABCDE1234F1Z5")         # ← NEW
        self.phone_input = QLineEdit(current_data.get("company_phone", ""))   # ← NEW PHONE
        self.phone_input.setPlaceholderText("e.g. 123123123123") 

        # ── Company logo: typed/pasted path, with an optional Browse
        # button as a convenience -- the path itself is what gets saved
        # and later read by the PDF generator, not an uploaded copy of
        # the file, so it must stay valid on this machine.
        logo_row = QHBoxLayout()
        self.logo_input = QLineEdit(current_data.get("company_logo_path", ""))
        self.logo_input.setPlaceholderText(r"e.g. C:\StockManager\logo.png")
        browse_btn = QPushButton("Browse")
        browse_btn.setObjectName("SmallButton")
        browse_btn.clicked.connect(self._browse_logo)
        logo_row.addWidget(self.logo_input)
        logo_row.addWidget(browse_btn)

        self.printer_combo = QComboBox()                                   # ← NEW PRINTER
        self._populate_printers(current_data.get("preferred_printer", ""))  # ← NEW PRINTER
        
        layout.addRow("Company Name:", self.name_input)
        layout.addRow("Address:", self.addr_input)
        layout.addRow("GST Number:", self.gst_input)   # ← NEW
        layout.addRow("Phone Number:", self.phone_input)
        layout.addRow("Logo Path:", logo_row)
        layout.addRow("Printer:", self.printer_combo)                      # ← NEW PRINTER

        btn = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn.accepted.connect(self.accept)
        btn.rejected.connect(self.reject)
        layout.addRow(btn)

    def _browse_logo(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Company Logo", "", "Images (*.png *.jpg *.jpeg)"
        )
        if path:
            self.logo_input.setText(path)

    def get_data(self):
        return {
            "company_name": self.name_input.text().strip(),
            "company_address": self.addr_input.text().strip(),
            "company_gst": self.gst_input.text().strip(),                  # ← NEW
            "company_phone": self.phone_input.text().strip(),              # ← NEW PHONE
            "company_logo_path": self.logo_input.text().strip(),
            "preferred_printer": (self.printer_combo.currentText()
                                   if self.printer_combo.currentText() != "Use Windows Default"
                                   else ""),                                # ← NEW PRINTER
        }
        
    def _populate_printers(self, saved_printer: str):
        self.printer_combo.addItem("Use Windows Default")
        try:
            import win32print
            printers = win32print.EnumPrinters(
                win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS
            )
            for p in printers:
                self.printer_combo.addItem(p[2])  # printer name
        except Exception:
            pass
        if saved_printer:
            idx = self.printer_combo.findText(saved_printer)
            if idx >= 0:
                self.printer_combo.setCurrentIndex(idx)


class SettingsWindow(QWidget):
    def __init__(self, user_data):
        super().__init__()
        self.user_data = user_data
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(15)

        title = QLabel("System Settings")
        title.setObjectName("PageTitle")
        layout.addWidget(title)

        # Database Management
        subtitle = QLabel("Database Management")
        subtitle.setObjectName("CardTitle")
        layout.addWidget(subtitle)

        btn_backup = QPushButton(" Create Backup")
        btn_backup.setObjectName("PrimaryButton")
        btn_backup.setIcon(icon("backup", on_accent=True))
        btn_backup.clicked.connect(self._manual_backup)

        btn_restore = QPushButton(" Restore Backup")
        btn_restore.setObjectName("WarningButton")
        btn_restore.setIcon(icon("download"))
        btn_restore.clicked.connect(self._restore_backup)

        layout.addWidget(btn_backup)
        layout.addWidget(btn_restore)

        # Company Details
        layout.addSpacing(20)
        comp_subtitle = QLabel("Company Information")
        comp_subtitle.setObjectName("CardTitle")
        layout.addWidget(comp_subtitle)

        # ── Show current GST number as a read-only label ──────────────── NEW ──
        self.gst_display = QLabel(f"GST Number: {user_data.get('company_gst') or 'Not set'}")
        self.phone_display = QLabel(f"Phone Number: {user_data.get('company_phone') or 'Not set'}")
        layout.addWidget(self.gst_display)
        layout.addWidget(self.phone_display)
        # ─────────────────────────────────────────────────────────────────────

        btn_update_company = QPushButton(" Update Company Details")
        btn_update_company.setIcon(icon("building"))
        btn_update_company.clicked.connect(self._handle_company_update)
        layout.addWidget(btn_update_company)

        layout.addStretch()

    def _handle_company_update(self):
        password, ok = QInputDialog.getText(
            self, "Authentication", "Enter your password to continue:",
            QLineEdit.Password,
        )
        if not ok or not password:
            return

        from app.utils.security import verify_password

        session = get_session()
        try:
            user = session.query(User).filter(User.id == self.user_data["id"]).first()
            if not user or not verify_password(password, user.password_hash):
                QMessageBox.critical(self, "Access Denied", "Incorrect password.")
                return
        finally:
            session.close()

        dialog = CompanyUpdateDialog(self.user_data)
        if dialog.exec():
            new_data = dialog.get_data()
            self._save_company_details(new_data)

    def _save_company_details(self, data):
        session = get_session()
        try:
            user = session.query(User).filter(User.id == self.user_data["id"]).first()
            if user:
                user.company_name = data["company_name"]
                user.company_address = data["company_address"]
                user.company_gst = data["company_gst"]                    # ← NEW
                user.company_phone = data["company_phone"]                # ← NEW PHONE
                user.company_logo_path = data["company_logo_path"]
                user.preferred_printer = data["preferred_printer"]         # ← NEW PRINTER
                session.commit()
                self.user_data.update(data)

                from app.services.auth_service import AuthService
                AuthService.refresh_cached_session(self.user_data)
                
                # ── Refresh the GST display label ──────────────────────── NEW ──
                self.gst_display.setText(
                    f"GST Number: {data.get('company_gst') or 'Not set'}"
                )
                self.phone_display.setText(
                    f"Phone Number: {data.get('company_phone') or 'Not set'}"
                )
                # ─────────────────────────────────────────────────────────────
                QMessageBox.information(self, "Success", "Company details updated!")
        except Exception as e:
            session.rollback()
            QMessageBox.critical(self, "Error", f"Failed to save: {str(e)}")
        finally:
            session.close()

    def _manual_backup(self):
        path = BackupService.manual_backup()
        if path:
            QMessageBox.information(self, "Backup Successful", f"Backup saved:\n{path}")
        else:
            QMessageBox.warning(self, "Backup Failed", "Unable to create backup.")

    def _restore_backup(self):
        from PySide2.QtWidgets import QApplication

        path, _ = QFileDialog.getOpenFileName(
            self, "Select Backup File", BACKUP_DIR, "*.db"
        )
        if not path:
            return

        reply = QMessageBox.question(
            self, "Restore",
            "This will overwrite the current database. Continue?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            if BackupService.restore(path):
                QMessageBox.information(
                    self, "Restore Successful",
                    "Database restored. The application will now restart.",
                )
                QApplication.quit()

