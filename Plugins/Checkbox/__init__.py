from typing import Any, List, Optional

from Nodes.node import Node


class Self_Node(Node):
    """Checkbox 节点：展示多个选项给前端，基于 `context_slot` 从上下文中取值。

    行为：
    - 从 `params.context_slot` (list of {id:int, key:str}) 检索上下文值，检索顺序为：
      本节点 `context` -> 本节点 `contexts` 列表 -> 通过注入的 `node_getter(node_id)` 获取目标节点并读取其 `context`/`contexts`。
    - 将构造出的 `options` 缓存到 `ex_hub`（仅用于前端 GET），并将 `FlowListener` 状态设置为 `CHECKBOX`。
    - 返回全部 outputs 的索引（按照 DesignFull，checkbox 激活后续输出）。

    Context Outputs:
    - `selection` (list[str] or list[int]): 用户最终选择的项（在用户 POST 回来后写入节点 `context`，键名由前端/param_config 约定）。
    - 前端可通过 `ex_hub.fetch(node_id)` 获取本节点当前的 `options` 列表（键名 `options`）。
    """

    def __init__(
        self,
        data: dict,
        in_hub=None,
        ex_hub=None,
        interrupt=None,
        listener=None,
        pin_manager=None,
        contexts: Optional[List[Any]] = None,
    ) -> None:
        super().__init__(
            data,
            in_hub=in_hub,
            ex_hub=ex_hub,
            interrupt=interrupt,
            listener=listener,
            pin_manager=pin_manager,
            contexts=contexts,
        )

    def _lookup_context(self, source_id: int, key: str) -> Any:
        # 1. 本节点顶层 context
        if source_id == self.node_id:
            if isinstance(self.context, dict) and key in self.context:
                return self.context.get(key)
            # 查找 self.contexts 列表
            for c in (self.contexts or []):
                if isinstance(c, dict) and key in c:
                    return c.get(key)

        # 2. 通过注入的 node_getter(node_id) 获取目标节点实例并读取其 context
        node_getter = getattr(self, "node_getter", None)
        if callable(node_getter):
            try:
                target_node = node_getter(source_id)
                if target_node is not None:
                    tctx = getattr(target_node, "context", None)
                    if isinstance(tctx, dict) and key in tctx:
                        return tctx.get(key)
                    # 再看 target_node.contexts 列表
                    for c in getattr(target_node, "contexts", []) or []:
                        if isinstance(c, dict) and key in c:
                            return c.get(key)
            except Exception:
                pass

        return None

    def execute(self) -> List[int]:
        params = self.params or {}
        slots = params.get("context_slot", [])

        # 收集上下文值
        values: List[Any] = []
        for s in slots:
            try:
                sid = int(s.get("id"))
                key = s.get("key")
            except Exception:
                continue

            val = self._lookup_context(sid, key)
            values.append(val)

        # 构造 options（将 None 跳过或显示为空字符串）
        options = [str(v) if v is not None else "" for v in values]

        # 设置监听器状态为 CHECKBOX（前端会根据此状态进行交互）
        listener = getattr(self, "listener", None)
        if listener is not None:
            try:
                listener.set_state(self.node_id, "CHECKBOX")
            except Exception:
                pass

        # 将选项缓存到 ex_hub，方便前端 GET
        ex_hub = getattr(self, "ex_hub", None)
        if ex_hub is not None:
            try:
                ex_hub.cache(self.node_id, {"options": options, "node_id": self.node_id})
            except Exception:
                pass

        # checkbox 激活全部 outputs
        return list(range(len(self.outputs or [])))
