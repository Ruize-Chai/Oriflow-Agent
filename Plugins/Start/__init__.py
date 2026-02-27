from typing import List, Any, Optional

from Nodes.node import Node


class Self_Node(Node):
    """Start 节点：入口节点，激活所有输出。

    按约定构造函数接受 (data, in_hub=None, ex_hub=None, interrupt=None, listener=None, pin_manager=None, contexts=None)
    """
    """
    Context Outputs:
    - 无（Start 节点本身不在 context 中产出业务数据）。
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

    def execute(self) -> List[int]:
        """返回所有 outputs 的索引，表示全部激活。"""
        return list(range(len(self.outputs or [])))
