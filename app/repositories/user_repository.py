from __future__ import annotations
from sqlalchemy.orm import Session
from app.models.user import User
from typing import Optional


class UserRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_username(self, username: str) -> Optional[User]:
        # FIX: Removed `User.is_active == True` — the User model has no
        # is_active column, which caused an AttributeError crash on login.
        return self.session.query(User).filter(
            User.username == username
        ).first()

    def get_by_email(self, email: str) -> Optional[User]:
        return self.session.query(User).filter(
            User.email == email
        ).first()

    def get_by_id(self, user_id: int) -> Optional[User]:
        return self.session.query(User).filter(User.id == user_id).first()

    def username_exists(self, username: str) -> bool:
        return self.session.query(User).filter(
            User.username == username
        ).count() > 0

    def email_exists(self, email: str) -> bool:
        return self.session.query(User).filter(
            User.email == email
        ).count() > 0

    def create(self, user: User) -> User:
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user

    def update(self, user: User) -> User:
        self.session.commit()
        self.session.refresh(user)
        return user





