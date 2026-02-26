from __future__ import annotations

from typing import Any, Dict

from Nodes.node import Node


class Self_node(Node):
    """IfCondition 插件：根据 payload 中的键值判断并将结果发布到指定通道。

    params:
      - key: payload 中的键（支持点号路径，例如 'user.age'）
      - equals: 与之比较的值（可选）
      - true_channel / false_channel: 要发布的通道（可选，默认基于 node id）
    """

    def __init__(self, data: Dict[str, Any]):
        super().__init__(data)
        self.params = data.get("params", {})
        self.key = self.params.get("key")
        self.equals = self.params.get("equals", None)
        self.true_ch = self.params.get("true_channel") or f"node:{self.node_id}:true"
        self.false_ch = self.params.get("false_channel") or f"node:{self.node_id}:false"

    def _get_by_path(self, obj: Dict[str, Any], path: str):
        if not path:
            return None
        cur = obj
        for p in path.split("."):
            if not isinstance(cur, dict):
                return None
            cur = cur.get(p)
        return cur

    async def execute(self, payload: Any) -> Any:
        # ensure result is always defined even if an exception occurs
        result = False
        try:
            val = None
            if isinstance(payload, dict) and self.key:
                val = self._get_by_path(payload, self.key)
            else:
                val = payload

            if self.equals is None:
                # truthiness check
                result = bool(val)
            else:
                result = val == self.equals

            # publish branch message for downstream subscribers if hub is available
            try:
                comm = getattr(self, "comm_hub", None)
                if comm is not None:
                    comm.publish(self.true_ch if result else self.false_ch, {"from": self.node_id, "payload": payload, "branch": result})
            except Exception:
                pass
        except Exception:
            # keep result as False on error
            pass

        return {"branch": result}


__all__ = ["Self_node"]
