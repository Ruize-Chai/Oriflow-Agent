from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class LLMApiPayload(BaseModel):
    api_key: Optional[str] = None
    endpoint: Optional[str] = None
    
