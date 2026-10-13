from __future__ import annotations
from PySide2.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QHeaderView, QDialogButtonBox, QFrame,
)

from app.database.connection import SessionLocal
from app.repositories.sale_repository import SaleRepository
from ui.dialogs.sale_history_dialog import SaleHistoryDialog


class CustomerHistoryDialog(QDialog):
    """
    Customer detail screen: summary totals (purchases / paid / pending)
    plus every invoice for that customer, with the ability to open any
    invoice's full item + payment breakdown directly -- without going
    through a "reprint bill" flow first.

    Read-only. Looks sales up by the customer's phone number via
    SaleRepository.get_by_customer_phone(), which mirrors how
    BillingService.process_checkout already links a Sale to a Customer
    (this schema has no Sale.customer_id FK -- phone is the join key).
    Does not change any existing business logic.
    """

    COLUMNS = ["Invoice #", "Date", "Items", "Total", "Paid", "Due", "Status"]

    def __init__(self, customer, parent=None):
        super().__init__(parent)
        self.customer = customer
        self.setWindowTitle(f"Purchase History \u2014 {customer.name}")
        self.setMinimumSize(700, 560)
        self._sales = []
        self._setup_ui()
        self._load()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        # -- Customer summary card --
        card = QFrame()
        card.setObjectName("SettingsCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(16, 12, 16, 12)
        card_layout.setSpacing(4)

        name_lbl = QLabel(self.customer.name)
        name_lbl.setStyleSheet("font-size: 18px; font-weight: 700;")
        card_layout.addWidget(name_lbl)
        card_layout.addWidget(self._info_row("Phone", self.customer.phone or "-"))
        card_layout.addWidget(self._info_row("Address", self.customer.address or "-"))
        layout.addWidget(card)

        # -- Totals row --
        totals_layout = QHBoxLayout()
        self.total_purchases_lbl = self._stat("Total Purchases", "\u20b90.00")
        self.total_paid_lbl = self._stat("Total Paid", "\u20b90.00")
        self.total_pending_lbl = self._stat("Total Pending", "\u20b90.00")
        totals_layout.addWidget(self.total_purchases_lbl["frame"])
        totals_layout.addWidget(self.total_paid_lbl["frame"])
        totals_layout.addWidget(self.total_pending_lbl["frame"])
        layout.addLayout(totals_layout)

        # -- Purchase history table --
        history_title = QLabel("Purchase History")
        history_title.setStyleSheet("font-weight: 700; font-size: 15px; margin-top: 6px;")
        layout.addWidget(history_title)

        self.table = QTableWidget(0, len(self.COLUMNS))
        self.table.setHorizontalHeaderLabels(self.COLUMNS)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.doubleClicked.connect(self._open_selected_invoice)
        layout.addWidget(self.table)

        hint = QLabel("Double-click an invoice to see its items and full payment history.")
        hint.setObjectName("CardDescription")
        layout.addWidget(hint)

        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.rejected.connect(self.reject)
        buttons.button(QDialogButtonBox.Close).clicked.connect(self.accept)
        layout.addWidget(buttons)

    def _load(self):
        with SessionLocal() as db:
            self._sales = SaleRepository(db).get_by_customer_phone(self.customer.phone)

        total_purchases = sum(s.total_amount for s in self._sales)
        total_paid = sum(s.paid_amount for s in self._sales)
        total_pending = sum(s.due_amount for s in self._sales)

        self.total_purchases_lbl["val"].setText(f"\u20b9{total_purchases:,.2f}")
        self.total_paid_lbl["val"].setText(f"\u20b9{total_paid:,.2f}")
        self.total_pending_lbl["val"].setText(f"\u20b9{total_pending:,.2f}")

        self.table.setRowCount(len(self._sales))
        for row, sale in enumerate(self._sales):
            item_count = len(getattr(sale, "items", []) or [])
            self.table.setItem(row, 0, QTableWidgetItem(f"#{sale.id}"))
            self.table.setItem(row, 1, QTableWidgetItem(
                sale.date_created.strftime("%d-%m-%Y %H:%M") if sale.date_created else "-"
            ))
            self.table.setItem(row, 2, QTableWidgetItem(f"{item_count} item(s)"))
            self.table.setItem(row, 3, QTableWidgetItem(f"\u20b9{sale.total_amount:.2f}"))
            self.table.setItem(row, 4, QTableWidgetItem(f"\u20b9{sale.paid_amount:.2f}"))
            self.table.setItem(row, 5, QTableWidgetItem(f"\u20b9{sale.due_amount:.2f}"))
            self.table.setItem(row, 6, QTableWidgetItem(sale.payment_status))

    def _open_selected_invoice(self):
        row = self.table.currentRow()
        if row < 0 or row >= len(self._sales):
            return
        sale = self._sales[row]
        with SessionLocal() as db:
            fresh_sale = SaleRepository(db).get_by_id(sale.id)
            if fresh_sale:
                dialog = SaleHistoryDialog(fresh_sale, parent=self)
                dialog.exec()

    @staticmethod
    def _info_row(label: str, value: str) -> QFrame:
        wrapper = QFrame()
        row_layout = QHBoxLayout(wrapper)
        row_layout.setContentsMargins(0, 0, 0, 0)
        lbl = QLabel(label)
        lbl.setObjectName("FieldLabel")
        lbl.setFixedWidth(80)
        val = QLabel(value)
        row_layout.addWidget(lbl)
        row_layout.addWidget(val)
        row_layout.addStretch()
        return wrapper

    @staticmethod
    def _stat(label: str, value: str) -> dict:
        frame = QFrame()
        frame.setObjectName("StatCard")
        frame.setFixedHeight(64)
        inner = QVBoxLayout(frame)
        inner.setContentsMargins(16, 8, 16, 8)
        val_lbl = QLabel(value)
        val_lbl.setObjectName("StatValue")
        val_lbl.setStyleSheet("font-size: 20px; font-weight: 700;")
        lbl = QLabel(label)
        lbl.setObjectName("StatLabel")
        inner.addWidget(val_lbl)
        inner.addWidget(lbl)
        return {"frame": frame, "val": val_lbl}
