from __future__ import annotations
from PySide2.QtWidgets import (
    QDialog, QFormLayout, QLabel, QDoubleSpinBox,
    QLineEdit, QDialogButtonBox, QMessageBox
)


class PaymentDialog(QDialog):
    """
    Small dialog used from the Pending Bills window to record a new
    payment against a sale that still has a due_amount > 0.
    """

    def __init__(self, sale, parent=None):
        super().__init__(parent)
        self.sale = sale
        self.setWindowTitle(f"Add Payment — Invoice #{sale.id}")
        self.setMinimumWidth(360)
        self._setup_ui()

    def _setup_ui(self):
        layout = QFormLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(24, 24, 24, 24)

        layout.addRow("Customer", QLabel(self.sale.customer_name or "Walk-in"))
        layout.addRow("Total Amount", QLabel(f"₹{self.sale.total_amount:.2f}"))
        layout.addRow("Already Paid", QLabel(f"₹{self.sale.paid_amount:.2f}"))

        due_label = QLabel(f"₹{self.sale.due_amount:.2f}")
        due_label.setStyleSheet("font-weight: bold; color: #f38ba8;")
        layout.addRow("Balance Due", due_label)

        self.amount_input = QDoubleSpinBox()
        self.amount_input.setPrefix("₹")
        self.amount_input.setDecimals(2)
        self.amount_input.setMinimum(0.01)
        self.amount_input.setMaximum(max(self.sale.due_amount, 0.01))
        self.amount_input.setValue(self.sale.due_amount)  # default: pay off in full
        layout.addRow("Payment Amount *", self.amount_input)

        self.note_input = QLineEdit()
        self.note_input.setPlaceholderText("Optional note (e.g. cash / UPI)")
        layout.addRow("Note", self.note_input)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def _on_accept(self):
        if self.amount_input.value() <= 0:
            QMessageBox.warning(self, "Invalid", "Enter an amount greater than zero.")
            return
        self.accept()

    def get_data(self) -> dict:
        return {
            "amount": self.amount_input.value(),
            "note": self.note_input.text().strip(),
        }


