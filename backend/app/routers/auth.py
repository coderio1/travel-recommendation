from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..config import get_settings
from ..crud import user as user_crud
from ..deps import get_current_user, get_db
from ..models.user import User
from ..schemas.auth import LoginIn, RegisterIn, TokenOut, UserOut
from ..security import create_access_token, verify_password

router = APIRouter(prefix="/api/auth", tags=["auth"])
settings = get_settings()


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterIn, db: Session = Depends(get_db)) -> User:
    """Register a new user; returns 409 if the email is already taken."""
    if user_crud.get_by_email(db, payload.email):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    return user_crud.create(db, email=payload.email, password=payload.password, name=payload.name)


@router.post("/login", response_model=TokenOut)
def login(payload: LoginIn, db: Session = Depends(get_db)) -> TokenOut:
    """Validate credentials and return a signed JWT access token."""
    user = user_crud.get_by_email(db, payload.email)
    # Same generic error for missing email vs. wrong password (avoids account enumeration).
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = create_access_token(subject=user.id)
    return TokenOut(access_token=token, expires_in=settings.jwt_expires_minutes * 60)


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)) -> User:
    """Return the profile of the currently authenticated user."""
    return current_user
