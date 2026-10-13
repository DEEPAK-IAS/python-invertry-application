from __future__ import annotations
from PySide2.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView
from PySide2.QtCore import Qt

HEADERS = ["ID", "Name", "SKU", "Size", "Price", "Stock", "GST rate", "Status"]

class ProductTable(QTableWidget):
    def __init__(self):
        super().__init__()
        self.setColumnCount(len(HEADERS))
        self.setHorizontalHeaderLabels(HEADERS)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.setEditTriggers(QTableWidget.NoEditTriggers)
        self.setSelectionBehavior(QTableWidget.SelectRows)
        self.setAlternatingRowColors(False)
        self.setSelectionBehavior(QTableWidget.SelectRows)
        self.selectionModel().selectionChanged.connect(self.viewport().update)
        self._products = []

    def load_products(self, products: list):
        self._products = products
        
        # 1. Filter out invalid/empty products before setting row count
        valid_products = [p for p in products if p.id is not None]
        
        # 2. Clear and set row count based on valid products only
        self.setRowCount(0)
        self.setRowCount(len(valid_products))
        
        # 3. Populate only valid rows
        for row, p in enumerate(valid_products):
            self.setItem(row, 0, QTableWidgetItem(str(p.id)))
            self.setItem(row, 1, QTableWidgetItem(p.name))
            self.setItem(row, 2, QTableWidgetItem(p.sku))
            self.setItem(row, 3, QTableWidgetItem(str(p.size)))
            self.setItem(row, 4, QTableWidgetItem(f"₹{p.price:.2f}"))
            self.setItem(row, 5, QTableWidgetItem(str(p.stock_qty)))
            gst = getattr(p, "gst_rate", 0.0) or 0.0
            self.setItem(row, 6, QTableWidgetItem(f"{gst:.1f}%"))   
            
            status_val = p.status.value if hasattr(p.status, 'value') else str(p.status)
            self.setItem(row, 7, QTableWidgetItem(status_val))     
            
    def get_selected_product(self) -> dict | None:
        row = self.currentRow()
        if row < 0 or row >= len(self._products):
            return None
        p = self._products[row]
        return {"id": p.id, "name": p.name, "sku": p.sku,
                "size": p.size, "price": p.price, "stock_qty": p.stock_qty,
                "gst_rate": getattr(p, "gst_rate", 0.0) or 0.0,}


