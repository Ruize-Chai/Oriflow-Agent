from typing import Any, List, Optional, Dict
from pydantic import BaseModel, Field


class ContextSlot(BaseModel):
    id: int
    key: str


class NodeParams(BaseModel):
    context_slot: Optional[List[ContextSlot]] = Field(default_factory=list)
    config_options: Optional[List[Any]] = None


class NodePayload(BaseModel):
    """Pydantic payload 对应 node_data_schema.json"""

    type: str
    inputs: List[int] = Field(default_factory=list)
    outputs: List[Optional[int]] = Field(default_factory=list)
    context: Dict[str, Any] = Field(default_factory=dict)
    params: NodeParams
    listen: Optional[List[int]] = Field(default_factory=list)
