"""简单的 API key 管理器（内存）。

提供按 provider 存取 API keys 的接口。当前实现仅在进程内保存，重启后会丢失。
"""
from typing import Dict, Optional

_KEYS: Dict[str, str] = {}


def set_api_key(provider: str, key: str) -> None:
    _KEYS[str(provider)] = str(key)


def get_api_key(provider: str) -> Optional[str]:
    return _KEYS.get(str(provider))


def clear_api_key(provider: str) -> None:
    _KEYS.pop(str(provider), None)


def has_key(provider: str) -> bool:
    return str(provider) in _KEYS


__all__ = ["set_api_key", "get_api_key", "clear_api_key", "has_key"]
