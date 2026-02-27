import asyncio
from typing import Any, List, Optional

from Nodes.node import Node


class Self_Node(Node):
    """Number Input 节点：向前端请求数字输入，等待 `InCommunicateHub` 的回复。

    行为：
    - 设置监听器状态为 `NUMBER INPUT` 并可将提示 `prompt` 缓存到 `ex_hub`。
    - 接收到输入后尝试解析为数值并写入自身 `context`（键名由 `params.param_config.key` 指定，默认 `number`），然后激活输出。

    Context Outputs:
    - `<key>` (int|float): 用户输入的数字，键名由 `params.param_config.key` 指定，默认 `number`。
    """

    def __init__(self, data: dict, **kwargs) -> None:
        super().__init__(data, **kwargs)

    async def execute(self) -> List[int]:
        params = self.params or {}
        cfg = params.get("param_config", {}) or {}
        key = cfg.get("key", "number")

        listener = getattr(self, "listener", None)
        if listener is not None:
            try:
                listener.set_state(self.node_id, "NUMBER INPUT")
            except Exception:
                pass

        prompt = cfg.get("prompt")
        ex_hub = getattr(self, "ex_hub", None)
        if prompt and ex_hub is not None:
            try:
                ex_hub.cache(self.node_id, {"prompt": prompt})
            except Exception:
                pass

        in_hub = getattr(self, "in_hub", None)

        value = None
        if in_hub is not None:
            for _ in range(600):
                try:
                    msg = in_hub.read(self.node_id)
                    if msg is not None:
                        try:
                            msg = in_hub.pop(self.node_id)
                        except Exception:
                            pass
                        if isinstance(msg, dict):
                            raw = msg.get("value") or msg.get("number") or msg.get(key)
                        else:
                            raw = msg
                        if raw is None:
                            value = None
                        else:
                            try:
                                value = float(raw)
                                # if it's an integer value, keep int
                                if isinstance(value, float) and value.is_integer():
                                    value = int(value)
                            except Exception:
                                value = None
                        break
                except Exception:
                    pass
                await asyncio.sleep(0.05)

        if value is not None:
            if not isinstance(self.context, dict):
                try:
                    self.context = {}
                except Exception:
                    pass
            try:
                self.context[key] = value
            except Exception:
                pass

        if listener is not None:
            try:
                listener.set_state(self.node_id, "SILENT")
            except Exception:
                pass

        return list(range(len(self.outputs or [])))
