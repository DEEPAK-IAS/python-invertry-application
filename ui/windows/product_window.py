from __future__ import annotations
from PySide2.QtWidgets import (QWidget, QVBoxLayout, QPushButton,
                                QHBoxLayout, QMessageBox)
from PySide2.QtCore import Signal
from ui.widgets.product_table import ProductTable
from ui.widgets.search_bar import SearchBar
from ui.dialogs.product_dialog import ProductDialog
from app.database.connection import get_session
from app.services.inventory_service import InventoryService
from app.models.product import Product
from app.repositories.product_repository import ProductRepository
from app.validators.product_validator import ProductValidator
from app.constants import ProductCategory, StockStatus
from app.design.icons import icon
from pydantic import ValidationError


class ProductWindow(QWidget):
    product_saved = Signal()

    def __init__(self):
        super().__init__()
        self._setup_ui()
        self.load_products()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 16, 24, 24)

        top = QHBoxLayout()
        self.search_bar = SearchBar()
        self.search_bar.textChanged.connect(self._on_search)

        self.add_btn = QPushButton("  Add Product")
        self.add_btn.setObjectName("PrimaryButton")
        self.add_btn.setIcon(icon("add", on_accent=True))
        self.add_btn.clicked.connect(self._add_product)

        self.edit_btn = QPushButton("  Edit")
        self.edit_btn.setObjectName("WarningButton")
        self.edit_btn.setIcon(icon("edit"))
        self.edit_btn.clicked.connect(self._edit_product)

        self.delete_btn = QPushButton("  Delete")
        self.delete_btn.setObjectName("DangerButton")
        self.delete_btn.setIcon(icon("delete"))
        self.delete_btn.clicked.connect(self._delete_product)

        top.addWidget(self.search_bar)
        top.addStretch()
        top.addWidget(self.add_btn)
        top.addWidget(self.edit_btn)
        top.addWidget(self.delete_btn)

        self.table = ProductTable()
        layout.addLayout(top)
        layout.addWidget(self.table)

    def load_products(self, keyword: str = ""):
        session = get_session()
        repo = ProductRepository(session)
        products = repo.search(keyword) if keyword else repo.get_all()
        self.table.load_products(products)
        session.close()

    def refresh_data(self):
        self.load_products()

    def _on_search(self, text: str):
        self.load_products(text)

    def _add_product(self):
        dialog = ProductDialog(self)
        if dialog.exec():
            data = dialog.get_data()
            try:
                validated = ProductValidator(**data)
            except ValidationError as e:
                QMessageBox.warning(self, "Validation Error", str(e))
                return

            session = get_session()
            try:
                service = InventoryService(session)
                
                # Dynamically set stock status based on quantity
                stock_status = StockStatus.IN_STOCK if validated.stock_qty > 0 else StockStatus.OUT_OF_STOCK

                product = Product(
                    name=validated.name,
                    sku=validated.sku,
                    size=validated.size,
                    price=validated.price,
                    stock_qty=validated.stock_qty,
                    gst_rate=validated.gst_rate,
                    status=stock_status,
                )
                service.add_product(product)
                self.load_products()
                self.product_saved.emit()
            except ValueError as e:
                QMessageBox.warning(self, "Duplicate SKU", str(e))
            except Exception as e:
                if "UNIQUE constraint failed: products.sku" in str(e):
                    QMessageBox.critical(
                        self, "Error", "This SKU already exists! Please use a unique SKU."
                    )
                else:
                    QMessageBox.critical(self, "Error", f"Database error: {str(e)}")
            finally:
                session.close()

    def _edit_product(self):
        product = self.table.get_selected_product()
        if not product:
            QMessageBox.information(self, "Edit", "Please select a product first.")
            return
        dialog = ProductDialog(self, product)
        if dialog.exec():
            data = dialog.get_data()
            try:
                validated = ProductValidator(**data)
            except ValidationError as e:
                QMessageBox.warning(self, "Validation Error", str(e))
                return

            session = get_session()
            try:
                repo = ProductRepository(session)
                p = repo.get_by_id(product["id"])
                if p:
                    p.name = validated.name
                    p.sku = validated.sku
                    p.size = validated.size
                    p.price = validated.price
                    p.stock_qty = validated.stock_qty
                    p.gst_rate = validated.gst_rate
                    # Update status dynamically on edit as well
                    p.status = StockStatus.IN_STOCK if validated.stock_qty > 0 else StockStatus.OUT_OF_STOCK
                    repo.update(p)
                self.load_products()
                self.product_saved.emit()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to update: {str(e)}")
            finally:
                session.close()

    def _delete_product(self):
        product = self.table.get_selected_product()
        if not product:
            QMessageBox.information(self, "Delete", "Please select a product first.")
            return
        confirm = QMessageBox.question(
            self, "Confirm Delete", f"Delete '{product['name']}'?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if confirm == QMessageBox.Yes:
            session = get_session()
            ProductRepository(session).delete(product["id"])
            session.close()
            self.load_products()
            self.product_saved.emit()