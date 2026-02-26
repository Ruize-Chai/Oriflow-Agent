from __future__ import annotations

import asyncio
from typing import Any, Dict, List

from Nodes.node import Node


class Self_node(Node):
    """Dropdown: 等待用户选择一个选项，支持默认值和验证选项集合。"""

    def __init__(self, data: Dict[str, Any]):
        super().__init__(data)
        self.params = data.get("params", {})
        self.options: List[Any] = list(self.params.get("options", []))
        self.channel = self.params.get("channel")
        self.default = self.params.get("default")
        self.prompt = self.params.get("prompt", "Please choose an option")

    async def execute(self, payload: Any) -> Any:
        if payload is not None:
            if not self.options or payload in self.options:
                return payload
            return self.default

        comm = getattr(self, "comm_hub", None)
        if comm is not None and hasattr(comm, "request_response") and self.channel:
            try:
                res = await comm.request_response(self.channel, {"prompt": self.prompt, "options": self.options})
                if res in self.options:
                    return res
                return self.default
            except Exception:
                return self.default

        return self.default


__all__ = ["Self_node"]
