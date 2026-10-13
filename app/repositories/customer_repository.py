from __future__ import annotations
from sqlalchemy.orm import Session
from app.models.customer import Customer
from typing import List, Optional

class CustomerRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_all(self) -> List[Customer]:
        return self.session.query(Customer).all()

    def get_by_id(self, customer_id: int) -> Optional[Customer]:
        return self.session.query(Customer).filter(Customer.id == customer_id).first()

    def create(self, customer: Customer) -> Customer:
        self.session.add(customer)
        self.session.commit()
        self.session.refresh(customer)
        return customer

    def update(self, customer: Customer) -> Customer:
        self.session.commit()
        self.session.refresh(customer)
        return customer

    def delete(self, customer_id: int) -> bool:
        customer = self.get_by_id(customer_id)
        if customer:
            self.session.delete(customer)
            self.session.commit()
            return True
        return False





