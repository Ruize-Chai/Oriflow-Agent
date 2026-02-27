from typing import Any, List, Optional

from Nodes.node import Node


class Self_Node(Node):
    """END 节点：没有输出，作为流程终点。

    Context Outputs:
    - 无（终点节点不在 context 中产出数据）。
    """

    def __init__(self, data: dict, **kwargs) -> None:
        super().__init__(data, **kwargs)

    def execute(self) -> List[int]:
        # END 节点不激活任何下游
        return []
