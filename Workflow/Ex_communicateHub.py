from threading import Lock
from typing import Any, Dict, Optional


class ExCommunicateHub:
    """向外寄存总线（前端/外部系统使用）。

    存储为 node_id -> single_message(覆盖写入），提供基本接口：
    - `cache(node_id, message)`：存入/覆盖消息
    - `read(node_id)`：读取当前消息（不清除）
    - `fetch(node_id)`：取出并清空消息，返回该消息或 None
    - `clear(node_id)`：清空消息

    设计与 `InCommunicateHub` 相似，但命名与使用面向前端/外部读取。
    """

    def __init__(self) -> None:
        self._lock = Lock()
        self._store: Dict[int, Any] = {}

    def cache(self, node_id: int, message: Any) -> None:
        """缓存（或覆盖）指定 `node_id` 的消息。"""
        with self._lock:
            self._store[int(node_id)] = message

    def read(self, node_id: int) -> Optional[Any]:
        """读取指定 `node_id` 的当前消息（不清空）。不存在返回 None。"""
        with self._lock:
            return self._store.get(int(node_id))

    def fetch(self, node_id: int) -> Optional[Any]:
        """取出并清空指定 `node_id` 的消息，返回该消息或 None。"""
        with self._lock:
            return self._store.pop(int(node_id), None)

    def clear(self, node_id: int) -> None:
        """清空指定 `node_id` 的消息（若不存在则无操作）。"""
        with self._lock:
            self._store.pop(int(node_id), None)

    def __repr__(self) -> str:  # pragma: no cover - trivial
        with self._lock:
            count = len(self._store)
        return f"<ExCommunicateHub nodes={count}>"
