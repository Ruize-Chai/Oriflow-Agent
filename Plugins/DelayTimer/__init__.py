import asyncio
from typing import Any, List

from Nodes.node import Node


class Self_Node(Node):
    """DelayTimer 节点：延时指定秒数后激活输出。

    - `params.param_config.duration` 指定等待秒数（默认 1 秒）。

    Context Outputs:
    - 无（该节点不在 context 中产出数据，仅触发延时后续流程）。
    """

    def __init__(self, data: dict, **kwargs) -> None:
        super().__init__(data, **kwargs)

    async def execute(self) -> List[int]:
        params = self.params or {}
        cfg = params.get("param_config", {}) or {}
        duration = cfg.get("duration", 1)
        try:
            duration = float(duration)
        except Exception:
            duration = 1.0

        # 设置 ACTIVE 状态（可选）
        listener = getattr(self, "listener", None)
        if listener is not None:
            try:
                listener.set_state(self.node_id, "ACTIVE")
            except Exception:
                pass

        # 等待
        await asyncio.sleep(duration)

        if listener is not None:
            try:
                listener.set_state(self.node_id, "SILENT")
            except Exception:
                pass

        return list(range(len(self.outputs or [])))
