from __future__ import annotations
from app.repositories.product_repository import ProductRepository
from app.repositories.customer_repository import CustomerRepository
from app.utils.logger import logger

class SalesService:
    def __init__(self, session):
        self.product_repo = ProductRepository(session)
        self.customer_repo = CustomerRepository(session)

    def process_sale(self, product_id: int, customer_id: int, quantity: int) -> dict:
        product = self.product_repo.get_by_id(product_id)
        if not product:
            raise ValueError("Product not found")
        if product.stock_qty < quantity:
            raise ValueError("Insufficient stock")

        total = product.price * quantity
        product.stock_qty -= quantity
        self.product_repo.update(product)

        logger.info(f"Sale processed: {quantity}x {product.sku} | Total: {total}")
        return {"product": product.name, "quantity": quantity, "total": total}





