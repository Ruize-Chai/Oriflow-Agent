"""
Flow 监听器模块。

提供一个轻量的 `FlowListener` 注册表，用于将回调绑定到节点状态事件。
回调签名为 (node_id: int, event: str, payload: Any)。

注册是同步的；回调可以是协程，`notify` 在调用时会 await 协程回调。
此模块仅负责注册与分发，不承担回调内部的错误处理。
"""
from typing import Any, Callable, Dict, List
import asyncio

CallbackType = Callable[[int, str, Any], Any]


class FlowListener:
    """节点状态监听注册表。

    - `register(node_id, callback)`: 为指定节点添加回调（可重复添加多个）
    - `unregister(node_id, callback)`: 移除回调
    - `notify(node_id, event, payload)`: 异步调用该节点的所有回调
    """

    def __init__(self):
        self._listeners: Dict[int, List[CallbackType]] = {}

    def register(self, node_id: int, callback: CallbackType) -> None:
        lst = self._listeners.setdefault(node_id, [])
        lst.append(callback)

    def unregister(self, node_id: int, callback: CallbackType) -> None:
        lst = self._listeners.get(node_id)
        if not lst:
            return
        try:
            lst.remove(callback)
        except ValueError:
            pass

    async def notify(self, node_id: int, event: str, payload: Any = None) -> None:
        """异步调用 `node_id` 的所有已注册回调。

        如果回调返回协程（是协程函数），则会对其进行 await；回调内部异常会被忽略。
        """
        lst = list(self._listeners.get(node_id, []))
        for cb in lst:
            try:
                res = cb(node_id, event, payload)
                if asyncio.iscoroutine(res):
                    await res
            except Exception:
                # 忽略回调中的异常，避免影响其它回调
                pass


__all__ = ["FlowListener"]
'''
workflow通过绑定listener,实现对流状态的流式监控。
'''