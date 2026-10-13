from __future__ import annotations
from sqlalchemy.orm import Session
from app.models.supplier import Supplier
from typing import List, Optional
from app.models.purchase import Purchase

class SupplierRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_all(self) -> List[Supplier]:
        return self.session.query(Supplier).all()

    def get_by_id(self, supplier_id: int) -> Optional[Supplier]:
        return self.session.query(Supplier).filter(Supplier.id == supplier_id).first()

    def create(self, supplier: Supplier) -> Supplier:
        self.session.add(supplier)
        self.session.commit()
        self.session.refresh(supplier)
        return supplier

    def delete(self, supplier_id: int):
        supplier = self.session.query(Supplier).filter(Supplier.id == supplier_id).first()
        if supplier:
            # Explicitly delete associated purchases first to prevent NOT NULL constraint crashes
            purchases = self.session.query(Purchase).filter(Purchase.supplier_id == supplier_id).all()
            for purchase in purchases:
                # Purchase items will be cleaned up if cascade is set, 
                # or we can delete them explicitly if needed:
                for item in purchase.items:
                    self.session.delete(item)
                self.session.delete(purchase)

            # Now safely delete the supplier
            self.session.delete(supplier)
            self.session.commit()





