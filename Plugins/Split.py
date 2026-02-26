from __future__ import annotations

from typing import Any, Dict, Iterable

from Nodes.node import Node


class Self_node(Node):
    """Split 插件：将 payload（应为 iterable）拆分并向指定通道发布每一项。

    params:
      - channel: 发布到的通道（可选，默认基于 node id）
    """

    def __init__(self, data: Dict[str, Any]):
        super().__init__(data)
        self.params = data.get("params", {})
        self.channel = self.params.get("channel") or f"node:{self.node_id}:split"

    async def execute(self, payload: Any) -> Any:
        try:
            items = []
            if isinstance(payload, (list, tuple)):
                items = payload
            elif hasattr(payload, "__iter__") and not isinstance(payload, (str, bytes, dict)):
                items = list(payload)
            else:
                # nothing to split
                return {"error": "payload not iterable"}

            # publish each item if comm_hub is available
            comm = getattr(self, "comm_hub", None)
            for it in items:
                try:
                    if comm is not None:
                        comm.publish(self.channel, {"from": self.node_id, "item": it})
                except Exception:
                    pass

            return {"count": len(items)}
        except Exception as e:
            return {"error": str(e)}


__all__ = ["Self_node"]
