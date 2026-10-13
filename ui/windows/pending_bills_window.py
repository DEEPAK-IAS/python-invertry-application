from __future__ import annotations
import os
import sys
from PySide2.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox,
)
from PySide2.QtCore import Qt

from app.database.connection import SessionLocal
from app.repositories.sale_repository import SaleRepository
from app.services.billing_service import BillingService
from app.utils.pdf_generator import generate_invoice_pdf, generate_payment_receipt_pdf
from ui.dialogs.payment_dialog import PaymentDialog
from ui.dialogs.sale_history_dialog import SaleHistoryDialog
from ui.widgets.table_action_button import TableActionButton
from app.design.icons import icon


class PendingBillsWindow(QWidget):
    """
    Shows every sale that still has a due_amount > 0 (i.e. the customer
    only paid part of the bill at checkout) and lets the user record
    further payments until the bill is fully settled.

    Business logic unchanged: this still calls BillingService.record_payment
    for every payment and never creates a second Sale/duplicate inventory
    movement. What's new is purely presentational/workflow:
      - "Pay"     records a payment, then offers a *Payment Receipt* PDF
                  (a short document for what was just paid) instead of
                  silently reprinting the whole invoice.
      - "History" shows every payment made against this bill so far,
                  plus the original line items, in one place.
      - "Reprint" regenerates the ORIGINAL invoice PDF unchanged (for
                  when a customer lost their copy) -- kept as a clearly
                  separate action from recording/receiving a payment.
    """

    COLUMNS = ["Invoice #", "Customer", "Phone", "Date",
               "Total", "Paid", "Due", "Status", "Actions"]

    def __init__(self, user_data: dict | None = None):
        super().__init__()
        self.user_data = user_data or {}
        self.setWindowTitle("Pending Bills")
        self._setup_ui()
        self.refresh()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 24)
        layout.setSpacing(14)

        header_layout = QHBoxLayout()
        title = QLabel("Pending Bills")
        title.setObjectName("PageTitle")
        header_layout.addWidget(title)
        header_layout.addStretch()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by customer name or phone...")
        self.search_input.setMaximumWidth(280)
        self.search_input.textChanged.connect(self._apply_filter)
        header_layout.addWidget(self.search_input)

        refresh_btn = QPushButton(" Refresh")
        refresh_btn.setIcon(icon("refresh"))
        refresh_btn.clicked.connect(self.refresh)
        header_layout.addWidget(refresh_btn)
        layout.addLayout(header_layout)

        self.total_due_label = QLabel("Total Outstanding: \u20b90.00")
        self.total_due_label.setObjectName("StatusPillDanger")
        layout.addWidget(self.total_due_label)

        self.table = QTableWidget(0, len(self.COLUMNS))
        self.table.setHorizontalHeaderLabels(self.COLUMNS)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.setColumnWidth(1, 150)
        self.table.setColumnWidth(8, 150)
        self.table.verticalHeader().setDefaultSectionSize(48)
        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table)

    def refresh(self):
        with SessionLocal() as db:
            self._pending_sales = SaleRepository(db).get_pending_bills()
        self._render(self._pending_sales)

    def _apply_filter(self, text):
        text = text.strip().lower()
        if not text:
            self._render(self._pending_sales)
            return
        filtered = [
            s for s in self._pending_sales
            if text in (s.customer_name or "").lower() or text in (s.customer_phone or "")
        ]
        self._render(filtered)

    def _render(self, sales):
        self.table.setRowCount(0)
        total_due = 0.0

        for sale in sales:
            row = self.table.rowCount()
            self.table.insertRow(row)

            self.table.setItem(row, 0, QTableWidgetItem(f"#{sale.id}"))
            self.table.setItem(row, 1, QTableWidgetItem(sale.customer_name or "Walk-in"))
            self.table.setItem(row, 2, QTableWidgetItem(sale.customer_phone or ""))
            self.table.setItem(row, 3, QTableWidgetItem(
                sale.date_created.strftime("%Y-%m-%d %H:%M") if sale.date_created else ""
            ))
            self.table.setItem(row, 4, QTableWidgetItem(f"\u20b9{sale.total_amount:.2f}"))
            self.table.setItem(row, 5, QTableWidgetItem(f"\u20b9{sale.paid_amount:.2f}"))

            due_item = QTableWidgetItem(f"\u20b9{sale.due_amount:.2f}")
            self.table.setItem(row, 6, due_item)

            status_item = QTableWidgetItem(sale.payment_status)
            self.table.setItem(row, 7, status_item)

            self.table.setCellWidget(row, 8, self._build_actions_cell(sale.id))

            total_due += sale.due_amount

        self.total_due_label.setText(f"Total Outstanding: \u20b9{total_due:,.2f}")

    def _build_actions_cell(self, sale_id: int) -> QWidget:
        """One consistent set of small icon buttons per row instead of a
        single hand-styled 'Add Payment' button -- fixes the inconsistent
        table-action sizing/icons complaint."""
        cell = QWidget()
        row_layout = QHBoxLayout(cell)
        row_layout.setContentsMargins(4, 2, 4, 2)
        row_layout.setSpacing(6)

        pay_btn = TableActionButton("payment", "Record a payment", on_click=lambda: self._open_payment_dialog(sale_id))
        history_btn = TableActionButton("history", "View payment history & items", on_click=lambda: self._open_history(sale_id))
        reprint_btn = TableActionButton("reprint", "Reprint original invoice", on_click=lambda: self._reprint_invoice(sale_id))

        row_layout.addWidget(pay_btn)
        row_layout.addWidget(history_btn)
        row_layout.addWidget(reprint_btn)
        row_layout.addStretch()
        return cell

    def _open_payment_dialog(self, sale_id: int):
        with SessionLocal() as db:
            sale = SaleRepository(db).get_by_id(sale_id)
            if not sale:
                QMessageBox.warning(self, "Not Found", "This invoice no longer exists.")
                self.refresh()
                return

            dialog = PaymentDialog(sale, parent=self)
            if dialog.exec():
                data = dialog.get_data()
                try:
                    updated_sale = BillingService.record_payment(
                        db, sale_id, data["amount"], data["note"]
                    )
                except Exception as e:
                    QMessageBox.critical(self, "Error", str(e))
                    self.refresh()
                    return

                # Offer a PAYMENT RECEIPT for what was just paid -- this
                # is a separate, smaller document from the invoice, and
                # the invoice itself is never regenerated or altered.
                receipt_choice = QMessageBox.question(
                    self,
                    "Payment Recorded",
                    (
                        f"Payment of \u20b9{data['amount']:.2f} recorded for Invoice #{sale_id}.\n"
                        f"Remaining due: \u20b9{updated_sale.due_amount:.2f}\n\n"
                        "Generate a payment receipt for this installment?"
                    ),
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.Yes,
                )
                if receipt_choice == QMessageBox.Yes:
                    try:
                        receipt_path = generate_payment_receipt_pdf(
                            updated_sale,
                            payment_amount=data["amount"],
                            payment_note=data["note"],
                            company_name=self.user_data.get("company_name", "Dindigul School Point"),
                            company_address=self.user_data.get("company_address", ""),
                            company_gst=self.user_data.get("company_gst", ""),
                            company_phone=self.user_data.get("company_phone", ""),
                            company_logo_path=self.user_data.get("company_logo_path", ""),
                        )
                        self._open_file(receipt_path)
                    except Exception as e:
                        QMessageBox.warning(self, "Receipt", f"Payment was recorded, but the receipt could not be generated: {e}")

        self.refresh()

    def _open_history(self, sale_id: int):
        with SessionLocal() as db:
            sale = SaleRepository(db).get_by_id(sale_id)
            if not sale:
                QMessageBox.warning(self, "Not Found", "This invoice no longer exists.")
                self.refresh()
                return
            dialog = SaleHistoryDialog(sale, parent=self)
            dialog.exec()

    def _reprint_invoice(self, sale_id: int):
        """Regenerates the ORIGINAL invoice PDF (unchanged line items/
        totals) for when a customer needs another copy. This is a
        distinct action from recording a payment and never touches
        paid_amount/due_amount/payment_status."""
        with SessionLocal() as db:
            sale = SaleRepository(db).get_by_id(sale_id)
            if not sale:
                QMessageBox.warning(self, "Not Found", "This invoice no longer exists.")
                self.refresh()
                return
            try:
                pdf_path = generate_invoice_pdf(
                    sale,
                    company_name=self.user_data.get("company_name", "Dindigul School Point"),
                    company_address=self.user_data.get("company_address", ""),
                    company_gst=self.user_data.get("company_gst", ""),
                    company_phone=self.user_data.get("company_phone", ""),
                    company_logo_path=self.user_data.get("company_logo_path", ""),
                )
                self._open_file(pdf_path)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not reprint invoice: {e}")

    @staticmethod
    def _open_file(path: str):
        try:
            if sys.platform.startswith("win"):
                os.startfile(path)
            else:
                # Dev-environment fallback (Windows-only in production)
                QMessageBox.information(None, "Saved", f"Saved to: {path}")
        except Exception:
            pass
