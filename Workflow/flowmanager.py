"""引脚/流 管理器模块。

提供一个轻量的 `FlowManager`，用于管理节点之间的输出（source -> targets）
以及目标节点的 listen 依赖（即哪些源节点必须先激活）。

接口说明：
- `bind_outputs(source_id, outputs_list)`: 绑定源节点的输出目标列表
- `bind_node_listen(node_id, listen_nodes)`: 注册目标节点所依赖的源节点集合
- `trigger_from(source_id)`: 标记某个源节点已激活，返回因本次激活而满足条件的目标节点列表
"""
from typing import Any, Dict, List, Optional


class FlowManager:
    """管理节点间的输出映射与监听依赖。

    数据结构：
    - `_outputs`: source_id -> [target_id, ...]
    - `_node_listens`: node_id -> set(required_source_ids)
    - `_node_activated`: node_id -> set(currently_activated_source_ids)
    """

    def __init__(self):
        # source_node_id -> list of target_node_ids
        self._outputs: Dict[int, List[int]] = {}
        # node_id -> set(required source node ids)
        self._node_listens: Dict[int, set] = {}
        # node_id -> currently activated source ids
        self._node_activated: Dict[int, set] = {}

    def bind_outputs(self, source_id: int, outputs_list: List[int]) -> None:
        """将 source_id 的输出目标追加为 outputs_list。"""
        self._outputs.setdefault(source_id, []).extend(outputs_list)

    def bind_node_listen(self, node_id: int, listen_nodes: List[int]) -> None:
        """注册 node_id 依赖的源节点集合（listen_nodes）。"""
        self._node_listens[node_id] = set(listen_nodes)
        self._node_activated.setdefault(node_id, set())

    def trigger_from(self, source_id: int, payload: Optional[Any] = None) -> List[int]:
        """标记 `source_id` 已激活，返回因本次激活而满足依赖的目标节点列表。

        对于没有任何 listen 要求的目标节点，视为立刻就绪。
        对于有 listen 要求的目标节点，只有当累积到达所需源节点集合时才就绪，
        并在就绪后重置激活集合以便下一轮工作。
        """
        ready: List[int] = []
        targets = list(self._outputs.get(source_id, []))
        for tgt in targets:
            if tgt in self._node_listens and len(self._node_listens[tgt]) > 0:
                self._node_activated.setdefault(tgt, set()).add(source_id)
                if self._node_activated[tgt] >= self._node_listens[tgt]:
                    ready.append(tgt)
                    # 就绪后为下一轮清空已激活集合
                    self._node_activated[tgt].clear()
            else:
                # 无依赖的目标节点直接就绪
                ready.append(tgt)
        return ready

    def unbind_all(self) -> None:
        """清除所有绑定关系。"""
        self._outputs.clear()
        self._node_listens.clear()
        self._node_activated.clear()


__all__ = ["FlowManager"]
