from __future__ import annotations
from PySide2.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                                QPushButton, QTableWidget, QTableWidgetItem,
                                QHeaderView, QMessageBox, QLabel, QFrame,
                                QComboBox, QDialog, QSplitter)
from PySide2.QtCore import Qt
from ui.widgets.search_bar import SearchBar
from ui.dialogs.supplier_dialog import SupplierDialog
from ui.dialogs.purchase_dialog import PurchaseDialog
from app.database.connection import get_session
from app.repositories.supplier_repository import SupplierRepository
from app.models.supplier import Supplier
from app.models.purchase import Purchase
from app.models.purchase_item import PurchaseItem
from app.design.icons import icon
from datetime import datetime

class SupplierDetailDialog(QDialog):
    """Detailed view for a specific supplier showing month-wise purchase invoices and crystal-clear item breakdowns."""
    def __init__(self, supplier: Supplier, parent=None):
        super().__init__(parent)
        self.supplier = supplier
        self.setWindowTitle(f"Supplier Ledger & Items Report — {supplier.name}")
        self.resize(850, 600)
        self._setup_ui()
        self.load_invoices()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)
        
        # Header Info Card
        info_lbl = QLabel(f"<b>Company:</b> {self.supplier.name} &nbsp;|&nbsp; <b>Contact:</b> {self.supplier.contact_name or 'N/A'} &nbsp;|&nbsp; <b>Phone:</b> {self.supplier.phone or 'N/A'}")
        info_lbl.setStyleSheet("font-size: 13px; padding: 6px; background: rgba(255,255,255,0.03); border-radius: 4px;")
        layout.addWidget(info_lbl)

        # Month Filter Bar, Total Label & Edit Button
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Filter Month:"))
        self.month_combo = QComboBox()
        self.month_combo.setFixedHeight(34)
        self.month_combo.addItem("All Time", "")
        for m in range(1, 13):
            self.month_combo.addItem(datetime(2000, m, 1).strftime('%B'), str(m))
        self.month_combo.currentIndexChanged.connect(self.load_invoices)
        filter_layout.addWidget(self.month_combo)
        
        # ── Dynamic Total Amount Label ──
        filter_layout.addSpacing(15)
        self.total_amount_lbl = QLabel("Total: ₹0.00")
        self.total_amount_lbl.setStyleSheet("font-size: 14px; font-weight: bold; color: #a6e3a1;")
        filter_layout.addWidget(self.total_amount_lbl)

        filter_layout.addStretch()

        edit_purchase_btn = QPushButton(" Edit Selected Invoice")
        edit_purchase_btn.setObjectName("WarningButton")
        edit_purchase_btn.setIcon(icon("edit"))
        edit_purchase_btn.clicked.connect(self._edit_purchase)
        filter_layout.addWidget(edit_purchase_btn)

        layout.addLayout(filter_layout)

        # Use a Splitter so user can resize the balance between Invoices and Items breakdown
        splitter = QSplitter(Qt.Vertical)
        splitter.setHandleWidth(6)

        # ── Top Section: Invoices Table ──
        inv_container = QWidget()
        inv_layout = QVBoxLayout(inv_container)
        inv_layout.setContentsMargins(0, 0, 0, 0)
        inv_layout.addWidget(QLabel("<b>Purchase Invoices</b> (Click an invoice to view items bought)"))
        
        self.inv_table = QTableWidget()
        self.inv_table.setColumnCount(3)
        self.inv_table.setHorizontalHeaderLabels(["Invoice No", "Date", "Total Amount (₹)"])
        self.inv_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.inv_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.inv_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.inv_table.setAlternatingRowColors(True)
        self.inv_table.verticalHeader().setVisible(False)
        self.inv_table.setStyleSheet("""
            QTableWidget::item:selected {
                background-color: #313244; 
                color: #ffffff;
            }
        """)
        self.inv_table.selectionModel().currentRowChanged.connect(self._on_invoice_selected)
        inv_layout.addWidget(self.inv_table)
        
        splitter.addWidget(inv_container)

        # ── Bottom Section: Itemized Breakdown Table ──
        item_container = QWidget()
        item_layout = QVBoxLayout(item_container)
        item_layout.setContentsMargins(0, 0, 0, 0)
        item_layout.addWidget(QLabel("<b>Items Bought in Selected Invoice</b>"))
        
        self.items_table = QTableWidget()
        self.items_table.setColumnCount(4)
        self.items_table.setHorizontalHeaderLabels(["Product Name", "Quantity", "Unit Price (₹)", "Subtotal (₹)"])
        self.items_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.items_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.items_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.items_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.items_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.items_table.setAlternatingRowColors(True)
        self.items_table.verticalHeader().setVisible(False)
        self.items_table.setStyleSheet("""
            QTableWidget::item:selected {
                background-color: #313244; 
                color: #ffffff;
            }
        """)
        item_layout.addWidget(self.items_table)
        
        splitter.addWidget(item_container)
        splitter.setSizes([250, 250])

        layout.addWidget(splitter)

    def load_invoices(self):
        from sqlalchemy.orm import joinedload
        session = get_session()
        try:
            # Eagerly load purchases AND their items while session is active
            purchases = session.query(Purchase)\
                .options(joinedload(Purchase.items))\
                .filter(Purchase.supplier_id == self.supplier.id)\
                .all()
            
            selected_month = self.month_combo.currentData()
            if selected_month:
                purchases = [p for p in purchases if p.purchase_date and str(p.purchase_date.month) == selected_month]

            self._current_purchases = purchases
            
            # ── Calculate and Update Total Amount for Filtered Period ──
            period_total = sum(p.total_amount for p in purchases)
            self.total_amount_lbl.setText(f"Total: ₹{period_total:,.2f}")

            self.inv_table.setRowCount(len(purchases))
            for row, p in enumerate(purchases):
                date_str = p.purchase_date.strftime("%d-%m-%Y") if p.purchase_date else ""
                self.inv_table.setItem(row, 0, QTableWidgetItem(str(p.invoice_number)))
                self.inv_table.setItem(row, 1, QTableWidgetItem(date_str))
                
                amt_item = QTableWidgetItem(f"₹{p.total_amount:.2f}")
                amt_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.inv_table.setItem(row, 2, amt_item)

            if purchases:
                self.inv_table.selectRow(0)
            else:
                self.items_table.setRowCount(0)
        finally:
            session.close()

    def _on_invoice_selected(self, current, previous):
        row = current.row()
        if row < 0 or not hasattr(self, '_current_purchases') or row >= len(self._current_purchases):
            self.items_table.setRowCount(0)
            return

        purchase = self._current_purchases[row]
        items = purchase.items if hasattr(purchase, 'items') else []

        self.items_table.setRowCount(len(items))
        for i_row, item in enumerate(items):
            self.items_table.setItem(i_row, 0, QTableWidgetItem(str(item.product_name)))
            
            qty_item = QTableWidgetItem(str(item.quantity))
            qty_item.setTextAlignment(Qt.AlignCenter)
            self.items_table.setItem(i_row, 1, qty_item)

            price_item = QTableWidgetItem(f"₹{item.unit_price:.2f}")
            price_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.items_table.setItem(i_row, 2, price_item)

            sub_item = QTableWidgetItem(f"₹{item.subtotal:.2f}")
            sub_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.items_table.setItem(i_row, 3, sub_item)

    def _edit_purchase(self):
        row = self.inv_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Selection Required", "Please select an invoice to edit.")
            return

        invoice_no = self.inv_table.item(row, 0).text()
        session = get_session()
        try:
            purchase = session.query(Purchase).filter(Purchase.invoice_number == invoice_no).first()
            if not purchase:
                return

            p_data = {
                "id": purchase.id,
                "supplier_id": purchase.supplier_id,
                "invoice_number": purchase.invoice_number,
                "items": [{"name": i.product_name, "qty": i.quantity, "price": i.unit_price} for i in purchase.items]
            }

            dialog = PurchaseDialog(self, purchase_data=p_data)
            if dialog.exec_():
                new_data = dialog.get_data()
                
                purchase.invoice_number = new_data["invoice_number"]
                purchase.total_amount = new_data["total_amount"]
                purchase.supplier_id = new_data["supplier_id"]

                session.query(PurchaseItem).filter(PurchaseItem.purchase_id == purchase.id).delete()
                for item_info in new_data["items"]:
                    new_item = PurchaseItem(
                        purchase_id=purchase.id,
                        product_name=item_info["name"],
                        quantity=item_info["qty"],
                        unit_price=item_info["price"],
                        subtotal=item_info["subtotal"]
                    )
                    session.add(new_item)

                session.commit()
                QMessageBox.information(self, "Success", "Purchase order updated successfully!")
                self.load_invoices()
        except Exception as e:
            session.rollback()
            QMessageBox.critical(self, "Error", f"Failed to update purchase: {e}")
        finally:
            session.close()


