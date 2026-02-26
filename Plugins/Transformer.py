from __future__ import annotations

from typing import Any, Dict

from Nodes.node import Node


class Self_node(Node):
    """Transformer: 基于简单模板或映射转化 payload。

    params:
      - template: 可选的字符串模板，使用 payload 作为 format 上下文： template.format(payload=payload)
      - map: 可选的 dict 映射规则，按键从 payload 中抽取
    """

    def __init__(self, data: Dict[str, Any]):
        super().__init__(data)
        self.params = data.get("params", {})
        self.template = self.params.get("template")
        self.map = self.params.get("map") or {}

    async def execute(self, payload: Any) -> Any:
        try:
            if self.template:
                try:
                    return self.template.format(payload=payload)
                except Exception:
                    pass

            if isinstance(self.map, dict) and isinstance(payload, dict):
                out = {}
                for k, pkey in self.map.items():
                    out[k] = payload.get(pkey)
                return out

        except Exception:
            pass
        return payload


__all__ = ["Self_node"]
