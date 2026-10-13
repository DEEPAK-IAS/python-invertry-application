from __future__ import annotations
from PySide2.QtWidgets import (QDialog, QFormLayout, QLineEdit,
                                QDialogButtonBox, QTextEdit)

class CustomerDialog(QDialog):
    def __init__(self, parent=None, customer=None):
        super().__init__(parent)
        self.setWindowTitle("Add Customer" if not customer else "Edit Customer")
        self.setMinimumWidth(400)
        self._setup_ui()
        if customer:
            self._populate(customer)

    def _setup_ui(self):
        layout = QFormLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(24, 24, 24, 24)

        self.name_input    = QLineEdit()
        self.email_input   = QLineEdit()
        self.phone_input   = QLineEdit()
        self.address_input = QTextEdit()
        self.address_input.setMaximumHeight(80)

        layout.addRow("Name *",   self.name_input)
        layout.addRow("Email",    self.email_input)
        layout.addRow("Phone",    self.phone_input)
        layout.addRow("Address",  self.address_input)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def _populate(self, c):
        self.name_input.setText(c.get("name", ""))
        self.email_input.setText(c.get("email", ""))
        self.phone_input.setText(c.get("phone", ""))
        self.address_input.setPlainText(c.get("address", ""))

    def get_data(self) -> dict:
        return {
            "name":    self.name_input.text().strip(),
            "email":   self.email_input.text().strip() or None,
            "phone":   self.phone_input.text().strip() or None,
            "address": self.address_input.toPlainText().strip() or None,
        }