class SupplierWindow(QWidget):
    def __init__(self):
        super().__init__()
        self._setup_ui()
        self.load_suppliers()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 16, 24, 24)
        layout.setSpacing(12)

        # ── Summary chips ──
        summary = QHBoxLayout()
        self.chip_total = self._chip("Total Suppliers", "0", "#cba6f7")
        self.chip_spend = self._chip("Total Procured Value", "₹0.00", "#a6e3a1")
        summary.addWidget(self.chip_total["frame"])
        summary.addWidget(self.chip_spend["frame"])
        summary.addStretch()

        # ── Toolbar ──
        toolbar = QHBoxLayout()
        self.search_bar = SearchBar()
        self.search_bar.setPlaceholderText("Search suppliers...")
        self.search_bar.textChanged.connect(self._on_search)

        self.purchase_btn = QPushButton(" Record Purchase")
        self.purchase_btn.setObjectName("PrimaryButton")
        self.purchase_btn.setIcon(icon("sales", on_accent=True))
        self.purchase_btn.clicked.connect(self._record_purchase)

        self.add_btn = QPushButton(" Add Supplier")
        self.add_btn.setObjectName("PrimaryButton")
        self.add_btn.setIcon(icon("add", on_accent=True))
        self.add_btn.clicked.connect(self._add_supplier)

        self.edit_btn = QPushButton(" Edit")
        self.edit_btn.setObjectName("WarningButton")
        self.edit_btn.setIcon(icon("edit"))
        self.edit_btn.clicked.connect(self._edit_supplier)

        self.delete_btn = QPushButton(" Delete")
        self.delete_btn.setObjectName("DangerButton")
        self.delete_btn.setIcon(icon("delete"))
        self.delete_btn.clicked.connect(self._delete_supplier)

        self.refresh_btn = QPushButton(" Refresh")
        self.refresh_btn.setIcon(icon("refresh"))
        self.refresh_btn.clicked.connect(self.load_suppliers)

        toolbar.addWidget(self.search_bar)
        toolbar.addStretch()
        toolbar.addWidget(self.refresh_btn)
        toolbar.addWidget(self.purchase_btn)
        toolbar.addWidget(self.add_btn)
        toolbar.addWidget(self.edit_btn)
        toolbar.addWidget(self.delete_btn)

        # ── Table ──
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Company", "Contact Person", "Email", "Phone", "Added"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        
        self.table.setStyleSheet("""
            QTableWidget::item:selected {
                background-color: #313244; 
                color: #ffffff;
            }
        """)
        
        self.table.doubleClicked.connect(self._open_supplier_ledger)

        layout.addLayout(summary)
        layout.addLayout(toolbar)
        layout.addWidget(self.table)

    def _chip(self, label, value, color) -> dict:
        frame = QFrame()
        frame.setObjectName("StatCard")
        frame.setFixedHeight(60)
        frame.setMinimumWidth(160)
        inner = QVBoxLayout(frame)
        inner.setContentsMargins(16, 6, 16, 6)
        val_lbl = QLabel(value)
        val_lbl.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {color};")
        lbl = QLabel(label)
        lbl.setStyleSheet("font-size: 11px; color: #6c7086;")
        inner.addWidget(val_lbl)
        inner.addWidget(lbl)
        return {"frame": frame, "val": val_lbl}

    def load_suppliers(self, keyword: str = ""):
        session = get_session()
        try:
            suppliers = SupplierRepository(session).get_all()
            if keyword:
                kw = keyword.lower()
                suppliers = [s for s in suppliers if
                             kw in s.name.lower() or
                             (s.contact_name and kw in s.contact_name.lower())]
            self._suppliers = suppliers
            self.chip_total["val"].setText(str(len(suppliers)))
            
            all_purchases = session.query(Purchase).all()
            total_spend = sum(p.total_amount for p in all_purchases)
            self.chip_spend["val"].setText(f"₹{total_spend:,.2f}")

            self.table.setRowCount(len(suppliers))
            for row, s in enumerate(suppliers):
                added = s.created_at.strftime("%d-%m-%Y") if s.created_at else ""
                self.table.setItem(row, 0, QTableWidgetItem(str(s.id)))
                self.table.setItem(row, 1, QTableWidgetItem(s.name))
                self.table.setItem(row, 2, QTableWidgetItem(s.contact_name or ""))
                self.table.setItem(row, 3, QTableWidgetItem(s.email or ""))
                self.table.setItem(row, 4, QTableWidgetItem(s.phone or ""))
                self.table.setItem(row, 5, QTableWidgetItem(added))
        finally:
            session.close()

    def _open_supplier_ledger(self):
        row = self.table.currentRow()
        if row < 0:
            return
        supplier_id = int(self.table.item(row, 0).text())
        session = get_session()
        try:
            s = SupplierRepository(session).get_by_id(supplier_id)
            if s:
                dialog = SupplierDetailDialog(s, self)
                dialog.exec_()
        finally:
            session.close()

    def _record_purchase(self):
        dialog = PurchaseDialog(self)
        if dialog.exec_():
            data = dialog.get_data()
            if not data["invoice_number"] or not data["supplier_id"]:
                QMessageBox.warning(self, "Error", "Supplier and Invoice Number are required.")
                return
            if not data["items"]:
                QMessageBox.warning(self, "Error", "At least one purchased item is required.")
                return

            session = get_session()
            try:
                new_purchase = Purchase(
                    supplier_id=data["supplier_id"],
                    invoice_number=data["invoice_number"],
                    total_amount=data["total_amount"]
                )
                session.add(new_purchase)
                session.flush()

                for item_data in data["items"]:
                    p_item = PurchaseItem(
                        purchase_id=new_purchase.id,
                        product_name=item_data["name"],
                        quantity=item_data["qty"],
                        unit_price=item_data["price"],
                        subtotal=item_data["subtotal"]
                    )
                    session.add(p_item)

                session.commit()
                QMessageBox.information(self, "Success", "Purchase order and items recorded successfully!")
                self.load_suppliers()
            except Exception as e:
                session.rollback()
                QMessageBox.critical(self, "Error", f"Failed to record purchase: {e}")
            finally:
                session.close()

    def _on_search(self, text: str):
        self.load_suppliers(text)

    def _add_supplier(self):
        dialog = SupplierDialog(self)
        if dialog.exec_():
            data = dialog.get_data()
            if not data["name"]:
                QMessageBox.warning(self, "Error", "Company name is required.")
                return
            session = get_session()
            try:
                s = Supplier(**data)
                SupplierRepository(session).create(s)
                QMessageBox.information(self, "Success", f"Supplier '{data['name']}' added!")
            except Exception as e:
                session.rollback()
                QMessageBox.critical(self, "Error", f"Failed: {e}")
            finally:
                session.close()
            self.load_suppliers()

    def _edit_supplier(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Edit", "Please select a supplier first.")
            return
        session = get_session()
        try:
            supplier_id = int(self.table.item(row, 0).text())
            repo = SupplierRepository(session)
            s    = repo.get_by_id(supplier_id)
            if not s:
                return
            existing = {"name": s.name, "contact_name": s.contact_name or "",
                        "email": s.email or "", "phone": s.phone or ""}
            dialog = SupplierDialog(self, existing)
            if dialog.exec_():
                data = dialog.get_data()
                if not data["name"]:
                    QMessageBox.warning(self, "Error", "Company name is required.")
                    return
                s.name         = data["name"]
                s.contact_name = data["contact_name"]
                s.email        = data["email"]
                s.phone        = data["phone"]
                repo.update(s)
        except Exception as e:
            session.rollback()
            QMessageBox.critical(self, "Error", f"Failed: {e}")
        finally:
            session.close()
        self.load_suppliers()

    def _delete_supplier(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Delete", "Please select a supplier first.")
            return
        name = self.table.item(row, 1).text()
        confirm = QMessageBox.question(
            self, "Confirm Delete",
            f"Delete supplier '{name}' and all their associated purchases?", 
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm == QMessageBox.Yes:
            supplier_id = int(self.table.item(row, 0).text())
            session = get_session()
            try:
                SupplierRepository(session).delete(supplier_id)
                QMessageBox.information(self, "Success", f"Supplier '{name}' deleted successfully.")
                self.load_suppliers()
            except Exception as e:
                session.rollback()
                QMessageBox.critical(self, "Error", f"Failed to delete supplier: {e}")
            finally:
                session.close()