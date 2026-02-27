from typing import Any, List, Optional
from pydantic import BaseModel, Field


class NodeState(BaseModel):
    node_id: int
    state: str


class NodeStateListPayload(BaseModel):
    workflow_id: str
    states: List[NodeState] = Field(default_factory=list)
