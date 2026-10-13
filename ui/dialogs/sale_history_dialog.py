from __future__ import annotations
from PySide2.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QHeaderView, QDialogButtonBox, QFrame, QWidget,
)
from PySide2.QtCore import Qt


class SaleHistoryDialog(QDialog):
    """
    Read-only detail view for one invoice: the items originally sold,
    plus every payment recorded against it (each Payment row, oldest
    first) with the running total. This is what makes purchase items
    visible without requiring "reprint bill" as the only way to see
    them, and is reused both from Pending Bills and from the Customer
    purchase-history screen.

    Does not modify the Sale/Payment data in any way -- display only.
    """

    def __init__(self, sale, parent=None):
        super().__init__(parent)
        self.sale = sale
        self.setWindowTitle(f"Invoice #{sale.id} \u2014 Details")
        self.setMinimumSize(900, 750)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        # ── Header summary ──
        header = QFrame()
        header.setObjectName("SettingsCard")
        h_layout = QVBoxLayout(header)
        h_layout.setContentsMargins(16, 12, 16, 12)
        h_layout.setSpacing(4)

        h_layout.addWidget(self._row("Customer", self.sale.customer_name or "Walk-in"))
        h_layout.addWidget(self._row("Phone", self.sale.customer_phone or "-"))
        h_layout.addWidget(self._row(
            "Date",
            self.sale.date_created.strftime("%d-%m-%Y %H:%M") if self.sale.date_created else "-",
        ))
        h_layout.addWidget(self._row("Total", f"\u20b9{self.sale.total_amount:.2f}"))
        h_layout.addWidget(self._row("Paid", f"\u20b9{self.sale.paid_amount:.2f}"))
        h_layout.addWidget(self._row("Due", f"\u20b9{self.sale.due_amount:.2f}"))
        h_layout.addWidget(self._row("Status", self.sale.payment_status))
        layout.addWidget(header)
        
        
        # ── Payment history ──
        layout.addWidget(self._section_title("Payment History"))
        payments_table = QTableWidget(0, 3)
        payments_table.setHorizontalHeaderLabels(["Date", "Amount", "Note"])
        payments_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        payments_table.setEditTriggers(QTableWidget.NoEditTriggers)
        payments_table.verticalHeader().setVisible(False)
        payments = sorted(
            getattr(self.sale, "payments", []) or [],
            key=lambda p: p.payment_date or 0,
        )
        payments_table.setRowCount(len(payments))
        for row, pay in enumerate(payments):
            payments_table.setItem(row, 0, QTableWidgetItem(
                pay.payment_date.strftime("%d-%m-%Y %H:%M") if pay.payment_date else "-"
            ))
            payments_table.setItem(row, 1, QTableWidgetItem(f"\u20b9{pay.amount:.2f}"))
            payments_table.setItem(row, 2, QTableWidgetItem(pay.note or ""))
        layout.addWidget(payments_table)

        # ── Line items ──
        layout.addWidget(self._section_title("Items Purchased"))
        items_table = QTableWidget(0, 4)
        items_table.setHorizontalHeaderLabels(["Product", "Qty", "Unit Price", "Total"])
        items_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        items_table.setEditTriggers(QTableWidget.NoEditTriggers)
        items_table.verticalHeader().setVisible(False)
        items = getattr(self.sale, "items", []) or []
        items_table.setRowCount(len(items))
        for row, item in enumerate(items):
            name = item.product_name + (f" ({item.size})" if getattr(item, "size", None) else "")
            items_table.setItem(row, 0, QTableWidgetItem(name))
            items_table.setItem(row, 1, QTableWidgetItem(str(item.quantity)))
            items_table.setItem(row, 2, QTableWidgetItem(f"\u20b9{item.unit_price:.2f}"))
            items_table.setItem(row, 3, QTableWidgetItem(f"\u20b9{item.total_price:.2f}"))
        layout.addWidget(items_table)


        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.rejected.connect(self.reject)
        buttons.accepted.connect(self.accept)
        buttons.button(QDialogButtonBox.Close).clicked.connect(self.accept)
        layout.addWidget(buttons)

    @staticmethod
    def _row(label: str, value: str) -> QFrame:
        wrapper = QFrame()
        row_layout = QHBoxLayout(wrapper)
        row_layout.setContentsMargins(0, 0, 0, 0)
        lbl = QLabel(label)
        lbl.setObjectName("FieldLabel")
        lbl.setFixedWidth(90)
        val = QLabel(value)
        val.setStyleSheet("font-weight: 600;")
        row_layout.addWidget(lbl)
        row_layout.addWidget(val)
        row_layout.addStretch()
        return wrapper

    @staticmethod
    def _section_title(text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet("font-weight: 700; font-size: 15px; margin-top: 4px;")
        return lbl
