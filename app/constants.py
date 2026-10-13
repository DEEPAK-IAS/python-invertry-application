from __future__ import annotations
from enum import Enum

class ProductCategory(str, Enum):
    ELECTRONICS = "Electronics"
    CLOTHING = "Clothing"
    FOOD = "Food"
    FURNITURE = "Furniture"
    OTHER = "Other"

class StockStatus(str, Enum):
    IN_STOCK = "In Stock"
    LOW_STOCK = "Low Stock"
    OUT_OF_STOCK = "Out of Stock"

class OrderStatus(str, Enum):
    PENDING = "Pending"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"

# Business rules
LOW_STOCK_THRESHOLD = 10





