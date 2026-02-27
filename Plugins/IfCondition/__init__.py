from typing import Any, List

from Nodes.node import Node


class Self_Node(Node):
    """IfCondition 节点：基于 `context_slot` 指定的布尔值判断分支。

    行为：
    - 读取由 `params.context_slot` 指定的布尔变量，若为 True 激活第一个输出索引（0），否则激活第二个输出索引（1）。

    Context Outputs:
    - 无直接输出到 context；分支依据来自指定节点的 context 中的布尔字段。
    """

    def __init__(self, data: dict, **kwargs) -> None:
        super().__init__(data, **kwargs)

    def _resolve_bool(self) -> bool:
        params = self.params or {}
        slots = params.get("context_slot", [])
        node_getter = getattr(self, "node_getter", None)

        for s in slots:
            try:
                sid = int(s.get("id"))
                key = s.get("key")
            except Exception:
                continue

            # 本节点
            if sid == self.node_id:
                if isinstance(self.context, dict) and key in self.context:
                    return bool(self.context.get(key))
                for c in (self.contexts or []):
                    if isinstance(c, dict) and key in c:
                        return bool(c.get(key))

            # 其它节点
            if callable(node_getter):
                try:
                    target = node_getter(sid)
                    if target is not None:
                        tctx = getattr(target, "context", None)
                        if isinstance(tctx, dict) and key in tctx:
                            return bool(tctx.get(key))
                        for c in getattr(target, "contexts", []) or []:
                            if isinstance(c, dict) and key in c:
                                return bool(c.get(key))
                except Exception:
                    pass

        return False

    def execute(self) -> List[int]:
        result = self._resolve_bool()
        outs = self.outputs or []
        if result:
            # True -> activate first output if exists
            if len(outs) >= 1:
                return [0]
        else:
            # False -> activate second output if exists
            if len(outs) >= 2:
                return [1]

        return []
