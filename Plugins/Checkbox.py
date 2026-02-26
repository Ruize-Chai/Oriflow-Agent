from __future__ import annotations

from typing import Any, Dict

from Nodes.node import Node


class Self_node(Node):
    """Checkbox: 返回布尔值，支持默认值或外部确认。"""

    def __init__(self, data: Dict[str, Any]):
        super().__init__(data)
        self.params = data.get("params", {})
        self.channel = self.params.get("channel")
        self.default = bool(self.params.get("default", False))
        self.prompt = self.params.get("prompt", "Please confirm (true/false)")

    async def execute(self, payload: Any) -> Any:
        if payload is not None:
            return bool(payload)

        comm = getattr(self, "comm_hub", None)
        if comm is not None and hasattr(comm, "request_response") and self.channel:
            try:
                res = await comm.request_response(self.channel, {"prompt": self.prompt})
                return bool(res)
            except Exception:
                return self.default

        return self.default


__all__ = ["Self_node"]
