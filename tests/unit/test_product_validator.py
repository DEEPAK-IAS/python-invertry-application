from __future__ import annotations
import pytest
from app.validators.product_validator import ProductValidator
from app.constants import ProductCategory

def test_valid_product():
    p = ProductValidator(
        name="Test Product",
        sku="elec-tst-001",
        category=ProductCategory.ELECTRONICS,
        price=99.99,
        stock_qty=10
    )
    assert p.sku == "ELEC-TST-001"

def test_invalid_price():
    with pytest.raises(Exception):
        ProductValidator(
            name="Bad Product",
            sku="bad-001",
            category=ProductCategory.OTHER,
            price=-10,
            stock_qty=0
        )

