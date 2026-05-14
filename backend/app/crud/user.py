from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models.user import User
from ..security import hash_password


def get_by_email(db: Session, email: str) -> User | None:
    """Look up a user by email address; returns None if not found."""
    return db.execute(select(User).where(User.email == email)).scalar_one_or_none()


def create(db: Session, *, email: str, password: str, name: str | None) -> User:
    """Create a new user with a bcrypt-hashed password."""
    user = User(email=email, name=name, password_hash=hash_password(password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
