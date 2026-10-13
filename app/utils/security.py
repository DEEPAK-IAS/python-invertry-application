from __future__ import annotations
import hashlib
import os

def hash_password(password: str) -> str:
    """Hashes a password securely using PBKDF2 HMAC with a random salt."""
    salt = os.urandom(32)
    pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    return salt.hex() + ':' + pwd_hash.hex()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a stored password against the provided plain text password."""
    try:
        salt_hex, hash_hex = hashed_password.split(':')
        salt = bytes.fromhex(salt_hex)
        pwd_hash = hashlib.pbkdf2_hmac('sha256', plain_password.encode('utf-8'), salt, 100000)
        return pwd_hash.hex() == hash_hex
    except Exception:
        # If the string is malformed or doesn't match, return False
        return False




