from __future__ import annotations

import asyncio
from typing import Any, Dict, Optional

from Nodes.node import Node


class Self_node(Node):
    """TextInput: 如果传入 payload 则直接返回；否则尝试通过 comm_hub.request_response 等待外部输入，或返回默认值。"""

    def __init__(self, data: Dict[str, Any]):
        super().__init__(data)
        self.params = data.get("params", {})
        self.channel = self.params.get("channel")
        self.default = self.params.get("default")
        self.prompt = self.params.get("prompt", "Please provide text input")

    async def execute(self, payload: Any) -> Any:
        # prefer explicit payload
        if payload is not None:
            return payload

        # try request_response on comm_hub
        comm = getattr(self, "comm_hub", None)
        if comm is not None and hasattr(comm, "request_response") and self.channel:
            try:
                res = await comm.request_response(self.channel, {"prompt": self.prompt})
                return res
            except asyncio.CancelledError:
                return self.default
            except Exception:
                return self.default

        return self.default


__all__ = ["Self_node"]
