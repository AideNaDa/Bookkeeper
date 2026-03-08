from pydantic import BaseModel
from typing import List
from core.states import States


class Response(BaseModel):
    text: str
    keyboard: List[str] | None = None
    new_state: States | None = None
