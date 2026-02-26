from __future__ import annotations

from typing import Any, Dict, List

from Nodes.node import Node


class Self_node(Node):
    """Merge 插件：在 execute 时读取指定 channels 的最近消息并合并返回/发布。

    params:
      - channels: list of channel names to read
      - output_channel: optional channel to publish merged result
    """

    def __init__(self, data: Dict[str, Any]):
        super().__init__(data)
        self.params = data.get("params", {})
        self.channels: List[str] = list(self.params.get("channels", []))
        self.output_channel: str = self.params.get("output_channel") or f"node:{self.node_id}:merged"

    async def execute(self, payload: Any) -> Any:
        try:
            result = {}
            for ch in self.channels:
                try:
                    val = None
                    if hasattr(self.comm_hub, "get_last"):
                        val = self.comm_hub.get_last(ch)
                    result[ch] = val
                except Exception:
                    result[ch] = None

            # publish merged
            try:
                self.comm_hub.publish(self.output_channel, {"from": self.node_id, "merged": result})
            except Exception:
                pass

            return {"merged": result}
        except Exception as e:
            return {"error": str(e)}


__all__ = ["Self_node"]
