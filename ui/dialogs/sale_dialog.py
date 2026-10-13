from __future__ import annotations
from PySide2.QtWidgets import (QDialog, QFormLayout, QComboBox,
                                QSpinBox, QDialogButtonBox, QLabel,
                                QLineEdit, QHBoxLayout, QVBoxLayout, QWidget)
from PySide2.QtCore import Qt
from app.database.connection import get_session
from app.repositories.product_repository import ProductRepository
from app.repositories.customer_repository import CustomerRepository

class SaleDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("New Sale")
        self.setMinimumWidth(420)
        self._products  = []
        self._customers = []
        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        layout = QFormLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(24, 24, 24, 24)

        self.product_combo  = QComboBox()
        self.customer_combo = QComboBox()
        self.qty_input      = QSpinBox()
        self.qty_input.setMinimum(1)
        self.qty_input.setMaximum(99999)

        self.price_label = QLabel("₹0.00")
        self.price_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.total_label = QLabel("₹0.00")
        self.total_label.setStyleSheet("font-weight: bold; font-size: 16px; color: #a6e3a1;")

        self.note_input = QLineEdit()
        self.note_input.setPlaceholderText("Optional note...")

        self.product_combo.currentIndexChanged.connect(self._update_price)
        self.qty_input.valueChanged.connect(self._update_total)

        layout.addRow("Product *",  self.product_combo)
        layout.addRow("Customer",   self.customer_combo)
        layout.addRow("Quantity *", self.qty_input)
        layout.addRow("Unit Price", self.price_label)
        layout.addRow("Total",      self.total_label)
        layout.addRow("Note",       self.note_input)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def _load_data(self):
        session = get_session()
        self._products  = ProductRepository(session).get_all()
        self._customers = CustomerRepository(session).get_all()
        session.close()

        self.product_combo.addItem("— Select Product —", None)
        for p in self._products:
            self.product_combo.addItem(f"{p.name}  [{p.sku}]  (Stock: {p.stock_qty})", p.id)

        self.customer_combo.addItem("— Walk-in Customer —", None)
        for c in self._customers:
            self.customer_combo.addItem(f"{c.name}", c.id)

    def _update_price(self):
        idx = self.product_combo.currentIndex() - 1
        if 0 <= idx < len(self._products):
            price = self._products[idx].price
            self.price_label.setText(f"₹{price:.2f}")
        else:
            self.price_label.setText("₹0.00")
        self._update_total()

    def _update_total(self):
        idx = self.product_combo.currentIndex() - 1
        if 0 <= idx < len(self._products):
            total = self._products[idx].price * self.qty_input.value()
            self.total_label.setText(f"₹{total:.2f}")
        else:
            self.total_label.setText("₹0.00")

    def get_data(self) -> dict | None:
        pidx = self.product_combo.currentIndex() - 1
        cidx = self.customer_combo.currentIndex() - 1
        if pidx < 0:
            return None
        product     = self._products[pidx]
        customer_id = self._customers[cidx].id if cidx >= 0 else None
        qty         = self.qty_input.value()
        return {
            "product_id":  product.id,
            "product_name": product.name,
            "customer_id": customer_id,
            "quantity":    qty,
            "unit_price":  product.price,
            "total":       product.price * qty,
            "stock_qty":   product.stock_qty,
            "note":        self.note_input.text().strip(),
        }


