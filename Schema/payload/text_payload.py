from pydantic import BaseModel


class TextPayload(BaseModel):
    node_id: int
    text: str
