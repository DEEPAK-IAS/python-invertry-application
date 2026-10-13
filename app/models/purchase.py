from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database.connection import Base
from datetime import datetime

class Purchase(Base):
    __tablename__ = "purchases"

    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False)
    invoice_number = Column(String, unique=True, nullable=False)
    total_amount = Column(Float, nullable=False, default=0.0)
    purchase_date = Column(DateTime, default=datetime.utcnow)
    notes = Column(String, nullable=True)

    supplier = relationship("Supplier", backref="purchases")