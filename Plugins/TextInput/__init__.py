import asyncio
from typing import Any, List, Optional

from Nodes.node import Node


class Self_Node(Node):
    """Text Input 节点：向前端请求文本输入，等待 `InCommunicateHub` 的回复。

    行为：
    - 设置监听器状态为 `TEXT INPUT` 并可将提示 `prompt` 缓存到 `ex_hub`，前端读取后展示并 POST 回来。
    - 接收到输入后写入自身 `context`（键名由 `params.param_config.key` 指定，默认 `text`），并激活全部 outputs。

    Context Outputs:
    - `<key>` (str): 用户输入的文本，键名由 `params.param_config.key` 指定，默认 `text`。
    """

    def __init__(self, data: dict, **kwargs) -> None:
        super().__init__(data, **kwargs)

    async def execute(self) -> List[int]:
        params = self.params or {}
        cfg = params.get("param_config", {}) or {}
        key = cfg.get("key", "text")

        listener = getattr(self, "listener", None)
        if listener is not None:
            try:
                listener.set_state(self.node_id, "TEXT INPUT")
            except Exception:
                pass

        # 可选提示内容缓存给前端
        prompt = cfg.get("prompt")
        ex_hub = getattr(self, "ex_hub", None)
        if prompt and ex_hub is not None:
            try:
                ex_hub.cache(self.node_id, {"prompt": prompt})
            except Exception:
                pass

        in_hub = getattr(self, "in_hub", None)

        # 等待 front-end 通过 in_hub.send(node_id, payload) 发送输入
        value = None
        if in_hub is not None:
            # poll 非阻塞地等待（InCommunicateHub 为同步结构）
            for _ in range(600):
                try:
                    msg = in_hub.read(self.node_id)
                    if msg is not None:
                        # 尝试 pop 以清除
                        try:
                            msg = in_hub.pop(self.node_id)
                        except Exception:
                            pass
                        # 支持直接字符串或 dict
                        if isinstance(msg, dict):
                            value = msg.get("value") or msg.get("text") or msg.get(key)
                        else:
                            value = msg
                        break
                except Exception:
                    pass
                await asyncio.sleep(0.05)

        # 写入自身 context
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

        # 恢复监听器状态为 SILENT
        if listener is not None:
            try:
                listener.set_state(self.node_id, "SILENT")
            except Exception:
                pass

        return list(range(len(self.outputs or [])))
