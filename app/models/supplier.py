from __future__ import annotations
from sqlalchemy import Column, Integer, String
from app.database.base import Base, TimestampMixin

class Supplier(Base, TimestampMixin):
    __tablename__ = "suppliers"

    id           = Column(Integer, primary_key=True, autoincrement=True)
    name         = Column(String(200), nullable=False)
    contact_name = Column(String(200), nullable=True)
    email        = Column(String(200), nullable=True)
    phone        = Column(String(20), nullable=True)

    def __repr__(self):
        return f"<Supplier {self.name}>"





