from typing import Any, List

from Nodes.node import Node


class Self_Node(Node):
    """Chatbox 节点：从指定的 context_slot 中收集上下文并向前端展示为聊天输出。

    行为：
    - 收集由 `params.context_slot` 列表指定的上下文项并合并为消息文本。
    - 将消息缓存到 `ex_hub`（键名由 `param_config.message_key` 指定，默认 `message`），并将 `FlowListener` 状态设置为 `OUTPUT`。

    Context Outputs:
    - `message` (str): 合并后的聊天消息文本，键名可通过 `param_config.message_key` 覆盖。
    """

    def __init__(self, data: dict, **kwargs) -> None:
        super().__init__(data, **kwargs)

    def _gather_contexts(self) -> List[str]:
        params = self.params or {}
        slots = params.get("context_slot", [])
        results: List[str] = []
        node_getter = getattr(self, "node_getter", None)
        for s in slots:
            try:
                sid = int(s.get("id"))
                key = s.get("key")
            except Exception:
                continue

            # 优先本节点
            if sid == self.node_id:
                if isinstance(self.context, dict) and key in self.context:
                    results.append(str(self.context.get(key)))
                    continue
                for c in (self.contexts or []):
                    if isinstance(c, dict) and key in c:
                        results.append(str(c.get(key)))
                        continue

            # 通过 node_getter 获取其他节点
            if callable(node_getter):
                try:
                    target = node_getter(sid)
                    if target is not None:
                        tctx = getattr(target, "context", None)
                        if isinstance(tctx, dict) and key in tctx:
                            results.append(str(tctx.get(key)))
                            continue
                        for c in getattr(target, "contexts", []) or []:
                            if isinstance(c, dict) and key in c:
                                results.append(str(c.get(key)))
                                continue
                except Exception:
                    pass

        return results

    def execute(self) -> List[int]:
        params = self.params or {}
        cfg = params.get("param_config", {}) or {}
        message_key = cfg.get("message_key", "message")

        contents = self._gather_contexts()
        message = "\n".join(contents)

        listener = getattr(self, "listener", None)
        if listener is not None:
            try:
                listener.set_state(self.node_id, "OUTPUT")
            except Exception:
                pass

        ex_hub = getattr(self, "ex_hub", None)
        if ex_hub is not None:
            try:
                ex_hub.cache(self.node_id, {message_key: message})
            except Exception:
                pass

        # 激活全部 outputs
        return list(range(len(self.outputs or [])))
