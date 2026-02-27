from threading import Lock
from typing import Any, Dict, Optional


class InCommunicateHub:
    """向内消息总线（每个 node 只保留单条消息）。

    存储结构为 node_id -> single_message(覆盖写入)。提供接口：
    - `send(node_id, message)`：写入/覆盖 node 的消息
    - `read(node_id)`：读取 node 的当前消息（不清除）
    - `pop(node_id)`：取出并清空 node 的消息，返回该消息或 None
    - `clear(node_id)`：清空 node 的消息
    """

    def __init__(self) -> None:
        self._lock = Lock()
        self._store: Dict[int, Any] = {}

    def send(self, node_id: int, message: Any) -> None:
        """写入（或覆盖）指定 `node_id` 的消息（线程安全）。"""
        with self._lock:
            self._store[int(node_id)] = message

    def read(self, node_id: int) -> Optional[Any]:
        """返回指定 `node_id` 的当前消息快照（不清除）。若不存在返回 None。"""
        with self._lock:
            return self._store.get(int(node_id))

    def pop(self, node_id: int) -> Optional[Any]:
        """取出并清空指定 `node_id` 的消息，返回该消息或 None(线程安全）。"""
        with self._lock:
            return self._store.pop(int(node_id), None)

    def clear(self, node_id: int) -> None:
        """清空指定 `node_id` 的消息（若不存在则无操作）。"""
        with self._lock:
            self._store.pop(int(node_id), None)

    def __repr__(self) -> str:  # pragma: no cover - trivial
        with self._lock:
            count = len(self._store)
        return f"<InCommunicateHub nodes={count}>"
