"""User model."""

from typing import Optional
from pydantic import BaseModel, EmailStr


class User(BaseModel):
    """User model."""
    id: str
    email: EmailStr
    username: str
    full_name: Optional[str] = None
    is_active: bool = True
    is_superuser: bool = False


class UserCreate(BaseModel):
    """User creation schema."""
    email: EmailStr
    username: str
    password: str
    full_name: Optional[str] = None


class UserUpdate(BaseModel):
    """User update schema."""
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    full_name: Optional[str] = None
    password: Optional[str] = None