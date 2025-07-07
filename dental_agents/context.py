from dataclasses import dataclass
from sqlmodel import Session

from api.security.auth import User

@dataclass
class AssistantContext:
    """The context object to hold all shared dependencies for a run."""
    db: Session
    user: User