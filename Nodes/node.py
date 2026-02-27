from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
import asyncio
import inspect

from Schema.base.node_base import BaseNode

try:
    # runtime helpers (may be None during unit tests)
    from Workflow.In_communicateHub import InCommunicateHub
    from Workflow.Ex_communicateHub import ExCommunicateHub
    from Workflow.interrupt import Interrupt
    from Workflow.listener import FlowListener
    from Workflow.pin_manager import PinManager
except Exception:  # pragma: no cover - optional runtime bindings
    InCommunicateHub = Any  # type: ignore
    ExCommunicateHub = Any  # type: ignore
    Interrupt = Any  # type: ignore
    FlowListener = Any  # type: ignore
    PinManager = Any  # type: ignore


class Node(BaseNode, ABC):
    """节点抽象类：继承自 `BaseNode`，插件应实现 `execute()`。

    构造时可以绑定运行时服务：内部/外部通信总线、中断器、监听器和引脚管理器。
    - `execute()` 返回一个 int 列表，表示要激活的 outputs 的索引（基于 `self.outputs` 顺序）。
    - 实例会构建 `listen_table`（来自 node.listen）和 `output_table`（index -> node_id）。
    - 框架负责在 `run()` 后将激活的输出写入 `in_hub` 并通过 `pin_manager` 激活对应引脚。
    """

    def __init__(self, data: Dict, in_hub=None, ex_hub=None, interrupt=None, listener=None, pin_manager=None, contexts: Optional[List[Any]] = None) -> None:
        super().__init__(data)

        # 绑定运行时服务（可为 None，在测试时可不提供）
        self.in_hub = in_hub
        self.ex_hub = ex_hub
        self.interrupt = interrupt
        self.listener = listener
        self.pin_manager = pin_manager

        # 构造 listen/output 表
        # listen_table: set of incoming node ids
        self.listen_table = set(int(x) for x in (self.listen or []))

        # output_table: index -> target node id (None allowed to mean terminal)
        self.output_table: Dict[int, Optional[int]] = {
            idx: (None if out is None else int(out))
            for idx, out in enumerate(self.outputs or [])
        }
        # 额外的上下文列表（按用户要求）
        self.contexts: List[Any] = list(contexts) if contexts is not None else []

    @abstractmethod
    def execute(self) -> object:
        """执行节点逻辑并返回要激活的 outputs 索引列表。

        返回值可以是同步的 `List[int]`，也可以是协程/awaitable（框架会在 `serve()` 中 await）。
        插件实现应只关注业务逻辑; 框架负责处理 awaitable 结果。
        """
        raise NotImplementedError()

    async def serve(self, timeout: Optional[float] = None) -> List[int]:
        """异步运行节点：

        步骤：
        1. 等待所有前置引脚触发（通过 `PinManager.wait_async`）
        2. 更新 `FlowListener` 为 ACTIVE
        3. 调用 `execute()`（支持协程或普通函数）
        4. 若未被 `Interrupt` 中断，触发后置引脚并通知 `InCommunicateHub`/`ExCommunicateHub`/`PinManager`
        5. 更新 `FlowListener` 为 SILENT 并返回激活的目标节点 id 列表
        """

        # 1) 等待前置引脚
        if self.pin_manager is not None and self.listen_table:
            waits = [self.pin_manager.wait_async(pid) for pid in self.listen_table]
            try:
                if timeout is None:
                    await asyncio.gather(*waits)
                else:
                    await asyncio.wait_for(asyncio.gather(*waits), timeout=timeout)
            except asyncio.TimeoutError:
                # 超时视为未触发，不执行
                return []

        # 2) 更新监视器
        listener = getattr(self, "listener", None)
        if listener is not None:
            try:
                listener.set_state(self.node_id, "ACTIVE")
            except Exception:
                pass

        # 3) 执行业务逻辑（支持 coroutine 或普通函数）
        try:
            result = self.execute()
            if inspect.isawaitable(result):
                activated_indices = await result  # type: ignore
            else:
                activated_indices = result
        except Exception:
            # 在执行期间若出现异常，尽量通知监听器并不向下传播
            try:
                if listener is not None:
                    listener.set_state(self.node_id, "SILENT")
            except Exception:
                pass
            return []

        # 确保返回列表
        if not isinstance(activated_indices, list):
            activated_indices = []

        # 强制转换为列表以满足静态类型检查与后续迭代
        if isinstance(activated_indices, list):
            activated_list: List[int] = list(activated_indices)
        else:
            try:
                activated_list = list(activated_indices)  # type: ignore
            except Exception:
                activated_list = []

        # 4) 中断检查与输出触发
        interrupt = getattr(self, "interrupt", None)
        if interrupt is not None and interrupt.is_set():
            try:
                if listener is not None:
                    listener.set_state(self.node_id, "SILENT")
            except Exception:
                pass
            return []

        activated_targets: List[int] = []
        for idx in activated_list:
            target = self.output_table.get(int(idx))
            if target is None:
                # 终点
                if self.pin_manager is not None:
                    try:
                        self.pin_manager.activate(-1)
                    except Exception:
                        pass
                continue

            activated_targets.append(target)
            # 触发目标引脚（节点间通信通过 PinManager）
            if self.pin_manager is not None:
                try:
                    self.pin_manager.activate(target)
                except Exception:
                    pass

            # 向前端缓存激活信息（ex_hub 用于前端/后端通信，非节点间消息传递）
            ex_hub = getattr(self, "ex_hub", None)
            if ex_hub is not None:
                try:
                    ex_hub.cache(self.node_id, {"activated": target})
                except Exception:
                    pass

        # 5) 更新监听器为 SILENT
        if listener is not None:
            try:
                listener.set_state(self.node_id, "SILENT")
            except Exception:
                pass

        return activated_targets
    




    #暂时不使用：
    def run(self) -> List[int]:
        """向后兼容同步运行接口：直接调用 execute() 并处理输出（不等待 pins）。"""
        activated_indices = []
        try:
            activated_indices = self.execute()
        except Exception:
            return []

        if not isinstance(activated_indices, list):
            try:
                activated_indices = list(activated_indices)  # type: ignore
            except Exception:
                activated_indices = []

        activated_targets: List[int] = []
        for idx in activated_indices:
            target = self.output_table.get(int(idx))
            if target is None:
                if self.pin_manager is not None:
                    try:
                        self.pin_manager.activate(-1)
                    except Exception:
                        pass
                continue

            activated_targets.append(target)
            # 使用 PinManager 激活目标引脚（节点间不通过 in_hub）
            if self.pin_manager is not None:
                try:
                    self.pin_manager.activate(target)
                except Exception:
                    pass

            # 向前端缓存激活信息（ex_hub 仍可用于前端/后端通信）
            ex_hub = getattr(self, "ex_hub", None)
            if ex_hub is not None:
                try:
                    ex_hub.cache(self.node_id, {"activated": target})
                except Exception:
                    pass

        return activated_targets
    



