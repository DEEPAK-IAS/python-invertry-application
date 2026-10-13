from __future__ import annotations
from sqlalchemy.orm import Session
from app.models.product import Product
from typing import List, Optional

class ProductRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_all(self) -> List[Product]:
        return self.session.query(Product).all()

    def get_by_id(self, product_id: int) -> Optional[Product]:
        return self.session.query(Product).filter(Product.id == product_id).first()

    def get_by_sku(self, sku: str) -> Optional[Product]:
        return self.session.query(Product).filter(Product.sku == sku).first()

    def search(self, keyword: str) -> List[Product]:
        return self.session.query(Product).filter(
            Product.name.ilike(f"%{keyword}%")
        ).all()

    def create(self, product: Product) -> Product:
        self.session.add(product)
        self.session.commit()
        self.session.refresh(product)
        return product

    def update(self, product: Product) -> Product:
        self.session.commit()
        self.session.refresh(product)
        return product

    def delete(self, product_id: int) -> bool:
        product = self.get_by_id(product_id)
        if product:
            self.session.delete(product)
            self.session.commit()
            return True
        return False





