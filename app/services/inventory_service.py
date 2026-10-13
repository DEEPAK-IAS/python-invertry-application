from __future__ import annotations
from app.repositories.product_repository import ProductRepository
from app.models.product import Product
from app.constants import StockStatus, LOW_STOCK_THRESHOLD
from app.utils.logger import logger
from typing import List

class InventoryService:
    def __init__(self, session):
        self.repo = ProductRepository(session)

    def add_product(self, product: Product) -> Product:
        # 1. Check if a product with this SKU already exists
        # We query by SKU to ensure uniqueness
        existing_product = self.repo.get_by_sku(product.sku)
        
        if existing_product:
            # Raise a specific error that the UI can catch
            raise ValueError(f"A product with SKU '{product.sku}' already exists.")
            
        # 2. Proceed if SKU is unique
        result = self.repo.create(product)
        logger.info(f"Product added: {result.sku}")
        return result

    def update_stock(self, product_id: int, quantity: int) -> Product:
        product = self.repo.get_by_id(product_id)
        if not product:
            raise ValueError(f"Product {product_id} not found")
        product.stock_qty += quantity
        product.status = self._calculate_status(product.stock_qty)
        return self.repo.update(product)

    def get_low_stock(self) -> List[Product]:
        return [p for p in self.repo.get_all() if p.stock_qty <= LOW_STOCK_THRESHOLD]

    def _calculate_status(self, qty: int) -> StockStatus:
        if qty <= 0:
            return StockStatus.OUT_OF_STOCK
        elif qty <= LOW_STOCK_THRESHOLD:
            return StockStatus.LOW_STOCK
        return StockStatus.IN_STOCK





