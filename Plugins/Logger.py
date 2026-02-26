from __future__ import annotations

from typing import Any, Dict

from Nodes.node import Node

try:
    from Logger import get_logger
except Exception:
    get_logger = None


class Self_node(Node):
    """Logger 插件：将 payload 记录到默认 logger 或打印到 stdout。"""

    def __init__(self, data: Dict[str, Any]):
        super().__init__(data)
        self.params = data.get("params", {})
        self.level = self.params.get("level", "info")
        try:
            self._logger = get_logger() if get_logger is not None else None
        except Exception:
            self._logger = None

    async def execute(self, payload: Any) -> Any:
        try:
            if self._logger is not None:
                lvl = self.level.lower()
                if lvl == "debug":
                    self._logger.debug(payload)
                elif lvl == "warning":
                    self._logger.warning(payload)
                elif lvl == "error":
                    self._logger.error(payload)
                else:
                    self._logger.info(payload)
            else:
                print(f"Logger[{self.node_id}]:", payload)
        except Exception:
            pass
        return payload


__all__ = ["Self_node"]
