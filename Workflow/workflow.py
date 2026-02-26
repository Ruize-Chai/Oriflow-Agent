from typing import Any, Dict, List, Optional
import asyncio

from Schema.base.workflow_base import BaseWorkflow
from Nodes.pluginSeeker import Search_Node
from Workflow.flowlistener import FlowListener
from Workflow.flowmanager import FlowManager
from Workflow.comm_interface import CommunicationHub


class Workflow(BaseWorkflow):
    """运行时工作流类。

    该类从 `BaseWorkflow` 派生：
    - 使用 `Search_Node` 实例化每个节点插件
    - 为每个节点注册 `FlowListener` 回调以接收节点完成事件
    - 使用 `FlowManager` 绑定节点间的输出与 listen 依赖关系
    """

    def __init__(self, data: Dict[str, Any]):
        super().__init__(data)
        # 运行时结构
        # 保持 BaseWorkflow.nodes（节点定义列表）不变；运行时实例保存在 `node_map`
        self.node_map: Dict[int, Any] = {}
        self.flow_listener = FlowListener()
        self.flow_manager = FlowManager()
        # 通用通信枢纽，提供节点与外部/人工输入的多路通信能力
        self.comm_hub = CommunicationHub()

        # build nodes and bindings
        self._build()

    def _build(self) -> None:
        # 遍历基类中存储的节点定义（列表），构建实例并完成绑定
        for n in self.nodes:
            node_obj = Search_Node(n.get("type"), n)
            # 注入通用通信枢纽引用到节点（若节点实现使用）
            try:
                node_obj.comm_hub = self.comm_hub
            except Exception:
                pass
            nid = n.get("id")
            # wrap instance execute to notify workflow when done
            orig_execute = getattr(node_obj, "execute", None)
            if orig_execute is not None:
                # 为实例包装 execute，使其在完成后通知 workflow（避免闭包晚绑定）
                async def _wrapped_execute(payload, _nid=nid, _orig=orig_execute):
                    res = None
                    try:
                        res = await _orig(payload)
                    except Exception:
                        # 执行错误由节点内部或上层处理；仍然会通知完成事件
                        pass
                    # 通知监听器该节点已完成
                    try:
                        await self.flow_listener.notify(_nid, "done", payload)
                    except Exception:
                        pass
                    return res
                # 将包装后的执行函数绑定到实例上
                node_obj.execute = _wrapped_execute

            # start listener task on node
            try:
                node_obj.start_listener()
            except Exception:
                pass
            self.node_map[nid] = node_obj

            # 注册该节点到通信枢纽，允许外部或工具通过 hub 直接发送消息到节点
            def _node_comm_callback(_node_id: int, channel: str, message: Any):
                # 默认行为：收到消息则触发节点（可由插件处理 payload）
                try:
                    node_obj.trigger(message)
                except Exception:
                    pass

            self.comm_hub.register_node(nid, _node_comm_callback)

            # 如果节点 params 中声明了要订阅的 channel，则自动订阅
            sub_chs = []
            try:
                sub_chs = list(n.get("params", {}).get("subscribe", []))
            except Exception:
                sub_chs = []
            for ch in sub_chs:
                # 将节点触发绑定到该 channel 的消息分发
                self.comm_hub.subscribe(ch, _node_comm_callback)

            # 绑定该节点的 listen 依赖（即该节点等待哪些源节点）
            listen_nodes = n.get("listen", []) or []
            self.flow_manager.bind_node_listen(nid, listen_nodes)

            # 绑定输出：将该节点 -> 其目标节点 id 列表注册到 FlowManager
            outputs = [o for o in (n.get("outputs") or []) if o is not None]
            if outputs:
                self.flow_manager.bind_outputs(nid, outputs)

            # register a simple listener that will be notified on node events
            async def _cb(node_id: int, event: str, payload: Any = None):
                # 默认行为：节点发出 'done' 事件后，通过 FlowManager 决定并触发目标节点
                if event == "done":
                    node = self.node_map.get(node_id)
                    if not node:
                        return
                    # 询问 FlowManager：本次 source 激活后哪些目标节点就绪
                    ready_nodes = self.flow_manager.trigger_from(node_id, payload)
                    for rn in ready_nodes:
                        target = self.node_map.get(rn)
                        if target:
                            target.trigger(payload)

            self.flow_listener.register(nid, _cb)

    # BaseWorkflow already stores node definitions in `self.nodes` (list of dicts).
    # Use those directly where needed.

    def start(self, payload: Optional[Any] = None) -> None:
        """Start the workflow by triggering the entry node's outputs (pin 0 convention).

        This will activate nodes according to the pin bindings.
        """
        # 解析 entry：优先按节点 id 解析，其次将其视为在节点定义列表中的索引
        entry_id = None
        if self.entry in self.node_map:
            entry_id = self.entry
        elif isinstance(self.entry, int):
            # 尝试在基类节点定义中寻找匹配 id
            for nd in self.nodes:
                if nd.get("id") == self.entry:
                    entry_id = self.entry
                    break
            # 若仍未找到，则将 entry 当作索引
            if entry_id is None:
                if 0 <= self.entry < len(self.nodes):
                    entry_id = self.nodes[self.entry].get("id")

        if entry_id is None:
            # 无法解析入口，静默返回
            return

        node = self.node_map.get(entry_id)
        if node:
            node.trigger(payload)

    def stop(self) -> None:
        for n in self.node_map.values():
            try:
                n.stop()
            except Exception:
                pass


__all__ = ["Workflow"]

