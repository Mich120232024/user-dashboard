"""Authentication schemas."""

from pydantic import BaseModel


class Token(BaseModel):
    """Token response schema."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Token data schema."""
    user_id: str | None = None


class TokenRefresh(BaseModel):
    """Token refresh request schema."""
    refresh_token: str