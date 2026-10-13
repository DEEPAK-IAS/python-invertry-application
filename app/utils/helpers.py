from __future__ import annotations
from datetime import datetime

def format_currency(amount: float) -> str:
    return f"₹{amount:,.2f}"

def format_date(dt: datetime) -> str:
    return dt.strftime("%d-%m-%Y %H:%M")

def generate_sku(name: str, category: str) -> str:
    prefix = category[:3].upper()
    suffix = name[:3].upper()
    timestamp = datetime.now().strftime("%H%M%S")
    return f"{prefix}-{suffix}-{timestamp}"





