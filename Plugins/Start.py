from __future__ import annotations

from typing import Any, Dict

from Nodes.node import Node


class Self_node(Node):
    """Start 节点：工作流入口节点，execute 直接返回 payload。"""

    def __init__(self, data: Dict[str, Any]):
        super().__init__(data)

    async def execute(self, payload: Any) -> Any:
        return payload


__all__ = ["Self_node"]
