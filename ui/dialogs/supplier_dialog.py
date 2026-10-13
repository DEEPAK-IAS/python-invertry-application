from __future__ import annotations
from PySide2.QtWidgets import (QDialog, QFormLayout, QLineEdit,
                                QDialogButtonBox)

class SupplierDialog(QDialog):
    def __init__(self, parent=None, supplier=None):
        super().__init__(parent)
        self.setWindowTitle("Add Supplier" if not supplier else "Edit Supplier")
        self.setMinimumWidth(400)
        self._setup_ui()
        if supplier:
            self._populate(supplier)

    def _setup_ui(self):
        layout = QFormLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(24, 24, 24, 24)

        self.name_input    = QLineEdit()
        self.contact_input = QLineEdit()
        self.email_input   = QLineEdit()
        self.phone_input   = QLineEdit()

        layout.addRow("Company Name *", self.name_input)
        layout.addRow("Contact Person", self.contact_input)
        layout.addRow("Email",          self.email_input)
        layout.addRow("Phone",          self.phone_input)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def _populate(self, s):
        self.name_input.setText(s.get("name", ""))
        self.contact_input.setText(s.get("contact_name", ""))
        self.email_input.setText(s.get("email", ""))
        self.phone_input.setText(s.get("phone", ""))

    def get_data(self) -> dict:
        return {
            "name":         self.name_input.text().strip(),
            "contact_name": self.contact_input.text().strip() or None,
            "email":        self.email_input.text().strip() or None,
            "phone":        self.phone_input.text().strip() or None,
        }


