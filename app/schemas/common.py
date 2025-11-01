from enum import Enum
from pydantic import BaseModel

class Role(str, Enum):
    Profesor = "Profesor"
    Estudiante = "Estudiante"

class VoteStatus(str, Enum):
    up = "up"
    down = "down"
    none = "none"

class Page(BaseModel):
    items: list
    next_cursor: str | None = None
