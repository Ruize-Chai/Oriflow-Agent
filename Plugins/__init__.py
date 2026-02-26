"""Plugins package marker.

插件通过 `Nodes.pluginSeeker.Search_Node` 动态导入 `Plugins.<name>` 模块。
确保 `Plugins` 是一个包以便 importlib 可以导入插件模块。
"""

__all__ = []
