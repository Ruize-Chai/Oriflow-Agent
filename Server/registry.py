"""简单的工作流运行时注册表（内存）。

在没有持久化或进程外管理器的情况下，这个模块为 HTTP 适配器提供
一个将 `wf_id` 映射到运行时 `Workflow` 实例的轻量注册表接口。

注意：仅适用于单进程测试/开发；生产环境应替换为进程间/分布式注册表。
"""
from typing import Any, Dict, Optional

_REGISTRY: Dict[str, Any] = {}


def register_workflow(wf_id: str, wf: Any) -> None:
    _REGISTRY[str(wf_id)] = wf


def get_workflow(wf_id: str) -> Optional[Any]:
    return _REGISTRY.get(str(wf_id))


def unregister_workflow(wf_id: str) -> None:
    _REGISTRY.pop(str(wf_id), None)


def list_workflows() -> Dict[str, Any]:
    return dict(_REGISTRY)


__all__ = ["register_workflow", "get_workflow", "unregister_workflow", "list_workflows"]
