from PySide2.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                                QLineEdit, QPushButton, QTableWidget, 
                                QTableWidgetItem, QComboBox, QMessageBox, QHeaderView, QFrame)
from PySide2.QtCore import Qt
from app.database.connection import get_session
from app.models.supplier import Supplier
from app.design.icons import icon

class PurchaseDialog(QDialog):
    def __init__(self, parent=None, purchase_data=None):
        super().__init__(parent)
        self.purchase_data = purchase_data
        self.setWindowTitle("Edit Purchase Order" if purchase_data else "Record Purchase Order")
        self.resize(900, 650)
        self._setup_ui()
        self.load_suppliers()
        
        if self.purchase_data:
            self._populate_data()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(20)

        # -- Header Title Card --
        title_text = "Edit Purchase Order" if self.purchase_data else "New Purchase Order Entry"
        title_lbl = QLabel(title_text)
        title_lbl.setObjectName("PageTitle")
        main_layout.addWidget(title_lbl)

        # ── Top Details Card (Supplier & Invoice) ──
        top_card = QFrame()
        top_card.setObjectName("StatCard")
        top_layout = QHBoxLayout(top_card)
        top_layout.setContentsMargins(20, 20, 20, 20)
        top_layout.setSpacing(20)

        self.supplier_combo = QComboBox()
        self.supplier_combo.setFixedHeight(45)
        self.supplier_combo.setStyleSheet("font-size: 14px; padding-left: 8px;")
        
        self.invoice_input = QLineEdit()
        self.invoice_input.setFixedHeight(45)
        self.invoice_input.setStyleSheet("font-size: 14px; padding-left: 8px;")
        self.invoice_input.setPlaceholderText("e.g., INV-2026-001")

        lbl_style = "font-size: 14px; font-weight: bold;"
        sup_lbl = QLabel("Supplier:")
        sup_lbl.setStyleSheet(lbl_style)
        inv_lbl = QLabel("Invoice No:")
        inv_lbl.setStyleSheet(lbl_style)

        top_layout.addWidget(sup_lbl)
        top_layout.addWidget(self.supplier_combo, 3)
        top_layout.addWidget(inv_lbl)
        top_layout.addWidget(self.invoice_input, 2)
        
        main_layout.addWidget(top_card)

        # ── Items Section Header & Add Button ──
        items_header_layout = QHBoxLayout()
        items_lbl = QLabel("Purchased Items")
        items_lbl.setStyleSheet("font-size: 16px; font-weight: bold;")
        items_header_layout.addWidget(items_lbl)
        items_header_layout.addStretch()

        add_row_btn = QPushButton("Add Item Row")
        add_row_btn.setObjectName("SmallButton")
        add_row_btn.setIcon(icon("add"))
        add_row_btn.clicked.connect(self._add_row)
        items_header_layout.addWidget(add_row_btn)

        main_layout.addLayout(items_header_layout)

        # ── Items Table ──
        self.items_table = QTableWidget()
        self.items_table.setColumnCount(5)
        self.items_table.setHorizontalHeaderLabels(["Product Name", "Qty", "Unit Price (₹)", "Subtotal (₹)", "Action"])
        
        self.items_table.verticalHeader().setDefaultSectionSize(52) 
        self.items_table.verticalHeader().setVisible(False)
        self.items_table.setAlternatingRowColors(True)
        self.items_table.setStyleSheet("font-size: 14px;")

        header = self.items_table.horizontalHeader()
        header.setStyleSheet("font-size: 13px; font-weight: bold; height: 35px;")
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)

        main_layout.addWidget(self.items_table)

        # ── Footer Total & Actions Card (INITIALIZED FIRST) ──
        footer_layout = QHBoxLayout()
        
        self.grand_total_lbl = QLabel("Grand Total: ₹0.00")
        self.grand_total_lbl.setStyleSheet("font-size: 18px; font-weight: bold; color: #a6e3a1;")
        footer_layout.addWidget(self.grand_total_lbl)
        
        footer_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFixedHeight(45)
        cancel_btn.setFixedWidth(120)
        cancel_btn.setStyleSheet("font-size: 14px;")
        cancel_btn.clicked.connect(self.reject)

        save_btn = QPushButton("Save Changes" if self.purchase_data else "Save Purchase Order")
        save_btn.setObjectName("PrimaryButton")
        save_btn.setFixedHeight(45)
        save_btn.setFixedWidth(200)
        save_btn.setStyleSheet("font-size: 14px; font-weight: bold;")
        save_btn.clicked.connect(self.accept)

        footer_layout.addWidget(cancel_btn)
        footer_layout.addWidget(save_btn)
        
        main_layout.addLayout(footer_layout)

        # ── ADD ROW AFTER LABELS EXIST ──
        if not self.purchase_data:
            self._add_row()

    def load_suppliers(self):
        session = get_session()
        try:
            suppliers = session.query(Supplier).all()
            for s in suppliers:
                self.supplier_combo.addItem(s.name, s.id)
            if self.purchase_data:
                idx = self.supplier_combo.findData(self.purchase_data["supplier_id"])
                if idx >= 0:
                    self.supplier_combo.setCurrentIndex(idx)
        finally:
            session.close()

    def _populate_data(self):
        self.invoice_input.setText(self.purchase_data["invoice_number"])
        for item in self.purchase_data["items"]:
            self._add_row(item["name"], item["qty"], item["price"])

    def _add_row(self, name="", qty=1, price=0.0):
        row = self.items_table.rowCount()
        self.items_table.insertRow(row)
        
        self.items_table.setItem(row, 0, QTableWidgetItem(name))
        
        qty_item = QTableWidgetItem(str(qty))
        qty_item.setTextAlignment(Qt.AlignCenter)
        self.items_table.setItem(row, 1, qty_item)
        
        price_item = QTableWidgetItem(f"{price:.2f}")
        price_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.items_table.setItem(row, 2, price_item)
        
        subtotal_item = QTableWidgetItem(f"{qty * price:.2f}")
        subtotal_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        subtotal_item.setFlags(subtotal_item.flags() & ~Qt.ItemIsEditable)
        self.items_table.setItem(row, 3, subtotal_item)

        del_btn = QPushButton("Remove")
        del_btn.setObjectName("DangerButton")
        del_btn.setIcon(icon("delete"))
        del_btn.clicked.connect(lambda: self._remove_row(row))
        self.items_table.setCellWidget(row, 4, del_btn)

        self.items_table.itemChanged.connect(self._calculate_totals)
        self._calculate_totals()

    def _remove_row(self, row):
        self.items_table.removeRow(row)
        self._calculate_totals()

    def _calculate_totals(self):
        total = 0.0
        try:
            self.items_table.itemChanged.disconnect(self._calculate_totals)
        except Exception:
            pass

        for row in range(self.items_table.rowCount()):
            qty_item = self.items_table.item(row, 1)
            price_item = self.items_table.item(row, 2)
            subtotal_item = self.items_table.item(row, 3)

            try:
                qty = int(qty_item.text()) if qty_item and qty_item.text().isdigit() else 0
            except ValueError:
                qty = 0

            try:
                price = float(price_item.text()) if price_item and price_item.text() else 0.0
            except ValueError:
                price = 0.0

            subtotal = qty * price
            if subtotal_item:
                subtotal_item.setText(f"{subtotal:.2f}")

            total += subtotal

        self.grand_total_lbl.setText(f"Grand Total: ₹{total:,.2f}")
        self.items_table.itemChanged.connect(self._calculate_totals)

    def get_data(self):
        items = []
        total = 0.0
        for row in range(self.items_table.rowCount()):
            name_item = self.items_table.item(row, 0)
            qty_item = self.items_table.item(row, 1)
            price_item = self.items_table.item(row, 2)
            
            if name_item and name_item.text().strip():
                name = name_item.text().strip()
                qty = int(qty_item.text()) if qty_item and qty_item.text().isdigit() else 1
                price = float(price_item.text()) if price_item and price_item.text() else 0.0
                subtotal = qty * price
                total += subtotal
                items.append({"name": name, "qty": qty, "price": price, "subtotal": subtotal})

        return {
            "supplier_id": self.supplier_combo.currentData(),
            "invoice_number": self.invoice_input.text().strip(),
            "total_amount": total,
            "items": items
        }