"""bcrypt password hashing and JWT token handling."""

from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
from jose import JWTError, jwt

from .config import get_settings

settings = get_settings()

def hash_password(plain: str) -> str:
    """Return a bcrypt hash of the given plain-text password."""
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    """Return True if plain matches the stored bcrypt hash, False otherwise."""
    if not hashed:
        return False
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def create_access_token(subject: str | int, extra_claims: dict[str, Any] | None = None) -> str:
    """Create a signed JWT with `sub`, `iat`, `exp`."""
    now = datetime.now(tz=timezone.utc)
    expires = now + timedelta(minutes=settings.jwt_expires_minutes)

    payload: dict[str, Any] = {
        "sub": str(subject),
        "iat": int(now.timestamp()),
        "exp": int(expires.timestamp()),
    }
    if extra_claims:
        payload.update(extra_claims)

    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict[str, Any]:
    """JWT decoding and validating. Raises `JWTError` on any failure (sig, expiry, format)."""
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])


# Re-export. Bridging direct import from jose.
__all__ = [
    "hash_password",
    "verify_password",
    "create_access_token",
    "decode_access_token",
    "JWTError",
]
