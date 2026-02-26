from __future__ import annotations

from typing import Any, Dict

from Nodes.node import Node


class Self_node(Node):
    """End 节点：工作流结束点，默认把 payload 返回并尝试记录日志（若可用）。"""

    def __init__(self, data: Dict[str, Any]):
        super().__init__(data)

    async def execute(self, payload: Any) -> Any:
        # try to log via comm_hub or logger
        try:
            logger = getattr(self, "logger", None)
            if logger is not None:
                logger.info(f"End node {self.node_id} payload: {payload}")
        except Exception:
            pass
        return payload


__all__ = ["Self_node"]
