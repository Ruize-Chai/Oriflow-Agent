from typing import List
from pydantic import BaseModel, Field


class CheckboxOptionsPayload(BaseModel):
    node_id: int
    options: List[str] = Field(default_factory=list)


class CheckboxSelectionPayload(BaseModel):
    node_id: int
    selections: List[int] = Field(default_factory=list)
