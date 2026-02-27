from threading import Lock
from typing import Optional, Dict


_lock = Lock()
_api_key: Optional[str] = None
_endpoint: Optional[str] = None


def set_llm_api(api_key: Optional[str] = None, endpoint: Optional[str] = None) -> None:
    """设置全局 LLM API 配置。提供 None 会忽略该项。

    其它模块（尤其是 LLM 插件）应通过 `from Workflow.llm_config import get_llm_api` 获取当前值。
    """
    global _api_key, _endpoint
    with _lock:
        if api_key is not None:
            _api_key = api_key
        if endpoint is not None:
            _endpoint = endpoint


def get_llm_api() -> Dict[str, Optional[str]]:
    """返回当前全局 LLM API 配置：{"api_key": str|None, "endpoint": str|None}。"""
    with _lock:
        return {"api_key": _api_key, "endpoint": _endpoint}


def clear_llm_api() -> None:
    """清空全局 LLM API 配置。"""
    global _api_key, _endpoint
    with _lock:
        _api_key = None
        _endpoint = None
