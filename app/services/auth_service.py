from __future__ import annotations
import hashlib
import secrets
import json
import os
from datetime import datetime, timedelta
from typing import Optional
from app.repositories.user_repository import UserRepository
from app.models.user import User
from app.database.connection import get_session
from app.utils.logger import logger

# FIX: Import CACHE_DIR from settings so that BOTH login() and auto_login()
# use the same path (~/Documents/StockManager/cache/session.json).
# Previously, auth_service hardcoded its own CACHE_DIR pointing to
# app/cache/ while login() saved to settings.CACHE_DIR — meaning
# auto_login() would never find the file that login() had just written.
from app.config.settings import CACHE_DIR

CACHE_FILE = os.path.join(CACHE_DIR, "session.json")
SESSION_DURATION_DAYS = 0

os.makedirs(CACHE_DIR, exist_ok=True)


# ── Password helpers ──
def _hash_password(password: str, salt: str = None) -> tuple[str, str]:
    if not salt:
        salt = secrets.token_hex(16)
    hashed = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 260000)
    return hashed.hex(), salt


def _verify_password(password: str, stored_hash: str) -> bool:
    """stored_hash format: salt$hash"""
    try:
        salt, hash_val = stored_hash.split("$", 1)
        computed, _ = _hash_password(password, salt)
        return computed == hash_val
    except Exception:
        return False


def _make_hash(password: str) -> str:
    salt = secrets.token_hex(16)
    hashed, _ = _hash_password(password, salt)
    return f"{salt}${hashed}"


# ── Session cache ──
class SessionCache:
    """
    Stores login session locally in a JSON file.
    On next launch, if session is still valid, user is auto-logged in.
    Uses CACHE_DIR from settings so all paths are consistent.
    """

    @staticmethod
    def save(user_data: dict) -> dict:
        # AFTER — expires at midnight tonight (end of current day)
        from datetime import datetime, timedelta
        today = datetime.utcnow().date()
        expiry = datetime(today.year, today.month, today.day, 23, 59, 59).isoformat()
        data = {**user_data, "expiry": expiry}
        os.makedirs(CACHE_DIR, exist_ok=True)
        with open(CACHE_FILE, "w") as f:
            json.dump(data, f, indent=2)
        logger.info(f"Session cached for user: {user_data.get('username', '?')}")
        return data

    @staticmethod
    def load() -> Optional[dict]:
        if not os.path.exists(CACHE_FILE):
            return None
        try:
            with open(CACHE_FILE, "r") as f:
                data = json.load(f)
            expiry = datetime.fromisoformat(data.get("expiry", "2000-01-01"))
            if datetime.utcnow() > expiry:
                SessionCache.clear()
                logger.info("Cached session expired — cleared")
                return None
            # Remove internal expiry key before returning to caller
            data.pop("expiry", None)
            return data
        except Exception:
            SessionCache.clear()
            return None

    @staticmethod
    def clear():
        if os.path.exists(CACHE_FILE):
            os.remove(CACHE_FILE)
        logger.info("Session cache cleared")

    @staticmethod
    def is_valid() -> bool:
        return SessionCache.load() is not None


# ── Auth service ──
class AuthService:

    @staticmethod
    def register(full_name, username, email, password, company_name="", company_address="",
                 company_gst="", company_logo_path="", company_phone=""):
        from app.database.connection import SessionLocal
        from app.models.user import User
        from app.utils.security import hash_password

        with SessionLocal() as db:
            if db.query(User).filter(User.username == username).first():
                return False, "Username already exists."
            if db.query(User).filter(User.email == email).first():
                return False, "Email already registered."

            new_user = User(
                full_name=full_name,
                username=username,
                email=email,
                password_hash=hash_password(password),
                company_name=company_name,
                company_address=company_address,
                company_gst=company_gst,
                company_logo_path=company_logo_path or None,
                company_phone=company_phone or None,
            )
            db.add(new_user)
            db.commit()
            return True, "Registration successful."

    @staticmethod
    def login(username, password, remember=False):
        from app.database.connection import SessionLocal
        from app.models.user import User
        from app.utils.security import verify_password

        with SessionLocal() as db:
            user = db.query(User).filter(User.username == username).first()
            if not user or not verify_password(password, user.password_hash):
                return False, "Invalid username or password.", None

            user_data = {
                "id": user.id,
                "username": user.username,
                "full_name": user.full_name,
                "email": user.email,
                "company_name": user.company_name or "My Company",
                "company_address": user.company_address or "",
                "company_gst": user.company_gst or "",
                "company_phone": getattr(user, "company_phone", "") or "",
                "company_logo_path": getattr(user, "company_logo_path", "") or "",
                "preferred_printer": getattr(user, "preferred_printer", "") or "",
            }

            # FIX: Use SessionCache.save() so the file is written to the same
            # location that auto_login() reads from.
            if remember:
                SessionCache.save(user_data)

            return True, "Login successful.", user_data

    @staticmethod
    def logout():
        SessionCache.clear()
        logger.info("User logged out")
        
    @staticmethod
    def refresh_cached_session(user_data: dict):
        """Re-writes the session cache with fresh data (e.g. after Settings
        updates), so auto-login on next launch doesn't load stale info."""
        if os.path.exists(CACHE_FILE):
            SessionCache.save(user_data)

    @staticmethod
    def auto_login() -> Optional[dict]:
        """Check cache and return user data if valid session exists."""
        return SessionCache.load()

    @staticmethod
    def get_branding() -> Optional[dict]:
        """
        Returns the registered company's branding info (name/address/
        phone/logo path) for the LOGIN SCREEN to display, before anyone
        has actually logged in. This app is single-company-per-install,
        so "the registered company" = whichever User row registered one
        first. Returns None if no one has registered a company yet, so
        the login screen can fall back to generic placeholder branding
        instead of a hardcoded company name.
        """
        from app.database.connection import SessionLocal
        from app.models.user import User

        with SessionLocal() as db:
            user = (
                db.query(User)
                .filter(User.company_name.isnot(None), User.company_name != "")
                .order_by(User.id.asc())
                .first()
            )
            if not user:
                return None
            return {
                "company_name": user.company_name,
                "company_address": user.company_address or "",
                "company_phone": getattr(user, "company_phone", "") or "",
                "company_logo_path": getattr(user, "company_logo_path", "") or "",
            }





