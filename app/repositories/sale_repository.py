from __future__ import annotations
from sqlalchemy.orm import Session
from app.models.sale import Sale
from typing import List, Optional


class SaleRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_all(self) -> List[Sale]:
        return self.session.query(Sale).order_by(Sale.id.desc()).all()

    def get_by_id(self, sale_id: int) -> Optional[Sale]:
        return self.session.query(Sale).filter(Sale.id == sale_id).first()

    def get_by_customer(self, customer_id: int) -> List[Sale]:
        return self.session.query(Sale).filter(Sale.customer_id == customer_id).all()

    def get_by_customer_phone(self, phone: str) -> List[Sale]:
        """
        Read-only lookup used by the customer purchase-history screen.

        NOTE: `Sale` has no `customer_id` foreign key in this schema --
        a sale is linked to a customer by phone number (this mirrors how
        BillingService.process_checkout already matches/creates the
        Customer row by phone at checkout time). This method is purely
        additive and does not change any existing query or behavior.
        """
        if not phone:
            return []
        return (
            self.session.query(Sale)
            .filter(Sale.customer_phone == phone)
            .order_by(Sale.date_created.desc())
            .all()
        )

    def create(self, sale: Sale) -> Sale:
        self.session.add(sale)
        self.session.commit()
        self.session.refresh(sale)
        return sale

    def delete(self, sale_id: int) -> bool:
        sale = self.get_by_id(sale_id)
        if sale:
            self.session.delete(sale)
            self.session.commit()
            return True
        return False

    def total_revenue(self) -> float:
        result = self.session.query(Sale).all()
        # FIX: Was `s.total` — the correct field name is `s.total_amount`.
        return sum(s.total_amount for s in result)

    def total_sales_count(self) -> int:
        return self.session.query(Sale).count()

    def get_pending_bills(self) -> List[Sale]:
        """All sales that still have an outstanding due amount, newest first."""
        return (
            self.session.query(Sale)
            .filter(Sale.due_amount > 0.001)
            .order_by(Sale.date_created.desc())
            .all()
        )

    def total_pending_dues(self) -> float:
        return sum(s.due_amount for s in self.get_pending_bills())





