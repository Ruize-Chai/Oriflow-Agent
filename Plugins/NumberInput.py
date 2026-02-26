from __future__ import annotations

import asyncio
from typing import Any, Dict, Optional

from Nodes.node import Node


class Self_node(Node):
    """NumberInput: 类似 TextInput，但尝试将结果转换为数字。"""

    def __init__(self, data: Dict[str, Any]):
        super().__init__(data)
        self.params = data.get("params", {})
        self.channel = self.params.get("channel")
        self.default = self.params.get("default")
        self.prompt = self.params.get("prompt", "Please provide numeric input")

    async def execute(self, payload: Any) -> Any:
        if payload is not None:
            try:
                return float(payload)
            except Exception:
                return self.default

        comm = getattr(self, "comm_hub", None)
        if comm is not None and hasattr(comm, "request_response") and self.channel:
            try:
                res = await comm.request_response(self.channel, {"prompt": self.prompt})
                return float(res) if res is not None else self.default
            except Exception:
                return self.default

        return self.default


__all__ = ["Self_node"]
