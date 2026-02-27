from typing import Any, Optional
from pydantic import BaseModel


class ChatboxOutputPayload(BaseModel):
    node_id: int
    message: str
    meta: Optional[Any] = None
