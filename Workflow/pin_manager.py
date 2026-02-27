"""PinManager: 以 asyncio.Event 为主的引脚管理器

职责：
- 托管按 id 的引脚状态(bool)，并为监听方在事件循环中提供 `asyncio.Event`。
- 提供 `activate(pin_id)` / `deactivate(pin_id)` / `is_active(pin_id)` /
  `async wait_async(pin_id, timeout=None)` / `get_pins()` / `clear_all()`。

实现说明：
- 内部维护一个线程安全的 `_state: Dict[int,bool]` 存当前激活状态。
- 当协程调用 `wait_async` 时，会在调用的事件循环中创建并保存 `asyncio.Event`,
  当 `activate` 在任意线程被调用时，会通过保存的 loop 用 `call_soon_threadsafe` 通知该事件。
"""

from threading import Lock
import asyncio
from typing import Dict, Optional, Tuple


class PinManager:
	def __init__(self) -> None:
		self._lock = Lock()
		# pin 当前激活状态
		self._state: Dict[int, bool] = {}
		# 异步事件表：pin_id -> (asyncio.Event, loop)
		self._async_pins: Dict[int, Tuple[asyncio.Event, asyncio.AbstractEventLoop]] = {}

	def activate(self, pin_id: int) -> None:
		"""激活指定引脚；如果存在等待的 asyncio.Event 会通知它。"""
		pid = int(pin_id)
		with self._lock:
			self._state[pid] = True
			pair = self._async_pins.get(pid)

		if pair is not None:
			async_ev, loop = pair
			try:
				loop.call_soon_threadsafe(async_ev.set)
			except Exception:
				# 忽略 loop 已关闭等情况
				pass

	def deactivate(self, pin_id: int) -> None:
		"""将指定引脚置为未激活；并尝试在 async 事件上清除标志。"""
		pid = int(pin_id)
		with self._lock:
			self._state[pid] = False
			pair = self._async_pins.get(pid)

		if pair is not None:
			async_ev, loop = pair
			try:
				loop.call_soon_threadsafe(async_ev.clear)
			except Exception:
				pass

	def is_active(self, pin_id: int) -> bool:
		"""查询指定引脚当前是否激活（线程安全）。"""
		with self._lock:
			return bool(self._state.get(int(pin_id), False))

	def get_async_event(self, pin_id: int) -> Optional[asyncio.Event]:
		"""若某个 pin 已在某事件循环中被 `wait_async` 注册，返回其 asyncio.Event，否则返回 None。"""
		with self._lock:
			pair = self._async_pins.get(int(pin_id))
		return pair[0] if pair is not None else None

	async def wait_async(self, pin_id: int, timeout: Optional[float] = None) -> bool:
		"""在当前协程事件循环中等待 pin 被激活。

		- 若在调用时 pin 已激活，立即返回 True。
		- 否则在当前 loop 中创建 asyncio.Event 并等待其 set。
		- 若在 `timeout` 内未激活，返回 False。
		"""
		pid = int(pin_id)

		if self.is_active(pid):
			return True

		loop = asyncio.get_running_loop()

		with self._lock:
			pair = self._async_pins.get(pid)
			if pair is None:
				async_ev = asyncio.Event()
				# 若在创建期间 state 被置为 True，则安排在本循环设置事件
				if self._state.get(pid, False):
					loop.call_soon(async_ev.set)
				self._async_pins[pid] = (async_ev, loop)
			else:
				async_ev, _ = pair

		try:
			if timeout is None:
				await async_ev.wait()
				return True
			else:
				await asyncio.wait_for(async_ev.wait(), timeout=timeout)
				return True
		except asyncio.TimeoutError:
			return False

	def get_pins(self) -> Dict[int, bool]:
		"""返回当前已知的 pins 及其激活状态副本。"""
		with self._lock:
			return dict(self._state)

	def clear_all(self) -> None:
		"""清除所有 pin 状态并移除 async 事件表。"""
		with self._lock:
			self._state.clear()
			self._async_pins.clear()

	def __repr__(self) -> str:
		with self._lock:
			return f"<PinManager pins={len(self._state)}>"


