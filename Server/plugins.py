from fastapi import APIRouter
from typing import Any
from Server.utils import read_plugin_lists

router = APIRouter(prefix="/plugins", tags=["plugins"])


@router.get("/", response_model=Any)
def get_plugins():
    """返回已注册的插件列表（来自 Plugins/pluginLists.json）。"""
    return read_plugin_lists()
