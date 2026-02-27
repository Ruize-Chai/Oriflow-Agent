from pydantic import BaseModel


class NumberPayload(BaseModel):
    node_id: int
    value: float
