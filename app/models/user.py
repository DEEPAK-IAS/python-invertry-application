from __future__ import annotations
from sqlalchemy import Column, Integer, String, DateTime
from app.database.connection import Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    
    # NEW FIELDS ADDED HERE
    company_name = Column(String, nullable=True)
    company_address = Column(String, nullable=True)
    company_gst = Column(String, nullable=True)
    company_phone = Column(String, nullable=True)
    preferred_printer = Column(String, nullable=True)
    company_logo_path = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)




