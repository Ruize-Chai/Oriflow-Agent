from typing import List, Optional
from pydantic import BaseModel


class PluginInfo(BaseModel):
    id: Optional[str]
    name: str
    type: str
    description: Optional[str] = None
    category: Optional[str] = None
    version: Optional[str] = None
    tags: Optional[List[str]] = None


class PluginListPayload(BaseModel):
    plugins: List[PluginInfo]


class PluginRequestPayload(BaseModel):
    # 请求特定 plugin 的标识符，可用 name 或 type
    name: Optional[str] = None
    type: Optional[str] = None


class PluginDetailPayload(BaseModel):
    plugin: PluginInfo
