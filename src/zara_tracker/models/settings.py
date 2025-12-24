"""User settings model."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class UserSetting:
    """User setting key-value pair."""
    id: Optional[int] = None
    key: str = ""
    value: str = ""
    updated_at: datetime = field(default_factory=datetime.now)
