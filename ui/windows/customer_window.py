from __future__ import annotations
from PySide2.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                                QPushButton, QTableWidget, QTableWidgetItem,
                                QHeaderView, QMessageBox, QLabel, QFrame)
from PySide2.QtCore import Qt
from ui.widgets.search_bar import SearchBar
from ui.dialogs.customer_dialog import CustomerDialog
from ui.dialogs.customer_history_dialog import CustomerHistoryDialog
from app.database.connection import get_session
from app.repositories.customer_repository import CustomerRepository
from app.models.customer import Customer
from app.design.icons import icon


class CustomerWindow(QWidget):
    def __init__(self):
        super().__init__()
        self._setup_ui()
        self.load_customers()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 16, 24, 24)
        layout.setSpacing(12)

        # -- Summary chip --
        summary = QHBoxLayout()
        self.chip_total = self._chip("Total Customers", "0")
        summary.addWidget(self.chip_total["frame"])
        summary.addStretch()

        # -- Toolbar --
        toolbar = QHBoxLayout()
        self.search_bar = SearchBar()
        self.search_bar.setPlaceholderText("Search by name or email...")
        self.search_bar.textChanged.connect(self._on_search)

        self.add_btn = QPushButton(" Add Customer")
        self.add_btn.setObjectName("PrimaryButton")
        self.add_btn.setIcon(icon("add", on_accent=True))
        self.add_btn.clicked.connect(self._add_customer)

        self.history_btn = QPushButton(" History")
        self.history_btn.setIcon(icon("history"))
        self.history_btn.clicked.connect(self._view_history)

        self.edit_btn = QPushButton(" Edit")
        self.edit_btn.setObjectName("WarningButton")
        self.edit_btn.setIcon(icon("edit"))
        self.edit_btn.clicked.connect(self._edit_customer)

        self.delete_btn = QPushButton(" Delete")
        self.delete_btn.setObjectName("DangerButton")
        self.delete_btn.setIcon(icon("delete"))
        self.delete_btn.clicked.connect(self._delete_customer)

        self.refresh_btn = QPushButton(" Refresh")
        self.refresh_btn.setIcon(icon("refresh"))
        self.refresh_btn.clicked.connect(self.load_customers)

        toolbar.addWidget(self.search_bar)
        toolbar.addStretch()
        toolbar.addWidget(self.refresh_btn)
        toolbar.addWidget(self.history_btn)
        toolbar.addWidget(self.add_btn)
        toolbar.addWidget(self.edit_btn)
        toolbar.addWidget(self.delete_btn)

        # -- Table --
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["ID", "Name", "Email", "Phone", "Address", "Joined"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        # Row hover/selected colors now come entirely from the theme's
        # QTableWidget::item:* rules (app/design/qss_builder.py) -- no
        # per-widget inline stylesheet fighting with the theme anymore.
        self.table.doubleClicked.connect(self._view_history)

        layout.addLayout(summary)
        layout.addLayout(toolbar)
        layout.addWidget(self.table)

        hint = QLabel("Double-click a customer to see their full purchase history.")
        hint.setObjectName("CardDescription")
        layout.addWidget(hint)

    def _chip(self, label, value) -> dict:
        frame = QFrame()
        frame.setObjectName("StatCard")
        frame.setFixedHeight(64)
        frame.setMinimumWidth(170)
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

    def load_customers(self, keyword: str = ""):
        session = get_session()
        try:
            customers = CustomerRepository(session).get_all()
            if keyword:
                kw = keyword.lower()
                customers = [c for c in customers if
                             kw in c.name.lower() or
                             (c.email and kw in c.email.lower()) or
                             (c.phone and kw in c.phone)]
            self._customers = customers
            self.chip_total["val"].setText(str(len(customers)))
            self.table.setRowCount(len(customers))
            for row, c in enumerate(customers):
                joined = c.created_at.strftime("%d-%m-%Y") if c.created_at else ""
                self.table.setItem(row, 0, QTableWidgetItem(str(c.id)))
                self.table.setItem(row, 1, QTableWidgetItem(c.name))
                self.table.setItem(row, 2, QTableWidgetItem(c.email or ""))
                self.table.setItem(row, 3, QTableWidgetItem(c.phone or ""))
                self.table.setItem(row, 4, QTableWidgetItem(c.address or ""))
                self.table.setItem(row, 5, QTableWidgetItem(joined))
        finally:
            session.close()

    def _on_search(self, text: str):
        self.load_customers(text)

    def _add_customer(self):
        dialog = CustomerDialog(self)
        if dialog.exec():
            data = dialog.get_data()
            if not data["name"]:
                QMessageBox.warning(self, "Error", "Name is required.")
                return
            session = get_session()
            try:
                c = Customer(**data)
                CustomerRepository(session).create(c)
                QMessageBox.information(self, "Success", f"Customer '{data['name']}' added!")
            except Exception as e:
                session.rollback()
                QMessageBox.critical(self, "Error", f"Failed: {e}")
            finally:
                session.close()
            self.load_customers()

    def _edit_customer(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Edit", "Please select a customer first.")
            return
        session = get_session()
        try:
            customer_id = int(self.table.item(row, 0).text())
            repo = CustomerRepository(session)
            c = repo.get_by_id(customer_id)
            if not c:
                return
            existing = {"name": c.name, "email": c.email or "",
                        "phone": c.phone or "", "address": c.address or ""}
            dialog = CustomerDialog(self, existing)
            if dialog.exec():
                data = dialog.get_data()
                if not data["name"]:
                    QMessageBox.warning(self, "Error", "Name is required.")
                    return
                c.name = data["name"]
                c.email = data["email"]
                c.phone = data["phone"]
                c.address = data["address"]
                repo.update(c)
        except Exception as e:
            session.rollback()
            QMessageBox.critical(self, "Error", f"Failed: {e}")
        finally:
            session.close()
        self.load_customers()

    def _delete_customer(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Delete", "Please select a customer first.")
            return
        name = self.table.item(row, 1).text()
        confirm = QMessageBox.question(self, "Confirm Delete",
            f"Delete customer '{name}'?", QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.Yes:
            customer_id = int(self.table.item(row, 0).text())
            session = get_session()
            CustomerRepository(session).delete(customer_id)
            session.close()
            self.load_customers()

    def _view_history(self):
        """Opens the customer purchase-history dialog: summary totals +
        every invoice + drill-down into items/payments -- without going
        through a reprint-bill flow first."""
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, "History", "Please select a customer first.")
            return
        session = get_session()
        try:
            customer_id = int(self.table.item(row, 0).text())
            customer = CustomerRepository(session).get_by_id(customer_id)
            if not customer:
                return
            if not customer.phone:
                QMessageBox.information(
                    self, "History",
                    "This customer has no phone number on file, so purchases "
                    "can't be matched to them (invoices are linked by phone)."
                )
                return
            dialog = CustomerHistoryDialog(customer, parent=self)
            dialog.exec()
        finally:
            session.close()

    def refresh(self):
        self.load_customers()
