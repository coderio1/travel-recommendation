from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


def _check_password_bytes(v: str) -> str:
    if len(v.encode()) > 72:
        raise ValueError("password must be 72 bytes or fewer when UTF-8 encoded")
    return v


class RegisterIn(BaseModel):
    email: EmailStr
    name: str | None = None
    password: str = Field(min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def password_fits_bcrypt(cls, v: str) -> str:
        return _check_password_bytes(v)


class LoginIn(BaseModel):
    email: EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def password_fits_bcrypt(cls, v: str) -> str:
        return _check_password_bytes(v)


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    name: str | None = None
