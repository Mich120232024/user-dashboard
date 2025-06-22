"""Message model placeholder."""

from pydantic import BaseModel


class Message(BaseModel):
    """Message model."""
    id: str
    subject: str
    body: str