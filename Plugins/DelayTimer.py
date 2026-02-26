from __future__ import annotations

import asyncio
from typing import Any, Dict

from Nodes.node import Node


class Self_node(Node):
    """DelayTimer: 在指定秒数后返回 payload。"""

    def __init__(self, data: Dict[str, Any]):
        super().__init__(data)
        self.params = data.get("params", {})
        self.delay = float(self.params.get("seconds", self.params.get("delay", 1)))

    async def execute(self, payload: Any) -> Any:
        try:
            await asyncio.sleep(self.delay)
        except Exception:
            pass
        return payload


__all__ = ["Self_node"]
