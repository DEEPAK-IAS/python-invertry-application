from __future__ import annotations
from sqlalchemy import Column, Integer, String, Float, Enum as SAEnum
from app.database.base import Base, TimestampMixin
from app.constants import ProductCategory, StockStatus

class Product(Base, TimestampMixin):
    __tablename__ = "products"

    id         = Column(Integer, primary_key=True, autoincrement=True)
    name       = Column(String(200), nullable=False)
    sku        = Column(String(50), unique=True, nullable=False)
    size   = Column(String, nullable=False)
    price      = Column(Float, nullable=False)
    stock_qty  = Column(Integer, default=0)
    status     = Column(SAEnum(StockStatus), default=StockStatus.IN_STOCK)
    supplier_id = Column(Integer, nullable=True)
    gst_rate = Column(Float, default=18.0)

    def __repr__(self):
        return f"<Product {self.sku} - {self.name}>"





