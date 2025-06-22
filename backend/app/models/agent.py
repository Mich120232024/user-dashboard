"""Agent model placeholder."""

from pydantic import BaseModel


class Agent(BaseModel):
    """Agent model."""
    id: str
    name: str
    status: str = "active"