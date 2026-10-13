from __future__ import annotations
from sqlalchemy import Column, Integer, String
from app.database.base import Base, TimestampMixin

class Customer(Base, TimestampMixin):
    __tablename__ = "customers"

    id      = Column(Integer, primary_key=True, autoincrement=True)
    name    = Column(String(200), nullable=False)
    email   = Column(String(200), unique=True, nullable=True)
    phone   = Column(String(20), nullable=True)
    address = Column(String(500), nullable=True)

    def __repr__(self):
        return f"<Customer {self.name}>"





