from threading import Lock
from typing import Optional


class Interrupt:
    """中断控制器，维护一个核心布尔值标志（线程安全）。

    提供同步的操作接口：
    - `set_true()`：将标志置为 True
    - `set_false()`：将标志置为 False
    - `toggle()`：切换标志并返回新的值

    当前值可通过 `is_set()` 或 `value` 属性读取。
    """

    def __init__(self, initial: Optional[bool] = False) -> None:
        # 用于保护对 _value 的并发访问
        self._lock = Lock()
        self._value = bool(initial)

    def set_true(self) -> None:
        """将中断标志设为 True。"""
        with self._lock:
            self._value = True

    def set_false(self) -> None:
        """将中断标志设为 False。"""
        with self._lock:
            self._value = False

    def toggle(self) -> bool:
        """切换中断标志并返回切换后的新值。"""
        with self._lock:
            self._value = not self._value
            return self._value

    def is_set(self) -> bool:
        """返回当前中断标志的值。"""
        with self._lock:
            return self._value

    @property
    def value(self) -> bool:
        """属性方式读取当前值（等同于 `is_set()`）。"""
        return self.is_set()

    def set(self, val: bool) -> None:
        """将中断标志设为指定的布尔值。"""
        with self._lock:
            self._value = bool(val)

    def __repr__(self) -> str:
        return f"<Interrupt value={self._value}>"
