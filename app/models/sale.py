from __future__ import annotations
from sqlalchemy import Column, Integer, Float, String, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.connection import Base

class Sale(Base):
    __tablename__ = "sales"

    id = Column(Integer, primary_key=True, index=True)
    customer_name = Column(String, nullable=True)
    customer_phone = Column(String, nullable=True)
    customer_gstin = Column(String, nullable=True)
    customer_address = Column(String(500), nullable=True)
    date_created = Column(DateTime, default=datetime.now)
    
    # Billing Totals
    subtotal = Column(Float, default=0.0)
    discount = Column(Float, default=0.0)
    
    # GST Handling
    is_gst_bill = Column(Boolean, default=False)
    gst_rate = Column(Float, default=0.0) # e.g., 18.0 for 18%
    gst_amount = Column(Float, default=0.0)
    
    total_amount = Column(Float, default=0.0)

    # --- Pending Bill / Partial Payment tracking ---
    paid_amount    = Column(Float, default=0.0)     # how much the customer has paid so far
    due_amount     = Column(Float, default=0.0)     # total_amount - paid_amount
    payment_status = Column(String, default="PAID") # "PAID" | "PARTIAL" | "UNPAID"
    
    discount_percentage = Column(Float, default=0.0)
    discount_amount = Column(Float, default=0.0)

    items    = relationship("SaleItem", back_populates="sale", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="sale", cascade="all, delete-orphan")


class SaleItem(Base):
    __tablename__ = "sale_items"

    id = Column(Integer, primary_key=True, index=True)
    sale_id = Column(Integer, ForeignKey("sales.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    product_name = Column(String) # Stored in case product name changes later
    size = Column(String(50), nullable=True)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)
    total_price = Column(Float, nullable=False)
    gst_rate = Column(Float, default=0.0)

    sale = relationship("Sale", back_populates="items")


class Payment(Base):
    """
    A single payment made against a Sale (invoice).
    A sale can have many payments over time — e.g. ₹500 now, ₹500 later —
    which is how a "pending bill" gets paid off gradually.
    """
    __tablename__ = "payments"

    id           = Column(Integer, primary_key=True, index=True)
    sale_id      = Column(Integer, ForeignKey("sales.id"), nullable=False)
    amount       = Column(Float, nullable=False)
    payment_date = Column(DateTime, default=datetime.now)
    note         = Column(String, nullable=True)

    sale = relationship("Sale", back_populates="payments")




