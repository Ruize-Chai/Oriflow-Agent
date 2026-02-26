"""
通用通信接口(Communication Hub)

职责：
- 在工作流内部为节点与外部系统提供多路通道(channel)通信能力。
- 支持节点订阅通道、发布消息、外部注入（人工输入）、请求-响应模式（可 await)。
- 使用 asyncio 实现异步发布/分发，保持可扩展与非阻塞。

设计要点：
- channel 为字符串标识；同一 channel 可有多个订阅者（回调或协程）。
- 支持按 node_id 直接发送消息(hub 会查找 node 的回调并调用）。
- 为外部输入预留 `inject_external`，外部系统（或人工界面）可通过该方法发送消息到某个 channel。
- 提供 `request_response` 简单实现，返回 Future,便于实现等待人工确认。

此模块为独立单元，后续由 workflow 与节点在初始化时注册回调或将 hub 暴露给插件使用。
"""
from __future__ import annotations

import asyncio
from typing import Any, Awaitable, Callable, Dict, List, Optional

Callback = Callable[[int, str, Any], Any]


class CommunicationHub:
    """多通道通信枢纽。

    API 简要说明：
    - `create_channel(name)`: 创建通道（幂等）
    - `subscribe(channel, callback)`: 订阅通道（回调可为协程函数）
    - `unsubscribe(channel, callback)`: 取消订阅
    - `publish(channel, message)`: 异步发布消息到通道（不等待回调完成）
    - `send_to_node(node_id, message)`: 直接发送到某个节点回调（若已注册）
    - `request_response(channel, message, timeout)`: 发布并等待单一响应（用于人工输入/确认）
    - `inject_external(channel, message)`: 外部/人工输入的快捷接口
    """

    def __init__(self):
        # channel -> list(callback)
        self._channels: Dict[str, List[Callback]] = {}
        # node_id -> callback (直接发送映射)
        self._node_map: Dict[int, Callback] = {}
        # request_response pending futures: channel -> list of futures
        self._pending: Dict[str, List[asyncio.Future]] = {}
        # last published message per channel（用于 Merge 等插件读取最近值）
        self._last_message: Dict[str, Any] = {}
        # background dispatch queue
        self._queue: asyncio.Queue = asyncio.Queue()
        self._dispatcher_task: Optional[asyncio.Task] = None

    def create_channel(self, name: str) -> None:
        self._channels.setdefault(name, [])

    def subscribe(self, channel: str, callback: Callback) -> None:
        """订阅 channel，回调签名为 (node_id:int| -1, channel:str, message:any)。"""
        self._channels.setdefault(channel, []).append(callback)

    def unsubscribe(self, channel: str, callback: Callback) -> None:
        lst = self._channels.get(channel)
        if not lst:
            return
        try:
            lst.remove(callback)
        except ValueError:
            pass

    def register_node(self, node_id: int, callback: Callback) -> None:
        """为直接发送注册节点回调。"""
        self._node_map[node_id] = callback

    def unregister_node(self, node_id: int) -> None:
        self._node_map.pop(node_id, None)

    async def _dispatcher(self) -> None:
        while True:
            channel, message = await self._queue.get()
            callbacks = list(self._channels.get(channel, []))
            for cb in callbacks:
                try:
                    res = cb(-1, channel, message)
                    if asyncio.iscoroutine(res):
                        await res
                except Exception:
                    # 忽略回调内异常
                    pass

    def _ensure_dispatcher(self) -> None:
        if self._dispatcher_task is None or self._dispatcher_task.done():
            self._dispatcher_task = asyncio.create_task(self._dispatcher())

    def publish(self, channel: str, message: Any) -> None:
        """异步将消息投递到 channel,返回立即返回（非阻塞）。"""
        self.create_channel(channel)
        # store last message
        try:
            self._last_message[channel] = message
        except Exception:
            pass
        self._ensure_dispatcher()
        # 放入队列由 dispatcher 处理
        self._queue.put_nowait((channel, message))

    def send_to_node(self, node_id: int, message: Any) -> None:
        """同步触发 node_id 的回调（若为协程则会创建任务）。"""
        cb = self._node_map.get(node_id)
        if not cb:
            return
        try:
            res = cb(node_id, "direct", message)
            if asyncio.iscoroutine(res):
                asyncio.create_task(res)
        except Exception:
            pass

    async def request_response(self, channel: str, message: Any, timeout: Optional[float] = None) -> Any:
        """发布消息并等待单个响应（返回值或超时返回 None）。

        典型用例：等待人工确认或外部系统回复。
        实现：在 `_pending[channel]` 放入 Future，外部在收到后调用 `inject_external`。
        """
        fut = asyncio.get_event_loop().create_future()
        self._pending.setdefault(channel, []).append(fut)
        self.publish(channel, message)
        try:
            return await asyncio.wait_for(fut, timeout) if timeout else await fut
        except asyncio.TimeoutError:
            # 清理 pending
            try:
                self._pending[channel].remove(fut)
            except Exception:
                pass
            return None

    def inject_external(self, channel: str, message: Any) -> None:
        """外部/人工输入：如果有 pending future 则首先满足其，否则广播到 channel 订阅者。"""
        # satisfy pending futures first
        pend = self._pending.get(channel)
        if pend:
            # pop oldest
            try:
                fut = pend.pop(0)
                if not fut.done():
                    fut.set_result(message)
                    return
            except Exception:
                pass
        # otherwise publish normally
        self.publish(channel, message)

    def get_last(self, channel: str):
        """返回 channel 上最近一次 publish 的消息（若无则返回 None）。"""
        return self._last_message.get(channel)


__all__ = ["CommunicationHub"]
