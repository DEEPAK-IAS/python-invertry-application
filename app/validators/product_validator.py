from __future__ import annotations
from pydantic import BaseModel, field_validator, Field

class ProductValidator(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    sku: str = Field(min_length=2, max_length=50)
    size: str = Field(min_length=1)
    price: float = Field(gt=0)
    stock_qty: int = Field(ge=0)
    gst_rate: float = 18.0

    @field_validator("sku")
    @classmethod
    def sku_uppercase(cls, v: str) -> str:
        return v.upper().strip()

    @field_validator("name")
    @classmethod
    def name_strip(cls, v: str) -> str:
        return v.strip()

    @field_validator("size")
    @classmethod
    def size_strip(cls, v: str) -> str:
        return v.strip()




